import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import cite_format as cf  # noqa: E402

ARTICLE = {
    "itemType": "journalArticle", "title": "Lucha y organización: repensar la historia de la clase obrera",
    "creators": [{"creatorType": "author", "firstName": "Omar", "lastName": "Acha"}],
    "publicationTitle": "Cuadernos del Ciesal", "volume": "", "issue": "14", "pages": "59-81", "date": "2015", "DOI": "",
}
CHAPTER = {
    "itemType": "bookSection", "title": "El sindicato de canillitas", "bookTitle": "Asociaciones y política",
    "creators": [{"creatorType": "author", "firstName": "Omar", "lastName": "Acha"},
                 {"creatorType": "editor", "firstName": "Omar", "lastName": "Acha"},
                 {"creatorType": "editor", "firstName": "Nicolás", "lastName": "Quiroga"}],
    "publisher": "Prometeo", "place": "Buenos Aires", "date": "2015", "pages": "45-70",
}
MANY = {**ARTICLE, "creators": [{"creatorType": "author", "firstName": f"N{i}", "lastName": f"Autor{i}"} for i in range(5)]}

TEMPLATE = {
    "name": "Revista de ejemplo",
    "names": {"first": "{FAMILY}, {given}", "rest": "{given} {FAMILY}", "sep": ", ", "last": " y ", "max": 3, "etal": " et al."},
    "short_names": {"two": " y ", "etal": " et al.", "threshold": 3},
    "editors": {"first": "{given} {family}", "rest": "{given} {family}", "last": " y ", "suffix_one": " (ed.)", "suffix_many": " (eds.)"},
    "reference": {
        "journalArticle": "{authors} ({year}): «{title}», *{container}*[, vol. {volume}][, n.º {issue}], pp. {pages:dash}.",
        "bookSection": "{authors} ({year}): «{title}», en {editors}, *{container}*, {place}, {publisher}, pp. {pages:dash}.",
        "*": "{authors} ({year}): *{title}*.",
    },
    "citation": "({authors_short}, {year}[: {locator}])",
}


class Html(unittest.TestCase):
    def test_markdown_italics_and_ordinal_indicators(self):
        html = '<div class="csl-entry">Acha, Omar. «Lucha». <i>Cuadernos del Ciesal</i>, n.<sup>o</sup> 14 (2015): 59-81.</div>'
        self.assertEqual(cf.html_to("markdown", html), "Acha, Omar. «Lucha». *Cuadernos del Ciesal*, n.º 14 (2015): 59-81.")

    def test_en_dash_skips_urls(self):
        text = "X. (2019). T. *J*, 3, 59-81. https://doi.org/10.1016/0003-066X.59-1"
        self.assertEqual(cf.en_dash_ranges(text), "X. (2019). T. *J*, 3, 59\u201381. https://doi.org/10.1016/0003-066X.59-1")

    def test_narratives(self):
        self.assertEqual(cf.spanish_connectors("(Acha, Quiroga, & Pérez, 2015)"), "(Acha, Quiroga y Pérez, 2015)")
        self.assertEqual(cf.narrative_from("(Marx & Engels, 1947)", "es"), "Marx y Engels (1947)")
        self.assertEqual(cf.narrative_from("(Acha, s. f.)", "es"), "Acha (s. f.)")
        self.assertEqual(cf.narrative_from("(Acha y Quiroga 2015)", "es"), "Acha y Quiroga (2015)")

    def test_entry_with_style_attribute(self):
        html = '<div class="csl-entry" style="margin-bottom: 1em;">Acha, Omar. 2015a. <i>Libro</i>.</div>'
        self.assertEqual(cf.html_to("text", html), "Acha, Omar. 2015a. Libro.")


class Locators(unittest.TestCase):
    def test_each_profile_prints_pages_its_own_way(self):
        self.assertEqual(cf.with_locator("(Acha, 2015)", "61", "apa", "citation"), "(Acha, 2015, p. 61)")
        self.assertEqual(cf.with_locator("(Acha, 2015)", "12-14", "apa", "citation"), "(Acha, 2015, pp. 12–14)")
        self.assertEqual(cf.with_locator("Acha (2015)", "61", "apa", "narrative"), "Acha (2015, p. 61)")
        self.assertEqual(cf.with_locator("(Acha 2015)", "p. 61", "chicago-author-date", "citation"), "(Acha 2015, 61)")
        self.assertEqual(cf.with_locator("Acha, «Lucha y organización».", "61", "chicago-notes", "note_short"),
                         "Acha, «Lucha y organización», 61.")
        # A full journal note carries the article's range: the cited page replaces it.
        self.assertEqual(cf.with_locator("Omar Acha, «Lucha», Cuadernos del Ciesal, n.º 14 (2015): 59–81.", "61",
                                         "chicago-notes", "note_full"),
                         "Omar Acha, «Lucha», Cuadernos del Ciesal, n.º 14 (2015): 61.")
        self.assertEqual(cf.with_locator("Omar Acha, Asociaciones (Prometeo, 2015).", "12", "chicago-notes", "note_full"),
                         "Omar Acha, Asociaciones (Prometeo, 2015), 12.")
        self.assertEqual(cf.with_locator("Juan B. Justo, «La teoría», Socialismo, 1920, 22.", "22", "chicago-notes", "note_full"),
                         "Juan B. Justo, «La teoría», Socialismo, 1920, 22.")


class Templates(unittest.TestCase):
    def test_article_with_optional_groups_and_modifiers(self):
        result = cf.template_render(TEMPLATE, ARTICLE, "reference", None)
        self.assertEqual(result["text"], "ACHA, Omar (2015): «Lucha y organización: repensar la historia de la clase obrera», "
                                         "*Cuadernos del Ciesal*, n.º 14, pp. 59–81.")
        self.assertEqual((result["pattern_for"], result["empty_fields"]), ("journalArticle", []))

    def test_chapter_editors_and_author_not_duplicated(self):
        text = cf.template_render(TEMPLATE, CHAPTER, "reference", None)["text"]
        self.assertEqual(text, "ACHA, Omar (2015): «El sindicato de canillitas», en Omar Acha y Nicolás Quiroga (eds.), "
                               "*Asociaciones y política*, Buenos Aires, Prometeo, pp. 45–70.")

    def test_etal_and_short_citation_with_locator(self):
        self.assertEqual(cf.template_render(TEMPLATE, MANY, "reference", None)["text"][:22], "AUTOR0, N0 et al. (201")
        self.assertEqual(cf.template_render(TEMPLATE, MANY, "citation", "61")["text"], "(Autor0 et al., 2015: 61)")
        self.assertEqual(cf.template_render(TEMPLATE, ARTICLE, "citation", None)["text"], "(Acha, 2015)")

    def test_unlisted_type_uses_fallback_and_missing_data_is_reported(self):
        book = {**ARTICLE, "itemType": "book", "title": "Libro"}
        self.assertEqual(cf.template_render(TEMPLATE, book, "reference", None),
                         {"text": "ACHA, Omar (2015): *Libro*.", "pattern_for": "*", "empty_fields": []})
        anonymous = {"itemType": "webpage", "title": "Página", "creators": [], "date": ""}
        self.assertEqual(cf.template_render(TEMPLATE, anonymous, "reference", None)["empty_fields"], ["authors", "year"])
        with_no_date = {**TEMPLATE, "no_date": "s. f."}
        self.assertEqual(cf.template_render(with_no_date, anonymous, "reference", None)["empty_fields"], ["authors"])
        self.assertEqual(cf.template_render(TEMPLATE, ARTICLE, "citation", None)["pattern_for"], "all")

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(SystemExit):
            cf.fill("{autor}", cf.template_fields(ARTICLE, TEMPLATE, None))

    def test_escaped_brackets_stay_literal(self):
        text, _ = cf.fill(r"\[Carta\] {title}[ ({place})]", {"title": "A Girri", "place": ""})
        self.assertEqual(text, "[Carta] A Girri")


class Comparison(unittest.TestCase):
    def test_comparable_ignores_italics_and_quote_style(self):
        self.assertEqual(cf.comparable('*Revista*, «Título» – 59–81'), cf.comparable('Revista, "Título" - 59-81'))

    def test_word_diff(self):
        self.assertEqual(cf.word_diff("ACHA, Omar (2015)", "ACHA, O. (2015)"), [{"produced": "Omar", "expected": "O."}])


class StyleSearch(unittest.TestCase):
    def test_search_and_resolve_use_the_cached_index(self):
        index = [{"name": "revista-x", "title": "Revista X de Historia", "dependent": 0, "updated": "2026-01-01 00:00:00",
                  "categories": {"format": "note", "fields": ["history"]}}]
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "styles.json"
            cache.write_text(json.dumps(index), encoding="utf-8")
            original = cf.cache_dir
            cf.cache_dir = lambda: Path(tmp)
            try:
                self.assertEqual([h["name"] for h in cf.search_styles("historia revista")], ["revista-x"])
                self.assertEqual(cf.resolve("revista-x")["family"], "note")
                self.assertEqual(cf.resolve("chicago")["name"], "chicago-notes")
                with self.assertRaises(SystemExit):
                    cf.resolve("revista-y")
            finally:
                cf.cache_dir = original


if __name__ == "__main__":
    unittest.main()
