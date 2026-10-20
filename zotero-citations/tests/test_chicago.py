import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import cite_audit  # noqa: E402
import style_chicago as sch  # noqa: E402
from test_cite_audit import _docx  # noqa: E402

FIX = HERE / "fixtures"


def by_rule(report):
    rules = {}
    for f in report["findings"]:
        rules.setdefault(f["rule"], []).append(f["subject"])
    return rules


class Detection(unittest.TestCase):
    def test_each_fixture_is_detected(self):
        expected = {"manuscrito.md": "apa", "chicago-notas.md": "chicago-notes",
                    "chicago-autor-fecha.md": "chicago-author-date", "chicago-notas-sin-bibliografia.md": "chicago-notes"}
        for name, style in expected.items():
            self.assertEqual(cite_audit.extract(FIX / name)["style"], style, name)

    def test_generic_chicago_request_picks_the_variant_or_defaults_to_notes(self):
        self.assertEqual(cite_audit.extract(FIX / "chicago-autor-fecha.md", "chicago")["style"], "chicago-author-date")
        self.assertEqual(cite_audit.resolve_style("chicago", {"style": None, "signals": {}}), ("chicago-notes", "default"))

    def test_requested_style_wins_but_mismatch_is_reported(self):
        report = cite_audit.audit(FIX / "manuscrito.md", "es", "chicago-author-date")
        self.assertEqual(report["style"], "chicago-author-date")
        self.assertIn("D-STYLE-MISMATCH", by_rule(report))


class NotesAndBibliography(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = cite_audit.audit(FIX / "chicago-notas.md", "es", "chicago")
        cls.rules = by_rule(cls.report)
        cls.cites = cls.report["citations"]

    def test_note_forms_are_parsed_in_document_order(self):
        self.assertEqual([(c["note"], c["kind"]) for c in self.cites], [
            ("1", "note-full"), ("2", "note-short"), ("2", "note-short"), ("3", "note-ibid"), ("4", "note-short"),
            ("5", "note-short"), ("6", "note-short"), ("7", "note-full"), ("8", "note-full"), ("9", "note-author")])
        self.assertEqual(next(c["locator"] for c in self.cites if c["note"] == "6"), "20–22")

    def test_notes_resolve_by_author_and_short_title(self):
        refs = self.report["references"]
        titles = {c["note"] + c["kind"]: refs[c["ref_indexes"][0]]["title"][:20] for c in self.cites if c.get("ref_indexes")}
        self.assertEqual(titles["1note-full"], "Lucha y organización")
        self.assertEqual(titles["6note-short"], "A la conquista de la")

    def test_note_problems(self):
        self.assertIn("C-IBID-AMBIGUOUS", self.rules)  # ibid. after a note citing two works
        self.assertIn("C-IBID", self.rules)
        self.assertEqual(len(self.rules["C-TITLE-MISMATCH"]), 1)
        self.assertTrue(self.rules["C-ORPHAN"][0].startswith("Mirta Zaida Lobato"))
        self.assertTrue(self.rules["C-ETAL-REQUIRED"][0].startswith("Igor Grossmann"))
        self.assertTrue(self.rules["C-AMBIGUOUS"][0].startswith("Acha, 70"))

    def test_bibliography_rules(self):
        wrong = self.rules["R-WRONG-SYSTEM"]
        self.assertEqual([w[:8] for w in wrong], ["Albrieu,", "Messeri,"])
        self.assertIn("R-3EM-DASH", self.rules)
        self.assertNotIn("R-ORDER", self.rules)  # the 3-em dash entry inherits its author
        self.assertIn("R-AUTHORS-LIMIT", self.rules)
        self.assertIn("R-DOI-FORMAT", self.rules)

    def test_quote_and_context_follow_the_note_call(self):
        first = self.cites[0]
        self.assertTrue(first["context"].startswith("La historiografía reciente"))
        self.assertEqual(first["quotes"][0]["text"], "la clase obrera no fue una creación del peronismo")
        self.assertEqual(first["quotes"][0]["locator"], "61")
        self.assertTrue(self.cites[1]["context"].startswith("El sindicato de canillitas"))

    def test_uncited_entries_are_only_informative(self):
        self.assertTrue(all(f["severity"] == "info" for f in self.report["findings"] if f["rule"] == "C-UNCITED"))


class NotesWithoutBibliography(unittest.TestCase):
    def test_full_notes_become_references(self):
        report = cite_audit.audit(FIX / "chicago-notas-sin-bibliografia.md", "es")
        rules = by_rule(report)
        self.assertTrue(report["references_from_notes"])
        self.assertEqual([r["title"][:20] for r in report["references"]], ["Lucha y organización"])
        self.assertTrue(rules["C-FIRST-NOTE-SHORT"][0].startswith("Camarero"))
        self.assertEqual(len(rules["C-REPEATED-FULL"]), 1)
        self.assertEqual([c.get("ref_indexes") for c in report["citations"]], [None, [0], [0], [0]])


class AuthorDate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = cite_audit.audit(FIX / "chicago-autor-fecha.md", "es")
        cls.rules = by_rule(cls.report)

    def test_year_suffixes_and_narrative_resolve(self):
        resolved = {c["raw"]: c.get("ref_indexes") for c in self.report["citations"]}
        self.assertEqual(resolved["(Acha 2015a, 61)"], [0])
        self.assertEqual(resolved["(Acha 2015b)"], [1])
        self.assertEqual(resolved["Albrieu y Palazzo (2020, 33)"], [3])

    def test_apa_habits_are_flagged(self):
        self.assertEqual(self.rules["C-COMMA-EXTRA"], ["Camarero, 2007"])
        self.assertIn("C-AMPERSAND", self.rules)
        self.assertIn("C-LOCATOR-FORMAT", self.rules)
        self.assertIn("C-ETAL-REQUIRED", self.rules)
        self.assertIn("R-AUTHORS-LIMIT", self.rules)

    def test_reference_parsing(self):
        ref = sch.parse_author_date_reference("Acha, Omar, y Nicolás Quiroga. 2015. *Asociaciones y política*. Prometeo.")
        self.assertEqual((ref["authors"], ref["year"], ref["title"]), (["Acha", "Quiroga"], "2015", "Asociaciones y política"))


class Names(unittest.TestCase):
    def test_inverted_name_lists(self):
        self.assertEqual(sch.parse_inverted_names("Acha, Omar, y Nicolás Quiroga")["authors"], ["Acha", "Quiroga"])
        self.assertEqual(sch.parse_inverted_names("Acha, Omar y Nicolás Quiroga")["authors"], ["Acha", "Quiroga"])
        self.assertEqual(sch.parse_inverted_names("Fuente, Alejandro de la, and Ana María del Valle")["authors"],
                         ["Fuente", "del Valle"])
        corporate = sch.parse_inverted_names("Organización Internacional del Trabajo")
        self.assertEqual(corporate["corporate"], "Organización Internacional del Trabajo")
        self.assertTrue(sch.parse_inverted_names("Smith, Ann, Bob Jones, Carl Lee, et al.")["etal"])


class DocxFootnotes(unittest.TestCase):
    def test_word_footnote_calls_anchor_note_citations(self):
        body = """
<w:p><w:r><w:t xml:space="preserve">Acha sostiene que «la clase obrera no fue una creación del peronismo».</w:t></w:r>
<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="1"/></w:r>
<w:r><w:t xml:space="preserve"> Otra oración sin nota.</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Bibliografía</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">Acha, Omar. «Lucha y organización». </w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>Cuadernos del Ciesal</w:t></w:r><w:r><w:t xml:space="preserve">, n.º 14 (2015): 59–81.</w:t></w:r></w:p>"""
        footnote = ('<w:footnote w:id="1"><w:p><w:r><w:footnoteRef/></w:r><w:r><w:t xml:space="preserve"> Acha, </w:t></w:r>'
                    '<w:r><w:t>«Lucha y organización», 61.</w:t></w:r></w:p></w:footnote>')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "notas.docx"
            _docx(path, body, footnote)
            report = cite_audit.audit(path, "es")
        self.assertEqual(report["style"], "chicago-notes")
        cite = report["citations"][0]
        self.assertEqual((cite["note"], cite["kind"], cite["ref_indexes"], cite["locator"]), ("1", "note-short", [0], "61"))
        self.assertEqual(cite["quotes"][0]["text"], "la clase obrera no fue una creación del peronismo")
        self.assertNotIn("Otra oración", cite["context"])


if __name__ == "__main__":
    unittest.main()
