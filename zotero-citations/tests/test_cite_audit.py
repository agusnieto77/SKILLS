import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import cite_audit  # noqa: E402
import citecore  # noqa: E402
import style_apa  # noqa: E402


def rules_for(findings, subject_prefix):
    return {f["rule"] for f in findings if f["subject"].startswith(subject_prefix)}


class SpanishManuscriptAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = cite_audit.audit(HERE / "fixtures" / "manuscrito.md", None)
        cls.findings = cls.report["findings"]

    def test_detects_apa_and_spanish(self):
        self.assertEqual((self.report["style"], self.report["style_source"]), ("apa", "detected"))
        self.assertEqual(self.report["summary"]["language"], "es")

    def test_orphan_and_uncited(self):
        orphans = [f["subject"] for f in self.findings if f["rule"] == "C-ORPHAN"]
        self.assertEqual(orphans, ["Lobato, 2001"])
        uncited = {f["subject"][:10] for f in self.findings if f["rule"] == "C-UNCITED"}
        self.assertEqual(uncited, {"Sin Citar,", "Romero, Lu"})

    def test_resolves_hard_citation_forms(self):
        # Corporate author with [ABBR] reused later, particles, year suffixes, title-first entries.
        flagged = {f["subject"] for f in self.findings if f["rule"] in ("C-ORPHAN", "C-YEAR-MISMATCH", "C-AMBIGUOUS")}
        for ok in ("OIT, 2019", "de la Fuente, 2001", "Camarero, 2007a", "Camarero, 2007b", "[Nota editorial], s. f."):
            self.assertNotIn(ok, flagged)

    def test_author_count_rules(self):
        self.assertIn("C-ETAL-MISUSE", rules_for(self.findings, "Korinek et al."))
        self.assertIn("C-SECOND-AUTHOR", rules_for(self.findings, "Marx, 1947"))
        self.assertIn("C-AUTHOR-COUNT", rules_for(self.findings, "Messeri, Crockett, Pérez"))
        self.assertNotIn("C-ETAL-MISSING", rules_for(self.findings, "Grossmann"))

    def test_year_mismatch_and_secondary(self):
        self.assertIn("C-YEAR-MISMATCH", rules_for(self.findings, "Acha, 2016"))
        self.assertIn("C-SECONDARY", rules_for(self.findings, "Ricoeur, 1970"))

    def test_reference_lint(self):
        self.assertIn("R-DOI-FORMAT", rules_for(self.findings, "Grossmann"))
        self.assertNotIn("R-FINAL-PERIOD", rules_for(self.findings, "Grossmann"))
        self.assertIn("R-PP-ARTICLE", rules_for(self.findings, "Messeri"))
        self.assertIn("R-TITLE-CASE", rules_for(self.findings, "Korinek"))
        self.assertTrue({"R-PLACE", "R-SERIAL-COMMA"} <= rules_for(self.findings, "Marx"))
        self.assertIn("R-RETRIEVED", rules_for(self.findings, "Organización"))
        self.assertIn("R-INITIALS", rules_for(self.findings, "Romero"))
        self.assertIn("R-UNPARSED", rules_for(self.findings, "Halperin"))
        self.assertIn("R-DASH", rules_for(self.findings, "Acha, O."))
        self.assertNotIn("R-ORDER", rules_for(self.findings, "de la Fuente"))

    def test_reference_kinds(self):
        kinds = {r["authors"][0] if r["authors"] else r["title"]: r["kind"] for r in self.report["references"] if r["parsed"]}
        self.assertEqual(kinds["Acha"], "article")
        self.assertEqual(kinds["Korinek"], "chapter")
        self.assertEqual(kinds["Messeri"], "article")
        self.assertEqual(kinds["Camarero"], "article")  # last one wins: 2007b is the article


class ApaRules(unittest.TestCase):
    def test_language_specific_nd_and_connectors(self):
        refs = [style_apa.parse_reference(t) for t in (
            "Alpha, A. (s. f.). *A book*. Press.",
            "Beta, B., y Gamma, C. (2020). *Another book*. Press.",
        )]
        rules = {f["rule"] for f in style_apa.lint(refs, "en", True)}
        self.assertIn("R-ND-LANG", rules)
        self.assertIn("R-CONNECTOR-LANG", rules)

    def test_same_author_year_needs_suffix(self):
        refs = [style_apa.parse_reference(t) for t in (
            "Alpha, A. (2020). *A book*. Press.", "Alpha, A. (2020). *B book*. Press.")]
        self.assertIn("R-SAME-AUTHOR-YEAR", {f["rule"] for f in style_apa.lint(refs, "en", True)})

    def test_chicago_punctuation_in_apa_text(self):
        refs = [{**style_apa.parse_reference("Acha, O. (2015). *Libro*. Prometeo."), "index": 0}]
        cites = citecore.find_author_date_citations(["Según la prensa (Acha 2015, 61) y en (Buenos Aires 1932)."])
        findings, _ = style_apa.crosscheck(cites, refs)
        self.assertEqual({f["rule"] for f in findings}, {"C-COMMA-MISSING", "C-LOCATOR-FORMAT"})


LONG_BLOCK = ("No obstante, estos resultados deben interpretarse con cautela, dado que no se han abordado los problemas "
              "de endogeneidad, y la evidencia obtenida no permite establecer relaciones causales entre las variables "
              "analizadas en ningún sentido ni para ningún país del estudio comparado")


class QuoteExtraction(unittest.TestCase):
    def quotes(self, paragraphs):
        return [(c["raw"], [(q["text"][:25], q["block"], q["locator"]) for q in c["quotes"]])
                for c in citecore.find_author_date_citations(paragraphs)]

    def test_inline_quotes_go_to_the_right_citation(self):
        result = self.quotes([
            "Acha (2015) sostiene que «la clase obrera no fue una creación del peronismo» (p. 61). "
            "Otros dicen que \"la huelga fue un fracaso total del sindicato\" (Lobato, 2001, p. 4)."])
        self.assertEqual(result, [
            ("Acha (2015)", [("la clase obrera no fue un", False, "p. 61")]),
            ("(Lobato, 2001, p. 4)", [("la huelga fue un fracaso ", False, "p. 4")]),
        ])

    def test_short_quoted_terms_are_not_quotes(self):
        result = self.quotes(["El llamado «sindicalismo revolucionario» creció (Camarero, 2007)."])
        self.assertEqual(result[0][1], [])

    def test_block_quote_after_introducing_colon(self):
        result = self.quotes(["Como advierte Acha (2015):", f"{LONG_BLOCK} (p. 29)."])
        self.assertEqual(result, [("Acha (2015)", [("No obstante, estos result", True, "p. 29")])])

    def test_prose_paragraph_ending_in_citation_is_not_a_block_quote(self):
        result = self.quotes([f"{LONG_BLOCK} (Acha, 2015)."])
        self.assertEqual(result[0][1], [])

    def test_markdown_and_word_quote_styles(self):
        self.assertEqual(self.quotes([f"> {LONG_BLOCK} (Acha, 2015, p. 29)."])[0][1][0][1:], (True, "p. 29"))
        styled = citecore.body_text({"text": f"{LONG_BLOCK} (Acha, 2015, p. 29).", "style": "Cita"})
        self.assertEqual(self.quotes([styled])[0][1][0][1:], (True, "p. 29"))

    def test_citations_are_linked_to_their_reference(self):
        report = cite_audit.audit(HERE / "fixtures" / "manuscrito.md", None)
        by_raw = {c["raw"]: c for c in report["citations"]}
        acha = report["references"][by_raw["(Acha, 2015, p. 61)"]["ref_indexes"][0]]
        self.assertEqual((acha["authors"], acha["year"]), (["Acha"], "2015"))
        self.assertNotIn("ref_indexes", by_raw["(Lobato, 2001)"])


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _docx(path: Path, body: str, footnotes: str):
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}"><w:body>{body}</w:body></w:document>"""
    notes = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:footnotes xmlns:w="{W_NS}">
<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>{footnotes}</w:footnotes>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document)
        archive.writestr("word/footnotes.xml", notes)


def _zotero_field_body():
    field = json.dumps({"citationItems": [{"uris": ["http://zotero.org/users/1234567/items/PD3F23HP"]}],
                        "properties": {"plainCitation": "(Acha, 2015)"}})
    half = len(field) // 2
    return f"""
<w:p><w:r><w:t xml:space="preserve">Texto con cita viva </w:t></w:r>
<w:r><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:instrText xml:space="preserve"> ADDIN ZOTERO_ITEM CSL_CITATION {field[:half]}</w:instrText></w:r>
<w:r><w:instrText xml:space="preserve">{field[half:]} </w:instrText></w:r>
<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>(Acha, 2015)</w:t></w:r>
<w:r><w:fldChar w:fldCharType="end"/></w:r><w:r><w:t>.</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Referencias</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">Acha, O. (2015). Lucha y organización. </w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>Cuadernos del Ciesal</w:t></w:r><w:r><w:t xml:space="preserve">, (14), 59–81.</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">Lobato, M. (2001). </w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>La vida en las fábricas</w:t></w:r><w:r><w:t>. Prometeo.</w:t></w:r></w:p>"""


class DocxInput(unittest.TestCase):
    def test_docx_fields_footnotes_and_italics(self):
        footnote = '<w:footnote w:id="1"><w:p><w:r><w:t>Sobre las fábricas, véase Lobato (2001, p. 4).</w:t></w:r></w:p></w:footnote>'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.docx"
            _docx(path, _zotero_field_body(), footnote)
            report = cite_audit.audit(path, "es")
        self.assertEqual(report["summary"]["zotero_field_item_keys"], ["PD3F23HP"])
        self.assertIn("D-LIVE-ZOTERO-FIELDS", {f["rule"] for f in report["findings"]})
        self.assertEqual(report["references"][0]["raw"], "Acha, O. (2015). Lucha y organización. *Cuadernos del Ciesal*, (14), 59–81.")
        # The footnote citation is what keeps Lobato from being reported as uncited.
        self.assertEqual(report["summary"]["uncited_references"], 0)
        self.assertEqual([c["origin"] for c in report["citations"] if c["authors"] == ["Lobato"]], ["note"])


if __name__ == "__main__":
    unittest.main()
