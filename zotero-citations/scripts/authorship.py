"""Ordered bibliographic authorship comparison; input metadata is untrusted data."""
from __future__ import annotations

import re

from zotlib import PARTICLES, fold, surname_key

_ETAL = re.compile(r"(?:\s*[,;]?\s*)\bet\s+al\.?\s*$", re.IGNORECASE)


def family_from_display(value: str | None) -> str | None:
    """Preserve a comma-delimited family name or leading surname particles."""
    if not value or not value.strip():
        return None
    if "," in value:
        return value.split(",", 1)[0].strip()
    words = value.split()
    start = len(words) - 1
    while start > 0 and fold(words[start - 1]) in PARTICLES:
        start -= 1
    return " ".join(words[start:])


def author_detail(value: str | dict, *, literal: bool = False) -> dict:
    """Use explicit literal/person fields, never equate a group with a person."""
    if isinstance(value, str):
        return {"literal" if literal else "family": value.strip()}
    if not isinstance(value, dict):
        return {"family": ""}
    if "literal" in value:
        return {"literal": str(value.get("literal") or "").strip()}
    family = value.get("family") or value.get("lastName")
    if family:
        particle = value.get("non-dropping-particle") or ""
        result = {"family": " ".join(p for p in (particle, family) if p).strip()}
        given = value.get("given") or value.get("firstName")
        if given:
            result["given"] = given
        return result
    if "name" in value:
        return {"literal": str(value.get("name") or "").strip()}
    return {"family": ""}


def author_label(value: dict) -> str:
    return value.get("literal") if "literal" in value else value.get("family", "")


def author_details(values: list, details: list | None = None, *, corporate: bool = False) -> list[dict]:
    if details is not None and len(details) == len(values):
        return [author_detail(value) for value in details]
    return [author_detail(value, literal=corporate) for value in values]


def split_truncation(values: list) -> tuple[list, bool]:
    """A terminal et al. is an explicit declaration, not an author to compare."""
    result = list(values)
    if not result or not isinstance(result[-1], str):
        return result, False
    last, count = _ETAL.subn("", result[-1])
    if not count:
        return result, False
    if last.strip():
        result[-1] = last.strip()
    else:
        result.pop()
    return result, True


def _same_author(left: dict, right: dict) -> bool:
    if ("literal" in left) != ("literal" in right):
        return False
    if "literal" in left:
        return bool(fold(left["literal"])) and fold(left["literal"]) == fold(right["literal"])
    a, b = surname_key(left.get("family")), surname_key(right.get("family"))
    if not a or not b:
        return False
    # Retain legacy partial compound surnames without allowing Garcia Lopez to
    # match Garcia Marquez merely because their first element is identical.
    return a == b or f" {a} " in f" {b} " or f" {b} " in f" {a} "


def compare_authorship(left: list, right: list, *, left_details: list | None = None,
                       right_details: list | None = None, left_complete: bool = True,
                       right_complete: bool = True, truncated: bool = False,
                       corporate: bool = False) -> dict:
    left, marker = split_truncation(left)
    right, right_marker = split_truncation(right)
    truncated = truncated or marker
    right_complete = right_complete and not right_marker and bool(right)
    left_complete = left_complete and bool(left)
    a = author_details(left, left_details, corporate=corporate)
    b = author_details(right, right_details)
    diffs, warnings = [], []
    for position, (person, source) in enumerate(zip(a, b, strict=False), 1):
        if not _same_author(person, source):
            diffs.append({"field": "first_author" if position == 1 else "authors", "position": position,
                          "manuscript": author_label(person), "sources": author_label(source),
                          "manuscript_kind": "literal" if "literal" in person else "person",
                          "sources_kind": "literal" if "literal" in source else "person", "severity": "error"})
    if truncated:
        if not left or (right_complete and len(left) >= len(right)):
            diffs.append({"field": "author_truncation", "manuscript": len(left), "sources": len(right),
                          "severity": "error"})
        elif not right_complete:
            warnings.append("La fuente no permite comprobar la truncación declarada de la autoría.")
    elif len(left) != len(right) and ((left_complete and right_complete)
          or (left_complete and len(right) > len(left)) or (right_complete and len(left) > len(right))):
        diffs.append({"field": "author_count", "manuscript": len(left), "sources": len(right), "severity": "error"})
    if not left_complete or not right_complete:
        warnings.append("Autoría incompleta: solo se cotejaron las posiciones disponibles; la cantidad no está validada.")
    return {"agree": not diffs, "complete": left_complete and right_complete,
            "truncated": truncated, "diffs": diffs, "warnings": warnings}
