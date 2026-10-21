import io
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import cite_audit  # noqa: E402
import docx_revise  # noqa: E402
from citecore import W  # noqa: E402

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ROOT_NS = (f'xmlns:w="{W_NS}" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
           'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"')
BODY = """
<w:p><w:r><w:t xml:space="preserve">Como señala Lobato (2001: 4), las fábricas.</w:t><w:footnoteReference w:id="1"/></w:r></w:p>
<w:p/>
<w:p><w:r><w:t xml:space="preserve">Otro párrafo intacto (Acha 2015).</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Referencias</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">Lobato, Mirta. (2001). </w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>La Vida en las Fábricas</w:t></w:r><w:r><w:t xml:space="preserve">. Buenos Aires: Prometeo.</w:t></w:r></w:p>
<w:p><w:r><w:t xml:space="preserve">Acha, O. (2015). Lucha y organización. </w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>Cuadernos del Ciesal</w:t></w:r><w:r><w:t xml:space="preserve">, (14), 59-81.</w:t></w:r></w:p>
"""
FOOTNOTE = ('<w:footnote w:id="1"><w:p><w:r><w:footnoteRef/></w:r><w:r><w:t xml:space="preserve"> Véase '
            '</w:t></w:r><w:r><w:rPr><w:i/></w:rPr><w:t>Historia obrera</w:t></w:r><w:r><w:t xml:space="preserve">'
            ' (Lobato 2001: 4).</w:t></w:r></w:p></w:footnote>')
# Paragraph numbering is cite_audit's: non-empty body paragraphs.
CITE, OTHER, LOBATO, ACHA = 0, 1, 3, 4


def _docx(path: Path, body: str = BODY, footnote: str = FOOTNOTE):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/></Types>'))
        archive.writestr("word/_rels/document.xml.rels", (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" '
            'Target="settings.xml"/></Relationships>'))
        archive.writestr("word/document.xml", (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {ROOT_NS}><w:body>{body}'
            '<w:sectPr/></w:body></w:document>'))
        archive.writestr("word/footnotes.xml", (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:footnotes {ROOT_NS}>'
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
            f'{footnote}</w:footnotes>'))
        archive.writestr("word/settings.xml", (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:settings xmlns:w="{W_NS}">'
            '<w:zoom w:percent="100"/><w:defaultTabStop w:val="708"/></w:settings>'))


def _views(p):
    """(rejected, accepted) text of a revised paragraph, italics marked with *...*."""
    def text(accept):
        tokens = list(docx_revise._view(p, accept))
        flags = [it and not t.isspace() for t, it in tokens]
        for i, (token, _) in enumerate(tokens):
            if token.isspace():  # a blank is italic only inside an italic stretch
                before = next((flags[j] for j in range(i - 1, -1, -1) if not tokens[j][0].isspace()), False)
                after = next((flags[j] for j in range(i + 1, len(tokens)) if not tokens[j][0].isspace()), False)
                flags[i] = before and after
        out, italic = [], False
        for (token, _), flag in zip(tokens, flags, strict=True):
            if flag != italic:
                out.append("*")
                italic = flag
            out.append(token)
        return "".join(out) + ("*" if italic else "")
    return text(False), text(True)


class Revise(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name) / "m.docx"
        _docx(self.src)
        self.out = Path(self.tmp.name) / "out.docx"

    def tearDown(self):
        self.tmp.cleanup()

    def run_edits(self, edits, **kw):
        return docx_revise.apply(self.src, edits, self.out, kw.get("author", "Revisor"))

    def paragraphs(self, part="word/document.xml"):
        with zipfile.ZipFile(self.out) as archive:
            root = ET.fromstring(archive.read(part))
        return [p for p in root.iter(W + "p") if docx_revise._paragraph(p)["text"]]

    def test_numbering_matches_cite_audit(self):
        appendix = ('<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Anexo</w:t></w:r></w:p>'
                    '<w:p><w:r><w:t xml:space="preserve">Datos tomados de la serie (Acha 2015, 60).</w:t></w:r></w:p>')
        _docx(self.src, BODY + appendix)
        report = cite_audit.audit(self.src, "es")
        cite = next(c for c in report["citations"] if c["raw"] == "(Acha 2015, 60)")
        ref = next(r for r in report["references"] if r["authors"] == ["Acha"])
        self.assertEqual((cite["paragraph"], ref["paragraph"]), (6, ACHA))
        self.run_edits([{"op": "replace", "paragraph": cite["paragraph"], "old": "(Acha 2015, 60)", "new": "(Acha, 2015, p. 60)"},
                        {"op": "rewrite", "paragraph": ref["paragraph"],
                         "new": "Acha, O. (2015). Lucha y organización. *Cuadernos del Ciesal*, (14), 59–81."}])
        paragraphs = self.paragraphs()
        self.assertEqual(_views(paragraphs[6])[1], "Datos tomados de la serie (Acha, 2015, p. 60).")
        self.assertTrue(_views(paragraphs[ACHA])[1].endswith("(14), 59–81."))

    def test_replace_is_tracked_and_reversible(self):
        self.run_edits([{"op": "replace", "paragraph": CITE, "old": "Lobato (2001: 4)",
                         "new": "Lobato (2001, p. 4)"}], author="Ana Pérez")
        p = self.paragraphs()[CITE]
        rejected, accepted = _views(p)
        self.assertEqual(rejected, "Como señala Lobato (2001: 4), las fábricas.[^1]")
        self.assertEqual(accepted, "Como señala Lobato (2001, p. 4), las fábricas.[^1]")
        self.assertEqual({el.get(W + "author") for el in p.iter() if el.tag in (W + "ins", W + "del")}, {"Ana Pérez"})
        untouched = self.paragraphs()[OTHER]
        self.assertFalse(any(el.tag in docx_revise.REVISION_TAGS for el in untouched.iter()))

    def test_output_keeps_word_namespaces_and_turns_tracking_on(self):
        self.run_edits([{"op": "replace", "paragraph": OTHER, "old": "Acha 2015", "new": "Acha, 2015"}])
        with zipfile.ZipFile(self.out) as archive:
            document = archive.read("word/document.xml").decode("utf-8")
            settings = ET.fromstring(archive.read("word/settings.xml"))
        head = document[:document.index(">", document.index("<w:document")) + 1]
        self.assertIn('mc:Ignorable="w14"', head)
        self.assertIn('xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"', head)
        self.assertEqual([el.tag for el in settings], [W + "zoom", W + "trackRevisions", W + "defaultTabStop"])

    def test_rewrite_tracks_italic_changes_from_markup(self):
        new = "Lobato, M. (2001). *La vida en las fábricas*. Prometeo."
        result = self.run_edits([{"op": "rewrite", "paragraph": LOBATO, "new": new}])
        rejected, accepted = _views(self.paragraphs()[LOBATO])
        self.assertEqual(accepted, new)
        self.assertEqual(rejected, "Lobato, Mirta. (2001). *La Vida en las Fábricas*. Buenos Aires: Prometeo.")
        self.assertEqual(result["revisions"]["italic_changes"], 0)
        self.out.unlink()
        result = self.run_edits([{"op": "rewrite", "paragraph": ACHA,
                                  "new": "Acha, O. (2015). *Lucha y organización*. Cuadernos del Ciesal, (14), 59–81."}])
        self.assertEqual(result["revisions"]["italic_changes"], 2)
        self.assertEqual(_views(self.paragraphs()[ACHA])[1],
                         "Acha, O. (2015). *Lucha y organización*. Cuadernos del Ciesal, (14), 59–81.")

    def test_text_without_markup_keeps_existing_italics(self):
        result = self.run_edits([{"op": "replace", "paragraph": LOBATO, "old": "La Vida en las Fábricas",
                                  "new": "La vida en las fábricas"}])
        self.assertEqual(result["revisions"]["italic_changes"], 0)
        self.assertEqual(_views(self.paragraphs()[LOBATO])[1],
                         "Lobato, Mirta. (2001). *La vida en las fábricas*. Buenos Aires: Prometeo.")

    def test_footnote_edit_keeps_note_number_and_italics(self):
        self.run_edits([{"op": "replace", "note": "1", "old": "(Lobato 2001: 4)", "new": "(Lobato, 2001, p. 4)"}])
        with zipfile.ZipFile(self.out) as archive:
            notes = ET.fromstring(archive.read("word/footnotes.xml"))
        p = next(n for n in notes.iter(W + "footnote") if n.get(W + "id") == "1").find(W + "p")
        self.assertIsNotNone(p.find(f".//{W}footnoteRef"))
        self.assertEqual(_views(p), (" Véase *Historia obrera* (Lobato 2001: 4).",
                                     " Véase *Historia obrera* (Lobato, 2001, p. 4)."))

    def test_insert_and_delete_paragraphs(self):
        self.run_edits([{"op": "insert", "after": LOBATO, "new": "Nueva, A. (2020). *Título*. Editorial."},
                        {"op": "delete", "paragraph": ACHA}])
        with zipfile.ZipFile(self.out) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
        paragraphs = [p for p in root.iter(W + "p") if list(docx_revise._view(p, False)) or list(docx_revise._view(p, True))]
        texts = [_views(p) for p in paragraphs]
        self.assertEqual(texts[4], ("", "Nueva, A. (2020). *Título*. Editorial."))
        self.assertEqual(texts[5][1], "")
        self.assertTrue(texts[5][0].startswith("Acha, O. (2015)"))
        marks = [el.tag for p in paragraphs[4:6] for el in p.find(f"{W}pPr/{W}rPr")]
        self.assertEqual(marks, [W + "ins", W + "del"])

    def test_comment_is_registered(self):
        result = self.run_edits([{"op": "comment", "paragraph": ACHA, "comment": "[verificar: editorial]\nFuente: CONICET"}])
        self.assertEqual(result["revisions"]["comments"], 1)
        with zipfile.ZipFile(self.out) as archive:
            comments = ET.fromstring(archive.read("word/comments.xml"))
            rels = archive.read("word/_rels/document.xml.rels").decode()
            types = archive.read("[Content_Types].xml").decode()
        self.assertEqual(["".join(t.text for t in p.iter(W + "t")) for p in comments.iter(W + "p")],
                         ["[verificar: editorial]", "Fuente: CONICET"])
        self.assertIn('Target="comments.xml"', rels)
        self.assertIn('PartName="/word/comments.xml"', types)
        self.assertEqual(docx_revise.summary(self.out)["revisions"]["comments"], 1)

    def test_invalid_edits_write_nothing(self):
        result = self.run_edits([
            {"op": "replace", "paragraph": CITE, "old": "Lobato (2001: 4)", "new": "Lobato (2001, p. 4)"},
            {"op": "replace", "paragraph": LOBATO, "old": "a", "new": "b"},
            {"op": "replace", "paragraph": OTHER, "old": "no existe", "new": "x"},
            {"op": "replace", "note": "1", "old": "Véase", "new": "Ver[^2]"},
            {"op": "rewrite", "paragraph": 99, "new": "x"}])
        self.assertFalse(result["written"])
        self.assertEqual([e["index"] for e in result["errors"]], [1, 2, 3, 4])
        self.assertIn("cannot create note calls", result["errors"][2]["error"])
        self.assertFalse(self.out.exists())

    def test_paragraphs_with_pending_revisions_or_live_fields_are_refused(self):
        body = BODY.replace('<w:t xml:space="preserve">Otro párrafo intacto (Acha 2015).</w:t></w:r>',
                            '<w:t xml:space="preserve">Otro párrafo intacto (Acha 2015).</w:t></w:r>'
                            '<w:ins w:id="9" w:author="X"><w:r><w:t>más</w:t></w:r></w:ins>')
        body += ('<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> ADDIN ZOTERO_ITEM {}'
                 '</w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>(Acha, 2015)</w:t></w:r>'
                 '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
        _docx(self.src, body)
        result = self.run_edits([{"op": "replace", "paragraph": OTHER, "old": "Otro", "new": "Un"},
                                 {"op": "rewrite", "paragraph": 5, "new": "(Acha, 2016)"}])
        self.assertEqual([e["error"].split(":")[0] for e in result["errors"]],
                         ["paragraph already has tracked changes", "live Zotero field"])

    def test_never_overwrites(self):
        self.out.write_bytes(b"keep")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_edits([{"op": "comment", "paragraph": 0, "comment": "x"}])
        self.assertEqual(self.out.read_bytes(), b"keep")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            docx_revise.apply(self.src, [], self.src, "x")


if __name__ == "__main__":
    unittest.main()
