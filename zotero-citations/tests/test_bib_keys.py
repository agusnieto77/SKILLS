import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

import cite_audit
import citecore


class BibliographyParser(unittest.TestCase):
    def test_nested_quoted_escaped_values_macros_and_original_locations(self):
        text = '\n@string{journal = "Revista"}\n@article{CaseKey,\n author={de la Cruz, Ana and {Equipo Uno}},\n title={Un {nivel {interior}} y \\{literal\\}},\n journal=journal # " de historia",\n note="Una {cita \\"anidada\\"}", year=2024, doi={10.1234/example}\n}\n'
        parsed = citecore.parse_bibliography(text, "fuentes.bib")
        self.assertTrue(parsed["complete"], parsed["warnings"])
        entry = parsed["entries"][0]
        self.assertEqual(entry["citekey"], "CaseKey")
        self.assertEqual(entry["fields"]["journal"], "Revista de historia")
        self.assertIn("{nivel {interior}}", entry["fields"]["title"])
        self.assertEqual(entry["original_entry"], text[entry["location"]["offset"]:entry["location"]["end"]])
        self.assertEqual((entry["location"]["line"], entry["location"]["column"]), (3, 1))

    def test_malformed_recovery_never_claims_complete(self):
        text = '@book{broken, title={Sin cerrar\n@book{good, title={Libro}, author={Doe, Jane}, year=2020}\n@article{bad, title="abierto'
        parsed = citecore.parse_bibliography(text, "mal.bib")
        self.assertFalse(parsed["complete"])
        self.assertIn("good", [e["citekey"] for e in parsed["entries"]])
        self.assertTrue(parsed["warnings"])
        self.assertTrue(all(w.get("location") for w in parsed["warnings"]))

    def test_unresolved_macro_and_missing_inheritance_warn(self):
        parsed = citecore.parse_bibliography('@book{k, title=missing # { fin}, crossref={absent}}', "a.bib")
        self.assertFalse(parsed["complete"])
        self.assertTrue(any(w["rule"] == "B-UNRESOLVED-MACRO" for w in parsed["warnings"]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "a.bib"
            path.write_text('@book{k, title={Libro}, crossref={absent}}', encoding="utf-8")
            data = cite_audit.audit(path, None)
            self.assertFalse(data["bibliography_complete"])
            self.assertIn("B-INHERITANCE", {f["rule"] for f in data["findings"]})

    def test_bib_inventory_has_match_compatible_fields_and_authorship(self):
        data = cite_audit.extract(HERE / "fixtures" / "keys.bib")
        ref = next(r for r in data["references"] if r["citekey"] == "Alpha")
        self.assertEqual((ref["authors"], ref["year"], ref["title"], ref["doi"]),
                         (["de la Cruz", "Equipo Uno"], "2024", "Historia anidada", "10.1234/alpha"))
        self.assertEqual(ref["author_details"], [{"family": "de la Cruz", "given": "Ana"}, {"literal": "Equipo Uno"}])
        self.assertEqual(ref["index"], 0)
        self.assertTrue(ref["parsed"])
        self.assertEqual(data["citations"], [])

    def test_crossref_xdata_and_parentheses_resolve_across_explicit_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.tex").write_text(r'\cite{child}', encoding="utf-8")
            (root / "one.bib").write_text('@incollection(child, title={Capítulo}, crossref={parent}, xdata={shared})', encoding="utf-8")
            (root / "two.bib").write_text('@book{parent, title={Volumen}, author={Doe, Jane}, year=2021}\n@xdata{shared,publisher={Editorial}}', encoding="utf-8")
            report = cite_audit.audit(root / "main.tex", None, bibliography_paths=[root / "one.bib", root / "two.bib"])
            child = report["references"][0]
            self.assertEqual((child["year"], child["authors"], child["fields"]["publisher"]), ("2021", ["Doe"], "Editorial"))
            self.assertTrue(report["bibliography_complete"])
            self.assertEqual(report["citations"][0]["ref_indexes"], [0])

    def test_duplicate_undefined_unused_and_case_sensitive_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript, bib = root / "m.tex", root / "refs.bib"
            manuscript.write_text(r'\cite{same,Same,missing}', encoding="utf-8")
            bib.write_text('@book{same,title={Uno}}\n@book{same,title={Dos}}\n@book{unused,title={Tres}}', encoding="utf-8")
            report = cite_audit.audit(manuscript, None, bibliography_paths=[bib])
            rules = {f["rule"]: f["severity"] for f in report["findings"]}
            self.assertEqual(rules["B-DUPLICATE-KEY"], "error")
            self.assertEqual(rules["C-UNDEFINED-KEY"], "error")
            self.assertEqual(rules["C-UNUSED-KEY"], "warning")
            self.assertNotIn("ref_indexes", report["citations"][0])
            self.assertEqual(len([f for f in report["findings"] if f["rule"] == "C-UNDEFINED-KEY"]), 2)

    def test_cyclic_macros_and_inheritance_warn_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            bib = Path(directory) / "cycle.bib"
            bib.write_text('@string{a=b}\n@string{b=a}\n@book{one,title=a,crossref={two}}\n'
                           '@book{two,title={Dos},crossref={one}}', encoding="utf-8")
            report = cite_audit.audit(bib, None)
            self.assertFalse(report["bibliography_complete"])
            self.assertTrue({"B-UNRESOLVED-MACRO", "B-INHERITANCE"} <= {f["rule"] for f in report["findings"]})
            self.assertNotIn("C-UNUSED-KEY", {f["rule"] for f in report["findings"]})

    def test_bib_comments_preamble_and_declared_truncation(self):
        text = '@comment{ignorar {anidado}}\n@preamble{"no ejecutar"}\n% @book{fake}\n' \
               '@book{k,author={Doe, Jane and others},title={Libro},year=2020}'
        parsed = citecore.parse_bibliography(text, "a.bib")
        self.assertTrue(parsed["complete"])
        self.assertEqual(len(parsed["entries"]), 1)
        ref = citecore.bibliography_reference(parsed["entries"][0], 0)
        self.assertTrue(ref["etal"])
        self.assertFalse(ref["authors_complete"])
        self.assertEqual(ref["authors"], ["Doe"])

    def test_bib_refs_match_zotero_by_normal_fields_not_citekey(self):
        import zotero_client
        ref = cite_audit.extract(HERE / "fixtures" / "keys.bib")["references"][0]
        item = {"key": "ABCDEFGH", "title": ref["title"], "creators": ["de la Cruz", "Equipo Uno"],
                "date": "2024", "DOI": ref["doi"], "ISBN": [], "inTrash": False}
        result = zotero_client.match_refs([ref], [item])[0]
        self.assertEqual((result["status"], result["best"]["key"]), ("exact-doi", "ABCDEFGH"))

    def test_cli_accepts_repeated_explicit_bibliographies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript, first, second = root / "m.tex", root / "a.bib", root / "b.bib"
            manuscript.write_text(r"\cite{a,b}", encoding="utf-8")
            first.write_text("@book{a,title={Uno}}", encoding="utf-8")
            second.write_text("@book{b,title={Dos}}", encoding="utf-8")
            with patch.object(sys, "argv", ["cite_audit.py", "audit", str(manuscript), "--bib", str(first),
                                             "--bib", str(second)]), patch.object(cite_audit, "emit") as emit:
                cite_audit.main()
            report = emit.call_args.args[0]
            self.assertEqual([c["ref_indexes"] for c in report["citations"]], [[0], [1]])


class KeyOccurrences(unittest.TestCase):
    def test_every_tex_command_with_optional_notes_and_multiple_keys(self):
        commands = ["cite", "parencite", "textcite", "autocite", "citep", "citet"]
        text = '\n'.join('\\' + command + '[véase {también}][pp. 2--4]{Alpha, beta}' for command in commands)
        citations = citecore.find_key_citations(text, "m.tex")
        self.assertEqual([c["citekey"] for c in citations], ["Alpha", "beta"] * len(commands))
        self.assertTrue(all(c["locator"] == "pp. 2--4" for c in citations))
        self.assertTrue(all(c["prenote"] == "véase {también}" for c in citations))
        for citation in citations:
            loc = citation["location"]
            self.assertEqual(text[loc["offset"]:loc["end"]], citation["citekey"])
            self.assertEqual(loc["file"], "m.tex")

    def test_tex_skips_comments_verbatim_and_escaped_commands(self):
        text = '% \\cite{comment}\n\\begin{verbatim}\n\\cite{code}\n\\end{verbatim}\n\\verb|\\cite{inline}|\n\\\\cite{escaped}\n\\cite{real} \\% \\cite{alsoReal}'
        self.assertEqual([c["citekey"] for c in citecore.find_key_citations(text, "m.tex")], ["real", "alsoReal"])

    def test_pandoc_quarto_skip_code_comments_email_and_preserve_location(self):
        text = '---\nbibliography: ../../never-read.bib\n---\nTexto [véase @Alpha, p. 7; @beta].\n`@inline` y persona@example.org.\n```python\n@fenced\n```\n<!-- @comment -->\n    @indented\n\\@escaped y @narrative.\n'
        cites = citecore.find_key_citations(text, "m.qmd")
        self.assertEqual([c["citekey"] for c in cites], ["Alpha", "beta", "narrative"])
        self.assertEqual(cites[0]["locator"], "p. 7")
        self.assertEqual((cites[0]["location"]["line"], cites[0]["location"]["column"]), (4, 15))
        self.assertEqual(text[cites[0]["location"]["offset"]:cites[0]["location"]["end"]], "Alpha")
        self.assertTrue(all(c.get("context") and "quotes" in c for c in cites))

    def test_pandoc_email_variants_and_multiline_code_are_not_citations(self):
        text = 'name.@example.org <other@example.org> mailto:a@example.org\n' \
               '``texto\n@notCodeCitation\n`` y [@real].'
        self.assertEqual([c["citekey"] for c in citecore.find_key_citations(text, "m.md")], ["real"])

    def test_tex_quote_shared_by_multiple_keys_keeps_each_binding(self):
        text = '«una cita textual con palabras suficientes» \\cite[p. 7]{Alpha,beta}.'
        citations = citecore.find_key_citations(text, "m.tex")
        self.assertEqual(len(citations), 2)
        self.assertTrue(all(c["quotes"][0]["text"] == "una cita textual con palabras suficientes" for c in citations))

    def test_quotes_bind_key_citations_and_inputs_stay_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript, bib = root / "m.qmd", root / "refs.bib"
            text = 'Según el estudio, «una cita textual con palabras suficientes» [@Alpha, p. 7].'
            manuscript.write_text(text, encoding="utf-8")
            bib.write_text('@article{Alpha,author={Doe, Jane},title={Libro},year=2024}', encoding="utf-8")
            before = (manuscript.read_bytes(), bib.read_bytes())
            data = cite_audit.audit(manuscript, None, bibliography_paths=[bib])
            citation = data["citations"][0]
            self.assertEqual(citation["ref_indexes"], [0])
            self.assertEqual(citation["quotes"][0]["text"], "una cita textual con palabras suficientes")
            self.assertEqual(citation["quotes"][0]["locator"], "p. 7")
            self.assertEqual((manuscript.read_bytes(), bib.read_bytes()), before)

    def test_no_bibliography_paths_are_inferred_from_untrusted_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "m.qmd"
            path.write_text('---\nbibliography: /not/a/real/file.bib\n---\n[@unknown]', encoding="utf-8")
            report = cite_audit.audit(path, None)
            self.assertEqual(report["references"], [])
            self.assertIn("C-UNDEFINED-KEY", {f["rule"] for f in report["findings"]})

    def test_pandoc_narrative_locator_and_html_code_exclusion(self):
        text = 'Según @Alpha [p. 9], el resultado cambia. <code>@notACitation</code>'
        citations = citecore.find_key_citations(text, "m.qmd")
        self.assertEqual([c["citekey"] for c in citations], ["Alpha"])
        self.assertEqual(citations[0]["locator"], "p. 9")
        self.assertEqual(citations[0]["raw"], "@Alpha [p. 9]")


if __name__ == "__main__":
    unittest.main()
