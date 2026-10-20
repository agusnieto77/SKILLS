import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
