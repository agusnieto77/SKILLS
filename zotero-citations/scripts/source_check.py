#!/usr/bin/env python3
"""Check citations against the full text Zotero has indexed for the cited item.

  check AUDIT_JSON MATCH_JSON [-k 3] [--no-passages]   every matched citation
  quote ITEM_KEY --text "..." [--locator "p. 61"]       one direct quote
  passages ITEM_KEY --query "..." [-k 5]                best passages for a claim

Deterministic checks: direct quotes (exact / exact-with-edits / near / not-found,
with the PDF page when Zotero kept page breaks) and unquoted verbatim copying
(runs of 6+ identical words). The claim-support verdict is left to the agent: the
script only ranks candidate passages (BM25) and returns them with page numbers.

Uses the local Zotero API when available (same rules as zotero_client.py).
"""
from __future__ import annotations

import argparse
import bisect
import difflib
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import bound_evidence, file_sha256, json_sha256, occurrence, text_sha256  # noqa: E402
from zotlib import emit, fail, fold, load_json_file, request  # noqa: E402

USABLE_MATCH = {"exact-doi", "exact-isbn", "strong", "strong-diff"}
TEXT_TYPES = ("application/pdf", "application/epub+zip", "text/html")
VERBATIM_MIN = 6
STOPWORDS = set("""
a al algo ante antes como con contra cual cuando de del desde donde e el ella ellas ellos en entre era es esa ese eso esta
este esto fue ha han hay la las le les lo los mas más me mi muy no nos o otra otro para pero por porque que qué se sea
ser si sí sin sino sobre son su sus también tan tanto te todo todos tras un una uno unos y ya
about after all also an and are as at be been but by can could did do does for from had has have he her his how i if in
into is it its may more most no not of on one or other our over said she should so some such than that the their them
then there these they this those to under up was we were what when which who will with would you
""".split())
# Verbs that only frame a citation ("Acha (2015) sostiene que...") carry no claim content.
REPORTING_VERBS = set("""
afirma afirman sostiene sostienen señala señalan explica explican plantea plantean indica indican advierte advierten
argumenta argumentan propone proponen destaca destacan menciona mencionan observa observan dice dicen escribe escriben
autor autores autora caso otros según
argue argues argued state states stated note notes noted suggest suggests suggested claim claims write writes
author authors
""".split())
QUOTE_CHARS = str.maketrans({"“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "´": "'",
                             "–": "-", "—": "-", "‐": "-", "‑": "-", "\u00a0": " "})


# --------------------------------------------------------------------------- text model

class SourceText:
    """Normalized full text with a map back to original offsets (for page numbers)."""

    def __init__(self, content: str, *, pages_field: str | None = None, total_pages: int | None = None,
                 annotations: list[dict] | None = None):
        self.content = content
        self.norm, self.pos = normalize(content)
        self.tokens = [(m.group(0), m.start()) for m in re.finditer(r"\w+", self.norm)]
        self.folded = [fold(t) for t, _ in self.tokens]
        self.freq = Counter(self.folded)
        self.has_page_breaks = "\f" in content
        self.annotations = annotations or []
        self.page_offset = self._page_offset(pages_field, total_pages)
        self._ngrams: dict | None = None

    def _page_offset(self, pages_field, total_pages) -> int | None:
        """printed page = pdf page + offset, from annotations (exact) or the item's page range."""
        offsets = Counter()
        for a in self.annotations:
            label, index = a.get("pageLabel"), a.get("pageIndex")
            if label and str(label).isdigit() and index is not None:
                offsets[int(label) - (index + 1)] += 1
        if offsets:
            return offsets.most_common(1)[0][0]
        match = re.match(r"\s*(\d+)\s*[-–]\s*(\d+)", pages_field or "")
        if match and total_pages:
            first, last = int(match.group(1)), int(match.group(2))
            span = last - first + 1
            if total_pages == span:
                return first - 1
            if total_pages == span + 1:  # publisher cover page
                return first - 2
        return None

    def page_at(self, norm_index: int) -> dict:
        if not self.has_page_breaks:
            return {"pdf_page": None, "printed_page": None}
        original = self.pos[min(norm_index, len(self.pos) - 1)] if self.pos else 0
        pdf_page = self.content.count("\f", 0, original) + 1
        return {"pdf_page": pdf_page, "printed_page": pdf_page + self.page_offset if self.page_offset is not None else None}

    def excerpt(self, norm_start: int, norm_end: int, pad: int = 160) -> str:
        if not self.pos:
            return ""
        a = self.pos[max(0, min(norm_start, len(self.pos) - 1))]
        b = self.pos[max(0, min(norm_end, len(self.pos) - 1))]
        a, b = max(0, a - pad), min(len(self.content), b + pad)
        while a > 0 and self.content[a - 1].isalnum():
            a -= 1
        while b < len(self.content) and self.content[b].isalnum():
            b += 1
        return re.sub(r"\s+", " ", self.content[a:b]).strip()

    def ngram_index(self) -> dict:
        if self._ngrams is None:
            index = defaultdict(list)
            for i in range(len(self.folded) - VERBATIM_MIN + 1):
                index[tuple(self.folded[i:i + VERBATIM_MIN])].append(i)
            self._ngrams = index
        return self._ngrams


def normalize(text: str) -> tuple[str, list[int]]:
    """Casefold, expand ligatures (NFKC), unify quotes/dashes, join hyphenated line breaks.

    Returns the normalized string and, for every normalized char, its original offset.
    """
    out, pos = [], []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "-\u00ad" and i and text[i - 1].isalpha():
            joined = re.match(r"[-\u00ad][ \t]*\r?\n[ \t]*(?=\w)", text[i:])
            if joined:
                i += joined.end()
                continue
        if ch == "\u00ad":
            i += 1
            continue
        for expanded in unicodedata.normalize("NFKC", ch).translate(QUOTE_CHARS):
            if expanded.isspace():
                if out and out[-1] == " ":
                    continue
                expanded = " "
            for c in expanded.casefold():
                out.append(c)
                pos.append(i)
        i += 1
    return "".join(out), pos


def _tokens(text: str) -> list[str]:
    return [fold(t) for t in re.findall(r"\w+", normalize(text)[0])]


# --------------------------------------------------------------------------- quotes

EDIT_SPLIT_RE = re.compile(r"\s*(?:\[[^\]]*\]|\(\s*(?:\.\.\.|…)\s*\)|\.\.\.|…)\s*")


def _locator_pages(locator: str | None) -> tuple[int, int] | None:
    """'p. 61' / 'pp. 12–14' (APA) or bare '61' / '12–14' (Chicago); paragraphs, notes and folios are not pages."""
    loc = (locator or "").strip()
    match = re.fullmatch(r"(?:pp?\.\s*)?(\d+)(?:\s*[–-]\s*(\d+))?", loc)
    if not match:
        return None
    first = int(match.group(1))
    last = int(match.group(2)) if match.group(2) else first
    if last < first:  # abbreviated range: 112–14 → 112–114
        last = int(str(first)[: len(str(first)) - len(match.group(2))] + match.group(2))
    return (first, last)


def _page_verdict(page: dict, locator: str | None, annotation_label: str | None) -> dict:
    expected = _locator_pages(locator)
    printed = int(annotation_label) if annotation_label and str(annotation_label).isdigit() else page["printed_page"]
    if not expected:
        status = "no-locator" if locator is None else "unparsed-locator"
    elif printed is None:
        # Without a printed-page mapping only the PDF page is known; say so explicitly.
        pdf_page = page.get("pdf_page")
        status = "matches-pdf-page" if pdf_page and expected[0] <= pdf_page <= expected[1] else "unverifiable"
    else:
        status = "consistent" if expected[0] <= printed <= expected[1] else "inconsistent"
    return {**page, "annotation_page_label": annotation_label, "locator": locator, "page_status": status}


def _annotation_label(source: SourceText, segment_norm: str) -> str | None:
    key = fold(segment_norm)
    for a in source.annotations:
        text = fold(a.get("text"))
        if text and len(text) > 15 and (key[:60] in text or text in key):
            return a.get("pageLabel")
    return None


def check_quote(source: SourceText, quote: str, locator: str | None = None) -> dict:
    segments = [s for s in EDIT_SPLIT_RE.split(quote) if len(s.split()) >= 2] or [quote]
    edited = len(segments) > 1 or bool(EDIT_SPLIT_RE.search(quote))
    cursor, first, last = 0, None, None
    for segment in segments:
        needle = normalize(segment)[0].strip(" .,;:\"'")
        hit = source.norm.find(needle, cursor)
        if hit < 0 or (first is not None and hit - last > 3000):
            break
        first = hit if first is None else first
        last = hit + len(needle)
        cursor = last
    else:
        label = _annotation_label(source, normalize(segments[0])[0])
        return {"status": "exact-with-edits" if edited else "exact", "similarity": 1.0,
                "source_excerpt": source.excerpt(first, last, pad=60),
                **_page_verdict(source.page_at(first), locator, label)}
    return _fuzzy_quote(source, " ".join(segments), locator)


def _fuzzy_quote(source: SourceText, quote: str, locator: str | None) -> dict:
    q = _tokens(quote)
    if not q or not source.folded:
        return {"status": "not-found", "similarity": 0.0}
    anchors = sorted({t for t in q if len(t) >= 4}, key=lambda t: source.freq.get(t, 0) or 10**9)[:3]
    starts = set()
    for anchor in anchors:
        offset = q.index(anchor)
        for i, token in enumerate(source.folded):
            if token == anchor:
                starts.add(max(0, i - offset))
            if len(starts) > 300:
                break
    # Similarity = share of the quote's words found in order in the source window, in
    # runs of 3+ words (isolated function words would inflate it; SequenceMatcher.ratio()
    # would be dragged down by the window padding).
    best = (0.0, None)
    for start in starts:
        window = source.folded[start:start + len(q) + 3]
        blocks = difflib.SequenceMatcher(None, q, window, autojunk=False).get_matching_blocks()
        matched = sum(b.size for b in blocks if b.size >= min(3, len(q)))
        if matched / len(q) > best[0]:
            best = (matched / len(q), start)
    ratio, start = best
    if start is None:
        return {"status": "not-found", "similarity": round(ratio, 3)}
    window = source.folded[start:start + len(q) + 3]
    matcher = difflib.SequenceMatcher(None, q, window, autojunk=False)
    longest = max((b.size for b in matcher.get_matching_blocks()), default=0)
    norm_start = source.tokens[start][1]
    norm_end = source.tokens[min(start + len(q), len(source.tokens) - 1)][1]
    if ratio < 0.6:
        # A long run of the quote is in the source but the rest is not: quote spliced,
        # continued from memory, or partly invented. Report where it diverges.
        if longest >= max(8, int(0.3 * len(q))):
            block = max(matcher.get_matching_blocks(), key=lambda b: b.size)
            return {"status": "partial", "similarity": round(ratio, 3), "matched_words": longest,
                    "quote_words": len(q), "diverges_after": " ".join(q[max(0, block.a + block.size - 6):block.a + block.size]),
                    "source_excerpt": source.excerpt(norm_start, norm_end, pad=40),
                    **_page_verdict(source.page_at(norm_start), locator, None)}
        return {"status": "not-found", "similarity": round(ratio, 3)}
    # Align the window's end with the quote's end so padding words are not reported:
    # after the last matching block, take as many source words as quote words remain.
    last = [b for b in matcher.get_matching_blocks() if b.size][-1]
    window = window[: last.b + last.size + (len(q) - last.a - last.size)]
    differences = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, q, window, autojunk=False).get_opcodes():
        if op != "equal":
            differences.append({"manuscript": " ".join(q[a1:a2]), "source": " ".join(window[b1:b2])})
    status = "near" if ratio >= 0.85 else "weak"
    return {"status": status, "similarity": round(ratio, 3), "differences": differences[:12],
            "source_excerpt": source.excerpt(norm_start, norm_end, pad=40),
            **_page_verdict(source.page_at(norm_start), locator, None)}


# --------------------------------------------------------------------------- verbatim copying

def strip_citation_and_quotes(context: str) -> str:
    text = re.sub(r"“[^”]*”|«[^»]*»|\"[^\"]*\"", " ", context)
    return re.sub(r"\([^()]*\d{4}[^()]*\)|\((?:p|pp)\.[^()]*\)", " ", text)


def find_verbatim(source: SourceText, text: str) -> list[dict]:
    claim_words = re.findall(r"\w+", text)
    claim = [fold(w) for w in claim_words]
    index = source.ngram_index()
    runs, i = [], 0
    while i <= len(claim) - VERBATIM_MIN:
        hits = index.get(tuple(claim[i:i + VERBATIM_MIN]))
        if not hits:
            i += 1
            continue
        best_len, best_pos = 0, hits[0]
        for pos in hits[:50]:
            length = VERBATIM_MIN
            while i + length < len(claim) and pos + length < len(source.folded) and claim[i + length] == source.folded[pos + length]:
                length += 1
            if length > best_len:
                best_len, best_pos = length, pos
        words = claim[i:i + best_len]
        if sum(w in STOPWORDS for w in words) / len(words) <= 0.6:
            start = source.tokens[best_pos][1]
            end = source.tokens[best_pos + best_len - 1][1]
            runs.append({"phrase": " ".join(claim_words[i:i + best_len]), "words": best_len,
                         "source_excerpt": source.excerpt(start, end, pad=80), **source.page_at(start)})
        i += best_len
    return runs


# --------------------------------------------------------------------------- passages

def _chunks(source: SourceText, target: int = 700) -> list[tuple[int, int]]:
    """Passage spans in normalized offsets; cut at every page break and at line breaks
    once a chunk reaches `target` chars. Boundaries come from the original text, since
    normalization collapses line and page breaks into spaces."""
    content, spans, start = source.content, [], 0
    for m in re.finditer(r"\f|\n", content):
        if m.group() == "\f" or m.start() - start >= target:
            if m.start() > start:
                spans.append((start, m.start()))
            start = m.end()
    if start < len(content):
        spans.append((start, len(content)))
    final = []
    for a, b in spans:  # very long unbroken text: hard-split
        while b - a > target * 2:
            final.append((a, a + target))
            a += target
        final.append((a, b))
    return [(bisect.bisect_left(source.pos, a), bisect.bisect_left(source.pos, b)) for a, b in final]


def rank_passages(source: SourceText, query: str, k: int = 3) -> list[dict]:
    terms = [t for t in _tokens(query) if t not in STOPWORDS and len(t) > 2 and not t.isdigit()]
    if not terms:
        return []
    spans = _chunks(source)
    docs = [[fold(t) for t in re.findall(r"\w+", source.norm[a:b])] for a, b in spans]
    avg = sum(map(len, docs)) / max(1, len(docs))
    df = Counter(t for d in docs for t in set(d))
    scored = []
    for (a, b), doc in zip(spans, docs, strict=True):
        tf = Counter(doc)
        score = 0.0
        for t in set(terms):
            if tf[t]:
                idf = math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(doc) / avg))
        if score > 0:
            scored.append((score, a, b))
    scored.sort(reverse=True)
    return [{"score": round(s, 2), "text": source.excerpt(a, b, pad=0)[:900], **source.page_at(a)} for s, a, b in scored[:k]]


# --------------------------------------------------------------------------- Zotero access

class ZoteroText:
    def __init__(self, source: str):
        from zotero_client import read_base  # shares the local-first selection rules

        self.base, self.headers, self.name = read_base(source)
        self._local_annotations: dict | None = None

    def _get(self, path: str, **params):
        resp = request("GET", self.base + path, params={"format": "json", **params} if "fulltext" not in path else None,
                       headers=self.headers, timeout=60)
        return resp.json() if resp.status == 200 else None

    def annotations(self, attachment: str) -> list[dict]:
        if self.name == "local":
            # The local API does not list annotations as attachment children.
            if self._local_annotations is None:
                grouped = defaultdict(list)
                for a in self._get("/items", itemType="annotation") or []:
                    grouped[a["data"].get("parentItem")].append(a["data"])
                self._local_annotations = grouped
            raw = self._local_annotations.get(attachment, [])
        else:
            raw = [c["data"] for c in self._get(f"/items/{attachment}/children", limit=100) or []
                   if c["data"].get("itemType") == "annotation"]
        result = []
        for a in raw:
            position = a.get("annotationPosition")
            index = json.loads(position).get("pageIndex") if isinstance(position, str) and position.startswith("{") else None
            if a.get("annotationText"):
                result.append({"text": a["annotationText"], "pageLabel": a.get("annotationPageLabel"),
                               "pageIndex": index, "comment": a.get("annotationComment")})
        return result

    def load(self, item_key: str) -> tuple[SourceText | None, dict]:
        item = self._get(f"/items/{item_key}")
        if not item:
            return None, {"status": "item-not-found"}
        item_data = item.get("data", item)
        item_info = {"itemKey": item_key, "item_version": item.get("version", item_data.get("version"))}
        children = self._get(f"/items/{item_key}/children") or []
        attachments = [{**c["data"], "version": c.get("version", c["data"].get("version"))}
                       for c in children if c["data"].get("itemType") == "attachment"
                       and c["data"].get("contentType") in TEXT_TYPES]
        best = None
        for att in attachments:
            data = self._get(f"/items/{att['key']}/fulltext")
            if data and data.get("content") and (best is None or len(data["content"]) > len(best[1]["content"])):
                best = (att, data)
        if not best:
            status = "no-attachment" if not attachments else "not-indexed"
            return None, {"status": status, **item_info, "attachments": [a["key"] for a in attachments]}
        att, data = best
        info = {"status": "ok", **item_info, "attachment": att["key"], "attachmentKey": att["key"],
                "attachment_version": att.get("version"), "source_text_sha256": text_sha256(data["content"]),
                "chars": len(data["content"]),
                "indexedPages": data.get("indexedPages"), "totalPages": data.get("totalPages")}
        if data.get("indexedPages") and data.get("totalPages") and data["indexedPages"] < data["totalPages"]:
            info["partial_index"] = True
        source = SourceText(data["content"], pages_field=item["data"].get("pages"), total_pages=data.get("totalPages"),
                            annotations=self.annotations(att["key"]))
        info["page_breaks"] = source.has_page_breaks
        info["page_offset"] = source.page_offset
        return source, info


# --------------------------------------------------------------------------- commands

def check(audit: dict, matches: dict, provider, k: int, passages: bool, *, previous: dict | None = None,
          input_hashes: dict | None = None) -> dict:
    from citecore import detect_lang

    key_of = {m["index"]: m["best"]["key"] for m in matches.get("matches", [])
              if m.get("best") and m.get("status") in USABLE_MATCH}
    manuscript_lang = audit.get("summary", {}).get("language")
    cache: dict = {}
    results, counts = [], Counter()
    for citation in audit.get("citations", []):
        refs = citation.get("ref_indexes") or []
        out = {"raw": citation["raw"], "paragraph": citation["paragraph"], "origin": citation["origin"],
               "context": citation.get("context")}
        if len(set(refs)) != 1 or refs[0] not in key_of:
            out["status"] = "no-zotero-item" if refs else "unresolved-citation"
            counts[out["status"]] += 1
            results.append(out)
            continue
        key = key_of[refs[0]]
        if key not in cache:
            cache[key] = provider.load(key)
        source, info = cache[key]
        out.update({"itemKey": key, "fulltext": info})
        if source is None:
            out["status"] = "no-fulltext"
            counts["no-fulltext"] += 1
            results.append(out)
            continue
        out["status"] = "checked"
        counts["checked"] += 1
        out["quotes"] = [{"text": q["text"][:300], "block": q["block"], **check_quote(source, q["text"], q.get("locator"))}
                         for q in citation.get("quotes", [])]
        for q in out["quotes"]:
            counts[f"quote-{q['status']}"] += 1
            if q.get("page_status") == "inconsistent":
                counts["quote-page-inconsistent"] += 1
        claim = strip_citation_and_quotes(citation.get("context") or "")
        out["verbatim"] = find_verbatim(source, claim)
        counts["verbatim-runs"] += len(out["verbatim"])
        names = {fold(n) for a in citation.get("authors", []) for n in a.split()}
        content_words = [t for t in _tokens(claim) if t not in STOPWORDS and t not in names and t not in REPORTING_VERBS
                         and len(t) > 2 and not t.isdigit()]
        if passages and len(content_words) < 4:
            out["claim_note"] = "the sentence only frames a quote: the quote check covers it"
        elif passages:
            out["passages"] = rank_passages(source, claim, k)
            source_lang = detect_lang(source.content[:20000])
            out["cross_language"] = bool(manuscript_lang and source_lang != manuscript_lang)
            out["needs_judgement"] = True
        results.append(out)
    evidence = bind_results(results, audit, matches, cache, k, passages, previous, input_hashes)
    return {"source": provider.name, "summary": dict(counts), "results": results, "evidence": evidence,
            "verdicts": "For each `needs_judgement` result decide: fiel | exagerada | parcial | sin respaldo, quoting the "
                        "passage. No full text = no verificable (never 'sin respaldo'). With cross_language, rerun "
                        "`passages` with the claim translated to the source language."}


def bind_results(results: list[dict], audit: dict, matches: dict, sources: dict, k: int, passages: bool,
                 previous: dict | None, input_hashes: dict | None) -> dict:
    """Reuse only a bound judgement for the exact occurrence and unchanged inputs."""
    manuscript = audit.get("evidence", {}).get("binding", {})
    inputs = {"audit_sha256": json_sha256(audit), "match_sha256": json_sha256(matches),
              "manuscript_sha256": manuscript.get("manuscript_sha256"), **(input_hashes or {})}
    manuscript_path = Path(audit["file"]) if audit.get("file") else None
    manuscript_changed = False
    if manuscript_path and manuscript_path.is_file():
        observed = file_sha256(manuscript_path)
        manuscript_changed = observed != inputs["manuscript_sha256"]
        inputs["manuscript_sha256"] = observed
    matched = {m["index"]: m["best"] for m in matches.get("matches", []) if m.get("best")}
    prior = {r.get("evidence", {}).get("binding", {}).get("occurrence", {}).get("id"): r
             for r in (previous or {}).get("results", [])}
    for index, (out, citation) in enumerate(zip(results, audit.get("citations", []), strict=True)):
        here = occurrence(citation, index, audit.get("file"))
        source, info = sources.get(out.get("itemKey"), (None, {}))
        best = matched.get((citation.get("ref_indexes") or [None])[0], {})
        binding = {**inputs, "occurrence": here, "itemKey": out.get("itemKey"),
                   "attachmentKey": info.get("attachmentKey", info.get("attachment")),
                   "item_version": info.get("item_version", best.get("version")),
                   "matched_item_version": best.get("version"), "attachment_version": info.get("attachment_version"),
                   "source_text_sha256": text_sha256(source.content) if source else None,
                   "source_metadata_sha256": json_sha256({"info": info, "annotations": source.annotations if source else [],
                                                         "page_offset": source.page_offset if source else None}),
                   "options": {"k": k, "passages": passages}}
        old = prior.get(here["id"])
        old_evidence = old.get("evidence", {}) if old else ({} if previous is not None else None)
        row_evidence = bound_evidence(binding, old_evidence)
        reusable = all(binding.get(key) is not None for key in
                       ("manuscript_sha256", "itemKey", "attachmentKey", "item_version", "attachment_version", "source_text_sha256"))
        if manuscript_changed or (previous is not None and not reusable):
            row_evidence["status"] = "stale"
            row_evidence["changed_inputs"].append("manuscript_since_audit" if manuscript_changed else "unbound_inputs")
        row_evidence["reusable"] = reusable and not manuscript_changed
        out["evidence"] = row_evidence
        if old and "judgement" in old:
            if row_evidence["status"] == "current" and row_evidence["reusable"]:
                out["judgement"] = old["judgement"]
            else:
                out["previous_judgement"] = old["judgement"]
    binding = {**inputs, "occurrences_sha256": json_sha256([r["evidence"]["binding"] for r in results])}
    overall = bound_evidence(binding, previous.get("evidence", {}) if previous is not None else None)
    if manuscript_changed or any(r["evidence"]["status"] == "stale" for r in results):
        overall["status"] = "stale"
    return overall


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["auto", "local", "web"], default="auto")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check")
    p.add_argument("audit_json"), p.add_argument("match_json")
    p.add_argument("-k", type=int, default=3, help="passages per citation")
    p.add_argument("--no-passages", action="store_true", help="only quotes and verbatim copying")
    p.add_argument("--previous", help="previous fidelity JSON; reuse only unchanged, occurrence-bound judgements")
    p = sub.add_parser("quote")
    p.add_argument("item_key"), p.add_argument("--text", required=True), p.add_argument("--locator")
    p = sub.add_parser("passages")
    p.add_argument("item_key"), p.add_argument("--query", required=True), p.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    provider = ZoteroText(args.source)
    if args.command == "check":
        emit(check(load_json_file(args.audit_json), load_json_file(args.match_json), provider, args.k, not args.no_passages,
                   previous=load_json_file(args.previous) if args.previous else None,
                   input_hashes={"audit_sha256": file_sha256(args.audit_json), "match_sha256": file_sha256(args.match_json)}))
        return
    source, info = provider.load(args.item_key)
    if source is None:
        fail(f"No indexed full text for {args.item_key}: {info['status']}")
    evidence = bound_evidence({"itemKey": args.item_key, "item_version": info.get("item_version"),
                               "attachmentKey": info.get("attachmentKey", info.get("attachment")),
                               "attachment_version": info.get("attachment_version"),
                               "source_text_sha256": text_sha256(source.content),
                               "request_sha256": json_sha256({"command": args.command, "text": getattr(args, "text", None),
                                                             "locator": getattr(args, "locator", None),
                                                             "query": getattr(args, "query", None), "k": getattr(args, "k", None)})})
    if args.command == "quote":
        emit({"fulltext": info, "evidence": evidence, **check_quote(source, args.text, args.locator)})
    else:
        emit({"fulltext": info, "evidence": evidence, "passages": rank_passages(source, args.query, args.k)})


if __name__ == "__main__":
    main()
