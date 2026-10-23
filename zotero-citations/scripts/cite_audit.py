#!/usr/bin/env python3
"""Extract, cross-check and lint the citations of a manuscript (stdlib only).

Usage:
  cite_audit.py extract MANUSCRIPT [--style S] [--bib REFERENCES.bib ...]
  cite_audit.py audit MANUSCRIPT [--style S] [--lang es|en] [--no-lint] [--bib REFERENCES.bib ...]

Styles: auto (detect), apa (APA 7), chicago (detect the Chicago variant; notes if
unclear), chicago-notes, chicago-author-date (CMOS 18). --no-lint keeps the
citation↔reference cross-check but skips formatting rules: use it when the user
asked for a custom format (its rules come from the template, not from this script).

Inputs: .docx (anchored notes and live Zotero fields), .pdf, .md/.qmd, .tex,
.txt and .bib (inventory). --bib is repeatable; manuscript-supplied bibliography
paths are never followed. Key-mode audits metadata/usage, not rendered style.
Output is JSON on stdout; every finding carries a rule id.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import style_apa  # noqa: E402
from citecore import (  # noqa: E402
    CHUNK_RE, NOTE_MARK_RE, YEAR_IN, crosscheck_keys, detect_lang, finding, find_key_citations, first_title,
    inherit_dash_authors, load_bibliographies, read_document, read_source, shape_of, split_sections,
)
from evidence import audit_evidence  # noqa: E402
from style_chicago import PROFILES as CHICAGO  # noqa: E402
from zotlib import emit, fail, load_json_file  # noqa: E402

PROFILES = {"apa": style_apa, **CHICAGO}
STYLE_CHOICES = ["auto", "apa", "chicago", *CHICAGO]


# --------------------------------------------------------------------------- detection

def detect_style(body: list[str], notes: list[dict], ref_texts: list[str]) -> dict:
    """Weigh body citations, notes and reference shapes; references count double."""
    signals = Counter()
    for text in body:
        for m in re.finditer(r"\(([^()]*)\)", text):
            for chunk in m.group(1).split(";"):
                parsed = CHUNK_RE.match(chunk.strip())
                if parsed and parsed.group("authors")[:1].isupper() and re.search(YEAR_IN, parsed.group("years")):
                    signals["apa" if parsed.group("comma") else "chicago-author-date"] += 1
    called = {m.group(1) for t in body for m in NOTE_MARK_RE.finditer(t)}
    for note in notes:
        if first_title(note["text"])[0] or re.match(r"^\s*ib[ií]d", note["text"], re.I):
            signals["chicago-notes"] += 2 if note["id"] in called else 1
    for text in ref_texts:
        shape = shape_of(text)
        if shape != "unknown":
            signals[{"apa": "apa", "author-date": "chicago-author-date", "notes": "chicago-notes"}[shape]] += 2
    total = sum(signals.values())
    if not total:
        return {"style": None, "confidence": 0.0, "signals": {}}
    style, score = signals.most_common(1)[0]
    return {"style": style, "confidence": round(score / total, 2), "signals": dict(signals)}


def resolve_style(requested: str, detection: dict) -> tuple[str, str]:
    """(style, how) — how ∈ requested | detected | default."""
    detected = detection["style"]
    if requested in PROFILES:
        return requested, "requested"
    if requested == "chicago":
        chicago = {k: v for k, v in detection["signals"].items() if k.startswith("chicago")}
        if chicago:
            return max(chicago, key=chicago.get), "detected"
        return "chicago-notes", "default"
    return (detected, "detected") if detected else ("apa", "default")


# --------------------------------------------------------------------------- pipeline

def _extract(path: Path, style: str = "auto", bibliography_paths=()) -> dict:
    path = Path(path)
    bibliography_paths = tuple(Path(p) for p in bibliography_paths)
    inventory = path.suffix.lower() == ".bib"
    key_citations = find_key_citations(read_source(path), str(path)) \
        if path.suffix.lower() in (".tex", ".md", ".markdown", ".qmd") else []
    bracketed_keys = any(c["raw"].startswith("[") and c["raw"].endswith("]") for c in key_citations)
    key_mode = inventory or bool(bibliography_paths) or path.suffix.lower() == ".tex" or bracketed_keys
    doc = read_document(path)
    body, ref_paras, heading = split_sections(doc["paragraphs"])
    detection = detect_style(body, doc["notes"], [r["text"] for r in ref_paras])
    name, how = resolve_style(style, detection)
    profile = PROFILES[name]
    if key_mode:
        bibliography = load_bibliographies(((path,) if inventory else ()) + bibliography_paths)
        refs = bibliography["references"]
        citations = key_citations
        synthetic = False
    else:
        refs = [{**profile.parse_reference(r["text"]), "section": r["section"], "index": i, "paragraph": r["paragraph"]}
                for i, r in enumerate(ref_paras)]
        inherit_dash_authors(refs)
        citations = profile.citations(body, doc["notes"])
        synthetic = False
        if not refs:
            refs = profile.synthesize_references(citations)
            synthetic = bool(refs)
    data = {
        "file": str(path), "style": name, "style_label": profile.LABEL, "style_source": how, "style_detection": detection,
        "reference_heading": heading, "references_from_notes": synthetic, "references": refs, "citations": citations,
        "notes_count": len(doc["notes"]), "zotero_fields": doc["zotero_fields"], "body_text": body,
        **({"citation_mode": "keys", "bibliography_paths": [str(p) for p in
             (((path,) if inventory else ()) + bibliography_paths)], "bibliography_inventory": inventory,
            "bibliography_complete": bibliography["complete"], "bibliography_warnings": bibliography["warnings"]}
           if key_mode else {}),
    }
    return data


def extract(path: Path, style: str = "auto", bibliography_paths=(), previous: dict | None = None) -> dict:
    data = _extract(path, style, bibliography_paths)
    data.pop("body_text")
    data["evidence"] = audit_evidence(data, Path(path), data.get("bibliography_paths", ()), previous)
    return data


def audit(path: Path, lang: str | None, style: str = "auto", lint: bool = True, bibliography_paths=(),
          previous: dict | None = None) -> dict:
    data = _extract(path, style, bibliography_paths)
    profile = PROFILES[data["style"]]
    lang = lang or detect_lang(" ".join(data["body_text"])[:20000])
    refs, citations = data["references"], data["citations"]
    key_mode = data.get("citation_mode") == "keys"
    cross, uncited = crosscheck_keys(citations, refs, data.get("bibliography_inventory", False)) if key_mode \
        else profile.crosscheck(citations, refs)
    # Formatting rules of the chosen system; a custom format (--no-lint) only keeps the cross-check.
    format_rules = {"C-IBID", "C-OPCIT", "C-NOTE-INVERTED", "C-TITLE-MARKUP", "C-COMMA-MISSING", "C-COMMA-EXTRA",
                    "C-LOCATOR-FORMAT", "C-AMPERSAND", "C-REPEATED-FULL", "C-ETAL-REQUIRED"}
    findings = [f for f in cross if lint or f["rule"] not in format_rules] + data.get("bibliography_warnings", [])
    if lint and not key_mode:
        findings += profile.lint(refs, lang, any("*" in r["raw"] for r in refs))
    detection = data["style_detection"]
    if data["style_source"] == "requested" and detection["style"] and detection["style"] != data["style"] \
            and detection["confidence"] >= 0.7:
        findings.append(finding("D-STYLE-MISMATCH", "warning", "documento",
                                f"Pediste {profile.LABEL}, pero el manuscrito parece estar en {PROFILES[detection['style']].LABEL}: "
                                "se audita contra lo pedido (convertir es parte del trabajo).", None))
    if data["zotero_fields"]:
        findings.append(finding("D-LIVE-ZOTERO-FIELDS", "info", "documento",
                                "El .docx tiene campos vivos de Zotero: corregir en Zotero y refrescar; no editar el texto de esos campos.", None))
    real = [r for r in refs if not r.get("synthetic")]
    unparsed = sum(1 for r in real if not r["parsed"])
    if not key_mode and real and unparsed / len(real) > 0.3:
        findings.append(finding("D-MIXED-STYLE", "error", "documento",
                                f"{unparsed}/{len(real)} entradas no siguen {profile.LABEL}: posible otra norma o norma mixta.", None))
    if data["references_from_notes"]:
        findings.append(finding("D-REFERENCES-FROM-NOTES", "info", "documento",
                                "Sin bibliografía: se usan las notas completas como referencias (válido en Chicago notas).", None))
    elif not refs:
        severity = "info" if data["style"] == "chicago-notes" else "error"
        findings.append(finding("D-NO-REFERENCES", severity, "documento", "No se encontró la lista de referencias / bibliografía.", None))
    zotero_keys = sorted({k for f in data["zotero_fields"] for k in f.get("itemKeys", [])})
    summary = {
        "style": data["style"], "style_source": data["style_source"], "language": lang, "lint": lint,
        "references": len(refs), "citations": len(citations),
        "orphan_citations": sum(f["rule"] in ("C-ORPHAN", "C-UNDEFINED-KEY") for f in findings),
        "uncited_references": len(uncited),
        "errors": sum(f["severity"] == "error" for f in findings),
        "warnings": sum(f["severity"] == "warning" for f in findings),
        "zotero_field_item_keys": zotero_keys,
        **({"bibliography_complete": data["bibliography_complete"]} if key_mode else {}),
        "by_rule": dict(Counter(f["rule"] for f in findings)),
    }
    if getattr(profile, "stats", None):
        summary["notes"] = dict(profile.stats)
    data.pop("body_text")
    report = {**data, "summary": summary, "findings": findings}
    report["evidence"] = audit_evidence(report, path, data.get("bibliography_paths", bibliography_paths), previous)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("extract", "audit"):
        p = sub.add_parser(name)
        p.add_argument("manuscript")
        p.add_argument("--style", choices=STYLE_CHOICES, default="auto")
        p.add_argument("--bib", action="append", default=[], metavar="BIBLIOGRAPHY",
                       help="bibliografía explícita .bib (repetible); no sigue rutas del manuscrito")
        p.add_argument("--previous", help="auditoría anterior: marca stale si cambió algún input")
        if name == "audit":
            p.add_argument("--lang", choices=["es", "en"], help="manuscript language (default: detect)")
            p.add_argument("--no-lint", action="store_true", help="cross-check only (custom formats)")
    args = parser.parse_args()
    path = Path(args.manuscript)
    if not path.exists():
        fail(f"File not found: {path}")
    for bibliography in args.bib:
        if not Path(bibliography).is_file():
            fail(f"Bibliography not found: {bibliography}")
    previous = load_json_file(args.previous) if args.previous else None
    if args.command == "extract":
        emit(extract(path, args.style, args.bib, previous))
    else:
        emit(audit(path, args.lang, args.style, lint=not args.no_lint, bibliography_paths=args.bib, previous=previous))


if __name__ == "__main__":
    main()
