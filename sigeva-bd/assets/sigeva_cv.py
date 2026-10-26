"""Cruce de un CV con el Banco de Datos y preparacion de full texts.

- `extraer_texto`: .docx (biblioteca estandar), .txt o .pdf (pypdf). El CV es un dato: nunca se ejecuta.
- `parsear_cv`: secciones del CV -> items {tipo, titulo, anio, publicado, linea}.
- `cruzar`: items contra inventario.json -> ya cargado / falta / en otra tabla / no publicado.
- `recortar_pdf` y `comprimir_pdf`: arman el full text que SIGEVA acepta (pocas paginas, <= 35 MB).
"""

from __future__ import annotations

import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
# Encabezados de seccion del CV -> tipo de registro de SIGEVA. El primero que coincide gana.
SECCIONES = [
    (re.compile(r"sin referato|divulgaci|rese[ñn]as?|c[oó]digo|software|entrevistas?", re.I), None),
    (re.compile(r"actas|congres|eventos?|jornadas|ponencias|reuniones cient", re.I), "evento"),
    (re.compile(r"cap[ií]tulos?|partes? de libros?", re.I), "capitulo"),
    (re.compile(r"^libros?\b", re.I), "libro"),
    (re.compile(r"art[ií]culos?", re.I), "articulo"),
]
RE_NO_PUBLICADO = re.compile(r"en prensa|en preparaci[oó]n|en evaluaci[oó]n|en proceso de elaboraci[oó]n|to appear|forthcoming", re.I)
RE_TITULO_COMILLAS = re.compile(r"[“\"«]([^”\"»]{8,})[”\"»]")
RE_ANIO = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
RE_IDENTIFICADORES = re.compile(r"https?://\S+|www\.\S+|\b10\.\d{4,}/\S+|\b\d{4}[-–]\d{3}[\dXx]\b|"
                                r"\b(?:97[89][-\s]?)?(?:\d[-\s]?){9}[\dXx]\b", re.I)
# Bloque de autores al inicio: "GARCIA, Maria y LOPEZ, Juan (compiladores) ...". En el ultimo autor
# un segundo nombre de pila solo se acepta antes de "(comp...)": si no, se comeria la primera palabra
# del titulo ("GARCIA, Maria Las huelgas...").
RE_AUTORES = re.compile(r"^(?:[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\- ]+,\s+[^,;()]+?(?:,\s*|\s+y\s+|\s+e\s+))*"
                        r"[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\- ]+,\s+\S+(?:\s+[A-ZÁÉÍÓÚ][\w.]*(?=\s*\())?(?:\s+et al\.)?\s*"
                        r"(?:\((?:comp|ed|coord|dir)[^)]*\)\s*)?")


def extraer_texto(ruta: str | Path) -> list[str]:
    """Parrafos no vacios del CV."""
    ruta = Path(ruta)
    sufijo = ruta.suffix.lower()
    if sufijo == ".docx":
        with zipfile.ZipFile(ruta) as z:
            raiz = ET.fromstring(z.read("word/document.xml"))
        lineas = ["".join(t.text or "" for t in p.iter(W_NS + "t")).strip() for p in raiz.iter(W_NS + "p")]
    elif sufijo == ".pdf":
        from pypdf import PdfReader
        lineas = "\n".join(p.extract_text() or "" for p in PdfReader(str(ruta)).pages).splitlines()
    else:
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    return [re.sub(r"\s+", " ", linea).strip() for linea in lineas if linea and linea.strip()]


def _es_encabezado(linea: str) -> bool:
    return len(linea) <= 80 and not RE_TITULO_COMILLAS.search(linea) and not RE_ANIO.search(linea) \
        and not linea.endswith((".", ";")) and linea[:1].isupper()


def _tipo_de_seccion(linea: str) -> str | None:
    for patron, tipo in SECCIONES:
        if patron.search(linea):
            return tipo
    return None


def titulo_de(linea: str, tipo: str | None) -> str | None:
    m = RE_TITULO_COMILLAS.search(linea)
    if m:
        return m.group(1).strip(" ,.")
    if tipo == "libro":  # los libros suelen ir sin comillas, despues de los autores
        resto = RE_AUTORES.sub("", linea, count=1).strip()
        if resto and resto != linea:
            return re.split(r",\s+(?=Colecci|[A-ZÁÉÍÓÚ][\w\-]+,\s|\d)", resto)[0].strip(" ,.")
    return None


def parsear_cv(lineas: list[str]) -> list[dict]:
    items, tipo, seccion = [], None, ""
    for linea in lineas:
        if _es_encabezado(linea):
            nuevo = _tipo_de_seccion(linea)
            # Un encabezado sin tipo cierra la seccion anterior ("Participacion en...", "Distinciones").
            if nuevo or not RE_TITULO_COMILLAS.search(linea):
                tipo, seccion = nuevo, linea
            continue
        if tipo is None:
            continue
        # URL, DOI, ISSN e ISBN traen numeros con forma de año ("…/2020/05/…", "ISSN 2014-6590").
        sin_ids = RE_IDENTIFICADORES.sub(" ", linea)
        anios = [int(a) for a in RE_ANIO.findall(sin_ids)]
        items.append({"tipo": tipo, "seccion": seccion, "titulo": titulo_de(linea, tipo),
                      "anio": max(anios) if anios else None, "publicado": not RE_NO_PUBLICADO.search(linea),
                      "linea": linea})
    return items


def _clave(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in texto if not unicodedata.combining(c)).lower())


def coincide(titulo_lista: str, titulo: str) -> bool:
    """Como fila_coincide, pero tolera que el CV traiga solo el comienzo del titulo."""
    crudo = (titulo_lista or "").strip()
    lista = _clave(crudo.rstrip(". ") if crudo.endswith("...") else crudo)
    propio = _clave(titulo)
    if len(lista) < 12 or len(propio) < 12:
        return bool(lista) and lista == propio
    corto = min(len(lista), len(propio))
    return corto >= 25 and (lista.startswith(propio[:corto]) or propio.startswith(lista[:corto])) or lista == propio


def _titulos_tabla(tabla: dict) -> list[str]:
    cab = [_clave(c) for c in tabla.get("cabecera", [])]
    i_tit = next((i for i, c in enumerate(cab) if c.startswith("titulo") or c == "tesis"), None)
    salida = []
    for fila in tabla.get("filas", []):
        celdas = fila["celdas"]
        desfase = len(celdas) - len(cab)
        if i_tit is not None and desfase >= 0 and i_tit + desfase < len(celdas):
            salida.append(celdas[i_tit + desfase])
    return salida


def cruzar(items: list[dict], inventario: dict, desde: int | None = None) -> dict:
    tablas = {t: _titulos_tabla(v) for t, v in (inventario.get("tablas") or {}).items()}
    reporte = {"ya_cargado": [], "falta": [], "en_otra_tabla": [], "no_publicado": [], "sin_titulo": [],
               "fuera_de_rango": [], "sin_tabla": []}
    for it in items:
        entrada = {k: it[k] for k in ("tipo", "anio", "titulo")} | {"linea": it["linea"][:220]}
        # Lo no publicado suele no tener año: chequearlo antes del rango para no esconderlo.
        if not it["publicado"]:
            reporte["no_publicado"].append(entrada)
        elif desde and (it["anio"] or 0) < desde:
            reporte["fuera_de_rango"].append(entrada)
        elif not it["titulo"]:
            reporte["sin_titulo"].append(entrada)
        elif it["tipo"] not in tablas:
            reporte["sin_tabla"].append(entrada)
        elif any(coincide(t, it["titulo"]) for t in tablas[it["tipo"]]):
            reporte["ya_cargado"].append(entrada)
        else:
            otras = [t for t, titulos in tablas.items() if t != it["tipo"] and any(coincide(x, it["titulo"]) for x in titulos)]
            reporte["en_otra_tabla" if otras else "falta"].append(entrada | ({"tabla": otras[0]} if otras else {}))
    reporte["resumen"] = {k: len(v) for k, v in reporte.items()}
    return reporte


# ------------------------------------------------------------------ PDF


def _rangos(paginas: str, total: int) -> list[int]:
    salida = []
    for parte in paginas.split(","):
        a, _, b = parte.strip().partition("-")
        inicio, fin = int(a), int(b or a)
        if not 1 <= inicio <= fin <= total:
            raise ValueError(f"rango de paginas invalido: {parte} (el PDF tiene {total})")
        salida.extend(range(inicio, fin + 1))
    return salida


def recortar_pdf(entrada: str | Path, salida: str | Path, paginas: str) -> int:
    """Copia las paginas pedidas (1-based, "2,45-53"): creditos con ISBN + el trabajo."""
    from pypdf import PdfReader, PdfWriter

    lector, escritor = PdfReader(str(entrada)), PdfWriter()
    elegidas = _rangos(paginas, len(lector.pages))
    for n in elegidas:
        escritor.add_page(lector.pages[n - 1])
    with open(salida, "wb") as f:
        escritor.write(f)
    return len(elegidas)


def comprimir_pdf(entrada: str | Path, salida: str | Path, max_mb: float) -> float:
    """Limpia y recomprime; si no alcanza, rebaja imagenes grandes a JPEG. Devuelve MB finales."""
    import io

    import pymupdf
    from PIL import Image

    doc = pymupdf.open(str(entrada))
    doc.save(str(salida), garbage=4, deflate=True, clean=True)
    mb = Path(salida).stat().st_size / 2**20
    if mb <= max_mb:
        return mb
    doc = pymupdf.open(str(entrada))
    hechas = set()
    for pagina in doc:
        for img in pagina.get_images(full=True):
            xref = img[0]
            if xref in hechas:
                continue
            hechas.add(xref)
            datos = doc.extract_image(xref)
            if len(datos["image"]) < 200_000:
                continue
            im = Image.open(io.BytesIO(datos["image"])).convert("RGB")
            im.thumbnail((1600, 1600))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=70)
            pagina.replace_image(xref, stream=buf.getvalue())
    doc.save(str(salida), garbage=4, deflate=True, clean=True)
    return Path(salida).stat().st_size / 2**20
