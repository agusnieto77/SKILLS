"""Chicago Manual of Style, 18th edition: author-date and notes-bibliography profiles (stdlib only).

Rules follow CMOS 18: up to six authors in a bibliography/reference list, more
than six → first three + et al. (13.23); one or two authors in notes and text
citations, three or more → first + et al. (13.23, 13.107); shortened citations
preferred to ibid. (13.37); repeat the author's name instead of a 3-em dash (13.72);
no comma between author and year in author-date citations; bare page numbers.
"""
from __future__ import annotations

import re

import style_apa
from citecore import (
    AUTHOR_DATE_HEAD_RE, DASH_AUTHOR_RE, NOTE_MARK_RE, URL_RE, attach_quotes, author_count_findings, base_reference,
    crosscheck_author_date, family_of, find_author_date_citations, finding, first_title, lint_shared, name_matches,
    narrative_authors, shape_of, split_names,
)
from zotlib import fold, main_title, title_similarity

ROLE_RE = re.compile(r",?\s*\(?(?:eds?|coords?|comps?|dirs?|trads?)\.\)?\s*$", re.I)
YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})[a-z]?\b")


# --------------------------------------------------------------------------- shared parsing

def parse_inverted_names(segment: str) -> dict:
    """'Acha, Omar, y Nicolás Quiroga' → families ['Acha', 'Quiroga'] (CMOS inverts only the first)."""
    segment = ROLE_RE.sub("", segment.strip().rstrip("."))
    etal = bool(re.search(r"\bet\s+al\.?", segment))
    segment = re.sub(r",?\s*\bet\s+al\.?", "", segment).strip(" ,")
    parts = [p.strip() for p in segment.split(",") if p.strip()]
    if len(parts) < 2:
        return {"authors": [segment] if segment else [], "corporate": segment or None, "etal": etal}
    rest = ", ".join(parts[1:])
    names = [n.strip() for n in re.split(r",\s*|\s+(?:y|and|e|&)\s+|^(?:y|and)\s+", rest) if n.strip()]
    families = [parts[0]] + [family_of(n) for n in names[1:]]
    return {"authors": families, "corporate": None, "etal": etal, "ampersand": "&" in segment}


def _with_names(ref: dict, segment: str) -> dict:
    if segment.startswith(("*", "«", "“", '"', "[")):
        ref["title_first"] = True
        return ref
    names = parse_inverted_names(segment)
    ref.update(authors=names["authors"], corporate=names["corporate"], etal=names["etal"],
               ampersand=names.get("ampersand", False), author_segment=segment)
    return ref


def parse_author_date_reference(text: str) -> dict:
    ref = base_reference(text)
    head = AUTHOR_DATE_HEAD_RE.match(text)
    if not head:
        return ref
    ref["parsed"] = True
    ref["year"] = head.group("date").strip()
    _with_names(ref, head.group("authors").strip())
    rest = head.group("rest").strip()
    if ref["title_first"]:
        ref["title"] = (first_title(head.group("authors"))[0] or head.group("authors")).strip("*«»“”\". ")
        return ref
    title, start, _ = first_title(rest)
    if title and start == 0:
        ref["title"] = title
        ref["kind"] = "article" if not rest.startswith("*") else "book"
    else:
        match = re.match(r"^(.+?[.?!])(?:\s|$)", rest)
        ref["title"] = (match.group(1) if match else rest).rstrip(".").strip()
    return ref


def parse_notes_reference(text: str) -> dict:
    ref = base_reference(text)
    title, start, end = first_title(text)
    if title is None:
        fallback = re.match(r"^([^,.]+,\s[^.]+?)\.\s+(.+?)\.\s", text)
        if not fallback:
            return ref
        segment, title, end = fallback.group(1), fallback.group(2), fallback.end(2)
    else:
        segment = text[:start].strip().rstrip(".").strip()
    ref["parsed"] = True
    ref["title"] = title
    if start == 0:
        ref["title_first"] = True
    else:
        _with_names(ref, segment)
    years = YEAR_RE.findall(URL_RE.sub("", text[end:]))
    ref["year"] = years[-1] if years else None
    ref["kind"] = "book" if text[start:start + 1] == "*" else "article" if re.search(r"\(\d{4}\)", text[end:]) else "unknown"
    return ref


def _title_matches(short: str | None, full: str | None) -> bool:
    fs, ff = fold(short), fold(full)
    if not fs or not ff:
        return False
    if ff.startswith(fs) or fs.startswith(ff):
        return True
    words = fs.split()
    if len(words) >= 2 and set(words) <= set(ff.split()):
        return True
    return title_similarity(short, full) >= 0.85 or title_similarity(short, main_title(full)) >= 0.9


def lint_chicago(refs: list[dict], lang: str, system: str) -> list[dict]:
    findings = lint_shared(refs, check_same_year=system == "author-date")
    for i, ref in enumerate(refs):
        raw, label = ref["raw"], ref["raw"][:90]
        if ref.get("synthetic"):
            continue
        if not ref["parsed"]:
            findings.append(finding("R-UNPARSED", "error", label, f"No se reconoce la estructura Chicago {system}.", i))
            continue
        expected = "author-date" if system == "author-date" else "notes"
        if ref["shape"] in ("apa", "author-date", "notes") and ref["shape"] != expected:
            other = {"apa": "APA (año entre paréntesis)", "author-date": "Chicago autor-fecha (año tras el autor)",
                     "notes": "Chicago notas (año al final)"}[ref["shape"]]
            findings.append(finding("R-WRONG-SYSTEM", "error", label, f"Entrada con forma de {other}; unificar con el sistema del manuscrito.", i))
        listed = len(ref["authors"])
        if not ref["corporate"] and listed > 6:
            findings.append(finding("R-AUTHORS-LIMIT", "error", label, "CMOS 18 (13.23): más de seis autores → los tres primeros + et al.", i))
        elif ref.get("etal") and listed != 3:
            findings.append(finding("R-AUTHORS-LIMIT", "warning", label, "CMOS 18 (13.23): con 'et al.' se listan exactamente los tres primeros autores.", i))
        if DASH_AUTHOR_RE.match(raw):
            findings.append(finding("R-3EM-DASH", "warning", label, "CMOS 18 (13.72): repetir el nombre del autor en vez de la raya de 3 em.", i))
        if ref.get("ampersand"):
            findings.append(finding("R-AMPERSAND", "warning", label, "Chicago: 'y' / 'and' entre autores, no '&'.", i))
        if lang == "es" and re.search(r"\bn\.\s?d\.", raw):
            findings.append(finding("R-ND-LANG", "error", label, "En español: 's. f.' en lugar de 'n.d.'.", i))
        if lang == "en" and re.search(r"\bs\.\s?f\.", raw):
            findings.append(finding("R-ND-LANG", "error", label, "In English: 'n.d.' instead of 's. f.'.", i))
    return findings


def _parse_any(text: str, preferred) -> dict:
    """Parse each entry with the parser of the system it is written in, so citations
    still resolve; R-WRONG-SYSTEM then flags entries outside the manuscript's system."""
    parser = {"apa": style_apa.parse_reference, "author-date": parse_author_date_reference,
              "notes": parse_notes_reference}.get(shape_of(text), preferred)
    ref = parser(text)
    return ref if ref["parsed"] else preferred(text)


# --------------------------------------------------------------------------- author-date

class AuthorDate:
    NAME = "chicago-author-date"
    LABEL = "Chicago 18.ª (autor-fecha)"
    CSL = "chicago-author-date"
    label = LABEL

    @staticmethod
    def parse_reference(text: str) -> dict:
        return _parse_any(text, parse_author_date_reference)

    @staticmethod
    def foreign_form(citation: dict):
        if citation.get("comma") is True:
            return ("C-COMMA-EXTRA", "error", "Chicago autor-fecha: sin coma entre autor y año, p. ej. (Acha 2015, 61).")
        return None

    @staticmethod
    def citation_findings(c: dict, ref: dict, i: int, label: str) -> list[dict]:
        out = []
        if re.match(r"\s*pp?\.\s*\d", c.get("locator") or ""):
            out.append(finding("C-LOCATOR-FORMAT", "warning", label, "Chicago: número de página sin 'p.', p. ej. (Acha 2015, 61).", i))
        if "&" in (c.get("author_text") or ""):
            out.append(finding("C-AMPERSAND", "warning", label, "Chicago: 'y' / 'and' entre autores, no '&'.", i))
        return out

    @classmethod
    def citations(cls, body: list[str], notes: list[dict]) -> list[dict]:
        return find_author_date_citations(body) + find_author_date_citations([n["text"] for n in notes], origin="note")

    @classmethod
    def crosscheck(cls, cites: list[dict], refs: list[dict]):
        return crosscheck_author_date(cites, refs, cls)

    @staticmethod
    def lint(refs: list[dict], lang: str, has_italic_markup: bool) -> list[dict]:
        return lint_chicago(refs, lang, "author-date")

    @staticmethod
    def synthesize_references(cites: list[dict]) -> list[dict]:
        return []


# --------------------------------------------------------------------------- notes and bibliography

IBID_RE = re.compile(r"^ib[ií]d(?:em)?\.?[,.]?\s*(?P<loc>.*)$", re.I)
# Hispanic/European back-references with an author: "Matienzo, José Nicolás: op. cit., p. 153" / ": ibídem p. 155".
AUTHOR_BACKREF_RE = re.compile(
    r"^(?P<who>[^:;«“\"*]{2,80}?)\s*[:,]\s*(?P<kw>op\.?\s?cit|loc\.?\s?cit|ib[ií]d(?:em)?)\.?[,.]?\s*(?P<loc>.*)$", re.I)
LOCATOR_TAIL_RE = re.compile(
    r"(?:,|:)\s*(?:pp?\.\s*)?(?P<loc>(?:caps?\.\s*)?[\dIVXLCivxlc]+(?:\s*[–-]\s*[\dIVXLCivxlc]+)?(?:\s?n\.?\s?\d+)?)\s*$")
AUTHOR_ONLY_RE = re.compile(
    r"^(?P<who>[A-ZÁÉÍÓÚÑ][\w’'\-]+(?:\s+(?:y|and)\s+[A-ZÁÉÍÓÚÑ][\w’'\-]+)?(?:\s+et\s+al\.)?),\s*(?:pp?\.\s*)?"
    r"(?P<loc>\d+(?:\s*[–-]\s*\d+)?)$")
SECONDARY_PREFIX_RE = re.compile(r"^(?:citad[oa]|cit\.|quoted)\s+(?:en|por|in|by)\s*:?\s*", re.I)
SEE_PREFIX_RE = re.compile(r"^(?:v[eé]ase(?:\s+tambi[eé]n)?|ver|cf\.|cfr\.|see(?:\s+also)?)\s+", re.I)
# " y Posada, Adolfo: op. cit." — a second inverted "Family, Given:" citation inside the same segment.
INVERTED_JOIN_RE = re.compile(r"\s+(?:y|and)\s+(?=[A-ZÁÉÍÓÚÑ][\w’'\-]+(?:\s[A-ZÁÉÍÓÚÑ][\w’'\-]+)?,\s[^:;«“\"*]{2,40}:)")
PART_IN_RE = re.compile(r"^[\s,.]*(?:en|in)\s+(?P<who>[^*«“\"]{3,120}?):\s*")
UNTITLED_RE = re.compile(r"^(?P<who>[^:;,]{2,40},[^:;]{2,40}):\s*(?P<title>[^,]{5,200}?),\s")


def _split_segments(text: str) -> list[str]:
    """Split a note on ';' outside titles (« », “ ”, *...*), then on ' y Family, Given:'."""
    segments, depth, italic, current = [], 0, False, []
    for ch in text:
        if ch in "«“":
            depth += 1
        elif ch in "»”":
            depth = max(0, depth - 1)
        elif ch == "*":
            italic = not italic
        if ch == ";" and not depth and not italic:
            segments.append("".join(current))
            current = []
        else:
            current.append(ch)
    segments.append("".join(current))
    segments = [s.strip() for s in segments if s.strip()]
    merged = []
    for seg in segments:
        # "Linz, Juan; "Crisis..."": a ';' typed after the author instead of ':' splits one citation in two.
        if merged and first_title(seg)[1] == 0 and first_title(merged[-1])[0] is None \
                and re.fullmatch(r"[^,]{2,40},[^,]{2,40}", merged[-1]):
            merged[-1] = f"{merged[-1]}: {seg}"
            continue
        merged.append(seg)
    out = []
    for seg in merged:
        out += [p.strip() for p in INVERTED_JOIN_RE.split(seg) if p.strip()]
    return out


def _clean_locator(loc: str | None) -> str | None:
    loc = re.sub(r"^\s*[pP]p?\.\s*", "", (loc or "").strip().rstrip(".")).strip()
    return loc or None


def _names(prefix_raw: str) -> tuple[list[str], int, bool, str, bool]:
    """(families, names listed, et al., author text, inverted) from the text before a title.

    'Acha, Omar:' / 'Moore, Barrington Jr. :' (Hispanic notes: inverted, colon) vs
    'Omar Acha,' (Chicago notes: natural order, comma).
    """
    inverted = bool(re.search(r"[:;]\s*$", prefix_raw)) and "," in prefix_raw
    prefix = re.sub(r"[\s,:;]+$", "", prefix_raw)
    if not prefix:
        return [], 0, False, "", False
    if inverted:
        names = parse_inverted_names(prefix)
        return names["authors"], len(names["authors"]), names["etal"], prefix, True
    author_text = narrative_authors(prefix)
    names, etal = split_names(author_text)
    return [family_of(n) for n in names], len(names), etal, author_text, False


def parse_note(note: dict) -> tuple[list[dict], int]:
    """Citations in one note → (citations, unparsed segment count)."""
    cites, unparsed = [], 0
    for segment in _split_segments(note["text"]):
        s = URL_RE.sub("", segment).strip().rstrip(".").strip()
        secondary = bool(SECONDARY_PREFIX_RE.match(s))
        s = SEE_PREFIX_RE.sub("", SECONDARY_PREFIX_RE.sub("", s))
        base = {"origin": "note", "note": note["id"], "raw": segment, "comma": None, "abbreviation": None, "years": [],
                "secondary_source": "citado en" if secondary else None}
        ibid = IBID_RE.match(s)
        if ibid:
            cites.append({**base, "kind": "note-ibid", "authors": [], "etal": False, "author_text": "", "title": None,
                          "locator": _clean_locator(ibid.group("loc"))})
            continue
        back = AUTHOR_BACKREF_RE.match(s)
        if back and not first_title(s)[0]:
            families, listed, etal, author_text, inverted = _names(back.group("who") + ":")
            kind = "note-ibid" if back.group("kw").lower().startswith("ib") else "note-opcit"
            cites.append({**base, "kind": kind, "authors": families, "names_listed": listed, "etal": etal,
                          "author_text": author_text, "title": None, "inverted": inverted,
                          "locator": _clean_locator(back.group("loc"))})
            continue
        title, start, end = first_title(s)
        part_title = None
        if title and start == 0:
            part = PART_IN_RE.match(s[end:])
            book = first_title(s[end + part.end():]) if part else (None, -1, -1)
            if part and book[0] and book[1] == 0:
                # "«Carta de Marx...» en Marx, Carlos y Federico Engels: *Correspondencia*" → the book is the work.
                part_title, title = title, book[0]
                families, listed, etal, author_text, inverted = _names(part.group("who") + ":")
                end = end + part.end() + book[2]
            else:
                families, listed, etal, author_text, inverted = [], 0, False, "", False
        elif title:
            families, listed, etal, author_text, inverted = _names(s[:start])
        else:
            untitled = UNTITLED_RE.match(s)
            if not untitled:
                only = AUTHOR_ONLY_RE.match(s)
                if only:
                    names, etal = split_names(only.group("who"))
                    cites.append({**base, "kind": "note-author", "authors": names, "names_listed": len(names),
                                  "etal": etal, "author_text": only.group("who"), "title": None,
                                  "locator": only.group("loc")})
                else:
                    unparsed += 1  # discursive remark or archival reference without a title
                continue
            title, end = untitled.group("title").strip(), untitled.end("title")
            families, listed, etal, author_text, inverted = _names(untitled.group("who") + ":")
            base["untitled_markup"] = True
        after = s[end:]
        years = YEAR_RE.findall(after)
        loc = LOCATOR_TAIL_RE.search(after)
        full = bool(years)
        cites.append({**base, "kind": "note-full" if full else "note-short", "authors": families, "names_listed": listed,
                      "etal": etal, "author_text": author_text, "title": title, "part_title": part_title,
                      "inverted": inverted, "years": years[:1],
                      "locator": loc.group("loc") if loc and not (full and loc.group("loc") in years) else None})
    return cites, unparsed


def note_citations(body: list[str], notes: list[dict]) -> tuple[list[dict], dict]:
    """Note citations in document order, anchored to the body sentence that calls each note."""
    parsed, stats = {}, {"notes": len(notes), "unparsed_segments": 0, "anchored": 0}
    for note in notes:
        cites, unparsed = parse_note(note)
        parsed[note["id"]] = cites
        stats["unparsed_segments"] += unparsed
    ordered, seen, recent, intro = [], set(), [], False
    for index, text in enumerate(body):
        found = []
        for m in NOTE_MARK_RE.finditer(text):
            note_id = m.group(1)
            if note_id in seen or note_id not in parsed:
                continue
            seen.add(note_id)
            for c in parsed[note_id]:
                # A call placed after the sentence's closing punctuation belongs to that sentence.
                anchor = m.start() - 1 if m.start() and text[m.start() - 1] in ".!?…;:," else m.start()
                at_end = not NOTE_MARK_RE.sub("", text[m.end():]).strip(" .")
                c.update(paragraph=index, span=[anchor, anchor], at_paragraph_end=at_end)
                found.append(c)
        if found:
            stats["anchored"] += len({c["note"] for c in found})
            attach_quotes(text, found, recent, intro)
            ordered += found
        recent = found or (recent if text.rstrip().endswith(":") else [])
        intro = text.rstrip().endswith(":")
    for note in notes:  # notes never called from the body (e.g. plain text input)
        if note["id"] not in seen:
            for c in parsed[note["id"]]:
                c.update(paragraph=None, context=None, quotes=[])
                ordered.append(c)
    return ordered, stats


def _same_work(a: dict, b: dict) -> bool:
    if a.get("title") and b.get("title"):
        return _title_matches(a["title"], b["title"]) and (
            not a["authors"] or not b["authors"] or fold(a["authors"][0]) == fold(b["authors"][0]))
    return bool(a["authors"] and b["authors"] and fold(a["authors"][0]) == fold(b["authors"][0]))


class Notes:
    NAME = "chicago-notes"
    LABEL = "Chicago 18.ª (notas y bibliografía)"
    CSL = "chicago-notes-bibliography"
    SHORT_CSL = "chicago-shortened-notes-bibliography"
    label = LABEL
    stats: dict = {}

    @staticmethod
    def parse_reference(text: str) -> dict:
        return _parse_any(text, parse_notes_reference)

    @classmethod
    def citations(cls, body: list[str], notes: list[dict]) -> list[dict]:
        cites, cls.stats = note_citations(body, notes)
        return cites

    @staticmethod
    def synthesize_references(cites: list[dict]) -> list[dict]:
        """No bibliography: the first full note of each work stands in as its reference."""
        refs = []
        for c in cites:
            if c["kind"] != "note-full" or any(_same_work(c, r) for r in refs):
                continue
            ref = base_reference(c["raw"])
            ref.update(parsed=True, synthetic=True, from_note=c["note"], authors=c["authors"], title=c["title"],
                       year=(c["years"] or [None])[0], etal=c["etal"], shape="notes")
            refs.append(ref)
        for i, r in enumerate(refs):
            r["index"] = i
        return refs

    @classmethod
    def crosscheck(cls, cites: list[dict], refs: list[dict]):
        findings, cited = [], set()
        synthetic = bool(refs) and all(r.get("synthetic") for r in refs)
        previous_note, previous_cites, seen_full = None, [], []
        by_author: dict[str, list[int]] = {}  # family → ref indexes cited so far, most recent last
        inverted_reported = False
        for c in cites:
            label = c["raw"][:70]
            author_key = fold(c["authors"][0]) if c["authors"] else None
            if c["kind"] == "note-ibid" and not c["authors"]:
                findings.append(finding("C-IBID", "info", label, "CMOS 18 (13.37) prefiere la cita abreviada (Autor, Título corto, página); 'ibid.' sigue admitido.", None))
                if len(previous_cites) != 1:
                    findings.append(finding("C-IBID-AMBIGUOUS", "error", label,
                                            "'Ibid.' solo puede seguir a una nota con una única fuente.", None))
                elif previous_cites[0].get("ref_indexes"):
                    c["ref_indexes"] = list(previous_cites[0]["ref_indexes"])
                    c["authors"] = previous_cites[0]["authors"]
                    if not c["locator"]:
                        c["locator"] = previous_cites[0].get("locator")  # bare "Ibid." = same work, same page
                        c["locator_inherited"] = bool(c["locator"])
            elif c["kind"] in ("note-ibid", "note-opcit"):
                word = "op. cit." if c["kind"] == "note-opcit" else "ibídem"
                findings.append(finding("C-OPCIT", "warning", label,
                                        f"'{word}' con autor: CMOS 18 usa la nota abreviada (Autor, Título corto, página).", None))
                history = by_author.get(author_key, [])
                if not history:
                    findings.append(finding("C-OPCIT-UNRESOLVED", "error", label,
                                            f"'{word}' sin una cita previa de ese autor.", None))
                else:
                    c["ref_indexes"] = [history[-1]]
                    cited.add(history[-1])
                    works = list(dict.fromkeys(history))
                    if len(works) > 1 and c["kind"] == "note-opcit":
                        findings.append(finding("C-OPCIT-AMBIGUOUS", "error", label,
                                                f"Ya se citaron {len(works)} obras de este autor: 'op. cit.' no indica cuál.",
                                                history[-1], candidates=works))
            else:
                parsed = [i for i, r in enumerate(refs) if r["parsed"]]
                by_name = [i for i in parsed if c["authors"] and name_matches(c, refs[i], {})]
                if c.get("title"):
                    pool = by_name or [i for i in parsed if not refs[i]["authors"]]
                    candidates = [i for i in pool if _title_matches(c["title"], refs[i]["title"])]
                else:
                    candidates = by_name if len(by_name) == 1 else []
                if len(candidates) == 1:
                    i = candidates[0]
                    cited.add(i)
                    c["ref_indexes"] = [i]
                    findings += cls._count_findings(c, refs[i], i, label)
                elif len(candidates) > 1 or (c["kind"] == "note-author" and len(by_name) > 1):
                    pool = candidates or by_name
                    cited.update(pool)
                    c["ambiguous_ref_indexes"] = pool
                    findings.append(finding("C-AMBIGUOUS", "error", label, "Varias obras del mismo autor coinciden: usar autor + título corto.", pool[0], candidates=pool))
                elif by_name and c.get("title"):
                    findings.append(finding("C-TITLE-MISMATCH", "error", label, f"El autor está en la bibliografía, pero ningún título coincide con «{c['title']}».", by_name[0]))
                elif refs and not synthetic:
                    findings.append(finding("C-ORPHAN", "error", label, "Cita en nota sin entrada en la bibliografía.", None, raw=c["raw"]))
                elif c["kind"] in ("note-short", "note-author") and not any(_same_work(c, f) for f in seen_full):
                    findings.append(finding("C-FIRST-NOTE-SHORT", "error", label,
                                            "Sin bibliografía, la primera cita de cada obra debe ser una nota completa.", None))
                if c["kind"] == "note-full":
                    if any(_same_work(c, f) for f in seen_full):
                        findings.append(finding("C-REPEATED-FULL", "warning", label,
                                                "Obra ya citada en nota completa: usar la forma abreviada (Autor, Título corto, página).", None))
                    seen_full.append(c)
            if c.get("inverted") and not inverted_reported:
                inverted_reported = True
                findings.append(finding("C-NOTE-INVERTED", "warning", label,
                                        "Notas en formato hispano 'Apellido, Nombre: Título': Chicago pone el nombre en orden normal "
                                        "(Barrington Moore Jr., Título). Si el formato es el de la revista, auditá con --no-lint.", None))
            if c.get("untitled_markup"):
                findings.append(finding("C-TITLE-MARKUP", "warning", label,
                                        f"Título sin cursiva ni comillas: «{c['title'][:60]}»; se infirió hasta la primera coma.", None))
            if c.get("authors") and c.get("ref_indexes"):
                by_author.setdefault(fold(c["authors"][0]), []).append(c["ref_indexes"][0])
            if c["note"] != previous_note:
                previous_note, previous_cites = c["note"], []
            previous_cites.append(c)
        uncited = [i for i, r in enumerate(refs) if r["parsed"] and i not in cited and not r.get("synthetic")]
        for i in uncited:
            findings.append(finding("C-UNCITED", "info", refs[i]["raw"][:90],
                                    "Entrada no citada en notas (válido si la bibliografía incluye obras consultadas).", i))
        if cls.stats.get("notes") and not cls.stats.get("anchored") and any(c.get("paragraph") is None for c in cites):
            findings.append(finding("D-NOTES-UNANCHORED", "info", "documento",
                                    "No se encontraron llamadas de nota en el cuerpo: no se puede verificar a qué oración respalda cada nota.", None))
        return findings, uncited

    @classmethod
    def _count_findings(cls, c: dict, ref: dict, i: int, label: str) -> list[dict]:
        """CMOS 18 (13.23): notes name one or two authors; three or more → first + et al."""
        if not c["authors"]:
            return []  # title-only short form (13.37)
        return author_count_findings(c, ref, i, label, cls)

    @staticmethod
    def lint(refs: list[dict], lang: str, has_italic_markup: bool) -> list[dict]:
        return lint_chicago(refs, lang, "notes")


PROFILES = {AuthorDate.NAME: AuthorDate, Notes.NAME: Notes}

