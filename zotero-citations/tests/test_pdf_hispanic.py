import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import cite_audit  # noqa: E402
import citecore  # noqa: E402
import style_chicago as sch  # noqa: E402

# Synthetic pdftohtml -xml output: body 16pt, footnotes 15pt, note calls 10pt, note numbers 9pt,
# a running footer on both pages, a hyphenated line break, an italic block quote and a note
# that continues on the next page.
FONTS = ('<fontspec id="0" size="16" family="Times"/><fontspec id="1" size="15" family="Times"/>'
         '<fontspec id="2" size="10" family="Times"/><fontspec id="3" size="9" family="Times"/>')


def text(top, left, font, content, height=15):
    return f'<text top="{top}" left="{left}" width="400" height="{height}" font="{font}">{content}</text>'


PAGE1 = "".join([
    text(100, 160, 0, "La historiografía sostiene que la clase obrera tuvo una larga histo-"),
    text(119, 141, 0, "ria previa al peronismo y que sus organizaciones fueron decisivas."),
    text(116, 600, 2, '<a href="x.html#1">1</a>', 9),
    text(150, 160, 0, "<i>“Los gobernantes se reclutan en una clase de ciudadanos que, si no constituyen</i>"),
    text(169, 141, 0, "<i>propiamente una casta, forman por lo menos una clase dirigente, en cuyo seno se</i>"),
    text(188, 141, 0, "<i>ingresa con relativa facilidad, y cuyos miembros mantienen relaciones estrechas”</i>"),
    text(185, 700, 2, '<a href="x.html#1"><i>2</i></a>', 9),
    text(1050, 141, 3, "1", 9),
    text(1053, 151, 1, " Acha, Omar: <i>Historia crítica</i>, Buenos Aires, Prometeo, 2009, p. 12."),
    text(1070, 141, 3, "2", 9),
    text(1073, 151, 1, " Matienzo, José Nicolás: <i>El régimen republicano-federal</i>, Buenos Aires, "),
    text(1150, 141, 0, "Revista de Prueba, Núm. 16"),
    text(1150, 700, 0, "7"),
])
PAGE2 = "".join([
    text(100, 160, 0, "Otros autores coinciden con ese diagnóstico.", 15),
    text(97, 480, 2, '<a href="x.html#2">3</a>', 9),
    text(1040, 141, 1, "Secretaría de Cultura, 1994, pp. 81-"),
    text(1057, 141, 1, "146."),
    text(1070, 141, 3, "3", 9),
    text(1073, 151, 1, " Matienzo, José Nicolás: op.cit. p. 153 y Acha, Omar: ibídem p. 14."),
    text(1150, 141, 0, "Revista de Prueba, Núm. 16"),
    text(1150, 700, 0, "8"),
])
XML = (f'<?xml version="1.0" encoding="UTF-8"?><pdf2xml><page number="1" height="1200" width="900">{FONTS}{PAGE1}</page>'
       f'<page number="2" height="1200" width="900">{PAGE2}</page></pdf2xml>')


class PdfReading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = citecore.parse_pdf_xml(XML)

    def test_notes_are_split_numbered_and_continued_across_pages(self):
        notes = {n["id"]: n["text"] for n in self.doc["notes"]}
        self.assertEqual(sorted(notes), ["1", "2", "3"])
        self.assertEqual(notes["1"], "Acha, Omar: *Historia crítica*, Buenos Aires, Prometeo, 2009, p. 12.")
        self.assertTrue(notes["2"].endswith("Secretaría de Cultura, 1994, pp. 81-146."))

    def test_body_calls_hyphenation_footer_and_block_quote(self):
        paragraphs = self.doc["paragraphs"]
        self.assertTrue(paragraphs[0]["text"].startswith("La historiografía sostiene que la clase obrera tuvo una larga historia previa"))
        self.assertTrue(paragraphs[0]["text"].endswith("decisivas.[^1]"))
        self.assertEqual(paragraphs[1]["style"], "Quote")
        self.assertTrue(paragraphs[1]["text"].endswith("estrechas”*[^2]"))
        self.assertTrue(all("Revista de Prueba" not in p["text"] for p in paragraphs))
        self.assertIn("[^3]", paragraphs[2]["text"])


def note(text, note_id="1"):
    return sch.parse_note({"id": note_id, "text": text})[0]


class HispanicNotes(unittest.TestCase):
    def test_inverted_author_and_locator(self):
        c = note("Moore, Barrington Jr. : *Los orígenes sociales de la dictadura*, Barcelona, Península, 1973, pp. 421-422.")[0]
        self.assertEqual((c["kind"], c["authors"], c["title"], c["years"], c["locator"], c["inverted"]),
                         ("note-full", ["Moore"], "Los orígenes sociales de la dictadura", ["1973"], "421-422", True))

    def test_part_inside_a_book_cites_the_book(self):
        c = note("“Carta de Marx a Weydemeyer, 7 de marzo de 1852” en Marx, Carlos y Federico Engels: "
                 "*Correspondencia*, Buenos Aires, Editorial Problemas, 1947, p. 71.")[0]
        self.assertEqual((c["authors"], c["title"], c["part_title"][:5]), (["Marx", "Engels"], "Correspondencia", "Carta"))

    def test_two_back_references_in_one_note(self):
        cites = note("Matienzo, José Nicolás: op.cit. p.153-154 y Posada, Adolfo: op.cit. p. 210")
        self.assertEqual([(c["kind"], c["authors"], c["locator"]) for c in cites],
                         [("note-opcit", ["Matienzo"], "153-154"), ("note-opcit", ["Posada"], "210")])

    def test_chapter_locator(self):
        c = note("Quesada, Ernesto: *La época de Rosas*, Buenos Aires, Instituto, 1926, cap. 2.")[0]
        self.assertEqual(c["locator"], "cap. 2")

    def test_bare_ibid_inherits_the_previous_page(self):
        cites = sch.parse_note({"id": "1", "text": "Ramos Mejía, José M.: *Las multitudes argentinas*, Buenos Aires, "
                                                   "Belgrano, 1977, p. 111."})[0] + sch.parse_note({"id": "2", "text": "Ibidem."})[0]
        sch.Notes.stats = {}
        sch.Notes.crosscheck(cites, sch.Notes.synthesize_references(cites))
        self.assertEqual((cites[1]["ref_indexes"], cites[1]["locator"], cites[1]["locator_inherited"]), ([0], "111", True))

    def test_ibidem_forms(self):
        self.assertEqual(note("Ibídem. P. 88.")[0]["locator"], "88")
        self.assertEqual(note("Ibidem.")[0]["locator"], None)
        c = note("Matienzo, José Nicolás: ibídem p. 155.")[0]
        self.assertEqual((c["kind"], c["authors"], c["locator"]), ("note-ibid", ["Matienzo"], "155"))

    def test_semicolon_typo_secondary_and_untitled(self):
        linz = note('Linz, Juan; "Crisis, breakdown and requilibration", in Linz, J. and Stepan, A., ed., '
                    '*The Breakdown of Democratic Regimes*. Baltimore, Johns Hopkins, 1978, p. 35.')
        self.assertEqual([(c["authors"], c["title"]) for c in linz], [(["Linz"], "Crisis, breakdown and requilibration")])
        melo = note("Citado en: Melo, Carlos R: *Los partidos políticos argentinos*, Córdoba, UNC, 1964, p.69.")[0]
        self.assertEqual((melo["authors"], melo["secondary_source"]), (["Melo"], "citado en"))
        cossio = note("Cossio, Carlos: La revolución del 6 de septiembre, Buenos Aires, La Facultad, 1933, p.146.")[0]
        self.assertEqual((cossio["title"], cossio["untitled_markup"]), ("La revolución del 6 de septiembre", True))


MANUSCRIPT = """# Artículo con notas hispanas

Primera afirmación.[^1] Segunda.[^2] Tercera.[^3] Cuarta.[^4] Quinta.[^5] Sexta.[^6]

[^1]: Matienzo, José Nicolás: *El régimen republicano-federal*, Buenos Aires, Secretaría de Cultura, 1994, p. 218.

[^2]: Matienzo, José Nicolás: op.cit. p. 153.

[^3]: Matienzo, José Nicolás: *Remedios contra el gobierno personal*, Buenos Aires, Anaconda, 1931, p. 84.

[^4]: Ibídem. P. 88.

[^5]: Matienzo, José Nicolás: op. cit., p. 90.

[^6]: Posada, Adolfo: op. cit., p. 210.
"""


class BackReferenceResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.md"
            path.write_text(MANUSCRIPT, encoding="utf-8")
            cls.report = cite_audit.audit(path, "es")
            cls.no_lint = cite_audit.audit(path, "es", lint=False)

    def test_op_cit_and_ibidem_point_to_the_last_cited_work(self):
        titles = [r["title"][:10] for r in self.report["references"]]
        resolved = [titles[c["ref_indexes"][0]] if c.get("ref_indexes") else None for c in self.report["citations"]]
        self.assertEqual(resolved, ["El régimen", "El régimen", "Remedios c", "Remedios c", "Remedios c", None])

    def test_findings(self):
        rules = [f["rule"] for f in self.report["findings"]]
        self.assertEqual(rules.count("C-OPCIT-AMBIGUOUS"), 1)  # note 5: two Matienzo works already cited
        self.assertIn("C-OPCIT-UNRESOLVED", rules)  # note 6: Posada never cited before
        self.assertIn("C-NOTE-INVERTED", rules)

    def test_no_lint_keeps_only_cross_check(self):
        rules = {f["rule"] for f in self.no_lint["findings"]}
        self.assertTrue({"C-OPCIT-AMBIGUOUS", "C-OPCIT-UNRESOLVED"} <= rules)
        self.assertFalse({"C-OPCIT", "C-NOTE-INVERTED", "C-IBID"} & rules)


if __name__ == "__main__":
    unittest.main()
