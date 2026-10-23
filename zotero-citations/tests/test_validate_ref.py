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

    def test_isbn_catalog_contributors_do_not_create_authorship_conflicts(self):
        with mock.patch.object(vr, "openlibrary_isbn", return_value=rec("openlibrary", authors=["Messeri"])), \
                mock.patch.object(vr, "citoid_isbn", return_value=rec("citoid (WorldCat)", authors=["Messeri", "Editor"])), \
                mock.patch.object(vr, "googlebooks_isbn", return_value=None):
            result = vr.validate_isbn("9780201896831", EXPECTED)
        self.assertEqual(result["verdict"], "validated")
        self.assertEqual(result["agreement"][0]["authorship"]["scope"], "first-author-only")

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

    def test_catalog_and_repository_creator_lists_keep_first_author_semantics(self):
        result = self.run_work({
            "repo:unne": [rec("repo:unne", title=self.TITLE, authors=["Sujatt", "Colaborador"], year="2023")],
            "bne": [rec("bne", title=self.TITLE, authors=["Sujatt", "Editor", "Otro"], year="2023")]})
        self.assertEqual(result["verdict"], "validated")

    def test_failing_source_is_unavailable_not_fatal(self):
        def down(*_):
            raise ConnectionError("timeout")
        with mock.patch.object(vr, "work_sources", return_value={"loc": down}):
            result = vr.validate_work(self.TITLE, "Sujatt", "2023")
        self.assertEqual((result["verdict"], result["unavailable"]), ("not-found", ["loc: timeout"]))

    def test_record_page_on_a_known_repository_joins_that_group(self):
        self.assertEqual(vr.independence_group("sitio:repositorio.unne.edu.ar"), "repositorios")
        self.assertEqual(vr.independence_group("sitio:www.scielo.org.ar"), "sitio:www.scielo.org.ar")


class OrderedAuthorship(unittest.TestCase):
    def test_source_truncation_keeps_literal_metadata_for_visible_authors(self):
        result = rec("crossref", authors=["Atlas", "et al."],
                     author_details=[{"literal": "Atlas"}, {"family": "et al."}])
        self.assertEqual(result["author_details"], [{"literal": "Atlas"}])
        self.assertFalse(result["authors_complete"])

    def test_provided_pmid_is_fetched_even_when_doi_registry_reports_missing(self):
        with mock.patch.object(vr, "registration_agency", return_value=None), \
                mock.patch.object(vr, "pubmed", return_value=rec("pubmed")) as fetch:
            result = vr.validate_doi("10.1234/test", {"pmid": "123"})
        fetch.assert_called_once_with("123")
        self.assertEqual(result["verdict"], "not-found")
        self.assertEqual(result["records"][0]["source"], "pubmed")

    def test_visible_extra_authors_conflict_with_a_complete_shorter_source(self):
        self.assertFalse(vr.agree(rec("crossref", authors=["Messeri"]),
                                 rec("openalex", authors=["Messeri", "Crockett"], authors_complete=False))["agree"])

    def test_null_source_authors_are_incomplete_not_an_adapter_failure(self):
        self.assertFalse(vr._from_crossref({"author": None})["authors_complete"])
        self.assertFalse(vr._from_openalex({"authorships": None})["authors_complete"])
        with mock.patch.object(vr, "get_json", return_value={"data": {"attributes": {"creators": None}}}):
            self.assertFalse(vr.datacite_doi("10.1234/test")["authors_complete"])
        response = mock.Mock(status=200)
        response.json.return_value = {"author": None}
        with mock.patch.object(vr, "request", return_value=response):
            self.assertFalse(vr.csl_negotiation("10.1234/test", "mEDRA")["authors_complete"])

    def test_shared_compound_component_does_not_hide_substitution(self):
        self.assertTrue(vr.compare_expected(rec("crossref", authors=["García Márquez"]),
                                            {"authors": ["García López"]}))

    def test_terminal_etal_marker_is_an_explicit_prefix(self):
        source = rec("crossref", authors=["Messeri", "Crockett"])
        self.assertEqual(vr.compare_expected(source, {"authors": ["Messeri et al."]}), [])
        partial = rec("crossref", authors=["Messeri", "et al."])
        self.assertFalse(partial["authors_complete"])
        self.assertEqual(partial["authors"], ["Messeri"])

    def test_incomplete_first_source_does_not_hide_complete_source_mismatch(self):
        result = vr.verdict([rec("openalex", authors=["Messeri"], authors_complete=False), rec("crossref")],
                            {"authors": ["Messeri", "Inventado"]}, [])
        self.assertEqual(result["diffs_vs_manuscript"][0]["position"], 2)
        self.assertFalse(result["authorship"]["validated"])

    def test_complete_sources_with_no_full_manuscript_never_claim_authorship_validation(self):
        result = vr.verdict([rec("crossref"), rec("openalex")], EXPECTED, [])
        self.assertFalse(result["authorship"]["validated"])
        self.assertEqual(result["authorship"]["manuscript_scope"], "first-author-only")

    def test_doi_pmid_cli_reaches_validator(self):
        with mock.patch.object(sys, "argv", ["validate_ref.py", "doi", "10.1234/test", "--pmid", "123"]), \
                mock.patch.object(vr, "validate_doi", return_value={}) as handler, mock.patch.object(vr, "emit"):
            vr.main()
        self.assertEqual(handler.call_args.args[1]["pmid"], "123")

    def test_invented_second_author_is_a_mismatch(self):
        result = vr.verdict([rec("crossref"), rec("openalex")],
                            {**EXPECTED, "authors": ["Messeri", "Inventado"]}, [])
        self.assertEqual(result["verdict"], "mismatch")
        self.assertEqual(result["diffs_vs_manuscript"][0]["position"], 2)

    def test_reordered_coauthors_conflict_even_with_same_first_and_count(self):
        a = rec("crossref", authors=["Messeri", "Crockett", "Quirós"])
        b = rec("openalex", authors=["Messeri", "Quirós", "Crockett"])
        self.assertFalse(vr.agree(a, b)["agree"])
        self.assertEqual(len(vr.agree(a, b)["authorship"]["diffs"]), 2)

    def test_particles_and_diacritics_match_at_every_position(self):
        a = rec("crossref", authors=["de la Cruz", "García Márquez", "van Beethoven"])
        b = rec("openalex", authors=["Cruz", "Garcia Marquez", "Beethoven"])
        self.assertTrue(vr.agree(a, b)["agree"])
        self.assertEqual(vr._family("Ludwig van Beethoven"), "van Beethoven")

    def test_source_differences_use_source_labels_not_manuscript(self):
        difference = vr.agree(rec("crossref"), rec("openalex", authors=["Messeri", "Inventado"]))["authorship"]["diffs"][0]
        self.assertEqual((difference["source_a"], difference["source_b"]), ("Crockett", "Inventado"))
        self.assertEqual((difference["source_a_kind"], difference["source_b_kind"]), ("person", "person"))
        self.assertNotIn("manuscript", difference)

    def test_structured_etal_preserves_literal_metadata_on_both_sides(self):
        from authorship import compare_authorship

        for left, right, left_details, right_details in [
                (["Atlas", "et al."], ["Atlas", "Smith"],
                 [{"literal": "Atlas"}, {"family": "et al."}], [{"literal": "Atlas"}, {"family": "Smith"}]),
                (["Atlas"], ["Atlas", "et al."],
                 [{"literal": "Atlas"}], [{"literal": "Atlas"}, {"family": "et al."}]),
                (["Atlas et al."], ["Atlas", "Smith"],
                 [{"literal": "Atlas et al."}], [{"literal": "Atlas"}, {"family": "Smith"}])]:
            with self.subTest(left=left, right=right):
                result = compare_authorship(left, right, left_details=left_details, right_details=right_details)
                self.assertEqual(result["diffs"], [])

    def test_separate_etal_preserves_structured_family_and_given_names(self):
        from authorship import _visible_authors, compare_authorship

        names = ["de la Cruz, Ana", "et al."]
        details = [{"family": "de la Cruz", "given": "Ana"}, {"family": "et al."}]
        visible, structured, marker = _visible_authors(names, details)
        self.assertEqual(visible, ["de la Cruz, Ana"])
        self.assertTrue(marker)
        self.assertEqual(structured, [{"family": "de la Cruz", "given": "Ana"}])
        result = compare_authorship(names, ["de la Cruz", "Smith"], left_details=details)
        self.assertEqual(result["diffs"], [])
        self.assertEqual(details[0], {"family": "de la Cruz", "given": "Ana"})

    def test_inline_etal_keeps_clean_structured_names_and_removes_embedded_marker(self):
        from authorship import _visible_authors

        for detail, expected in [
                ({"family": "de la Cruz", "given": "Ana"}, {"family": "de la Cruz", "given": "Ana"}),
                ({"family": "de la Cruz et al.", "given": "Ana"}, {"family": "de la Cruz", "given": "Ana"}),
                ({"literal": "Atlas et al."}, {"literal": "Atlas"})]:
            with self.subTest(detail=detail):
                names = ["Atlas et al."] if "literal" in detail else ["de la Cruz, Ana et al."]
                visible, structured, marker = _visible_authors(names, [detail])
                self.assertEqual(visible, ["Atlas"] if "literal" in detail else ["de la Cruz, Ana"])
                self.assertTrue(marker)
                self.assertEqual(structured, [expected])

    def test_inline_etal_with_missing_structured_name_stays_unidentified(self):
        from authorship import _visible_authors, compare_authorship

        for detail in ({}, {"given": "Ana"}):
            with self.subTest(detail=detail):
                visible, structured, marker = _visible_authors(["Cruz et al."], [detail])
                self.assertEqual(visible, ["Cruz"])
                self.assertTrue(marker)
                self.assertEqual(structured, [{"family": ""}])
                result = compare_authorship(["Cruz et al."], ["Cruz", "Smith"], left_details=[detail])
                self.assertFalse(result["agree"])

    def test_truncation_warning_identifies_right_label(self):
        from authorship import compare_authorship

        for label, target in (("sources", "La fuente"), ("zotero", "Zotero"),
                              ("source_b", "La segunda fuente"), ("catalog", "La lista «catalog»")):
            with self.subTest(label=label):
                result = compare_authorship(["Cruz"], ["Cruz"], truncated=True,
                                            right_complete=False, right_label=label)
                self.assertIn(f"{target} no permite comprobar la truncación declarada de la autoría.", result["warnings"])


    def test_declared_etal_accepts_only_a_proper_ordered_prefix(self):
        source = rec("crossref", authors=["Messeri", "Crockett", "Quirós"])
        self.assertEqual(vr.compare_expected(source, {"authors": ["Messeri", "Crockett"], "etal": True}), [])
        for names in (["Messeri", "Inventado"], ["Crockett", "Messeri"],
                      ["Messeri", "Crockett", "Quirós"]):
            with self.subTest(names=names):
                self.assertTrue(vr.compare_expected(source, {"authors": names, "etal": True}))
        self.assertTrue(vr.compare_expected(source, {"authors": ["Messeri", "Crockett"]}))

    def test_literal_consortium_is_not_a_person_with_the_same_surname(self):
        source = rec("crossref", authors=["Atlas"], author_details=[{"literal": "Atlas"}])
        self.assertTrue(vr.compare_expected(source, {"authors": [{"family": "Atlas"}]}))
        self.assertEqual(vr.compare_expected(source, {"authors": [{"literal": "ATLAS"}]}), [])

    def test_omitted_or_partial_source_authors_are_not_fully_validated(self):
        for partial in (rec("openalex", authors=[]),
                        rec("openalex", authors=["Messeri"], authors_complete=False)):
            with self.subTest(partial=partial):
                result = vr.verdict([rec("crossref"), partial], {**EXPECTED, "authors": ["Messeri", "Crockett"]}, [])
                self.assertEqual(result["verdict"], "single-source")
                self.assertFalse(result["authorship"]["validated"])
                self.assertTrue(result["warnings"])

    def test_partial_source_still_exposes_substituted_visible_author(self):
        partial = rec("openalex", authors=["Messeri", "Inventado"], authors_complete=False)
        self.assertFalse(vr.agree(rec("crossref"), partial)["agree"])

    def test_source_adapters_preserve_order_and_literal_authors(self):
        crossref = vr._from_crossref({"author": [{"family": "de la Cruz"}, {"name": "Atlas Consortium"}]})
        self.assertEqual(crossref["authors"], ["de la Cruz", "Atlas Consortium"])
        self.assertEqual(crossref["author_details"][1], {"literal": "Atlas Consortium"})
        self.assertFalse(vr._from_crossref({})["authors_complete"])
        with mock.patch.object(vr, "get_json", return_value={"data": {"attributes": {
                "creators": [{"familyName": "Quirós"}, {"name": "Atlas", "nameType": "Organizational"}]}}}):
            datacite = vr.datacite_doi("10.1234/test")
        self.assertEqual(datacite["author_details"][1], {"literal": "Atlas"})
        response = mock.Mock(status=200)
        response.json.return_value = {"author": [{"family": "Cruz", "non-dropping-particle": "de la"}, {"literal": "Atlas"}]}
        with mock.patch.object(vr, "request", return_value=response):
            csl = vr.csl_negotiation("10.1234/test", "mEDRA")
        self.assertEqual(csl["authors"], ["de la Cruz", "Atlas"])

    def test_openalex_truncation_and_missing_entries_are_explicit(self):
        result = vr._from_openalex({"authors_count": 3, "authorships": [
            {"author": {"display_name": "Ana de la Cruz"}}, {"author": {"display_name": "Lisa Messeri"}}]})
        self.assertEqual(result["authors"], ["de la Cruz", "Messeri"])
        self.assertFalse(result["authors_complete"])
        self.assertTrue(result["authorship_warnings"])

    def test_cli_full_authors_repeatable_and_legacy_single_author(self):
        for argv, names, legacy in [
                (["--authors", '["Messeri", {"literal": "Atlas"}]', "--etal"], ["Messeri", {"literal": "Atlas"}], False),
                (["--author", "Messeri", "--author", "Crockett"], ["Messeri", "Crockett"], False),
                (["--author", "Messeri"], None, True)]:
            with self.subTest(argv=argv), mock.patch.object(sys, "argv", ["validate_ref.py", "doi", "10.1234/test", *argv]), \
                    mock.patch.object(vr, "validate_doi", return_value={}) as handler, mock.patch.object(vr, "emit"):
                vr.main()
            expected = handler.call_args.args[1]
            self.assertEqual(expected.get("authors"), names)
            self.assertEqual(expected.get("author"), "Messeri" if legacy else None)

    def test_doi_uses_provided_and_discovered_pmid(self):
        for supplied in (True, False):
            with self.subTest(supplied=supplied), \
                    mock.patch.object(vr, "registration_agency", return_value="Crossref"), \
                    mock.patch.object(vr, "crossref_doi", return_value=rec("crossref")), \
                    mock.patch.object(vr, "openalex_doi", return_value=rec("openalex", pmid="123")), \
                    mock.patch.object(vr, "pubmed", return_value=rec("pubmed", doi="10.1234/test")) as fetch:
                vr.validate_doi("10.1234/test", {"pmid": "123"} if supplied else {})
            fetch.assert_called_once_with("123")


PUBMED_SUMMARY = {"result": {"123": {"title": "A study.", "pubdate": "2024", "fulljournalname": "Journal",
    "authors": [{"name": "de la Cruz A"}, {"name": "Atlas Consortium", "authtype": "CollectiveName"}],
    "articleids": [{"idtype": "doi", "value": "10.1234/test"}]}}}
PUBMED_XML = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article>
<ArticleTitle>A <i>study</i></ArticleTitle><Journal><Title>Journal</Title><JournalIssue><PubDate><Year>2024</Year>
</PubDate></JournalIssue></Journal><AuthorList CompleteYN="Y"><Author><LastName>de la Cruz</LastName>
<ForeName>Ana</ForeName></Author><Author><CollectiveName>Atlas Consortium</CollectiveName></Author>
</AuthorList></Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1234/test</ArticleId>
</ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>"""


class PubMedAuthorship(unittest.TestCase):
    def test_invented_pmid_is_not_found_without_unavailable_sources(self):
        for summary in ({"result": {"999": {"error": "Invalid uid"}}}, {"result": {"uids": []}}):
            with self.subTest(summary=summary), mock.patch.object(vr, "get_json", return_value=summary), \
                    mock.patch.object(vr, "request", return_value=FakeResponse("<PubmedArticleSet/>")):
                result = vr.validate_pmid("999", {})
            self.assertEqual(result["verdict"], "not-found")
            self.assertEqual(result["unavailable"], [])
            self.assertEqual(result["records"], [])

    def test_valid_empty_pubmed_responses_return_none_without_unavailable(self):
        with mock.patch.object(vr, "get_json", return_value={"result": {"uids": []}}), \
                mock.patch.object(vr, "request", return_value=FakeResponse("<PubmedArticleSet/>")):
            self.assertIsNone(vr.pubmed("999"))
            result = vr.validate_pmid("999", {})
        self.assertEqual(result["unavailable"], [])

    def test_empty_pubmed_record_without_warnings_returns_none(self):
        record = vr._record("pubmed", pmid="999", authors_complete=False)
        self.assertIsNone(vr._pubmed_result(record, []))

    def test_empty_pubmed_record_error_always_has_a_reason(self):
        record = vr._record("pubmed", pmid="999", authors_complete=False)
        with self.assertRaisesRegex(ConnectionError, r"\S"):
            vr._pubmed_result(record, [""])

    def test_no_metadata_and_failed_efetch_remains_unavailable(self):
        with mock.patch.object(vr, "get_json", side_effect=ConnectionError("summary timeout")), \
                mock.patch.object(vr, "request", side_effect=ConnectionError("fetch timeout")):
            result = vr.validate_pmid("999", {})
        self.assertIn("fetch timeout", result["unavailable"][0])

    def test_esummary_failure_with_empty_efetch_stays_unavailable(self):
        for error in (ConnectionError("summary timeout"), ConnectionError("quota exceeded"), ValueError("invalid JSON")):
            with self.subTest(error=error), mock.patch.object(vr, "get_json", side_effect=error), \
                    mock.patch.object(vr, "request", return_value=FakeResponse("<PubmedArticleSet/>")):
                with self.assertRaisesRegex(ConnectionError, str(error)):
                    vr.pubmed("999")
                result = vr.validate_pmid("999", {})
                self.assertTrue(result["unavailable"])
                self.assertIn(str(error), result["unavailable"][0])

    def test_invalid_esummary_with_empty_efetch_stays_unavailable(self):
        for summary in (None, {}, {"error": "API rate limit exceeded"}, {"result": []}):
            with self.subTest(summary=summary), mock.patch.object(vr, "get_json", return_value=summary), \
                    mock.patch.object(vr, "request", return_value=FakeResponse("<PubmedArticleSet/>")):
                with self.assertRaises(ConnectionError):
                    vr.pubmed("999")

    def test_pmid_command_path_uses_efetch_with_summary_metadata(self):
        with mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                mock.patch.object(vr, "request", return_value=FakeResponse(PUBMED_XML)), \
                mock.patch.object(vr, "crossref_doi", return_value=rec("crossref", title="A study",
                    authors=["de la Cruz", "Atlas Consortium"],
                    author_details=[{"family": "de la Cruz"}, {"literal": "Atlas Consortium"}])):
            result = vr.validate_pmid("123", {"authors": [{"family": "Cruz"}, {"literal": "Atlas Consortium"}]})
        self.assertEqual(result["verdict"], "validated")
        self.assertTrue(result["authorship"]["validated"])

    def test_untrusted_xml_entity_declaration_falls_back_without_expansion(self):
        body = '<!DOCTYPE x [<!ENTITY instruction "untrusted">]><PubmedArticleSet>&instruction;</PubmedArticleSet>'
        with mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                mock.patch.object(vr, "request", return_value=FakeResponse(body)):
            result = vr.pubmed("123")
        self.assertFalse(result["authors_complete"])
        self.assertNotIn("untrusted", result["title"])

    def test_efetch_uses_ordered_people_and_collective_names(self):
        with mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                mock.patch.object(vr, "request", return_value=FakeResponse(PUBMED_XML)) as fetch:
            result = vr.pubmed("123")
        self.assertTrue(result["authors_complete"])
        self.assertEqual(result["authors"], ["de la Cruz", "Atlas Consortium"])
        self.assertEqual(result["author_details"][1], {"literal": "Atlas Consortium"})
        self.assertEqual(result["container"], "Journal")
        self.assertEqual(fetch.call_args.kwargs["params"]["retmode"], "xml")

    def test_efetch_failure_keeps_esummary_with_explicit_warning(self):
        for response in (FakeResponse("<eFetchResult><ERROR>unavailable</ERROR></eFetchResult>"),
                         FakeResponse("<broken"), FakeResponse("", 503), FakeResponse("<PubmedArticleSet/>")):
            with self.subTest(body=response.body), mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                    mock.patch.object(vr, "request", return_value=response):
                result = vr.pubmed("123")
            self.assertEqual(result["title"], "A study")
            self.assertEqual(result["authors"], ["de la Cruz", "Atlas Consortium"])
            self.assertFalse(result["authors_complete"])
            self.assertTrue(result["authorship_warnings"])

    def test_efetch_transport_error_retains_summary(self):
        with mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                mock.patch.object(vr, "request", side_effect=ConnectionError("timeout")):
            result = vr.pubmed("123")
        self.assertFalse(result["authors_complete"])
        self.assertIn("timeout", " ".join(result["authorship_warnings"]))

    def test_efetch_can_recover_when_esummary_is_unavailable(self):
        with mock.patch.object(vr, "get_json", side_effect=ConnectionError("summary timeout")), \
                mock.patch.object(vr, "request", return_value=FakeResponse(PUBMED_XML)):
            result = vr.pubmed("123")
        self.assertEqual((result["title"], result["doi"], result["year"]), ("A study", "10.1234/test", "2024"))
        self.assertTrue(result["authors_complete"])
        self.assertTrue(result["authorship_warnings"])

    def test_incomplete_xml_author_list_cannot_be_fully_validated(self):
        with mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                mock.patch.object(vr, "request", return_value=FakeResponse(PUBMED_XML.replace('CompleteYN="Y"', 'CompleteYN="N"'))):
            result = vr.pubmed("123")
        self.assertFalse(result["authors_complete"])
        self.assertTrue(result["authorship_warnings"])

    def test_mismatched_xml_pmid_does_not_replace_summary_authors(self):
        with mock.patch.object(vr, "get_json", return_value=PUBMED_SUMMARY), \
                mock.patch.object(vr, "request", return_value=FakeResponse(PUBMED_XML.replace(">123<", ">999<"))):
            result = vr.pubmed("123")
        self.assertFalse(result["authors_complete"])
        self.assertTrue(result["authorship_warnings"])


if __name__ == "__main__":
    unittest.main()
