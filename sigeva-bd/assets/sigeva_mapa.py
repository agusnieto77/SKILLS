"""Mapa estructural del Banco de Datos de SIGEVA y deteccion de cambios.

`mapear` recorre el rol Banco de Datos en solo lectura: menus, listas y formularios
de alta vacios. Nunca envia formularios ni sigue acciones sobre registros (editar,
borrar, importar...). Solo guarda estructura: pantallas, campos, tipos, etiquetas,
opciones, tablas y navegacion; nunca valores cargados por la persona.

`comparar_mapas` y `verificar_contrato` detectan campos nuevos o eliminados,
cambios de tipo, opciones, obligatoriedad, navegacion y, sobre todo, cualquier
ruptura de los selectores que usa `sigeva_bd.py cargar` (el CONTRATO).
"""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit

# Acciones que se pueden abrir sin riesgo: un formulario de alta vacio.
ACCIONES_SEGURAS = {"", "nuevo"}
PARAMETROS_ACCION = ("action", "accion", "btnsubmit", "buttonsubmit", "metodo", "method", "operacion")
# Nunca se visitan, aunque parezcan paginas: cierran sesion, importan o comparten datos.
RUTAS_PROHIBIDAS = re.compile(r"salir|logout|importar|sincroniz|archivodinamico|descarga|download|imprimir.*\.pdf", re.I)
PARAMETROS_DESCARTABLES = re.compile(r"^(ticket|jsessionid|paginar|d-\d+-[pso]|_)$", re.I)
# Pares parametro=valor de paginacion: algunos enlaces los acumulan en cada visita (bcoRoles.do).
VALORES_PAGINACION = {"paginar"}
PARAMETROS_REGISTRO = re.compile(r"^(id|produccionid|actividadid|personaid|tramiteid|archivoid)$", re.I)
# Pasos de navegacion con submit permitidos: solo los que abren un formulario vacio.
PASOS_SEGUROS = {"bcoPrecargarArticulo.do?action=Nuevo": "Omitir"}
SEVERIDADES = ("critico", "alto", "medio", "bajo")

JS_ESTRUCTURA = r"""() => {
    const limpio = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const etiqueta = (el) => {
        if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if (l) return limpio(l.innerText); }
        // Solo celdas que parecen rotulos ("Titulo:*"): una celda con datos de la persona no es etiqueta.
        let td = el.closest('td');
        for (let i = 0; td && i < 3; i++) {
            td = td.previousElementSibling;
            if (!td) break;
            const t = limpio(td.innerText);
            if (/[:*]\s*\*?$/.test(t) && t.length <= 90) return t;
        }
        return '';
    };
    const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    const formularios = Array.from(document.forms).map(f => {
        const campos = {};
        const botones = [], nombresBoton = [];
        Array.from(f.elements).forEach(el => {
            const tag = el.tagName.toLowerCase();
            const tipo = (el.type || '').toLowerCase();
            if ((tag === 'input' && ['submit', 'button', 'image', 'reset'].includes(tipo)) || tag === 'button') {
                const valor = limpio(el.value || el.innerText);
                if (valor) botones.push(valor);
                if (el.name && !nombresBoton.includes(el.name)) nombresBoton.push(el.name);
                return;
            }
            if (!el.name) return;
            const c = campos[el.name] || (campos[el.name] = {name: el.name, tag, tipo, etiqueta: '', obligatorio: false,
                visible: false, datepicker: false, cantidad: 0, valores_opcion: [], opciones: null});
            c.cantidad += 1;
            if (tipo !== 'hidden' && c.tipo === 'hidden') { c.tag = tag; c.tipo = tipo; }
            const et = etiqueta(el);
            if (et && !c.etiqueta) c.etiqueta = et.replace(/\s*\*\s*$/, '').replace(/:\s*$/, '');
            c.obligatorio = c.obligatorio || /\*\s*$/.test(et) || el.required;
            c.visible = c.visible || (tipo !== 'hidden' && visible(el));
            c.datepicker = c.datepicker || el.classList.contains('hasDatepicker');
            if ((tipo === 'radio' || tipo === 'checkbox') && el.value && !c.valores_opcion.includes(el.value)) c.valores_opcion.push(el.value);
            if (tag === 'select' && !c.opciones) c.opciones = Array.from(el.options).map(o => [o.value, limpio(o.text)]);
        });
        return {name: f.getAttribute('name') || '', action: f.getAttribute('action') || '', metodo: (f.method || 'get').toLowerCase(),
                enctype: (f.enctype || '').toLowerCase(), campos: Object.values(campos), botones: Array.from(new Set(botones)),
                botones_name: nombresBoton};
    });
    const tablas = Array.from(document.querySelectorAll('table')).filter(t => t.tHead).map(t => ({
        id: t.id || '', orden: ((t.tHead.innerHTML.match(/d-(\d+)-s=/) || [])[1]) || '',
        cabecera: Array.from(t.tHead.querySelectorAll('th')).map(h => limpio(h.innerText))}));
    const enlaces = [];
    document.querySelectorAll('a[href], [onclick]').forEach(el => {
        const texto = limpio(el.innerText || el.value || el.title || '').slice(0, 80);
        const href = el.getAttribute('href') || '';
        const oc = el.getAttribute('onclick') || '';
        const m = /location(?:\.href)?\s*=\s*['"]([^'"]+)['"]/.exec(oc);
        if (href && !href.startsWith('javascript:') && href !== '#') enlaces.push({texto, href});
        else if (m) enlaces.push({texto, href: m[1]});
    });
    const titulo = limpio((document.querySelector('.titulo, .tituloPagina, h1, h2, h3, legend') || {}).innerText || document.title).slice(0, 100);
    const version = limpio((document.querySelector('.version') || {}).innerText || '');
    return {titulo, version, formularios, tablas, enlaces, iframes: document.querySelectorAll('iframe').length};
}"""


def hash_corto(datos) -> str:
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def clasificar_url(href: str, url_actual: str, base: str) -> dict:
    """Normaliza un enlace y decide si se puede visitar sin riesgo.

    Devuelve {ruta, accion, visitar, motivo}. `ruta` es relativa a /eva/ y sin
    parametros de sesion, paginacion ni ids de registros.
    """
    absoluta = urljoin(url_actual, href.strip())
    partes, base_partes = urlsplit(absoluta), urlsplit(base)
    if partes.scheme not in ("http", "https") or partes.netloc != base_partes.netloc:
        return {"ruta": absoluta, "accion": "", "visitar": False, "motivo": "externo"}
    if not partes.path.startswith("/eva/"):
        return {"ruta": partes.path.lstrip("/"), "accion": "", "visitar": False, "motivo": "fuera del Banco de Datos"}
    pagina = partes.path[len("/eva/"):]
    params, accion = set(), ""
    for k, v in parse_qsl(partes.query, keep_blank_values=True):
        if PARAMETROS_DESCARTABLES.match(k) or v.strip().lower() in VALORES_PAGINACION:
            continue
        if k.lower() in PARAMETROS_ACCION:
            accion = v.strip().lower()
        params.add((k, "N" if _es_id_registro(k, v) else v))
    # Canonica: parametros unicos y ordenados, para que el orden no cree pantallas "nuevas".
    params = sorted(params)
    ruta = pagina + ("?" + urlencode(params, safe="=/") if params else "")
    if RUTAS_PROHIBIDAS.search(pagina):
        return {"ruta": ruta, "accion": accion, "visitar": False, "motivo": "ruta prohibida (sesion, importacion o descarga)"}
    if accion not in ACCIONES_SEGURAS:
        return {"ruta": ruta, "accion": accion, "visitar": False, "motivo": f"accion sobre registros ({accion})"}
    if any(v == "N" for _, v in params):
        return {"ruta": ruta, "accion": accion, "visitar": False, "motivo": "pagina de un registro"}
    return {"ruta": ruta, "accion": accion, "visitar": True, "motivo": ""}


def _es_id_registro(clave: str, valor: str) -> bool:
    """Ids de registros de la persona (no estructura): se generalizan a N.

    Los ids estructurales (tipoFinanciamientoId=5, sincronizarformId=30) son chicos;
    los de registros (formacionId=1167646, cargoIdId=1295205) no.
    """
    if not valor.isdigit():
        return False
    return bool(PARAMETROS_REGISTRO.match(clave)) or (clave.lower().endswith("id") and len(valor) >= 4)


def canonica(ruta: str, base: str = "https://sigeva.invalid/") -> str:
    """Forma canonica de una ruta relativa a /eva/ (conserva un sufijo '#paso')."""
    ruta, _, paso = ruta.partition("#")
    sin_eva = ruta.split("eva/", 1)[-1]
    normal = clasificar_url(sin_eva, urljoin(base, "eva/"), base)["ruta"]
    return normal + (f"#{paso}" if paso else "")


def _tipo_pantalla(estructura: dict) -> str:
    editables = [c for f in estructura["formularios"] for c in f["campos"]
                 if c["tipo"] not in ("hidden",) and c["visible"]]
    if any(t["cabecera"] and t["cabecera"][0].strip().upper() == "NUEVO" for t in estructura["tablas"]):
        return "lista"
    return "formulario" if len(editables) >= 2 else "menu"


def mapear(sesion, inicio: str | list[str], max_pantallas: int = 300, pausa_ms: int = 1_000, log=print,
           seguir: bool = True) -> dict:
    """Recorrido en anchura desde `inicio` (rutas relativas a /eva/). Solo lectura.

    Con `seguir=False` visita solo esas pantallas (y sus pasos seguros): es el chequeo
    rapido del contrato que hace `cargar` antes de guardar.
    """
    page = sesion.page
    inicios = [inicio] if isinstance(inicio, str) else list(inicio)
    pendientes, vistas = [canonica(r.partition("#")[0]) for r in inicios], set()
    pasos = {canonica(k): v for k, v in PASOS_SEGUROS.items()}
    pantallas, omitidos, errores = {}, {}, {}
    version = ""
    while pendientes and len(pantallas) < max_pantallas:
        ruta = pendientes.pop(0)
        if ruta in vistas:
            continue
        vistas.add(ruta)
        url = sesion.url(ruta if ruta.startswith("eva/") else "eva/" + ruta)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_load_state("load", timeout=60_000)
            page.wait_for_timeout(pausa_ms)
            if not sesion.viva():
                errores[ruta] = f"la sesion se perdio (quede en {page.url[:80]})"
                break
            estructura = page.evaluate(JS_ESTRUCTURA)
        except Exception as e:  # una pantalla rota no corta el mapa: queda registrada
            errores[ruta] = str(e).splitlines()[0][:200]
            continue
        version = version or estructura["version"]
        destino = pendientes if seguir else []
        pantallas[ruta] = _resumir_pantalla(ruta, estructura, page.url, sesion.base, destino, vistas, omitidos)
        if ruta in pasos:
            boton = pasos[ruta]
            try:
                page.click(f'input[type="submit"][value="{boton}"]')
                page.wait_for_load_state("load", timeout=60_000)
                page.wait_for_timeout(pausa_ms)
                estructura = page.evaluate(JS_ESTRUCTURA)
                ruta_paso = f"{ruta}#{boton.lower()}"
                pantallas[ruta_paso] = _resumir_pantalla(ruta_paso, estructura, page.url, sesion.base, destino, vistas, omitidos)
            except Exception as e:
                errores[f"{ruta}#{boton.lower()}"] = str(e).splitlines()[0][:200]
        if len(pantallas) % 10 == 0:
            log(f"  {len(pantallas)} pantallas, {len(pendientes)} pendientes")
    return {"version_sigeva": version, "pantallas": pantallas, "omitidos": omitidos, "errores": errores,
            "completo": not pendientes and not errores, "pendientes_sin_visitar": pendientes[:50]}


def _resumir_pantalla(ruta, estructura, url_real, base, pendientes, vistas, omitidos) -> dict:
    navegacion, acciones = set(), {}
    for enlace in estructura["enlaces"]:
        c = clasificar_url(enlace["href"], url_real, base)
        if c["visitar"]:
            navegacion.add(c["ruta"])
            if c["ruta"] not in vistas and c["ruta"] not in pendientes:
                pendientes.append(c["ruta"])
        elif c["motivo"] not in ("externo",):
            acciones.setdefault(c["ruta"], c["motivo"])
            omitidos.setdefault(c["ruta"], c["motivo"])
    formularios = []
    for f in estructura["formularios"]:
        accion_form = clasificar_url(f["action"] or url_real, url_real, base)["ruta"] if f["action"] else ""
        formularios.append({**f, "action": accion_form})
    return {"ruta": ruta, "titulo": estructura["titulo"], "tipo": _tipo_pantalla(estructura),
            "formularios": formularios, "tablas": estructura["tablas"], "navegacion": sorted(navegacion),
            "acciones": dict(sorted(acciones.items())), "iframes": estructura["iframes"]}


# Pantallas que muestran datos de la propia persona: sus combos dependientes (provincia,
# partido...) se arman con esos datos, asi que ni el conteo ni el hash de opciones se publican.
PANTALLAS_PERSONALES = re.compile(r"^(bcoDatoPersonal|bcoExperticia|bcoDatoAcademico|bcoCArchivosAdjuntos|bcoRoles|"
                                  r"bcoABMRoles|bcoCompartirFormulario|bcoIncorporarParticipante)", re.I)


def sanear(mapa: dict) -> dict:
    """Version publicable del mapa: opciones como conteo + hash, sin datos de la persona."""
    salida = json.loads(json.dumps(mapa))
    for ruta, pantalla in salida.get("pantallas", {}).items():
        personal = bool(PANTALLAS_PERSONALES.match(ruta))
        for f in pantalla["formularios"]:
            for c in f["campos"]:
                opciones = c.pop("opciones", None)
                if opciones is not None and not personal:
                    c["opciones_n"] = len(opciones)
                    c["opciones_hash"] = hash_corto(opciones)
    salida.pop("pendientes_sin_visitar", None)
    return salida


def _campos(pantalla: dict) -> dict:
    return {(f["name"] or f["action"] or str(i), c["name"]): c
            for i, f in enumerate(pantalla.get("formularios", [])) for c in f["campos"]}


def _opciones_firma(campo: dict) -> tuple:
    if campo.get("opciones") is not None:
        return len(campo["opciones"]), hash_corto(campo["opciones"])
    return campo.get("opciones_n"), campo.get("opciones_hash")


def comparar_mapas(base: dict, actual: dict) -> list[dict]:
    """Diferencias estructurales entre dos mapas (saneados o completos)."""
    cambios = []

    def agregar(severidad, pantalla, tipo, detalle):
        cambios.append({"severidad": severidad, "pantalla": pantalla, "tipo": tipo, "detalle": detalle})

    if base.get("version_sigeva") != actual.get("version_sigeva"):
        agregar("medio", "-", "version", f"{base.get('version_sigeva')} -> {actual.get('version_sigeva')}")
    pb, pa = base.get("pantallas", {}), actual.get("pantallas", {})
    for ruta in sorted(set(pb) - set(pa)):
        agregar("alto", ruta, "pantalla-eliminada", pb[ruta].get("titulo", ""))
    for ruta in sorted(set(pa) - set(pb)):
        agregar("medio", ruta, "pantalla-nueva", pa[ruta].get("titulo", ""))
    for ruta in sorted(set(pb) & set(pa)):
        b, a = pb[ruta], pa[ruta]
        cb, ca = _campos(b), _campos(a)
        for clave in sorted(set(cb) - set(ca)):
            agregar("alto", ruta, "campo-eliminado", f"{clave[1]} ({cb[clave]['tipo']})")
        for clave in sorted(set(ca) - set(cb)):
            c = ca[clave]
            agregar("alto" if c.get("obligatorio") else "medio", ruta, "campo-nuevo",
                    f"{c['name']} ({c['tipo']}){' obligatorio' if c.get('obligatorio') else ''} '{c.get('etiqueta', '')}'")
        for clave in sorted(set(cb) & set(ca)):
            x, y = cb[clave], ca[clave]
            if (x["tag"], x["tipo"]) != (y["tag"], y["tipo"]):
                agregar("alto", ruta, "campo-tipo", f"{clave[1]}: {x['tag']}/{x['tipo']} -> {y['tag']}/{y['tipo']}")
            if bool(x.get("obligatorio")) != bool(y.get("obligatorio")):
                agregar("alto" if y.get("obligatorio") else "medio", ruta, "campo-obligatoriedad",
                        f"{clave[1]}: {'ahora obligatorio' if y.get('obligatorio') else 'ya no obligatorio'}")
            if x.get("datepicker") != y.get("datepicker"):
                agregar("medio", ruta, "campo-datepicker", f"{clave[1]}: datepicker {x.get('datepicker')} -> {y.get('datepicker')}")
            if sorted(x.get("valores_opcion") or []) != sorted(y.get("valores_opcion") or []):
                agregar("alto", ruta, "campo-valores", f"{clave[1]}: {x.get('valores_opcion')} -> {y.get('valores_opcion')}")
            fx, fy = _opciones_firma(x), _opciones_firma(y)
            if fx != fy:
                agregar("bajo", ruta, "campo-opciones", f"{clave[1]}: {fx[0]} -> {fy[0]} opciones")
            if (x.get("etiqueta") or "") != (y.get("etiqueta") or ""):
                agregar("bajo", ruta, "campo-etiqueta", f"{clave[1]}: '{x.get('etiqueta')}' -> '{y.get('etiqueta')}'")
        fb = {f["name"] or f["action"]: f for f in b.get("formularios", [])}
        fa = {f["name"] or f["action"]: f for f in a.get("formularios", [])}
        for nombre in sorted(set(fb) & set(fa)):
            if fb[nombre]["action"] != fa[nombre]["action"]:
                agregar("alto", ruta, "formulario-action", f"{nombre}: {fb[nombre]['action']} -> {fa[nombre]['action']}")
            for boton in sorted(set(fb[nombre]["botones"]) - set(fa[nombre]["botones"])):
                agregar("alto", ruta, "boton-eliminado", f"{nombre}: '{boton}'")
            for boton in sorted(set(fa[nombre]["botones"]) - set(fb[nombre]["botones"])):
                agregar("medio", ruta, "boton-nuevo", f"{nombre}: '{boton}'")
        for nombre in sorted(set(fb) - set(fa)):
            agregar("alto", ruta, "formulario-eliminado", nombre)
        for nombre in sorted(set(fa) - set(fb)):
            agregar("medio", ruta, "formulario-nuevo", nombre)
        tb = {t["id"] or t["orden"]: t for t in b.get("tablas", [])}
        ta = {t["id"] or t["orden"]: t for t in a.get("tablas", [])}
        for tid in sorted(set(tb) - set(ta)):
            agregar("alto", ruta, "tabla-eliminada", tid)
        for tid in sorted(set(ta) - set(tb)):
            agregar("medio", ruta, "tabla-nueva", tid)
        for tid in sorted(set(tb) & set(ta)):
            if tb[tid]["cabecera"] != ta[tid]["cabecera"] or tb[tid]["orden"] != ta[tid]["orden"]:
                agregar("alto", ruta, "tabla-cambiada", f"{tid}: {tb[tid]['orden']} {tb[tid]['cabecera']} -> {ta[tid]['orden']} {ta[tid]['cabecera']}")
        for destino in sorted(set(b.get("navegacion", [])) - set(a.get("navegacion", []))):
            agregar("medio", ruta, "navegacion-eliminada", destino)
        for destino in sorted(set(a.get("navegacion", [])) - set(b.get("navegacion", []))):
            agregar("bajo", ruta, "navegacion-nueva", destino)
        for destino in sorted(set(b.get("acciones", {})) - set(a.get("acciones", {}))):
            agregar("medio", ruta, "accion-eliminada", destino)
        for destino in sorted(set(a.get("acciones", {})) - set(b.get("acciones", {}))):
            agregar("bajo", ruta, "accion-nueva", destino)
    return cambios


def _pantalla_de(mapa: dict, ruta: str) -> dict | None:
    pantallas = mapa.get("pantallas", {})
    if ruta in pantallas:
        return pantallas[ruta]
    return pantallas.get(canonica(ruta))


def verificar_contrato(mapa: dict, contrato: list[dict]) -> list[dict]:
    """Lo que `cargar` necesita encontrar. Cada falta es critica: la carga fallaria o, peor, cargaria mal."""
    cambios = []
    for item in contrato:
        pantalla = _pantalla_de(mapa, item["pantalla"])
        if pantalla is None:
            cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-pantalla",
                            "detalle": f"{item['uso']}: la pantalla no aparecio en el mapa"})
            continue
        campos = {c["name"]: c for f in pantalla["formularios"] for c in f["campos"]}
        botones = {b for f in pantalla["formularios"] for b in f["botones"] + f.get("botones_name", [])}
        for nombre, req in item.get("campos", {}).items():
            c = campos.get(nombre)
            if c is None:
                cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-campo",
                                "detalle": f"{item['uso']}: falta el campo '{nombre}'"})
                continue
            if req.get("tag") and c["tag"] != req["tag"]:
                cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-tipo",
                                "detalle": f"{item['uso']}: '{nombre}' es {c['tag']}, se esperaba {req['tag']}"})
            for valor in req.get("valores", []):
                if valor not in (c.get("valores_opcion") or []):
                    cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-valor",
                                    "detalle": f"{item['uso']}: '{nombre}' ya no ofrece el valor {valor}"})
            if req.get("datepicker") and not c.get("datepicker"):
                cambios.append({"severidad": "alto", "pantalla": item["pantalla"], "tipo": "contrato-datepicker",
                                "detalle": f"{item['uso']}: '{nombre}' dejo de ser datepicker (revisar fijar_fechas)"})
        for boton in item.get("botones", []):
            if boton not in botones:
                cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-boton",
                                "detalle": f"{item['uso']}: falta el boton '{boton}'"})
        tablas = {t["id"] or t["orden"]: t for t in pantalla["tablas"]}
        for tid, req in item.get("tablas", {}).items():
            t = tablas.get(tid)
            if t is None:
                cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-tabla",
                                "detalle": f"{item['uso']}: falta la tabla '{tid}'"})
                continue
            if req.get("orden") and t["orden"] != req["orden"]:
                cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-tabla",
                                "detalle": f"{item['uso']}: la tabla '{tid}' pagina con d-{t['orden']}, se esperaba d-{req['orden']}"})
            cab = [c.upper() for c in t["cabecera"]]
            for col in req.get("columnas", []):
                if col.upper() not in cab:
                    cambios.append({"severidad": "critico", "pantalla": item["pantalla"], "tipo": "contrato-tabla",
                                    "detalle": f"{item['uso']}: la tabla '{tid}' no tiene la columna {col}"})
    return cambios


def resumen_cambios(cambios: list[dict]) -> dict:
    return {s: sum(1 for c in cambios if c["severidad"] == s) for s in SEVERIDADES}


def _md(texto: str) -> str:
    return (texto or "").replace("|", "\\|")


def generar_documento(mapa: dict, contrato: list[dict]) -> str:
    """Markdown de referencia generado del mapa saneado. No editar a mano: se regenera."""
    pantallas = mapa.get("pantallas", {})
    lineas = [
        "# Mapa del Banco de Datos de SIGEVA",
        "",
        "> Archivo generado por `sigeva_bd.py mapear --aceptar` / `verificar --aceptar`. No editar a mano.",
        "",
        f"- Versión de SIGEVA: **{mapa.get('version_sigeva') or 'desconocida'}**",
        f"- Capturado: {mapa.get('capturado_en_utc', '?')}",
        f"- Pantallas: {len(pantallas)} · omitidas por seguridad: {len(mapa.get('omitidos', {}))} · errores: {len(mapa.get('errores', {}))}",
        f"- Recorrido completo: {'sí' if mapa.get('completo') else 'no'}",
        "",
        "Solo estructura: nombres de campo, tipos, etiquetas y cantidad de opciones. Los valores de la persona no se registran.",
        "",
        "## Contrato del cargador",
        "",
        "Lo que `cargar` necesita encontrar. `verificar` marca como **crítico** cualquier faltante.",
        "",
        "| Uso | Pantalla | Campos | Botones | Tablas |",
        "|---|---|---|---|---|",
    ]
    for item in contrato:
        lineas.append(f"| {_md(item['uso'])} | `{item['pantalla']}` | {len(item.get('campos', {}))} | "
                      f"{_md(', '.join(item.get('botones', [])))} | {_md(', '.join(item.get('tablas', {})))} |")
    grupos: dict[str, list[str]] = {}
    for ruta in pantallas:
        modulo = re.search(r"idModulo=(\d+)", ruta)
        grupos.setdefault(f"Módulo {modulo.group(1)}" if modulo else "Formularios y pantallas sin módulo", []).append(ruta)
    lineas += ["", "## Índice de pantallas", "", "| Pantalla | Tipo | Título | Formularios | Campos | Tablas |", "|---|---|---|---|---|---|"]
    for ruta in sorted(pantallas):
        p = pantallas[ruta]
        n_campos = sum(len(f["campos"]) for f in p["formularios"])
        lineas.append(f"| [`{_md(ruta)}`](#{_ancla(ruta)}) | {p['tipo']} | {_md(p['titulo'])} | {len(p['formularios'])} | {n_campos} | {len(p['tablas'])} |")
    for grupo in sorted(grupos):
        lineas += ["", f"## {grupo}"]
        for ruta in sorted(grupos[grupo]):
            p = pantallas[ruta]
            lineas += ["", f"### `{ruta}`", "", f"{p['tipo'].capitalize()} — {_md(p['titulo'])}"]
            for t in p["tablas"]:
                lineas.append(f"- Tabla `{t['id'] or '?'}` (displaytag `d-{t['orden']}`): {_md(' · '.join(t['cabecera']))}")
            for f in p["formularios"]:
                visibles = [c for c in f["campos"] if c["tipo"] != "hidden"]
                ocultos = [c["name"] for c in f["campos"] if c["tipo"] == "hidden"]
                lineas += ["", f"Formulario `{f['name'] or '(sin nombre)'}` → `{_md(f['action'])}` ({f['metodo'].upper()})"
                           + (f"; botones: {_md(', '.join(f['botones']))}" if f["botones"] else "")]
                if visibles:
                    lineas += ["", "| Campo | Tipo | Etiqueta | Oblig. | Notas |", "|---|---|---|---|---|"]
                    for c in visibles:
                        notas = []
                        if c.get("datepicker"):
                            notas.append("datepicker")
                        if c.get("valores_opcion"):
                            notas.append("valores " + ", ".join(c["valores_opcion"]))
                        if c.get("opciones_n") is not None:
                            notas.append(f"{c['opciones_n']} opciones")
                        if c.get("cantidad", 1) > 1:
                            notas.append(f"x{c['cantidad']}")
                        if not c.get("visible"):
                            notas.append("oculto al cargar")
                        lineas.append(f"| `{c['name']}` | {c['tag']}/{c['tipo']} | {_md(c.get('etiqueta', ''))} | "
                                      f"{'sí' if c.get('obligatorio') else ''} | {_md('; '.join(notas))} |")
                if ocultos:
                    lineas.append(f"\nOcultos: {', '.join(f'`{n}`' for n in ocultos[:60])}{' …' if len(ocultos) > 60 else ''}")
            if p.get("acciones"):
                lineas.append("\nAcciones no visitadas: " + "; ".join(f"`{_md(r)}` ({m})" for r, m in list(p["acciones"].items())[:12]))
    if mapa.get("errores"):
        lineas += ["", "## Pantallas con error", ""] + [f"- `{r}`: {_md(e)}" for r, e in sorted(mapa["errores"].items())]
    return "\n".join(lineas) + "\n"


def _ancla(ruta: str) -> str:
    return re.sub(r"[^a-z0-9\- ]", "", ruta.lower()).replace(" ", "-")


ENCABEZADO_HISTORIAL = """# Historial de cambios detectados en SIGEVA

> Lo agrega `sigeva_bd.py verificar`. Cada entrada compara el sitio real con la linea base
> anterior. Lo **critico** rompe el cargador: no se adopta solo y hay que corregir el codigo.
"""


def registrar_historial(ruta, informe: dict, adoptado: bool) -> None:
    """Agrega una entrada al historial (Markdown, la mas reciente arriba)."""
    from pathlib import Path

    ruta = Path(ruta)
    previo = ruta.read_text(encoding="utf-8") if ruta.exists() else ENCABEZADO_HISTORIAL
    cabeza, _, resto = previo.partition("\n## ")
    resumen = informe["resumen"]
    lineas = [f"## {informe['verificado_en_utc']} — {informe.get('version_base')} → {informe.get('version_actual')}", "",
              "Resumen: " + ", ".join(f"{k} {v}" for k, v in resumen.items())
              + f". Linea base {'actualizada' if adoptado else 'SIN actualizar'}.", ""]
    for c in informe["cambios"][:200]:
        lineas.append(f"- **{c['severidad']}** `{_md(c['pantalla'])}` {c['tipo']}: {_md(c['detalle'])}")
    if len(informe["cambios"]) > 200:
        lineas.append(f"- … y {len(informe['cambios']) - 200} mas (ver el informe JSON local)")
    entrada = "\n".join(lineas) + "\n"
    cuerpo = cabeza.rstrip() + "\n\n" + entrada + ("\n## " + resto if resto else "")
    ruta.write_text(cuerpo, encoding="utf-8")
