#!/usr/bin/env python3
"""Carga asistida del Banco de Datos de Actividades CyT de SIGEVA CONICET.

Uso:
    python sigeva_bd.py doctor
    python sigeva_bd.py bib          --bib cv.bib --salida registros.json [--config config.json]
    python sigeva_bd.py inventario   --config config.json [--dir sigeva-trabajo]
    python sigeva_bd.py catalogo     --config config.json [--limite 40]
    python sigeva_bd.py inspeccionar --config config.json --url "eva/bcoPremio.do?accion=Nuevo"
    python sigeva_bd.py preparar     --registros registros.json --config config.json
    python sigeva_bd.py cargar       --registros sigeva-trabajo/listos.json --config config.json
                                     [--guardar] [--limite 5] [--claves K1 K2] [--confirmar]
    python sigeva_bd.py mapear       --env-file .env --headless [--aceptar]
    python sigeva_bd.py verificar    --env-file .env --headless [--auto | --aceptar]

Todo lo que entra al Banco de Datos es una declaracion jurada. Por eso:
- `cargar` llena los formularios en seco por defecto: solo guarda con `--guardar`.
- Despues de cada alta va a buscar el registro a la lista y compara las fechas.
- Nunca modifica ni borra registros, y nunca aprieta "Enviar presentacion".
- No inventa datos: lo que falta se informa en `preparar` y bloquea la carga.
- Antes de cada tanda revisa que SIGEVA siga teniendo los campos que usa (CONTRATO).
- Las credenciales se tipean en el navegador o llegan por --env-file o SIGEVA_USER/SIGEVA_PASS;
  nunca se escriben en disco.

Probado contra SIGEVA CONICET 14.11.24.6 (mapa de solo lectura) y contra un SIGEVA simulado
(validation/). `mapear` y `verificar` documentan la estructura real y detectan cambios.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

VERSION = "1.0.0"
BASE_DEFECTO = "https://si.conicet.gov.ar"
ROL_BANCO_DATOS = 96
RUTAS = {
    "intranet": "intranet/index.htm",
    "indice": "eva/indexBancoDatos.do?idModulo=1&idGrupo=0&idMenu=0",
    "lista_publicaciones": "eva/bcoProduccionListaPublicacion.do?idModulo=6&idGrupo=6&idMenu=1466&prod=cientifica",
    "alta_articulo": "eva/bcoPrecargarArticulo.do?action=Nuevo",
    "alta_evento": "eva/bcoProduccionListaPublicacionCongreso.do?action=Nuevo&publicado=1",
    "alta_capitulo": "eva/bcoProduccionListaPublicacionCapituloLibro.do?action=Nuevo",
    "alta_libro": "eva/bcoProduccionLibroPublicacion.do?action=Nuevo",
}
# Ids de displaytag de las tablas de la lista de publicaciones (14.11.x).
TABLAS_DEFECTO = {"articulo": "3997137", "evento": "8106305", "capitulo": "4551421", "libro": "148512"}
# Rol de quien declara en libros y partes de libro (casillas del formulario).
ROLES = {"autor": "isAutor", "editor": "isEditor", "revisor": "isRevisor"}
# En libros y partes de libro el referato es el radio "referato" (0 = no, 2 = si), no "tipoReferato".
REFERATO_LIBRO = {True: "2", False: "0"}
SOPORTE = {"impreso": "1", "electronico": "2"}
REFERATO_CON = "2"
PUBLICADO = "1"
# Lo que `cargar` e `inventario` necesitan encontrar en SIGEVA. `verificar` lo contrasta
# contra el mapa real: cualquier faltante es critico. Pantallas relativas a /eva/.
_CAMPOS_COMUNES = {
    "produccion": {"tag": "input"}, "idioma": {"tag": "select"}, "hdnresumen": {"tag": "textarea"},
    "campo_0": {"tag": "select"}, "campo_0_0": {"tag": "select"}, "palabraLabel": {"tag": "input"},
    "theFile": {"tag": "input"}, "autorParticipacionLabel": {"tag": "input"}, "editorial": {"tag": "input"},
    "web": {"tag": "input"}, "tipoSoporteChecked": {"tag": "input", "valores": ["1", "2"]},
}
CONTRATO = [
    {"uso": "inventario y verificacion de altas", "pantalla": RUTAS["lista_publicaciones"].split("eva/", 1)[1],
     "tablas": {"articulo": {"orden": TABLAS_DEFECTO["articulo"], "columnas": ["AÑO", "TÍTULO"]},
                "congresoPublicado": {"orden": TABLAS_DEFECTO["evento"], "columnas": ["AÑO", "TÍTULO"]},
                "capituloLibro": {"orden": TABLAS_DEFECTO["capitulo"], "columnas": ["AÑO", "TÍTULO"]},
                "libro": {"orden": TABLAS_DEFECTO["libro"], "columnas": ["AÑO", "TÍTULO"]}}},
    {"uso": "alta de articulo: precarga", "pantalla": RUTAS["alta_articulo"].split("eva/", 1)[1], "botones": ["Omitir"]},
    {"uso": "alta de articulo", "pantalla": RUTAS["alta_articulo"].split("eva/", 1)[1] + "#omitir",
     "campos": {**_CAMPOS_COMUNES, "bissn": {"tag": "input"}, "brevista": {"tag": "input"}, "publicacionId": {"tag": "input"},
                "srevista": {"tag": "textarea"}, "pais": {"tag": "select"}, "lugarEdicion": {"tag": "input"},
                "volumen": {"tag": "input"}, "numero": {"tag": "input"}, "paginaInicial": {"tag": "input"},
                "paginaFinal": {"tag": "input"}, "doi": {"tag": "input"}, "fechaPublica": {"tag": "input", "datepicker": True},
                "tipoReferato": {"tag": "input", "valores": [REFERATO_CON]}, "publicado": {"tag": "input", "valores": [PUBLICADO]},
                "tipoAdjunto": {"tag": "select"}},
     "botones": ["Buscar por ISSN / e-ISSN", "Buscar por Nombre", "Guardar", "Volver", "autorNuevo"]},
    {"uso": "alta de trabajo en evento", "pantalla": RUTAS["alta_evento"].split("eva/", 1)[1],
     "campos": {**_CAMPOS_COMUNES, "tipoTrabajo": {"tag": "select"}, "tipoPublicacion": {"tag": "select"},
                "tituloPublicacion": {"tag": "input"}, "issnIsbn": {"tag": "input"}, "paisEdicion": {"tag": "select"},
                "lugarPublicacion": {"tag": "input"}, "anioPublica": {"tag": "input", "datepicker": True},
                "reunionCientifica": {"tag": "input"}, "tipoReunion": {"tag": "select"}, "alcanceNacional": {"tag": "input"},
                "alcanceInternacional": {"tag": "input"}, "paisEvento": {"tag": "select"}, "lugarReunion": {"tag": "input"},
                "fechaReunion": {"tag": "input", "datepicker": True}},
     "botones": ["Guardar", "Volver", "autorNuevo"]},
    {"uso": "alta de parte de libro", "pantalla": RUTAS["alta_capitulo"].split("eva/", 1)[1],
     "campos": {**_CAMPOS_COMUNES, "tipoParteLibro": {"tag": "select"}, "tituloLibro": {"tag": "input"},
                "isbn": {"tag": "input"}, "pais": {"tag": "select"}, "lugarEdicion": {"tag": "input"},
                "paginaInicial": {"tag": "input"}, "paginaFinal": {"tag": "input"}, "totalPaginasLibro": {"tag": "input"},
                "anioPublica": {"tag": "input", "datepicker": True}, "publicado": {"tag": "input", "valores": [PUBLICADO]},
                "referato": {"tag": "input", "valores": list(REFERATO_LIBRO.values())},
                "compiladorParticipacionLabel": {"tag": "input"},
                **{n: {"tag": "input"} for n in ROLES.values()}},
     "botones": ["Guardar", "Volver", "autorNuevo", "compiladorNuevo"]},
    {"uso": "alta de libro", "pantalla": RUTAS["alta_libro"].split("eva/", 1)[1],
     "campos": {**{k: v for k, v in _CAMPOS_COMUNES.items() if k != "theFile"}, "qqfile": {"tag": "input"},
                "isbn": {"tag": "input"}, "pais": {"tag": "select"}, "lugarEdicion": {"tag": "input"},
                "totalPaginasLibro": {"tag": "input"}, "anioPublica": {"tag": "input", "datepicker": True},
                "publicado": {"tag": "input", "valores": [PUBLICADO]},
                "referato": {"tag": "input", "valores": list(REFERATO_LIBRO.values())},
                **{n: {"tag": "input"} for n in ROLES.values()}},
     "botones": ["Guardar", "Volver", "autorNuevo"]},
]
TIPOS_PUBLICACION = ("articulo", "evento", "capitulo", "libro")
TIPOS = TIPOS_PUBLICACION + ("generico",)
MAX_PDF_MB = 35  # El formulario lo anuncia pero no lo valida: mas grande guarda nada.
LIMITE_DEFECTO = 5
LIMITE_MAXIMO = 20  # Tandas cortas: SIGEVA se traba con estado de sesion acumulado.
PAUSA_ENTRE_ALTAS_MS = 4_000
ESPERA_LOGIN_MS = 600_000
MAX_PAGINAS_LISTA = 60
INTENTOS_CONFIRMACION = 6  # x 10 s: con PDF grandes el registro aparece tarde.
VERSIONES_ADJUNTO = {"postprint": r"post.?print|aceptad", "final": r"final|publicad|editorial"}
# Mensajes de validacion: SIGEVA usa varios verbos; filtrar por uno solo lee fallos como exitos.
RE_ERROR_FORM = re.compile(r"\bdebe (?:ingresar|seleccionar|adjuntar|especificar|completar|indicar|elegir|cargar)[^\n]{0,140}", re.I)
RE_EXCEPCION = re.compile(r"\b(\w+Exception)\b")
RE_REUBICAR_ARCHIVO = re.compile(r"seleccione nuevamente el archivo", re.I)
RE_BOTON_PROHIBIDO = re.compile(r"enviar|eliminar|borrar|modificar", re.I)
# Rechazos del CAS (clave incorrecta, cuenta bloqueada): ante estos nunca se reintenta.
RE_LOGIN_RECHAZADO = re.compile(r"incorrect|inv[aá]lid|bloquead|no coinciden|credenciales|intentos", re.I)

EQUIVALENTES_LATIN1 = str.maketrans({
    "‘": "'", "’": "'", "‚": ",", "“": '"', "”": '"', "„": '"',
    "‐": "-", "‑": "-", "–": "-", "—": "-", "−": "-", "…": "...",
    "ı": "i", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D", "œ": "oe", "Œ": "OE",
    "≤": "<=", "≥": ">=", "→": "->", "•": "·", "μ": "µ",
})
IDIOMAS_BIB = {
    "english": "Inglés", "en": "Inglés", "american": "Inglés", "british": "Inglés",
    "spanish": "Español", "es": "Español", "castellano": "Español", "español": "Español",
    "portuguese": "Portugués", "pt": "Portugués", "brazilian": "Portugués", "portugués": "Portugués",
    "french": "Francés", "fr": "Francés", "francés": "Francés",
    "german": "Alemán", "de": "Alemán", "italian": "Italiano", "it": "Italiano",
}
MESES = {
    "jan": 1, "january": 1, "ene": 1, "enero": 1, "feb": 2, "february": 2, "febrero": 2,
    "mar": 3, "march": 3, "marzo": 3, "apr": 4, "april": 4, "abr": 4, "abril": 4,
    "may": 5, "mayo": 5, "jun": 6, "june": 6, "junio": 6, "jul": 7, "july": 7, "julio": 7,
    "aug": 8, "august": 8, "ago": 8, "agosto": 8, "sep": 9, "sept": 9, "september": 9,
    "septiembre": 9, "setiembre": 9, "oct": 10, "october": 10, "octubre": 10,
    "nov": 11, "november": 11, "noviembre": 11, "dec": 12, "december": 12, "dic": 12, "diciembre": 12,
}


class ErrorCarga(RuntimeError):
    """Un registro no se pudo llenar o guardar; la tanda puede seguir."""


class CorteTanda(RuntimeError):
    """Algo hace dudar de todo lo que siga (fecha mal guardada, HTML desconocido)."""


# ------------------------------------------------------------------ texto


def sin_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar_titulo(texto: str) -> str:
    """Clave de comparacion: minusculas, sin acentos, sin LaTeX ni puntuacion."""
    texto = limpiar_latex(texto or "")
    return re.sub(r"[^a-z0-9]", "", sin_acentos(texto).lower())


def normalizar_nombre(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sin_acentos(texto or "").lower()).strip()


def a_latin1(texto: str) -> tuple[str, list[str]]:
    """Lleva a ISO-8859-1 lo que no entra. Devuelve el texto y los caracteres cambiados.

    SIGEVA sirve y guarda en ISO-8859-1: lo que no entra termina como entidad HTML
    en el CV impreso. Se informa cada reemplazo para que la persona lo revise.
    """
    salida, cambiados = [], []
    for c in (texto or "").translate(EQUIVALENTES_LATIN1):
        try:
            c.encode("latin-1")
            salida.append(c)
        except UnicodeEncodeError:
            base = "".join(b for b in unicodedata.normalize("NFKD", c)
                           if not unicodedata.combining(b) and b.encode("latin-1", "ignore"))
            salida.append(base or "?")
            cambiados.append(c)
    return "".join(salida), cambiados


_ACENTOS_LATEX = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303", "c": "\u0327"}


def limpiar_latex(texto: str) -> str:
    """Quita el marcado LaTeX habitual de BibTeX: llaves, acentos y comandos."""
    def acento(m: re.Match) -> str:
        return unicodedata.normalize("NFC", m.group(2) + _ACENTOS_LATEX[m.group(1)])

    texto = re.sub(r"\\([`'^\"~c])\s*\{?\s*([A-Za-z])\s*\}?", acento, texto)
    texto = texto.replace(r"\&", "&").replace(r"\%", "%").replace(r"\_", "_").replace("--", "-")
    # Dentro de $...$ los comandos son simbolos ($\mu$ -> mu); fuera, marcado que se descarta.
    texto = re.sub(r"\$([^$]*)\$", lambda m: re.sub(r"\\([A-Za-z]+)\s*", r"\1", m.group(1)), texto)
    texto = re.sub(r"\\[A-Za-z]+\s*", "", texto)
    texto = texto.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", texto).strip()


def mes_anio(valor: str | None) -> str | None:
    """Fecha a mm/aaaa. Sin mes conocido devuelve None: SIGEVA lo exige y no se estima."""
    valor = (valor or "").strip()
    if not valor:
        return None
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", valor)
    if m and 1 <= int(m.group(1)) <= 12:
        return f"{int(m.group(1)):02d}/{m.group(2)}"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", valor)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{int(m.group(2)):02d}/{m.group(3)}"
    m = re.fullmatch(r"(\d{4})-(\d{1,2})(?:-\d{1,2})?", valor)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{int(m.group(2)):02d}/{m.group(1)}"
    return None


def anio_de(valor: str | None) -> int | None:
    m = re.search(r"(\d{4})", valor or "")
    return int(m.group(1)) if m else None


def ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ BibTeX


def parsear_bibtex(texto: str) -> list[dict]:
    """Parser minimo de BibTeX: entradas con campos entre llaves, comillas o numeros."""
    entradas, i, n = [], 0, len(texto)
    while True:
        i = texto.find("@", i)
        if i < 0:
            break
        m = re.match(r"@\s*([A-Za-z]+)\s*[{(]", texto[i:])
        if not m:
            i += 1
            continue
        tipo = m.group(1).lower()
        i += m.end()
        if tipo in ("comment", "string", "preamble"):
            i = _saltar_bloque(texto, i - 1)
            continue
        coma = texto.find(",", i)
        if coma < 0:
            break
        clave = texto[i:coma].strip()
        i = coma + 1
        campos: dict[str, str] = {}
        while i < n:
            while i < n and texto[i] in " \t\r\n,":
                i += 1
            if i >= n or texto[i] in "})":
                i += 1
                break
            m = re.match(r"([A-Za-z][\w\-:.]*)\s*=\s*", texto[i:])
            if not m:
                i = _saltar_bloque(texto, i)
                break
            nombre = m.group(1).lower()
            i += m.end()
            valor, i = _leer_valor(texto, i)
            campos[nombre] = valor
        entradas.append({"tipo_entrada": tipo, "clave": clave, "campos": campos})
    return entradas


def _leer_valor(texto: str, i: int) -> tuple[str, int]:
    partes = []
    while i < len(texto):
        c = texto[i]
        if c == "{":
            fin = _saltar_bloque(texto, i)
            partes.append(texto[i + 1:fin - 1])
            i = fin
        elif c == '"':
            j, nivel = i + 1, 0
            while j < len(texto) and not (texto[j] == '"' and nivel == 0):
                nivel += texto[j] == "{"
                nivel -= texto[j] == "}"
                j += 1
            partes.append(texto[i + 1:j])
            i = j + 1
        else:
            m = re.match(r"[^,#}\s]+", texto[i:])
            if m:
                partes.append(m.group(0))
                i += m.end()
        while i < len(texto) and texto[i] in " \t\r\n":
            i += 1
        if i < len(texto) and texto[i] == "#":
            i += 1
            while i < len(texto) and texto[i] in " \t\r\n":
                i += 1
            continue
        break
    return "".join(partes).strip(), i


def _saltar_bloque(texto: str, i: int) -> int:
    """Desde una llave o parentesis de apertura, devuelve la posicion siguiente al cierre."""
    apertura = texto[i] if i < len(texto) else "{"
    cierre = ")" if apertura == "(" else "}"
    nivel = 0
    while i < len(texto):
        if texto[i] == apertura:
            nivel += 1
        elif texto[i] == cierre:
            nivel -= 1
            if nivel == 0:
                return i + 1
        i += 1
    return i


def separar_autores(valor: str) -> list[dict]:
    autores = []
    for crudo in re.split(r"\s+and\s+", valor or ""):
        nombre = limpiar_latex(crudo).strip()
        if not nombre or nombre.lower() == "others":
            continue
        if "," in nombre:
            apellido, _, nombres = nombre.partition(",")
        else:
            partes = nombre.split()
            apellido, nombres = partes[-1], " ".join(partes[:-1])
        autores.append({"apellido": apellido.strip(), "nombre": nombres.strip()})
    return autores


def _fecha_bib(campos: dict) -> str | None:
    if campos.get("date"):
        fecha = mes_anio(campos["date"])
        if fecha:
            return fecha
    anio, mes = campos.get("year", "").strip(), campos.get("month", "").strip().lower().rstrip(".")
    if not anio or not mes:
        return None
    numero = int(mes) if mes.isdigit() else MESES.get(mes)
    return f"{numero:02d}/{anio}" if numero and 1 <= numero <= 12 else None


def bib_a_registros(entradas: list[dict], idioma_defecto: str | None = None) -> tuple[list[dict], list[dict]]:
    """Convierte entradas BibTeX en registros de carga. No completa lo que el .bib no trae."""
    registros, descartes = [], []
    for e in entradas:
        c, tipo_bib = e["campos"], e["tipo_entrada"]
        if tipo_bib == "article":
            tipo = "articulo"
        elif tipo_bib in ("inproceedings", "conference"):
            tipo = "evento"
        else:
            descartes.append({"clave": e["clave"], "tipo_entrada": tipo_bib,
                              "motivo": "sin conversor automatico: cargar como 'generico' o a mano"})
            continue
        idioma = IDIOMAS_BIB.get((c.get("langid") or c.get("language") or "").strip().lower()) or idioma_defecto
        reg = {
            "clave": e["clave"], "tipo": tipo,
            "titulo": limpiar_latex(c.get("title", "")),
            "autores": separar_autores(c.get("author", "")),
            "anio": int(c["year"]) if c.get("year", "").strip().isdigit() else None,
            "idioma": idioma,
            "resumen": limpiar_latex(c.get("abstract", "")) or None,
            "palabras_clave": [k.strip() for k in re.split(r"[;,]", limpiar_latex(c.get("keywords", ""))) if k.strip()],
            "doi": c.get("doi", "").strip() or None,
            "url": c.get("url", "").strip() or None,
            "editorial": limpiar_latex(c.get("publisher", "")) or None,
            "en_prensa": bool(re.search(r"to appear|in press|en prensa", c.get("note", "") + c.get("pubstate", ""), re.I)),
        }
        if tipo == "articulo":
            reg.update({
                "revista": limpiar_latex(c.get("journaltitle") or c.get("journal", "")) or None,
                "issn": c.get("issn", "").strip() or None,
                "volumen": c.get("volume", "").strip() or None,
                "numero": (c.get("number") or c.get("issue") or "").strip() or None,
                "paginas": limpiar_latex(c.get("pages", "")) or None,
                "fecha_publicacion": _fecha_bib(c),
            })
        else:
            reg.update({
                "titulo_publicacion": limpiar_latex(c.get("booktitle", "")) or None,
                "reunion": limpiar_latex(c.get("eventtitle") or c.get("booktitle", "")) or None,
                "isbn": c.get("isbn", "").strip() or None,
                "ciudad_edicion": limpiar_latex(c.get("location") or c.get("address", "")) or None,
                "ciudad_evento": limpiar_latex(c.get("venue", "")) or None,
                "fecha_evento": mes_anio(c.get("eventdate", "")),
                "anio_publicacion": reg["anio"],
            })
        registros.append({k: v for k, v in reg.items() if v not in (None, "", [])} | {"en_prensa": reg["en_prensa"]})
    return registros, descartes


# ------------------------------------------------------------------ configuracion


def cargar_config(ruta: str | None) -> dict:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8")) if ruta else {}
    config = {
        "base": BASE_DEFECTO, "rol_banco_datos": ROL_BANCO_DATOS, "persona_id": "",
        "declarante": {"apellido": "", "nombre": ""}, "idioma_defecto": None,
        "area_conocimiento": {"campo": "", "subcampo": ""}, "tablas": dict(TABLAS_DEFECTO),
    }
    for clave, valor in datos.items():
        if isinstance(valor, dict) and isinstance(config.get(clave), dict):
            config[clave] = {**config[clave], **valor}
        else:
            config[clave] = valor
    config["base"] = str(config["base"]).rstrip("/") + "/"
    return config


def es_declarante(autor: dict, config: dict) -> bool:
    if "declarante" in autor:
        return bool(autor["declarante"])
    apellido = normalizar_nombre(config.get("declarante", {}).get("apellido", ""))
    return bool(apellido) and normalizar_nombre(autor.get("apellido", "")) == apellido


# ------------------------------------------------------------------ validacion


def _requeridos(reg: dict, campos: list[str]) -> list[str]:
    return [f"falta '{c}'" for c in campos if reg.get(c) in (None, "", [])]


def validar_registro(reg: dict, config: dict) -> tuple[list[str], list[str]]:
    """Errores bloquean la carga; avisos se muestran para revision humana."""
    errores, avisos = [], []
    tipo = reg.get("tipo")
    if tipo not in TIPOS:
        return [f"tipo desconocido '{tipo}' (usar {', '.join(TIPOS)})"], avisos
    if not reg.get("clave"):
        errores.append("falta 'clave' (identificador estable del registro)")
    if reg.get("en_prensa"):
        errores.append("en prensa: SIGEVA solo computa lo publicado; cargar cuando salga")
    archivo = reg.get("archivo")
    if archivo:
        ruta = Path(archivo)
        if not ruta.is_file():
            errores.append(f"archivo inexistente: {archivo}")
        elif ruta.stat().st_size > MAX_PDF_MB * 2**20:
            errores.append(f"archivo de {ruta.stat().st_size / 2**20:.1f} MB: SIGEVA acepta hasta {MAX_PDF_MB} "
                           "y con mas guarda sin error y sin registro (comprimir con Ghostscript)")
    if tipo == "generico":
        errores += _requeridos(reg, ["rubro", "url_alta", "url_lista", "campos", "buscar_en_lista"])
        if isinstance(reg.get("campos"), dict):
            for nombre, valor in reg["campos"].items():
                if not isinstance(valor, (str, int, float, bool, dict, list)):
                    errores.append(f"campo '{nombre}': valor no soportado")
        boton = reg.get("boton_guardar", "Guardar")
        if RE_BOTON_PROHIBIDO.search(boton):
            errores.append(f"boton_guardar '{boton}' no permitido: el script solo da altas nuevas")
        return errores, avisos

    errores += _requeridos(reg, ["titulo", "autores", "resumen", "idioma"])
    if not archivo:
        errores.append("falta 'archivo': SIGEVA exige el full text y sin el no guarda")
    area = reg.get("area_conocimiento") or config.get("area_conocimiento") or {}
    if not area.get("campo") or not area.get("subcampo"):
        errores.append("falta el area del conocimiento (config.area_conocimiento o registro)")
    autores = reg.get("autores") or []
    declarantes = [a for a in autores if es_declarante(a, config)]
    if autores and len(declarantes) != 1:
        errores.append(f"{len(declarantes)} autores marcados como declarante: tiene que haber exactamente uno")
    if declarantes and not config.get("persona_id"):
        avisos.append("sin persona_id en config: solo se puede marcar al declarante si el formulario usa el radio autorSel")
    if not reg.get("palabras_clave"):
        avisos.append("sin palabras clave")
    soporte = reg.get("soporte") or (["electronico"] if reg.get("url") or reg.get("doi") else ["impreso"])
    if "electronico" in soporte and not (reg.get("url") or reg.get("doi")):
        errores.append("soporte electronico sin URL ni DOI: SIGEVA lo rechaza")
    for campo in ("titulo", "resumen"):
        _, cambiados = a_latin1(str(reg.get(campo) or ""))
        if cambiados:
            avisos.append(f"{campo}: caracteres fuera de ISO-8859-1 reemplazados ({''.join(sorted(set(cambiados)))[:20]})")

    if tipo == "articulo":
        errores += _requeridos(reg, ["editorial", "pais_edicion"])
        if not (reg.get("publicacion_id") or reg.get("issn") or reg.get("revista")):
            errores.append("falta la revista: 'publicacion_id' del catalogo, 'issn' o 'revista'")
        if not mes_anio(reg.get("fecha_publicacion")):
            errores.append("falta 'fecha_publicacion' en mm/aaaa (no se estima el mes)")
        if reg.get("referato", True) is not True:
            errores.append("articulo sin referato: el script solo cubre 'con referato'; cargar a mano o como generico")
        if reg.get("version_adjunto", "postprint") not in VERSIONES_ADJUNTO:
            errores.append("version_adjunto debe ser 'postprint' o 'final' (SIGEVA no acepta preprint)")
        for a in autores:
            if not a.get("institucion_id"):
                errores.append(f"autor {a.get('apellido', '?')}: sin 'institucion_id'; SIGEVA exige filiacion por autor "
                               "en articulos (resolver con el catalogo o dar el alta a mano una vez)")
    elif tipo == "evento":
        errores += _requeridos(reg, ["titulo_publicacion", "tipo_publicacion", "reunion", "tipo_reunion",
                                     "pais_evento", "ciudad_evento", "pais_edicion", "editorial", "anio_publicacion"])
        if not mes_anio(reg.get("fecha_evento")):
            errores.append("falta 'fecha_evento' en mm/aaaa")
        if not reg.get("alcance") in ("nacional", "internacional"):
            errores.append("falta 'alcance': 'nacional' o 'internacional'")
    else:  # capitulo o libro
        errores += _requeridos(reg, ["editorial", "pais_edicion", "anio_publicacion", "isbn", "paginas_libro"])
        if tipo == "capitulo":
            errores += _requeridos(reg, ["titulo_libro", "tipo_parte", "paginas"])
            # SIGEVA lo exige al guardar aunque el formulario no lo marque con asterisco.
            if not reg.get("compiladores"):
                errores.append("falta 'compiladores': SIGEVA exige al menos un compilador/editor/organizador del libro")
        if reg.get("referato") not in (True, False):
            errores.append("falta 'referato': true o false (comite editorial/referato del libro)")
        roles = reg.get("rol") or ["autor"]
        if not roles or any(r not in ROLES for r in roles):
            errores.append(f"'rol' debe ser una lista con {', '.join(ROLES)}")
        for c in reg.get("compiladores") or []:
            if c.get("institucion") and not c.get("institucion_id"):
                avisos.append(f"compilador {c.get('apellido', '?')}: institucion sin id, se carga sin filiacion")
    if tipo != "articulo":
        if reg.get("isbn") and not re.fullmatch(r"[\dXx\-]{9,17}", reg["isbn"]):
            errores.append("isbn/issn con formato invalido: SIGEVA lo valida")
        for a in autores:
            if a.get("institucion") and not a.get("institucion_id"):
                avisos.append(f"autor {a.get('apellido', '?')}: institucion sin id, se carga sin filiacion")
    return errores, avisos


# ------------------------------------------------------------------ catalogo e inventario


def resolver_con_catalogo(reg: dict, catalogo: dict) -> list[str]:
    """Completa ids de revista e instituciones solo con coincidencia exacta. Devuelve avisos.

    Una filiacion equivocada en una declaracion jurada es peor que una sin resolver:
    no hay coincidencia difusa.
    """
    avisos = []
    instituciones = {normalizar_nombre(k): v for k, v in (catalogo.get("instituciones") or {}).items()}
    for v in list(instituciones.values()):
        instituciones.setdefault(normalizar_nombre(v.get("label", "")), v)
    for autor in reg.get("autores") or []:
        nombre = autor.get("institucion")
        if autor.get("institucion_id") or not nombre:
            continue
        hallada = instituciones.get(normalizar_nombre(nombre))
        if hallada:
            autor.update({"institucion_id": str(hallada["id"]), "institucion": hallada["label"],
                          "institucion_otra": bool(hallada.get("otra"))})
        else:
            avisos.append(f"institucion fuera del catalogo local: {nombre} (buscarla con el comando 'institucion' antes de dejarla sin filiacion)")
    if reg.get("tipo") == "articulo" and not reg.get("publicacion_id"):
        revistas = (catalogo.get("revistas") or {}).values()
        issn = re.sub(r"[^0-9Xx]", "", reg.get("issn") or "").upper()
        por_issn = [r for r in revistas if issn and re.sub(r"[^0-9Xx]", "", r.get("issn") or "").upper() == issn]
        por_nombre = [r for r in revistas if reg.get("revista") and normalizar_nombre(r.get("label")) == normalizar_nombre(reg["revista"])]
        elegida = por_issn[0] if len(por_issn) == 1 else (por_nombre[0] if len(por_nombre) == 1 and not por_issn else None)
        if elegida:
            reg["publicacion_id"], reg["revista"] = str(elegida["id"]), elegida["label"]
    return avisos


class _ParserTablas(HTMLParser):
    """Extrae tablas de displaytag: cabecera, filas, enlaces de edicion e id de tabla."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tablas: list[dict] = []
        self._pila: list[dict] = []
        self._seccion = ""
        self._celda: list[str] | None = None
        self._fila: dict | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._pila.append({"id": None, "cabecera": [], "filas": [], "_seccion": ""})
            return
        if not self._pila:
            return
        t = self._pila[-1]
        if tag in ("thead", "tbody", "tfoot"):
            t["_seccion"] = tag
        elif tag == "tr":
            self._fila = {"celdas": [], "editar": "", "enlaces": []}
        elif tag in ("td", "th"):
            self._celda = []
        elif tag == "a":
            href = a.get("href") or ""
            # Solo el parametro de orden propio identifica la tabla: desde la pagina 2 (o con un
            # d-<id>-p en la query) los enlaces de todas las tablas copian el -p de las demas.
            m = re.search(r"d-(\d+)-s=", href)
            if m and t["_seccion"] == "thead" and not t["id"]:
                t["id"] = m.group(1)
            if self._fila is not None and href:
                self._fila["enlaces"].append(href)
                if re.search(r"action=editar|accion=editar", href, re.I):
                    self._fila["editar"] = self._fila["editar"] or href

    def handle_endtag(self, tag):
        if not self._pila:
            return
        t = self._pila[-1]
        if tag in ("td", "th") and self._celda is not None and self._fila is not None:
            self._fila["celdas"].append(re.sub(r"\s+", " ", "".join(self._celda)).strip())
            self._celda = None
        elif tag == "tr" and self._fila is not None:
            if t["_seccion"] == "thead" or (not t["cabecera"] and not self._fila["editar"] and t["_seccion"] != "tbody"):
                t["cabecera"] = self._fila["celdas"]
            elif self._fila["celdas"]:
                t["filas"].append(self._fila)
            self._fila = None
        elif tag == "table":
            terminada = self._pila.pop()
            terminada.pop("_seccion", None)
            self.tablas.append(terminada)

    def handle_data(self, data):
        if self._celda is not None:
            self._celda.append(data)


def parsear_tablas(html: str) -> list[dict]:
    p = _ParserTablas()
    p.feed(html)
    p.close()
    return p.tablas


def fila_coincide(titulo_lista: str, titulo: str) -> bool:
    """Compara un titulo de la lista (puede venir truncado con '...') con el registro."""
    crudo = (titulo_lista or "").strip()
    truncado = crudo.endswith("...")
    clave_lista = normalizar_titulo(crudo.rstrip(". ") if truncado else crudo)
    clave = normalizar_titulo(titulo)
    if not clave or not clave_lista:
        return False
    return clave_lista == clave or (truncado and len(clave_lista) >= 25 and clave.startswith(clave_lista))


def buscar_todas_en_tabla(tabla: dict, titulo: str) -> list[dict]:
    cab = [sin_acentos(c).lower() for c in tabla.get("cabecera", [])]
    i_tit = next((i for i, c in enumerate(cab) if c.startswith("titulo")), None)
    i_anio = next((i for i, c in enumerate(cab) if c == "ano" or c.startswith("ano ")), None)
    if i_tit is None:
        raise CorteTanda("la tabla de la lista no tiene columna Titulo: ¿cambio el HTML de SIGEVA?")
    halladas = []
    for fila in tabla.get("filas", []):
        celdas = fila["celdas"]
        # La primera columna de displaytag (Editar|Borrar) puede faltar en la cabecera.
        desfase = len(celdas) - len(cab)
        if desfase < 0:  # "No hay registros cargados." y filas de agrupacion: no son registros
            continue
        if i_tit + desfase < len(celdas) and fila_coincide(celdas[i_tit + desfase], titulo):
            anio = celdas[i_anio + desfase] if i_anio is not None and i_anio + desfase < len(celdas) else ""
            halladas.append({"titulo": celdas[i_tit + desfase], "anio": anio_de(anio), "editar": fila["editar"]})
    return halladas


def buscar_en_tabla(tabla: dict, titulo: str) -> dict | None:
    halladas = buscar_todas_en_tabla(tabla, titulo)
    return halladas[0] if halladas else None


def cruzar_con_inventario(reg: dict, inventario: dict) -> dict | None:
    tabla = (inventario.get("tablas") or {}).get(reg.get("tipo"))
    if not tabla:
        return None
    return buscar_en_tabla(tabla, reg.get("titulo", ""))


def preparar(registros: list[dict], config: dict, catalogo: dict, inventario: dict | None) -> dict:
    listos, bloqueados, ya_cargados = [], [], []
    for original in registros:
        reg = json.loads(json.dumps(original))
        avisos = resolver_con_catalogo(reg, catalogo) if catalogo else []
        errores, mas_avisos = validar_registro(reg, config)
        avisos += mas_avisos
        en_sigeva = cruzar_con_inventario(reg, inventario) if inventario and reg.get("tipo") in TIPOS_PUBLICACION else None
        if en_sigeva:
            ya_cargados.append({"clave": reg.get("clave"), "titulo": reg.get("titulo"), "en_sigeva": en_sigeva})
        elif errores:
            bloqueados.append({"clave": reg.get("clave"), "titulo": reg.get("titulo") or reg.get("rubro"),
                               "errores": errores, "avisos": avisos})
        else:
            listos.append(reg | {"_avisos": avisos} if avisos else reg)
    return {"listos": listos, "bloqueados": bloqueados, "ya_cargados": ya_cargados,
            "inventario_usado": bool(inventario), "inventario_capturado": (inventario or {}).get("capturado_en_utc")}


# ------------------------------------------------------------------ estado y recibos


class Estado:
    """Log append-only (JSON Lines): reanudar sin repetir y dejar rastro auditable."""

    def __init__(self, ruta: Path) -> None:
        self.ruta = ruta

    def registrar(self, entrada: dict) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**entrada, "cuando_utc": ahora_utc()}, ensure_ascii=False) + "\n")

    def guardados(self) -> set[str]:
        if not self.ruta.exists():
            return set()
        claves = set()
        for linea in self.ruta.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if e.get("resultado") in ("guardado", "ya-estaba"):
                claves.add(e.get("clave"))
        return claves


def escribir_json(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, ruta)


def leer_json(ruta: Path | str | None, defecto=None):
    if not ruta or not Path(ruta).exists():
        return defecto
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def log(mensaje: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {mensaje}", file=sys.stderr, flush=True)


# ------------------------------------------------------------------ navegador

JS_DESCARGAR = r"""async (url) => {
    const r = await fetch(url, {credentials: 'same-origin'});
    const buf = await r.arrayBuffer();
    const tipo = r.headers.get('content-type') || '';
    const m = /charset=([\w-]+)/i.exec(tipo);
    return new TextDecoder(m ? m[1] : 'iso-8859-1').decode(buf);
}"""

JS_CONTROLES = r"""() => {
    const etiqueta = (el) => {
        const lbl = el.id && document.querySelector(`label[for="${el.id}"]`);
        if (lbl) return lbl.innerText.trim();
        const td = el.closest('td');
        const prev = td && td.previousElementSibling;
        return prev ? prev.innerText.replace(/\s+/g, ' ').trim() : '';
    };
    return Array.from(document.querySelectorAll('input, select, textarea, button')).map((el, i) => ({
        orden: i, tag: el.tagName.toLowerCase(), tipo: (el.type || '').toLowerCase(), name: el.name || '',
        id: el.id || '', valor: el.type === 'file' ? '' : (el.value || ''), etiqueta: etiqueta(el),
        visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
        checked: !!el.checked, datepicker: el.classList.contains('hasDatepicker'),
        obligatorio: /\*/.test(etiqueta(el)),
        opciones: el.tagName === 'SELECT' ? Array.from(el.options).map(o => [o.value, o.text.trim()]) : undefined,
    }));
}"""

JS_FIJAR_FECHAS = r"""(fechas) => {
    const $ = window.jQuery;
    if ($) $('.hasDatepicker').each(function () { try { $(this).datepicker('hide'); } catch (e) {} });
    if (document.activeElement) document.activeElement.blur();
    const leido = {};
    for (const [nombre, valor] of Object.entries(fechas)) {
        const p = valor.split('/');
        const d = p.length === 2 ? new Date(+p[1], +p[0] - 1, 1) : new Date(+p[0], 0, 1);
        document.getElementsByName(nombre).forEach(el => {
            if (el.type !== 'hidden' && $ && $(el).hasClass('hasDatepicker')) $(el).datepicker('setDate', d);
            el.value = valor;
        });
        leido[nombre] = Array.from(document.getElementsByName(nombre)).map(e => e.value);
    }
    return leido;
}"""

# Autores y compiladores usan los mismos campos con distinto prefijo ("autor"/"compilador"):
# preSubmit() los serializa con participacionToJson(prefijo) en <prefijo>JSON.
JS_INYECTAR_PERSONAS = r"""([personas, personaId, p]) => {
    const filas = () => document.getElementsByName(p + 'ParticipacionLabel');
    const nuevo = document.getElementsByName(p + 'Nuevo')[0];
    for (let i = 0; filas().length < personas.length && nuevo && i < 200; i++) nuevo.click();
    const esc = (v) => String(v).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
    const oculto = (n, v) => `<input type="hidden" name="${p}${n}" value="${esc(v)}">`;
    personas.forEach((a, i) => {
        const campos = filas();
        if (i >= campos.length) return;
        campos[i].value = a.nombre;
        campos[i].dispatchEvent(new Event('change', {bubbles: true}));
        if (!a.id) return;
        // preSubmit() serializa solo las filas del <tbody> de la tabla anidada de cada persona.
        const tabla = campos[i].closest('table');
        if (!tabla) return;
        const cuerpo = tabla.tBodies[0] || tabla.appendChild(document.createElement('tbody'));
        cuerpo.insertAdjacentHTML('beforeend', `<tr class="odd"><td colspan="2"><div>${esc(a.label)}</div>
            ${oculto('OrganizacionLabel', a.label)}${oculto('OrganizacionId', a.id)}
            ${oculto('ParticipacionOrganizacionId', '')}${oculto('ParticipacionId', '')}
            ${oculto('isOtraOrganizacion', a.otra ? 'true' : 'false')}${oculto('PaisId', '')}
            ${oculto('ProvinciaId', '')}${oculto('RelacionadaId', '')}${oculto('Nivel', '')}
            ${oculto('Ruta', a.label)}${oculto('TipoId', '')}${oculto('AffiliationId', '')}
            </td></tr>`);
    });
    const idx = personas.findIndex(a => a.propio);
    let marcado = false;
    if (idx >= 0) {
        const radios = document.getElementsByName(p + 'Sel');
        const ids = document.getElementsByName(p + 'PersonaId');
        if (radios[idx]) { radios[idx].checked = true; radios[idx].dispatchEvent(new Event('change', {bubbles: true})); marcado = true; }
        if (ids[idx] && personaId) { ids[idx].value = personaId; marcado = true; }
    }
    const leidos = Array.from(filas()).slice(0, personas.length).map(c => {
        const t = c.closest('table');
        const orgs = t && t.tBodies[0] ? Array.from(t.tBodies[0].querySelectorAll(`input[name="${p}OrganizacionId"]`)).map(e => e.value) : [];
        return {nombre: c.value, ids: orgs};
    });
    return {filas: filas().length, declarante: idx, marcado, leidos};
}"""

JS_LEER_CAMPOS = r"""async ([url, nombres]) => {
    const r = await fetch(url, {credentials: 'same-origin'});
    const buf = await r.arrayBuffer();
    const tipo = r.headers.get('content-type') || '';
    const m = /charset=([\w-]+)/i.exec(tipo);
    const doc = new DOMParser().parseFromString(new TextDecoder(m ? m[1] : 'iso-8859-1').decode(buf), 'text/html');
    const out = {};
    for (const n of nombres) {
        out[n] = Array.from(doc.getElementsByName(n)).filter(e => !((e.type === 'checkbox' || e.type === 'radio') && !e.checked))
            .map(e => e.tagName === 'SELECT' ? (e.selectedOptions[0] || {}).value || '' : e.value);
    }
    return out;
}"""


def _playwright():
    try:
        from playwright.sync_api import TimeoutError as PWTimeout
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Falta Playwright: python -m pip install -r assets/requirements.txt && python -m playwright install chromium")
    return sync_playwright, PWTimeout


class Sesion:
    """Navegador con contexto limpio, dentro del rol Banco de Datos."""

    def __init__(self, config: dict, trabajo: Path, headless: bool = False) -> None:
        self.config, self.trabajo, self.headless = config, trabajo, headless
        self.base = config["base"]
        self.capturas = trabajo / "capturas"
        self.dialogos: list[str] = []
        self.aceptar_dialogos = False

    def url(self, ruta: str) -> str:
        return urljoin(self.base, ruta)

    def __enter__(self) -> "Sesion":
        sync_playwright, self.PWTimeout = _playwright()
        self._pw = sync_playwright().start()
        # Contexto nuevo en cada corrida: el estado acumulado de sesion traba a SIGEVA.
        self._nav = self._pw.chromium.launch(headless=self.headless)
        self._ctx = self._nav.new_context(viewport={"width": 1400, "height": 1000}, accept_downloads=False)
        self.page = self._ctx.new_page()
        self.page.on("dialog", self._dialogo)
        return self

    def __exit__(self, *exc) -> None:
        try:
            self._ctx.close()
            self._nav.close()
        finally:
            self._pw.stop()

    def _dialogo(self, dialogo) -> None:
        self.dialogos.append(dialogo.message)
        log(f"    dialogo de SIGEVA: {dialogo.message[:120]}")
        if self.aceptar_dialogos:
            dialogo.accept()
        else:
            dialogo.dismiss()

    def captura(self, nombre: str) -> str:
        self.capturas.mkdir(parents=True, exist_ok=True)
        ruta = self.capturas / (re.sub(r"[^\w.-]+", "_", nombre)[:80] + ".png")
        try:
            self.page.screenshot(path=str(ruta), full_page=True)
        except Exception as e:  # la captura nunca debe tapar el error original
            log(f"    no pude guardar la captura: {str(e).splitlines()[0][:80]}")
        return str(ruta)

    def iniciar(self) -> None:
        page = self.page
        page.goto(self.url(RUTAS["intranet"]), wait_until="domcontentloaded", timeout=60_000)
        selector_rol = 'a[onclick*="redirect("]'
        if page.locator(selector_rol).count():
            log("Sesion ya autenticada.")
        else:
            usuario, clave = os.environ.get("SIGEVA_USER"), os.environ.get("SIGEVA_PASS")
            if usuario and clave:
                self._ingresar(usuario, clave, selector_rol)
            else:
                print("\n" + "=" * 70, file=sys.stderr)
                print("  Ingresa tu usuario y contrasena en la ventana de Chromium.", file=sys.stderr)
                print(f"  El script no los ve ni los guarda. Espera hasta {ESPERA_LOGIN_MS // 60_000} minutos.", file=sys.stderr)
                print("=" * 70 + "\n", file=sys.stderr)
                try:
                    # Los enlaces de rol estan en un menu colapsado: 'attached', no 'visible'.
                    page.wait_for_selector(selector_rol, state="attached", timeout=ESPERA_LOGIN_MS)
                except self.PWTimeout:
                    raise SystemExit("No detecte la sesion iniciada.") from None
            log("Sesion iniciada.")
        page.goto(self.url(RUTAS["intranet"]), wait_until="domcontentloaded")
        rol = int(self.config["rol_banco_datos"])
        if not page.locator(f'a[onclick*="redirect({rol})"]').count():
            raise SystemExit(f"La cuenta no tiene el rol {rol} (Usuario de Banco de Datos de Actividades de CyT).")
        page.evaluate(f"redirect({rol})")
        page.wait_for_url("**/eva/**", timeout=60_000)
        log("Dentro del Banco de Datos.")

    def _ingresar(self, usuario: str, clave: str, selector_rol: str) -> None:
        """Ingreso por el CAS distinguiendo "clave rechazada" de "CAS colgado".

        SIGEVA bloquea la cuenta tras varios ingresos fallidos: si el CAS muestra un rechazo se corta
        sin reintentar. Si en cambio el CAS no responde (paso varias veces: la pagina queda colgada y
        ni la captura carga), puede que el ingreso igual haya prosperado: primero se espera y se
        recarga la intranet; recien si vuelve al formulario se intenta UNA vez mas.
        """
        page = self.page
        for intento in (1, 2):
            page.wait_for_selector("input#username", timeout=60_000)
            page.fill("input#username", usuario)
            page.fill("input#password", clave)
            # No esperar la navegacion del click: el CAS a veces la demora mas de 30 s.
            page.click('button[name="submitBtn"]', no_wait_after=True)
            try:
                page.wait_for_selector(selector_rol, state="attached", timeout=90_000)
                return
            except self.PWTimeout:
                pass
            try:
                texto = page.inner_text("body", timeout=10_000)
            except Exception:
                texto = ""
            if RE_LOGIN_RECHAZADO.search(texto):
                captura = self.captura("login-rechazado")
                raise SystemExit(f"El CAS rechazo el ingreso: no se reintenta para no bloquear la cuenta. Revisar {captura}.")
            log(f"    el CAS no respondio en 90 s (intento {intento}/2); espero y recargo la intranet")
            page.wait_for_timeout(60_000)
            try:
                page.goto(self.url(RUTAS["intranet"]), wait_until="domcontentloaded", timeout=90_000)
                if page.locator(selector_rol).count():
                    return  # el ingreso habia prosperado aunque la pagina no lo mostrara
            except self.PWTimeout:
                pass
        captura = self.captura("login-fallido")
        raise SystemExit(f"El CAS de CONICET no respondio en dos intentos (quede en {page.url[:90]}). Probar entrar a mano "
                         f"en el navegador; si funciona, reintentar mas tarde. Captura: {captura}")

    def viva(self) -> bool:
        return "/eva/" in self.page.url and "login" not in self.page.url.lower()

    def evaluar(self, js: str, arg=None):
        """page.evaluate tolerante a la navegacion que SIGEVA sigue haciendo despues de Guardar."""
        for intento in range(5):
            try:
                self.page.wait_for_load_state("load", timeout=45_000)
                return self.page.evaluate(js, arg)
            except Exception as e:
                if "context was destroyed" not in str(e) and "navigat" not in str(e).lower() or intento == 4:
                    raise
                self.page.wait_for_timeout(1_500)

    def descargar(self, ruta: str) -> str:
        return self.evaluar(JS_DESCARGAR, self.url(ruta))

    def leer_tabla(self, ruta_lista: str, id_tabla: str | None) -> dict | None:
        """Recorre todas las paginas de una tabla de displaytag. None si la tabla no existe."""
        combinada, vistas = None, set()
        for pagina in range(1, MAX_PAGINAS_LISTA + 1):
            sep = "&" if "?" in ruta_lista else "?"
            ruta = f"{ruta_lista}{sep}d-{id_tabla}-p={pagina}" if id_tabla else ruta_lista
            tablas = parsear_tablas(self.descargar(ruta))
            tabla = next((t for t in tablas if t["id"] == id_tabla), None) if id_tabla else _tabla_principal(tablas)
            if tabla is None:
                return combinada
            if combinada is None:
                combinada = {"id": tabla["id"], "cabecera": tabla["cabecera"], "filas": []}
            nuevas = 0
            for fila in tabla["filas"]:
                clave = fila["editar"] or "|".join(fila["celdas"])
                if clave not in vistas:
                    vistas.add(clave)
                    combinada["filas"].append(fila)
                    nuevas += 1
            if not nuevas or not id_tabla:
                break
        return combinada

    def leer_campos(self, ruta: str, nombres: list[str]) -> dict:
        return self.evaluar(JS_LEER_CAMPOS, [self.url(ruta if "/" in ruta else "eva/" + ruta), nombres])


def _tabla_principal(tablas: list[dict]) -> dict | None:
    con_filas = [t for t in tablas if any(f["editar"] for f in t["filas"])]
    return max(con_filas, key=lambda t: len(t["filas"])) if con_filas else (tablas[0] if tablas else None)


def _ruta_eva(href: str) -> str:
    """Los enlaces de las listas son relativos a /eva/."""
    if href.startswith("http") or href.startswith("/"):
        return href
    return href if href.startswith("eva/") else "eva/" + href


# ------------------------------------------------------------------ llenado


class Formulario:
    """Primitivas de llenado que respetan las trampas de SIGEVA."""

    def __init__(self, sesion: Sesion) -> None:
        self.s = sesion
        self.page = sesion.page

    def _loc(self, nombre: str):
        visibles = self.page.locator(f'[name="{nombre}"]:not([type="hidden"])')
        return visibles if visibles.count() else self.page.locator(f'[name="{nombre}"]')

    def existe(self, nombre: str) -> bool:
        return self.page.locator(f'[name="{nombre}"]').count() > 0

    def texto(self, nombre: str, valor, obligatorio: bool = True) -> None:
        if valor in (None, ""):
            return
        loc = self._loc(nombre)
        if not loc.count():
            if obligatorio:
                raise ErrorCarga(f"no encontre el campo '{nombre}' en el formulario")
            return
        texto, _ = a_latin1(str(valor))
        loc.first.fill(texto)

    def opciones(self, nombre: str) -> list[list[str]]:
        return self.page.evaluate(
            """(n) => { const e = document.querySelector(`select[name="${n}"]`);
                        return e ? Array.from(e.options).map(o => [o.value, o.text.trim()]) : []; }""", nombre)

    def elegir(self, nombre: str, *, valor: str | None = None, etiqueta: str | None = None) -> str:
        """select_option real (Struts no registra asignaciones por JavaScript)."""
        opciones = self.opciones(nombre)
        if not opciones:
            raise ErrorCarga(f"no encontre el combo '{nombre}'")
        if etiqueta is not None:
            buscada = normalizar_nombre(etiqueta)
            exactas = [v for v, t in opciones if normalizar_nombre(t) == buscada]
            if len(exactas) != 1:
                disponibles = ", ".join(t for v, t in opciones if v and not v.startswith("-"))[:300]
                raise ErrorCarga(f"'{etiqueta}' no es una opcion unica de '{nombre}'. Opciones: {disponibles}")
            valor = exactas[0]
        if valor is None or not any(v == str(valor) for v, _ in opciones):
            raise ErrorCarga(f"el valor '{valor}' no esta en '{nombre}'")
        if str(valor).startswith("-"):
            raise ErrorCarga(f"'{nombre}': los valores negativos son encabezados deshabilitados")
        self.page.locator(f'select[name="{nombre}"]').first.select_option(str(valor), timeout=10_000)
        return str(valor)

    def marcar(self, nombre: str, valor: str) -> None:
        loc = self.page.locator(f'input[name="{nombre}"][value="{valor}"]')
        if not loc.count():
            raise ErrorCarga(f"no encontre la opcion {nombre}={valor}")
        loc.first.check()

    def casilla(self, nombre: str, marcada: bool = True) -> None:
        loc = self.page.locator(f'input[name="{nombre}"]')
        if not loc.count():
            raise ErrorCarga(f"no encontre la casilla '{nombre}'")
        loc.first.set_checked(marcada)

    def fijar_fechas(self, fechas: dict[str, str]) -> None:
        """Datepicker de jQuery UI: fill() se pisa al perder el foco; setDate no."""
        if not fechas:
            return
        leidas = self.page.evaluate(JS_FIJAR_FECHAS, fechas)
        for nombre, valor in fechas.items():
            if not leidas.get(nombre) or any(v != valor for v in leidas[nombre]):
                raise ErrorCarga(f"la fecha {nombre} quedo {leidas.get(nombre)} en vez de {valor}")

    def area(self, campo: str, subcampo: str) -> None:
        self.elegir("campo_0", valor=str(campo))
        # campo_0_0 llega por AJAX: se espera la opcion buscada.
        hallado: list[str] = []
        opciones: list[list[str]] = []
        for _ in range(20):
            self.page.wait_for_timeout(300)
            opciones = self.opciones("campo_0_0")
            hallado = [v for v, t in opciones if v == str(subcampo)] or \
                      [v for v, t in opciones if not str(subcampo).isdigit() and normalizar_nombre(str(subcampo)) in normalizar_nombre(t)]
            if len(hallado) == 1:
                self.elegir("campo_0_0", valor=hallado[0])
                return
            if len(hallado) > 1:
                break  # ya cargo y es ambiguo: esperar no lo resuelve
        reales = [(v, t[:60]) for v, t in opciones if v and not v.startswith("-")]
        if len(hallado) > 1:
            candidatas = [(v, t[:60]) for v, t in opciones if v in hallado]
            raise ErrorCarga(f"el subcampo '{subcampo}' es ambiguo en el area {campo}; usar el value. Coinciden: {candidatas}")
        raise ErrorCarga(f"no aparecio el subcampo '{subcampo}' del area {campo}. Opciones: {reales or 'ninguna (AJAX sin respuesta)'}")

    def palabras(self, palabras: list[str]) -> list[str]:
        campos = self.page.locator('input[name="palabraLabel"]')
        for i, palabra in enumerate(palabras[:campos.count()]):
            campos.nth(i).fill(a_latin1(palabra.upper())[0])
        return [f"entraron {campos.count()} de {len(palabras)} palabras clave"] if len(palabras) > campos.count() else []

    def adjuntar(self, ruta: str, version: str | None) -> None:
        if not self.existe("theFile"):
            raise ErrorCarga("el formulario no tiene campo de archivo (theFile)")
        self.page.locator('input[name="theFile"]').first.set_input_files(ruta)
        if version and self.existe("tipoAdjunto"):
            patron = re.compile(VERSIONES_ADJUNTO[version], re.I)
            hallados = [v for v, t in self.opciones("tipoAdjunto") if v and v != "-1" and patron.search(t)]
            if len(hallados) != 1:
                raise ErrorCarga(f"no encontre una unica version de adjunto '{version}' en tipoAdjunto")
            self.elegir("tipoAdjunto", valor=hallados[0])

    def subir_fine_uploader(self, ruta: str) -> None:
        """Libros: el full text va por un uploader AJAX (qqfile) que sube el archivo apenas se elige."""
        if not self.existe("qqfile"):
            raise ErrorCarga("el formulario no tiene el uploader de full text (qqfile)")
        self.page.locator('input[name="qqfile"]').first.set_input_files(ruta)
        try:
            self.page.wait_for_selector(".qq-upload-success, .qq-upload-fail", timeout=180_000)
        except self.s.PWTimeout:
            raise ErrorCarga("el uploader del full text no termino en 3 minutos") from None
        if self.page.locator(".qq-upload-fail").count():
            raise ErrorCarga("SIGEVA rechazo el archivo en el uploader: " + self.page.inner_text(".qq-upload-fail")[:160])

    def valor(self, nombre: str) -> str:
        loc = self._loc(nombre)
        return loc.first.input_value() if loc.count() else ""


def _personas_para_inyectar(personas: list[dict], config: dict) -> list[dict]:
    datos = []
    for a in personas:
        nombre, _ = a_latin1(f"{a.get('apellido', '')}, {a.get('nombre', '')}".strip(", "))
        datos.append({"nombre": nombre, "propio": es_declarante(a, config),
                      "id": str(a.get("institucion_id") or ""), "label": a_latin1(a.get("institucion") or "")[0],
                      "otra": bool(a.get("institucion_otra"))})
    return datos


def cargar_personas(f: Formulario, personas: list[dict], config: dict, prefijo: str = "autor") -> list[str]:
    """Autores (exigen un declarante) o compiladores (lo marcan solo si quien declara esta entre ellos)."""
    datos = _personas_para_inyectar(personas, config)
    r = f.page.evaluate(JS_INYECTAR_PERSONAS, [datos, str(config.get("persona_id") or ""), prefijo])
    if r["filas"] < len(datos):
        raise ErrorCarga(f"entraron {r['filas']} de {len(datos)} {prefijo}es")
    if prefijo == "autor" and (r["declarante"] < 0 or not r["marcado"]):
        raise ErrorCarga("no pude marcar al autor declarante (revisar persona_id en config)")
    for esperado, leido in zip(datos, r["leidos"], strict=False):
        if leido["nombre"] != esperado["nombre"] or (esperado["id"] and esperado["id"] not in leido["ids"]):
            raise ErrorCarga(f"{prefijo} {esperado['nombre']} no quedo como se esperaba: {leido}")
    return []


def cargar_autores(f: Formulario, reg: dict, config: dict) -> list[str]:
    return cargar_personas(f, reg["autores"], config, "autor")


def _soporte(f: Formulario, reg: dict) -> None:
    enlace = reg.get("url") or (f"https://doi.org/{reg['doi']}" if reg.get("doi") else "")
    soporte = reg.get("soporte") or (["electronico"] if enlace else ["impreso"])
    if not f.existe("tipoSoporteChecked"):
        return
    for nombre, valor in SOPORTE.items():
        loc = f.page.locator(f'input[name="tipoSoporteChecked"][value="{valor}"]')
        if loc.count():
            loc.first.set_checked(nombre in soporte)
    if "electronico" in soporte:
        f.texto("web", enlace[:250], obligatorio=False)


def _comunes(f: Formulario, reg: dict, config: dict, adjuntar: bool = True) -> list[str]:
    """Campos comunes a las publicaciones. Van despues de autores: el buscador re-renderiza."""
    if not f.existe("idioma"):
        raise ErrorCarga(f"el formulario no esta donde se esperaba (quede en {f.page.url.rsplit('/', 1)[-1][:60]})")
    f.elegir("idioma", etiqueta=reg["idioma"])
    f.texto("hdnresumen", reg["resumen"])
    area = reg.get("area_conocimiento") or config["area_conocimiento"]
    f.area(area["campo"], area["subcampo"])
    avisos = f.palabras(reg.get("palabras_clave") or [])
    if adjuntar:
        f.adjuntar(reg["archivo"], reg.get("version_adjunto", "postprint") if reg["tipo"] == "articulo" else None)
    return avisos


def _ir_al_alta_articulo(s: Sesion) -> None:
    page = s.page
    for intento in range(1, 4):
        page.goto(s.url(RUTAS["alta_articulo"]), wait_until="domcontentloaded")
        try:
            # "Omitir" saltea la precarga por DOI, que es intermitente y deja campos vacios.
            page.wait_for_selector('input[type="submit"][value="Omitir"]', state="attached", timeout=20_000)
            page.click('input[type="submit"][value="Omitir"]')
            page.wait_for_selector('input[name="bissn"]', state="attached", timeout=45_000)
            return
        except s.PWTimeout:
            log(f"    SIGEVA no respondio al abrir el alta ({intento}/3)")
            page.wait_for_timeout(8_000)
    raise ErrorCarga("SIGEVA no abrio el formulario de articulo")


def _elegir_revista(f: Formulario, reg: dict) -> list[str]:
    page = f.page
    if reg.get("publicacion_id"):
        page.evaluate("""([id, label]) => {
            document.getElementsByName('publicacionId').forEach(e => e.value = id);
            document.getElementsByName('srevista').forEach(e => e.value = label);
        }""", [str(reg["publicacion_id"]), a_latin1(reg.get("revista") or "")[0]])
        return []
    issn = (reg.get("issn") or "").strip()
    if issn:
        f.texto("bissn", issn)
        page.click('input[value="Buscar por ISSN / e-ISSN"]')
    else:
        f.texto("brevista", reg["revista"][:60])
        page.click('input[value="Buscar por Nombre"]')
    page.wait_for_selector('input[type="submit"][value="Seleccionar"]', state="attached", timeout=45_000)
    candidatas = page.evaluate("""() => Array.from(document.getElementsByName('idPublicacion')).map(e => ({
        valor: e.value, texto: (e.closest('tr') || e.parentElement).innerText.replace(/\\s+/g, ' ').trim()}))""")
    if issn:
        clave = re.sub(r"[^0-9X]", "", issn.upper())
        coinciden = [c for c in candidatas if clave in re.sub(r"[^0-9X]", "", c["texto"].upper())]
        candidatas = coinciden or candidatas
    avisos = []
    if len(candidatas) == 1:
        page.locator(f'input[name="idPublicacion"][value="{candidatas[0]["valor"]}"]').first.check()
    elif not candidatas and issn and reg.get("revista_otra_autorizada"):
        page.check('input[name="otraRevistaSeleccionada"]')
        f.texto("botrarevista", reg.get("revista", "")[:120])
        f.texto("botroissn", issn)
        avisos.append("revista dada de alta como 'otra' (no estaba en el catalogo)")
    elif not candidatas:
        raise ErrorCarga("la revista no esta en el catalogo de SIGEVA; para darla de alta como 'otra' "
                         "hace falta ISSN y 'revista_otra_autorizada': true en el registro")
    else:
        opciones = "; ".join(c["texto"][:70] for c in candidatas[:5])
        raise ErrorCarga(f"{len(candidatas)} revistas coinciden; fijar 'publicacion_id'. Candidatas: {opciones}")
    page.click('input[type="submit"][value="Seleccionar"]')
    page.wait_for_selector('input[name="produccion"]', state="attached", timeout=45_000)
    return avisos


def llenar_articulo(s: Sesion, reg: dict, config: dict) -> tuple[list[str], dict]:
    _ir_al_alta_articulo(s)
    f = Formulario(s)
    avisos = _elegir_revista(f, reg)
    f.texto("editorial", reg["editorial"])
    f.elegir("pais", etiqueta=reg["pais_edicion"])
    f.texto("lugarEdicion", reg.get("ciudad_edicion"), obligatorio=False)
    f.texto("produccion", reg["titulo"])
    for campo, clave in (("volumen", "volumen"), ("tomo", "tomo"), ("numero", "numero"), ("doi", "doi")):
        f.texto(campo, reg.get(clave), obligatorio=False)
    paginas = re.match(r"\s*(\w+)\s*-+\s*(\w+)", reg.get("paginas") or "")
    if paginas:
        f.texto("paginaInicial", paginas.group(1), obligatorio=False)
        f.texto("paginaFinal", paginas.group(2), obligatorio=False)
    f.marcar("tipoReferato", REFERATO_CON)
    f.marcar("publicado", PUBLICADO)
    avisos += cargar_autores(f, reg, config)
    _soporte(f, reg)
    avisos += _comunes(f, reg, config)
    fechas = {"fechaPublica": mes_anio(reg["fecha_publicacion"])}
    f.fijar_fechas(fechas)  # Al final: cada vuelta por un buscador las vuelve a pisar.
    return avisos, fechas


def llenar_evento(s: Sesion, reg: dict, config: dict) -> tuple[list[str], dict]:
    s.page.goto(s.url(RUTAS["alta_evento"]), wait_until="domcontentloaded")
    s.page.wait_for_selector('input[name="produccion"]', state="attached", timeout=45_000)
    f = Formulario(s)
    f.elegir("tipoTrabajo", etiqueta=reg.get("tipo_trabajo", "Artículo Completo"))
    f.texto("produccion", reg["titulo"])
    f.elegir("tipoPublicacion", etiqueta=reg["tipo_publicacion"])
    f.texto("tituloPublicacion", reg["titulo_publicacion"][:250])
    f.texto("issnIsbn", reg.get("isbn"), obligatorio=False)
    f.elegir("paisEdicion", etiqueta=reg["pais_edicion"])
    f.texto("lugarPublicacion", reg.get("ciudad_edicion"), obligatorio=False)
    f.texto("editorial", reg["editorial"])
    f.texto("reunionCientifica", reg["reunion"][:250])
    f.elegir("tipoReunion", etiqueta=reg["tipo_reunion"])
    f.casilla("alcanceNacional", reg["alcance"] == "nacional")
    f.casilla("alcanceInternacional", reg["alcance"] == "internacional")
    f.elegir("paisEvento", etiqueta=reg["pais_evento"])
    f.texto("lugarReunion", reg["ciudad_evento"])
    f.texto("institucionOrganizadora", reg.get("institucion_organizadora"), obligatorio=False)
    avisos = cargar_autores(f, reg, config)
    _soporte(f, reg)
    avisos += _comunes(f, reg, config)
    fechas = {"fechaReunion": mes_anio(reg["fecha_evento"]), "anioPublica": str(reg["anio_publicacion"])}
    f.fijar_fechas({k: v for k, v in fechas.items() if f.existe(k)})
    return avisos, {k: v for k, v in fechas.items() if f.existe(k)}


def _datos_de_libro(f: Formulario, reg: dict) -> None:
    """Campos que comparten libro y parte de libro."""
    f.texto("isbn", reg.get("isbn"), obligatorio=False)
    f.texto("totalPaginasLibro", reg.get("paginas_libro"), obligatorio=False)
    f.marcar("publicado", PUBLICADO)
    f.marcar("referato", REFERATO_LIBRO[reg["referato"]])
    f.elegir("pais", etiqueta=reg["pais_edicion"])
    f.texto("lugarEdicion", reg.get("ciudad_edicion"), obligatorio=False)
    f.texto("editorial", reg["editorial"])
    roles = reg.get("rol") or ["autor"]
    for rol, casilla in ROLES.items():
        f.casilla(casilla, rol in roles)


def llenar_capitulo(s: Sesion, reg: dict, config: dict) -> tuple[list[str], dict]:
    s.page.goto(s.url(RUTAS["alta_capitulo"]), wait_until="domcontentloaded")
    s.page.wait_for_selector('input[name="produccion"]', state="attached", timeout=45_000)
    f = Formulario(s)
    f.elegir("tipoParteLibro", etiqueta=reg["tipo_parte"])
    f.texto("tituloLibro", reg["titulo_libro"][:250])
    f.texto("produccion", reg["titulo"])
    paginas = re.match(r"\s*(\w+)\s*-+\s*(\w+)", reg.get("paginas") or "")
    if paginas:
        f.texto("paginaInicial", paginas.group(1), obligatorio=False)
        f.texto("paginaFinal", paginas.group(2), obligatorio=False)
    _datos_de_libro(f, reg)
    avisos = cargar_autores(f, reg, config)
    if reg.get("compiladores"):
        avisos += cargar_personas(f, reg["compiladores"], config, "compilador")
    _soporte(f, reg)
    avisos += _comunes(f, reg, config)
    fechas = {"anioPublica": str(reg["anio_publicacion"])}
    f.fijar_fechas(fechas)
    return avisos, fechas


def llenar_libro(s: Sesion, reg: dict, config: dict, subir: bool) -> tuple[list[str], dict]:
    s.page.goto(s.url(RUTAS["alta_libro"]), wait_until="domcontentloaded")
    s.page.wait_for_selector('input[name="produccion"]', state="attached", timeout=45_000)
    f = Formulario(s)
    f.texto("produccion", reg["titulo"])
    _datos_de_libro(f, reg)
    avisos = cargar_autores(f, reg, config)
    _soporte(f, reg)
    avisos += _comunes(f, reg, config, adjuntar=False)
    if subir:
        f.subir_fine_uploader(reg["archivo"])
    else:
        # El uploader sube al servidor apenas se elige el archivo: en seco no se toca.
        avisos.append("en seco no se sube el full text (uploader AJAX); se sube al guardar")
    fechas = {"anioPublica": str(reg["anio_publicacion"])}
    f.fijar_fechas(fechas)
    return avisos, fechas


def aplicar_campos(f: Formulario, campos: dict) -> dict:
    """Escribe cada campo por su name segun el control real. Devuelve las fechas, que se fijan al final."""
    fechas = {}
    for nombre, valor in campos.items():
        if not f.existe(nombre):
            raise ErrorCarga(f"el formulario no tiene el campo '{nombre}' (volver a inspeccionar)")
        tipo = f.page.evaluate("""(n) => { const e = document.getElementsByName(n);
            const v = Array.from(e).find(x => x.type !== 'hidden') || e[0];
            return {tag: v.tagName.toLowerCase(), tipo: (v.type || '').toLowerCase(), fecha: v.classList.contains('hasDatepicker')}; }""", nombre)
        if isinstance(valor, dict) and "fecha" in valor:
            fechas[nombre] = str(valor["fecha"])
        elif tipo["fecha"]:
            fechas[nombre] = str(valor)
        elif tipo["tag"] == "select":
            if isinstance(valor, dict):
                f.elegir(nombre, etiqueta=valor.get("etiqueta"), valor=valor.get("valor"))
            else:
                f.elegir(nombre, valor=str(valor))
        elif tipo["tipo"] == "radio":
            f.marcar(nombre, str(valor))
        elif tipo["tipo"] == "checkbox":
            valores = valor if isinstance(valor, list) else [valor]
            for v in valores:
                if isinstance(v, bool):
                    f.casilla(nombre, v)
                else:
                    f.marcar(nombre, str(v))
        else:
            f.texto(nombre, valor)
    return fechas


def llenar_generico(s: Sesion, reg: dict) -> tuple[list[str], dict]:
    """Formulario relevado con `inspeccionar`: cada campo por su name."""
    s.page.goto(s.url(reg["url_alta"]), wait_until="domcontentloaded")
    s.page.wait_for_load_state("load")
    f = Formulario(s)
    fechas = aplicar_campos(f, reg["campos"])
    if reg.get("archivo"):
        f.page.locator(f'input[name="{reg.get("campo_archivo", "theFile")}"]').first.set_input_files(reg["archivo"])
    f.fijar_fechas(fechas)
    return [], fechas


# ------------------------------------------------------------------ guardado y verificacion


def _ids_lista(s: Sesion, url_lista: str) -> set[str]:
    html = s.descargar(url_lista)
    return {f["editar"] for t in parsear_tablas(html) for f in t["filas"] if f["editar"]}


def _texto_pagina(s: Sesion) -> str:
    for _ in range(3):
        try:
            return s.page.inner_text("body")
        except Exception:
            s.page.wait_for_timeout(3_000)
    return ""


def _apretar_guardar(s: Sesion, boton: str, autorizado: bool = False) -> str:
    """`autorizado` solo lo usan `modificar` (Modificar) y su limpieza de duplicados (Eliminar)."""
    if RE_BOTON_PROHIBIDO.search(boton) and not autorizado:
        raise CorteTanda(f"boton '{boton}' prohibido")
    loc = s.page.locator(f'input[type="submit"][value="{boton}"], button:has-text("{boton}")')
    if not loc.count():
        raise ErrorCarga(f"no encontre el boton '{boton}'")
    s.aceptar_dialogos = True
    try:
        # Esperar la navegacion del submit: un wait_for_load_state vuelve en el acto sobre la
        # pagina vieja y se leeria el formulario anterior, sin el mensaje de error.
        try:
            with s.page.expect_navigation(wait_until="load", timeout=90_000):
                loc.first.click(no_wait_after=True)
        except s.PWTimeout:
            log("    Guardar no navego en 90 s; se verifica igual en la lista")
    finally:
        s.aceptar_dialogos = False
    return _texto_pagina(s)


def guardar(s: Sesion, reg: dict, fechas: dict, boton: str = "Guardar") -> dict:
    cuerpo = _apretar_guardar(s, boton)
    error = RE_ERROR_FORM.search(cuerpo)
    if error and reg.get("archivo") and reg.get("tipo") != "libro" and RE_REUBICAR_ARCHIVO.search(cuerpo):
        # Al re-renderizar, SIGEVA vacia el archivo y pisa las fechas: se reponen una vez.
        log("    re-adjuntando el archivo y reintentando una vez")
        f = Formulario(s)
        s.page.locator(f'input[name="{reg.get("campo_archivo", "theFile")}"]').first.set_input_files(reg["archivo"])
        f.fijar_fechas({k: v for k, v in fechas.items() if f.existe(k)})
        cuerpo = _apretar_guardar(s, boton)
        error = RE_ERROR_FORM.search(cuerpo)
    excepcion = RE_EXCEPCION.search(cuerpo)
    return {"error": error.group(0).strip() if error else None, "excepcion": excepcion.group(1) if excepcion else None}


def confirmar_publicacion(s: Sesion, reg: dict, id_tabla: str, esperar: bool = True) -> dict | None:
    intentos = INTENTOS_CONFIRMACION if esperar else 1
    for i in range(intentos):
        tabla = s.leer_tabla(RUTAS["lista_publicaciones"], id_tabla)
        if tabla is None:
            raise CorteTanda(f"no encontre la tabla {id_tabla} en la lista: ¿cambio el HTML de SIGEVA?")
        fila = buscar_en_tabla(tabla, reg["titulo"])
        if fila or i == intentos - 1:
            return fila
        s.page.wait_for_timeout(10_000)
    return None


def comparar_campos(s: Sesion, href: str, esperados: dict) -> dict:
    leidos = s.leer_campos(_ruta_eva(href), list(esperados))
    return {k: {"esperado": v, "guardado": leidos.get(k)} for k, v in esperados.items()
            if not leidos.get(k) or any(x != v for x in leidos[k])}


def _esperados_genericos(reg: dict) -> dict:
    esperados = {}
    for nombre, valor in reg["campos"].items():
        if isinstance(valor, dict) and "fecha" in valor:
            esperados[nombre] = str(valor["fecha"])
        elif isinstance(valor, dict) and valor.get("valor") is not None:
            esperados[nombre] = str(valor["valor"])
        elif isinstance(valor, (str, int, float)) and not isinstance(valor, bool):
            esperados[nombre] = a_latin1(str(valor))[0]
    return esperados


def procesar_registro(s: Sesion, reg: dict, config: dict, guardar_de_verdad: bool, confirmar: bool) -> dict:
    tipo, clave = reg["tipo"], reg["clave"]
    base = {"clave": clave, "tipo": tipo, "titulo": reg.get("titulo") or reg.get("rubro")}
    ids_antes: set[str] = set()
    if tipo in TIPOS_PUBLICACION:
        id_tabla = str(config["tablas"][tipo])
        if confirmar_publicacion(s, reg, id_tabla, esperar=False):
            return base | {"resultado": "ya-estaba"}
    else:
        listado = s.descargar(reg["url_lista"])
        if normalizar_nombre(reg["buscar_en_lista"]) in normalizar_nombre(listado_texto(listado)):
            return base | {"resultado": "ya-estaba", "detalle": f"'{reg['buscar_en_lista']}' figura en la lista"}
        ids_antes = {f["editar"] for t in parsear_tablas(listado) for f in t["filas"] if f["editar"]}

    if tipo == "articulo":
        avisos, fechas = llenar_articulo(s, reg, config)
    elif tipo == "evento":
        avisos, fechas = llenar_evento(s, reg, config)
    elif tipo == "capitulo":
        avisos, fechas = llenar_capitulo(s, reg, config)
    elif tipo == "libro":
        avisos, fechas = llenar_libro(s, reg, config, subir=guardar_de_verdad)
    else:
        avisos, fechas = llenar_generico(s, reg)
    captura = s.captura(f"{'seco' if not guardar_de_verdad else 'antes'}-{tipo}-{clave}")
    if not guardar_de_verdad:
        try:  # Libera el formulario en el servidor sin guardar.
            s.page.click('input[type="submit"][value="Volver"]', timeout=5_000)
        except Exception:
            pass
        return base | {"resultado": "en-seco", "avisos": avisos, "fechas": fechas, "captura": captura}
    if confirmar:
        respuesta = input(f"    ¿Guardar '{base['titulo'][:60]}'? [s/N] ").strip().lower()
        if respuesta != "s":
            return base | {"resultado": "omitido", "captura": captura}

    resultado = guardar(s, reg, fechas, reg.get("boton_guardar", "Guardar"))
    if resultado["error"]:
        return base | {"resultado": "rechazado", "detalle": resultado["error"], "captura": s.captura(f"rechazo-{clave}")}

    # Sin error visible no alcanza: SIGEVA puede volver sin quejarse y sin guardar,
    # y una excepcion de Hibernate a veces guarda igual. Solo cuenta la lista.
    if tipo in TIPOS_PUBLICACION:
        fila = confirmar_publicacion(s, reg, id_tabla)
        if not fila:
            return base | {"resultado": "no-guardado", "detalle": resultado["excepcion"] or "sin error visible y no figura en la lista",
                           "captura": s.captura(f"no-guardo-{clave}")}
        diferencias = comparar_campos(s, fila["editar"], fechas) if fila["editar"] else {"editar": "sin enlace"}
        if diferencias:
            raise CorteTanda(json.dumps(base | {"resultado": "guardado-con-diferencias", "diferencias": diferencias}, ensure_ascii=False))
        return base | {"resultado": "guardado", "verificado": True, "avisos": avisos, "en_lista": fila}

    nuevos: set[str] = set()
    for _ in range(INTENTOS_CONFIRMACION):
        nuevos = _ids_lista(s, reg["url_lista"]) - ids_antes
        if nuevos:
            break
        s.page.wait_for_timeout(10_000)
    if len(nuevos) != 1:
        detalle = "no aparecio ningun registro nuevo" if not nuevos else f"aparecieron {len(nuevos)} registros nuevos"
        if nuevos:
            raise CorteTanda(json.dumps(base | {"resultado": "verificacion-ambigua", "detalle": detalle}, ensure_ascii=False))
        return base | {"resultado": "no-guardado", "detalle": resultado["excepcion"] or detalle, "captura": s.captura(f"no-guardo-{clave}")}
    href = nuevos.pop()
    diferencias = comparar_campos(s, href, _esperados_genericos(reg))
    if diferencias:
        raise CorteTanda(json.dumps(base | {"resultado": "guardado-con-diferencias", "diferencias": diferencias, "editar": href}, ensure_ascii=False))
    return base | {"resultado": "guardado", "verificado": True, "avisos": avisos, "editar": href}


def listado_texto(html: str) -> str:
    return " ".join(" ".join(f["celdas"]) for t in parsear_tablas(html) for f in t["filas"])


# ------------------------------------------------------------------ comandos


def cmd_doctor(_args) -> int:
    estado = {"python": sys.version.split()[0], "playwright": None, "chromium": None}
    try:
        from playwright.sync_api import sync_playwright
        import playwright
        estado["playwright"] = getattr(playwright, "__version__", "instalado")
        with sync_playwright() as pw:
            nav = pw.chromium.launch(headless=True)
            estado["chromium"] = nav.version
            nav.close()
    except ImportError:
        estado["error"] = "falta playwright: python -m pip install -r assets/requirements.txt"
    except Exception as e:
        estado["error"] = f"Chromium no arranca: {str(e).splitlines()[0][:200]} (python -m playwright install chromium)"
    print(json.dumps(estado, ensure_ascii=False, indent=1))
    return 0 if estado.get("chromium") else 1


def cmd_bib(args) -> int:
    config = cargar_config(args.config)
    entradas = parsear_bibtex(Path(args.bib).read_text(encoding="utf-8", errors="replace"))
    registros, descartes = bib_a_registros(entradas, config.get("idioma_defecto"))
    declarante = config.get("declarante", {})
    for reg in registros:
        for autor in reg["autores"]:
            if declarante.get("apellido") and es_declarante(autor, config):
                autor["declarante"] = True
    escribir_json(Path(args.salida), registros)
    print(json.dumps({"entradas": len(entradas), "registros": len(registros), "descartes": descartes,
                      "salida": args.salida}, ensure_ascii=False, indent=1))
    return 0


def cmd_preparar(args) -> int:
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    registros = leer_json(args.registros, [])
    catalogo = leer_json(args.catalogo or trabajo / "catalogo.json", {})
    inventario = leer_json(args.inventario or trabajo / "inventario.json")
    reporte = preparar(registros, config, catalogo, inventario)
    escribir_json(trabajo / "listos.json", reporte["listos"])
    resumen = {"registros": len(registros), "listos": len(reporte["listos"]), "bloqueados": reporte["bloqueados"],
               "ya_cargados": reporte["ya_cargados"], "inventario_usado": reporte["inventario_usado"],
               "inventario_capturado": reporte["inventario_capturado"], "salida": str(trabajo / "listos.json")}
    if not inventario:
        resumen["advertencia"] = "sin inventario: no se pudo descartar lo ya cargado (correr 'inventario' antes)"
    escribir_json(trabajo / "reporte_preparar.json", resumen)
    print(json.dumps(resumen, ensure_ascii=False, indent=1))
    return 0


def cmd_inventario(args) -> int:
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        verificacion_previa(s, args, config, trabajo)
        tablas = {}
        for tipo, id_tabla in config["tablas"].items():
            tabla = s.leer_tabla(RUTAS["lista_publicaciones"], str(id_tabla))
            if tabla is None:
                raise SystemExit(f"No encontre la tabla de {tipo} (id {id_tabla}): ¿cambio el HTML de SIGEVA?")
            tablas[tipo] = tabla
        s.page.goto(s.url(RUTAS["indice"]), wait_until="domcontentloaded")
        indice = s.page.inner_text("body")
        s.captura("inventario-indice")
    previo = trabajo / "inventario.json"
    if previo.exists():
        sello = leer_json(previo, {}).get("capturado_en_utc", "previo")[:19].replace(":", "")
        os.replace(previo, trabajo / f"inventario-{sello}.json")
    inventario = {"capturado_en_utc": ahora_utc(), "base": config["base"], "tablas": tablas,
                  "indice_texto": indice}
    escribir_json(previo, inventario)
    print(json.dumps({"salida": str(previo), "filas": {t: len(v["filas"]) for t, v in tablas.items()},
                      "control": "comparar con los conteos del indice del Banco de Datos (indice_texto)"},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_catalogo(args) -> int:
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    ruta = trabajo / "catalogo.json"
    catalogo = leer_json(ruta, {"revistas": {}, "instituciones": {}})
    # Revistas e instituciones se acumulan entre corridas; quien declara se recuenta con lo leido hoy.
    catalogo["personas_declarante"] = {}
    fallos = 0
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        verificacion_previa(s, args, config, trabajo)
        hrefs = []
        for id_tabla in config["tablas"].values():
            tabla = s.leer_tabla(RUTAS["lista_publicaciones"], str(id_tabla)) or {"filas": []}
            hrefs += [f["editar"] for f in tabla["filas"] if f["editar"]]
        hrefs = hrefs[:args.limite] if args.limite else hrefs
        log(f"{len(hrefs)} registros a leer (solo lectura)")
        for i, href in enumerate(hrefs, 1):
            try:
                # Los autores se arman por JavaScript: hace falta abrir la pagina, no basta fetch.
                s.page.goto(s.url(_ruta_eva(href)), wait_until="domcontentloaded", timeout=45_000)
                s.page.wait_for_timeout(600)
                d = s.page.evaluate("""() => {
                    const todos = (n) => Array.from(document.getElementsByName(n)).map(e => e.value);
                    const uno = (n) => (document.getElementsByName(n)[0] || {}).value || '';
                    const texto = document.body.innerText || '';
                    const issn = (texto.match(/ISSN\\s*:?\\s*([0-9]{4}-?[0-9]{3}[0-9Xx])/) || [])[1] || '';
                    return {publicacionId: uno('publicacionId'), revista: uno('srevista') || uno('revista'), issn,
                            labels: todos('autorOrganizacionLabel'), ids: todos('autorOrganizacionId'),
                            otras: todos('autorisOtraOrganizacion'),
                            // El id solo no le dice nada a una persona: se guarda con el nombre del autor de esa fila.
                            personas: Array.from(document.getElementsByName('autorPersonaId')).filter(e => e.value).map(e => {
                                const tabla = e.closest('table');
                                const nombre = tabla && tabla.querySelector('[name="autorParticipacionLabel"]');
                                return {id: e.value, nombre: nombre ? nombre.value.trim() : ''};
                            })};
                }""")
            except s.PWTimeout:
                fallos += 1
                continue
            if d["publicacionId"] and d["revista"]:
                catalogo["revistas"][normalizar_nombre(d["revista"])] = {"id": d["publicacionId"], "label": d["revista"], "issn": d["issn"]}
            for label, id_, otra in zip(d["labels"], d["ids"], d["otras"], strict=False):
                if label and id_ and id_ != "0":
                    catalogo["instituciones"][normalizar_nombre(label)] = {"id": id_, "label": label, "otra": otra == "true"}
            for persona in {(p["id"], p["nombre"]) for p in d["personas"]}:
                previo = catalogo["personas_declarante"].get(persona[0])
                entrada = previo or {"veces": 0, "nombres": []}
                entrada["veces"] += 1
                if persona[1] and persona[1] not in entrada["nombres"]:
                    entrada["nombres"].append(persona[1])
                catalogo["personas_declarante"][persona[0]] = entrada
            if i % 10 == 0:
                log(f"  {i}/{len(hrefs)}")
    catalogo["capturado_en_utc"] = ahora_utc()
    escribir_json(ruta, catalogo)
    personas = sorted(((k, v) for k, v in catalogo["personas_declarante"].items() if isinstance(v, dict)),
                      key=lambda x: -x[1]["veces"])
    print(json.dumps({"salida": str(ruta), "revistas": len(catalogo["revistas"]),
                      "instituciones": len(catalogo["instituciones"]), "fallos": fallos,
                      "persona_id_candidatos": [{"persona_id": k, "nombres": v["nombres"], "registros": v["veces"]}
                                                for k, v in personas[:3]],
                      "nota": "persona_id: mostrar los nombres a la persona y que confirme cual es ella; nunca pedir que apruebe un numero solo"},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_institucion(args) -> int:
    """Busca en el catalogo oficial de SIGEVA desde el alta de evento. Solo lectura: no selecciona ni guarda."""
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    if len(args.texto.strip()) < 3:
        raise SystemExit("SIGEVA exige al menos 3 caracteres para buscar")
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        verificacion_previa(s, args, config, trabajo)
        page, f = s.page, Formulario(s)
        page.goto(s.url(RUTAS["alta_evento"]), wait_until="domcontentloaded")
        page.locator('input[name="autorOrganizacionBuscar"]').first.fill(args.texto)
        page.locator('input[name="btnSubmitBuscar"]').first.click()
        page.wait_for_selector('select[name="filtroPais"]', state="attached", timeout=60_000)
        f.elegir("filtroPais", etiqueta=args.pais)
        page.wait_for_timeout(1_500)  # el combo de provincia se repuebla
        if args.provincia:
            f.elegir("filtroProvincia", etiqueta=args.provincia)
            page.wait_for_timeout(800)
        page.fill('input[name="filtroOrganizacion"]', args.texto)
        page.click('input[type="button"][value="Buscar"]')
        page.wait_for_timeout(4_000)
        crudos = page.evaluate("""() => Array.from(document.querySelectorAll('span.orgBuscar')).map(e => ({
            nombre: e.innerText.replace(/\\s+/g, ' ').trim(), ruta: ((e.getAttribute('onclick') || '').match(/navegar\\('([\\d-]+)'\\)/) || [])[1] || ''}))""")
        provincias = [t for v, t in f.opciones("filtroProvincia") if v and not v.startswith("-")][:40]
        s.captura(f"institucion-{args.texto}")
    # El id es el ultimo tramo de la ruta, sin ceros a la izquierda; la ruta muestra de quien depende.
    por_ruta = {r["ruta"]: r["nombre"] for r in crudos if r["ruta"]}
    resultados = [{"institucion_id": str(int(ruta.split("-")[-1])), "nombre": nombre,
                   "depende_de": " > ".join(por_ruta.get("-".join(ruta.split("-")[:i]), "?") for i in range(1, len(ruta.split("-"))))}
                  for ruta, nombre in por_ruta.items() if normalizar_nombre(args.texto) in normalizar_nombre(nombre)]
    print(json.dumps({"buscado": args.texto, "pais": args.pais, "provincia": args.provincia, "resultados": resultados,
                      "provincias_disponibles": provincias if not args.provincia else None,
                      "nota": "mostrar nombre y dependencia a la persona; usar institucion_id con 'otra': false"},
                     ensure_ascii=False, indent=1))
    return 0


# ------------------------------------------------------------------ modificar

RE_ID_REGISTRO = re.compile(r"(?:produccionId|actividadId|formacionId|cargoIdId|[?&]id)=(\d+)", re.I)
BOTONES_ELIMINAR = ("Eliminar", "Borrar", "Confirmar")

JS_VALORES = r"""(nombres) => {
    const out = {};
    for (const n of nombres) {
        out[n] = Array.from(document.getElementsByName(n))
            .filter(e => !((e.type === 'checkbox' || e.type === 'radio') && !e.checked))
            .map(e => e.tagName === 'SELECT' ? (e.selectedOptions[0] || {}).value || '' : e.value);
    }
    return out;
}"""

JS_MARCAR_DECLARANTE = r"""([personaId, apellido]) => {
    const norm = (s) => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const labels = Array.from(document.getElementsByName('autorParticipacionLabel'));
    const filas = labels.map(c => {
        const t = c.closest('table');
        return {nombre: c.value, persona: t && t.querySelector('[name="autorPersonaId"]')};
    }).filter(f => f.nombre);
    if (filas.some(f => f.persona && f.persona.value === personaId)) return {estado: 'ya-marcado'};
    const candidatas = filas.filter(f => norm(f.nombre).split(/[\s,]+/).includes(apellido));
    if (candidatas.length !== 1 || !candidatas[0].persona) return {estado: candidatas.length ? 'ambiguo' : 'sin-coincidencia'};
    candidatas[0].persona.value = personaId;
    return {estado: 'marcado', nombre: candidatas[0].nombre};
}"""


def _id_registro(href: str) -> str:
    m = RE_ID_REGISTRO.search(href or "")
    return m.group(1) if m else href


def _ids_tabla(tabla: dict | None) -> dict[str, str]:
    return {_id_registro(f["editar"]): f["editar"] for f in (tabla or {}).get("filas", []) if f["editar"]}


def _valor_cambio(texto: str):
    """`--campo nombre=valor`: JSON si lo parece ({"etiqueta": ...}, true, [...]), texto en otro caso."""
    texto = texto.strip()
    if texto[:1] in "{[" or texto in ("true", "false"):
        return json.loads(texto)
    return texto


def _eliminar_registro(s: Sesion, href: str) -> str | None:
    """Abre la pantalla de borrado de UN registro y la confirma. Devuelve el boton usado o None."""
    borrar = re.sub(r"(action|accion)=editar", lambda m: f"{m.group(1)}={'Borrar' if m.group(1) == 'action' else 'borrar'}",
                    href, flags=re.I)
    if borrar == href:
        raise ErrorCarga(f"no pude derivar el enlace de borrado de {href}")
    # El token de Struts es uno por sesion: la pantalla se carga justo antes de confirmar.
    s.page.goto(s.url(_ruta_eva(borrar)), wait_until="domcontentloaded")
    s.page.wait_for_load_state("load")
    for boton in BOTONES_ELIMINAR:
        if s.page.locator(f'input[type="submit"][value="{boton}"]').count():
            _apretar_guardar(s, boton, autorizado=True)
            return boton
    s.captura(f"borrado-sin-boton-{_id_registro(href)}")
    return None


def modificar_registro(s: Sesion, config: dict, tipo: str, titulo: str, cambios: dict,
                       guardar_de_verdad: bool, borrar_duplicado: bool) -> dict:
    """Edita un registro sin dejar duplicados.

    En SIGEVA "Modificar" suele crear un registro con id nuevo y retirar el anterior; si se
    modifica desde un id viejo queda un duplicado. Protocolo: abrir el id que muestra la lista
    AHORA, guardar, y comparar los ids de la lista antes y despues. Exactamente un id nuevo y el
    viejo retirado (o el mismo id editado en el lugar) es exito; el viejo todavia presente junto
    al nuevo es un duplicado, que solo se borra con `borrar_duplicado` y tras verificar el nuevo.
    """
    id_tabla = str(config["tablas"][tipo])
    tabla = s.leer_tabla(RUTAS["lista_publicaciones"], id_tabla)
    if tabla is None:
        raise CorteTanda(f"no encontre la tabla {id_tabla} en la lista: ¿cambio el HTML de SIGEVA?")
    halladas = buscar_todas_en_tabla(tabla, titulo)
    if len(halladas) != 1:
        raise ErrorCarga(f"'{titulo}' coincide con {len(halladas)} registros de la lista; tiene que ser exactamente uno")
    fila = halladas[0]
    id_viejo, ids_antes = _id_registro(fila["editar"]), _ids_tabla(tabla)
    base = {"tipo": tipo, "titulo": fila["titulo"], "id_antes": id_viejo}

    s.page.goto(s.url(_ruta_eva(fila["editar"])), wait_until="domcontentloaded")
    s.page.wait_for_load_state("load")
    s.page.wait_for_timeout(1_500)  # autores y area se arman por JavaScript
    if not s.page.locator('input[type="submit"][value="Modificar"]').count():
        raise ErrorCarga("la pantalla abierta no tiene el boton Modificar")
    f = Formulario(s)
    nombres = list(cambios)
    antes = f.page.evaluate(JS_VALORES, nombres)
    fechas = aplicar_campos(f, cambios)
    # Al modificar registros viejos SIGEVA exige al declarante ("Debe seleccionar su nombre").
    declarante = {"estado": "sin-persona_id"}
    if config.get("persona_id") and config.get("declarante", {}).get("apellido"):
        declarante = f.page.evaluate(JS_MARCAR_DECLARANTE, [str(config["persona_id"]),
                                                            normalizar_nombre(config["declarante"]["apellido"])])
    f.fijar_fechas(fechas)
    despues = f.page.evaluate(JS_VALORES, nombres)
    base |= {"cambios": {n: {"antes": antes.get(n), "despues": despues.get(n)} for n in nombres}, "declarante": declarante}
    captura = s.captura(f"{'seco' if not guardar_de_verdad else 'antes'}-modificar-{id_viejo}")
    if not guardar_de_verdad:
        try:
            s.page.click('input[type="submit"][value="Volver"]', timeout=5_000)
        except Exception:
            pass
        return base | {"resultado": "en-seco", "captura": captura}

    cuerpo = _apretar_guardar(s, "Modificar", autorizado=True)
    error = RE_ERROR_FORM.search(cuerpo)
    if error:
        return base | {"resultado": "rechazado", "detalle": error.group(0).strip(), "captura": s.captura(f"rechazo-modificar-{id_viejo}")}

    ids_despues: dict[str, str] = {}
    for intento in range(INTENTOS_CONFIRMACION):
        ids_despues = _ids_tabla(s.leer_tabla(RUTAS["lista_publicaciones"], id_tabla))
        if set(ids_despues) - set(ids_antes) or (intento and id_viejo in ids_despues):
            break
        s.page.wait_for_timeout(10_000)
    nuevos = sorted(set(ids_despues) - set(ids_antes))
    faltan = sorted(set(ids_antes) - set(ids_despues) - {id_viejo})
    if len(nuevos) > 1 or faltan:
        raise CorteTanda(json.dumps(base | {"resultado": "lista-inesperada", "nuevos": nuevos, "desaparecidos": faltan}, ensure_ascii=False))
    if not nuevos and id_viejo not in ids_despues:
        raise CorteTanda(json.dumps(base | {"resultado": "registro-desaparecido"}, ensure_ascii=False))
    id_final = nuevos[0] if nuevos else id_viejo
    href_final = ids_despues[id_final]
    leidos = s.leer_campos(_ruta_eva(href_final), nombres)
    diferencias = {n: {"esperado": despues.get(n), "guardado": leidos.get(n)} for n in nombres if leidos.get(n) != despues.get(n)}
    base |= {"id_despues": id_final, "modo_sigeva": "edicion-en-el-lugar" if id_final == id_viejo else "version-nueva"}
    if diferencias:
        raise CorteTanda(json.dumps(base | {"resultado": "guardado-con-diferencias", "diferencias": diferencias}, ensure_ascii=False))
    if id_final == id_viejo or id_viejo not in ids_despues:
        return base | {"resultado": "modificado", "verificado": True}

    # Quedaron el viejo y el nuevo: duplicado.
    if not borrar_duplicado:
        return base | {"resultado": "duplicado", "detalle": f"quedo el registro viejo {id_viejo}; borrarlo con --borrar-duplicado"}
    boton = _eliminar_registro(s, ids_despues[id_viejo])
    finales = _ids_tabla(s.leer_tabla(RUTAS["lista_publicaciones"], id_tabla))
    if boton and id_viejo not in finales and id_final in finales:
        return base | {"resultado": "modificado", "verificado": True, "duplicado_borrado": id_viejo}
    return base | {"resultado": "duplicado", "detalle": f"no pude borrar el registro viejo {id_viejo}",
                   "captura": s.captura(f"duplicado-{id_viejo}")}


def cmd_modificar(args) -> int:
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    cambios = {}
    for par in args.campo or []:
        nombre, sep, valor = par.partition("=")
        if not sep or not nombre.strip():
            raise SystemExit(f"--campo espera nombre=valor: '{par}'")
        cambios[nombre.strip()] = _valor_cambio(valor)
    if not cambios:
        raise SystemExit("indicar al menos un --campo nombre=valor (nombres: ver `inspeccionar` o el mapa)")
    estado = Estado(trabajo / "estado.jsonl")
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        verificacion_previa(s, args, config, trabajo)
        try:
            r = modificar_registro(s, config, args.tipo, args.titulo, cambios, args.guardar, args.borrar_duplicado)
        except ErrorCarga as e:
            r = {"tipo": args.tipo, "titulo": args.titulo, "resultado": "error", "detalle": str(e)}
        except CorteTanda as e:
            try:
                r = json.loads(str(e))
            except json.JSONDecodeError:
                r = {"tipo": args.tipo, "titulo": args.titulo, "resultado": "corte", "detalle": str(e)}
            r["captura"] = s.captura("corte-modificar")
    r = {"comando": "modificar", "modo": "guardar" if args.guardar else "en-seco"} | r
    if args.guardar:
        estado.registrar(r)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r["resultado"] in ("modificado", "en-seco") else 1


def cmd_cv(args) -> int:
    """Cruza un CV (.docx/.pdf/.txt) con inventario.json: que falta cargar. Sin red."""
    import sigeva_cv as CV

    trabajo = Path(args.dir)
    inventario = leer_json(args.inventario or trabajo / "inventario.json")
    if inventario is None:
        raise SystemExit("No hay inventario: correr 'inventario' antes (con las tablas de libro y capitulo en config.tablas)")
    excluir = {normalizar_titulo(t) for t in (leer_json(args.excluir, []) if args.excluir else [])}
    items = [i for i in CV.parsear_cv(CV.extraer_texto(args.cv)) if normalizar_titulo(i["titulo"] or "") not in excluir]
    reporte = CV.cruzar(items, inventario, desde=args.desde)
    reporte |= {"cv": str(args.cv), "inventario_capturado": inventario.get("capturado_en_utc"), "desde": args.desde,
                "tablas_inventariadas": list(inventario.get("tablas", {}))}
    escribir_json(trabajo / "cruce-cv.json", reporte)
    print(json.dumps({k: reporte[k] for k in ("resumen", "falta", "en_otra_tabla", "sin_titulo", "sin_tabla")}
                     | {"salida": str(trabajo / "cruce-cv.json")}, ensure_ascii=False, indent=1))
    return 0


def cmd_pdf(args) -> int:
    """Arma el full text: recorta paginas (creditos + trabajo) y/o comprime por debajo de 35 MB."""
    import sigeva_cv as CV

    origen, salida = Path(args.entrada), Path(args.salida)
    if origen.resolve() == salida.resolve():
        raise SystemExit("--salida tiene que ser otro archivo")
    resultado = {"entrada": str(origen), "salida": str(salida)}
    actual = origen
    if args.paginas:
        resultado["paginas"] = CV.recortar_pdf(origen, salida, args.paginas)
        actual = salida
    mb = actual.stat().st_size / 2**20
    if mb > args.max_mb or args.comprimir:
        temporal = salida.with_suffix(".tmp.pdf")
        mb = CV.comprimir_pdf(actual, temporal, args.max_mb)
        os.replace(temporal, salida)
    elif actual != salida:
        salida.write_bytes(actual.read_bytes())
    resultado |= {"mb": round(mb, 2), "entra_en_sigeva": mb <= MAX_PDF_MB}
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
    return 0 if mb <= MAX_PDF_MB else 1


def cmd_inspeccionar(args) -> int:
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        verificacion_previa(s, args, config, trabajo)
        s.page.goto(s.url(args.url), wait_until="domcontentloaded")
        s.page.wait_for_load_state("load")
        s.page.wait_for_timeout(800)
        controles = s.page.evaluate(JS_CONTROLES)
        nombre = re.sub(r"[^\w]+", "_", args.url.split("?")[0].rsplit("/", 1)[-1])
        captura = s.captura(f"inspeccion-{nombre}")
        html = trabajo / "inspecciones" / f"{nombre}.html"
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text(s.page.content(), encoding="utf-8")
        salida = trabajo / "inspecciones" / f"{nombre}.json"
        escribir_json(salida, {"url": args.url, "capturado_en_utc": ahora_utc(), "controles": controles})
        # Volver sin guardar: inspeccionar nunca envia el formulario.
    print(json.dumps({"salida": str(salida), "captura": captura, "html": str(html),
                      "controles": len(controles), "con_name": len({c["name"] for c in controles if c["name"]})},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_cargar(args) -> int:
    config = cargar_config(args.config)
    trabajo = Path(args.dir)
    if not 1 <= args.limite <= LIMITE_MAXIMO:
        raise SystemExit(f"--limite debe estar entre 1 y {LIMITE_MAXIMO}: SIGEVA se traba con tandas largas")
    estado = Estado(trabajo / "estado.jsonl")
    registros = leer_json(args.registros, [])
    hechos = estado.guardados()
    cola = []
    for reg in registros:
        if args.claves and reg.get("clave") not in args.claves:
            continue
        if reg.get("clave") in hechos:
            continue
        errores, _ = validar_registro(reg, config)
        if errores:
            raise SystemExit(f"El registro {reg.get('clave')} no paso la validacion: {errores}. Correr 'preparar'.")
        cola.append(reg)
    cola = cola[:args.limite]
    recibo = {"comando": "cargar", "modo": "guardar" if args.guardar else "en-seco", "inicio_utc": ahora_utc(),
              "solicitados": len(cola), "resultados": [], "motivo_fin": "completo"}
    ruta_recibo = trabajo / f"recibo-cargar-{datetime.now():%Y%m%d-%H%M%S}.json"
    if not cola:
        recibo["motivo_fin"] = "nada pendiente con esos filtros"
        escribir_json(ruta_recibo, recibo)
        print(json.dumps(recibo, ensure_ascii=False, indent=1))
        return 0
    log(f"{len(cola)} registros. Modo: {'GUARDAR' if args.guardar else 'EN SECO (no guarda)'}")
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        verificacion_previa(s, args, config, trabajo)
        if any(r["tipo"] in TIPOS_PUBLICACION for r in cola):
            fallas = chequear_contrato(s)
            recibo["contrato"] = fallas
            if fallas:
                recibo["motivo_fin"] = "SIGEVA cambio: el contrato del cargador no se cumple (correr 'verificar')"
                recibo["fin_utc"] = ahora_utc()
                escribir_json(ruta_recibo, recibo)
                print(json.dumps(recibo | {"recibo": str(ruta_recibo)}, ensure_ascii=False, indent=1))
                return 2
        for i, reg in enumerate(cola, 1):
            if i > 1:
                s.page.wait_for_timeout(PAUSA_ENTRE_ALTAS_MS)
            log(f"({i}/{len(cola)}) [{reg['tipo']}] {(reg.get('titulo') or reg.get('rubro'))[:60]}")
            if not s.viva():
                recibo["motivo_fin"] = "la sesion expiro"
                break
            try:
                r = procesar_registro(s, reg, config, args.guardar, args.confirmar)
            except ErrorCarga as e:
                r = {"clave": reg["clave"], "tipo": reg["tipo"], "resultado": "error", "detalle": str(e),
                     "captura": s.captura(f"error-{reg['clave']}")}
            except CorteTanda as e:
                try:
                    r = json.loads(str(e))
                except json.JSONDecodeError:
                    r = {"clave": reg["clave"], "resultado": "corte", "detalle": str(e)}
                r["captura"] = s.captura(f"corte-{reg['clave']}")
                estado.registrar(r)
                recibo["resultados"].append(r)
                recibo["motivo_fin"] = f"corte de tanda: {r.get('resultado')}"
                log(f"    CORTE: {str(e)[:200]}")
                break
            estado.registrar(r)
            recibo["resultados"].append(r)
            log(f"    {r['resultado']}" + (f": {r.get('detalle', '')[:160]}" if r.get("detalle") else ""))
            escribir_json(ruta_recibo, recibo)
        recibo["dialogos"] = s.dialogos
    recibo["fin_utc"] = ahora_utc()
    conteo: dict[str, int] = {}
    for r in recibo["resultados"]:
        conteo[r["resultado"]] = conteo.get(r["resultado"], 0) + 1
    recibo["conteo"] = conteo
    escribir_json(ruta_recibo, recibo)
    print(json.dumps(recibo | {"recibo": str(ruta_recibo)}, ensure_ascii=False, indent=1))
    malos = {"error", "rechazado", "no-guardado", "corte", "guardado-con-diferencias", "verificacion-ambigua"}
    return 1 if any(r["resultado"] in malos for r in recibo["resultados"]) else 0


def chequear_contrato(s: Sesion) -> list[dict]:
    """Visita solo las pantallas del contrato (sin seguir enlaces) y devuelve lo que falta."""
    import sigeva_mapa as M

    log("Chequeando que SIGEVA siga teniendo lo que el cargador necesita...")
    mapa = M.mapear(s, [c["pantalla"] for c in CONTRATO], max_pantallas=len(CONTRATO) * 2, pausa_ms=300,
                    log=lambda _m: None, seguir=False)
    return M.verificar_contrato(mapa, CONTRATO)


REFERENCIAS = Path(__file__).resolve().parent.parent / "references"


def cargar_env(ruta: str) -> None:
    """Lee usuario y clave de un .env y los deja solo en el entorno de este proceso.

    Acepta USER/PASS o SIGEVA_USER/SIGEVA_PASS. Nunca imprime ni escribe los valores.
    """
    claves = {"USER": "SIGEVA_USER", "SIGEVA_USER": "SIGEVA_USER", "PASS": "SIGEVA_PASS",
              "PASSWORD": "SIGEVA_PASS", "SIGEVA_PASS": "SIGEVA_PASS"}
    leidas = set()
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        destino = claves.get(clave.strip().removeprefix("export ").strip())
        if destino:
            os.environ[destino] = valor.strip().strip('"').strip("'")
            leidas.add(destino)
    if leidas != {"SIGEVA_USER", "SIGEVA_PASS"}:
        raise SystemExit(f"{ruta}: faltan USER y/o PASS (o SIGEVA_USER/SIGEVA_PASS)")


def _capturar_mapa(s: Sesion, args, config: dict, trabajo: Path) -> dict:
    """Recorre el Banco de Datos con una sesion ya iniciada y guarda el mapa completo (solo local)."""
    import sigeva_mapa as M

    log("Mapeando en solo lectura (no se envia ningun formulario)...")
    mapa = M.mapear(s, RUTAS["indice"].split("eva/", 1)[1], max_pantallas=args.max_pantallas,
                    pausa_ms=args.pausa_ms, log=log)
    mapa = {"capturado_en_utc": ahora_utc(), "base": config["base"], **mapa}
    ruta = trabajo / "mapas" / f"mapa-{datetime.now():%Y%m%d-%H%M%S}.json"
    escribir_json(ruta, mapa)  # completo, con opciones: solo local
    log(f"Mapa completo (local) en {ruta}")
    return mapa


def _mapa_en_vivo(args, config: dict, trabajo: Path) -> dict:
    with Sesion(config, trabajo, headless=args.headless) as s:
        s.iniciar()
        return _capturar_mapa(s, args, config, trabajo)


def _aceptar_mapa(mapa: dict, referencias: Path) -> dict:
    import sigeva_mapa as M

    saneado = M.sanear(mapa)
    documento = M.generar_documento(saneado, CONTRATO)
    contenido = json.dumps(saneado, ensure_ascii=False) + documento
    secretos = [os.environ.get(k) for k in ("SIGEVA_USER", "SIGEVA_PASS")]
    if any(s and len(s) >= 3 and s in contenido for s in secretos):
        raise SystemExit("El mapa contiene una credencial: no se escribe la linea base. Revisar sanear().")
    escribir_json(referencias / "mapa-base.json", saneado)
    (referencias / "mapa-sitio.md").write_text(documento, encoding="utf-8")
    return {"linea_base": str(referencias / "mapa-base.json"), "documento": str(referencias / "mapa-sitio.md")}


def cmd_mapear(args) -> int:
    import sigeva_mapa as M

    config = cargar_config(args.config)
    mapa = _mapa_en_vivo(args, config, Path(args.dir))
    contrato = M.verificar_contrato(mapa, CONTRATO)
    salida = {"pantallas": len(mapa["pantallas"]), "omitidos": len(mapa["omitidos"]), "errores": mapa["errores"],
              "completo": mapa["completo"], "version_sigeva": mapa["version_sigeva"], "contrato": contrato}
    if args.aceptar:
        salida |= _aceptar_mapa(mapa, Path(args.referencias))
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    return 1 if not mapa["completo"] else (2 if contrato else 0)


def _verificar(actual: dict, base: dict, referencias: Path, trabajo: Path, auto: bool, aceptar: bool) -> tuple[dict, int]:
    """Compara un mapa con la linea base y el contrato, registra y adopta segun el modo. Devuelve (informe, codigo)."""
    import sigeva_mapa as M

    cambios = M.verificar_contrato(actual, CONTRATO) + M.comparar_mapas(base, M.sanear(actual))
    orden = {s: i for i, s in enumerate(M.SEVERIDADES)}
    cambios.sort(key=lambda c: (orden[c["severidad"]], c["pantalla"], c["tipo"]))
    informe = {"verificado_en_utc": ahora_utc(), "linea_base_capturada": base.get("capturado_en_utc"),
               "version_base": base.get("version_sigeva"), "version_actual": actual.get("version_sigeva"),
               "recorrido_completo": actual.get("completo"), "errores_recorrido": actual.get("errores"),
               "resumen": M.resumen_cambios(cambios), "cambios": cambios}
    ruta = trabajo / "verificaciones" / f"verificacion-{datetime.now():%Y%m%d-%H%M%S}.json"
    escribir_json(ruta, informe)
    informe["informe"] = str(ruta)
    criticos = informe["resumen"]["critico"]
    adoptar = aceptar or (auto and actual.get("completo") and not criticos)
    if adoptar and (cambios or aceptar):
        informe["aceptado"] = _aceptar_mapa(actual, referencias)
    if cambios:
        M.registrar_historial(referencias / "historial-cambios.md", informe, adoptado=bool(adoptar))
    if not actual.get("completo"):
        codigo = 1
    elif auto:
        codigo = 2 if criticos else 0
    else:
        codigo = 2 if cambios and not aceptar else 0
    escribir_json(trabajo / "ultima-verificacion.json",
                  {"verificado_en_utc": informe["verificado_en_utc"], "codigo": codigo, "resumen": informe["resumen"],
                   "referencias": str(referencias.resolve()), "informe": str(ruta)})
    return informe, codigo


def _linea_base(referencias: Path) -> dict:
    base = leer_json(referencias / "mapa-base.json")
    if base is None:
        raise SystemExit(f"No hay linea base en {referencias}: correr 'mapear --aceptar' primero")
    return base


def cmd_verificar(args) -> int:
    config = cargar_config(args.config)
    trabajo, referencias = Path(args.dir), Path(args.referencias)
    base = _linea_base(referencias)
    actual = leer_json(args.mapa) if args.mapa else _mapa_en_vivo(args, config, trabajo)
    informe, codigo = _verificar(actual, base, referencias, trabajo, args.auto, args.aceptar)
    print(json.dumps(informe, ensure_ascii=False, indent=1))
    return codigo


def verificacion_previa(s: Sesion, args, config: dict, trabajo: Path) -> None:
    """`verificar --auto` al inicio de cualquier trabajo contra SIGEVA, en la misma sesion.

    Se reutiliza una verificacion aprobada (codigo 0, misma linea base) de las ultimas
    `--vigencia-horas`; con 0 se verifica siempre. Cualquier otro resultado corta el trabajo.
    """
    referencias = Path(args.referencias)
    base = _linea_base(referencias)
    ultima = leer_json(trabajo / "ultima-verificacion.json", {})
    if args.vigencia_horas > 0 and ultima.get("codigo") == 0 and ultima.get("referencias") == str(referencias.resolve()):
        edad_h = (datetime.now(timezone.utc) - datetime.fromisoformat(ultima["verificado_en_utc"])).total_seconds() / 3600
        if edad_h < args.vigencia_horas:
            log(f"Verificacion vigente ({edad_h:.1f} h, sin cambios criticos): no se repite el recorrido.")
            return
    log("Verificando que SIGEVA coincida con la documentacion antes de empezar (verificar --auto)...")
    informe, codigo = _verificar(_capturar_mapa(s, args, config, trabajo), base, referencias, trabajo, auto=True, aceptar=False)
    resumen = ", ".join(f"{k} {v}" for k, v in informe["resumen"].items())
    if codigo == 1:
        raise SystemExit(f"La verificacion previa no pudo recorrer todo el sitio ({informe['errores_recorrido']}). "
                         f"No se sigue. Informe: {informe['informe']}")
    if codigo == 2:
        criticos = "; ".join(c["detalle"] for c in informe["cambios"] if c["severidad"] == "critico")[:600]
        raise SystemExit(f"SIGEVA cambio en algo que usa la skill ({resumen}): {criticos}. "
                         f"No se sigue hasta corregirlo. Informe: {informe['informe']}")
    log(f"Verificacion previa OK ({resumen})" + ("; documentacion actualizada." if informe.get("aceptado") else "."))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="comando", required=True)

    def comun(p, navegador: bool = False):
        p.add_argument("--config", help="config.json (base, rol, persona_id, declarante, area_conocimiento)")
        p.add_argument("--dir", default="sigeva-trabajo", help="carpeta de trabajo (inventario, catalogo, estado, capturas)")
        if navegador:
            p.add_argument("--headless", action="store_true",
                           help="sin ventana: solo con credenciales del entorno o contra el simulador de pruebas")
            p.add_argument("--env-file", help=".env con USER/PASS: se usan solo para autenticar, nunca se escriben")
            p.add_argument("--referencias", default=str(REFERENCIAS), help="carpeta de mapa-base.json y mapa-sitio.md")
            p.add_argument("--max-pantallas", type=int, default=300)
            p.add_argument("--pausa-ms", type=int, default=1_000, help="espera entre pantallas (no martillar el servidor)")
            if p.prog.split()[-1] not in ("mapear", "verificar"):
                p.add_argument("--vigencia-horas", type=float, default=6,
                               help="reusar una verificacion aprobada de las ultimas N horas (0 = verificar siempre)")
        return p

    sub.add_parser("doctor", help="verifica Python, Playwright y Chromium")
    p = comun(sub.add_parser("bib", help="BibTeX -> registros.json (articulos y eventos)"))
    p.add_argument("--bib", required=True)
    p.add_argument("--salida", default="registros.json")
    comun(sub.add_parser("inventario", help="lee lo ya cargado (solo lectura)"), navegador=True)
    p = comun(sub.add_parser("catalogo", help="ids de revistas, instituciones y persona (solo lectura)"), navegador=True)
    p.add_argument("--limite", type=int, default=0, help="registros a abrir (0 = todos)")
    p = comun(sub.add_parser("inspeccionar", help="releva los campos de un formulario sin enviarlo"), navegador=True)
    p.add_argument("--url", required=True, help="ruta relativa a la base, p. ej. eva/bcoPremio.do?accion=Nuevo")
    p = comun(sub.add_parser("institucion", help="busca una institucion en el catalogo oficial de SIGEVA (solo lectura)"), navegador=True)
    p.add_argument("--texto", required=True, help="parte del nombre (minimo 3 caracteres), p. ej. RAVIGNANI")
    p.add_argument("--pais", default="Argentina", help="etiqueta del pais en SIGEVA")
    p.add_argument("--provincia", help="etiqueta exacta de la provincia (con Argentina suele ser obligatoria)")
    p = comun(sub.add_parser("modificar", help="edita un registro existente sin dejar duplicados (en seco sin --guardar)"),
              navegador=True)
    p.add_argument("--tipo", required=True, choices=TIPOS_PUBLICACION)
    p.add_argument("--titulo", required=True, help="titulo tal como figura en la lista (debe coincidir con uno solo)")
    p.add_argument("--campo", action="append", help='nombre=valor, repetible; valor JSON para selects: \'idioma={"etiqueta":"Español"}\'')
    p.add_argument("--guardar", action="store_true", help="apretar Modificar de verdad y verificar la lista")
    p.add_argument("--borrar-duplicado", action="store_true",
                   help="si SIGEVA deja el registro viejo junto al nuevo, borrar el viejo tras verificar el nuevo")
    p = comun(sub.add_parser("cv", help="cruza un CV (.docx/.pdf/.txt) con el inventario: que falta cargar (sin red)"))
    p.add_argument("--cv", required=True)
    p.add_argument("--inventario")
    p.add_argument("--desde", type=int, help="solo trabajos de este año en adelante")
    p.add_argument("--excluir", help="JSON con titulos del CV que la persona confirmo que ya estan (otro titulo en SIGEVA)")
    p = sub.add_parser("pdf", help="recorta y/o comprime un PDF para usarlo como full text")
    p.add_argument("--entrada", required=True)
    p.add_argument("--salida", required=True)
    p.add_argument("--paginas", help='paginas 1-based a conservar, p. ej. "2,45-53" (creditos con ISBN + el trabajo)')
    p.add_argument("--comprimir", action="store_true")
    p.add_argument("--max-mb", type=float, default=30.0)
    p = comun(sub.add_parser("preparar", help="resuelve ids, valida y descarta lo ya cargado (sin red)"))
    p.add_argument("--registros", required=True)
    p.add_argument("--catalogo")
    p.add_argument("--inventario")
    p = comun(sub.add_parser("cargar", help="llena formularios; guarda solo con --guardar"), navegador=True)
    p.add_argument("--registros", required=True)
    p.add_argument("--guardar", action="store_true", help="guardar de verdad (sin esto: en seco, con capturas)")
    p.add_argument("--limite", type=int, default=LIMITE_DEFECTO)
    p.add_argument("--claves", nargs="+", help="cargar solo estas claves")
    p.add_argument("--confirmar", action="store_true", help="pedir confirmacion en la terminal antes de cada guardado")
    for nombre, ayuda in (("mapear", "recorre el Banco de Datos en solo lectura y documenta su estructura"),
                          ("verificar", "compara el sitio real con la linea base y con el contrato del cargador")):
        p = comun(sub.add_parser(nombre, help=ayuda), navegador=True)
        p.add_argument("--aceptar", action="store_true", help="adoptar el mapa actual como linea base y regenerar la documentacion")
        if nombre == "verificar":
            p.add_argument("--mapa", help="comparar un mapa ya capturado en vez de recorrer el sitio")
            p.add_argument("--auto", action="store_true",
                           help="adopta solo cambios no criticos y registra todo en el historial (es lo que corre al inicio de cada trabajo)")
    args = parser.parse_args(argv)
    if getattr(args, "env_file", None):
        cargar_env(args.env_file)
    comandos = {"doctor": cmd_doctor, "bib": cmd_bib, "inventario": cmd_inventario, "catalogo": cmd_catalogo,
                "inspeccionar": cmd_inspeccionar, "institucion": cmd_institucion, "preparar": cmd_preparar, "cargar": cmd_cargar,
                "modificar": cmd_modificar, "cv": cmd_cv, "pdf": cmd_pdf, "mapear": cmd_mapear, "verificar": cmd_verificar}
    return comandos[args.comando](args)


if __name__ == "__main__":
    sys.exit(main())
