"""Tests offline de prensa-ws: fixtures HTML y PDF locales, sin red."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from unittest import mock

from pypdf import PdfWriter

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import prensa_ws as scraping  # noqa: E402

LISTING_URL = "https://prensahistorica.mcu.es/es/publicaciones/numeros_por_mes.do?idPublicacion=1002062"
OTHER_LISTING_URL = "https://prensahistorica.mcu.es/es/publicaciones/numeros_por_mes.do?idPublicacion=1000798295"


def make_pdf_bytes(pages: int = 1, title: str = "") -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    if title:
        writer.add_metadata({"/Title": title})
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


HTML_ONE_ITEM = """
<html><body>
  <div class="issue">
    <div>Año I Número 1 - 16 Marzo 1893</div>
    <a href="../catalogo_imagenes/grupo.do?path=1000375459">Copia digital</a>
    <a href="../catalogo_imagenes/grupo.do?path=2000857258">PDF</a>
    <a href="/es/consulta/registro.do?id=1029158">Ficha</a>
  </div>
</body></html>
"""

HTML_TWO_ITEMS = """
<html><body>
  <div class="issue">
    <div>Año I Número 1 - 16 Marzo 1893</div>
    <a href="../catalogo_imagenes/grupo.do?path=1000375459">Copia digital</a>
    <a href="../catalogo_imagenes/grupo.do?path=2000857258">PDF</a>
    <a href="/es/consulta/registro.do?id=1029158">Ficha</a>
  </div>
  <div class="issue">
    <div>Año I Número 2 - 23 Marzo 1893</div>
    <a href="../catalogo_imagenes/grupo.do?path=1000375460">Copia digital</a>
    <a href="../catalogo_imagenes/grupo.do?path=2000857259">PDF</a>
  </div>
</body></html>
"""

HTML_OTHER_PUB_ONE_ITEM = """
<html><body>
  <div class="issue">
    <div>Año I Número 1 - 2 Enero 1900</div>
    <a href="../catalogo_imagenes/grupo.do?path=3000000001">PDF</a>
  </div>
</body></html>
"""

# Diseño con iconos (observado en idPublicacion=1006238): sin texto "PDF",
# el marcador es data-analytics-grouptitle="PDF" y la fecha viene en
# data-analytics-recordtitle. El enlace JPEG comparte path y no debe tomarse.
HTML_ICON_LAYOUT = """
<html><body>
  <div class="item">
    <a id="gri8476519-icon" href="../catalogo_imagenes/grupo.do?path=8476519"
       data-analytics-grouptitle="Copia en JPEG"
       data-analytics-recordtitle="Gazeta de México: Número 36 - 1730 noviembre"
       title="Copia en JPEG"></a>
    <a id="gri8476519" href="../catalogo_imagenes/grupo.do?path=8476519"
       data-analytics-grouptitle="PDF"
       data-analytics-recordtitle="Gazeta de México: Número 36 - 1730 noviembre"
       title='PDF - &quot;Se abrirá una ventana nueva&quot;'></a>
  </div>
  <div class="item">
    <a id="gri8476520-icon" href="../catalogo_imagenes/grupo.do?path=8476520"
       data-analytics-grouptitle="Copia en JPEG"
       data-analytics-recordtitle="Gazeta de México: Número 37 - 1730 diciembre"></a>
    <a id="gri8476520" href="../catalogo_imagenes/grupo.do?path=8476520"
       data-analytics-grouptitle="PDF"
       data-analytics-recordtitle="Gazeta de México: Número 37 - 1730 diciembre">PDF</a>
  </div>
</body></html>
"""

# Listado por años: la página muestra un año y enlaza los demás con anyo=YYYY.
HTML_YEAR_1730 = """
<html><body>
  <div class="item">
    <a href="../catalogo_imagenes/grupo.do?path=8476519"
       data-analytics-grouptitle="PDF"
       data-analytics-recordtitle="Gazeta de México: Número 36 - 1730 noviembre"></a>
  </div>
  <div class="item">
    <a href="../catalogo_imagenes/grupo.do?path=8476520"
       data-analytics-grouptitle="PDF"
       data-analytics-recordtitle="Gazeta de México: Número 37 - 1730 diciembre"></a>
  </div>
  <a href="../publicaciones/numeros_por_mes.do?idPublicacion=1006238&amp;anyo=1732">Año 1732</a>
</body></html>
"""

HTML_YEAR_1732 = """
<html><body>
  <div class="item">
    <a href="../catalogo_imagenes/grupo.do?path=8476521"
       data-analytics-grouptitle="PDF"
       data-analytics-recordtitle="Gazeta de México: Número 52 - 1732 marzo"></a>
  </div>
  <a href="../publicaciones/numeros_por_mes.do?idPublicacion=1006238&amp;anyo=1730">Año 1730</a>
</body></html>
"""


@dataclass
class FakeResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes
    url: str = "https://example.test/material.pdf"

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.requests: list[tuple[str, float | None, bool]] = []
        self.closed = False

    def get(self, url: str, timeout: float | None = None, allow_redirects: bool = True):
        self.requests.append((url, timeout, allow_redirects))
        if not self.responses:
            raise AssertionError(f"Unexpected network call for {url}")
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


def listing_response(html: str) -> FakeResponse:
    return FakeResponse(
        status_code=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        content=html.encode("utf-8"),
    )


def pdf_response(content: bytes) -> FakeResponse:
    return FakeResponse(
        status_code=200,
        headers={"Content-Type": "application/pdf"},
        content=content,
    )


class ValidateArgsTests(unittest.TestCase):
    def test_target_size_has_no_upper_bound(self):
        for valid in (1, 3, 10, 100, 200, 5000, 1_000_000):
            with self.subTest(valid=valid):
                self.assertEqual(valid, scraping.validate_target_size(valid))

    def test_target_size_rejects_invalid(self):
        for invalid in (0, -1, 2.5, True, None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    scraping.validate_target_size(invalid)

    def test_pausa_accepts_zero_and_rejects_negative(self):
        self.assertEqual(0.0, scraping.validate_pausa(0))
        self.assertEqual(1.5, scraping.validate_pausa(1.5))
        with self.assertRaises(ValueError):
            scraping.validate_pausa(-0.1)

    def test_pausa_rejects_non_finite_values(self):
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    scraping.validate_pausa(invalid)

    def test_publicacion_id_must_be_numeric(self):
        with self.assertRaises(ValueError):
            scraping.validate_publicacion_id("abc-1002062")
        self.assertEqual("1002062", scraping.validate_publicacion_id(" 1002062 "))


class ParsePublicacionesTests(unittest.TestCase):
    def test_single_and_comma_separated_ids(self):
        self.assertEqual(["1002062"], scraping.parse_publicaciones("1002062"))
        self.assertEqual(
            ["1002062", "1000798295"],
            scraping.parse_publicaciones("1002062, 1000798295"),
        )
    def test_deduplicates_preserving_order(self):
        self.assertEqual(
            ["1000798295", "1002062"],
            scraping.parse_publicaciones("1000798295,1002062,1000798295"),
        )

    def test_reads_id_list_from_file_ignoring_comments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            list_file = Path(tmpdir) / "pubs.txt"
            list_file.write_text(
                "# publicaciones objetivo\n1002062\n\n1000798295\n", encoding="utf-8"
            )
            self.assertEqual(
                ["1002062", "1000798295"],
                scraping.parse_publicaciones("@pubs.txt", base_dir=Path(tmpdir)),
            )

    def test_rejects_missing_file_and_bad_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                scraping.parse_publicaciones("@noexiste.txt", base_dir=Path(tmpdir))
        with self.assertRaises(ValueError):
            scraping.parse_publicaciones("1002062,no-numero")
        with self.assertRaises(ValueError):
            scraping.parse_publicaciones("")


class BuildUrlsTests(unittest.TestCase):
    def test_listing_url_uses_publicacion_id(self):
        self.assertEqual(
            "https://prensahistorica.mcu.es/es/publicaciones/numeros_por_mes.do?idPublicacion=1002062",
            scraping.build_listing_url("1002062"),
        )

    def test_unverified_publicacion_reports_coverage(self):
        meta = scraping.publicacion_meta("9999999")
        self.assertEqual("publicacion_no_verificada_previamente", meta["cobertura"])
        verified = scraping.publicacion_meta("1002062")
        self.assertIn("33 enlaces PDF", verified["cobertura"])


class ExtractPrensaItemsTests(unittest.TestCase):
    def test_extracts_items_from_listing_html(self):
        items = scraping.extract_prensa_items(HTML_TWO_ITEMS, base_url=LISTING_URL)
        self.assertEqual(2, len(items))
        self.assertEqual("prensa_2000857258", items[0].id)
        self.assertEqual("Año I Número 1 - 16 Marzo 1893", items[0].titulo)
        self.assertEqual(
            "https://prensahistorica.mcu.es/es/catalogo_imagenes/grupo.do?path=2000857258",
            items[0].url_material,
        )
        self.assertEqual("16 Marzo 1893", items[0].fecha_publicacion)
        self.assertEqual("23 Marzo 1893", items[1].fecha_publicacion)

    def test_ignores_copia_digital_and_record_links(self):
        items = scraping.extract_prensa_items(HTML_ONE_ITEM, base_url=LISTING_URL)
        self.assertEqual(1, len(items))
        self.assertNotIn("1000375459", items[0].url_material)
        self.assertNotIn("registro.do", items[0].url_material)

    def test_extracts_icon_layout_and_recordtitle(self):
        items = scraping.extract_prensa_items(HTML_ICON_LAYOUT, base_url=LISTING_URL)
        self.assertEqual(2, len(items))
        self.assertEqual(["prensa_8476519", "prensa_8476520"], [item.id for item in items])
        self.assertEqual("Gazeta de México: Número 36 - 1730 noviembre", items[0].titulo)
        self.assertEqual("1730 noviembre", items[0].fecha_publicacion)
        self.assertEqual("1730 diciembre", items[1].fecha_publicacion)
        self.assertTrue(all("grupo.do" in item.url_material for item in items))

    def test_extract_year_urls_from_listing(self):
        years = scraping.extract_year_urls(HTML_YEAR_1730, LISTING_URL)
        self.assertEqual([1732], list(years))
        self.assertIn("anyo=1732", years[1732])
        self.assertEqual({}, scraping.extract_year_urls(HTML_TWO_ITEMS, LISTING_URL))


class PdfMaterializationTests(unittest.TestCase):
    def test_download_rejects_html_and_leaves_no_final_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "bad.pdf"
            session = FakeSession(
                [
                    FakeResponse(
                        status_code=200,
                        headers={"Content-Type": "text/html; charset=utf-8"},
                        content=b"<html><body>not a pdf</body></html>",
                    )
                ]
            )
            with self.assertRaises(scraping.PdfValidationError):
                scraping.download_pdf_atomic(
                    session=session,
                    url="https://example.test/material.pdf",
                    destination=dest,
                    timeout=5,
                )
            self.assertFalse(dest.exists())
            self.assertEqual([], list(dest.parent.glob("bad.pdf*")))

    def test_reuses_existing_valid_pdf_without_downloading(self):
        pdf_bytes = make_pdf_bytes(pages=1, title="original")
        expected_sha = scraping.sha256_bytes(pdf_bytes)
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "prensa" / "pdf" / "item.pdf"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(pdf_bytes)
            session = FakeSession([])
            result = scraping.materialize_pdf_item(
                session=session,
                url="https://example.test/material.pdf",
                destination=dest,
                expected_sha256=expected_sha,
                timeout=5,
            )
            self.assertTrue(result.reused)
            self.assertFalse(result.downloaded)
            self.assertEqual(expected_sha, result.sha256)
            self.assertEqual(0, len(session.requests))

    def test_redownloads_when_existing_pdf_is_corrupted(self):
        good_pdf = make_pdf_bytes(pages=1, title="good")
        good_sha = scraping.sha256_bytes(good_pdf)
        bad_pdf = good_pdf[:32]
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "prensa" / "pdf" / "item.pdf"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(bad_pdf)
            session = FakeSession([pdf_response(good_pdf)])
            result = scraping.materialize_pdf_item(
                session=session,
                url="https://example.test/material.pdf",
                destination=dest,
                expected_sha256=good_sha,
                timeout=5,
            )
            self.assertFalse(result.reused)
            self.assertTrue(result.downloaded)
            self.assertEqual(good_pdf, dest.read_bytes())
            self.assertEqual(1, len(session.requests))

    def test_redownloads_when_existing_pdf_hash_changes_but_file_still_opens(self):
        original_pdf = make_pdf_bytes(pages=1, title="original")
        original_sha = scraping.sha256_bytes(original_pdf)
        altered_pdf = make_pdf_bytes(pages=2, title="altered")
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "prensa" / "pdf" / "item.pdf"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(altered_pdf)
            session = FakeSession([pdf_response(original_pdf)])
            result = scraping.materialize_pdf_item(
                session=session,
                url="https://example.test/material.pdf",
                destination=dest,
                expected_sha256=original_sha,
                timeout=5,
            )
            self.assertFalse(result.reused)
            self.assertTrue(result.downloaded)
            self.assertEqual(original_pdf, dest.read_bytes())
            self.assertEqual(1, len(session.requests))


class RunPrensaSourceTests(unittest.TestCase):
    def test_downloads_and_manifests_each_item(self):
        first = make_pdf_bytes(pages=1, title="one")
        second = make_pdf_bytes(pages=1, title="two")
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession([listing_response(HTML_TWO_ITEMS), pdf_response(first), pdf_response(second)])
            result = scraping.run_prensa_source(
                session=session,
                output_dir=Path(tmpdir),
                target_meta=2,
                previous_successes={},
            )
            self.assertEqual(2, result.exitos_pdf)
            self.assertEqual(0, result.errores)
            self.assertEqual("abierto", result.estado_acceso)
            self.assertEqual("meta alcanzada", result.motivo_detencion)
            estados = [row["estado"] for row in result.manifest_rows]
            self.assertEqual(["descargado_pdf", "descargado_pdf"], estados)
            self.assertTrue(all(len(row["sha256"]) == 64 for row in result.manifest_rows))
            self.assertTrue((Path(tmpdir) / "prensa" / "pdf" / "prensa_2000857258.pdf").exists())
            self.assertTrue((Path(tmpdir) / "prensa" / "pdf" / "prensa_2000857259.pdf").exists())

    def test_reuse_preserves_original_capture_time(self):
        pdf_bytes = make_pdf_bytes(pages=1, title="original")
        sha = scraping.sha256_bytes(pdf_bytes)
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            output_dir = Path(tmpdir)
            dest = output_dir / "prensa" / "pdf" / "prensa_2000857258.pdf"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(pdf_bytes)
            previous = {
                ("prensa", "prensa_2000857258"): {
                    "fuente": "prensa",
                    "id": "prensa_2000857258",
                    "sha256": sha,
                    "capturado_en_utc": "2024-01-01T00:00:00Z",
                    "estado": "descargado_pdf",
                }
            }
            session = FakeSession([listing_response(HTML_ONE_ITEM)])
            result = scraping.run_prensa_source(
                session=session,
                output_dir=output_dir,
                target_meta=1,
                previous_successes=previous,
            )
            self.assertEqual(1, result.exitos_pdf)
            self.assertEqual(1, result.reutilizados)
            self.assertEqual(0, result.errores)
            self.assertEqual("2024-01-01T00:00:00Z", result.manifest_rows[0]["capturado_en_utc"])
            self.assertEqual("reutilizado_existente_valido", result.manifest_rows[0]["motivo"])
            self.assertEqual(1, len(session.requests))

    def test_duplicate_pdf_sha_is_omitted_not_counted(self):
        pdf_bytes = make_pdf_bytes(pages=1, title="duplicate")
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession(
                [listing_response(HTML_TWO_ITEMS), pdf_response(pdf_bytes), pdf_response(pdf_bytes)]
            )
            result = scraping.run_prensa_source(
                session=session,
                output_dir=Path(tmpdir),
                target_meta=2,
                previous_successes={},
            )
            self.assertEqual(1, result.exitos_pdf)
            self.assertEqual(1, result.omitidos)
            estados = [row["estado"] for row in result.manifest_rows]
            self.assertIn("descargado_pdf", estados)
            self.assertIn("omitido", estados)

    def test_listing_403_stops_publication_as_restricted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = FakeSession(
                [
                    FakeResponse(
                        status_code=403,
                        headers={"Content-Type": "text/plain; charset=utf-8", "Retry-After": "600"},
                        content=b"Forbidden",
                    )
                ]
            )
            result = scraping.run_prensa_source(
                session=session,
                output_dir=Path(tmpdir),
                target_meta=3,
                previous_successes={},
            )
            self.assertEqual("contenido_restringido", result.estado_acceso)
            self.assertIn("403", result.motivo_detencion)
            self.assertIn("Retry-After=600", result.motivo_detencion)
            self.assertEqual("prensa_1002062_preflight", result.manifest_rows[0]["id"])
            self.assertEqual(1, len(session.requests))
            self.assertEqual(3, result.faltante)

    def test_empty_listing_raises_for_rediagnosis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = FakeSession([listing_response("<html><body>sin enlaces</body></html>")])
            with self.assertRaises(RuntimeError) as ctx:
                scraping.run_prensa_source(
                    session=session,
                    output_dir=Path(tmpdir),
                    target_meta=3,
                    previous_successes={},
                )
            self.assertIn("no contiene enlaces PDF", str(ctx.exception))

    def test_year_pages_are_followed_until_target(self):
        pdfs = [make_pdf_bytes(pages=1, title=f"y{i}") for i in range(3)]
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession(
                [
                    listing_response(HTML_YEAR_1730),
                    listing_response(HTML_YEAR_1732),
                    pdf_response(pdfs[0]),
                    pdf_response(pdfs[1]),
                    pdf_response(pdfs[2]),
                ]
            )
            result = scraping.run_prensa_source(
                session=session,
                output_dir=Path(tmpdir),
                target_meta=10,
                previous_successes={},
                publicacion="1006238",
            )
            self.assertEqual(3, result.exitos_pdf)
            self.assertEqual(0, result.errores)
            self.assertIn("2 páginas de año consultadas", result.motivo_detencion)
            self.assertEqual(
                ["prensa_8476519", "prensa_8476520", "prensa_8476521"],
                [row["id"] for row in result.manifest_rows],
            )
            self.assertTrue((Path(tmpdir) / "prensa" / "prensa_listado_numeros_por_mes_1006238_1732.html").exists())
            self.assertEqual(5, len(session.requests))

    def test_year_pages_stop_lazily_when_target_reached(self):
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession([listing_response(HTML_YEAR_1730), pdf_response(make_pdf_bytes())])
            result = scraping.run_prensa_source(
                session=session,
                output_dir=Path(tmpdir),
                target_meta=1,
                previous_successes={},
                publicacion="1006238",
            )
            self.assertEqual(1, result.exitos_pdf)
            self.assertEqual(1, result.omitidos)
            self.assertEqual("meta alcanzada", result.motivo_detencion)
            self.assertEqual(2, len(session.requests))

    def test_year_page_403_keeps_collected_items_and_records_restriction(self):
        pdfs = [make_pdf_bytes(pages=1, title=f"r{i}") for i in range(2)]
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession(
                [
                    listing_response(HTML_YEAR_1730),
                    FakeResponse(
                        status_code=429,
                        headers={"Content-Type": "text/plain; charset=utf-8", "Retry-After": "120"},
                        content=b"Too Many Requests",
                    ),
                    pdf_response(pdfs[0]),
                    pdf_response(pdfs[1]),
                ]
            )
            result = scraping.run_prensa_source(
                session=session,
                output_dir=Path(tmpdir),
                target_meta=10,
                previous_successes={},
                publicacion="1006238",
            )
            self.assertEqual(2, result.exitos_pdf)
            self.assertEqual(1, result.errores)
            self.assertEqual("prensa_1006238_anyo_1732", result.manifest_rows[0]["id"])
            self.assertEqual("contenido_restringido", result.manifest_rows[0]["estado"])
            self.assertIn("página(s) de año con acceso restringido", result.motivo_detencion)
            self.assertIn("429", result.manifest_rows[0]["motivo"])


class ManifestTests(unittest.TestCase):
    def test_write_manifest_preserves_existing_rows_and_updates_by_identity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir)
            first = scraping.build_manifest_row(
                id_="prensa_2000857258",
                url_origen=LISTING_URL,
                url_material="https://prensahistorica.mcu.es/es/catalogo_imagenes/grupo.do?path=2000857258",
                tipo_material="pdf",
                titulo="Año I Número 1 - 16 Marzo 1893",
                fecha_publicacion="16 Marzo 1893",
                ruta_pdf="prensa/pdf/prensa_2000857258.pdf",
                sha256_value="sha-one",
                estado="descargado_pdf",
                motivo="descargado_nuevo",
            )
            second = scraping.build_manifest_row(
                id_="prensa_2000857259",
                url_origen=LISTING_URL,
                url_material="https://prensahistorica.mcu.es/es/catalogo_imagenes/grupo.do?path=2000857259",
                tipo_material="pdf",
                titulo="Año I Número 2 - 23 Marzo 1893",
                fecha_publicacion="23 Marzo 1893",
                ruta_pdf="prensa/pdf/prensa_2000857259.pdf",
                sha256_value="sha-two",
                estado="descargado_pdf",
                motivo="descargado_nuevo",
            )
            scraping.write_manifest([first], output)
            scraping.write_manifest([second], output)
            with (output / "manifest.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(2, len(rows))
            self.assertEqual({"prensa_2000857258", "prensa_2000857259"}, {row["id"] for row in rows})

    def test_manifest_identity_does_not_change_with_discovery_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir)
            original = scraping.build_manifest_row(
                id_="prensa_1",
                url_origen="https://example.test/pdf",
                url_material="https://example.test/material",
                estado="descargado_pdf",
            )
            updated = dict(original, url_origen="https://example.test/listado")
            scraping.write_manifest([original], output)
            scraping.write_manifest([updated], output)
            with (output / "manifest.csv").open(encoding="utf-8", newline="") as handle:
                records = list(csv.DictReader(handle))
            self.assertEqual(1, len(records))
            self.assertEqual(updated["url_origen"], records[0]["url_origen"])

    def test_load_previous_successes_keeps_only_downloads_with_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir)
            rows = [
                scraping.build_manifest_row(
                    id_="prensa_a", url_origen=LISTING_URL, estado="descargado_pdf", sha256_value="sha-a"
                ),
                scraping.build_manifest_row(id_="prensa_b", url_origen=LISTING_URL, estado="error"),
                scraping.build_manifest_row(
                    id_="prensa_c", url_origen=LISTING_URL, estado="descargado_pdf", sha256_value=""
                ),
            ]
            scraping.write_manifest(rows, output)
            successes = scraping.load_previous_successes(output)
            self.assertEqual({("prensa", "prensa_a")}, set(successes))

    def test_rerun_drops_stale_page_rows_of_touched_publication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir)
            stale = scraping.build_manifest_row(
                id_="prensa_1006238_error", url_origen=LISTING_URL, estado="error", motivo="fallo transitorio"
            )
            other_pub_error = scraping.build_manifest_row(
                id_="prensa_9999999_error", url_origen=LISTING_URL, estado="error", motivo="otra publicación"
            )
            material = scraping.build_manifest_row(
                id_="prensa_8476519", url_origen=LISTING_URL, estado="descargado_pdf", sha256_value="sha-x"
            )
            scraping.write_manifest([stale, other_pub_error, material], output)
            scraping.write_manifest([material], output, publicaciones=["1006238"])
            with (output / "manifest.csv").open(encoding="utf-8", newline="") as handle:
                ids = {row["id"] for row in csv.DictReader(handle)}
            self.assertEqual({"prensa_9999999_error", "prensa_8476519"}, ids)


class PipelineTests(unittest.TestCase):
    def test_pipeline_runs_multiple_publicaciones_on_one_manifest(self):
        first = make_pdf_bytes(pages=1, title="one")
        other = make_pdf_bytes(pages=1, title="other")
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession(
                [
                    listing_response(HTML_ONE_ITEM),
                    pdf_response(first),
                    listing_response(HTML_OTHER_PUB_ONE_ITEM),
                    pdf_response(other),
                ]
            )
            manifest_rows, summary_rows = scraping.run_pipeline(
                1, Path(tmpdir), ["1002062", "1000798295"], session=session
            )
            self.assertEqual(2, len(summary_rows))
            self.assertEqual("abierto", summary_rows[0]["estado_acceso"])
            self.assertEqual("abierto", summary_rows[1]["estado_acceso"])
            self.assertEqual(
                {"prensa_2000857258", "prensa_3000000001"},
                {row["id"] for row in manifest_rows},
            )
            self.assertTrue((Path(tmpdir) / "prensa" / "pdf" / "prensa_3000000001.pdf").exists())

    def test_restricted_publicacion_does_not_stop_the_rest(self):
        first = make_pdf_bytes(pages=1, title="one")
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(scraping.time, "sleep", return_value=None):
            session = FakeSession(
                [
                    FakeResponse(
                        status_code=403,
                        headers={"Content-Type": "text/plain; charset=utf-8"},
                        content=b"Forbidden",
                    ),
                    listing_response(HTML_OTHER_PUB_ONE_ITEM),
                    pdf_response(first),
                ]
            )
            manifest_rows, summary_rows = scraping.run_pipeline(
                1, Path(tmpdir), ["1002062", "1000798295"], session=session
            )
            self.assertEqual(2, len(summary_rows))
            self.assertEqual("contenido_restringido", summary_rows[0]["estado_acceso"])
            self.assertEqual("abierto", summary_rows[1]["estado_acceso"])
            self.assertEqual("prensa_1002062_preflight", manifest_rows[0]["id"])
            self.assertEqual("prensa_3000000001", manifest_rows[1]["id"])

    def test_pipeline_reports_errors_without_crashing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = FakeSession([])
            with mock.patch.object(
                scraping,
                "run_prensa_source",
                side_effect=RuntimeError("boom"),
            ):
                manifest_rows, summary_rows = scraping.run_pipeline(
                    3, Path(tmpdir), ["1002062"], session=session
                )
            self.assertEqual(1, len(summary_rows))
            self.assertEqual("error", summary_rows[0]["estado_acceso"])
            self.assertIn("boom", summary_rows[0]["motivo_detencion"])
            self.assertEqual("prensa_1002062_error", manifest_rows[0]["id"])

    def test_pipeline_closes_own_session_but_not_injected_one(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            injected = FakeSession([listing_response(HTML_ONE_ITEM), pdf_response(make_pdf_bytes())])
            with mock.patch.object(scraping.time, "sleep", return_value=None):
                scraping.run_pipeline(1, Path(tmpdir), session=injected)
            self.assertFalse(injected.closed)

            created = FakeSession([listing_response(HTML_ONE_ITEM), pdf_response(make_pdf_bytes())])
            with (
                mock.patch.object(scraping, "make_http_session", return_value=created),
                mock.patch.object(scraping.time, "sleep", return_value=None),
            ):
                scraping.run_pipeline(1, Path(tmpdir))
            self.assertTrue(created.closed)


class CliTests(unittest.TestCase):
    def test_main_rejects_invalid_n_before_any_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(scraping, "make_http_session") as factory:
                code = scraping.main(["--n", "0", "--salida", tmpdir])
            self.assertEqual(2, code)
            factory.assert_not_called()
            self.assertFalse((Path(tmpdir) / "manifest.csv").exists())

    def test_main_rejects_invalid_pausa_before_any_request(self):
        for bad in ("-1", "nan", "inf"):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as tmpdir:
                with mock.patch.object(scraping, "make_http_session") as factory:
                    code = scraping.main(["--pausa", bad, "--salida", tmpdir])
                self.assertEqual(2, code)
                factory.assert_not_called()
                self.assertFalse((Path(tmpdir) / "manifest.csv").exists())

    def test_main_accepts_large_targets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = FakeSession(
                [listing_response(HTML_ONE_ITEM), pdf_response(make_pdf_bytes())]
            )
            with (
                mock.patch.object(scraping, "make_http_session", return_value=session),
                mock.patch.object(scraping.time, "sleep", return_value=None),
            ):
                code = scraping.main(["--n", "5000", "--salida", tmpdir])
            self.assertEqual(0, code)
            self.assertEqual(1, len(session.requests) - 1)  # listado + 1 PDF disponible

    def test_main_runs_and_writes_outputs(self):
        pdf_bytes = make_pdf_bytes(pages=1, title="cli")
        with tempfile.TemporaryDirectory() as tmpdir:
            session = FakeSession([listing_response(HTML_ONE_ITEM), pdf_response(pdf_bytes)])
            with (
                mock.patch.object(scraping, "make_http_session", return_value=session),
                mock.patch.object(scraping.time, "sleep", return_value=None),
            ):
                code = scraping.main(["--n", "1", "--salida", tmpdir])
            self.assertEqual(0, code)
            with (Path(tmpdir) / "manifest.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(1, len(rows))
            self.assertEqual("descargado_pdf", rows[0]["estado"])
            self.assertEqual(scraping.sha256_bytes(pdf_bytes), rows[0]["sha256"])
            self.assertTrue((Path(tmpdir) / "resumen.csv").exists())
            self.assertTrue((Path(tmpdir) / "prensa" / "pdf" / "prensa_2000857258.pdf").exists())

    def test_main_accepts_publicacion_list(self):
        first = make_pdf_bytes(pages=1, title="a")
        other = make_pdf_bytes(pages=1, title="b")
        with tempfile.TemporaryDirectory() as tmpdir:
            session = FakeSession(
                [
                    listing_response(HTML_ONE_ITEM),
                    pdf_response(first),
                    listing_response(HTML_OTHER_PUB_ONE_ITEM),
                    pdf_response(other),
                ]
            )
            with (
                mock.patch.object(scraping, "make_http_session", return_value=session),
                mock.patch.object(scraping.time, "sleep", return_value=None),
            ):
                code = scraping.main(
                    ["--n", "1", "--publicacion", "1002062,1000798295", "--salida", tmpdir]
                )
            self.assertEqual(0, code)
            with (Path(tmpdir) / "resumen.csv").open(encoding="utf-8", newline="") as handle:
                summary = list(csv.DictReader(handle))
            self.assertEqual(2, len(summary))

    def test_main_clears_stale_error_row_after_successful_rerun(self):
        pdfs = [make_pdf_bytes(pages=1, title=f"s{i}") for i in range(2)]
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir)
            scraping.write_manifest(
                [
                    scraping.build_manifest_row(
                        id_="prensa_1006238_error",
                        url_origen=scraping.build_listing_url("1006238"),
                        estado="error",
                        motivo="fallo transitorio",
                    )
                ],
                output,
            )
            session = FakeSession(
                [
                    listing_response(HTML_YEAR_1730),
                    pdf_response(pdfs[0]),
                    pdf_response(pdfs[1]),
                ]
            )
            with (
                mock.patch.object(scraping, "make_http_session", return_value=session),
                mock.patch.object(scraping.time, "sleep", return_value=None),
            ):
                code = scraping.main(["--n", "2", "--publicacion", "1006238", "--salida", tmpdir])
            self.assertEqual(0, code)
            with (output / "manifest.csv").open(encoding="utf-8", newline="") as handle:
                ids = {row["id"] for row in csv.DictReader(handle)}
            self.assertNotIn("prensa_1006238_error", ids)
            self.assertEqual({"prensa_8476519", "prensa_8476520"}, ids)

    def test_main_rejects_non_numeric_publicacion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(scraping, "make_http_session") as factory:
                code = scraping.main(["--publicacion", "no-numero", "--salida", tmpdir])
            self.assertEqual(2, code)
            factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
