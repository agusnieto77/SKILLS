"""Bindings for audit inputs and occurrence-specific conclusions (stdlib only)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from zotlib import now_iso


def file_sha256(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def json_sha256(value) -> str:
    return text_sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def occurrence(citation: dict, index: int, file: str | None = None) -> dict:
    """Identity is the exact location, not author/year or the cited Zotero item.

    Content has a separate hash so a replacement sentence at the same location
    invalidates its judgement instead of inheriting it.
    """
    location = {"file": file, "origin": citation.get("origin"), "paragraph": citation.get("paragraph"),
                "note": citation.get("note"), "span": citation.get("span"), "citation_index": index,
                **(citation.get("location") or {})}
    content = {k: citation.get(k) for k in ("raw", "context", "quotes", "locator", "ref_indexes", "citekey", "keys")}
    return {"id": json_sha256(location), "location": location, "sha256": json_sha256(content),
            "itemKey": citation.get("itemKey"), "attachmentKey": citation.get("attachmentKey"),
            "item_version": citation.get("item_version"), "attachment_version": citation.get("attachment_version")}


def bound_evidence(binding: dict, previous: dict | None = None) -> dict:
    """Missing bindings in an old report are stale, never assumed equivalent."""
    changed = []
    if previous is not None:
        old = previous.get("binding")
        changed = [k for k in sorted(set(binding) | set(old or {})) if old is None or binding.get(k) != old.get(k)]
        if previous.get("status") == "stale" and not changed:
            changed = ["previous_stale"]
    return {"schema": 1, "checked_at": now_iso(), "binding": binding,
            "status": "stale" if changed else "current", "changed_inputs": changed}


def audit_evidence(data: dict, path: Path, bibliography_paths=(), previous: dict | None = None) -> dict:
    binding = {"manuscript_file": str(path), "manuscript_sha256": file_sha256(path),
               "bibliographies": [{"file": str(p), "sha256": file_sha256(p)} for p in bibliography_paths]}
    for index, citation in enumerate(data.get("citations", [])):
        citation["occurrence"] = occurrence(citation, index, str(path))
    # Includes parsed citations, findings and locations, but not timestamps or the
    # evidence envelope itself. This is a content hash, not a substitute for the
    # exact audit.json byte hash recorded by source_check's CLI.
    binding["audit_content_sha256"] = json_sha256({k: v for k, v in data.items() if k != "evidence"})
    return bound_evidence(binding, previous.get("evidence", {}) if previous is not None else None)
