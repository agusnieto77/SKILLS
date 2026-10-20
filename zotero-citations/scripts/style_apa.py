"""APA 7 profile: reference parsing and APA-specific rules (stdlib only)."""
from __future__ import annotations

import re
from collections import Counter

from citecore import (
    APA_HEAD_RE, base_reference, crosscheck_author_date, find_author_date_citations, finding, lint_shared,
)

NAME = "apa"
LABEL = "APA 7"
CSL = "apa"
PERSON_RE = re.compile(r"(?P<family>[^,&()\[\]]+?),\s*(?P<given>(?:[A-ZÁÉÍÓÚÑÜÇ][a-záéíóúñü]?\.[\s\-]*)+)")


def parse_reference(text: str) -> dict:
    ref = base_reference(text)
    ref["editors_as_authors"] = False
    head = APA_HEAD_RE.match(text)
    if not head:
        return ref
    ref["parsed"] = True
    ref["year"] = head.group("date").strip()
    authors, rest = head.group("authors").strip(), head.group("rest").strip()
    if re.search(r"\((?:Eds?|Coords?|Comps?|Dirs?)\.\)", authors):
        ref["editors_as_authors"] = True
        authors = re.sub(r"\s*\((?:Eds?|Coords?|Comps?|Dirs?)\.\)", "", authors)
    ref["etal"] = bool(re.search(r"\bet\s+al\.", authors))
    if authors.startswith(("*", "[", "“", '"')):
        ref["title_first"] = True
        ref["title"] = authors.strip("*[]“”\". ")
    else:
        people = [m.group("family").strip(" .&").removeprefix("& ").removeprefix("y ").strip() for m in PERSON_RE.finditer(authors)]
        full_given = [] if people else re.findall(
            r"(?:^|;\s*|,?\s+(?:y|&|and)\s+)([^,;&]+?),\s+[A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]{2,}", authors)
        if people:
            ref["authors"] = [p for p in people if p and p != "..."]
        elif full_given:
            ref["authors"] = [f.strip() for f in full_given]
            ref["full_given_names"] = True
        else:
            ref["corporate"] = authors.rstrip(".").strip()
            ref["authors"] = [ref["corporate"]]
    if not ref["title"]:
        if rest.startswith("*"):
            end = rest.find("*", 1)
            ref["title"] = rest[1:end] if end > 0 else rest.strip("*")
            ref["title_italic"] = True
        else:
            match = re.match(r"^(.+?[.?!])(?:\s|$)", re.sub(r"\[[^\]]*\]", "", rest))
            ref["title"] = (match.group(1) if match else rest).rstrip(".").strip()
            ref["title_italic"] = False
    if re.search(r"\b(?:En|In)\s+.{0,200}?\((?:Eds?|Coords?|Comps?|Dirs?)\.\)", rest):
        ref["kind"] = "chapter"
    elif re.search(r"\[(?:Tesis|Thesis|Doctoral|Master)", rest, re.I):
        ref["kind"] = "thesis"
    elif re.search(r",\s*(?:\*?\d+\*?)?(?:\(\d+[^)]*\))?,\s*(?:pp?\.\s*)?(?:e?\d+|[ivxlc]+)(?:[–-]\d+)?\.?", rest):
        ref["kind"] = "article"
    elif ref["isbn"] or ref.get("title_italic"):
        ref["kind"] = "book"
    return ref


def foreign_form(citation: dict):
    if citation.get("comma") is False:
        return ("C-COMMA-MISSING", "error", "APA: coma entre autor y año, p. ej. (Acha, 2015).")
    return None


def citation_findings(c: dict, ref: dict, i: int, label: str) -> list[dict]:
    loc = (c.get("locator") or "").strip()
    if re.fullmatch(r"\d+(?:\s*[–-]\s*\d+)?", loc):
        return [finding("C-LOCATOR-FORMAT", "warning", label, "APA: localizador con 'p.' o 'pp.', p. ej. (Acha, 2015, p. 61).", i)]
    return []


def citations(body: list[str], notes: list[dict]) -> list[dict]:
    return find_author_date_citations(body) + find_author_date_citations([n["text"] for n in notes], origin="note")


def synthesize_references(cites: list[dict]) -> list[dict]:
    return []  # APA always needs a reference list


def crosscheck(cites: list[dict], refs: list[dict]):
    return crosscheck_author_date(cites, refs, _Style)


def lint(refs: list[dict], lang: str, has_italic_markup: bool) -> list[dict]:
    findings = lint_shared(refs, check_same_year=True)
    connectors = Counter()
    for i, ref in enumerate(refs):
        raw, label = ref["raw"], ref["raw"][:90]
        if not ref["parsed"]:
            hint = " (parece Chicago autor-fecha)" if ref["shape"] == "author-date" else \
                   " (parece Chicago notas)" if ref["shape"] == "notes" else ""
            findings.append(finding("R-UNPARSED", "error", label,
                                    f"No sigue la estructura APA 'Autor, A. (Año). Título...'{hint}.", i))
            continue
        head = APA_HEAD_RE.match(raw)
        author_seg, tail = head.group("authors"), head.group("rest")
        if re.search(r"\b(recuperado\s+de|retrieved\s+from|disponible\s+en|available\s+(at|from))\b", raw, re.I):
            findings.append(finding("R-RETRIEVED", "warning", label, "APA 7 omite 'Recuperado de'; solo 'Recuperado el <fecha> de <URL>' para contenido que cambia.", i))
        if ref["etal"]:
            findings.append(finding("R-ETAL-IN-LIST", "error", label, "APA 7 lista hasta 20 autores; 'et al.' no va en referencias.", i))
        if ref.get("full_given_names"):
            findings.append(finding("R-INITIALS", "error", label, "Usar iniciales para los nombres de pila.", i))
        if lang == "es" and re.search(r"\(n\.\s?d\.", raw):
            findings.append(finding("R-ND-LANG", "error", label, "En español: 's. f.' en lugar de 'n.d.'.", i))
        if lang == "en" and re.search(r"\(s\.\s?f\.", raw):
            findings.append(finding("R-ND-LANG", "error", label, "In English: 'n.d.' instead of 's. f.'.", i))
        if re.search(r"\s&\s", author_seg):
            connectors["&"] += 1
        if re.search(r"\.\s*,?\s+y\s+[A-ZÁÉÍÓÚÑ]", author_seg):
            connectors["y"] += 1
            if lang == "es" and re.search(r",\s+y\s", author_seg):
                findings.append(finding("R-SERIAL-COMMA", "warning", label, "En español no va coma antes de 'y'.", i))
        if ref["kind"] == "article" and re.search(r"\bpp?\.\s*\d", tail):
            findings.append(finding("R-PP-ARTICLE", "error", label, "Artículos de revista: páginas sin 'pp.'.", i))
        if re.search(r"(?:^|\.\s)(?:[A-ZÁÉÍÓÚ][\wáéíóúñ]+(?:\s[A-ZÁÉÍÓÚ][\wáéíóúñ]+)*):\s+[A-ZÁÉÍÓÚ][^.]{1,60}\.(?:\s|$)",
                     tail.split(ref["title"] or "\0")[-1]) and ref["kind"] in ("book", "chapter", "unknown"):
            findings.append(finding("R-PLACE", "warning", label, "APA 7 omite la ciudad de la editorial ('Ciudad: Editorial' → 'Editorial').", i))
        if lang == "es" and re.search(r"\(\d+(st|nd|rd|th) ed\.\)", raw):
            findings.append(finding("R-EDITION-LANG", "warning", label, "En español: '(2.ª ed.)'.", i))
        title = ref.get("title") or ""
        words = [w for w in re.split(r"[\s:–—-]+", title)[1:] if len(w) >= 4 and not w.isupper()]
        capitalized = [w for w in words if w[:1].isupper()]
        if ref["kind"] in ("book", "chapter", "article", "thesis") and len(words) >= 3 and len(capitalized) / len(words) >= 0.6:
            findings.append(finding("R-TITLE-CASE", "warning", label, "Título en Title Case: APA usa sentence case para la obra (respetar nombres propios).", i))
        if has_italic_markup and "*" not in raw and ref["kind"] in ("book", "article", "thesis"):
            findings.append(finding("R-ITALICS", "warning", label, "Sin itálicas: título del libro/tesis o nombre y volumen de la revista van en cursiva.", i))
    if connectors["&"] and connectors["y"]:
        findings.append(finding("R-CONNECTOR-MIX", "warning", "lista completa", "Mezcla de '&' e 'y' entre autores: unificar.", None))
    if lang == "en" and connectors["y"]:
        findings.append(finding("R-CONNECTOR-LANG", "warning", "lista completa", "English reference lists use '&'.", None))
    return findings


class _Style:
    label = LABEL
    foreign_form = staticmethod(foreign_form)
    citation_findings = staticmethod(citation_findings)
