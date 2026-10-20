import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import source_check as sc  # noqa: E402

PAGE_1 = ("Resumen. Mediante la aplicación de técnicas de minería de textos, se desarrolló una metodo-\n"
          "logía para medir el número de conﬂictos sociales relacionados con la explotación de recursos naturales.")
PAGE_2 = ("Los trabajadores portuarios del Paraná organizaron la primera huelga general en 1932, "
          "cuando la crisis redujo los salarios y el gobierno provincial reprimió la protesta en Diamante.")
PAGE_3 = ("Las rentas procedentes de la minería se asocian con el índice de noticias conflictivas, "
          "aunque la relación no permite inferir causalidad entre las variables.")
CONTENT = "\f".join([PAGE_1, PAGE_2, PAGE_3])


def source(**kwargs):
    return sc.SourceText(CONTENT, **kwargs)


class Normalization(unittest.TestCase):
    def test_ligatures_hyphenation_and_quotes(self):
        norm, pos = sc.normalize("con\uFB02icto “obrero” metodo-\nlogía")
        self.assertEqual(norm, 'conflicto "obrero" metodología')
        # Offsets map back to the original text (used for page numbers and excerpts).
        self.assertEqual(len(norm), len(pos))
        self.assertEqual("con\uFB02icto “obrero” metodo-\nlogía"[pos[norm.index("logía")]], "l")


class Quotes(unittest.TestCase):
    def test_exact_across_line_break_hyphen_and_ligature(self):
        result = sc.check_quote(source(), "se desarrolló una metodología para medir el número de conflictos sociales")
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["pdf_page"], 1)

    def test_editorial_omissions_and_insertions(self):
        quote = "los trabajadores portuarios [...] organizaron la primera huelga general en 1932, cuando la crisis [económica] redujo los salarios"
        self.assertEqual(sc.check_quote(source(), quote)["status"], "exact-with-edits")

    def test_altered_wording_is_reported_with_differences(self):
        result = sc.check_quote(source(), "los trabajadores portuarios del Paraná organizaron la primera huelga general en 1934")
        self.assertEqual(result["status"], "near")
        self.assertEqual(result["differences"], [{"manuscript": "1934", "source": "1932"}])

    def test_partially_invented_quote(self):
        quote = ("cuando la crisis redujo los salarios y el gobierno provincial reprimió la protesta en Diamante "
                 "y luego disolvió todos los sindicatos de la provincia durante una década entera")
        result = sc.check_quote(source(), quote)
        self.assertEqual(result["status"], "partial")
        self.assertIn("diamante", result["diverges_after"])

    def test_invented_quote(self):
        self.assertEqual(sc.check_quote(source(), "la minería genera conflictos inevitables en todas las comunidades")["status"],
                         "not-found")


class Pages(unittest.TestCase):
    def test_printed_page_from_annotations(self):
        annotations = [{"text": "huelga general", "pageLabel": "42", "pageIndex": 1}]
        result = sc.check_quote(source(annotations=annotations), "organizaron la primera huelga general en 1932", "p. 42")
        self.assertEqual((result["printed_page"], result["page_status"]), (42, "consistent"))
        wrong = sc.check_quote(source(annotations=annotations), "organizaron la primera huelga general en 1932", "p. 45")
        self.assertEqual(wrong["page_status"], "inconsistent")

    def test_printed_page_from_article_range_with_cover(self):
        self.assertEqual(sc.SourceText(CONTENT, pages_field="29-30", total_pages=3).page_offset, 27)
        self.assertEqual(sc.SourceText(CONTENT, pages_field="29-31", total_pages=3).page_offset, 28)

    def test_without_mapping_only_pdf_page_is_claimed(self):
        result = sc.check_quote(source(), "Las rentas procedentes de la minería se asocian", "p. 3")
        self.assertEqual((result["printed_page"], result["page_status"]), (None, "matches-pdf-page"))
        no_breaks = sc.check_quote(sc.SourceText(CONTENT.replace("\f", "\n")), "Las rentas procedentes de la minería", "p. 3")
        self.assertEqual(no_breaks["page_status"], "unverifiable")


class VerbatimAndPassages(unittest.TestCase):
    def test_unquoted_copy_is_detected_but_quoted_text_is_not(self):
        claim = sc.strip_citation_and_quotes(
            "Según el autor, la crisis redujo los salarios y el gobierno provincial reprimió la protesta (Pérez, 2001). "
            "«los trabajadores portuarios del Paraná organizaron la primera huelga»")
        runs = sc.find_verbatim(source(), claim)
        self.assertEqual(len(runs), 1)
        self.assertTrue(runs[0]["phrase"].startswith("la crisis redujo los salarios"))
        self.assertEqual(runs[0]["pdf_page"], 2)

    def test_function_word_runs_are_ignored(self):
        text = sc.SourceText("y de la que en el de la que y de la que en el")
        self.assertEqual(sc.find_verbatim(text, "y de la que en el de la que"), [])

    def test_passages_rank_relevant_page_first(self):
        passages = sc.rank_passages(source(), "rentas mineras y noticias conflictivas", k=2)
        self.assertEqual(passages[0]["pdf_page"], 3)


class FakeProvider:
    name = "test"

    def __init__(self, sources):
        self.sources = sources

    def load(self, key):
        return self.sources.get(key, (None, {"status": "not-indexed"}))


class CheckFlow(unittest.TestCase):
    def test_resolution_statuses_and_counts(self):
        audit = {"summary": {"language": "es"}, "citations": [
            {"raw": "(Pérez, 2001)", "paragraph": 0, "origin": "body", "ref_indexes": [0], "authors": ["Pérez"],
             "context": "La huelga de 1932 fue reprimida por el gobierno provincial en Diamante (Pérez, 2001).",
             "quotes": [{"text": "organizaron la primera huelga general en 1932", "block": False, "locator": None}]},
            {"raw": "(Gómez, 1990)", "paragraph": 1, "origin": "body", "ref_indexes": [1], "authors": ["Gómez"],
             "context": "x", "quotes": []},
            {"raw": "(Ruiz, 1980)", "paragraph": 2, "origin": "body", "ref_indexes": [2], "authors": ["Ruiz"],
             "context": "x", "quotes": []},
            {"raw": "(Nadie, 1970)", "paragraph": 3, "origin": "body", "context": "x", "quotes": []},
        ]}
        matches = {"matches": [
            {"index": 0, "status": "strong", "best": {"key": "AAAA1111"}},
            {"index": 1, "status": "exact-doi", "best": {"key": "BBBB2222"}},
            {"index": 2, "status": "weak", "best": {"key": "CCCC3333"}},
        ]}
        provider = FakeProvider({"AAAA1111": (source(), {"status": "ok"})})
        result = sc.check(audit, matches, provider, k=2, passages=True)
        self.assertEqual([r["status"] for r in result["results"]],
                         ["checked", "no-fulltext", "no-zotero-item", "unresolved-citation"])
        first = result["results"][0]
        self.assertEqual(first["quotes"][0]["status"], "exact")
        self.assertTrue(first["needs_judgement"])
        self.assertFalse(first["cross_language"])


if __name__ == "__main__":
    unittest.main()
