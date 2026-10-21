"""Style-independent manuscript handling for the citation audit (stdlib only).

Reading (.docx with anchored footnotes, Markdown/Pandoc footnotes, plain text),
reference-section splitting, author-date citation extraction, quote/context
attachment, author-name matching and the lint rules every style shares.
Style-specific parsing and rules live in style_apa.py and style_chicago.py.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zotlib import DOI_RE, PARTICLES, fail, fold, normalize_doi, normalize_isbn, surname_key  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ZOTERO_URI_RE = re.compile(r"zotero\.org/(users|groups)/(\d+|local/\w+)/items/([A-Z0-9]{8})")
NOTE_MARK_RE = re.compile(r"\[\^([\w-]+)\]")

REF_HEADING_RE = re.compile(
    r"^(referencias(\s+bibliogr[aá]ficas)?|lista\s+de\s+referencias|bibliograf[ií]a(\s+(citada|consultada))?|"
    r"references|reference\s+list|bibliography|works\s+cited|obras\s+citadas|"
    r"fuentes(\s+(y\s+bibliograf[ií]a|citadas|consultadas|primarias|secundarias|documentales|ed[ií]tas|in[eé]ditas))?|"
    r"fuentes\s+de\s+archivo|archivos(\s+consultados)?)$",
    re.I,
)
END_HEADING_RE = re.compile(r"^(anexos?|ap[eé]ndices?|appendix|appendices|notas|notes|tablas|figuras)\b", re.I)

YEAR_IN = r"(?:\d{4}[a-z]?(?:/\d{4})?|s\.\s?f\.(?:-?[a-z])?|n\.\s?d\.(?:-?[a-z])?|en\s+prensa|in\s+press|forthcoming)"
YEARS_IN = rf"{YEAR_IN}(?:\s*,\s*{YEAR_IN})*"
NARRATIVE_PAREN_RE = re.compile(rf"^\s*(?P<years>{YEARS_IN})\s*(?:,\s*(?P<loc>.+?))?\s*$", re.I)
# Author-date chunk: "Acha, 2015, p. 61" (APA) or "Acha 2015, 61" (Chicago). The comma is recorded.
CHUNK_RE = re.compile(rf"^(?P<authors>.+?)(?P<comma>,)?\s+(?P<years>{YEARS_IN})\s*(?:,\s*(?P<loc>.+?))?\s*$", re.I)
PREFIX_RE = re.compile(
    r"^(?:(?:v[eé]ase(?:\s+tambi[eé]n)?|ver|cf\.|cfr\.|e\.\s?g\.,?|p\.\s?ej\.,?|por\s+ejemplo,?|see(?:\s+also)?|tambi[eé]n)\s+)+",
    re.I,
)
SECONDARY_RE = re.compile(r",?\s*(?:como\s+se\s+cita\s+en|citad[oa]\s+en|as\s+cited\s+in|quoted\s+in)\s+", re.I)
LEADING_STOPWORDS = {
    "en", "la", "el", "los", "las", "lo", "un", "una", "según", "segun", "como", "para", "por", "desde", "ver",
    "véase", "vease", "tanto", "mientras", "aunque", "si", "pero", "the", "in", "as", "for", "see", "while",
    "although", "however", "sin", "embargo", "asimismo", "luego", "también", "tambien", "así", "asi", "cf",
}
CONNECTORS = {"y", "e", "and", "&", ","}
URL_RE = re.compile(r"https?://\S+")
ISBN_RE = re.compile(r"ISBN(?:-1[03])?:?\s*([\dXx][\dXx\- ]{8,16}[\dXx])")
ABBREV_END_RE = re.compile(
    r"(?:\b(?:al|p|pp|ed|eds|cf|cfr|vol|vols|núm|nro|n|no|s|f|ff|cap|párr|dr|sr|sra|op|cit|ibid|ibíd|ca|e\.g|i\.e|[A-ZÁÉÍÓÚÑ])\.)$", re.I)
QUOTE_RE = re.compile(r"“([^”]+)”|«([^»]+)»|\"([^\"]+)\"")
PAGE_ONLY_RE = re.compile(r"\((?:p|pp|párr|f|ff)\.\s*[^()]{1,30}\)")


def finding(rule: str, severity: str, subject: str, message: str, ref_index, **extra) -> dict:
    return {"rule": rule, "severity": severity, "subject": subject, "message": message, "ref_index": ref_index, **extra}


def detect_lang(text: str) -> str:
    words = re.findall(r"[a-záéíóúñ]+", text.lower())
    es = sum(w in {"el", "la", "los", "las", "de", "que", "y", "en", "del", "por", "una", "con"} for w in words)
    en = sum(w in {"the", "of", "and", "to", "in", "is", "that", "for", "with", "as", "by", "an"} for w in words)
    return "es" if es >= en else "en"


# --------------------------------------------------------------------------- reading

def _run_text(run) -> str:
    parts = []
    for el in run:
        if el.tag == W + "t":
            parts.append(el.text or "")
        elif el.tag == W + "tab":
            parts.append("\t")
        elif el.tag in (W + "br", W + "cr"):
            parts.append(" ")
        elif el.tag == W + "noBreakHyphen":
            parts.append("-")
        elif el.tag == W + "footnoteReference":
            parts.append(f"[^{el.get(W + 'id')}]")
        elif el.tag == W + "endnoteReference":
            parts.append(f"[^e{el.get(W + 'id')}]")
    return "".join(parts)


def _is_italic(run) -> bool:
    rpr = run.find(W + "rPr")
    if rpr is None:
        return False
    italic = rpr.find(W + "i")
    return italic is not None and italic.get(W + "val", "true") not in ("0", "false", "off")


def _paragraph(p) -> dict:
    pieces: list[list] = []
    for run in p.iter(W + "r"):
        text = _run_text(run)
        if not text:
            continue
        italic = _is_italic(run) and not NOTE_MARK_RE.fullmatch(text)
        if pieces and pieces[-1][1] == italic:
            pieces[-1][0] += text
        else:
            pieces.append([text, italic])
    text = "".join(_mark_italic(t) if it and t.strip() else t for t, it in pieces)
    style = p.find(f"{W}pPr/{W}pStyle")
    return {"text": text.strip(), "style": style.get(W + "val") if style is not None else None}


def _mark_italic(text: str) -> str:
    """`*...*` around the words; surrounding whitespace stays outside so the plain text is unchanged."""
    core = text.strip()
    start = text.index(core)
    return f"{text[:start]}*{core}*{text[start + len(core):]}"


def _zotero_fields(root) -> list[dict]:
    """Collect live Zotero citation fields (complex and simple fields)."""
    instructions, stack = [], []
    for el in root.iter():
        if el.tag == W + "fldChar":
            kind = el.get(W + "fldCharType")
            if kind == "begin":
                stack.append([])
            elif kind in ("separate", "end") and stack:
                instr = "".join(stack.pop())
                if instr:
                    instructions.append(instr)
        elif el.tag == W + "instrText" and stack:
            stack[-1].append(el.text or "")
        elif el.tag == W + "fldSimple":
            instructions.append(el.get(W + "instr") or "")
    fields = []
    for instr in instructions:
        if "ZOTERO_ITEM" in instr:
            payload = instr[instr.find("{"):instr.rfind("}") + 1]
            keys, plain = [], None
            try:
                data = json.loads(payload)
                plain = (data.get("properties") or {}).get("plainCitation")
                for item in data.get("citationItems", []):
                    uris = item.get("uris") or ([item["uri"]] if item.get("uri") else [])
                    for uri in uris:
                        match = ZOTERO_URI_RE.search(uri or "")
                        if match:
                            keys.append(match.group(3))
            except ValueError:
                keys = [m.group(3) for m in ZOTERO_URI_RE.finditer(instr)]
            fields.append({"type": "citation", "itemKeys": keys, "plainCitation": plain})
        elif "ZOTERO_BIBL" in instr:
            fields.append({"type": "bibliography"})
    return fields


def read_docx(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        body = ET.fromstring(archive.read("word/document.xml"))
        footnotes = ET.fromstring(archive.read("word/footnotes.xml")) if "word/footnotes.xml" in names else None
        endnotes = ET.fromstring(archive.read("word/endnotes.xml")) if "word/endnotes.xml" in names else None
    paragraphs = [_paragraph(p) for p in body.iter(W + "p")]
    notes = []
    for root, tag, prefix in ((footnotes, "footnote", ""), (endnotes, "endnote", "e")):
        if root is None:
            continue
        for note in root.iter(W + tag):
            if note.get(W + "type") in ("separator", "continuationSeparator", "continuationNotice"):
                continue
            text = " ".join(_paragraph(p)["text"] for p in note.iter(W + "p")).strip()
            if text:
                notes.append({"id": f"{prefix}{note.get(W + 'id')}", "text": text})
    fields = _zotero_fields(body)
    for root in (footnotes, endnotes):
        if root is not None:
            fields += _zotero_fields(root)
    return {"paragraphs": [p for p in paragraphs if p["text"]], "notes": notes, "zotero_fields": fields}


def read_text(path: Path) -> dict:
    """Markdown/plain text. Pandoc footnotes (`[^1]` in text, `[^1]: ...` definitions) become anchored notes."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    paragraphs, current = [], []
    for line in text.splitlines():
        # Hanging-indent continuation lines belong to the previous paragraph.
        if line.strip() and (line[:1] in (" ", "\t")) and current:
            current.append(line.strip())
            continue
        if current:
            paragraphs.append(" ".join(current))
            current = []
        if line.strip():
            current = [line.strip()]
    if current:
        paragraphs.append(" ".join(current))
    notes, kept = [], []
    for p in paragraphs:
        definition = re.match(r"^\[\^([\w-]+)\]:\s*(.*)$", p)
        if definition:
            notes.append({"id": definition.group(1), "text": definition.group(2).strip()})
        else:
            kept.append({"text": p, "style": None})
    return {"paragraphs": kept, "notes": notes, "zotero_fields": []}


# --------------------------------------------------------------------------- PDF

NOTE_MARKER_RE = re.compile(r"^\s*(\d{1,3}|[*†‡])\s*$")


def _pdf_runs(el) -> list[tuple[str, bool]]:
    """(text, italic) runs of a pdftohtml <text> element."""
    runs = []

    def walk(node, italic):
        italic = italic or node.tag == "i"
        if node.text:
            runs.append((node.text, italic))
        for child in node:
            walk(child, italic)
            if child.tail:
                runs.append((child.tail, italic))

    walk(el, False)
    return [(html.unescape(t), i) for t, i in runs]


def _pdf_xml(path: Path) -> str:
    tool = shutil.which("pdftohtml")
    if not tool:
        fail("Reading PDF needs Poppler's pdftohtml (bundled with MiKTeX, TeX Live, Git for Windows, or "
             "`apt install poppler-utils`); otherwise convert the PDF to .docx or .txt first.")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "doc"
        proc = subprocess.run([tool, "-xml", "-i", "-q", "-nodrm", "-enc", "UTF-8", str(path), str(out)],
                              capture_output=True, timeout=300)
        xml_path = out.with_suffix(".xml")
        if not xml_path.exists():
            fail(f"pdftohtml could not read {path.name}: {proc.stderr.decode(errors='replace')[:200]}")
        return xml_path.read_text(encoding="utf-8", errors="replace")


def read_pdf(path: Path) -> dict:
    return parse_pdf_xml(_pdf_xml(path), path.name)


def parse_pdf_xml(xml_text: str, name: str = "PDF") -> dict:
    """Body paragraphs and footnotes from a text PDF, using font sizes and positions.

    Body text is the dominant font size; footnote text is slightly smaller; superscript
    digits are note calls in the body and note numbers in the note area. Repeated
    headers/footers and page numbers are dropped, end-of-line hyphenation is joined,
    italics become *...*, and fully italic paragraphs are marked as block quotes.
    """
    root = ET.fromstring(re.sub(r"<!DOCTYPE[^>]*>", "", xml_text))
    sizes = {f.get("id"): float(f.get("size")) for f in root.iter("fontspec")}
    pages = []
    for page in root.iter("page"):
        height = float(page.get("height") or 1200)
        elements = []
        for el in page.iter("text"):
            runs = _pdf_runs(el)
            text = "".join(t for t, _ in runs)
            if not text.strip():
                continue
            elements.append({"top": float(el.get("top")), "left": float(el.get("left")),
                             "width": float(el.get("width") or 0), "height": float(el.get("height")),
                             "size": sizes.get(el.get("font"), 0.0), "runs": runs, "text": text})
        pages.append((height, elements))
    if not any(els for _, els in pages):
        fail(f"{name} has no text layer (scanned PDF?): run OCR first.")
    weight = Counter()
    for _, els in pages:
        for e in els:
            weight[e["size"]] += len(e["text"])
    body_size = weight.most_common(1)[0][0]
    # Headers/footers: same text (digits ignored) at the same height on many pages.
    seen = Counter()
    for _, els in pages:
        for e in els:
            seen[(round(e["top"] / 8), re.sub(r"\d+", "#", e["text"].strip()))] += 1
    repeated = max(2, len(pages) // 2) if len(pages) > 1 else 10**9  # a single page has no running heads

    def kind(e):
        if e["size"] <= body_size * 0.72:
            return "small"
        return "note" if e["size"] < body_size * 0.97 else "body"

    paragraphs, notes, current_note = [], [], None
    para, para_style_chars, last = [], [0, 0], None
    margin = Counter(round(e["left"]) for _, els in pages for e in els if kind(e) == "body").most_common(1)[0][0]
    spacing = []

    def flush():
        nonlocal para, para_style_chars
        if para:
            text = _render_runs(para)
            italic, total = para_style_chars
            style = "Quote" if total and italic / total >= 0.85 and len(text.split()) >= 25 else None
            if text:
                paragraphs.append({"text": text, "style": style})
        para, para_style_chars = [], [0, 0]

    for height, els in pages:
        # Repeated running heads/feet need letters: digit-only text at a fixed height is often a note number.
        kept = [e for e in els if not (re.search(r"[^\W\d_]", e["text"]) and
                                       seen[(round(e["top"] / 8), re.sub(r"\d+", "#", e["text"].strip()))] >= repeated)
                and not (e["text"].strip().isdigit() and kind(e) != "small"
                         and (e["top"] < height * 0.08 or e["top"] > height * 0.9))]
        lines: list[dict] = []
        for e in sorted((e for e in kept if kind(e) != "small"), key=lambda e: (e["top"], e["left"])):
            line = next((ln for ln in lines if abs(ln["top"] - e["top"]) <= 3), None)
            if line is None:
                line = {"top": e["top"], "bottom": e["top"] + e["height"], "items": []}
                lines.append(line)
            line["items"].append(e)
            line["bottom"] = max(line["bottom"], e["top"] + e["height"])
        for e in (e for e in kept if kind(e) == "small"):
            bottom = e["top"] + e["height"]
            line = min((ln for ln in lines if ln["top"] - 3 <= bottom <= ln["bottom"] + 3),
                       key=lambda ln: abs(ln["top"] - e["top"]), default=None)
            if line is None:
                line = {"top": e["top"], "bottom": bottom, "items": []}
                lines.append(line)
            line["items"].append(e)
        lines.sort(key=lambda ln: ln["top"])
        for line in lines:
            items = sorted(line["items"], key=lambda e: e["left"])
            chars = Counter()
            for e in items:
                chars[kind(e)] += len(e["text"].strip())
            line_kind = "note" if chars["note"] > chars["body"] else "body" if chars["body"] else "small"
            if line_kind == "small":
                continue
            runs: list[tuple[str, bool]] = []
            for pos, e in enumerate(items):
                if kind(e) == "small" and NOTE_MARKER_RE.match(e["text"]):
                    marker = e["text"].strip()
                    if line_kind == "note" and pos == 0:
                        current_note = {"id": marker, "runs": []}
                        notes.append(current_note)
                    elif line_kind == "body":
                        runs.append((f"[^{marker}]", False))
                    continue
                previous = items[pos - 1] if pos else None
                if previous is not None and runs and not runs[-1][0].endswith(" ") and not e["text"].startswith(" ") \
                        and e["left"] - (previous["left"] + previous["width"]) > e["size"] * 0.15:
                    runs.append((" ", False))  # separate words that pdftohtml emitted as separate fragments
                runs.extend(e["runs"])
            if line_kind == "note" and current_note is None:
                line_kind = "body"  # note-sized text before any numbered note: front matter, not a footnote
            if line_kind == "note":
                _append_line(current_note["runs"], runs)
                continue
            left = items[0]["left"]
            gap = line["top"] - last if last is not None and last < line["top"] else None
            if gap:
                spacing.append(gap)
            typical = sorted(spacing)[len(spacing) // 2] if spacing else 20
            if para and (left > margin + 10 or (gap and gap > typical * 1.5)):
                flush()
            _append_line(para, runs)
            for text, italic in runs:
                letters = sum(c.isalpha() for c in text)
                para_style_chars[1] += letters
                para_style_chars[0] += letters if italic else 0
            last = line["top"]
        # A new page keeps the paragraph open unless the next line is indented (handled above).
        last = None
    flush()
    out_notes = [{"id": n["id"], "text": _render_runs(n["runs"])} for n in notes]
    return {"paragraphs": paragraphs, "notes": [n for n in out_notes if n["text"]], "zotero_fields": []}


def _append_line(target: list, runs: list[tuple[str, bool]]) -> None:
    """Join a line to the running text: drop end-of-line hyphens before lowercase, else add a space."""
    if not runs:
        return
    if target:
        prev_text, prev_italic = target[-1]
        stripped = prev_text.rstrip()
        first = runs[0][0].lstrip()
        if re.search(r"[^\W\d_]-$", stripped) and not stripped.endswith("--") and first[:1].islower():
            target[-1] = (stripped[:-1], prev_italic)
            runs = [(first, runs[0][1])] + runs[1:]
        elif re.search(r"\d[-–]$", stripped) and first[:1].isdigit():
            target[-1] = (stripped, prev_italic)  # page range split across lines: 81-/146
            runs = [(first, runs[0][1])] + runs[1:]
        elif not prev_text.endswith((" ", "\t")):
            target[-1] = (prev_text + " ", prev_italic)
    target.extend(runs)


def _render_runs(runs: list[tuple[str, bool]]) -> str:
    merged: list[list] = []
    for text, italic in runs:
        if merged and (merged[-1][1] == italic or not text.strip()):
            merged[-1][0] += text
        else:
            merged.append([text, italic])
    out = []
    for text, italic in merged:
        if italic and text.strip():
            lead = text[: len(text) - len(text.lstrip())]
            trail = text[len(text.rstrip()):]
            out.append(f"{lead}*{text.strip()}*{trail}")
        else:
            out.append(text)
    return re.sub(r"\s+", " ", "".join(out)).replace(" *[^", "*[^").strip()


def read_document(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx(path)
    if suffix == ".pdf":
        return read_pdf(path)
    if suffix in (".md", ".markdown", ".txt", ".text", ""):
        return read_text(path)
    fail(f"Unsupported input {suffix!r}: convert to .docx, .pdf, .md or .txt first.")


# --------------------------------------------------------------------------- sections

def _heading_text(paragraph: dict) -> str:
    text = re.sub(r"^#+\s*", "", paragraph["text"]).strip().strip("*_").strip()
    return re.sub(r"^\d+(\.\d+)*\.?\s+", "", text).rstrip(":").strip()


def _is_heading_like(paragraph: dict) -> bool:
    text = paragraph["text"]
    style = (paragraph.get("style") or "").lower()
    return (
        text.startswith("#")
        or "heading" in style
        or "ttulo" in style
        or "titulo" in style
        or (len(text) < 70 and not re.search(r"[.)]$", text) and not re.search(r"\(\d{4}", text))
    )


def _looks_like_reference(text: str) -> bool:
    return bool(re.search(r"\b1[0-9]{3}\b|\b20[0-9]{2}\b|s\.\s?f\.|n\.\s?d\.", text))


def body_text(paragraph: dict) -> str:
    """Word quote styles (Quote, Intense Quote, Cita, Cita destacada) become '> ' block quotes."""
    style = (paragraph.get("style") or "").lower()
    return f"> {paragraph['text']}" if "quote" in style or style.startswith("cita") else paragraph["text"]


def split_sections(paragraphs: list[dict]) -> tuple[list[str], list[dict], str | None]:
    """Return (body paragraphs, reference entries with sub-section, heading).

    Body keeps one slot per paragraph (the reference section left blank), so citation
    `paragraph` indexes and reference `paragraph` indexes both point at the document.
    """
    heads = [i for i, p in enumerate(paragraphs) if _is_heading_like(p) and REF_HEADING_RE.match(_heading_text(p))]
    if not heads:
        return [body_text(p) for p in paragraphs], [], None
    later = [i for i in heads if i >= len(paragraphs) * 0.4]
    start = later[0] if later else heads[-1]
    heading = _heading_text(paragraphs[start])
    body = [body_text(p) for p in paragraphs[:start]] + [""] * (len(paragraphs) - start)
    refs, section = [], heading
    for i in range(start + 1, len(paragraphs)):
        p = paragraphs[i]
        if _is_heading_like(p):
            title = _heading_text(p)
            if END_HEADING_RE.match(title):
                body[i:] = [body_text(q) for q in paragraphs[i:]]
                break
            if REF_HEADING_RE.match(title) or not _looks_like_reference(p["text"]):
                section = title
                continue
        text = re.sub(r"^(?:[-*•]\s+|\d+[.)]\s+)", "", p["text"]).strip()
        refs.append({"text": text, "section": section, "paragraph": i})
    return body, refs, heading


# --------------------------------------------------------------------------- reference helpers

def base_reference(text: str) -> dict:
    """Identifier fields every style shares; style parsers fill the rest."""
    doi = DOI_RE.search(text)
    url = URL_RE.search(text)
    isbn = ISBN_RE.search(text)
    return {"raw": text, "parsed": False, "shape": shape_of(text), "authors": [], "corporate": None, "title": None,
            "title_first": False, "year": None, "etal": False, "kind": "unknown",
            "doi": normalize_doi(doi.group(0)) if doi else None,
            "url": url.group(0).rstrip(".") if url else None,
            "isbn": normalize_isbn(isbn.group(1)) if isbn else None}


APA_HEAD_RE = re.compile(
    r"^(?P<authors>[^«“\"*()]+?)\s*\((?P<date>(?:\d{4}[a-z]?(?:/\d{4})?|\[?ca\.\s?\d{4}\]?|\[\d{4}\??\]|\d{4}[–-]\d{4})"
    r"(?:,\s*[^)]{1,40})?|s\.\s?f\.(?:-?[a-z])?|n\.\s?d\.(?:-?[a-z])?|en\s+prensa|in\s+press)\)\.?\s*(?P<rest>.*)$",
    re.I,
)
AUTHOR_DATE_HEAD_RE = re.compile(
    r"^(?P<authors>[^()]+?)\.\s+(?P<date>\d{4}[a-z]?|\[\d{4}\]\s?\d{4}[a-z]?|n\.\s?d\.(?:-?[a-z])?|s\.\s?f\.(?:-?[a-z])?|"
    r"forthcoming|en\s+prensa)\.\s+(?P<rest>.+)$",
    re.I,
)
TITLE_MARK_RE = re.compile(r"«([^»]+)»|“([^”]+)”|\"([^\"]+)\"|\*([^*]+)\*")


def shape_of(text: str) -> str:
    """Which documentation system a reference entry is written in."""
    if APA_HEAD_RE.match(text):
        return "apa"
    if AUTHOR_DATE_HEAD_RE.match(text):
        return "author-date"
    title = TITLE_MARK_RE.search(text)
    if title and (title.start() == 0 or re.match(r"^[^.«“\"*]+,\s[^.«“\"*]+\.\s", text)):
        return "notes"
    return "unknown"


def first_title(text: str) -> tuple[str | None, int, int]:
    m = TITLE_MARK_RE.search(text)
    if not m:
        return None, -1, -1
    title = next(g for g in m.groups() if g is not None)
    return title.strip().rstrip(".,;:").strip(), m.start(), m.end()


def norm_year(token: str | None) -> str:
    """Comparable year token: '2019a', 'sf', 'sf-a', 'inpress'."""
    token = fold(token or "").replace(" ", "")
    token = token.replace("nd", "sf") if token.startswith("nd") else token
    token = "inpress" if token in ("enprensa", "inpress", "forthcoming") else token
    return token


def ref_sort_keys(ref: dict) -> tuple[str, str]:
    """Sort keys with and without leading particles ('de la Fuente' vs 'Fuente')."""
    first = ref["authors"][0] if ref["authors"] else ref.get("title") or ""
    return fold(first), surname_key(first)


DASH_AUTHOR_RE = re.compile(r"^\s*(?:—{2,}|–{3,}|-{3,}|_{3,})")


def inherit_dash_authors(refs: list[dict]) -> None:
    """'———.' repeats the previous entry's author(s): copy them so order and matching work."""
    for prev, ref in zip(refs, refs[1:], strict=False):
        if DASH_AUTHOR_RE.match(ref["raw"]) and prev["authors"]:
            ref.update(authors=list(prev["authors"]), corporate=prev["corporate"], title_first=False, dash_author=True)


def family_of(display: str) -> str:
    """Family name from 'Given Family' (CMOS non-inverted names); keeps leading particles."""
    tokens = display.strip(" .,").split()
    if len(tokens) <= 1:
        return display.strip(" .,")
    family = [tokens[-1]]
    for token in reversed(tokens[:-1]):
        if token.lower() in PARTICLES - {"y", "e"}:
            family.insert(0, token)
        else:
            break
    return " ".join(family)


# --------------------------------------------------------------------------- author-date citations

def split_names(author_text: str) -> tuple[list[str], bool]:
    etal = bool(re.search(r"\bet\s+al\.?", author_text))
    author_text = re.sub(r",?\s*\bet\s+al\.?", "", author_text).strip(" ,")
    if not author_text:
        return [], etal
    names = [n.strip(" .") for n in re.split(r"\s*(?:,|\s&\s|\sy\s|\se\s|\sand\s)\s*", author_text) if n.strip(" .")]
    return names, etal


def narrative_authors(prefix: str) -> str:
    prefix = NOTE_MARK_RE.sub("", prefix)
    tokens = re.findall(r"et al\.|\[[^\]]+\]|[\w’'\-]+\.?|&|,", prefix)[-14:]
    taken: list[str] = []
    for token in reversed(tokens):
        bare = token.rstrip(".")
        if token == "et al." or token in CONNECTORS or bare.lower() in PARTICLES:
            taken.append(token)
        elif bare[:1].isupper() or token.startswith("["):
            taken.append(token)
        else:
            break
    taken.reverse()
    while taken and (taken[0] in CONNECTORS or taken[0].lower() in PARTICLES - {"de", "del", "van", "von", "da", "di", "dos", "la"}):
        taken.pop(0)
    while taken and taken[0].rstrip(".").lower() in LEADING_STOPWORDS:
        taken.pop(0)
    return " ".join(taken).replace(" ,", ",")


def _sentence_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    left = 0
    for m in re.finditer(r"[.!?…][»”\"]?(?:\[\^[\w-]+\])?\s+", text[:start]):
        if not ABBREV_END_RE.search(text[:m.start() + 1]):
            left = m.end()
    right = len(text)
    for m in re.finditer(r"[.!?…](?:\[\^[\w-]+\])?(?=\s+[A-ZÁÉÍÓÚÑ¿¡“«\"(]|\s*$)", text[end:]):
        if not ABBREV_END_RE.search(text[: end + m.start() + 1]):
            right = end + m.end()
            break
    return left, right


def attach_quotes(text: str, cites: list[dict], previous: list[dict], intro: bool) -> None:
    """Give each citation its sentence and the direct quotes it supports.

    A quote belongs to the nearest citation (or footnote marker) after it in the
    same sentence, else to the nearest one before it (narrative: `Acha (2015)
    sostiene que «...» (p. 61)`). Block quotes need an explicit marker and a page
    locator; with only a locator they belong to the last citation before the
    introducing paragraph.
    """
    for c in cites:
        left, right = _sentence_bounds(text, *c["span"])
        c["context"] = NOTE_MARK_RE.sub("", text[left:right]).strip()
        c["quotes"] = []
    for m in QUOTE_RE.finditer(text):
        quote = next(g for g in m.groups() if g is not None).strip()
        if len(quote.split()) < 4:
            continue
        same = [c for c in cites if _sentence_bounds(text, *c["span"]) == _sentence_bounds(text, m.start(), m.end())]
        after = [c for c in same if c["span"][0] >= m.end()]
        before = [c for c in same if c["span"][1] <= m.start()]
        owners = after[:1] if after else before[-1:]
        # Several citations in one note share its marker: the quote belongs to the first.
        for owner in owners:
            tail = PAGE_ONLY_RE.search(text, m.end())
            locator = owner.get("locator") or (tail.group(0).strip("()") if tail and tail.start() - m.end() < 5 else None)
            owner["quotes"].append({"text": quote, "block": False, "locator": locator})
    if len(text.split()) < 40 or QUOTE_RE.search(text) or not (text.startswith(">") or intro):
        return
    body = NOTE_MARK_RE.sub("", text.lstrip("> ")).strip()
    ending = [c for c in cites if c.get("at_paragraph_end") or len(text.rstrip(". ")) - c["span"][1] <= 1]
    page_tail = PAGE_ONLY_RE.search(text[-40:])
    owner = ending[0] if ending else previous[-1] if previous and page_tail else None
    locator = (owner or {}).get("locator") or (page_tail.group(0).strip("()") if page_tail else None)
    if owner is None or not locator:
        return
    cut = body.rfind("(") if not ending or ending[0].get("origin") != "note" else len(body)
    owner.setdefault("quotes", []).append({"text": body[:cut].strip().rstrip(" .:"), "block": True, "locator": locator})


def find_author_date_citations(paragraphs: list[str], origin: str = "body") -> list[dict]:
    """Parenthetical and narrative author-date citations, APA or Chicago form.

    `comma` records whether the author and year were separated by a comma (APA)
    or not (Chicago); each style decides whether the other form is an error.
    """
    citations, recent, intro = [], [], False
    for index, text in enumerate(paragraphs):
        found = []
        for match in re.finditer(r"\(([^()]*)\)", text):
            content = match.group(1)
            if not re.search(YEAR_IN, content, re.I):
                continue
            span = [match.start(), match.end()]
            narrative = NARRATIVE_PAREN_RE.match(content)
            if narrative:
                authors = narrative_authors(text[: match.start()].rstrip())
                names, etal = split_names(authors)
                if names:
                    abbreviation = re.search(r"\[([A-ZÁÉÍÓÚÑ]{2,})\]", authors)
                    found.append({
                        "kind": "narrative", "authors": names, "etal": etal, "author_text": authors, "comma": None,
                        "abbreviation": abbreviation.group(1) if abbreviation else None,
                        "years": [y.strip() for y in re.findall(YEAR_IN, narrative.group("years"), re.I)],
                        "locator": narrative.group("loc"), "raw": f"{authors} ({content})",
                        "origin": origin, "paragraph": index, "span": span,
                    })
                continue
            for chunk in content.split(";"):
                chunk = PREFIX_RE.sub("", chunk.strip())
                parts = SECONDARY_RE.split(chunk)
                secondary = parts[0] if len(parts) > 1 else None
                chunk = parts[-1]
                parsed = CHUNK_RE.match(chunk)
                if not parsed:
                    continue
                authors = parsed.group("authors").strip()
                if not (authors[:1].isupper() or authors[:1] in "“\"*[«") or len(authors) > 150:
                    continue
                names, etal = split_names(authors)
                abbreviation = re.search(r"\[([A-ZÁÉÍÓÚÑ]{2,})\]", authors)
                found.append({
                    "kind": "parenthetical", "authors": names, "etal": etal, "author_text": authors,
                    "comma": bool(parsed.group("comma")),
                    "abbreviation": abbreviation.group(1) if abbreviation else None,
                    "years": [y.strip() for y in re.findall(YEAR_IN, parsed.group("years"), re.I)],
                    "locator": parsed.group("loc"), "secondary_source": secondary,
                    "raw": f"({chunk.strip()})", "origin": origin, "paragraph": index, "span": span,
                })
        attach_quotes(text, found, recent, intro)
        citations += found
        # An introducing paragraph ("Como advierte Acha (2015):") hands its citation to the block below.
        recent = found or (recent if text.rstrip().endswith(":") else [])
        intro = text.rstrip().endswith(":")
    return citations


# --------------------------------------------------------------------------- matching

def name_matches(citation: dict, ref: dict, abbreviations: dict) -> bool:
    """Match a citation's first author against a reference's first author.

    Tries the whole author text first (corporate names may contain 'y'), then the
    first split name, expanding known [ABBR] forms and trying token suffixes so that
    'Según Marx' or 'Omar Acha' still resolve to 'Marx' / 'Acha'.
    """
    whole = re.sub(r",?\s*\bet\s+al\.?", "", citation.get("author_text") or "").strip(" ,")
    # The whole text only matches by equality (corporate authors containing 'y');
    # suffix matching on it could wrongly hit a later co-author's surname.
    names = [(whole, False)] if whole else []
    names += [(n, True) for n in citation["authors"][:1]]
    for name, allow_suffix in names:
        name = abbreviations.get(name.strip("[] "), name)
        candidate = re.sub(r"\s*\[[^\]]+\]", "", name).strip() or name.strip("[] ")
        if not candidate:
            continue
        if not ref["authors"]:
            title = fold(ref.get("title"))
            if title and title.startswith(fold(candidate)):
                return True
            continue
        first = ref["authors"][0]
        if fold(candidate) == fold(first):
            return True
        if not allow_suffix:
            continue
        tokens = candidate.split()
        for start in range(len(tokens)):
            if surname_key(" ".join(tokens[start:])) == surname_key(first):
                return True
    return False


def abbreviations_of(citations: list[dict]) -> dict:
    return {c["abbreviation"]: re.sub(r"\s*\[[^\]]+\]", "", c["author_text"])
            for c in citations if c.get("abbreviation")}


def crosscheck_author_date(citations: list[dict], refs: list[dict], style) -> tuple[list[dict], list[int]]:
    """Link author-date citations to reference entries by first author + year.

    `style` supplies `foreign_form(citation)` → (rule, severity, message) when the
    citation uses another system's punctuation, `citation_findings` and `label`.
    """
    findings, cited = [], set()
    abbreviations = abbreviations_of(citations)
    for c in citations:
        foreign = style.foreign_form(c)
        for year in c["years"]:
            ny = norm_year(year)
            by_name = [i for i, r in enumerate(refs) if r["parsed"] and name_matches(c, r, abbreviations)]
            exact = [i for i in by_name if norm_year(refs[i]["year"]) == ny]
            base = [i for i in by_name if re.sub(r"[a-z]$", "", norm_year(refs[i]["year"])) == ny]
            label = f"{', '.join(c['authors'])}{' et al.' if c['etal'] else ''}, {year}"
            if foreign and not (exact or base):
                continue  # "(Buenos Aires 1932)" in an APA text is prose, not a citation
            if len(exact) == 1 or (not exact and len(base) == 1):
                i = (exact or base)[0]
                cited.add(i)
                c.setdefault("ref_indexes", []).append(i)
                if foreign:
                    findings.append(finding(foreign[0], foreign[1], label, foreign[2], i))
                findings += author_count_findings(c, refs[i], i, label, style)
                if c.get("secondary_source"):
                    findings.append(finding("C-SECONDARY", "info", label, f"Cita secundaria de '{c['secondary_source']}': solo la fuente secundaria va en la lista.", i))
                findings += style.citation_findings(c, refs[i], i, label)
            elif len(exact) > 1 or len(base) > 1:
                candidates = exact or base
                cited.update(candidates)
                c.setdefault("ambiguous_ref_indexes", []).extend(candidates)
                findings.append(finding("C-AMBIGUOUS", "error", label,
                                        "Varias referencias con mismo autor y año: agregar sufijos a/b en lista y citas.",
                                        candidates[0], candidates=candidates))
            elif by_name:
                years = sorted({refs[i]["year"] or "?" for i in by_name})
                findings.append(finding("C-YEAR-MISMATCH", "error", label, f"Autor presente en la lista con otro año: {', '.join(years)}.", by_name[0]))
            else:
                findings.append(finding("C-ORPHAN", "error", label, "Cita sin entrada en la lista de referencias.", None, raw=c["raw"]))
    uncited = [i for i, r in enumerate(refs) if r["parsed"] and i not in cited]
    for i in uncited:
        findings.append(finding("C-UNCITED", "warning", refs[i]["raw"][:90], "Entrada de la lista sin cita en el texto.", i))
    return findings, uncited


def author_count_findings(c: dict, ref: dict, i: int, label: str, style) -> list[dict]:
    """CMOS 18 (13.23) and APA 7 agree: 1–2 authors named, 3+ → 'First et al.'."""
    n = len(ref["authors"])
    cited_n = 1 if ref["corporate"] else len(c["authors"])
    if not n:
        return []  # title-first entry (no author): nothing to count
    if c["etal"] and n < 3 and not ref.get("etal"):
        return [finding("C-ETAL-MISUSE", "error", label, f"La referencia tiene {n} autor(es); 'et al.' solo corresponde con 3 o más.", i)]
    if cited_n > n and not ref.get("etal"):
        return [finding("C-AUTHOR-COUNT", "error", label, f"La cita nombra {cited_n} autores; la referencia tiene {n}: {', '.join(ref['authors'])}.", i)]
    if not c["etal"] and cited_n >= 3:
        return [finding("C-ETAL-REQUIRED", "error", label, f"{style.label}: con 3+ autores usar 'Primer autor et al.'.", i)]
    if not c["etal"] and (n >= 3 or ref.get("etal")):
        return [finding("C-ETAL-MISSING", "error", label, f"La referencia tiene 3+ autores: citar como '{ref['authors'][0]} et al.'.", i)]
    if not c["etal"] and n == 2 and cited_n == 1:
        return [finding("C-SECOND-AUTHOR", "error", label, f"Obra de 2 autores: citar ambos ({' y '.join(ref['authors'])}).", i)]
    return []


# --------------------------------------------------------------------------- shared lint

def lint_shared(refs: list[dict], *, check_same_year: bool) -> list[dict]:
    """Rules every documentation system shares: DOI as URL, en dashes, punctuation, order."""
    findings = []
    for i, ref in enumerate(refs):
        raw, label = ref["raw"], ref["raw"][:90]
        if not ref["parsed"] or ref.get("synthetic"):
            continue
        before_links = URL_RE.split(raw)[0]
        if re.search(r"\bdoi:\s*10\.|dx\.doi\.org|http://doi\.org", raw, re.I):
            findings.append(finding("R-DOI-FORMAT", "error", label, f"DOI como URL: https://doi.org/{ref['doi'] or '...'}", i))
        if re.search(r"(?<![\d/.])\d+-\d+(?![\d/])", before_links.split(ref["title"] or "\0")[-1]):
            findings.append(finding("R-DASH", "warning", label, "Rangos de páginas con raya corta (en dash): 10–20.", i))
        if not re.search(r"(\.|https?://\S+|\]|10\.\d{4,9}/\S+)$", raw.strip()):
            findings.append(finding("R-FINAL-PERIOD", "warning", label, "La entrada debe terminar en punto (salvo DOI/URL).", i))
        if re.search(r"\.\.(?!\.)|\s,|,,|\.\s\.", raw.replace("...", "")):
            findings.append(finding("R-PUNCT", "warning", label, "Puntuación duplicada o espacio antes de coma.", i))
    parsed = [(i, r) for i, r in enumerate(refs) if r["parsed"] and not r.get("synthetic")]
    for (_, a), (j, b) in zip(parsed, parsed[1:], strict=False):
        (fa, sa), (fb, sb) = ref_sort_keys(a), ref_sort_keys(b)
        if a.get("section") == b.get("section") and fa > fb and sa > sb:
            findings.append(finding("R-ORDER", "error", b["raw"][:90], f"Fuera de orden alfabético (va antes de '{a['raw'][:40]}...').", j))
    if check_same_year:
        groups = defaultdict(list)
        for i, r in parsed:
            groups[(tuple(fold(x) for x in r["authors"]), norm_year(r["year"]))].append(i)
        for idx in groups.values():
            if len(idx) > 1:
                findings.append(finding("R-SAME-AUTHOR-YEAR", "error", refs[idx[0]]["raw"][:90],
                                        "Mismo autor y año: usar sufijos a, b (ordenar por título).", idx[0], candidates=idx))
    return findings
