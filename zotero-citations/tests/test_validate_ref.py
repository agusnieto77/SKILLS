import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate_ref as vr  # noqa: E402
import zotlib  # noqa: E402


def rec(source, title="Artificial intelligence and illusions of understanding in scientific research",
        authors=("Messeri", "Crockett"), year="2024", **extra):
    return vr._record(source, title=title, authors=list(authors), year=year, **extra)


EXPECTED = {"title": "Artificial intelligence and illusions of understanding in scientific research", "author": "Messeri", "year": "2024"}


class Verdicts(unittest.TestCase):
    def test_two_agreeing_sources_validate(self):
        self.assertEqual(vr.verdict([rec("crossref"), rec("openalex")], EXPECTED, [])["verdict"], "validated")

    def test_one_source_is_not_enough(self):
        result = vr.verdict([rec("crossref"), None], EXPECTED, ["openalex: timeout"])
        self.assertEqual(result["verdict"], "single-source")
        self.assertEqual(result["unavailable"], ["openalex: timeout"])

    def test_sources_disagreeing_is_conflict(self):
        result = vr.verdict([rec("crossref"), rec("openalex", title="A completely different paper about fisheries")], EXPECTED, [])
        self.assertEqual(result["verdict"], "conflict")

    def test_manuscript_differs_from_consensus(self):
        result = vr.verdict([rec("crossref"), rec("openalex")], {**EXPECTED, "author": "Crockett", "year": "2022"}, [])
        self.assertEqual(result["verdict"], "mismatch")
        self.assertEqual([d["field"] for d in result["diffs_vs_manuscript"]], ["first_author", "year"])

    def test_online_first_year_is_tolerated(self):
        crossref = rec("crossref", year="2024", online_year="2023")
        openalex = rec("openalex", year="2023")
        result = vr.verdict([crossref, openalex], {**EXPECTED, "year": "2023"}, [])
        self.assertEqual(result["verdict"], "validated")

    def test_compound_surnames_agree(self):
        a = rec("openlibrary", title="Breve historia", authors=["Halperin Donghi"], year="1972")
        b = rec("citoid", title="Breve historia", authors=["Donghi"], year="1972")
        self.assertTrue(vr.agree(a, b)["agree"])

    def test_nothing_found(self):
        self.assertEqual(vr.verdict([None, None], EXPECTED, [])["verdict"], "not-found")


class Integrity(unittest.TestCase):
    CROSSREF_UPDATED_BY = [
        {"DOI": "10.1016/s0140-6736(04)15715-2", "type": "correction", "label": "Correction", "source": "retraction-watch",
         "updated": {"date-parts": [[2004, 3, 6]]}},
        {"DOI": "10.1016/s0140-6736(10)60175-4", "type": "retraction", "label": "Retraction", "source": "retraction-watch",
         "updated": {"date-parts": [[2010, 2, 6]]}},
    ]

    def test_retraction_outranks_correction(self):
        notices = vr._notices(self.CROSSREF_UPDATED_BY)
        self.assertEqual(notices[1], {"type": "retraction", "label": "Retraction", "notice_doi": "10.1016/s0140-6736(10)60175-4",
                                      "source": "retraction-watch", "date": "2010-2-6"})
        self.assertEqual(vr.integrity_status(notices, None), "retracted")

    def test_status_vocabulary(self):
        def status(kind, retracted=None):
            return vr.integrity_status([{"type": kind}] if kind else [], retracted)
        self.assertEqual(status("withdrawal"), "retracted")
        self.assertEqual(status("expression_of_concern"), "expression-of-concern")
        self.assertEqual(status("erratum"), "corrected")
        self.assertEqual(status("new_version"), "new-version")
        self.assertEqual(status(None), "clean")
        self.assertEqual(status(None, retracted=True), "retracted")  # OpenAlex flag alone is enough

    def test_integrity_is_unknown_without_crossref_or_openalex(self):
        self.assertEqual(vr.integrity_of([rec("datacite")])["status"], "unknown")
        crossref = rec("crossref", notices=vr._notices(self.CROSSREF_UPDATED_BY))
        self.assertEqual(vr.integrity_of([crossref, rec("openalex")])["status"], "retracted")

    def test_dois_collected_from_audit_and_match_outputs(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            audit, match = Path(tmp) / "a.json", Path(tmp) / "m.json"
            audit.write_text(json.dumps({"references": [{"index": 0, "doi": "10.1234/aaaa"}, {"index": 1, "doi": None}]}))
            match.write_text(json.dumps({"matches": [{"index": 0, "best": {"DOI": "10.1234/AAAA"}},
                                                     {"index": 1, "best": {"DOI": "https://doi.org/10.5678/bbbb"}},
                                                     {"index": 2, "best": None}]}))
            self.assertEqual(vr._dois_from_files([str(audit), str(match)]), {"10.1234/aaaa": [0], "10.5678/bbbb": [1]})


class Identifiers(unittest.TestCase):
    def test_doi_normalization(self):
        self.assertEqual(zotlib.normalize_doi("https://doi.org/10.1038/S41586-024-07146-0."), "10.1038/s41586-024-07146-0")
        self.assertEqual(zotlib.normalize_doi("doi:10.1126/science.adi1778)"), "10.1126/science.adi1778")
        self.assertIsNone(zotlib.normalize_doi("not a doi"))

    def test_isbn_checksums(self):
        self.assertEqual(zotlib.normalize_isbn("0-201-89683-4"), "9780201896831")
        self.assertEqual(zotlib.normalize_isbn("978-0-201-89683-1"), "9780201896831")
        self.assertIsNone(zotlib.normalize_isbn("978-0-201-89683-2"))
        self.assertEqual(zotlib.isbns_in("9780201896831 9780201896848"), {"9780201896831", "9780201896848"})

    def test_family_name_parsing(self):
        self.assertEqual(vr._family("Julieta Quirós"), "Quirós")
        self.assertEqual(vr._family("Quirós, Julieta"), "Quirós")


class FakeResponse:
    def __init__(self, body: str, status: int = 200):
        self.status, self.body = status, body.encode("utf-8")


LOC_MODS = """<zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/"><zs:records><zs:record><zs:recordData>
<mods xmlns="http://www.loc.gov/mods/v3"><titleInfo><title>Distant reading</title></titleInfo>
<titleInfo type="uniform"><title>Essays. Selections</title></titleInfo>
<name type="personal" usage="primary"><namePart>Moretti, Franco,</namePart><namePart type="date">1950-</namePart></name>
<originInfo><dateIssued encoding="marc">2013</dateIssued></originInfo>
<originInfo eventType="publication"><agent><namePart>Verso,</namePart></agent><dateIssued>2013.</dateIssued></originInfo>
<identifier type="isbn">9781781680841</identifier><identifier type="lccn">2012047274</identifier></mods>
</zs:recordData></zs:record></zs:records></zs:searchRetrieveResponse>"""
BNE_DC = """<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"><records><record><recordData>
<srw_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:srw_dc="info:srw/schema/1/dc-schema">
<dc:title>Cien años de soledad [Texto impreso]</dc:title><dc:contributor>García Márquez, Gabriel 1927-2014</dc:contributor>
<dc:publisher>Buenos Aires</dc:publisher><dc:publisher>Sudamericana</dc:publisher><dc:date>cop. 1967</dc:date>
<dc:identifier>alma:34BNE_INST/bibs/991</dc:identifier></srw_dc:dc></recordData></record></records></searchRetrieveResponse>"""
DSPACE7 = {"_embedded": {"searchResult": {"_embedded": {"objects": [{"_embedded": {"indexableObject": {
    "name": "Trabajadores de salud en conflicto : las protestas en el área de salud pública de Chaco entre 2017 y 2021",
    "handle": "123456789/53956", "metadata": {
        "dc.contributor.author": [{"value": "Sujatt, Julio Andrés"}], "dc.date.issued": [{"value": "2023-05-18"}],
        "dc.type": [{"value": "Ponencia"}]}}}}]}}}}
LAREFERENCIA = {"records": [{"title": "Trabajadores de salud en conflicto: las protestas en el área de salud pública de Chaco",
                             "authors": {"primary": {"Sujatt, Julio Andrés": {"role": ["author"]}}},
                             "publicationDates": ["2023"], "institutions": ["Universidad Nacional del Nordeste"],
                             "urls": [{"url": "http://repositorio.unne.edu.ar/handle/123456789/53956"}], "id": "AR_1"}]}


class CatalogParsing(unittest.TestCase):
    def test_library_of_congress_mods(self):
        with mock.patch.object(vr, "request", return_value=FakeResponse(LOC_MODS)):
            [r] = vr.loc_search("Distant reading", "Moretti", "2013")
        self.assertEqual((r["title"], r["authors"], r["year"], r["publisher"]), ("Distant reading", ["Moretti"], "2013", "Verso,"))
        self.assertEqual((r["isbn"], r["url"]), (["9781781680841"], "https://lccn.loc.gov/2012047274"))

    def test_bne_dublin_core_strips_material_designation_and_dates(self):
        with mock.patch.object(vr, "request", return_value=FakeResponse(BNE_DC)):
            [r] = vr.bne_search("Cien años de soledad", "García Márquez", "1967")
        self.assertEqual((r["title"], r["authors"], r["year"]), ("Cien años de soledad", ["García Márquez"], "1967"))
        self.assertEqual(r["publisher"], "Buenos Aires, Sudamericana")

    def test_dspace7_and_lareferencia(self):
        with mock.patch.object(vr, "get_json", return_value=DSPACE7):
            [repo] = vr.dspace_search("unne", "d7:https://repositorio.unne.edu.ar", "Trabajadores de salud")
        self.assertEqual((repo["source"], repo["authors"], repo["year"]), ("repo:unne", ["Sujatt"], "2023"))
        self.assertEqual(repo["url"], "https://repositorio.unne.edu.ar/handle/123456789/53956")
        with mock.patch.object(vr, "get_json", return_value=LAREFERENCIA):
            [lr] = vr.lareferencia_search("Trabajadores de salud", None, None)
        self.assertEqual((lr["authors"], lr["year"], lr["publisher"]), (["Sujatt"], "2023", "Universidad Nacional del Nordeste"))

    def test_solr_syntax_is_neutralized(self):
        self.assertEqual(vr._solr('Trabajadores: "las protestas" (2017-2021)'), "Trabajadores las protestas 2017 2021")


class WorkValidation(unittest.TestCase):
    TITLE = "Trabajadores de salud en conflicto: las protestas en el área de salud pública de Chaco entre 2017 y 2021"

    def run_work(self, results: dict, **kw):
        sources = {name: (lambda *a, found=found: [dict(r) for r in found]) for name, found in results.items()}
        with mock.patch.object(vr, "work_sources", return_value=sources):
            return vr.validate_work(self.TITLE, "Sujatt", kw.get("year", "2023"))

    def test_repository_and_lareferencia_are_one_source(self):
        hit = {"title": self.TITLE, "authors": ["Sujatt"], "year": "2023"}
        result = self.run_work({"repo:unne": [vr._record("repo:unne", **hit)],
                                "lareferencia": [vr._record("lareferencia", **hit)], "loc": []})
        self.assertEqual(result["verdict"], "single-source")
        self.assertEqual(list(result["groups"]), ["repositorios"])

    def test_two_independent_catalogs_validate_and_misses_become_leads(self):
        hit = {"title": self.TITLE, "authors": ["Sujatt"], "year": "2023"}
        other = vr._record("crossref", title="Trabajadores de la salud en la Argentina", authors=["Pérez"], year="2023")
        result = self.run_work({"repo:unne": [vr._record("repo:unne", **hit)], "bne": [vr._record("bne", **hit)],
                                "crossref": [other]})
        self.assertEqual((result["verdict"], set(result["groups"])), ("validated", {"repositorios", "bne"}))
        self.assertEqual([lead["source"] for lead in result["leads"]], ["crossref"])
        self.assertEqual(self.run_work({"repo:unne": [vr._record("repo:unne", **hit)], "bne": [vr._record("bne", **hit)]},
                                       year="2021")["verdict"], "mismatch")

    def test_failing_source_is_unavailable_not_fatal(self):
        def down(*_):
            raise ConnectionError("timeout")
        with mock.patch.object(vr, "work_sources", return_value={"loc": down}):
            result = vr.validate_work(self.TITLE, "Sujatt", "2023")
        self.assertEqual((result["verdict"], result["unavailable"]), ("not-found", ["loc: timeout"]))

    def test_record_page_on_a_known_repository_joins_that_group(self):
        self.assertEqual(vr.independence_group("sitio:repositorio.unne.edu.ar"), "repositorios")
        self.assertEqual(vr.independence_group("sitio:www.scielo.org.ar"), "sitio:www.scielo.org.ar")


if __name__ == "__main__":
    unittest.main()
