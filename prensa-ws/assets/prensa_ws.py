"""prensa-ws · Descarga verificada de ejemplares PDF de Prensa Histórica.

Adaptado desde Scripts/clase1/clase1_scraping.py (curso de web scraping con IA,
centra). Fuente `prensa` (Prensa Histórica, prensahistorica.mcu.es).

Sin topes autoimpuestos de volumen: `--n` acepta cualquier entero >= 1 por
publicación y `--publicacion` acepta una lista de ids o un archivo `@lista.txt`,
de modo que un mismo manifiesto pueda acumular miles de ejemplares. El ritmo es
configurable con `--pausa` (default 2 s; 0 = sin pausa). robots.txt del sitio:
HTTP 404. Las condiciones publicadas por el sitio (descargas personales
permitidas; contacto previo pedido para operaciones masivas) están documentadas
en references/fuente.md como información del operador; el script no las impone.

Comportamiento verificado (clase 1 + smoke de esta skill):

- El listado `numeros_por_mes.do?idPublicacion=...` expone enlaces cuyo texto
  visible es exactamente `PDF`; apuntan a `catalogo_imagenes/grupo.do?path=N`,
  que sirve el archivo PDF directamente (la URL no termina en `.pdf`).
- PDF validado por firma `%PDF-` + apertura con pypdf antes de mover a destino;
  SHA-256 en manifiesto; reutilización de archivos ya descargados.
- HTTP 401/403/429 aborta esa publicación y se reporta (`contenido_restringido`);
  no se eluden bloqueos técnicos ni se suplantan identidades.
- TLS verificado siempre (`truststore` en Windows); nunca `verify=False`.

Uso:

    python prensa_ws.py --n 3 --salida datos
    python prensa_ws.py --n 500 --publicacion 1002062 --salida datos
    python prensa_ws.py --n 2000 --publicacion @publicaciones.txt --pausa 0.5 --salida datos
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

try:
    import truststore
except ImportError:  # pragma: no cover - solo en entornos Windows sin truststore
    truststore = None

MANIFEST_COLUMNS = [
    "fuente",
    "id",
    "url_origen",
    "url_material",
    "tipo_material",
    "titulo",
    "fecha_publicacion",
    "autor",
    "capturado_en_utc",
    "ruta_html",
    "ruta_txt",
    "ruta_pdf",
    "sha256",
    "estado",
    "motivo",
]

SUMMARY_COLUMNS = [
    "fuente",
    "estado_acceso",
    "meta",
    "exitos_html",
    "exitos_pdf",
    "reutilizados",
    "omitidos",
    "errores",
    "faltante",
    "motivo_detencion",
    "consulta",
    "orden",
    "cobertura",
    "snapshot_html",
]

REQUEST_TIMEOUT = 30.0
DEFAULT_OUTPUT_DIRNAME = "datos"
DEFAULT_PUBLICACION = "1002062"
DEFAULT_TARGET = 3
DEFAULT_PAUSA_SECONDS = 2.0

SITE_BASE = "https://prensahistorica.mcu.es"
BULK_CONTACT_EMAIL = "info.bvph@cultura.gob.es"
BULK_POLICY_URL = (
    "https://prensahistorica.mcu.es/es/cms/elemento.do?id=estaticos/paginas/REPRODUCCIONES.html"
)
USER_AGENT = f"PrensaWsSkill/1.2 (contacto: {BULK_CONTACT_EMAIL})"

# Conocimiento verificado en la clase 1 por idPublicacion; otras publicaciones
# usan el mismo tipo de página pero parten con cobertura no verificada.
PUBLICACIONES_VERIFICADAS: dict[str, dict[str, str]] = {
    "1002062": {
        "consulta": "Pluma y Lápiz : periódico ilustrado (idPublicacion=1002062)",
        "orden": "Año, mes y número ascendente tal como aparece en el listado verificado",
        "cobertura": "33 enlaces PDF observados en el listado; números 1-34 con la excepción visible del 16",
    },
}


class PdfValidationError(RuntimeError):
    pass


class SourceAccessError(RuntimeError):
    def __init__(self, url: str, message: str, status_code: int | None = None, retry_after: str = ""):
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.retry_after = retry_after


@dataclass
class PrensaItem:
    fuente: str
    id: str
    url_origen: str
    url_material: str
    tipo_material: str
    titulo: str
    fecha_publicacion: str
    autor: str = ""


@dataclass
class MaterializationResult:
    reused: bool
    downloaded: bool
    sha256: str
    path: Path


@dataclass
class SourceResult:
    fuente: str
    estado_acceso: str
    meta: int
    exitos_html: int = 0
    exitos_pdf: int = 0
    reutilizados: int = 0
    omitidos: int = 0
    errores: int = 0
    faltante: int = 0
    motivo_detencion: str = ""
    consulta: str = ""
    orden: str = ""
    cobertura: str = ""
    snapshot_html: str = ""
    manifest_rows: list[dict[str, str]] = field(default_factory=list)


# ---------- Helpers genéricos ----------


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_publicacion_id(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned.isdigit():
        raise ValueError("cada idPublicacion debe ser numérico")
    return cleaned


def parse_publicaciones(value: str, base_dir: Path | None = None) -> list[str]:
    """Resuelve `--publicacion`: un id, lista separada por comas o `@archivo.txt`.

    El archivo admite un id por línea; se ignoran líneas vacías y comentarios `#`.
    """
    token = (value or "").strip()
    if not token:
        raise ValueError("--publicacion no puede estar vacío")
    if token.startswith("@"):
        path = Path(token[1:])
        if not path.is_absolute() and base_dir is not None:
            path = base_dir / path
        if not path.is_file():
            raise ValueError(f"archivo de publicaciones no encontrado: {token[1:]}")
        with path.open(encoding="utf-8") as handle:
            lines = [line.strip() for line in handle]
        tokens = [line for line in lines if line and not line.startswith("#")]
    else:
        tokens = [part.strip() for part in token.split(",")]
    if not tokens:
        raise ValueError("--publicacion no resolvió ningún id")
    publicaciones: list[str] = []
    for item in tokens:
        publicacion = validate_publicacion_id(item)
        if publicacion not in publicaciones:
            publicaciones.append(publicacion)
    if not publicaciones:
        raise ValueError("--publicacion no resolvió ningún id")
    return publicaciones


def validate_target_size(n: int) -> int:
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError("--n debe ser un entero >= 1")
    if n < 1:
        raise ValueError("--n debe ser un entero >= 1")
    return n


def validate_pausa(seconds: float) -> float:
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        raise ValueError("--pausa debe ser un número >= 0 (segundos)")
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("--pausa debe ser un número finito >= 0 (segundos)")
    return float(seconds)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def safe_filename(value: str, fallback: str = "item") -> str:
    value = normalize_whitespace(value)
    value = re.sub(r'[<>:"/\\|?*]+', "_", value)
    value = re.sub(r"[\x00-\x1f]+", "_", value)
    value = value.strip(" .")
    return value or fallback


def to_relative_text(path: Path, base_dir: Path) -> str:
    try:
        return path.relative_to(base_dir).as_posix()
    except ValueError:
        return path.as_posix()


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    ensure_directory(path.parent)
    with tempfile.NamedTemporaryFile("w", encoding=encoding, delete=False, dir=path.parent, newline="") as handle:
        tmp_path = Path(handle.name)
        handle.write(content)
    os.replace(tmp_path, path)


def ensure_pdf_openable(path: Path) -> None:
    with path.open("rb") as handle:
        signature = handle.read(5)
        if signature != b"%PDF-":
            raise PdfValidationError(f"{path} no comienza con firma PDF")
    try:
        PdfReader(str(path))
    except Exception as exc:  # pragma: no cover - los fallos de pypdf varían por archivo
        raise PdfValidationError(f"{path} no pudo abrirse con pypdf") from exc


def sniff_pdf_bytes(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise PdfValidationError("la respuesta no contiene firma PDF")
    try:
        PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise PdfValidationError("el PDF descargado no se pudo abrir con pypdf") from exc


def make_http_session() -> requests.Session:
    if sys.platform == "win32" and truststore is not None:
        truststore.inject_into_ssl()
    session = requests.Session()
    session.verify = True
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
        }
    )
    return session


def build_listing_url(publicacion: str) -> str:
    return f"{SITE_BASE}/es/publicaciones/numeros_por_mes.do?idPublicacion={publicacion}"


def publicacion_meta(publicacion: str) -> dict[str, str]:
    return PUBLICACIONES_VERIFICADAS.get(
        publicacion,
        {
            "consulta": f"publicación idPublicacion={publicacion}",
            "orden": "orden del listado tal como se publica",
            "cobertura": "publicacion_no_verificada_previamente",
        },
    )


# ---------- Manifiesto y resumen ----------


def build_manifest_row(
    *,
    fuente: str = "prensa",
    id_: str,
    url_origen: str,
    url_material: str = "",
    tipo_material: str = "",
    titulo: str = "",
    fecha_publicacion: str = "",
    autor: str = "",
    capturado_en_utc: str | None = None,
    ruta_html: str = "",
    ruta_txt: str = "",
    ruta_pdf: str = "",
    sha256_value: str = "",
    estado: str = "",
    motivo: str = "",
) -> dict[str, str]:
    return {
        "fuente": fuente,
        "id": id_,
        "url_origen": url_origen,
        "url_material": url_material,
        "tipo_material": tipo_material,
        "titulo": titulo,
        "fecha_publicacion": fecha_publicacion,
        "autor": autor,
        "capturado_en_utc": capturado_en_utc or utc_now_iso(),
        "ruta_html": ruta_html,
        "ruta_txt": ruta_txt,
        "ruta_pdf": ruta_pdf,
        "sha256": sha256_value,
        "estado": estado,
        "motivo": motivo,
    }


def load_manifest_rows(output_dir: Path) -> list[dict[str, str]]:
    manifest_path = output_dir / "manifest.csv"
    if not manifest_path.exists():
        return []
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


PAGE_ROW_PATTERN = re.compile(r"^prensa_(?P<pub>\d+)_(?:preflight|error|anyo_\d+)$")


def _is_stale_page_row(row: dict[str, str], publicaciones: set[str]) -> bool:
    match = PAGE_ROW_PATTERN.match(row.get("id", ""))
    return bool(match and match.group("pub") in publicaciones)


def write_manifest(rows: list[dict[str, str]], output_dir: Path, publicaciones: list[str] | None = None) -> Path:
    """Escribe el manifiesto preservando filas de ejecuciones anteriores.

    La identidad de un registro es (fuente, id); la URL de descubrimiento no
    participa, para que un mismo material no duplique filas ni impida reutilizar
    el archivo ya descargado. Al re-ejecutar publicaciones (parámetro
    `publicaciones`), se descartan sus filas de página obsoletas
    (`prensa_<pub>_preflight|error|anyo_<YYYY>`): el resultado vigente de esa
    publicación es el de la corrida actual, y una fila de error vieja no debe
    contradecir descargas exitosas.
    """
    manifest_path = output_dir / "manifest.csv"
    ensure_directory(output_dir)
    merged = load_manifest_rows(output_dir)
    if publicaciones:
        touched = set(publicaciones)
        merged = [row for row in merged if not _is_stale_page_row(row, touched)]
    position = {(row.get("fuente", ""), row.get("id", "")): index for index, row in enumerate(merged)}
    for row in rows:
        complete = {column: row.get(column, "") for column in MANIFEST_COLUMNS}
        key = (complete["fuente"], complete["id"])
        if key in position:
            merged[position[key]] = complete
        else:
            position[key] = len(merged)
            merged.append(complete)
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(merged)
    return manifest_path


def write_summary(rows: list[dict[str, str]], output_dir: Path) -> Path:
    summary_path = output_dir / "resumen.csv"
    ensure_directory(output_dir)
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return summary_path


def load_previous_successes(output_dir: Path) -> dict[tuple[str, str], dict[str, str]]:
    successes: dict[tuple[str, str], dict[str, str]] = {}
    for row in load_manifest_rows(output_dir):
        if row.get("estado") == "descargado_pdf" and row.get("sha256"):
            successes[(row.get("fuente", ""), row.get("id", ""))] = row
    return successes


# ---------- Extracción del listado ----------


OLD_DATE_PATTERN = re.compile(r"Año\s+.+?Número\s+(?P<num>\d+)\s+-\s+(?P<fecha>\d{1,2}\s+\w+\s+\d{4})")
NEW_DATE_PATTERN = re.compile(r"Número\s+(?P<num>\d+)\s+-\s+(?P<fecha>\d{4}\s+\w+)")
YEAR_LINK_PATTERN = re.compile(r"numeros_por_mes\.do\?idPublicacion=\d+&(?:amp;)?anyo=(\d{4})")


def _is_pdf_anchor(anchor) -> bool:
    """Reconoce las dos variantes reales de enlace de ejemplar.

    - Diseño clásico: texto visible exactamente `PDF`.
    - Diseño con iconos: sin texto útil, pero con
      `data-analytics-grouptitle="PDF"` (o `title` que empieza con `PDF`).
    """
    if normalize_whitespace(anchor.get_text(" ", strip=True)) == "PDF":
        return True
    if normalize_whitespace(anchor.get("data-analytics-grouptitle", "")) == "PDF":
        return True
    return (anchor.get("title") or "").strip().upper().startswith("PDF")


def _item_metadata(anchor, title: str) -> tuple[str, str]:
    """Devuelve (título, fecha) desde el metadato del sitio o el texto previo."""
    record_title = anchor.get("data-analytics-recordtitle")
    if record_title:
        title = normalize_whitespace(record_title)
    for pattern in (OLD_DATE_PATTERN, NEW_DATE_PATTERN):
        match = pattern.search(title)
        if match:
            return title, match.group("fecha")
    return title, ""


def extract_prensa_items(html: str, base_url: str) -> list[PrensaItem]:
    """Extrae ejemplares de una página de listado (números por mes o por año).

    Acepta ambos diseños del sitio. En el clásico, el nodo de texto anterior
    (`Año I Número 1 - 16 Marzo 1893`) aporta título y fecha; en el de iconos,
    `data-analytics-recordtitle` (`Gazeta de México: Número 36 - 1730
    noviembre`). Los enlaces de copia JPEG y ficha se descartan.
    """
    soup = BeautifulSoup(html, "html.parser")
    items: list[PrensaItem] = []
    seen_ids: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href") or ""
        resolved = urljoin(base_url, href)
        if "grupo.do" not in resolved:
            continue
        if not _is_pdf_anchor(anchor):
            continue
        title = ""
        prior = anchor.find_previous(string=OLD_DATE_PATTERN)
        if prior:
            title = normalize_whitespace(str(prior))
        if not title and anchor.get("data-analytics-recordtitle"):
            title = normalize_whitespace(anchor.get("data-analytics-recordtitle"))
        title, fecha = _item_metadata(anchor, title)
        pdf_id_match = re.search(r"path=(\d+)", resolved)
        if pdf_id_match:
            material_id = f"prensa_{pdf_id_match.group(1)}"
        else:
            material_id = f"prensa_{safe_filename(title, fallback='pdf')}"
        if material_id in seen_ids:
            continue
        seen_ids.add(material_id)
        items.append(
            PrensaItem(
                fuente="prensa",
                id=material_id,
                url_origen=base_url,
                url_material=resolved,
                tipo_material="pdf",
                titulo=title,
                fecha_publicacion=fecha,
            )
        )
    return items


def extract_year_urls(html: str, base_url: str) -> dict[int, str]:
    """Años adicionales enlazados desde un listado (`...&anyo=YYYY`).

    `numeros_por_mes.do` muestra un año por página; el resto de años aparece
    como enlaces `Año YYYY`. Las publicaciones de un solo año no tienen enlaces.
    """
    soup = BeautifulSoup(html, "html.parser")
    years: dict[int, str] = {}
    for anchor in soup.find_all("a", href=True):
        match = YEAR_LINK_PATTERN.search(anchor.get("href") or "")
        if match:
            years.setdefault(int(match.group(1)), urljoin(base_url, anchor.get("href") or ""))
    return years


def fetch_listing_snapshot(session: requests.Session, url: str, destination: Path) -> str:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    if response.status_code in {401, 403, 429}:
        retry_after = response.headers.get("Retry-After", "")
        detail = f"Listado Prensa respondió HTTP {response.status_code}"
        if retry_after:
            detail = f"{detail}; Retry-After={retry_after}"
        raise SourceAccessError(url, detail, status_code=response.status_code, retry_after=retry_after)
    if response.status_code != 200:
        raise RuntimeError(f"Listado Prensa devolvió HTTP {response.status_code}")
    text = response.text
    atomic_write_text(destination, text, encoding="utf-8")
    return text


# ---------- Descarga y validación de PDF ----------


def existing_pdf_is_valid(path: Path, expected_sha256: str | None = None) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        ensure_pdf_openable(path)
    except PdfValidationError:
        return False
    if expected_sha256 is not None and sha256_file(path) != expected_sha256:
        return False
    return True


def download_pdf_atomic(
    *,
    session: requests.Session,
    url: str,
    destination: Path,
    timeout: float,
) -> MaterializationResult:
    response = session.get(url, timeout=timeout, allow_redirects=True)
    if response.status_code in {401, 403, 429}:
        retry_after = response.headers.get("Retry-After", "")
        detail = f"PDF respondió HTTP {response.status_code}"
        if retry_after:
            detail = f"{detail}; Retry-After={retry_after}"
        raise SourceAccessError(url, detail, status_code=response.status_code, retry_after=retry_after)
    if response.status_code != 200:
        raise PdfValidationError(f"HTTP {response.status_code} al descargar PDF")
    content_type = response.headers.get("Content-Type", "").lower()
    if "pdf" not in content_type:
        raise PdfValidationError(f"Content-Type no PDF: {content_type or 'sin header'}")
    data = response.content
    sniff_pdf_bytes(data)
    ensure_directory(destination.parent)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=destination.parent, suffix=".part") as handle:
        temp_path = Path(handle.name)
        handle.write(data)
    try:
        ensure_pdf_openable(temp_path)
        os.replace(temp_path, destination)
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return MaterializationResult(reused=False, downloaded=True, sha256=sha256_bytes(data), path=destination)


def materialize_pdf_item(
    *,
    session: requests.Session,
    url: str,
    destination: Path,
    expected_sha256: str | None = None,
    timeout: float = REQUEST_TIMEOUT,
) -> MaterializationResult:
    if existing_pdf_is_valid(destination, expected_sha256=expected_sha256):
        return MaterializationResult(
            reused=True,
            downloaded=False,
            sha256=sha256_file(destination),
            path=destination,
        )
    result = download_pdf_atomic(session=session, url=url, destination=destination, timeout=timeout)
    if expected_sha256 is not None and result.sha256 != expected_sha256:
        destination.unlink(missing_ok=True)
        raise PdfValidationError(
            f"Hash inesperado para {destination.name}: {result.sha256} != {expected_sha256}"
        )
    return result


# ---------- Ejecución por publicación ----------


def build_prensa_destination(output_dir: Path, item: PrensaItem) -> Path:
    return output_dir / "prensa" / "pdf" / f"{safe_filename(item.id, fallback='pdf')}.pdf"


def build_summary_row(result: SourceResult) -> dict[str, str]:
    return {
        "fuente": result.fuente,
        "estado_acceso": result.estado_acceso,
        "meta": str(result.meta),
        "exitos_html": str(result.exitos_html),
        "exitos_pdf": str(result.exitos_pdf),
        "reutilizados": str(result.reutilizados),
        "omitidos": str(result.omitidos),
        "errores": str(result.errores),
        "faltante": str(result.faltante),
        "motivo_detencion": result.motivo_detencion,
        "consulta": result.consulta,
        "orden": result.orden,
        "cobertura": result.cobertura,
        "snapshot_html": result.snapshot_html,
    }


def run_prensa_source(
    *,
    session: requests.Session,
    output_dir: Path,
    target_meta: int,
    previous_successes: dict[tuple[str, str], dict[str, str]],
    publicacion: str = DEFAULT_PUBLICACION,
    pausa: float = DEFAULT_PAUSA_SECONDS,
) -> SourceResult:
    cfg = publicacion_meta(publicacion)
    listing_url = build_listing_url(publicacion)
    source_dir = output_dir / "prensa"
    ensure_directory(source_dir)
    snapshot_path = source_dir / f"prensa_listado_numeros_por_mes_{publicacion}.html"

    try:
        html = fetch_listing_snapshot(session, listing_url, snapshot_path)
    except SourceAccessError as exc:
        return SourceResult(
            fuente="prensa",
            estado_acceso="contenido_restringido",
            meta=target_meta,
            errores=1,
            faltante=target_meta,
            motivo_detencion=str(exc),
            consulta=cfg["consulta"],
            orden=cfg["orden"],
            cobertura=cfg["cobertura"],
            snapshot_html="",
            manifest_rows=[
                build_manifest_row(
                    id_=f"prensa_{publicacion}_preflight",
                    url_origen=listing_url,
                    estado="contenido_restringido",
                    motivo=str(exc),
                )
            ],
        )

    items = extract_prensa_items(html, listing_url)
    year_urls = extract_year_urls(html, listing_url)
    pages_fetched = 1
    page_restrictions: list[dict[str, str]] = []
    seen_item_ids = {item.id for item in items}

    for year in sorted(year_urls):
        if len(items) >= target_meta:
            break
        year_url = year_urls[year]
        year_snapshot = source_dir / f"prensa_listado_numeros_por_mes_{publicacion}_{year}.html"
        try:
            year_html = fetch_listing_snapshot(session, year_url, year_snapshot)
        except SourceAccessError as exc:
            page_restrictions.append(
                build_manifest_row(
                    id_=f"prensa_{publicacion}_anyo_{year}",
                    url_origen=year_url,
                    estado="contenido_restringido",
                    motivo=str(exc),
                )
            )
            break
        pages_fetched += 1
        for item in extract_prensa_items(year_html, year_url):
            if item.id in seen_item_ids:
                continue
            seen_item_ids.add(item.id)
            items.append(item)
        time.sleep(pausa)

    if not items:
        raise RuntimeError(
            "el listado no contiene enlaces PDF con el formato esperado; "
            "revisar references/fuente.md y re-diagnosticar antes de insistir"
        )

    seen_hashes = {row.get("sha256", "") for row in previous_successes.values() if row.get("sha256")}
    manifest_rows: list[dict[str, str]] = list(page_restrictions)
    reused = 0
    errores = len(page_restrictions)
    omitidos = 0
    exitos_pdf = 0
    first_pdf_waited = False

    for item in items[:target_meta]:
        if not first_pdf_waited:
            time.sleep(pausa)
            first_pdf_waited = True
        dest = build_prensa_destination(output_dir, item)
        prev_success = previous_successes.get((item.fuente, item.id))
        expected_sha = str(prev_success.get("sha256", "") or "") if prev_success else ""
        captured_at = str(prev_success.get("capturado_en_utc", "") or "") if prev_success else ""

        try:
            result = materialize_pdf_item(
                session=session,
                url=item.url_material,
                destination=dest,
                expected_sha256=expected_sha or None,
            )
        except SourceAccessError as exc:
            errores += 1
            manifest_rows.append(
                build_manifest_row(
                    id_=item.id,
                    url_origen=item.url_origen,
                    url_material=item.url_material,
                    tipo_material=item.tipo_material,
                    titulo=item.titulo,
                    fecha_publicacion=item.fecha_publicacion,
                    autor=item.autor,
                    estado="contenido_restringido",
                    motivo=str(exc),
                )
            )
            return SourceResult(
                fuente="prensa",
                estado_acceso="contenido_restringido",
                meta=target_meta,
                exitos_pdf=exitos_pdf,
                reutilizados=reused,
                omitidos=omitidos,
                errores=errores,
                faltante=max(target_meta - exitos_pdf, 0),
                motivo_detencion=str(exc),
                consulta=cfg["consulta"],
                orden=cfg["orden"],
                cobertura=cfg["cobertura"],
                snapshot_html=to_relative_text(snapshot_path, output_dir),
                manifest_rows=manifest_rows,
            )
        except Exception as exc:
            errores += 1
            manifest_rows.append(
                build_manifest_row(
                    id_=item.id,
                    url_origen=item.url_origen,
                    url_material=item.url_material,
                    tipo_material=item.tipo_material,
                    titulo=item.titulo,
                    fecha_publicacion=item.fecha_publicacion,
                    autor=item.autor,
                    estado="error",
                    motivo=str(exc),
                )
            )
            time.sleep(pausa)
            continue

        is_prev_success_same_sha = bool(prev_success and prev_success.get("sha256", "") == result.sha256)
        if result.sha256 and result.sha256 in seen_hashes and not is_prev_success_same_sha:
            omitidos += 1
            manifest_rows.append(
                build_manifest_row(
                    id_=item.id,
                    url_origen=item.url_origen,
                    url_material=item.url_material,
                    tipo_material=item.tipo_material,
                    titulo=item.titulo,
                    fecha_publicacion=item.fecha_publicacion,
                    autor=item.autor,
                    capturado_en_utc=captured_at or None,
                    ruta_pdf=to_relative_text(dest, output_dir),
                    sha256_value=result.sha256,
                    estado="omitido",
                    motivo="duplicado_sha256",
                )
            )
            time.sleep(pausa)
            continue

        if result.sha256:
            seen_hashes.add(result.sha256)
        if result.reused:
            reused += 1
        exitos_pdf += 1
        manifest_rows.append(
            build_manifest_row(
                id_=item.id,
                url_origen=item.url_origen,
                url_material=item.url_material,
                tipo_material=item.tipo_material,
                titulo=item.titulo,
                fecha_publicacion=item.fecha_publicacion,
                autor=item.autor,
                capturado_en_utc=captured_at or None,
                ruta_pdf=to_relative_text(dest, output_dir),
                sha256_value=result.sha256,
                estado="descargado_pdf",
                motivo="reutilizado_existente_valido" if result.reused else "descargado_nuevo",
            )
        )
        time.sleep(pausa)

    faltante = max(target_meta - exitos_pdf, 0)
    motivo = "meta alcanzada" if exitos_pdf >= target_meta else f"solo {exitos_pdf} PDF disponibles en el listado obtenido"
    if pages_fetched > 1:
        motivo += f" ({pages_fetched} páginas de año consultadas)"
    if page_restrictions:
        motivo += f"; {len(page_restrictions)} página(s) de año con acceso restringido"
    return SourceResult(
        fuente="prensa",
        estado_acceso="abierto",
        meta=target_meta,
        exitos_pdf=exitos_pdf,
        reutilizados=reused,
        omitidos=omitidos + max(len(items) - min(len(items), target_meta), 0),
        errores=errores,
        faltante=faltante,
        motivo_detencion=motivo,
        consulta=cfg["consulta"],
        orden=cfg["orden"],
        cobertura=cfg["cobertura"],
        snapshot_html=to_relative_text(snapshot_path, output_dir),
        manifest_rows=manifest_rows,
    )


def run_pipeline(
    target_size: int,
    output_dir: Path,
    publicaciones: list[str] | None = None,
    session: requests.Session | None = None,
    pausa: float = DEFAULT_PAUSA_SECONDS,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Ejecuta todas las publicaciones pedidas sobre un mismo manifiesto.

    Un fallo o bloqueo de una publicación aborta solo esa publicación; las
    demás continúan y todo queda registrado.
    """
    target_meta = validate_target_size(target_size)
    validate_pausa(pausa)
    publicaciones = publicaciones or [DEFAULT_PUBLICACION]
    if not publicaciones:
        raise ValueError("se requiere al menos una idPublicacion")
    ensure_directory(output_dir)

    own_session = session is None
    active_session = session if session is not None else make_http_session()
    manifest_rows: list[dict[str, str]] = []
    summary_rows: list[dict[str, str]] = []
    try:
        previous_successes = load_previous_successes(output_dir)
        for publicacion in publicaciones:
            cfg = publicacion_meta(publicacion)
            try:
                result = run_prensa_source(
                    session=active_session,
                    output_dir=output_dir,
                    target_meta=target_meta,
                    previous_successes=previous_successes,
                    publicacion=publicacion,
                    pausa=pausa,
                )
            except Exception as exc:
                result = SourceResult(
                    fuente="prensa",
                    estado_acceso="error",
                    meta=target_meta,
                    errores=1,
                    faltante=target_meta,
                    motivo_detencion=str(exc),
                    consulta=cfg["consulta"],
                    orden=cfg["orden"],
                    cobertura=cfg["cobertura"],
                    snapshot_html="",
                    manifest_rows=[
                        build_manifest_row(
                            id_=f"prensa_{publicacion}_error",
                            url_origen=build_listing_url(publicacion),
                            estado="error",
                            motivo=str(exc),
                        )
                    ],
                )
            manifest_rows.extend(result.manifest_rows)
            summary_rows.append(build_summary_row(result))
    finally:
        if own_session:
            active_session.close()
    return manifest_rows, summary_rows


# ---------- CLI ----------


def print_cli_summary(summary_rows: list[dict[str, str]], output_dir: Path) -> None:
    print(f"Resumen prensa-ws · salida={output_dir}")
    for row in summary_rows:
        print(
            "- {consulta}: meta={meta} pdf={exitos_pdf} reutilizados={reutilizados} "
            "omitidos={omitidos} errores={errores} faltante={faltante} motivo={motivo_detencion}".format(**row)
        )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="prensa-ws · Prensa Histórica (prensahistorica.mcu.es)")
    parser.add_argument(
        "--n",
        type=int,
        default=DEFAULT_TARGET,
        help="objetivo de ejemplares por publicación; cualquier entero >= 1, sin tope (default: 3)",
    )
    parser.add_argument(
        "--publicacion",
        default=DEFAULT_PUBLICACION,
        help="idPublicacion, lista separada por comas o @archivo.txt con un id por línea",
    )
    parser.add_argument(
        "--pausa",
        type=float,
        default=DEFAULT_PAUSA_SECONDS,
        help=f"segundos entre peticiones; 0 desactiva la pausa (default: {DEFAULT_PAUSA_SECONDS})",
    )
    parser.add_argument("--salida", type=Path, default=Path.cwd() / DEFAULT_OUTPUT_DIRNAME)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        validate_target_size(args.n)
        validate_pausa(args.pausa)
        publicaciones = parse_publicaciones(args.publicacion, base_dir=Path.cwd())
    except ValueError as exc:
        print(f"Error de argumentos: {exc}", file=sys.stderr)
        return 2

    manifest_rows, summary_rows = run_pipeline(
        args.n, args.salida, publicaciones, pausa=args.pausa
    )
    write_manifest(manifest_rows, args.salida, publicaciones=publicaciones)
    write_summary(summary_rows, args.salida)
    print_cli_summary(summary_rows, args.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
