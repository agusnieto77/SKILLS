#!/usr/bin/env python3
"""Apply manuscript corrections to a .docx as Word tracked changes (stdlib only).

  apply MANUSCRIPT.docx EDITS.json --out REVISED.docx [--author NAME]
  summary REVISED.docx

The input file is never modified. Every correction becomes a revision (insertion,
deletion, italic change) or a comment that the author accepts or rejects in Word;
"Track Changes" is switched on in the output so later edits are recorded as well.
All edits are validated first: if any of them cannot be applied, nothing is written.

Targets use cite_audit's numbering: `paragraph` = index of the non-empty body
paragraph (the `paragraph` field of citations); `note` = footnote id ("3") or
endnote id ("e3"). Text follows the audit convention: `*italic*`, `[^3]` for a
note call, `\\*` for a literal asterisk.

  {"op": "replace", "paragraph": 23, "old": "(Thernstrom 1973)", "new": "(Thernstrom, 1973)"}
  {"op": "replace", "note": "56", "old": "Piva y Santella 2022", "new": "Piva y Santella, 2022"}
  {"op": "rewrite", "paragraph": 205, "new": "Barclay, G. W. (1958). *Techniques of population analysis*. Wiley."}
  {"op": "insert", "after": 230, "new": "Entry missing from the list ..."}
  {"op": "delete", "paragraph": 231}
  {"op": "comment", "paragraph": 205, "comment": "[verificar: editorial]"}

Any edit may carry "comment" (a Word comment on that paragraph); "occurrence"
(1-based) picks one of several matches of `old`. Several edits on one paragraph
apply in file order, each on the result of the previous one.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import io
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citecore import W, _is_italic, _paragraph  # noqa: E402
from zotlib import emit, fail  # noqa: E402

XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
NOTE_TOKEN_RE = re.compile(r"\[\^e?[\w-]+\]")
REVISION_TAGS = {W + t for t in ("ins", "del", "moveFrom", "moveTo", "rPrChange", "pPrChange")}
# Run children the audit reads as text; anything else (field codes, drawings, page-break
# hints, the note number inside a note) is invisible to the audit and always kept.
OBJECT_KEYS = {W + "tab": "\t", W + "br": " ", W + "cr": " ", W + "noBreakHyphen": "-"}
# CT_RPr children that precede <w:i>; Word rejects run properties out of schema order.
RPR_BEFORE_ITALIC = {W + t for t in ("rStyle", "rFonts", "b", "bCs")}
# CT_Settings children that precede <w:trackRevisions>.
SETTINGS_BEFORE_TRACK = {W + t for t in (
    "writeProtection", "view", "zoom", "removePersonalInformation", "removeDateAndTime",
    "doNotDisplayPageBoundaries", "displayBackgroundShape", "printPostScriptOverText",
    "printFractionalCharacterWidth", "printFormsData", "embedTrueTypeFonts", "embedSystemFonts",
    "saveSubsetFonts", "saveFormsData", "mirrorMargins", "alignBordersAndEdges",
    "bordersDoNotSurroundHeader", "bordersDoNotSurroundFooter", "gutterAtTop", "hideSpellingErrors",
    "hideGrammaticalErrors", "activeWritingStyle", "proofState", "formsDesign", "attachedTemplate",
    "linkStyles", "stylePaneFormatFilter", "stylePaneSortMethod", "documentType", "mailMerge",
    "revisionView")}
COMMENTS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
COMMENTS_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
PARTS = {"body": "word/document.xml", "footnote": "word/footnotes.xml", "endnote": "word/endnotes.xml"}


class EditError(Exception):
    pass


# --------------------------------------------------------------------------- XML parts

def _parse(data: bytes) -> ET.Element:
    # Register the part's prefixes so they survive serialization (Word resolves
    # mc:Ignorable="w14 ..." by prefix).
    for _, (prefix, uri) in ET.iterparse(io.BytesIO(data), events=("start-ns",)):
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            pass
    return ET.fromstring(data)


def _serialize(root: ET.Element, original: bytes) -> bytes:
    """Serialize keeping the original XML declaration and root start tag.

    ElementTree drops namespace declarations it does not use itself (those named only
    in mc:Ignorable), so the original root tag is restored and the declarations
    ElementTree hoisted from inner elements are added to it.
    """
    text = ET.tostring(root, encoding="unicode")
    new_head = re.match(r"<[^>]*>", text)
    old_head = re.search(rb"<[^?!][^>]*>", original)
    head = old_head.group(0).decode("utf-8")
    declared = dict(re.findall(r'xmlns:([\w.-]+)="([^"]*)"', head))
    extra = []
    for prefix, uri in re.findall(r'xmlns:([\w.-]+)="([^"]*)"', new_head.group(0)):
        if prefix not in declared:
            extra.append(f' xmlns:{prefix}="{uri}"')
        elif declared[prefix] != uri:
            raise EditError(f"namespace prefix {prefix!r} is bound to two URIs; cannot serialize safely")
    if extra:
        cut = len(head) - (2 if head.endswith("/>") else 1)
        head = head[:cut] + "".join(extra) + head[cut:]
    return original[:old_head.start()] + head.encode("utf-8") + text[new_head.end():].encode("utf-8")


# --------------------------------------------------------------------------- text model

@dataclass
class Atom:
    run: ET.Element
    child: ET.Element
    char: str | None  # one character of a <w:t>; None for whole-element atoms
    key: str | None   # text in the audit convention; None = invisible to the audit
    italic: bool


def _object_key(child: ET.Element) -> str | None:
    if child.tag == W + "footnoteReference":
        return f"[^{child.get(W + 'id')}]"
    if child.tag == W + "endnoteReference":
        return f"[^e{child.get(W + 'id')}]"
    return OBJECT_KEYS.get(child.tag)


def _atoms(p: ET.Element) -> list[Atom]:
    atoms = []
    for run in p.iter(W + "r"):
        italic = _is_italic(run)
        for child in run:
            if child.tag == W + "rPr":
                continue
            if child.tag == W + "t":
                atoms += [Atom(run, child, ch, ch, italic) for ch in child.text or ""]
            else:
                atoms.append(Atom(run, child, None, _object_key(child), False))
    return atoms


def _has_markup(text: str) -> bool:
    return re.search(r"(?<!\\)\*", text) is not None


def parse_marked(text: str, inherit: bool = False) -> list[tuple[str, bool | None]]:
    """Audit text -> [(token, italic)]; a note call `[^3]` is one token.

    With `inherit`, italic is None: the text keeps whatever formatting it already has.
    """
    tokens, italic, i = [], False, 0
    while i < len(text):
        if text.startswith("\\*", i):
            tokens.append(("*", italic))
            i += 2
            continue
        if text[i] == "*":
            italic = not italic
            i += 1
            continue
        note = NOTE_TOKEN_RE.match(text, i)
        if note:
            tokens.append((note.group(0), False))
            i = note.end()
            continue
        tokens.append((text[i], None if inherit else italic))
        i += 1
    if italic:
        raise EditError(f"unbalanced '*' in {text!r} (use \\* for a literal asterisk)")
    return tokens


def _plain(tokens) -> str:
    return "".join(t for t, _ in tokens)


def _shows_italic(token: str) -> bool:
    """Italics are compared only where they are visible: single non-blank characters."""
    return len(token) == 1 and not token.isspace()


def _replace(model: list, old: str, new: str, occurrence: int | None) -> list:
    """Replace one occurrence of `old`; without `*` in old/new the formatting is left as is."""
    old_plain = _plain(parse_marked(old))
    if not old_plain:
        raise EditError("'old' is empty")
    starts, pos = {}, 0
    for i, (token, _) in enumerate(model):
        starts[pos] = i
        pos += len(token)
    starts[pos] = len(model)
    plain = _plain(model)
    hits = [m.start() for m in re.finditer(f"(?={re.escape(old_plain)})", plain)]
    hits = [h for h in hits if h in starts and h + len(old_plain) in starts]
    if not hits:
        raise EditError(f"'old' not found: {old_plain!r} (copy it from the audit text of this paragraph)")
    if occurrence is None and len(hits) > 1:
        raise EditError(f"'old' occurs {len(hits)} times: add \"occurrence\" (1-{len(hits)})")
    index = (occurrence or 1) - 1
    if not 0 <= index < len(hits):
        raise EditError(f"occurrence {occurrence} out of range (1-{len(hits)})")
    a, b = starts[hits[index]], starts[hits[index] + len(old_plain)]
    return model[:a] + parse_marked(new, inherit=not (_has_markup(old) or _has_markup(new))) + model[b:]


def _with_edges(model: list, new: str) -> list:
    """Rewrite keeps the paragraph's leading/trailing blanks, which the audit text strips."""
    lead = 0
    while lead < len(model) and model[lead][0].isspace():
        lead += 1
    trail = len(model)
    while trail > lead and model[trail - 1][0].isspace():
        trail -= 1
    return model[:lead] + parse_marked(new.strip(), inherit=not _has_markup(new)) + model[trail:]


def _check_note_calls(model: list, original: list) -> None:
    calls = {t for t, _ in model if NOTE_TOKEN_RE.fullmatch(t)} - {t for t, _ in original}
    if calls:
        raise EditError(f"cannot create note calls {sorted(calls)}: only existing calls can be kept or deleted")


def _spans(keys: list[str]) -> list[tuple[int, int, str]]:
    """Word-level spans for a readable diff: runs of word characters, every other token alone."""
    spans, i = [], 0
    while i < len(keys):
        j = i + 1
        if len(keys[i]) == 1 and (keys[i].isalnum() or keys[i] == "_"):
            while j < len(keys) and len(keys[j]) == 1 and (keys[j].isalnum() or keys[j] == "_"):
                j += 1
        spans.append((i, j, "".join(keys[i:j])))
        i = j
    return spans


# --------------------------------------------------------------------------- revisions

@dataclass
class Revisor:
    author: str
    date: str
    next_id: int
    comments: list = field(default_factory=list)
    counts: Counter = field(default_factory=Counter)

    def mark(self, tag: str) -> ET.Element:
        self.next_id += 1
        self.counts[tag] += 1
        return ET.Element(W + tag, {W + "id": str(self.next_id), W + "author": self.author, W + "date": self.date})

    # ---- runs

    @staticmethod
    def _rpr(run: ET.Element | None) -> ET.Element | None:
        rpr = run.find(W + "rPr") if run is not None else None
        if rpr is None:
            return None
        rpr = copy.deepcopy(rpr)
        for change in rpr.findall(W + "rPrChange"):
            rpr.remove(change)
        return rpr

    @staticmethod
    def _set_italic(rpr: ET.Element | None, italic: bool) -> ET.Element | None:
        if rpr is None:
            if not italic:
                return None
            rpr = ET.Element(W + "rPr")
        for tag in ("i", "iCs"):
            for el in rpr.findall(W + tag):
                rpr.remove(el)
        if italic:
            index = max((i + 1 for i, el in enumerate(rpr) if el.tag in RPR_BEFORE_ITALIC), default=0)
            rpr.insert(index, ET.Element(W + "i"))
        return rpr

    @staticmethod
    def _content(atoms: list[Atom], deleted: bool) -> list[ET.Element]:
        out, buf, source = [], [], None

        def flush():
            if buf:
                t = ET.Element(W + ("delText" if deleted else "t"), {XML_SPACE: "preserve"})
                t.text = "".join(buf)
                out.append(t)
                buf.clear()

        for atom in atoms:
            if atom.char is not None:
                if atom.child is not source:
                    flush()
                    source = atom.child
                buf.append(atom.char)
            else:
                flush()
                source = None
                out.append(copy.deepcopy(atom.child))
        flush()
        return out

    def _run(self, template: ET.Element, rpr: ET.Element | None, content: list[ET.Element]) -> ET.Element:
        run = ET.Element(W + "r", dict(template.attrib))
        if rpr is not None:
            run.append(rpr)
        run.extend(content)
        return run

    def inserted(self, tokens: list[tuple[str, bool]], base: ET.Element | None) -> ET.Element:
        ins = self.mark("ins")
        groups: list[list] = []
        for token, italic in tokens:
            if NOTE_TOKEN_RE.fullmatch(token):
                raise EditError(f"cannot create note call {token}: only existing calls can be kept or deleted")
            if groups and groups[-1][0] == italic:
                groups[-1][1].append(token)
            else:
                groups.append([italic, [token]])
        for italic, chunk in groups:
            run = ET.Element(W + "r")
            rpr = self._set_italic(self._rpr(base), italic)
            if rpr is not None:
                run.append(rpr)
            for piece in re.split(r"(\t)", "".join(chunk)):
                if piece == "\t":
                    run.append(ET.Element(W + "tab"))
                elif piece:
                    t = ET.SubElement(run, W + "t", {XML_SPACE: "preserve"})
                    t.text = piece
            ins.append(run)
        return ins

    # ---- paragraphs

    def revise(self, p: ET.Element, model: list[tuple[str, bool | None]]) -> list[tuple[str, bool]]:
        """Turn the paragraph into `model` with tracked changes (word-level diff).

        Returns the model with inherited italics (None) resolved, for the self-check.
        """
        atoms = _atoms(p)
        keyed = [a for a in atoms if a.key is not None]
        index = {id(a): k for k, a in enumerate(keyed)}
        old_keys, new_keys = [a.key for a in keyed], [t for t, _ in model]
        old_spans, new_spans = _spans(old_keys), _spans(new_keys)
        if not keyed:
            raise EditError("paragraph has no text runs")
        state = ["keep"] * len(keyed)
        italic_to: dict[int, bool] = {}
        inserts: dict[int, list] = defaultdict(list)
        resolved = list(model)
        char_runs = [a.run if a.char is not None else None for a in keyed]

        def base_run(k: int) -> ET.Element | None:
            # Formatting for inserted text: the nearest real text run, never a note call.
            for j in list(range(min(k, len(keyed) - 1), -1, -1)) + list(range(k + 1, len(keyed))):
                if char_runs[j] is not None:
                    return char_runs[j]
            return None

        def bounds(spans, i1, i2, total):
            start = spans[i1][0] if i1 < len(spans) else total
            return start, (spans[i2 - 1][1] if i2 > i1 else start)

        matcher = difflib.SequenceMatcher(None, [s[2] for s in old_spans], [s[2] for s in new_spans], autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            a, b = bounds(old_spans, i1, i2, len(keyed))
            c, d = bounds(new_spans, j1, j2, len(model))
            if tag == "equal":
                for k, j in zip(range(a, b), range(c, d), strict=True):
                    atom, (token, italic) = keyed[k], model[j]
                    if italic is None:
                        resolved[j] = (token, atom.italic)
                    elif atom.char is not None and _shows_italic(token) and atom.italic != italic:
                        state[k] = "format"
                        italic_to[k] = italic
                continue
            for k in range(a, b):
                state[k] = "delete"
            if d > c:
                anchor = (b if tag == "replace" else a) - 1
                base = base_run(anchor)
                for j in range(c, d):
                    if resolved[j][1] is None:
                        resolved[j] = (resolved[j][0], _is_italic(base) if base is not None else False)
                inserts[anchor] += resolved[c:d]

        # Blanks inside a re-formatted stretch join it: one change per stretch, not per word.
        k = 0
        while k < len(keyed):
            j = k
            while j < len(keyed) and state[j] == "keep" and keyed[j].char is not None and keyed[j].char.isspace():
                j += 1
            if j > k and k > 0 and j < len(keyed) and state[k - 1] == state[j] == "format" \
                    and italic_to[k - 1] == italic_to[j]:
                for blank in range(k, j):
                    state[blank], italic_to[blank] = "format", italic_to[j]
            k = max(j, k + 1)

        if not any(s != "keep" for s in state) and not inserts:
            return resolved

        parents = {child: parent for parent in p.iter() for child in parent}
        by_run: dict[int, list[Atom]] = defaultdict(list)
        runs = []
        for atom in atoms:
            if id(atom.run) not in by_run:
                runs.append(atom.run)
            by_run[id(atom.run)].append(atom)

        for run in runs:
            run_atoms = by_run[id(run)]
            ks = [index[id(a)] for a in run_atoms if id(a) in index]
            touched = any(state[k] != "keep" or k in inserts for k in ks) or (0 in ks and -1 in inserts)
            if not touched:
                continue
            pieces: list = []  # ("atoms", (status, italic), [atoms]) | ("insert", tokens, base run)
            for atom in run_atoms:
                k = index.get(id(atom))
                if k == 0 and -1 in inserts:
                    pieces.append(("insert", inserts.pop(-1), base_run(0)))
                mode = ("keep", None) if k is None else (state[k], italic_to.get(k))
                if pieces and pieces[-1][0] == "atoms" and pieces[-1][1] == mode:
                    pieces[-1][2].append(atom)
                else:
                    pieces.append(("atoms", mode, [atom]))
                if k is not None and k in inserts:
                    pieces.append(("insert", inserts.pop(k), base_run(k)))
            out = []
            for kind, mode, payload in pieces:
                if kind == "insert":
                    out.append(self.inserted(mode, payload))
                    continue
                status, italic = mode
                if status == "keep":
                    out.append(self._run(run, self._rpr(run), self._content(payload, False)))
                elif status == "delete":
                    deletion = self.mark("del")
                    deletion.append(self._run(run, self._rpr(run), self._content(payload, True)))
                    out.append(deletion)
                else:
                    old = self._rpr(run)
                    rpr = self._set_italic(copy.deepcopy(old), italic)
                    change = self.mark("rPrChange")
                    change.append(old if old is not None else ET.Element(W + "rPr"))
                    rpr.append(change)
                    out.append(self._run(run, rpr, self._content(payload, False)))
            parent = parents[run]
            at = list(parent).index(run)
            parent.remove(run)
            for offset, el in enumerate(out):
                parent.insert(at + offset, el)
        return resolved

    def mark_paragraph(self, p: ET.Element, tag: str) -> None:
        """Mark the paragraph mark itself as inserted or deleted."""
        ppr = p.find(W + "pPr")
        if ppr is None:
            ppr = ET.Element(W + "pPr")
            p.insert(0, ppr)
        rpr = ppr.find(W + "rPr")
        if rpr is None:
            rpr = ET.Element(W + "rPr")
            tail = [i for i, el in enumerate(ppr) if el.tag in (W + "sectPr", W + "pPrChange")]
            ppr.insert(tail[0] if tail else len(ppr), rpr)
        rpr.insert(0, self.mark(tag))

    def new_paragraph(self, after: ET.Element, model: list[tuple[str, bool]]) -> ET.Element:
        p = ET.Element(W + "p")
        ppr = after.find(W + "pPr")
        if ppr is not None:
            ppr = copy.deepcopy(ppr)
            for el in list(ppr):
                if el.tag in (W + "sectPr", W + "pPrChange"):
                    ppr.remove(el)
            for rpr in ppr.findall(W + "rPr"):
                for el in list(rpr):
                    if el.tag in REVISION_TAGS:
                        rpr.remove(el)
            p.append(ppr)
        self.counts["paragraph-inserted"] += 1
        self.mark_paragraph(p, "ins")
        base = next((a.run for a in _atoms(after) if a.char is not None), None)
        if model:
            p.append(self.inserted(model, base))
        return p

    def comment(self, p: ET.Element, text: str) -> None:
        self.next_id += 1
        cid = str(self.next_id)
        start = 1 if len(p) and p[0].tag == W + "pPr" else 0
        p.insert(start, ET.Element(W + "commentRangeStart", {W + "id": cid}))
        p.append(ET.Element(W + "commentRangeEnd", {W + "id": cid}))
        ref = ET.SubElement(p, W + "r")
        ET.SubElement(ref, W + "commentReference", {W + "id": cid})
        self.comments.append((cid, text))


# --------------------------------------------------------------------------- views (self-check)

def _view(el: ET.Element, accept: bool, inside_ins=False, inside_del=False):
    for child in el:
        if child.tag == W + "pPr":
            continue
        if child.tag == W + "ins":
            yield from _view(child, accept, True, inside_del)
        elif child.tag == W + "del":
            yield from _view(child, accept, inside_ins, True)
        elif child.tag == W + "r":
            if (accept and inside_del) or (not accept and inside_ins):
                continue
            rpr = child.find(W + "rPr")
            if not accept and rpr is not None and rpr.find(W + "rPrChange") is not None:
                italic = _rpr_italic(rpr.find(f"{W}rPrChange/{W}rPr"))
            else:
                italic = _rpr_italic(rpr)
            for c in child:
                if c.tag in (W + "t", W + "delText"):
                    yield from ((ch, italic) for ch in c.text or "")
                elif _object_key(c) is not None:
                    yield _object_key(c), False
        else:
            yield from _view(child, accept, inside_ins, inside_del)


def _rpr_italic(rpr: ET.Element | None) -> bool:
    italic = rpr.find(W + "i") if rpr is not None else None
    return italic is not None and italic.get(W + "val", "true") not in ("0", "false", "off")


def _same(a: list, b: list) -> bool:
    return len(a) == len(b) and all(
        x[0] == y[0] and (not _shows_italic(x[0]) or x[1] == y[1]) for x, y in zip(a, b, strict=True))


# --------------------------------------------------------------------------- apply

def _blocker(p: ET.Element) -> str | None:
    if any(el.tag in REVISION_TAGS for el in p.iter()):
        return "paragraph already has tracked changes: accept or reject them in Word first"
    if p.find(f".//{W}txbxContent") is not None:
        return "paragraph contains a text box"
    instr = "".join(el.text or "" for el in p.iter(W + "instrText"))
    instr += "".join(el.get(W + "instr", "") for el in p.iter(W + "fldSimple"))
    if "ZOTERO_" in instr:
        return "live Zotero field: correct the item in Zotero and refresh instead"
    return None


def _initials(author: str) -> str:
    return "".join(w[0] for w in re.findall(r"[^\W\d_]+", author)[:3]).upper() or "R"


def _max_id(roots) -> int:
    ids = [int(v) for root in roots for el in root.iter() for k, v in el.attrib.items()
           if k == W + "id" and re.fullmatch(r"-?\d+", v)]
    return max(ids, default=0)


def _comments_part(existing: bytes | None, revisor: Revisor) -> bytes:
    original = existing or (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:comments>')
    root = _parse(original)
    for cid, text in revisor.comments:
        comment = ET.SubElement(root, W + "comment", {W + "id": cid, W + "author": revisor.author,
                                                      W + "date": revisor.date, W + "initials": _initials(revisor.author)})
        for i, line in enumerate(text.split("\n")):
            para = ET.SubElement(comment, W + "p")
            if i == 0:
                ET.SubElement(ET.SubElement(para, W + "r"), W + "annotationRef")
            t = ET.SubElement(ET.SubElement(para, W + "r"), W + "t", {XML_SPACE: "preserve"})
            t.text = line
    return _serialize(root, original)


def _register_comments(rels: bytes, types: bytes) -> tuple[bytes, bytes]:
    rels_text, types_text = rels.decode("utf-8"), types.decode("utf-8")
    if COMMENTS_REL + '"' not in rels_text:
        used = {int(n) for n in re.findall(r'Id="rId(\d+)"', rels_text)}
        rid = f"rId{max(used, default=0) + 1}"
        rels_text = rels_text.replace(
            "</Relationships>", f'<Relationship Id="{rid}" Type="{COMMENTS_REL}" Target="comments.xml"/></Relationships>')
    if 'PartName="/word/comments.xml"' not in types_text:
        types_text = types_text.replace(
            "</Types>", f'<Override PartName="/word/comments.xml" ContentType="{COMMENTS_TYPE}"/></Types>')
    return rels_text.encode("utf-8"), types_text.encode("utf-8")


def _track_revisions(settings: bytes) -> bytes:
    root = _parse(settings)
    if root.find(W + "trackRevisions") is None:
        index = max((i + 1 for i, el in enumerate(root) if el.tag in SETTINGS_BEFORE_TRACK), default=0)
        root.insert(index, ET.Element(W + "trackRevisions"))
    return _serialize(root, settings)


def _targets(roots: dict) -> tuple[list, dict]:
    """Body paragraphs numbered like cite_audit; notes by id ("3", "e3")."""
    body = [p for p in roots["body"].iter(W + "p") if _paragraph(p)["text"]]
    notes = {}
    for kind, prefix in (("footnote", ""), ("endnote", "e")):
        if kind in roots:
            for note in roots[kind].iter(W + kind):
                notes[f"{prefix}{note.get(W + 'id')}"] = [p for p in note.iter(W + "p")]
    return body, notes


def apply(src: Path, edits: list[dict], out: Path, author: str) -> dict:
    if out.resolve() == src.resolve():
        fail("--out must be a new file: the original manuscript is never overwritten.")
    if out.exists():
        fail(f"{out} already exists: choose another --out (nothing is overwritten).")
    with zipfile.ZipFile(src) as archive:
        raw = {name: archive.read(name) for name in archive.namelist()}
    roots = {kind: _parse(raw[part]) for kind, part in PARTS.items() if part in raw}
    body, notes = _targets(roots)
    revisor = Revisor(author, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), _max_id(roots.values()))

    models: dict[int, list] = {}      # id(paragraph) -> target text model
    originals: dict[int, tuple] = {}  # id(paragraph) -> (paragraph, original model)
    deleted, comments, inserts, errors = set(), [], defaultdict(list), []

    def model_of(p):
        if id(p) not in models:
            reason = _blocker(p)
            if reason:
                raise EditError(reason)
            original = [(a.key, a.italic) for a in _atoms(p) if a.key is not None]
            originals[id(p)] = (p, original)
            models[id(p)] = list(original)
        return models[id(p)]

    def body_paragraph(edit, key="paragraph"):
        n = edit.get(key)
        if not isinstance(n, int) or not 0 <= n < len(body):
            raise EditError(f"{key} must be an integer between 0 and {len(body) - 1}")
        return body[n]

    def target(edit):
        if "note" in edit:
            note = notes.get(str(edit["note"]))
            if not note:
                raise EditError(f"note {edit['note']!r} not found")
            return note
        return [body_paragraph(edit)]

    for i, edit in enumerate(edits):
        try:
            op = edit.get("op")
            if op == "insert":
                anchor = body_paragraph(edit, "after")
                if not edit.get("new"):
                    raise EditError("insert needs 'new'")
                model = parse_marked(edit["new"])
                _check_note_calls(model, [])
                inserts[id(anchor)].append((anchor, model, edit.get("comment")))
                continue
            paragraphs = target(edit)
            if op == "replace":
                if "new" not in edit:
                    raise EditError("replace needs 'new'")
                hits = []
                for p in paragraphs:
                    if _plain(parse_marked(edit.get("old", ""))) in _plain(model_of(p)):
                        hits.append(p)
                if len(paragraphs) > 1 and len(hits) > 1:
                    raise EditError("'old' occurs in several paragraphs of this note: make it more specific")
                p = hits[0] if hits else paragraphs[0]
                models[id(p)] = _replace(model_of(p), edit.get("old", ""), edit["new"], edit.get("occurrence"))
                _check_note_calls(models[id(p)], originals[id(p)][1])
            elif op == "rewrite":
                if len(paragraphs) != 1 or "new" not in edit:
                    raise EditError("rewrite needs 'new' and a single-paragraph target")
                p = paragraphs[0]
                models[id(p)] = _with_edges(model_of(p), edit["new"])
                _check_note_calls(models[id(p)], originals[id(p)][1])
            elif op == "delete":
                if "note" in edit:
                    raise EditError("delete works on body paragraphs; to drop a note call, replace it")
                p = paragraphs[0]
                model_of(p)
                deleted.add(id(p))
            elif op == "comment":
                p = paragraphs[0]
                if not edit.get("comment"):
                    raise EditError("comment needs 'comment'")
            else:
                raise EditError(f"unknown op {op!r} (replace, rewrite, insert, delete, comment)")
            if edit.get("comment"):
                comments.append((p, edit["comment"]))
        except EditError as err:
            errors.append({"index": i, "edit": edit, "error": str(err)})
    for pid in deleted:
        p, original = originals[pid]
        if models[pid] != original:
            errors.append({"index": None, "edit": {"paragraph": body.index(p)},
                           "error": "paragraph is both edited and deleted"})
    if errors:
        return {"errors": errors, "written": False,
                "note": "No file was written: fix these edits and run again."}

    for pid, (p, _) in originals.items():
        models[pid] = revisor.revise(p, [] if pid in deleted else models[pid])
        if pid in deleted:
            revisor.mark_paragraph(p, "del")
            revisor.counts["paragraph-deleted"] += 1
    new_paragraphs = []
    parent_of = {child: parent for parent in roots["body"].iter() for child in parent}
    for items in inserts.values():
        anchor = items[0][0]
        parent = parent_of[anchor]
        at = list(parent).index(anchor)
        for offset, (_, model, note) in enumerate(items, start=1):
            p = revisor.new_paragraph(anchor, model)
            parent.insert(at + offset, p)
            new_paragraphs.append((p, model))
            if note:
                comments.append((p, note))
    for p, text in comments:
        revisor.comment(p, text)

    # Self-check: rejecting everything restores the original text; accepting gives the edits.
    for pid, (p, original) in originals.items():
        expected = models[pid]
        if not _same(list(_view(p, False)), original) or not _same(list(_view(p, True)), expected):
            raise EditError(f"internal check failed on paragraph {_paragraph(p)['text'][:80]!r}; nothing written")
    for p, model in new_paragraphs:
        if list(_view(p, False)) or not _same(list(_view(p, True)), model):
            raise EditError("internal check failed on an inserted paragraph; nothing written")

    touched = set(originals) | {id(p) for p, _ in comments} | {id(p) for p, _ in new_paragraphs}
    parts = {PARTS[kind]: _serialize(root, raw[PARTS[kind]]) for kind, root in roots.items()
             if any(id(p) in touched for p in root.iter(W + "p"))}
    if "word/settings.xml" in raw:
        parts["word/settings.xml"] = _track_revisions(raw["word/settings.xml"])
    if revisor.comments:
        parts["word/comments.xml"] = _comments_part(raw.get("word/comments.xml"), revisor)
        rels, types = _register_comments(raw["word/_rels/document.xml.rels"], raw["[Content_Types].xml"])
        parts["word/_rels/document.xml.rels"], parts["[Content_Types].xml"] = rels, types
    try:
        with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                zout.writestr(info, parts.pop(info.filename, None) or raw[info.filename], compress_type=info.compress_type)
            for name, data in parts.items():
                zout.writestr(name, data)
    except BaseException:
        out.unlink(missing_ok=True)
        raise
    return {"written": True, "out": str(out), "author": author, "date": revisor.date, "edits": len(edits),
            "paragraphs_revised": len(originals), "track_revisions_on": "word/settings.xml" in raw,
            "revisions": _counts(revisor.counts, len(revisor.comments))}


def _counts(counts: Counter, comments: int) -> dict:
    return {"insertions": counts["ins"] - counts["paragraph-inserted"],
            "deletions": counts["del"] - counts["paragraph-deleted"],
            "italic_changes": counts["rPrChange"], "paragraphs_inserted": counts["paragraph-inserted"],
            "paragraphs_deleted": counts["paragraph-deleted"], "comments": comments}


def summary(path: Path) -> dict:
    """Inventory of the revisions and comments in a .docx (report and verification)."""
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        roots = [ET.fromstring(archive.read(PARTS[k])) for k in PARTS if PARTS[k] in names]
        comments = ET.fromstring(archive.read("word/comments.xml")) if "word/comments.xml" in names else None
        settings = archive.read("word/settings.xml") if "word/settings.xml" in names else b""
    counts, authors, paragraphs = Counter(), Counter(), 0
    for root in roots:
        for p in root.iter(W + "p"):
            if any(el.tag in REVISION_TAGS for el in p.iter()):
                paragraphs += 1
            for ppr_rpr in p.findall(f"{W}pPr/{W}rPr"):
                for el in ppr_rpr:
                    if el.tag in (W + "ins", W + "del"):
                        counts["paragraph-inserted" if el.tag == W + "ins" else "paragraph-deleted"] += 1
        for el in root.iter():
            if el.tag in REVISION_TAGS:
                counts[el.tag[len(W):]] += 1
                authors[el.get(W + "author")] += 1
    n_comments = len(comments.findall(W + "comment")) if comments is not None else 0
    return {"file": str(path), "track_revisions_on": b"trackRevisions" in settings,
            "paragraphs_with_revisions": paragraphs, "revisions": _counts(counts, n_comments),
            "authors": dict(authors)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("apply", help="write a copy with the edits as tracked changes")
    p.add_argument("manuscript", type=Path)
    p.add_argument("edits", type=Path, help="JSON list of edits")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--author", default="zotero-citations", help="name shown on each revision and comment")
    p = sub.add_parser("summary", help="count revisions and comments in a .docx")
    p.add_argument("docx", type=Path)
    args = parser.parse_args()
    if args.command == "summary":
        emit(summary(args.docx))
        return
    if args.manuscript.suffix.lower() != ".docx":
        fail("Tracked changes need a .docx manuscript; for .md/.txt deliver a copy plus the edit log.")
    edits = json.loads(args.edits.read_text(encoding="utf-8"))
    if not isinstance(edits, list):
        fail("EDITS.json must be a JSON list of edits.")
    try:
        result = apply(args.manuscript, edits, args.out, args.author)
    except EditError as err:
        fail(str(err))
    emit(result)
    if not result["written"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
