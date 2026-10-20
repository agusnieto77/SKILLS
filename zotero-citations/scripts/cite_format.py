#!/usr/bin/env python3
"""Format Zotero items as references and citations (stdlib only).

  render --keys K1,K2 [--style S] [--lang es|en] [--format markdown|text|html]
         [--locators K1:61,K2:12-14] [--ref-connector amp|y]
  styles --search TEXT [--format author-date|note|numeric]   search the Zotero style repository
  match-style --key K --example "reference as the user wants it" [--styles a,b] [--search TEXT]
  template render --template T.json --keys K1,K2 [--locators ...]
  template check --template T.json --key K --expect "example" [--part reference|citation|note_full|note_short]

Styles: apa (APA 7), chicago-author-date, chicago-notes (CMOS 18), or any CSL id
from the Zotero repository (e.g. iso690-author-date-es). Rendering uses Zotero's
citeproc (local API first); official profiles get extra fixes Zotero lacks
(en dashes, Spanish "y" in APA citations, year suffixes, locators).
"""
from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zotero_client import PERIODICAL_TYPES, looks_title_case, read  # noqa: E402
from zotlib import cache_dir, emit, fail, first_author, fold, load_json_file, main_title, request, year_of  # noqa: E402

OFFICIAL = {
    "apa": {"csl": "apa", "family": "author-date", "label": "APA 7"},
    "chicago-author-date": {"csl": "chicago-author-date", "family": "author-date", "label": "Chicago 18.ª (autor-fecha)"},
    "chicago-notes": {"csl": "chicago-notes-bibliography", "short_csl": "chicago-shortened-notes-bibliography",
                      "family": "note", "label": "Chicago 18.ª (notas y bibliografía)"},
}
ALIASES = {"chicago": "chicago-notes", "chicago-notes-bibliography": "chicago-notes", "apa7": "apa"}
CANDIDATES = ["apa", "apa-6th-edition", "chicago-author-date", "chicago-notes-bibliography",
              "chicago-shortened-notes-bibliography", "chicago-author-date-17th-edition", "modern-language-association",
              "harvard-cite-them-right", "iso690-author-date-es", "iso690-full-note-es", "american-sociological-association",
              "american-political-science-association", "ieee"]
STYLES_TTL = 7 * 24 * 3600
YEAR_TOKEN = r"(?:\d{4}[a-z]?|s\.\s?f\.(?:-[a-z])?|n\.\s?d\.(?:-[a-z])?|en prensa|in press)"


# --------------------------------------------------------------------------- style repository

def style_index() -> list[dict]:
    cache = cache_dir() / "styles.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < STYLES_TTL:
        return json.loads(cache.read_text(encoding="utf-8"))
    resp = request("GET", "https://www.zotero.org/styles-files/styles.json", timeout=120)
    if resp.status != 200:
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        fail(f"Could not download the Zotero style index ({resp.status}).")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(resp.text, encoding="utf-8")
    return resp.json()


def search_styles(query: str, fmt: str | None = None, limit: int = 25) -> list[dict]:
    words = fold(query).split()
    hits = []
    for s in style_index():
        haystack = fold(f"{s['title']} {s['name']} {' '.join(s['categories'].get('fields', []))}")
        if all(w in haystack for w in words) and (not fmt or s["categories"]["format"] == fmt):
            hits.append({"name": s["name"], "title": s["title"], "format": s["categories"]["format"],
                         "dependent": bool(s["dependent"]), "updated": s["updated"][:10]})
    return sorted(hits, key=lambda h: (h["dependent"], len(h["title"])))[:limit]


def resolve(style: str) -> dict:
    """Profile for an official name, or a repository/URL CSL with its family from the index."""
    name = ALIASES.get(style, style)
    if name in OFFICIAL:
        return {"name": name, "official": True, **OFFICIAL[name]}
    family = "author-date"
    if not style.startswith("http"):
        known = {s["name"]: s for s in style_index()}
        if name not in known:
            close = difflib.get_close_matches(name, list(known), n=3)
            fail(f"Style {style!r} is not in the Zotero repository" + (f" (did you mean {close}?)" if close else "") +
                 "; use `styles --search`.")
        family = known[name]["categories"]["format"]
        title = known[name]["title"]
    else:
        title = style
    return {"name": name, "official": False, "csl": name, "family": family, "label": title}


# --------------------------------------------------------------------------- text helpers

def html_to(fmt: str, fragment: str) -> str:
    inner = re.sub(r"(?s)^.*?<div class=\"csl-entry\"[^>]*>(.*?)</div>.*$", r"\1", fragment).strip()
    # Ordinal indicators: "n.<sup>o</sup>" is "n.º", not "n.o".
    inner = re.sub(r"<sup>o</sup>", "º", inner)
    inner = re.sub(r"<sup>a</sup>", "ª", inner)
    if fmt == "html":
        return inner
    text = re.sub(r"<span style=\"font-style:normal;?\">(.*?)</span>", r"\1", inner)
    text = re.sub(r"<div class=\"csl-left-margin\">(.*?)</div>", r"\1 ", text)
    marker = "*" if fmt == "markdown" else ""
    text = re.sub(r"</?i>", marker, text)
    text = re.sub(r"</?b>", "**" if fmt == "markdown" else "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def en_dash_ranges(text: str) -> str:
    head, sep, tail = text.partition("http")
    head = re.sub(r"(?<![\w/.])(\d+)-(\d+)(?![\w/])", "\\1\u2013\\2", head)
    return head + sep + tail


def spanish_connectors(citation: str) -> str:
    return re.sub(r",?\s&\s", " y ", citation)


def narrative_from(parenthetical: str, lang: str) -> str:
    """'(Acha, 2015)' (APA) or '(Acha 2015)' (Chicago) → 'Acha (2015)'."""
    inner = parenthetical.strip()
    if inner.startswith("(") and inner.endswith(")"):
        inner = inner[1:-1]
    match = re.match(rf"^(?P<who>.+?),?\s+(?P<when>{YEAR_TOKEN}.*)$", inner)
    if not match:
        return parenthetical
    joiner = " y " if lang == "es" else " and "
    who = re.sub(r",?\s(?:&|y|and)\s", joiner, match.group("who"))
    return f"{who} ({match.group('when')})"


def page_label(locator: str, style: str) -> str:
    loc = en_dash_ranges(locator.strip())
    if style == "apa" and re.fullmatch(r"[\divxlc]+(?:–[\divxlc]+)?", loc, re.I):
        return f"{'pp.' if '–' in loc else 'p.'} {loc}"
    return re.sub(r"^pp?\.\s*", "", loc) if style != "apa" else loc


def with_locator(text: str, locator: str, style: str, part: str) -> str:
    """Insert a page locator the way each official profile prints it."""
    loc = page_label(locator, style)
    if part in ("citation", "narrative"):
        return re.sub(r"\)\s*$", f", {loc})", text, count=1)
    # Notes: a full journal note ends with the article range after ':' — replace it with the cited page.
    body = text.rstrip().rstrip(".")
    if part == "note_full" and re.search(r":\s*[\d–-]+$", body):
        return re.sub(r":\s*[\d–-]+$", f": {loc}", body) + "."
    if body.endswith(f", {loc}"):
        return f"{body}."  # the note already ends with that page (e.g. a one-page item): do not repeat it
    return f"{body}, {loc}."


def quality_flags(data: dict, family: str = "author-date") -> list[str]:
    flags = []
    if family == "note" and not data.get("shortTitle") and len(main_title(data.get("title") or "").split()) > 4:
        flags.append("no Short Title in Zotero: short notes will repeat the full title (CMOS 13.32: up to four words)")
    title = data.get("title") or ""
    if data["itemType"] not in PERIODICAL_TYPES | {"webpage"} and looks_title_case(title):
        flags.append("title stored in Title Case (Zotero practice is sentence case; APA prints it as stored)")
    if title.isupper() and len(title) > 8:
        flags.append("title stored in ALL CAPS")
    if data["itemType"] == "webpage" and re.search(r"\s[-|–]\s[^-|–]{3,}$", title):
        flags.append("webpage title seems to include the site name suffix")
    if not data.get("date"):
        flags.append("no date (renders s. f./n.d.)")
    if not data.get("creators"):
        flags.append("no creators (entry starts with the title)")
    if data["itemType"] == "journalArticle" and not data.get("DOI") and not data.get("url"):
        flags.append("journal article without DOI or URL")
    if data["itemType"] == "bookSection" and re.fullmatch(r"\s*\d+\s*", data.get("pages") or ""):
        flags.append("bookSection 'pages' holds a single page: store the chapter's full range (the cited page goes in "
                     "the citation)")
    required = {"bookSection": "bookTitle", "journalArticle": "publicationTitle", "thesis": "university",
                "conferencePaper": "proceedingsTitle", "webpage": "url"}
    field = required.get(data["itemType"])
    if field and not data.get(field):
        flags.append(f"{data['itemType']} without {field} (entry renders incomplete)")
    return flags


# --------------------------------------------------------------------------- CSL rendering

def fetch(keys: list[str], csl: str, locale: str, source: str) -> tuple[dict, dict, str]:
    """{key: data}, {key: {bib, citation}} rendered by Zotero's citeproc."""
    entries, data_by_key, used = {}, {}, None
    for start in range(0, len(keys), 50):
        chunk = keys[start:start + 50]
        resp, used = read(source, "/items", {"itemKey": ",".join(chunk), "format": "json",
                                             "include": "data,bib,citation", "style": csl, "locale": locale})
        # The local API also returns children (attachments, annotations) for itemKey lookups.
        for item in (i for i in resp.json() if i["key"] in chunk):
            data_by_key[item["key"]] = item["data"]
            entries[item["key"]] = {"bib": item.get("bib", ""), "citation": item.get("citation", "")}
    return data_by_key, entries, used


def year_suffixes(data_by_key: dict, entries: dict, csl: str, locale: str, source: str) -> dict:
    """2015a/2015b only appear when same-author/same-year works are rendered together."""
    groups = defaultdict(list)
    for key, data in data_by_key.items():
        groups[(fold(first_author(data.get("creators"))), year_of(data.get("date")))].append(key)
    suffix = {}
    for (_, year), group in groups.items():
        if len(group) < 2 or not year:
            continue
        resp, _ = read(source, "/items/top", {"itemKey": ",".join(group), "format": "bib", "style": csl, "locale": locale})
        rendered = [html_to("text", f"<div class=\"csl-entry\">{e}</div>")
                    for e in re.findall(r"(?s)<div class=\"csl-entry\"[^>]*>(.*?)</div>", resp.text)]
        for key in group if rendered else []:
            plain = html_to("text", entries[key]["bib"])
            best = max(rendered, key=lambda r: difflib.SequenceMatcher(None, re.sub(rf"\b{year}[a-z]\b", year, r), plain).ratio())
            found = re.search(rf"\b{year}([a-z])\b", best)
            if found:
                suffix[key] = (year, found.group(1))
    return suffix


def render(keys: list[str], *, style: str, lang: str, fmt: str, locators: dict, ref_connector: str, source: str) -> dict:
    profile = resolve(style)
    locale = "es-ES" if lang == "es" else "en-US"
    data_by_key, entries, used = fetch(keys, profile["csl"], locale, source)
    short = fetch(keys, profile["short_csl"], locale, source)[1] if profile.get("short_csl") else {}
    suffix = year_suffixes(data_by_key, entries, profile["csl"], locale, source) if profile["family"] == "author-date" else {}
    out = []
    for key in keys:
        if key not in entries:
            continue
        reference = html_to(fmt, entries[key]["bib"])
        citation = html_to(fmt, f"<div class=\"csl-entry\">{entries[key]['citation']}</div>")
        if key in suffix:
            year, letter = suffix[key]
            reference = re.sub(rf"\b{year}\b(?![a-z])", f"{year}{letter}", reference, count=1)
            citation = re.sub(rf"\b{year}\b(?![a-z])", f"{year}{letter}", citation, count=1)
        if profile["official"]:
            reference, citation = en_dash_ranges(reference), en_dash_ranges(citation)
        if profile["name"] == "apa":
            if ref_connector == "y":
                author_part, sep, rest = reference.partition(" (")
                reference = spanish_connectors(author_part) + sep + rest
            if lang == "es":
                citation = spanish_connectors(citation)
        entry = {"key": key, "itemType": data_by_key[key]["itemType"], "reference": reference,
                 "quality": quality_flags(data_by_key[key], profile["family"])}
        loc = locators.get(key)
        if profile["family"] == "note":
            entry["note_full"] = citation
            if key in short:
                entry["note_short"] = en_dash_ranges(html_to(fmt, f"<div class=\"csl-entry\">{short[key]['citation']}</div>"))
            if loc and profile["official"]:
                entry["note_full_with_locator"] = with_locator(entry["note_full"], loc, profile["name"], "note_full")
                entry["note_short_with_locator"] = with_locator(entry["note_short"], loc, profile["name"], "note_short")
        else:
            entry["citation"] = citation
            if profile["family"] == "author-date":
                entry["narrative"] = narrative_from(citation, lang)
            if loc and profile["official"]:
                entry["citation_with_locator"] = with_locator(citation, loc, profile["name"], "citation")
                entry["narrative_with_locator"] = with_locator(entry["narrative"], loc, profile["name"], "narrative")
        out.append(entry)
    numeric = profile["family"] in ("numeric", "label")
    ordered = out if numeric else sorted(out, key=lambda e: fold(re.sub(r"[*<>«»“”\"]", "", e["reference"])))
    warnings = []
    if locators and not profile["official"]:
        warnings.append("Locators are only inserted for official profiles; add them following the style's own examples.")
    if profile["family"] == "author-date":
        initials = defaultdict(set)
        for data in data_by_key.values():
            for creator in data.get("creators", [])[:1]:
                if creator.get("lastName"):
                    initials[fold(creator["lastName"])].add(fold(creator.get("firstName")))
        warnings += [f"Surname '{name}' appears with different given names {sorted(v)}: if they are different people "
                     "add initials to the in-text citations (APA 8.20, CMOS 13.109); if the same person, unify in Zotero"
                     for name, v in initials.items() if len(v) > 1]
    return {"style": profile["name"], "style_label": profile["label"], "csl": profile["csl"], "family": profile["family"],
            "locale": locale, "source": used, "missing": [k for k in keys if k not in entries], "warnings": warnings,
            "entries": out, "bibliography": [e["reference"] for e in ordered]}


# --------------------------------------------------------------------------- matching an example

def comparable(text: str) -> str:
    text = html_to("text", f"<div class=\"csl-entry\">{text}</div>") if "<" in text else text
    text = re.sub(r"[*_]", "", text).translate(str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"', "‘": "'", "’": "'",
                                                               "–": "-", "—": "-"}))
    return re.sub(r"\s+", " ", text).strip()


def word_diff(produced: str, expected: str) -> list[dict]:
    a, b = produced.split(), expected.split()
    out = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            out.append({"produced": " ".join(a[a1:a2]), "expected": " ".join(b[b1:b2])})
    return out


def match_style(key: str, example: str, styles: list[str], lang: str, source: str) -> dict:
    locale = "es-ES" if lang == "es" else "en-US"
    target = comparable(example)
    results, errors = [], {}
    for csl in styles:
        try:
            _, entries, _ = fetch([key], resolve(csl)["csl"], locale, source)
        except SystemExit:
            errors[csl] = "render failed"
            continue
        if key not in entries:
            errors[csl] = "item not found"
            continue
        best = None
        for part in ("bib", "citation"):
            produced = comparable(entries[key][part])
            ratio = difflib.SequenceMatcher(None, produced, target, autojunk=False).ratio()
            if best is None or ratio > best["similarity"]:
                best = {"style": csl, "part": "reference" if part == "bib" else "citation", "similarity": round(ratio, 3),
                        "produced": produced, "differences": word_diff(produced, target)}
        results.append(best)
    results.sort(key=lambda r: -r["similarity"])
    top = results[0] if results else None
    verdict = "exact" if top and top["similarity"] >= 0.995 else "close" if top and top["similarity"] >= 0.9 else "none"
    ties = [r["style"] for r in results if top and r is not top and r["similarity"] >= top["similarity"] - 0.002]
    next_step = {"exact": "Use this CSL style for the whole manuscript (render --style).",
                 "close": "Show the differences; if the user confirms them as intended, build a template "
                          "(template check) starting from this style's output.",
                 "none": "Build a template from the example (template check) and ask about anything it does not show."}[verdict]
    if ties:
        next_step = (f"{len(ties) + 1} styles produce this {top['part']} equally ({', '.join([top['style'], *ties])}): "
                     "ask the user for an example of the in-text citation or note to tell them apart. " + next_step)
    return {"key": key, "example": example, "verdict": verdict, "best": top, "ties": ties, "ranking": results[:8],
            "errors": errors, "next": next_step}


# --------------------------------------------------------------------------- custom templates

FIELD_SOURCES = {
    "title": ("title", "caseName", "nameOfAct", "subject"),
    "container": ("publicationTitle", "bookTitle", "proceedingsTitle", "websiteTitle", "blogTitle", "forumTitle",
                  "encyclopediaTitle", "dictionaryTitle", "programTitle", "seriesTitle"),
    "publisher": ("publisher", "university", "institution", "repository", "company", "label", "network", "studio",
                  "distributor"),
    "number": ("reportNumber", "number", "billNumber", "patentNumber", "episodeNumber", "archiveID"),
    "type": ("thesisType", "reportType", "manuscriptType", "letterType", "websiteType", "genre", "type", "mapType",
             "artworkMedium"),
    "place": ("place", "eventPlace"),
}
PLACEHOLDER_RE = re.compile(r"\{(\w+)(?::(\w+))?\}")
PRIMARY_CREATORS = ("author", "artist", "cartographer", "programmer", "director", "interviewee", "podcaster", "sponsor",
                    "inventor", "composer", "performer")


def _initials(given: str) -> str:
    return " ".join(f"{p[0]}." for p in re.split(r"[\s.]+", given or "") if p)


def _name(creator: dict, pattern: str) -> str:
    if creator.get("name"):
        return creator["name"]
    family, given = creator.get("lastName", ""), creator.get("firstName", "")
    values = {"family": family, "FAMILY": family.upper(), "given": given, "initials": _initials(given),
              "INITIALS": _initials(given).upper()}
    return PLACEHOLDER_RE.sub(lambda m: values.get(m.group(1), ""), pattern).strip(" ,")


def format_names(creators: list[dict], cfg: dict) -> str:
    if not creators:
        return ""
    first, rest = cfg.get("first", "{family}, {given}"), cfg.get("rest", "{given} {family}")
    limit, keep = cfg.get("max", 99), cfg.get("etal_after", 1)
    shown = creators if len(creators) <= limit else creators[:keep]
    names = [_name(c, first if i == 0 else rest) for i, c in enumerate(shown)]
    if len(creators) > limit:
        return cfg.get("sep", ", ").join(names) + cfg.get("etal", " et al.")
    if len(names) == 1:
        return names[0]
    return cfg.get("sep", ", ").join(names[:-1]) + cfg.get("last", " y ") + names[-1]


def short_names(creators: list[dict], cfg: dict) -> str:
    fams = [c.get("lastName") or c.get("name") or "" for c in creators]
    if not fams:
        return ""
    if len(fams) >= cfg.get("threshold", 3):
        return fams[0] + cfg.get("etal", " et al.")
    return cfg.get("two", " y ").join(fams)


def template_fields(data: dict, template: dict, locator: str | None) -> dict:
    creators = data.get("creators", [])
    primary = [c for c in creators if c.get("creatorType") in PRIMARY_CREATORS] or \
              [c for c in creators if c.get("creatorType") == "editor"]
    editors = [c for c in creators if c.get("creatorType") == "editor"] if primary and primary[0].get("creatorType") != "editor" else []
    fields = {k: next((data.get(f) for f in sources if data.get(f)), "") for k, sources in FIELD_SOURCES.items()}
    doi = (data.get("DOI") or "").strip()
    ed_cfg = template.get("editors", {})
    fields.update(
        authors=format_names(primary, template.get("names", {})),
        authors_short=short_names(primary, template.get("short_names", {})),
        editors=(format_names(editors, ed_cfg) + (ed_cfg.get("suffix_many", " (eds.)") if len(editors) > 1 else
                                                  ed_cfg.get("suffix_one", " (ed.)"))) if editors else "",
        year=year_of(data.get("date")) or template.get("no_date", ""), date=data.get("date", ""),
        short_title=main_title(fields["title"]),
        volume=data.get("volume", ""), issue=data.get("issue", ""), pages=data.get("pages", ""),
        edition=data.get("edition", ""), series=data.get("series", ""), doi=doi,
        doi_url=f"https://doi.org/{doi}" if doi else "", url=data.get("url", ""),
        archive=data.get("archive", ""), archive_location=data.get("archiveLocation", ""),
        call_number=data.get("callNumber", ""), access_date=(data.get("accessDate") or "")[:10],
        locator=locator or "", ISBN=data.get("ISBN", ""),
    )
    return fields


def _apply(value: str, modifier: str | None) -> str:
    if modifier == "upper":
        return value.upper()
    if modifier == "lower":
        return value.lower()
    if modifier == "dash":
        return en_dash_ranges(value)
    if modifier == "cap":
        return value[:1].upper() + value[1:]
    return value


def fill(pattern: str, fields: dict) -> tuple[str, list[str]]:
    """Fill {field[:modifier]} placeholders; drop [optional groups] with an empty placeholder.

    Returns the text and the required (non-optional) placeholders that were empty,
    so missing data is reported instead of silently printing '(): Title'.
    """
    names = {n for n, _ in PLACEHOLDER_RE.findall(pattern)}
    unknown = {n for n in names if n not in fields}
    if unknown:
        fail(f"Unknown template fields {sorted(unknown)}; valid: {sorted(fields)}")

    def group(match: re.Match) -> str:
        inner = match.group(1)
        if any(not fields.get(n) for n, _ in PLACEHOLDER_RE.findall(inner)):
            return ""
        return PLACEHOLDER_RE.sub(lambda m: _apply(str(fields.get(m.group(1), "")), m.group(2)), inner)

    text = re.sub(r"(?<!\\)\[((?:\\.|[^\[\]])*)(?<!\\)\]", group, pattern)
    empty = sorted({m.group(1) for m in PLACEHOLDER_RE.finditer(text) if not fields.get(m.group(1))})
    text = PLACEHOLDER_RE.sub(lambda m: _apply(str(fields.get(m.group(1), "")), m.group(2)), text)
    text = text.replace("\\[", "[").replace("\\]", "]")
    return re.sub(r"\s{2,}", " ", text).strip(), empty


def template_render(template: dict, data: dict, part: str, locator: str | None) -> dict:
    patterns = template.get(part) or {}
    if isinstance(patterns, str):
        patterns = {"*": patterns}
    pattern = patterns.get(data["itemType"]) or patterns.get("*")
    if not pattern:
        return {"text": None, "pattern_for": None, "empty_fields": []}
    text, empty = fill(pattern, template_fields(data, template, locator))
    specific = set(patterns) - {"*"}
    return {"text": text, "empty_fields": empty,
            "pattern_for": data["itemType"] if data["itemType"] in specific else "*" if specific else "all"}


def item_data(keys: list[str], source: str) -> dict:
    data = {}
    for start in range(0, len(keys), 50):
        chunk = keys[start:start + 50]
        resp, _ = read(source, "/items", {"itemKey": ",".join(chunk), "format": "json"})
        data.update({i["key"]: i["data"] for i in resp.json() if i["key"] in chunk})
    return data


def cmd_template(args) -> dict:
    template = load_json_file(args.template)
    locators = parse_locators(args.locators)
    if args.action == "check":
        data = item_data([args.key], args.source).get(args.key)
        if not data:
            fail(f"Item {args.key} not found.")
        result = template_render(template, data, args.part, locators.get(args.key))
        produced = result["text"] or ""
        return {"key": args.key, "part": args.part, "pattern_for": result["pattern_for"], "produced": produced,
                "expected": args.expect, "exact": produced == args.expect,
                "exact_ignoring_italics": comparable(produced) == comparable(args.expect),
                "empty_fields": result["empty_fields"],
                "differences": word_diff(comparable(produced), comparable(args.expect))}
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    data = item_data(keys, args.source)
    parts = [p for p in ("reference", "citation", "note_full", "note_short") if template.get(p)]
    entries, fallback = [], defaultdict(list)
    for key in keys:
        if key not in data:
            continue
        entry = {"key": key, "itemType": data[key]["itemType"]}
        for part in parts:
            result = template_render(template, data[key], part, locators.get(key))
            entry[part] = result["text"]
            if result["empty_fields"]:
                entry.setdefault("empty_fields", {})[part] = result["empty_fields"]
            if result["pattern_for"] == "*":
                fallback[data[key]["itemType"]].append(key)
        entries.append(entry)
    ordered = sorted((e for e in entries if e.get("reference")), key=lambda e: fold(re.sub(r"[*«»“”\"]", "", e["reference"])))
    incomplete = {e["key"]: e["empty_fields"] for e in entries if e.get("empty_fields")}
    return {"template": template.get("name"), "entries": entries, "bibliography": [e["reference"] for e in ordered],
            "missing": [k for k in keys if k not in data],
            "fallback_types": {t: sorted(set(k)) for t, k in fallback.items()},
            "incomplete": incomplete,
            "note": "fallback_types used the '*' pattern and incomplete entries lack required data: ask the user how "
                    "those should look (or mark [verificar]) before delivering."}


# --------------------------------------------------------------------------- cli

def parse_locators(raw: str | None) -> dict:
    out = {}
    for pair in (raw or "").split(","):
        if ":" in pair:
            key, loc = pair.split(":", 1)
            out[key.strip()] = loc.strip()
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["auto", "local", "web"], default="auto")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("render")
    p.add_argument("--keys", required=True)
    p.add_argument("--style", default="apa")
    p.add_argument("--lang", choices=["es", "en"], default="es")
    p.add_argument("--format", choices=["markdown", "text", "html"], default="markdown")
    p.add_argument("--locators", help="KEY:61,KEY2:12-14")
    p.add_argument("--ref-connector", choices=["amp", "y"], default="amp", help="APA only: '&' or 'y' in the list")
    p = sub.add_parser("styles")
    p.add_argument("--search", required=True)
    p.add_argument("--format", choices=["author-date", "note", "numeric", "author", "label"])
    p = sub.add_parser("match-style")
    p.add_argument("--key", required=True)
    p.add_argument("--example", required=True)
    p.add_argument("--styles", help="comma-separated CSL ids to add to the default candidates")
    p.add_argument("--search", help="also try repository styles matching this text (e.g. a journal name)")
    p.add_argument("--lang", choices=["es", "en"], default="es")
    p = sub.add_parser("template")
    p.add_argument("action", choices=["render", "check"])
    p.add_argument("--template", required=True)
    p.add_argument("--keys")
    p.add_argument("--key")
    p.add_argument("--expect")
    p.add_argument("--part", default="reference", choices=["reference", "citation", "note_full", "note_short"])
    p.add_argument("--locators")
    args = parser.parse_args()
    if args.command == "render":
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        emit(render(keys, style=args.style, lang=args.lang, fmt=args.format, locators=parse_locators(args.locators),
                    ref_connector=args.ref_connector, source=args.source))
    elif args.command == "styles":
        emit({"results": search_styles(args.search, args.format)})
    elif args.command == "match-style":
        styles = list(CANDIDATES)
        styles += [s.strip() for s in (args.styles or "").split(",") if s.strip()]
        if args.search:
            styles += [h["name"] for h in search_styles(args.search, limit=8)]
        emit(match_style(args.key, args.example, list(dict.fromkeys(styles)), args.lang, args.source))
    else:
        if args.action == "check" and not (args.key and args.expect):
            fail("template check needs --key and --expect")
        if args.action == "render" and not args.keys:
            fail("template render needs --keys")
        emit(cmd_template(args))


if __name__ == "__main__":
    main()
