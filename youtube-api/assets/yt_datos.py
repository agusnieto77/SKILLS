#!/usr/bin/env python3
"""Cliente de datos publicos de YouTube: metadatos, transcripcion y comentarios.

Uso:
    python yt_datos.py metadatos    --url https://www.youtube.com/watch?v=ID [--out datos]
    python yt_datos.py pistas       --url ID [--out datos]
    python yt_datos.py transcripcion --url ID [--lang es,en] [--tipo-subtitulo manual] [--tlang es]
    python yt_datos.py comentarios  --url https://www.youtube.com/watch?v=ID [--max 200] [--con-respuestas] [--out datos]
    python yt_datos.py todo         --url https://www.youtube.com/watch?v=ID [--max 200] [--out datos]
    Todos aceptan --url ID1 ID2 o --archivo-ids ids.txt (hasta 50 entradas).
    Comentarios: --max-paginas 1..60 y --max-peticiones 1..120, compartidos con respuestas.

Solo lectura: no envia credenciales ni modifica nada en YouTube. Usa la API
interna (InnerTube) y las paginas publicas de watch, igual que un navegador
anonimo. Si el sitio exige sesion, se informa el bloqueo en lugar de evadirlo.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote_plus, urlparse

import requests

try:  # Windows no trae CA del sistema para OpenSSL: usar el almacen del SO.
    import truststore

    truststore.inject_into_ssl()
except Exception:  # pragma: no cover - entornos sin truststore
    pass

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
TIMEOUT = 30.0
PAUSA = 1.0  # segundos entre peticiones: no martillar el servidor.
CLIENT_ANDROID = {"clientName": "ANDROID", "clientVersion": "20.10.38"}
CLIENT_WEB = {"clientName": "WEB", "clientVersion": "2.20240101.00.00"}
MAX_VIDEOS = 50
MAX_PAGINAS = 60
MAX_PETICIONES = 120  # Intentos HTTP de /next, incluidos los reintentos 429.


class YouTubeError(RuntimeError):
    """Error recuperable de la recoleccion."""


class LimiteComentarios(YouTubeError):
    """Presupuesto agotado sin solicitar otra pagina."""


@dataclass
class PresupuestoComentarios:
    max_paginas: int = MAX_PAGINAS
    max_peticiones: int = MAX_PETICIONES
    paginas_consumidas: int = 0
    peticiones_consumidas: int = 0

    def consumir_peticion(self):
        if self.paginas_consumidas >= self.max_paginas:
            raise LimiteComentarios("max_paginas")
        if self.peticiones_consumidas >= self.max_peticiones:
            raise LimiteComentarios("max_peticiones")
        self.peticiones_consumidas += 1

    def salida(self, maximo: int) -> dict:
        return {
            "max_filas": maximo,
            "max_paginas": self.max_paginas,
            "max_peticiones": self.max_peticiones,
            "paginas_consumidas": self.paginas_consumidas,
            "peticiones_consumidas": self.peticiones_consumidas,
            "alcance": "youtubei/v1/next; incluye orden, hilos y reintentos; excluye watch/player/timedtext",
        }


# --------------------------------------------------------------------------- #
# Utilidades puras (sin red): se pueden probar de forma aislada.
# --------------------------------------------------------------------------- #
def extraer_id_video(url: str) -> str:
    """Devuelve el ID de 11 caracteres de una URL o ID de YouTube."""
    texto = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", texto):
        return texto
    partes = urlparse(texto)
    if partes.netloc.endswith("youtu.be"):
        id_ = partes.path.strip("/").split("/")[0]
    elif "v" in parse_qs(partes.query):
        id_ = parse_qs(partes.query)["v"][0]
    else:
        segmentos = [s for s in partes.path.split("/") if s]
        if len(segmentos) >= 2 and segmentos[0] in {"shorts", "embed", "live", "v"}:
            id_ = segmentos[1]
        else:
            candidatos = re.findall(r"[?&]v=([A-Za-z0-9_-]{11})", texto)
            id_ = candidatos[0] if candidatos else ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", id_):
        raise YouTubeError(f"No se pudo deducir el ID del video a partir de {url!r}")
    return id_


def _json_empotrado(html: str, variable: str) -> dict | None:
    """Extrae un objeto JSON asignado a una variable global de la pagina.

    Decodifica desde la llave de apertura con raw_decode: un regex no codicioso
    cortaria en el primer "};" que aparezca dentro de un string del JSON.
    """
    decodificador = json.JSONDecoder()
    for patron in (
        rf"var\s+{variable}\s*=\s*",
        rf'"{variable}"\]\s*=\s*',
        rf"\b{variable}\s*=\s*",
    ):
        for m in re.finditer(patron, html):
            inicio = m.end()
            if not html.startswith("{", inicio):
                continue
            try:
                objeto, _ = decodificador.raw_decode(html, inicio)
            except json.JSONDecodeError:
                continue
            if isinstance(objeto, dict):
                return objeto
    return None


def extraer_respuesta_player(html: str) -> dict | None:
    """ytInitialPlayerResponse: metadatos del video y pistas de subtitulo."""
    return _json_empotrado(html, "ytInitialPlayerResponse")


def extraer_datos_iniciales(html: str) -> dict | None:
    """ytInitialData: seccion de comentarios y demas contenido de la pagina."""
    return _json_empotrado(html, "ytInitialData")


def _texto_runs(runs: list | None) -> str:
    if not isinstance(runs, list):
        return ""
    return "".join(str(r.get("text", "")) for r in runs if isinstance(r, dict))


def metadatos_desde_player(player: dict) -> dict:
    """Normaliza los metadatos utiles de la respuesta del reproductor."""
    detalles = player.get("videoDetails") or {}
    micro = (player.get("microformat") or {}).get("playerMicroformatRenderer") or {}
    estado = (player.get("playabilityStatus") or {}).get("status")
    return {
        "video_id": detalles.get("videoId"),
        "titulo": detalles.get("title"),
        "canal": detalles.get("author"),
        "canal_id": detalles.get("channelId"),
        "vistas": int(detalles.get("viewCount") or 0),
        "duracion_s": int(detalles.get("lengthSeconds") or 0),
        "descripcion": detalles.get("shortDescription") or "",
        "keywords": detalles.get("keywords") or [],
        "categoria": micro.get("category"),
        "likes": int(micro.get("likeCount") or 0),
        "fecha_publicacion": micro.get("publishDate"),
        "fecha_subida": micro.get("uploadDate"),
        "es_en_vivo": bool(detalles.get("isLiveContent")),
        "disponibilidad": estado,
    }


def segmentos_desde_timedtext(xml_texto: str) -> list[dict]:
    """Convierte el XML timedtext (formatos 1 y 3) en segmentos con tiempo."""
    try:
        raiz = ET.fromstring(xml_texto)
    except ET.ParseError as exc:
        raise YouTubeError(f"Respuesta de subtitulos no interpretable: {exc}") from exc
    segmentos: list[dict] = []
    for nodo in raiz.iter():
        if nodo.tag == "text":  # formato 1: <text start dur>texto</text>
            inicio = float(nodo.get("start") or 0)
            dur = float(nodo.get("dur") or 0)
            texto = "".join(nodo.itertext())
            if texto.strip():
                segmentos.append({"inicio": inicio, "duracion": dur, "texto": texto.strip()})
        elif nodo.tag == "p":  # formato 3: <p t d><s>trozo</s></p>
            inicio = float(nodo.get("t") or 0) / 1000.0
            dur = float(nodo.get("d") or 0) / 1000.0
            texto = "".join(nodo.itertext())
            if texto.strip():
                segmentos.append({"inicio": inicio, "duracion": dur, "texto": texto.strip()})
    return segmentos


def _buscar_seccion_comentarios(datos: dict | None) -> dict | None:
    """Localiza el bloque comment-item-section dentro de ytInitialData."""
    if not isinstance(datos, dict):
        return None

    def recorrer(nodo):
        if isinstance(nodo, dict):
            if nodo.get("sectionIdentifier") == "comment-item-section":
                return nodo
            for valor in nodo.values():
                hallazgo = recorrer(valor)
                if hallazgo:
                    return hallazgo
        elif isinstance(nodo, list):
            for valor in nodo:
                hallazgo = recorrer(valor)
                if hallazgo:
                    return hallazgo
        return None

    return recorrer(datos)


def _tokens_continuacion(nodo) -> list[dict]:
    """Tokens de continuacion hallados en cualquier parte de un subarbol."""
    hallados: list[dict] = []
    if isinstance(nodo, dict):
        comando = nodo.get("continuationCommand")
        if isinstance(comando, dict) and comando.get("token"):
            hallados.append(
                {
                    "token": comando["token"],
                    "click_tracking": nodo.get("clickTrackingParams"),
                }
            )
        for valor in nodo.values():
            hallados.extend(_tokens_continuacion(valor))
    elif isinstance(nodo, list):
        for valor in nodo:
            hallados.extend(_tokens_continuacion(valor))
    return hallados


def _view_model(item: dict) -> dict | None:
    """Normaliza el view model de un comentario (nuevo y viejo formato)."""
    vm = item.get("commentViewModel")
    if isinstance(vm, dict):
        return vm.get("commentViewModel", vm)
    hilo = item.get("commentThreadRenderer")
    if isinstance(hilo, dict):
        vm = hilo.get("commentViewModel")
        if isinstance(vm, dict):
            return vm.get("commentViewModel", vm)
    return None


def _coincidir_entidad(entities: dict, clave: str) -> dict | None:
    """Localiza la entidad de un comentario por clave (exacto o prefijo)."""
    if not clave:
        return None
    directa = entities.get(clave)
    if directa:
        return directa
    for entidad, payload in entities.items():
        if clave.startswith(entidad):
            return payload
    return None


def _elegir_pista(lista: list[dict], idiomas: list[str] | None = None, tipo: str = "cualquiera") -> dict:
    """Preferencias explicitas en orden; dentro de cada idioma, manual antes que ASR."""
    if tipo not in {"cualquiera", "manual", "asr"}:
        raise YouTubeError("Tipo de subtitulo desconocido.")
    candidatas = [p for p in lista if tipo == "cualquiera" or (p.get("kind") == "asr") == (tipo == "asr")]
    if not candidatas:
        raise YouTubeError(f"No hay pistas del tipo {tipo!r}.")
    if idiomas:
        for codigo in idiomas:
            coincidencias = [p for p in candidatas if p.get("languageCode") == codigo]
            if coincidencias:
                return next((p for p in coincidencias if p.get("kind") != "asr"), coincidencias[0])
        disponibles = ", ".join(sorted({p.get("languageCode", "?") for p in candidatas}))
        raise YouTubeError(f"No hay subtitulos en {idiomas!r} del tipo {tipo}; disponibles: {disponibles}")
    manual = [p for p in candidatas if p.get("kind") != "asr"]
    candidatas = manual or candidatas
    for codigo in ("es", "es-419", "en"):
        for pista in candidatas:
            if pista.get("languageCode") == codigo:
                return pista
    return candidatas[0]


def _consulta_continuacion(token: dict) -> dict:
    """Arma el cuerpo de consulta para un token de continuacion."""
    consulta = {"continuation": token["token"]}
    if token.get("click_tracking"):
        consulta["clickTracking"] = {"clickTrackingParams": token["click_tracking"]}
    return consulta


_SUFIJOS_CONTEO = (
    (r"(mil\s*mill|bn|b)\b", 1_000_000_000),
    (r"(mill|m)\b", 1_000_000),
    (r"(mil|k)\b", 1_000),
)


def _numero_de_conteo(texto: str) -> int | None:
    """Convierte "2.460.280", "1,234", "2,4 M", "15 mil" o "3.1K" en entero.

    Las formas abreviadas son aproximadas; por eso se prefiere el texto exacto.
    """
    limpio = str(texto).strip().lower().replace("\xa0", " ")
    for patron, factor in _SUFIJOS_CONTEO:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*" + patron, limpio)
        if m:
            return int(round(float(m.group(1).replace(",", ".")) * factor))
    digitos = re.sub(r"[^\d]", "", limpio)
    return int(digitos) if digitos else None


def _contar_comentarios(cabecera: dict) -> int | None:
    """Total de comentarios declarado por la pagina.

    `countText` trae el total exacto ("2.460.280 comentarios"); `commentsCount`
    suele venir abreviado ("2,4 M"). Se usa el primero cuando existe.
    """
    for clave in ("countText", "commentsCount"):
        bloque = cabecera.get(clave) or {}
        texto = bloque.get("simpleText") or _texto_runs(bloque.get("runs"))
        if texto:
            numero = _numero_de_conteo(texto)
            if numero is not None:
                return numero
    return None


def _token_de_orden(cabecera: dict, orden: str) -> dict | None:
    """Token de clasificacion ("Destacados" / "Mas recientes") de la cabecera."""
    submenu = (
        ((cabecera.get("sortMenu") or {}).get("sortFilterSubMenuRenderer") or {}).get("subMenuItems") or []
    )
    if not submenu:
        return None
    indice = 1 if orden == "newest" else 0
    if indice >= len(submenu):
        return None
    tokens = _tokens_continuacion(submenu[indice])
    return _consulta_continuacion(tokens[0]) if tokens else None


def _siguiente_consulta(items: list) -> dict | None:
    """Consulta de la pagina siguiente, si la pagina la publica.

    Los hilos de respuestas anidan el token en un boton ("Mostrar mas
    respuestas") en lugar del endpoint directo.
    """
    for item in items:
        if not isinstance(item, dict):
            continue
        bloque = item.get("continuationItemRenderer")
        if not isinstance(bloque, dict):
            continue
        candidatos = [
            bloque.get("continuationEndpoint") or {},
            ((bloque.get("button") or {}).get("buttonRenderer") or {}).get("command") or {},
        ]
        for endpoint in candidatos:
            comando = endpoint.get("continuationCommand") or {}
            if comando.get("token"):
                return _consulta_continuacion(
                    {
                        "token": comando["token"],
                        "click_tracking": endpoint.get("clickTrackingParams"),
                    }
                )
    return None


def item_por_id(items: list, comment_id: str | None) -> dict:
    """Localiza el item de hilo que corresponde a un comentario."""
    if not comment_id:
        return {}
    for item in items:
        if not isinstance(item, dict):
            continue
        vm = _view_model(item)
        if vm and vm.get("commentId") == comment_id:
            return item
    return {}


def _token_de_respuestas(item: dict) -> dict | None:
    """Token de continuacion del hilo de respuestas de un comentario."""
    if not item:
        return None
    hilo = item.get("commentThreadRenderer") or {}
    respuestas = (hilo.get("replies") or {}).get("commentRepliesRenderer") or {}
    for contenido in respuestas.get("contents") or []:
        bloque = (contenido or {}).get("continuationItemRenderer") or {}
        endpoint = bloque.get("continuationEndpoint") or {}
        comando = endpoint.get("continuationCommand") or {}
        if comando.get("token"):
            return _consulta_continuacion(
                {"token": comando["token"], "click_tracking": endpoint.get("clickTrackingParams")}
            )
    return None


def _comentarios_de_items(items: list, entities: dict) -> list[dict]:
    """Traduce view models + entidad de payload a filas de comentario."""
    filas: list[dict] = []
    for item in items:
        vm = _view_model(item)
        if not vm:
            continue
        payload = _coincidir_entidad(entities, vm.get("commentKey", "")) or {}
        entidad = payload.get("commentEntityPayload") or {}
        props = entidad.get("properties") or {}
        contenido = (props.get("content") or {}).get("content") or ""
        if not contenido.strip():
            continue
        toolbar = entidad.get("toolbar") or {}
        autor = entidad.get("author") or {}
        filas.append(
            {
                "comment_id": props.get("commentId") or vm.get("commentId"),
                "autor": autor.get("displayName"),
                "autor_canal_id": autor.get("channelId"),
                "autor_es_creador": bool(autor.get("isCreator")),
                "texto": contenido.strip(),
                "publicado": props.get("publishedTime"),
                "likes": toolbar.get("likeCountNotliked"),
                "respuestas": toolbar.get("replyCount"),
                "nivel": props.get("replyLevel", 0),
            }
        )
    return filas


@dataclass
class ClienteYouTube:
    """Cliente HTTP de solo lectura contra la API interna de YouTube."""

    sesion: requests.Session = field(default_factory=requests.Session)
    pausar: float = PAUSA
    # Cache por video: `todo` reutiliza la ficha y la respuesta del reproductor
    # en lugar de pedirlas una vez por operacion.
    _html: dict = field(default_factory=dict, repr=False)
    _player: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self.sesion.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        )

    # -- infraestructura ---------------------------------------------------- #
    @staticmethod
    def _espera_429(respuesta: requests.Response) -> float:
        """Segundos a esperar ante HTTP 429: Retry-After numerico, acotado a 30 s.

        Retry-After tambien puede ser una fecha HTTP; en ese caso se usa la
        espera por defecto en lugar de fallar al convertir.
        """
        try:
            espera = float(respuesta.headers.get("Retry-After") or 10)
        except ValueError:
            espera = 10.0
        return min(max(espera, 0.0), 30.0)

    def _get(self, url: str, **kwargs) -> requests.Response:
        respuesta = self.sesion.get(url, timeout=TIMEOUT, **kwargs)
        if respuesta.status_code == 429:
            time.sleep(self._espera_429(respuesta))
            respuesta = self.sesion.get(url, timeout=TIMEOUT, **kwargs)
        return respuesta

    def _post(self, url: str, payload: dict, presupuesto: PresupuestoComentarios | None = None) -> requests.Response:
        if presupuesto:
            presupuesto.consumir_peticion()
        respuesta = self.sesion.post(url, json=payload, timeout=TIMEOUT)
        if respuesta.status_code == 429:
            if presupuesto:
                presupuesto.consumir_peticion()
            time.sleep(self._espera_429(respuesta))
            respuesta = self.sesion.post(url, json=payload, timeout=TIMEOUT)
        return respuesta

    # -- paginas publicas ---------------------------------------------------- #
    def pagina_watch(self, video_id: str) -> str:
        """HTML publico de la ficha del video (una sola descarga por video)."""
        if video_id in self._html:
            return self._html[video_id]
        respuesta = self._get(f"https://www.youtube.com/watch?v={video_id}")
        if respuesta.status_code != 200:
            raise YouTubeError(
                f"No se pudo abrir la ficha del video (HTTP {respuesta.status_code}). "
                "Puede ser un video privado, restringido por edad o eliminado."
            )
        self._html[video_id] = respuesta.text
        return respuesta.text

    def clave_api(self, html: str) -> str:
        """Clave publica de InnerTube que la propia pagina publica."""
        m = re.search(r'"INNERTUBE_API_KEY":"([A-Za-z0-9_-]+)"', html)
        if not m:
            raise YouTubeError("La pagina no publico ninguna clave de API; YouTube cambio el HTML.")
        return m.group(1)

    def version_cliente(self, html: str) -> str:
        m = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html)
        return m.group(1) if m else CLIENT_WEB["clientVersion"]

    # -- API interna --------------------------------------------------------- #
    def reproductor(self, video_id: str, clave: str) -> dict:
        """Respuesta de youtubei/v1/player: metadatos y pistas de subtitulo."""
        if video_id in self._player:
            return self._player[video_id]
        payload = {
            "context": {"client": CLIENT_ANDROID},
            "videoId": video_id,
            "contentCheckOk": True,
            "racyCheckOk": True,
        }
        respuesta = self._post(f"https://www.youtube.com/youtubei/v1/player?key={clave}", payload)
        if respuesta.status_code != 200:
            raise YouTubeError(f"El reproductor respondio HTTP {respuesta.status_code}")
        datos = respuesta.json()
        estado = (datos.get("playabilityStatus") or {}).get("status")
        if estado not in (None, "OK"):
            motivo = (datos.get("playabilityStatus") or {}).get("reason") or estado
            raise YouTubeError(f"El video no es reproducible de forma anonima: {motivo}")
        self._player[video_id] = datos
        return datos

    def siguiente(self, clave: str, ctx: dict, presupuesto: PresupuestoComentarios | None = None, **consulta) -> dict:
        """Respuesta de youtubei/v1/next (comentarios y continuaciones)."""
        payload = {"context": ctx, **consulta}
        respuesta = self._post(f"https://www.youtube.com/youtubei/v1/next?key={clave}", payload, presupuesto)
        if respuesta.status_code != 200:
            raise YouTubeError(f"youtubei/v1/next respondio HTTP {respuesta.status_code}")
        datos = respuesta.json()
        if not isinstance(datos, dict):
            raise YouTubeError("youtubei/v1/next no devolvio un objeto JSON.")
        if datos.get("error"):
            raise YouTubeError(f"youtubei/v1/next devolvio un error: {datos['error']}")
        if presupuesto:
            presupuesto.paginas_consumidas += 1
        return datos

    # -- operaciones de alto nivel ------------------------------------------- #
    def metadatos(self, video_id: str) -> dict:
        html = self.pagina_watch(video_id)
        player = extraer_respuesta_player(html)
        if not player:
            raise YouTubeError("No se encontro ytInitialPlayerResponse en la ficha del video.")
        datos = metadatos_desde_player(player)
        if not datos.get("titulo"):
            estado = datos.get("disponibilidad") or "desconocido"
            raise YouTubeError(
                f"El video no expone metadatos publicos (estado del reproductor: {estado}). "
                "Puede estar eliminado, ser privado o estar restringido por edad."
            )
        return datos

    def pistas_subtitulo(self, video_id: str) -> list[dict]:
        """Pistas de subtitulo disponibles (idioma, nombre y si es autodeclarada)."""
        html = self.pagina_watch(video_id)
        clave = self.clave_api(html)
        player = self.reproductor(video_id, clave)
        lista = (
            ((player.get("captions") or {}).get("playerCaptionsTracklistRenderer") or {}).get("captionTracks")
            or []
        )
        pistas = []
        for pista in lista:
            pistas.append(
                {
                    "idioma": pista.get("languageCode"),
                    "nombre": _texto_runs((pista.get("name") or {}).get("runs"))
                    or (pista.get("name") or {}).get("simpleText"),
                    "automatica": pista.get("kind") == "asr",
                    "traducible": bool(pista.get("isTranslatable")),
                    "base_url": pista.get("baseUrl"),
                }
            )
        return pistas

    def transcripcion(
        self, video_id: str, idioma: str | list[str] | None = None,
        tipo: str = "cualquiera", tlang: str | None = None,
    ) -> dict:
        """Subtitulo original o traduccion automatica solicitada a YouTube."""
        if tlang and not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", tlang):
            raise YouTubeError("Codigo tlang no valido.")
        html = self.pagina_watch(video_id)
        clave = self.clave_api(html)
        player = self.reproductor(video_id, clave)
        lista = (
            ((player.get("captions") or {}).get("playerCaptionsTracklistRenderer") or {}).get("captionTracks")
            or []
        )
        if not lista:
            raise YouTubeError("El video no expone transcripcion (subtitulos desactivados).")
        idiomas = [idioma] if isinstance(idioma, str) else idioma
        elegida = _elegir_pista(lista, idiomas, tipo)
        base = elegida.get("baseUrl")
        if not base:
            raise YouTubeError("La pista de subtitulos no trae URL de descarga.")
        if tlang:
            if not elegida.get("isTranslatable"):
                raise YouTubeError("La pista no declara que admita traduccion.")
            # Conservar los bytes de los parametros firmados: no parsear y
            # recodificar la query completa. Solo sustituir/agregar tlang.
            direccion, separador, fragmento = base.partition("#")
            ruta, _, query = direccion.partition("?")
            parametros = [p for p in query.split("&") if p and unquote_plus(p.split("=", 1)[0]) != "tlang"]
            parametros.append("tlang=" + quote(tlang, safe="-"))
            base = ruta + "?" + "&".join(parametros) + (separador + fragmento if separador else "")
        respuesta = self._get(base)
        if respuesta.status_code != 200 or not respuesta.content:
            raise YouTubeError(
                "YouTube no devolvio el archivo de subtitulos (posible requisito de PO token, proof of origin). "
                "Usar yt-dlp como alternativa."
            )
        segmentos = segmentos_desde_timedtext(respuesta.text)
        if not segmentos:
            raise YouTubeError("El archivo de subtitulos venia vacio.")
        return {
            "video_id": video_id,
            "idioma": tlang or elegida.get("languageCode"),
            "idioma_fuente": elegida.get("languageCode"),
            "idioma_destino": tlang or elegida.get("languageCode"),
            "automatica": elegida.get("kind") == "asr",
            "traducida": bool(tlang),
            "metodo": "InnerTube player + timedtext",
            "metodo_traduccion": "traduccion_automatica_youtube_tlang" if tlang else None,
            "traduccion_verificada": False if tlang else None,
            "aviso_traduccion": (
                "Traduccion automatica solicitada a YouTube; fixtures verifican la peticion, "
                "no el idioma servido ni la compatibilidad de la URL firmada."
            ) if tlang else None,
            "segmentos": segmentos,
            "texto": " ".join(s["texto"] for s in segmentos),
        }

    def _continuaciones_items(self, respuesta: dict) -> list[dict]:
        items: list[dict] = []
        for endpoint in respuesta.get("onResponseReceivedEndpoints") or []:
            for clave in ("reloadContinuationItemsCommand", "appendContinuationItemsAction"):
                bloque = endpoint.get(clave)
                if isinstance(bloque, dict):
                    items.extend(bloque.get("continuationItems") or [])
        return items

    @staticmethod
    def _entidades(respuesta: dict) -> dict:
        entidades: dict = {}
        for mutacion in (
            ((respuesta.get("frameworkUpdates") or {}).get("entityBatchUpdate") or {}).get("mutations") or []
        ):
            clave = mutacion.get("entityKey")
            payload = mutacion.get("payload") or {}
            if clave and "commentEntityPayload" in payload:
                entidades[clave] = payload
        return entidades

    def comentarios(
        self, video_id: str, maximo: int = 200, con_respuestas: bool = False,
        orden: str = "newest", max_paginas: int = MAX_PAGINAS, max_peticiones: int = MAX_PETICIONES,
    ) -> dict:
        """Recorre comentarios con presupuesto compartido para orden, paginas y respuestas."""
        if maximo < 1 or not 1 <= max_paginas <= MAX_PAGINAS or not 1 <= max_peticiones <= MAX_PETICIONES:
            raise YouTubeError("Limites: max >= 1, max-paginas entre 1 y 60, max-peticiones entre 1 y 120.")
        if orden not in {"newest", "top"}:
            raise YouTubeError("El orden debe ser newest o top.")
        presupuesto = PresupuestoComentarios(max_paginas, max_peticiones)
        html = self.pagina_watch(video_id)
        clave = self.clave_api(html)
        ctx = {"client": {**CLIENT_WEB, "clientVersion": self.version_cliente(html), "hl": "es", "gl": "ES"}}
        seccion = _buscar_seccion_comentarios(extraer_datos_iniciales(html))
        if not seccion:
            raise YouTubeError("La pagina no expone la seccion de comentarios del video.")
        tokens = _tokens_continuacion(seccion)
        if not tokens:
            raise YouTubeError("No se hallo token de paginacion de comentarios.")
        consulta = _consulta_continuacion(tokens[0])
        filas: list[dict] = []
        hilos: list[dict] = []
        vistos: set[str] = set()
        vistos_tokens: set[str] = set()
        declarados = None
        motivo = "sin_continuacion"
        errores: list[str] = []
        orden_aplicado = False
        while consulta:
            if len(filas) >= maximo:
                motivo = "max_filas"
                break
            token = consulta["continuation"]
            if token in vistos_tokens:
                motivo = "token_repetido"
                break
            vistos_tokens.add(token)
            try:
                respuesta = self.siguiente(clave, ctx, presupuesto=presupuesto, **consulta)
            except LimiteComentarios as exc:
                motivo = str(exc)
                break
            except (YouTubeError, requests.RequestException, ValueError) as exc:
                motivo = "error_pagina"
                errores.append(str(exc))
                time.sleep(self.pausar)
                break
            items = self._continuaciones_items(respuesta)
            cabecera = next((i["commentsHeaderRenderer"] for i in items if "commentsHeaderRenderer" in i), None)
            if cabecera:
                declarados = _contar_comentarios(cabecera)
                consulta_orden = _token_de_orden(cabecera, orden)
                if not orden_aplicado and consulta_orden and consulta_orden["continuation"] not in vistos_tokens:
                    orden_aplicado = True
                    consulta = consulta_orden
                    time.sleep(self.pausar)
                    continue
            nuevas = _comentarios_de_items(items, self._entidades(respuesta))
            omitidas = False
            for fila in nuevas:
                cid = fila.get("comment_id")
                if cid and cid in vistos:
                    continue
                if cid:
                    vistos.add(cid)
                token_respuesta = _token_de_respuestas(item_por_id(items, cid))
                esperadas = _numero_de_conteo(str(fila.get("respuestas") or "")) or 0
                if token_respuesta or esperadas:
                    hilos.append({"comment_id": cid, "consulta": token_respuesta, "esperadas": esperadas})
                if len(filas) < maximo:
                    filas.append(fila)
                else:
                    omitidas = True
            consulta = _siguiente_consulta(items)
            if omitidas or (len(filas) >= maximo and consulta):
                motivo = "max_filas"
                break
            time.sleep(self.pausar)
        respuestas = self._respuestas(
            clave, ctx, hilos, maximo - len(filas), presupuesto, vistos, con_respuestas
        )
        filas.extend(respuestas["filas"])
        pendientes = respuestas["hilos_no_expandidos"]
        if motivo == "sin_continuacion" and respuestas["motivo_fin"]:
            motivo = respuestas["motivo_fin"]
        parcial = (
            motivo != "sin_continuacion" or bool(pendientes) or orden == "top"
            or (declarados is not None and len(filas) < declarados)
        )
        return {
            "video_id": video_id, "metodo": "InnerTube youtubei/v1/next", "orden": orden,
            "comentarios_declarados": declarados, "obtenidos": len(filas), "comentarios": filas,
            "parcial": parcial, "motivo_fin": motivo, "presupuesto": presupuesto.salida(maximo),
            "hilos_no_expandidos": pendientes, "errores": errores,
            "cobertura": "Solo continuaciones publicadas; fin natural no garantiza exhaustividad.",
        }

    def _respuestas(
        self, clave: str, ctx: dict, hilos: list[dict], restantes: int,
        presupuesto: PresupuestoComentarios, vistos: set[str], solicitadas: bool,
    ) -> dict:
        """Expande hilos sin silenciar errores ni exceder filas o presupuesto."""
        filas: list[dict] = []
        pendientes: list[dict] = []
        motivo_fin = None
        for hilo in hilos:
            actual = hilo["consulta"]
            obtenidas = 0
            error = None
            motivo = None
            tokens: set[str] = set()
            if not solicitadas:
                motivo = "no_solicitadas"
            elif restantes <= len(filas):
                motivo = "max_filas"
            elif not actual:
                motivo = "sin_token_respuestas"
            while actual and motivo is None:
                token = actual["continuation"]
                if token in tokens:
                    motivo = "token_repetido"
                    break
                tokens.add(token)
                try:
                    respuesta = self.siguiente(clave, ctx, presupuesto=presupuesto, **actual)
                except LimiteComentarios as exc:
                    motivo = str(exc)
                    break
                except (YouTubeError, requests.RequestException, ValueError) as exc:
                    motivo, error = "error_hilo", str(exc)
                    time.sleep(self.pausar)
                    break
                items = self._continuaciones_items(respuesta)
                nuevas = _comentarios_de_items(items, self._entidades(respuesta))
                for fila in nuevas:
                    cid = fila.get("comment_id")
                    if cid and cid in vistos:
                        continue
                    if len(filas) >= restantes:
                        motivo = "max_filas"
                        break
                    if cid:
                        vistos.add(cid)
                    fila.update(respuesta_a=hilo["comment_id"], nivel=1)
                    filas.append(fila)
                    obtenidas += 1
                actual = _siguiente_consulta(items)
                if actual and len(filas) >= restantes:
                    motivo = "max_filas"
                time.sleep(self.pausar)
            if motivo is None and obtenidas < hilo["esperadas"]:
                motivo = "menos_respuestas_declaradas"
            if motivo:
                registro = {
                    "comment_id": hilo["comment_id"], "respuestas_declaradas": hilo["esperadas"],
                    "respuestas_obtenidas": obtenidas, "motivo": motivo,
                }
                if error:
                    registro["error"] = error
                pendientes.append(registro)
                if solicitadas and motivo_fin is None:
                    motivo_fin = motivo
        return {"filas": filas, "hilos_no_expandidos": pendientes, "motivo_fin": motivo_fin}


# --------------------------------------------------------------------------- #
# Escritura de resultados
# --------------------------------------------------------------------------- #
def _escribir_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def _escribir_csv(ruta: Path, filas: list[dict], columnas: list[str]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=columnas, extrasaction="ignore")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(fila)


COLUMNAS_COMENTARIOS = [
    "comment_id",
    "respuesta_a",
    "autor",
    "autor_canal_id",
    "autor_es_creador",
    "texto",
    "publicado",
    "likes",
    "respuestas",
    "nivel",
]
COLUMNAS_SEGMENTOS = ["inicio", "duracion", "texto"]


def _sello() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _arg_comunes(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", nargs="+", action="extend", default=[], help="IDs o URLs; repetible, maximo 50 entradas")
    parser.add_argument("--archivo-ids", type=Path, help="Archivo UTF-8: un ID o URL por linea; maximo 50 entradas")
    parser.add_argument("--out", default="datos", help="Carpeta de salida (por defecto: datos)")
    parser.add_argument("--json", dest="solo_json", action="store_true", help="No escribir CSV")


def _arg_idiomas(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lang", action="append", help="Idiomas fuente en orden, separados por coma; repetible")
    parser.add_argument("--tipo-subtitulo", choices=["cualquiera", "manual", "asr"], default="cualquiera")
    parser.add_argument("--tlang", help="Idioma destino: traduccion automatica solicitada a YouTube, no verificada")


def _arg_comentarios(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max", dest="maximo", type=int, default=200, help="Maximo de filas, incluidas respuestas")
    parser.add_argument("--max-paginas", type=int, default=MAX_PAGINAS, help="Paginas /next por video: 1-60")
    parser.add_argument("--max-peticiones", type=int, default=MAX_PETICIONES, help="Intentos HTTP /next por video: 1-120")
    parser.add_argument("--con-respuestas", action="store_true")
    parser.add_argument("--orden", choices=["newest", "top"], default="newest",
                        help="newest: mas recientes; top: jerarquia de interfaz; ninguno garantiza exhaustividad")


def _entradas(args: argparse.Namespace) -> list[str]:
    entradas = list(args.url)
    if len(entradas) > MAX_VIDEOS:
        raise YouTubeError("El lote admite como maximo 50 entradas.")
    if args.archivo_ids:
        with args.archivo_ids.open(encoding="utf-8-sig") as archivo:
            for linea in archivo:
                valor = linea.strip()
                if valor and not valor.startswith("#"):
                    entradas.append(valor)
                    if len(entradas) > MAX_VIDEOS:
                        raise YouTubeError("El lote admite como maximo 50 entradas.")
    if not entradas:
        raise YouTubeError("Indicar --url o --archivo-ids con al menos una entrada.")
    return entradas


def _operacion(cliente: ClienteYouTube, video_id: str, comando: str, args: argparse.Namespace) -> dict:
    if comando == "metadatos":
        datos = cliente.metadatos(video_id)
        datos["fuente"] = "youtube.com/watch (ytInitialPlayerResponse)"
    elif comando == "pistas":
        datos = {"video_id": video_id, "metodo": "InnerTube player", "pistas": cliente.pistas_subtitulo(video_id)}
    elif comando == "transcripcion":
        idiomas = [codigo.strip() for valor in (args.lang or []) for codigo in valor.split(",") if codigo.strip()]
        datos = cliente.transcripcion(video_id, idiomas or None, tipo=args.tipo_subtitulo, tlang=args.tlang)
    else:
        datos = cliente.comentarios(
            video_id, maximo=args.maximo, con_respuestas=args.con_respuestas, orden=args.orden,
            max_paginas=args.max_paginas, max_peticiones=args.max_peticiones,
        )
    datos["capturado_en_utc"] = _sello()
    salida = Path(args.out)
    _escribir_json(salida / f"{video_id}_{comando}.json", datos)
    if not args.solo_json and comando in {"transcripcion", "comentarios"}:
        filas = datos["segmentos"] if comando == "transcripcion" else datos["comentarios"]
        columnas = COLUMNAS_SEGMENTOS if comando == "transcripcion" else COLUMNAS_COMENTARIOS
        _escribir_csv(salida / f"{video_id}_{comando}.csv", filas, columnas)
    return datos


def _ejecutar_video(cliente: ClienteYouTube, video_id: str, args: argparse.Namespace) -> dict:
    if args.comando != "todo":
        return _operacion(cliente, video_id, args.comando, args)
    resultado = {"video_id": video_id}
    for comando in ("metadatos", "transcripcion", "comentarios"):
        try:
            resultado[comando] = _operacion(cliente, video_id, comando, args)
        except (YouTubeError, requests.RequestException, ValueError) as exc:
            error = {"video_id": video_id, "error": str(exc), "capturado_en_utc": _sello()}
            resultado[comando] = error
            _escribir_json(Path(args.out) / f"{video_id}_{comando}.json", error)
    return resultado


def _errores_resultado(datos: dict) -> list[str]:
    errores = list(datos.get("errores") or [])
    if "error" in datos:
        errores.append(datos["error"])
    errores.extend(h["error"] for h in datos.get("hilos_no_expandidos", []) if "error" in h)
    for comando in ("metadatos", "transcripcion", "comentarios"):
        if isinstance(datos.get(comando), dict):
            errores.extend(_errores_resultado(datos[comando]))
    return errores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)
    for comando in ("metadatos", "pistas", "transcripcion", "comentarios", "todo"):
        parte = sub.add_parser(comando)
        _arg_comunes(parte)
        if comando in {"transcripcion", "todo"}:
            _arg_idiomas(parte)
        if comando in {"comentarios", "todo"}:
            _arg_comentarios(parte)
    args = parser.parse_args(argv)
    try:
        entradas = _entradas(args)
        if args.comando in {"comentarios", "todo"} and (
            args.maximo < 1 or not 1 <= args.max_paginas <= MAX_PAGINAS
            or not 1 <= args.max_peticiones <= MAX_PETICIONES
        ):
            raise YouTubeError("Limites: max >= 1, max-paginas 1-60, max-peticiones 1-120.")
    except (YouTubeError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    lote = len(entradas) > 1 or args.archivo_ids is not None
    cliente = ClienteYouTube()
    resultados = []
    for posicion, entrada in enumerate(entradas, 1):
        registro = {"posicion": posicion, "entrada": entrada}
        try:
            video_id = extraer_id_video(entrada)
        except YouTubeError as exc:
            if not lote:
                print(f"error: {exc}", file=sys.stderr)
                return 2
            registro.update(ok=False, error=str(exc))
            resultados.append(registro)
            continue
        registro["video_id"] = video_id
        try:
            datos = _ejecutar_video(cliente, video_id, args)
            errores = _errores_resultado(datos)
            registro.update(ok=not errores, resultado=datos)
            if errores:
                registro["error"] = "; ".join(errores)
            if not lote:
                print(json.dumps(datos, ensure_ascii=False, indent=2))
                return 1 if errores else 0
        except (YouTubeError, requests.RequestException, ValueError, OSError) as exc:
            registro.update(ok=False, error=str(exc))
            if not lote:
                print(f"error: {exc}", file=sys.stderr)
                return 3 if isinstance(exc, requests.RequestException) else 1
        resultados.append(registro)
        if posicion < len(entradas):
            time.sleep(cliente.pausar)
    recibo = {
        "comando": args.comando, "capturado_en_utc": _sello(), "max_videos": MAX_VIDEOS,
        "total": len(resultados), "exitosos": sum(r["ok"] for r in resultados), "resultados": resultados,
        "metodo": "Lectura publica anonima; procesamiento secuencial, sin evasion de bloqueos",
    }
    try:
        _escribir_json(Path(args.out) / f"lote_{args.comando}.json", recibo)
    except OSError as exc:
        print(f"error al escribir recibo: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(recibo, ensure_ascii=False, indent=2))
    return 0 if all(r["ok"] for r in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
