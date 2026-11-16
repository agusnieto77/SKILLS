"""Módulo de convocatorias (presentación/solicitud) de SIGEVA: PIP y similares.

Complementa el Banco de Datos (sigeva_bd.py) con el trámite de presentación que se
entra por el rol "Usuario presentación/solicitud" (redirect(72)). Misma disciplina:

- `pip-mapear` recorre el módulo en solo lectura y arma la línea base
  (references/mapa-pip-base.json). Nunca envía formularios ni aprieta ENVIAR.
- `pip-verificar --auto` corre al inicio de todo trabajo contra el módulo.
- `pip-preparar` valida un pip.json (datos del trámite) sin red: lo que falta se
  informa y bloquea; nada se completa con algo plausible.
- `pip-cargar` llena cada sección en seco por defecto y, solo con `--guardar`,
  guarda y vuelve a leer la tabla de estados hasta que la sección dice "Ok".
- `ENVIAR PRESENTACIÓN` NUNCA lo aprieta `pip-cargar`. Existe `pip-enviar`, aparte,
  que exige `--confirmo-enviar` y que todos los estados estén en "Ok"; la vía
  preferida es que la persona lo aprete a mano.

El trámite es una declaración jurada: los datos los declara la persona en pip.json;
los nombres de campo de cada formulario salen del mapa o de `inspeccionar`.

Contador de estados: la cantidad exacta la da la tabla del trámite (el módulo PIP
2026-2028 muestra 11 ítems); nada se hardcodea: el cargador lee y relee la tabla.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import sigeva_bd as B
import sigeva_mapa as M

ROL_PRESENTACION = 72
BASE_PIP = "mapa-pip-base.json"
DOC_PIP = "mapa-pip-sitio.md"
VERIF_PIP = "ultima-verificacion-pip.json"
MAX_PDF_MB = 35.0  # El BD usa 35 MB; el límite real del módulo se releva con inspeccionar.
INTENTOS_ESTADO = 6  # x 10 s: igual que la confirmacion de altas, por guardados demorados.
PAUSA_GUARDADO_MS = 4_000
RE_OK = re.compile(r"^ok$", re.I)
RE_SIN_DATOS = re.compile(r"sin\s+datos", re.I)
RE_ENVIAR = re.compile(r"enviar", re.I)
RE_MONTO = re.compile(r"^\d{1,9}(,\d{1,2})?$")
ROLES_GRUPO = {"Titular": "1", "Co-titular": "2", "Investigador": "3", "Becario": "4", "Prof técnico": "5"}

SECCIONES_ESPERADAS = [  # informativo (PIP 2026-2028): la tabla real del trámite manda.
    "Datos del proyecto", "Aspectos éticos", "Seguridad", "Recusación",
    "Grupo de Investigación", "Financiamiento Básico", "Financiamiento Adicional",
    "Otras Fuentes de Financiamiento", "Plan de trabajo (PDF)", "Aval de la autoridad máxima (PDF firmado)",
]

MALOS = {"error", "rechazado", "no-guardado", "corte"}


class ErrorPip(RuntimeError):
    """Un ítem no se pudo llenar o guardar; la tanda puede seguir."""


class CortePip(RuntimeError):
    """Algo hace dudar de todo lo que sigue (sección que no aparece, trámite cambiado)."""


def log(mensaje: str) -> None:
    B.log(mensaje)


def _rotulo(texto: str) -> str:
    return B.sin_acentos(texto or "").lower().strip()


def _linea_base(referencias: Path) -> dict:
    base = B.leer_json(referencias / BASE_PIP)
    if base is None:
        raise SystemExit(f"No hay línea base PIP en {referencias}: correr 'pip-mapear --aceptar' primero")
    return base


def _es_base_real(config: dict) -> bool:
    # cargar_config normaliza la base con "/" final: comparar sin ella.
    return str(config.get("base", "")).rstrip("/") == B.BASE_DEFECTO.rstrip("/")


def _chequear_origen(base: dict, config: dict) -> None:
    """La línea base del simulador no habilita trabajos contra el sitio real (y viceversa)."""
    origen = base.get("origen", "real")
    real = _es_base_real(config)
    if origen != ("real" if real else "simulador"):
        raise SystemExit(
            f"La línea base PIP es de origen '{origen}' pero la base configurada es "
            f"{'el sitio real' if real else 'el simulador'}: correr 'pip-mapear --aceptar' contra esa base primero.")


def _excepciones_de_modulo() -> None:
    """En convocatorias tramiteId es estructura y las altas usan acciones propias."""
    M.IDS_ESTRUCTURALES_EXTRA = {"tramiteid"}
    M.ACCIONES_SEGURAS_EXTRA = {"alta", "editaralta", "cargar", "verificar"}


def _ir_a_presentacion(s: B.Sesion) -> None:
    """Entra por el rol de presentación (72) en vez del Banco de Datos (96)."""
    s.iniciar(rol=int(s.config.get("rol_presentacion") or ROL_PRESENTACION))


def _ruta_actual(s: B.Sesion) -> str:
    return M.canonica(s.page.url)


def _landing(s: B.Sesion, base: dict) -> str:
    ruta = base.get("inicio_pip")
    if not ruta:
        raise SystemExit("La línea base PIP no dice cuál es la pantalla de inicio (inicio_pip): "
                         "correr 'pip-mapear --aceptar'")
    s.page.goto(s.url(B._ruta_eva(ruta)), wait_until="domcontentloaded", timeout=60_000)
    s.page.wait_for_load_state("load", timeout=60_000)
    return ruta


def _navegar(s: B.Sesion, ruta: str) -> None:
    """Navega a una ruta del módulo: las relativas viven bajo /eva/ (B._ruta_eva)."""
    s.page.goto(s.url(B._ruta_eva(ruta)), wait_until="domcontentloaded", timeout=60_000)
    s.page.wait_for_load_state("load", timeout=60_000)


def _filas_tramites(s: B.Sesion) -> list[dict]:
    """Enlaces a trámites (index.do?tramiteid=N) con el texto de su fila contenedora."""
    return s.page.evaluate("""() => {
        const res = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href') || '';
            if (!/tramiteid=\\d+/.test(href)) return;
            let el = a.parentElement, cont = '';
            for (let i = 0; i < 6 && el; i++) {
                const t = (el.innerText || '').trim().replace(/\\s+/g, ' ');
                if (t.length > 20) { cont = t.slice(0, 300); break; }
                el = el.parentElement;
            }
            res.push({ruta: href, texto: cont || a.innerText || href});
        });
        return res;
    }""")


def _ir_postulaciones(s: B.Sesion, intentos: int = 3) -> str:
    """Abre MIS POSTULACIONES (la página a veces devuelve 500: reintentar).

    El enlace vive en el menú de las páginas internas, no siempre en el inicio:
    si no está en la página actual, se baja un nivel por los enlaces del menú
    (p. ej. CONVOCATORIAS) hasta encontrarlo.
    """
    def _menu_postulaciones() -> str | None:
        for e in s.page.evaluate(M.JS_ESTRUCTURA)["enlaces"]:
            if "postulacion" in _rotulo(e["texto"]):
                c = M.clasificar_url(e["href"], s.page.url, s.base)
                if c["visitar"]:
                    return c["ruta"]
        return None
    menu = _menu_postulaciones()
    if menu is None:
        vistos: set[str] = set()
        for e in s.page.evaluate(M.JS_ESTRUCTURA)["enlaces"]:
            c = M.clasificar_url(e["href"], s.page.url, s.base)
            if c["visitar"] and c["ruta"] not in vistos:
                vistos.add(c["ruta"])
                _navegar(s, c["ruta"])
                menu = _menu_postulaciones()
                if menu is not None:
                    break
    if menu is None:
        raise SystemExit("En el módulo no hay enlace a MIS POSTULACIONES.")
    for i in range(intentos):
        _navegar(s, menu)
        if "500" not in (s.page.title() or ""):
            return menu
        log(f"    MIS POSTULACIONES devolvió 500 (intento {i + 1}/{intentos}); esperando y reintentando...")
        s.page.wait_for_timeout(5000)
    raise SystemExit(f"MIS POSTULACIONES sigue devolviendo 500 tras {intentos} intentos (falla de SIGEVA, no de la skill).")


def _buscar_tramite(s: B.Sesion, codigo: str | None) -> tuple[str, str, set[str]]:
    """Encuentra el trámite por su código.

    El código es el que muestra SIGEVA, p. ej. 11220260100119CO. Primero busca
    enlaces directos al trámite en la página actual (simulador y accesos directos);
    si no hay, va a MIS POSTULACIONES y elige la fila por código. Sin código, y
    solo si hay exactamente un trámite, usa ese; con varios, pide --tramite (con
    nombres legibles). Devuelve (ruta, titulo, otras_rutas).
    """
    directos = []
    for e in s.page.evaluate(M.JS_ESTRUCTURA)["enlaces"]:
        c = M.clasificar_url(e["href"], s.page.url, s.base)
        if c["visitar"] and "solicitud" in c["ruta"].lower():
            directos.append({"ruta": c["ruta"], "texto": e["texto"] or c["ruta"]})
    if codigo:
        clave = _rotulo(codigo)
        exactos = [c for c in directos
                   if clave in _rotulo(c["texto"]) or clave in _rotulo(c["ruta"])]
        if len(exactos) == 1:
            return exactos[0]["ruta"], exactos[0]["texto"], set()
    elif len(directos) == 1:
        return directos[0]["ruta"], directos[0]["texto"], set()
    _ir_postulaciones(s)
    candidatos = _filas_tramites(s)
    if codigo:
        clave = _rotulo(codigo)
        exactos = [c for c in candidatos
                   if clave in _rotulo(c["texto"]) or clave in _rotulo(c["ruta"])]
    elif len(candidatos) == 1:
        exactos = candidatos
    else:
        exactos = []
    if len(exactos) != 1:
        lista = "\n".join(f"  - {c['texto'][:110]} -> {c['ruta']}" for c in candidatos) or "  (ninguno)"
        raise SystemExit(f"No pude identificar el trámite (código: {codigo or 'no indicado'}). Trámites:\n{lista}\n"
                         "Correr con --tramite <código>.")
    otros = {M.canonica(c["ruta"]) for c in candidatos if c["ruta"] != exactos[0]["ruta"]}
    return exactos[0]["ruta"], exactos[0]["texto"], otros


def abrir_tramite(s: B.Sesion, base: dict, codigo: str | None) -> str:
    """Abre la pantalla del trámite y devuelve su ruta canónica."""
    _landing(s, base)
    ruta, titulo, _otros = _buscar_tramite(s, codigo)
    _navegar(s, ruta)
    return ruta


def leer_estados(s: B.Sesion) -> list[dict]:
    """Lee la tabla de estados del trámite abierto en la página actual.

    Cada fila: {seccion, estado, enlace}. `enlace` es el href de apertura cuando la
    sección lo ofrece; las que dependen del Banco de Datos pueden no tenerlo.
    """
    html = s.descargar(B._ruta_eva(_ruta_actual(s)))
    filas = []
    for tabla in B.parsear_tablas(html):
        for f in tabla["filas"]:
            celdas = [c.strip() for c in f["celdas"] if c.strip()]
            if not celdas:
                continue
            ok = any(RE_OK.fullmatch(c) for c in celdas)
            sin = any(RE_SIN_DATOS.search(c) for c in celdas)
            if not ok and not sin:
                continue
            etiqueta = next((c for c in celdas if not RE_OK.fullmatch(c) and not RE_SIN_DATOS.search(c)),
                            celdas[0] if len(celdas) > 1 else "")
            etiqueta = etiqueta.lstrip("- ").strip()
            filas.append({"seccion": etiqueta, "estado": "Ok" if ok else "Sin Datos",
                          "enlace": (f["enlaces"][0] if f["enlaces"] else "")})
    return filas


def _resumen_estados(filas: list[dict]) -> dict[str, str]:
    return {f["seccion"]: f["estado"] for f in filas}


def _fila_estado(estados: list[dict], seccion: str) -> dict | None:
    objetivo = _rotulo(seccion)
    exactas = [f for f in estados if _rotulo(f["seccion"]) == objetivo]
    if exactas:
        return exactas[0]
    parciales = [f for f in estados if objetivo and objetivo in _rotulo(f["seccion"])]
    return parciales[0] if len(parciales) == 1 else None


# --------------------------------------------------------------------------- mapear / verificar

def _verificacion_pip_actual(s: B.Sesion, args, config: dict, trabajo: Path, codigo: str | None) -> dict:
    """Mapa del módulo de convocatorias con una sesión ya iniciada en el rol 72."""
    _excepciones_de_modulo()
    inicio = _ruta_actual(s)
    ruta_tramite, titulo, otros = _buscar_tramite(s, codigo)
    _navegar(s, ruta_tramite)
    estructuras = s.page.evaluate(M.JS_ESTRUCTURA)
    estados_tabla = next((t["id"] for t in estructuras["tablas"]
                          if any("estado" in c.lower() for c in t["cabecera"])), "") \
        or _id_tabla_estados_por_html(s)
    log(f"Mapeando el módulo de convocatorias en solo lectura (trámite: {titulo[:70]})...")
    mapa = M.mapear(s, [inicio, ruta_tramite], max_pantallas=args.max_pantallas,
                    pausa_ms=args.pausa_ms, log=log, excluir=otros)
    mapa = {"capturado_en_utc": B.ahora_utc(), "base": config["base"], "modulo": "pip",
            "origen": "real" if _es_base_real(config) else "simulador",
            "inicio_pip": inicio, "tramite_pantalla": M.canonica(ruta_tramite),
            "tramite": titulo, "estados_tabla_id": estados_tabla, **mapa}
    ruta = trabajo / "mapas" / f"mapa-pip-{datetime.now():%Y%m%d-%H%M%S}.json"
    B.escribir_json(ruta, mapa)
    log(f"Mapa completo (local) en {ruta}")
    return mapa


def _id_tabla_estados_por_html(s: B.Sesion) -> str:
    html = s.descargar(B._ruta_eva(_ruta_actual(s)))
    for t in B.parsear_tablas(html):
        cuerpo = _rotulo(" ".join(" ".join(f["celdas"]) for f in t["filas"]))
        if RE_SIN_DATOS.search(cuerpo) or re.search(r"\bok\b", cuerpo):
            return t.get("id") or ""
    return ""


def _chequear_enviar(actual: dict, base: dict) -> list[dict]:
    """El botón ENVIAR debe existir (para saber que el trámite es enviable); nunca se aprieta solo."""
    pantalla = base.get("tramite_pantalla")
    p = M._pantalla_de(actual, pantalla) if pantalla else None
    if p is None:
        return []
    botones = {b for f in p.get("formularios", []) for b in f.get("botones", [])}
    if not any(RE_ENVIAR.search(b) for b in botones):
        return [{"severidad": "alto", "pantalla": pantalla, "tipo": "contrato-boton",
                 "detalle": "el trámite ya no muestra el botón ENVIAR (¿enviado, vencido o cambió el sitio?): revisar"}]
    return []


def _contrato_pip(base: dict) -> list[dict]:
    """Contrato del trámite: pantalla y tabla de estados. El ENVIAR se chequea aparte (_chequear_enviar)."""
    pantalla = base.get("tramite_pantalla")
    if not pantalla:
        return [{"severidad": "critico", "pantalla": "-", "tipo": "contrato-pantalla",
                 "detalle": "la línea base PIP no registró la pantalla del trámite (tramite_pantalla)"}]
    contrato = {"uso": "estados del trámite", "pantalla": pantalla}
    if base.get("estados_tabla_id"):
        contrato["tablas"] = {base["estados_tabla_id"]: {"columnas": ["ESTADO"]}}
    return [contrato]


def _aceptar_mapa_pip(mapa: dict, referencias: Path) -> dict:
    saneado = M.sanear(mapa)
    documento = _documento_pip(saneado)
    contenido = json.dumps(saneado, ensure_ascii=False) + documento
    secretos = [os.environ.get(k) for k in ("SIGEVA_USER", "SIGEVA_PASS")]
    if any(s and len(s) >= 3 and s in contenido for s in secretos):
        raise SystemExit("El mapa contiene una credencial: no se escribe la línea base.")
    B.escribir_json(referencias / BASE_PIP, saneado)
    (referencias / DOC_PIP).write_text(documento, encoding="utf-8")
    return {"linea_base": str(referencias / BASE_PIP), "documento": str(referencias / DOC_PIP),
            "origen": saneado.get("origen"), "inicio_pip": saneado.get("inicio_pip")}


def _documento_pip(mapa: dict) -> str:
    lineas = [f"# Mapa del módulo de convocatorias ({mapa.get('tramite', 'PIP')})",
              "", f"- Origen: **{mapa.get('origen')}** (capturado {mapa.get('capturado_en_utc')})",
              f"- Inicio del módulo: `{mapa.get('inicio_pip')}`",
              f"- Pantalla del trámite: `{mapa.get('tramite_pantalla')}` "
              f"(tabla de estados: `{mapa.get('estados_tabla_id') or 'sin id'}`)", "",
              "| Pantalla | Tipo | Campos | Botones |", "|---|---|---|---|"]
    for ruta, p in sorted(mapa.get("pantallas", {}).items()):
        campos = sum(len(f.get("campos", [])) for f in p.get("formularios", []))
        botones = sorted({b for f in p.get("formularios", []) for b in f.get("botones", [])})
        lineas.append(f"| `{ruta}` | {p.get('tipo')} | {campos} | {', '.join(botones[:6])} |")
    if mapa.get("errores"):
        lineas += ["", "## Errores de recorrido", ""] + [f"- `{k}`: {v}" for k, v in mapa["errores"].items()]
    return "\n".join(lineas) + "\n"


def _verificar_pip(actual: dict, base: dict, referencias: Path, trabajo: Path,
                   auto: bool, aceptar: bool) -> tuple[dict, int]:
    cambios = M.verificar_contrato(actual, _contrato_pip(base)) + M.comparar_mapas(base, M.sanear(actual)) \
        + _chequear_enviar(actual, base)
    orden = {s: i for i, s in enumerate(M.SEVERIDADES)}
    cambios.sort(key=lambda c: (orden[c["severidad"]], c["pantalla"], c["tipo"]))
    informe = {"verificado_en_utc": B.ahora_utc(), "modulo": "pip",
               "linea_base_capturada": base.get("capturado_en_utc"),
               "version_base": base.get("version_sigeva"), "version_actual": actual.get("version_sigeva"),
               "recorrido_completo": actual.get("completo"), "errores_recorrido": actual.get("errores"),
               "resumen": M.resumen_cambios(cambios), "cambios": cambios}
    ruta = trabajo / "verificaciones" / f"verificacion-pip-{datetime.now():%Y%m%d-%H%M%S}.json"
    B.escribir_json(ruta, informe)
    informe["informe"] = str(ruta)
    criticos = informe["resumen"]["critico"]
    adoptar = aceptar or (auto and actual.get("completo") and not criticos)
    if adoptar and (cambios or aceptar):
        informe["aceptado"] = _aceptar_mapa_pip(actual, referencias)
    if cambios:
        M.registrar_historial(referencias / "historial-cambios.md", informe, adoptado=bool(adoptar))
    if not actual.get("completo"):
        codigo = 1
    elif auto:
        codigo = 2 if criticos else 0
    else:
        codigo = 2 if cambios and not aceptar else 0
    B.escribir_json(trabajo / VERIF_PIP, {"verificado_en_utc": informe["verificado_en_utc"], "codigo": codigo,
                                          "resumen": informe["resumen"], "referencias": str(referencias.resolve()),
                                          "informe": str(ruta)})
    return informe, codigo


def verificacion_previa_pip(s: B.Sesion, args, config: dict, trabajo: Path, codigo: str | None) -> None:
    """`pip-verificar --auto` al inicio de cada trabajo contra el módulo (misma sesión)."""
    referencias = Path(args.referencias)
    base = _linea_base(referencias)
    _chequear_origen(base, config)
    ultima = B.leer_json(trabajo / VERIF_PIP, {})
    if getattr(args, "vigencia_horas", 6) > 0 and ultima.get("codigo") == 0 \
            and ultima.get("referencias") == str(referencias.resolve()):
        edad_h = (datetime.now(timezone.utc) - datetime.fromisoformat(ultima["verificado_en_utc"])).total_seconds() / 3600
        if edad_h < args.vigencia_horas:
            log(f"Verificación PIP vigente ({edad_h:.1f} h): no se repite el recorrido.")
            return
    log("Verificando el módulo de convocatorias antes de empezar (pip-verificar --auto)...")
    informe, codigo_v = _verificar_pip(_verificacion_pip_actual(s, args, config, trabajo, codigo),
                                       base, referencias, trabajo, auto=True, aceptar=False)
    resumen = ", ".join(f"{k} {v}" for k, v in informe["resumen"].items())
    if codigo_v == 1:
        raise SystemExit(f"La verificación PIP no pudo recorrer el módulo ({informe['errores_recorrido']}). No se sigue.")
    if codigo_v == 2:
        criticos = "; ".join(c["detalle"] for c in informe["cambios"] if c["severidad"] == "critico")[:600]
        raise SystemExit(f"El módulo de convocatorias cambió en algo que usa la skill ({resumen}): {criticos}. No se sigue.")
    log(f"Verificación PIP previa OK ({resumen})" + ("; documentación actualizada." if informe.get("aceptado") else "."))


# --------------------------------------------------------------------------- preparar (sin red)

def validar_pip(datos: dict, config: dict) -> dict:
    """Valida pip.json como declaración: lo que falta bloquea, nada se estima."""
    limite_mb = float(config.get("limite_adjunto_mb") or MAX_PDF_MB)
    errores, items = [], []
    tramite = str(datos.get("tramite") or "").strip()
    if not tramite or not re.search(r"\d{6,}", tramite):
        errores.append("falta 'tramite' (el código que muestra SIGEVA, p. ej. 11220260100119CO)")
    secciones = datos.get("secciones")
    if not isinstance(secciones, list) or not secciones:
        errores.append("falta 'secciones' (lista con al menos una sección a completar)")
        secciones = []
    claves: set[str] = set()
    for i, s in enumerate(secciones, 1):
        clave = str(s.get("clave") or "").strip()
        if not clave:
            errores.append(f"sección {i}: falta 'clave'")
            continue
        if clave in claves:
            errores.append(f"clave duplicada: {clave}")
        claves.add(clave)
        item = {"clave": clave, "seccion": str(s.get("seccion") or "").strip(),
                "campos": s.get("campos") or {}, "avisos": []}
        if not item["seccion"]:
            errores.append(f"{clave}: falta 'seccion' (el nombre tal como figura en la tabla de estados)")
        grilla = s.get("grilla")
        if grilla is not None:
            if not isinstance(grilla, dict) or not grilla:
                errores.append(f"{clave}: 'grilla' debe ser un dict rubro -> {{año: monto}}")
            else:
                for rubro, por_anio in grilla.items():
                    if not isinstance(por_anio, dict) or not por_anio:
                        errores.append(f"{clave}: grilla sin años para el rubro {rubro!r}")
                        continue
                    for anio, monto in por_anio.items():
                        if not isinstance(monto, str) or not RE_MONTO.fullmatch(monto.strip()):
                            errores.append(f"{clave}: monto inválido para rubro {rubro} año {anio}: {monto!r} "
                                           "(formato: dígitos con decimales opcionales tras coma, p. ej. 6500000,00)")
                item["grilla"] = {str(k): {str(a): str(v).strip() for a, v in d.items()} for k, d in grilla.items()}
        for dep in s.get("dependientes") or []:
            if not all(str(dep.get(k) or "").strip() for k in ("combo_padre", "valor_padre", "combo", "valor")):
                errores.append(f"{clave}: dependiente mal especificado (combo_padre, valor_padre, combo, valor): {dep!r}")
            else:
                item.setdefault("dependientes", []).append({k: str(dep[k]).strip() for k in
                                                           ("combo_padre", "valor_padre", "combo", "valor")})
        miembros = s.get("miembros")
        if miembros is not None:
            if not isinstance(miembros, list) or not miembros:
                errores.append(f"{clave}: 'miembros' debe ser una lista no vacía")
            else:
                vistos_m: set[str] = set()
                for m in miembros:
                    nombre = str(m.get("nombre") or "").strip()
                    ded = str(m.get("dedicacion") or "").strip()
                    if not nombre:
                        errores.append(f"{clave}: miembro sin 'nombre'")
                    if _rotulo(nombre) in vistos_m:
                        errores.append(f"{clave}: miembro duplicado: {nombre}")
                    vistos_m.add(_rotulo(nombre))
                    if not re.fullmatch(r"\d{1,3}", ded) or int(ded) > 100:
                        errores.append(f"{clave}: dedicación inválida para {nombre}: {ded!r} (0-100)")
                    if m.get("rol") and m["rol"] not in ROLES_GRUPO:
                        errores.append(f"{clave}: rol inválido para {nombre}: {m['rol']!r} "
                                       f"(opciones: {', '.join(ROLES_GRUPO)})")
                item["miembros"] = [{"nombre": str(m.get("nombre", "")).strip(),
                                     "dedicacion": str(m.get("dedicacion", "")).strip(),
                                     **({"rol": m["rol"]} if m.get("rol") else {})} for m in miembros]
        filas = s.get("filas")
        if filas is not None:
            if not isinstance(filas, list) or not filas or not all(isinstance(x, dict) and x for x in filas):
                errores.append(f"{clave}: 'filas' debe ser una lista no vacía de dicts columna -> valor")
            else:
                columnas = list(filas[0])
                for n, fila in enumerate(filas, 1):
                    if list(fila) != columnas:
                        errores.append(f"{clave}: la fila {n} no tiene las mismas columnas que la primera ({columnas})")
                    vacias = [c for c in columnas if not str(fila.get(c) or "").strip()]
                    if vacias:
                        errores.append(f"{clave}: fila {n} con columnas vacías (no se estiman): {', '.join(vacias)}")
                item["filas"] = [{c: str(fila.get(c) or "").strip() for c in columnas} for fila in filas]
        seleccion = s.get("seleccion")
        if seleccion is not None:
            campo = str((seleccion or {}).get("campo") or "").strip()
            valores = [str(v).strip() for v in (seleccion or {}).get("valores") or []]
            if not campo or not valores or not all(valores) or len(set(valores)) != len(valores):
                errores.append(f"{clave}: 'seleccion' requiere 'campo' y 'valores' (lista no vacía, sin repetidos)")
            item["seleccion"] = {"campo": campo, "valores": valores}
        if not item["campos"] and not s.get("archivo") and not grilla and miembros is None \
                and filas is None and seleccion is None:
            if s.get("guardar_vacio"):
                item["guardar_vacio"] = True
                item["avisos"].append("guardado vacío a pedido explícito (nada para declarar)")
            else:
                errores.append(f"{clave}: sin 'campos', 'archivo', 'grilla', 'miembros', 'filas' ni 'seleccion': "
                               "nada para completar")
        archivo = s.get("archivo")
        if archivo:
            ruta = Path(str(archivo.get("ruta") or ""))
            if not ruta.exists():
                errores.append(f"{clave}: el archivo no existe: {ruta}")
            else:
                peso = ruta.stat().st_size
                with open(ruta, "rb") as fh:
                    es_pdf = fh.read(5) == b"%PDF-"
                if not es_pdf:
                    errores.append(f"{clave}: el adjunto no es un PDF: {ruta.name}")
                if peso > limite_mb * 1024 * 1024:
                    errores.append(f"{clave}: el adjunto pesa {peso / 1048576:.1f} MB y el límite relevado es {limite_mb:g} MB")
            if not str(archivo.get("tipo") or "").strip():
                errores.append(f"{clave}: falta 'tipo' del adjunto (el valor de tipoArchivo del slot: ver pip.md)")
            item["archivo"] = {"ruta": str(ruta), "campo": str(archivo.get("campo") or "theFile"),
                               "tipo": str(archivo.get("tipo") or "").strip()}
        if isinstance(item["campos"], dict):
            vacios = [k for k, v in item["campos"].items() if v in (None, "", [])]
            if vacios:
                errores.append(f"{clave}: campos con valor vacío (no se estiman): {', '.join(vacios)}")
        items.append(item)
    return {"tramite": tramite, "errores": errores, "items": items, "limite_adjunto_mb": limite_mb}


def _resolver_dependientes(f: B.Formulario, item: dict) -> None:
    """Selects con opciones por AJAX: elige el padre, espera las opciones del hijo y lo fija.

    Igual que Formulario.area pero genérico: item["dependientes"] =
    [{combo_padre, valor_padre, combo, valor}].
    """
    for dep in item.get("dependientes") or []:
        f.elegir(dep["combo_padre"], valor=str(dep["valor_padre"]))
        hallado: list[str] = []
        for _ in range(20):
            f.page.wait_for_timeout(300)
            hallado = [v for v, t in f.opciones(dep["combo"]) if v == str(dep["valor"])]
            if len(hallado) == 1:
                f.elegir(dep["combo"], valor=hallado[0])
                break
        if len(hallado) != 1:
            reales = [(v, t[:60]) for v, t in f.opciones(dep["combo"]) if v and not v.startswith("-")]
            raise ErrorPip(f"no apareció la opción {dep['valor']!r} en {dep['combo']}. Opciones: {reales or 'ninguna'}")


def cmd_pip_preparar(args) -> int:
    _excepciones_de_modulo()
    config = B.cargar_config(args.config)
    datos = B.leer_json(args.datos, None)
    if datos is None:
        raise SystemExit(f"No pude leer {args.datos}")
    salida = validar_pip(datos, config)
    ruta = Path(args.salida) if args.salida else Path(args.datos).with_name("pip-listos.json")
    B.escribir_json(ruta, salida)
    print(json.dumps({"salida": str(ruta), "items": len(salida["items"]), "errores": salida["errores"]},
                     ensure_ascii=False, indent=1))
    return 1 if salida["errores"] else 0


# --------------------------------------------------------------------------- cargar

def _abrir_formulario(s: B.Sesion, fila: dict) -> None:
    enlace = fila.get("enlace") or ""
    if not enlace:
        raise ErrorPip("la sección no ofrece enlace de carga desde el trámite: resolvésela primero en el lugar que "
                       "corresponda (p. ej. integrantes declarados en el Banco de Datos)")
    s.page.goto(s.url(B._ruta_eva(enlace)), wait_until="domcontentloaded", timeout=60_000)
    s.page.wait_for_load_state("load", timeout=60_000)


def _mapear_grilla_montos(f: B.Formulario) -> list[dict]:
    """Lee la grilla real de montos: por input, etiqueta del rubro y código ubicaciones.

    Devuelve [{indice, etiqueta, rubro, anio}]. El código 'ubicaciones' trae
    "rubro-año-..." (ids internos de SIGEVA, que NO siempre coinciden con el número
    visible del rubro). La etiqueta es la última celda de la fila con "(N)"
    (el agrupador "GASTOS DE ..." va primero; en "OTROS GASTOS (8)" es la única).
    """
    filas = f.page.evaluate("""() => Array.from(document.querySelectorAll("input[name='montos']")).map(inp => {
        const tr = inp.closest('tr');
        const celdas = tr ? Array.from(tr.cells).map(td => (td.innerText || '').trim().replace(/\\s+/g, ' ')) : [];
        const nums = celdas.filter(t => /\\(\\d+\\)/.test(t));
        const etq = nums.length ? nums[nums.length - 1] : '';
        const td = inp.closest('td');
        const hid = td ? td.querySelector("input[name='ubicaciones']") : null;
        return {label: etq.slice(0, 80), ubi: hid ? hid.value : ''};
    })""")
    mapa = []
    for i, r in enumerate(filas):
        partes = (r["ubi"] or "").split("-")
        rubro, anio = (partes[0], partes[1]) if len(partes) >= 2 else ("", "")
        mapa.append({"indice": i, "etiqueta": r["label"], "rubro": rubro, "anio": anio})
    return mapa


def planificar_grilla(mapa: list[dict], grilla: dict) -> list[tuple[int, str]]:
    """Decide qué valor va en cada input de la grilla: [(indice, monto)].

    `mapa` sale de _mapear_grilla_montos; `grilla` es {codigo_rubro: {año: monto}}
    con códigos de `ubicaciones` del pip.json (ver pip.md). Pura (sin navegador).
    """
    if not mapa:
        raise ErrorPip("el formulario no tiene grilla de montos (input[name=montos])")
    por_rubro: dict[str, set] = {}
    for m in mapa:
        por_rubro.setdefault(m["rubro"], set()).add(m["etiqueta"])
    for rubro, etqs in por_rubro.items():
        if len(etqs) != 1 or not next(iter(etqs)):
            disp = "; ".join(f"{m['rubro']}/{m['anio']} ({m['etiqueta'][:30]})" for m in mapa)
            raise ErrorPip(f"la grilla es ambigua para el rubro {rubro}: etiquetas {sorted(etqs)}. "
                           f"Celdas vistas: {disp[:400]}")
    plan = []
    for rubro, por_anio in grilla.items():
        for anio, monto in por_anio.items():
            cands = [m for m in mapa if m["rubro"] == str(rubro) and m["anio"] == str(anio)]
            if len(cands) != 1:
                disp = "; ".join(f"{m['rubro']}/{m['anio']} ({m['etiqueta'][:30]})" for m in mapa)
                raise ErrorPip(f"la grilla no tiene una celda única para rubro {rubro} año {anio}. "
                               f"Celdas vistas: {disp[:400]}")
            plan.append((cands[0]["indice"], str(monto)))
    return plan


def _llenar_grilla(f: B.Formulario, grilla: dict) -> None:
    """Completa la grilla de montos {rubro: {año: "6500000,00"}} según la grilla real."""
    locs = f.page.locator("input[name='montos']")
    for indice, monto in planificar_grilla(_mapear_grilla_montos(f), grilla):
        locs.nth(indice).fill(monto)

def planificar_grupo(filas: list[dict], miembros: list[dict]) -> tuple[list[dict], list[str]]:
    """Decide qué aplicar por fila: [({indice, pid, valor_rol, dedicacion})], [avisos].

    Pura (sin navegador): filas como las lee _aplicar_grupo del DOM.
    """
    if not filas:
        raise ErrorPip("el formulario no tiene grilla de integrantes (select[name=tipoGrupoRol])")
    plan, avisos = [], []
    for m in miembros:
        objetivo = _rotulo(m["nombre"])
        cands = [r for r in filas if objetivo and objetivo in _rotulo(r["texto"])]
        if len(cands) != 1:
            avisos.append(f"no encontrado (o ambiguo) en la grilla: {m['nombre']}")
            continue
        r = cands[0]
        valor_rol = f"{r['pid']}-{ROLES_GRUPO[m['rol']]}" if m.get("rol") else None
        plan.append({"indice": r["indice"], "pid": r["pid"], "valor_rol": valor_rol,
                     "dedicacion": str(m["dedicacion"])})
    return plan, avisos


def _leer_grupo(f: B.Formulario) -> list[dict]:
    """Lee la grilla de integrantes: rol, dedicación y si está habilitado (casilla HAB)."""
    return f.page.evaluate("""() => Array.from(document.querySelectorAll("select[name='tipoGrupoRol']")).map((sel, i) => {
        const tr = sel.closest('tr');
        const tds = tr ? Array.from(tr.cells).map(td => (td.innerText || '').trim()).join(' | ') : '';
        const pid = (Array.from(sel.options).map(o => o.value).find(v => /^\\d+-\\d+$/.test(v)) || '').split('-')[0];
        const ded = tr ? (tr.querySelector("input[name='porcentajeDedicacion']") || {}).value : '';
        const hab = tr ? tr.querySelector("input[type=checkbox][name='seleccionadas']") : null;
        return {indice: i, texto: tds.slice(0, 200), pid: pid, ded: ded, rol: sel.value || '',
                hab: hab ? hab.checked : true};
    })""")


def grupo_al_dia(filas: list[dict], miembros: list[dict]) -> tuple[bool, list[str]]:
    """Dice si la grilla ya refleja lo pedido: habilitado, dedicación y rol. Pura: testeable."""
    plan, avisos = planificar_grupo(filas, miembros)
    por_indice = {r["indice"]: r for r in filas}
    for p in plan:
        actual = por_indice.get(p["indice"], {})
        if not actual.get("hab", True):
            return False, avisos
        if str(actual.get("ded") or "") != p["dedicacion"]:
            return False, avisos
        if p["valor_rol"] and actual.get("rol") != p["valor_rol"]:
            return False, avisos
    return True, avisos


def _aplicar_grupo(f: B.Formulario, miembros: list[dict]) -> list[str]:
    """Habilita (casilla HAB) y fija dedicación y rol por fila de la grilla, emparejando por nombre.

    Sin la casilla HAB la persona no integra el proyecto aunque figure en la grilla.
    Devuelve avisos para los miembros que no figuran en la grilla (no se inventan) y para
    los que quedarían sin rol.
    """
    filas = _leer_grupo(f)
    plan, avisos = planificar_grupo(filas, miembros)
    por_indice = {r["indice"]: r for r in filas}
    for p in plan:
        hab = f.page.locator(f"input[type=checkbox][name='seleccionadas'][value='{p['pid']}']")
        if hab.count() and not hab.first.is_checked() and hab.first.is_enabled():
            hab.first.check()
        if p["valor_rol"]:
            f.page.locator("select[name='tipoGrupoRol']").nth(p["indice"]).select_option(p["valor_rol"])
        elif por_indice[p["indice"]]["rol"].endswith("-0"):
            avisos.append(f"sin rol en la grilla: {por_indice[p['indice']]['texto'][:60]} (indicar 'rol')")
        f.page.locator("input[name='porcentajeDedicacion']").nth(p["indice"]).fill(p["dedicacion"])
    return avisos


def _normal(texto) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _leer_valores(f: B.Formulario, nombres: list[str]) -> dict:
    """Valor actual de cada control por name: texto, select (valor y texto), radios y casillas."""
    return f.page.evaluate("""(nombres) => Object.fromEntries(nombres.map(n => {
        const todos = Array.from(document.getElementsByName(n));
        const visibles = todos.filter(e => e.type !== 'hidden');
        const els = visibles.length ? visibles : todos;
        if (!els.length) return [n, null];
        const e = els[0];
        if (e.type === 'radio') return [n, {valor: (els.find(x => x.checked) || {}).value || ''}];
        if (e.type === 'checkbox') return [n, {valor: els.filter(x => x.checked).map(x => x.value), casilla: e.checked}];
        if (e.tagName === 'SELECT') {
            const o = e.options[e.selectedIndex] || {};
            return [n, {valor: o.value || '', texto: (o.text || '').trim()}];
        }
        return [n, {valor: e.value || ''}];
    }))""", nombres)


def diferencias_campos(actual: dict, deseado: dict) -> list[str]:
    """Nombres de los campos cuyo valor cargado no coincide con el pedido. Pura: testeable."""
    distintos = []
    for nombre, valor in deseado.items():
        a = actual.get(nombre)
        if a is None:
            distintos.append(nombre)
            continue
        if isinstance(valor, dict) and "fecha" in valor:
            igual = _normal(a.get("valor")) == _normal(valor["fecha"])
        elif isinstance(valor, dict) and "valor" in valor:
            igual = str(a.get("valor")) == str(valor["valor"])
        elif isinstance(valor, dict) and "etiqueta" in valor:
            igual = _rotulo(_normal(a.get("texto"))) == _rotulo(_normal(valor["etiqueta"]))
        elif isinstance(valor, bool):
            igual = bool(a.get("casilla")) == valor
        elif isinstance(valor, list):
            igual = sorted(map(str, valor)) == sorted(map(str, a.get("valor") or []))
        else:
            igual = _normal(a.get("valor")) == _normal(valor)
        if not igual:
            distintos.append(nombre)
    return distintos


def _leer_filas(f: B.Formulario, columnas: list[str]) -> list[list[str]]:
    """Grilla de filas repetidas (p. ej. recusación: apellido/nombre/observacion): una lista por fila."""
    valores = f.page.evaluate("""(cols) => cols.map(n => Array.from(document.getElementsByName(n))
        .filter(e => e.type !== 'hidden').map(e => e.value || ''))""", columnas)
    largo = min((len(v) for v in valores), default=0)
    return [[valores[c][i] for c in range(len(columnas))] for i in range(largo)]


def filas_al_dia(actual: list[list[str]], deseadas: list[dict]) -> bool:
    """Las filas no vacías cargadas son exactamente las pedidas, en orden. Pura: testeable."""
    llenas = [[_normal(x) for x in fila] for fila in actual if any(_normal(x) for x in fila)]
    return llenas == [[_normal(v) for v in d.values()] for d in deseadas]


def _llenar_filas(f: B.Formulario, deseadas: list[dict]) -> None:
    """Escribe las filas pedidas en orden y vacía las sobrantes (la lista declarada es la completa)."""
    columnas = list(deseadas[0])
    disponibles = len(_leer_filas(f, columnas))
    if len(deseadas) > disponibles:
        raise ErrorPip(f"la pantalla ofrece {disponibles} filas y se piden {len(deseadas)}")
    for c in columnas:
        cajas = f.page.locator(f"[name='{c}']:not([type=hidden])")
        for i in range(disponibles):
            cajas.nth(i).fill(deseadas[i][c] if i < len(deseadas) else "")


def _pagina_siguiente(s: B.Sesion) -> bool:
    """Avanza la lista paginada por su enlace "Siguiente"; False si no hay más páginas."""
    enlace = s.page.locator("a", has_text=re.compile(r"^\s*\[?Siguiente"))
    if not enlace.count():
        return False
    with s.page.expect_navigation(wait_until="load", timeout=60_000):
        enlace.first.click()
    return True


def recorrer_seleccion(s: B.Sesion, campo: str, valores: list[str], tildar: bool,
                       max_pasos: int = 2000) -> dict:
    """Recorre una lista paginada de casillas desde la página abierta.

    Con `tildar`, hace clic en cada casilla pedida que esté sin tildar; en SIGEVA cada clic
    envía el formulario y lo guarda (por eso en seco no se hace clic). Tras cada clic se sigue
    desde la página a la que vuelva el sitio. Nunca destilda: lo que ya estaba queda.
    Devuelve {tildados, sin_tildar, no_encontrados} (listas de valores).
    """
    objetivo = set(valores)
    estado: dict[str, bool] = {}
    tildados: list[str] = []
    for _ in range(max_pasos):
        pagina = s.page.evaluate("""(c) => Object.fromEntries(Array.from(document.getElementsByName(c))
            .filter(e => e.type === 'checkbox').map(e => [e.value, e.checked]))""", campo)
        estado.update(pagina)
        pendientes = [v for v, marcado in pagina.items() if v in objetivo and not marcado]
        if tildar and pendientes:
            with s.page.expect_navigation(wait_until="load", timeout=60_000):
                s.page.locator(f"input[name='{campo}'][value='{pendientes[0]}']").first.click()
            tildados.append(pendientes[0])
            continue
        if not _pagina_siguiente(s):
            break
    else:
        raise ErrorPip(f"la lista de '{campo}' no terminó de recorrerse en {max_pasos} pasos")
    return {"tildados": tildados,
            "sin_tildar": [v for v in valores if v in estado and not estado[v]],
            "no_encontrados": [v for v in valores if v not in estado]}


def _abrir_adjunto(s: B.Sesion, fila: dict, tipo: str) -> None:
    """Abre la página de subida del slot: lista de adjuntos -> Adjuntar del tipoArchivo dado."""
    enlace = fila.get("enlace") or ""
    if not enlace:
        raise ErrorPip("la sección de adjuntos no ofrece enlace: informar la ruta manualmente")
    _navegar(s, enlace)
    idx = s.page.evaluate("""(tipo) => {
        const forms = Array.from(document.forms);
        for (let i = 0; i < forms.length; i++) {
            const h = forms[i].querySelector("input[type=hidden][name=tipoArchivo]");
            if (h && h.value === tipo) return i;
        }
        return -1;
    }""", tipo)
    if idx < 0:
        raise ErrorPip(f"la página de adjuntos no ofrece un slot con tipoArchivo={tipo!r}")
    with s.page.expect_navigation(wait_until="load", timeout=60_000):
        s.page.locator("form").nth(idx).locator("input[type=submit]").click()
    s.page.wait_for_load_state("load", timeout=60_000)


def _adjuntar_pip(f: B.Formulario, item: dict) -> None:
    archivo = item.get("archivo")
    if not archivo:
        return
    campo = archivo.get("campo")
    loc = f.page.locator(f'input[name="{campo}"]') if campo and f.existe(campo) \
        else f.page.locator('input[type="file"]')
    if not loc.count():
        raise ErrorPip("la página de subida no tiene campo de archivo")
    loc.first.set_input_files(archivo["ruta"])


def _leer_estados_con_reintento(s: B.Sesion, base: dict, codigo: str | None, seccion: str,
                                intentos: int | None = None) -> tuple[list[dict], dict | None]:
    """Relee la tabla de estados hasta que la sección dice "Ok" (guardar no significa guardado)."""
    intentos = INTENTOS_ESTADO if intentos is None else intentos
    fila = None
    for i in range(intentos):
        abrir_tramite(s, base, codigo)
        estados = leer_estados(s)
        fila = _fila_estado(estados, seccion)
        if fila and fila["estado"] == "Ok":
            return estados, fila
        if i < intentos - 1:
            s.page.wait_for_timeout(10_000)
    return estados, fila


def _abrir_y_leer(s: B.Sesion, base: dict, codigo: str | None, seccion: str) -> tuple[list[dict], dict | None]:
    """Abre el trámite y lee la tabla de estados, reintentando si vino vacía (carga lenta).

    Corta la tanda solo si la sección sigue sin figurar tras los reintentos.
    """
    estados, fila = [], None
    for intento in range(3):
        abrir_tramite(s, base, codigo)
        estados = leer_estados(s)
        fila = _fila_estado(estados, seccion)
        if fila is not None:
            return estados, fila
        if intento < 2:
            s.page.wait_for_timeout(10_000)
    disponibles = "; ".join(f["seccion"] for f in estados)[:400]
    raise CortePip(json.dumps({"resultado": "corte", "seccion": seccion,
                                "detalle": f"la sección '{seccion}' no figura en la tabla de estados. "
                                           f"Secciones vistas: {disponibles}"}))


def huella(item: dict) -> str:
    """Huella del contenido pedido: si cambian los datos de una sección, deja de darse por hecha."""
    contenido = {k: v for k, v in item.items() if k != "avisos"}
    return hashlib.sha1(json.dumps(contenido, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def _hechos(ruta: Path) -> dict[str, str]:
    """clave -> huella de la última vez que quedó al día ("guardado" o "ya-estaba").

    Las entradas sin huella (de versiones anteriores) no cuentan: esas secciones se vuelven a
    comparar contra el sitio, que es barato y no guarda nada si ya coinciden.
    """
    hechos: dict[str, str] = {}
    if not ruta.exists():
        return hechos
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if e.get("clave") and e.get("resultado") in ("guardado", "ya-estaba") and e.get("huella"):
            hechos[e["clave"]] = e["huella"]
    return hechos


def _comparable(item: dict) -> bool:
    """Tipos cuyo contenido se puede releer del formulario para saber si ya está al día."""
    return bool(item.get("campos") or item.get("filas") or item.get("seleccion")) or item.get("miembros") is not None


def _diferencias(s: B.Sesion, f: B.Formulario, item: dict) -> tuple[list[str], list[str]]:
    """Compara lo pedido con lo cargado (solo lectura). Devuelve ([diferencias], [avisos])."""
    difiere: list[str] = []
    avisos: list[str] = []
    if item.get("miembros") is not None:
        al_dia, avisos = grupo_al_dia(_leer_grupo(f), item["miembros"])
        if not al_dia:
            difiere.append("grupo")
    if item.get("campos"):
        nombres = list(item["campos"])
        difiere += [f"campo {n}" for n in diferencias_campos(_leer_valores(f, nombres), item["campos"])]
    if item.get("filas"):
        columnas = list(item["filas"][0])
        if not filas_al_dia(_leer_filas(f, columnas), item["filas"]):
            difiere.append("filas")
    if item.get("seleccion"):
        r = recorrer_seleccion(s, item["seleccion"]["campo"], item["seleccion"]["valores"], tildar=False)
        if r["sin_tildar"] or r["no_encontrados"]:
            difiere.append(f"selección: {len(r['sin_tildar'])} sin tildar, {len(r['no_encontrados'])} no encontrados")
    return difiere, avisos


def procesar_item(s: B.Sesion, base: dict, codigo: str | None, item: dict, guardar: bool) -> dict:
    resultado = {"clave": item["clave"], "seccion": item["seccion"]}
    estados, fila = _abrir_y_leer(s, base, codigo, item["seccion"])
    en_ok = fila["estado"] == "Ok"
    if en_ok and not _comparable(item):
        resultado["resultado"] = "ya-estaba"
        return resultado
    if item.get("archivo"):
        _abrir_adjunto(s, fila, str(item["archivo"].get("tipo") or ""))
    else:
        _abrir_formulario(s, fila)
    f = B.Formulario(s)
    avisos: list[str] = []
    if en_ok:
        # "Ok" no significa "al día": se relee lo cargado y solo se guarda si difiere.
        difiere, avisos = _diferencias(s, f, item)
        if not difiere:
            resultado.update({"avisos": avisos, "resultado": "ya-estaba"})
            return resultado
        resultado["difiere"] = difiere
        if item.get("seleccion"):
            _abrir_formulario(s, fila)  # el recorrido de la comparación dejó otra página abierta
            f = B.Formulario(s)
    if item.get("miembros") is not None:
        avisos = _aplicar_grupo(f, item["miembros"])
    if item.get("campos"):
        fechas = B.aplicar_campos(f, item["campos"])
        f.fijar_fechas(fechas)
    if item.get("dependientes"):
        _resolver_dependientes(f, item)
    if item.get("grilla"):
        _llenar_grilla(f, item["grilla"])
    if item.get("filas"):
        _llenar_filas(f, item["filas"])
    if item.get("seleccion"):
        # Cada clic en estas casillas ya envía el formulario y guarda. Primero se recorre sin tocar
        # nada (y se corta si falta algún valor); los clics, solo con --guardar y con todo validado.
        campo, valores = item["seleccion"]["campo"], item["seleccion"]["valores"]
        sel = recorrer_seleccion(s, campo, valores, tildar=False)
        if sel["no_encontrados"]:
            raise ErrorPip(f"la lista no ofrece {len(sel['no_encontrados'])} de los valores pedidos: "
                           f"{', '.join(sel['no_encontrados'][:10])}")
        if guardar and sel["sin_tildar"]:
            _abrir_formulario(s, fila)
            sel = recorrer_seleccion(s, campo, valores, tildar=True)
        ya = len(valores) - len(sel["tildados"]) - len(sel["sin_tildar"])
        avisos.append(f"selección: {ya} ya tildados, {len(sel['tildados'])} tildados ahora, "
                      f"{len(sel['sin_tildar'])} por tildar")
    if item.get("archivo"):
        _adjuntar_pip(f, item)
    resultado["avisos"] = avisos
    resultado["captura_seco"] = s.captura(f"pip-seco-{item['clave']}")
    if not guardar:
        resultado["resultado"] = "en-seco"
        return resultado
    # Las pantallas traen notas fijas con el mismo verbo que los errores ("(2) Debe seleccionar a las
    # personas que desea habilitar..."): solo cuenta como rechazo un mensaje que no estaba antes.
    previos = {m.group(0) for m in B.RE_ERROR_FORM.finditer(B._texto_pagina(s))}
    cuerpo = B._apretar_guardar(s, "Guardar")
    error = next((m for m in B.RE_ERROR_FORM.finditer(cuerpo) if m.group(0) not in previos), None)
    if error:
        resultado.update({"resultado": "rechazado", "detalle": error.group(0)[:200],
                          "captura": s.captura(f"pip-rechazado-{item['clave']}")})
        return resultado
    estados, fila_ok = _leer_estados_con_reintento(s, base, codigo, item["seccion"])
    resultado["estados"] = _resumen_estados(estados)
    if not fila_ok or fila_ok["estado"] != "Ok":
        resultado.update({"resultado": "no-guardado", "captura": s.captura(f"pip-no-guardado-{item['clave']}")})
        return resultado
    if _comparable(item):
        # Releer lo guardado: el estado "Ok" no prueba que el contenido sea el pedido.
        _abrir_formulario(s, fila_ok)
        difiere, _ = _diferencias(s, B.Formulario(s), item)
        if difiere:
            resultado.update({"resultado": "no-guardado", "detalle": f"releído distinto: {'; '.join(difiere)[:300]}",
                              "captura": s.captura(f"pip-no-guardado-{item['clave']}")})
            return resultado
    resultado["resultado"] = "guardado"
    return resultado


def cmd_pip_cargar(args) -> int:
    _excepciones_de_modulo()
    config = B.cargar_config(args.config)
    trabajo = Path(args.dir)
    base = _linea_base(Path(args.referencias))
    _chequear_origen(base, config)
    estado_log = B.Estado(trabajo / "estado-pip.jsonl")
    datos = B.leer_json(args.datos, None)
    if not datos or datos.get("errores"):
        raise SystemExit(f"{args.datos} tiene errores o no existe: correr 'pip-preparar' primero")
    hechos = _hechos(trabajo / "estado-pip.jsonl")
    cola = [i for i in datos["items"] if not (args.claves and i["clave"] not in args.claves)
            and hechos.get(i["clave"]) != huella(i)][:B.LIMITE_MAXIMO]
    recibo = {"comando": "pip-cargar", "modo": "guardar" if args.guardar else "en-seco",
              "inicio_utc": B.ahora_utc(), "tramite": datos.get("tramite"), "solicitados": len(cola),
              "resultados": [], "motivo_fin": "completo"}
    ruta_recibo = trabajo / f"recibo-pip-cargar-{datetime.now():%Y%m%d-%H%M%S}.json"
    if not cola:
        recibo["motivo_fin"] = "nada pendiente con esos filtros"
        B.escribir_json(ruta_recibo, recibo)
        print(json.dumps(recibo, ensure_ascii=False, indent=1))
        return 0
    log(f"{len(cola)} secciones. Modo: {'GUARDAR' if args.guardar else 'EN SECO (no guarda)'}")
    with B.Sesion(config, trabajo, headless=args.headless) as s:
        _ir_a_presentacion(s)
        verificacion_previa_pip(s, args, config, trabajo, datos.get("tramite"))
        base = _linea_base(Path(args.referencias))  # la verificación pudo adoptarla
        for i, item in enumerate(cola, 1):
            if i > 1:
                s.page.wait_for_timeout(PAUSA_GUARDADO_MS)
            log(f"({i}/{len(cola)}) [{item['seccion'][:60]}]")
            if not s.viva():
                recibo["motivo_fin"] = "la sesión expiró"
                break
            try:
                r = procesar_item(s, base, datos.get("tramite"), item, args.guardar)
            except ErrorPip as e:
                r = {"clave": item["clave"], "seccion": item["seccion"], "resultado": "error", "detalle": str(e),
                     "captura": s.captura(f"pip-error-{item['clave']}")}
            except CortePip as e:
                try:
                    r = json.loads(str(e))
                except json.JSONDecodeError:
                    r = {"clave": item["clave"], "resultado": "corte", "detalle": str(e)}
                r["captura"] = s.captura(f"pip-corte-{item['clave']}")
                estado_log.registrar(r)
                recibo["resultados"].append(r)
                recibo["motivo_fin"] = f"corte de tanda: {r.get('resultado')}"
                log(f"    CORTE: {str(e)[:200]}")
                break
            r["huella"] = huella(item)
            estado_log.registrar(r)
            recibo["resultados"].append(r)
            log(f"    {r['resultado']}" + (f": {r.get('detalle', '')[:160]}" if r.get("detalle") else ""))
            B.escribir_json(ruta_recibo, recibo)
        abrir_tramite(s, base, datos.get("tramite"))
        recibo["estados"] = _resumen_estados(leer_estados(s))
        recibo["dialogos"] = s.dialogos
    recibo["fin_utc"] = B.ahora_utc()
    recibo["recibo"] = str(ruta_recibo)
    B.escribir_json(ruta_recibo, recibo)
    print(json.dumps(recibo, ensure_ascii=False, indent=1))
    pendientes = [k for k, v in recibo["estados"].items() if v != "Ok"]
    if recibo["motivo_fin"] != "completo":
        log(f"Fin: {recibo['motivo_fin']}.")
    elif pendientes:
        log(f"Pendientes ({len(pendientes)}): {', '.join(pendientes)}")
    else:
        log("TODO en 'Ok'. ENVIAR PRESENTACIÓN lo apreta la persona (o 'pip-enviar --confirmo-enviar').")
    return 1 if any(r["resultado"] in MALOS for r in recibo["resultados"]) else 0


# --------------------------------------------------------------------------- solo lectura y envío

def cmd_pip_estados(args) -> int:
    _excepciones_de_modulo()
    config = B.cargar_config(args.config)
    trabajo = Path(args.dir)
    base = _linea_base(Path(args.referencias))
    _chequear_origen(base, config)
    with B.Sesion(config, trabajo, headless=args.headless) as s:
        _ir_a_presentacion(s)
        verificacion_previa_pip(s, args, config, trabajo, args.tramite)
        base = _linea_base(Path(args.referencias))
        abrir_tramite(s, base, args.tramite)
        captura = s.captura("pip-estados")
        filas = leer_estados(s)
    print(json.dumps({"tramite": args.tramite, "estados": _resumen_estados(filas),
                      "con_enlace": [f["seccion"] for f in filas if f["enlace"]], "captura": captura},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_pip_enviar(args) -> int:
    """Único comando que puede apretar ENVIAR: aparte, explícito y solo con todo en "Ok"."""
    _excepciones_de_modulo()
    if not args.confirmo_enviar:
        raise SystemExit("ENVIAR PRESENTACIÓN es irreversible: correr de nuevo con --confirmo-enviar, o apretar el "
                         "botón a mano en el navegador (vía preferida).")
    config = B.cargar_config(args.config)
    trabajo = Path(args.dir)
    base = _linea_base(Path(args.referencias))
    _chequear_origen(base, config)
    with B.Sesion(config, trabajo, headless=args.headless) as s:
        _ir_a_presentacion(s)
        verificacion_previa_pip(s, args, config, trabajo, args.tramite)
        base = _linea_base(Path(args.referencias))
        abrir_tramite(s, base, args.tramite)
        captura_antes = s.captura("pip-enviar-antes")
        estados = leer_estados(s)
        pendientes = [f["seccion"] for f in estados if f["estado"] != "Ok"]
        if pendientes:
            print(json.dumps({"enviado": False, "motivo": f"hay secciones sin 'Ok': {pendientes}",
                              "estados": _resumen_estados(estados), "captura": captura_antes},
                             ensure_ascii=False, indent=1))
            return 2
        botones = s.page.evaluate(
            """() => Array.from(document.querySelectorAll('input[type=submit],button'))
                 .map(b => (b.value || b.innerText || '').trim()).filter(v => /enviar/i.test(v))""")
        if not botones:
            raise SystemExit("no encontré el botón ENVIAR en el trámite (¿cambió el sitio?): correr 'pip-verificar'")
        s.aceptar_dialogos = True  # SIGEVA pide confirmación antes de ENVIAR
        cuerpo = B._apretar_guardar(s, botones[0], autorizado=True)
        s.aceptar_dialogos = False
        abrir_tramite(s, base, args.tramite)
        estados_despues = leer_estados(s)
        recibido = bool(re.search(r"recibid|enviad|generad", _rotulo(cuerpo)))
        salida = {"enviado": True, "recibido": recibido, "cuerpo": cuerpo[:600],
                  "estados": _resumen_estados(estados_despues), "captura": s.captura("pip-enviar-despues")}
        print(json.dumps(salida, ensure_ascii=False, indent=1))
        return 0 if recibido else 1


def cmd_pip_mapear(args) -> int:
    _excepciones_de_modulo()
    config = B.cargar_config(args.config)
    with B.Sesion(config, Path(args.dir), headless=args.headless) as s:
        _ir_a_presentacion(s)
        mapa = _verificacion_pip_actual(s, args, config, Path(args.dir), args.tramite)
    contrato = M.verificar_contrato(mapa, _contrato_pip(mapa))
    salida = {"pantallas": len(mapa["pantallas"]), "omitidos": len(mapa["omitidos"]), "errores": mapa["errores"],
              "completo": mapa["completo"], "version_sigeva": mapa["version_sigeva"], "origen": mapa["origen"],
              "inicio_pip": mapa["inicio_pip"], "tramite_pantalla": mapa["tramite_pantalla"],
              "estados_tabla_id": mapa["estados_tabla_id"], "contrato": contrato}
    if args.aceptar:
        salida |= _aceptar_mapa_pip(mapa, Path(args.referencias))
    print(json.dumps(salida, ensure_ascii=False, indent=1))
    return 1 if not mapa["completo"] else (2 if contrato else 0)


def cmd_pip_verificar(args) -> int:
    _excepciones_de_modulo()
    config = B.cargar_config(args.config)
    trabajo, referencias = Path(args.dir), Path(args.referencias)
    base = _linea_base(referencias)
    _chequear_origen(base, config)
    actual = B.leer_json(args.mapa) if getattr(args, "mapa", None) else None
    if actual is None:
        with B.Sesion(config, trabajo, headless=args.headless) as s:
            _ir_a_presentacion(s)
            actual = _verificacion_pip_actual(s, args, config, trabajo, args.tramite)
    informe, codigo = _verificar_pip(actual, base, referencias, trabajo, args.auto, args.aceptar)
    print(json.dumps(informe, ensure_ascii=False, indent=1))
    return codigo
