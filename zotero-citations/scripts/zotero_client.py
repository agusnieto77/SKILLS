#!/usr/bin/env python3
"""Zotero library client for the citation workflow (stdlib only).

Reads use the local Zotero API (desktop app, no rate limit) when available and
fall back to the Web API; writes always go to the Web API. Every write command is
a dry run unless --confirm is passed.

  whoami                                   key owner, access, local API status (key masked)
  search  --doi D | --isbn I | --title T [--author A] [--year Y]
  match   AUDIT_JSON                       match manuscript references against the library
  get     KEY [KEY...]                     editable JSON + version
  template ITEM_TYPE                       empty Zotero JSON for an item type
  check   PAYLOAD_JSON                     validate items against the live Zotero schema
  create  PAYLOAD_JSON [--confirm] [--collection C] [--audit-tags] [--allow-duplicate]
  update  KEY PATCH_JSON --version N [--confirm]
  trash   KEY --version N [--confirm]      move to trash (reversible), never hard-delete

Formatting (references, citations, notes) lives in cite_format.py.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zotlib import (  # noqa: E402
    NON_BIB_TYPES, cache_dir, emit, env, fail, fold, isbns_in, local_base, web_base,
    item_doi, library_prefix, load_json_file, main_title, mask, normalize_doi, normalize_isbn,
    now_iso, request, surname_match, title_similarity, year_match, year_of,
)
from authorship import author_detail, compare_authorship  # noqa: E402

API_HEADERS = {"Zotero-API-Version": "3"}
BATCH = 50
SCHEMA_TTL = 7 * 24 * 3600
PERIODICAL_TYPES = {"journalArticle", "magazineArticle", "newspaperArticle"}
STRUCTURAL_KEYS = {"itemType", "creators", "tags", "collections", "relations", "parentItem", "deleted", "inPublications"}
SECONDARY_CREATORS = {"editor", "seriesEditor", "translator", "contributor", "bookAuthor", "reviewedAuthor", "recipient"}
SNAPSHOT_FORMAT = 3  # bump when summarize() changes so cached snapshots are rebuilt


# --------------------------------------------------------------------------- transport

def web_headers(write: bool = False) -> dict:
    key = env("ZOTERO_API_KEY")
    if not key and write:
        fail("ZOTERO_API_KEY is not set; writes need a key with library write access.")
    return {**API_HEADERS, **({"Zotero-API-Key": key} if key else {})}


_local_ok: bool | None = None


def local_available() -> bool:
    global _local_ok
    if _local_ok is None:
        try:
            resp = request("GET", f"{local_base()}/", headers=API_HEADERS, timeout=2, retries=0)
            _local_ok = resp.status == 200 and resp.header("Zotero-API-Version") == "3"
        except ConnectionError:
            _local_ok = False
    return _local_ok


def read_base(source: str) -> tuple[str, dict, str]:
    """Return (base URL with library prefix, headers, source name)."""
    prefix = library_prefix()
    if source in ("auto", "local") and local_available():
        return f"{local_base()}{prefix}", dict(API_HEADERS), "local"
    if source == "local":
        fail("Local Zotero API unavailable: open Zotero and enable Settings → Advanced → "
             "'Allow other applications on this computer to communicate with Zotero'.")
    return f"{web_base()}{prefix}", web_headers(), "web"


def read(source: str, path: str, params: dict | None = None):
    base, headers, name = read_base(source)
    resp = request("GET", base + path, params=params, headers=headers, timeout=60)
    if resp.status == 400 and name == "local":
        # The local API only serves the logged-in user; another library ID falls back to the web.
        base, headers, name = f"{web_base()}{library_prefix()}", web_headers(), "web"
        resp = request("GET", base + path, params=params, headers=headers, timeout=60)
    if resp.status != 200:
        fail(f"GET {path} via {name} API returned {resp.status}: {resp.text[:300]}")
    return resp, name


# --------------------------------------------------------------------------- schema

def load_schema() -> dict:
    override = env("ZOTERO_SCHEMA_FILE")
    if override:
        return load_json_file(override)
    cache = cache_dir() / "schema.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < SCHEMA_TTL:
        return json.loads(cache.read_text(encoding="utf-8"))
    resp = request("GET", f"{web_base()}/schema", timeout=60)
    if resp.status != 200:
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
        fail(f"Could not download the Zotero schema ({resp.status}).")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(resp.text, encoding="utf-8")
    return resp.json()


# Common wrong item types (often from other managers or older docs) → Zotero type.
TYPE_ALIASES = {"photograph": "artwork", "photo": "artwork", "article": "journalArticle", "chapter": "bookSection",
                "website": "webpage", "web": "webpage", "proceedings": "conferencePaper", "inproceedings": "conferencePaper",
                "phdthesis": "thesis", "mastersthesis": "thesis", "techreport": "report", "data": "dataset",
                "software": "computerProgram", "misc": "document", "unpublished": "manuscript", "law": "statute"}


def schema_index(schema: dict) -> dict:
    return {
        t["itemType"]: {
            "fields": {f["field"] for f in t["fields"]},
            # Base field → type-specific name, e.g. report: publisher → institution.
            "base": {f["baseField"]: f["field"] for f in t["fields"] if f.get("baseField")},
            "creators": {c["creatorType"] for c in t.get("creatorTypes", [])},
        }
        for t in schema["itemTypes"]
    }


def looks_title_case(title: str) -> bool:
    words = [w for w in re.split(r"[\s:–—-]+", title or "")[1:] if len(w) >= 4 and not w.isupper()]
    return len(words) >= 3 and sum(w[:1].isupper() for w in words) / len(words) >= 0.6


def check_items(items: list[dict], *, for_create: bool = True) -> list[dict]:
    index = schema_index(load_schema())
    results = []
    for i, item in enumerate(items):
        errors, warnings = [], []
        item_type = item.get("itemType")
        spec = index.get(item_type)
        if not spec:
            close = TYPE_ALIASES.get(str(item_type).lower()) or next(iter(difflib.get_close_matches(str(item_type), index.keys(), n=1)), None)
            errors.append(f"itemType {item_type!r} does not exist" + (f" (use {close!r})" if close else ""))
            results.append({"index": i, "errors": errors, "warnings": warnings})
            continue
        for field in item:
            if field in STRUCTURAL_KEYS or field in spec["fields"]:
                continue
            if field in ("key", "version"):
                (warnings if not for_create else errors).append(
                    f"'{field}' must not be sent when creating (Citoid/exported JSON carries it; drop it)")
                continue
            if field in spec["base"]:
                errors.append(f"field {field!r} is called {spec['base'][field]!r} in {item_type}")
                continue
            close = difflib.get_close_matches(field, spec["fields"], n=1)
            errors.append(f"field {field!r} is not valid for {item_type}" + (f" (did you mean {close[0]!r}?)" if close else ""))
        for c_index, creator in enumerate(item.get("creators", [])):
            ctype = creator.get("creatorType")
            if ctype not in spec["creators"]:
                errors.append(f"creators[{c_index}].creatorType {ctype!r} not valid for {item_type}: {sorted(spec['creators'])}")
            has_name = bool(creator.get("name"))
            has_split = bool(creator.get("lastName") or creator.get("firstName"))
            if has_name == has_split:
                errors.append(f"creators[{c_index}] needs either 'name' (single field) or 'lastName'/'firstName', not both/neither")
        if not item.get("creators") and item_type not in ("webpage", "document", "manuscript", "artwork", "map"):
            warnings.append("no creators: APA will start the entry with the title; confirm it is truly anonymous")
        title = item.get("title") or item.get("caseName") or item.get("nameOfAct")
        if not title:
            errors.append("missing title")
        elif item_type not in PERIODICAL_TYPES | {"webpage"} and looks_title_case(title):
            warnings.append("title looks like Title Case; APA renders titles as stored, so store sentence case")
        doi = item.get("DOI")
        if doi:
            if normalize_doi(doi) is None:
                errors.append(f"DOI {doi!r} is not a DOI")
            elif re.match(r"(?i)(https?://|doi:)", doi.strip()):
                errors.append("DOI must be bare (10.xxxx/yyy), without https://doi.org/ or doi:")
        if item.get("ISBN"):
            raw_tokens = re.findall(r"[0-9Xx][0-9Xx\- ]{8,16}[0-9Xx]", item["ISBN"])
            bad = [t for t in raw_tokens if not normalize_isbn(t)]
            if bad or not raw_tokens:
                errors.append(f"ISBN checksum invalid: {bad or item['ISBN']}")
        date = item.get("date") or ""
        if re.search(r"(?i)s\.\s?f\.|n\.\s?d\.", date):
            errors.append("date must be empty for undated works; APA renders 's. f.'/'n.d.' itself")
        if item.get("url") and not re.match(r"https?://", item["url"]):
            errors.append("url must start with http:// or https://")
        for tag in item.get("tags", []):
            if not isinstance(tag, dict) or not isinstance(tag.get("tag"), str):
                errors.append(f"tag {tag!r} must be {{'tag': '...'}}")
        results.append({"index": i, "errors": errors, "warnings": warnings})
    return results


# --------------------------------------------------------------------------- snapshot / matching

def summarize(item: dict) -> dict:
    data = item.get("data", item)
    # Primary creators only: a chapter's editors or a translator are not its authors.
    creators = ([c for c in data.get("creators", []) if c.get("creatorType") not in SECONDARY_CREATORS]
                or data.get("creators", []))
    return {
        "key": data.get("key") or item.get("key"),
        "version": data.get("version") or item.get("version"),
        "itemType": data.get("itemType"),
        "title": data.get("title") or data.get("caseName") or data.get("nameOfAct"),
        "creators": [c.get("lastName") or c.get("name") for c in creators],
        "creator_details": [author_detail(c) for c in creators],
        "date": data.get("date"),
        "DOI": item_doi(data),
        "ISBN": sorted(isbns_in(data.get("ISBN"))),
        "container": data.get("publicationTitle") or data.get("bookTitle") or data.get("proceedingsTitle"),
        "inTrash": bool(data.get("deleted")),
    }


def _fetch_top(base: str, headers: dict, name: str, since: str | None = None) -> list[dict]:
    items, start = [], 0
    while True:
        params = {"format": "json", "includeTrashed": 1, "limit": 100, "start": start, "since": since}
        if name == "local":
            params.pop("limit"), params.pop("start")
        resp = request("GET", base + "/items/top", params=params, headers=headers, timeout=120)
        if resp.status != 200:
            fail(f"Snapshot failed via {name} API ({resp.status}): {resp.text[:200]}")
        page = resp.json()
        items += [summarize(i) for i in page if i["data"]["itemType"] not in NON_BIB_TYPES]
        start += len(page)
        if name == "local" or len(page) < 100:
            return items


def snapshot(source: str) -> tuple[list[dict], str]:
    """All top-level bibliographic items (incl. trash), cached per library version.

    Web snapshots are refreshed incrementally (`since` + `/deleted`), the Zotero sync
    protocol, so only items changed after the cached version are downloaded.
    """
    base, headers, name = read_base(source)
    probe = request("GET", base + "/items/top", params={"limit": 1, "format": "keys"}, headers=headers, timeout=60)
    version = probe.header("Last-Modified-Version") or "0"
    cache = cache_dir() / f"snapshot-v{SNAPSHOT_FORMAT}-{name}-{library_prefix().strip('/').replace('/', '-')}.json"
    cached = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else None
    if cached and cached.get("version") == version:
        return cached["items"], name
    if cached and name == "web":
        deleted = request("GET", base + "/deleted", params={"since": cached["version"]}, headers=headers, timeout=60)
        if deleted.status == 200:
            changed = _fetch_top(base, headers, name, since=cached["version"])
            gone = set((deleted.json() or {}).get("items", [])) | {i["key"] for i in changed}
            items = [i for i in cached["items"] if i["key"] not in gone] + changed
        else:
            items = _fetch_top(base, headers, name)
    else:
        items = _fetch_top(base, headers, name)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"version": version, "items": items}, ensure_ascii=False), encoding="utf-8")
    return items, name


def score(ref: dict, item: dict) -> float:
    title = title_similarity(ref.get("title"), item["title"])
    author = surname_match((ref.get("authors") or [None])[0], (item["creators"] or [None])[0])
    if not ref.get("authors") and not item["creators"]:
        author = 1.0
    return round(0.6 * title + 0.25 * author + 0.15 * year_match(ref.get("year"), item["date"]), 3)


def diff_fields(ref: dict, item: dict) -> list[dict]:
    diffs = []
    if ref.get("title") and title_similarity(ref["title"], item["title"]) < 0.97:
        diffs.append({"field": "title", "manuscript": ref["title"], "zotero": item["title"]})
    if year_of(ref.get("year")) != year_of(item["date"]):
        diffs.append({"field": "year", "manuscript": ref.get("year"), "zotero": item["date"]})
    ref_authors, z_authors = ref.get("authors") or [], item["creators"]
    if ref_authors or ref.get("etal") or ref.get("authors_truncated"):
        authorship = compare_authorship(
            ref_authors, z_authors, left_details=ref.get("author_details"),
            right_details=item.get("creator_details"), corporate=bool(ref.get("corporate")),
            truncated=bool(ref.get("etal") or ref.get("authors_truncated")), right_label="zotero",
        )
        diffs.extend(authorship["diffs"])
        if ref_authors and not z_authors:
            diffs.append({"field": "author_count", "manuscript": len(ref_authors), "zotero": 0, "severity": "warning"})
    if ref.get("doi") and item["DOI"] and ref["doi"] != item["DOI"]:
        diffs.append({"field": "DOI", "manuscript": ref["doi"], "zotero": item["DOI"]})
    if ref.get("doi") and not item["DOI"]:
        diffs.append({"field": "DOI", "manuscript": ref["doi"], "zotero": None})
    return diffs


def match_refs(refs: list[dict], items: list[dict]) -> list[dict]:
    by_doi, by_isbn, by_token, by_author = defaultdict(list), defaultdict(list), defaultdict(set), defaultdict(set)
    for n, item in enumerate(items):
        if item["DOI"]:
            by_doi[item["DOI"]].append(n)
        for isbn in item["ISBN"]:
            by_isbn[isbn].append(n)
        for token in set(fold(item["title"]).split()):
            if len(token) >= 5:
                by_token[token].add(n)
        if item["creators"]:
            by_author[fold(item["creators"][0])].add(n)
    results = []
    for ref in refs:
        out = {"index": ref.get("index"), "raw": ref.get("raw"), "status": "none", "best": None, "alternatives": []}
        exact = by_doi.get(ref.get("doi") or "", []) or by_isbn.get(ref.get("isbn") or "", [])
        if exact:
            found = [items[n] for n in exact]
            out["status"] = "exact-doi" if ref.get("doi") in by_doi else "exact-isbn"
            live = [f for f in found if not f["inTrash"]] or found
            out["best"] = {**live[0], "score": 1.0, "diffs": diff_fields(ref, live[0])}
            out["alternatives"] = [{**f, "score": 1.0} for f in found if f is not live[0]]
            if all(f["inTrash"] for f in found):
                out["status"] = "trashed"
            if len(found) > 1:
                out["duplicates_in_library"] = [f["key"] for f in found]
            results.append(out)
            continue
        if not ref.get("title"):
            results.append(out)
            continue
        tokens = [t for t in set(fold(ref["title"]).split()) if len(t) >= 5]
        pool = set()
        for token in tokens:
            pool |= by_token.get(token, set())
        for author in ref.get("authors") or []:
            pool |= by_author.get(fold(author), set())
        ranked = sorted(((score(ref, items[n]), items[n]) for n in pool), key=lambda pair: -pair[0])[:3]
        if ranked:
            top_score, top = ranked[0]
            out["best"] = {**top, "score": top_score, "diffs": diff_fields(ref, top)}
            out["alternatives"] = [{**it, "score": s} for s, it in ranked[1:] if s >= 0.5]
            out["status"] = "strong" if top_score >= 0.85 else "weak" if top_score >= 0.65 else "none"
            if out["status"] == "strong" and out["best"]["diffs"]:
                out["status"] = "strong-diff"
            if out["status"] != "none" and top["inTrash"]:
                out["status"] = "trashed"
            if out["status"] == "none":
                out["best"] = None
        results.append(out)
    return results


# --------------------------------------------------------------------------- web lookups for dedupe

def web_find(query: str, mode: str) -> list[dict]:
    resp = request("GET", f"{web_base()}{library_prefix()}/items/top", headers=web_headers(),
                   params={"q": query, "qmode": mode, "includeTrashed": 1, "format": "json", "limit": 25}, timeout=60)
    if resp.status != 200:
        fail(f"Web search failed ({resp.status}): {resp.text[:200]}")
    return [summarize(i) for i in resp.json() if i["data"]["itemType"] not in NON_BIB_TYPES]


def find_duplicates(item: dict) -> list[dict]:
    hits = []
    doi = normalize_doi(item.get("DOI"))
    if doi:
        hits += [h for h in web_find(doi, "everything") if h["DOI"] == doi]
    for isbn in isbns_in(item.get("ISBN")):
        hits += [h for h in web_find(isbn, "everything") if isbn in h["ISBN"]]
    title = item.get("title")
    if title and not hits:
        phrase = " ".join(main_title(title).split()[:6])
        for h in web_find(phrase, "titleCreatorYear"):
            if title_similarity(title, h["title"]) >= 0.9 and year_match(item.get("date"), h["date"]) >= 1:
                hits.append(h)
    unique = {h["key"]: h for h in hits}
    return list(unique.values())


# --------------------------------------------------------------------------- writes

def _write_log(method: str, endpoint: str, status: int, **extra) -> dict:
    return {"timestamp": now_iso(), "method": method, "endpoint": endpoint, "status": status, **extra}


def create(items: list[dict], *, confirm: bool, collection: str | None, audit_tags: bool, allow_duplicate: bool) -> dict:
    for item in items:
        item.pop("key", None), item.pop("version", None)
        if collection:
            item["collections"] = sorted(set(item.get("collections", [])) | {collection})
        if audit_tags:
            tags = {t["tag"] for t in item.get("tags", [])}
            for tag in ("citation-audited", f"validated-{time.strftime('%Y-%m-%d')}"):
                if tag not in tags:
                    item.setdefault("tags", []).append({"tag": tag})
    checks = check_items(items)
    duplicates = {i: d for i, item in enumerate(items) if (d := find_duplicates(item))}
    endpoint = f"POST {library_prefix()}/items"
    report = {"endpoint": endpoint, "items": items, "check": checks,
              "duplicates": {str(i): d for i, d in duplicates.items()},
              "batches": (len(items) + BATCH - 1) // BATCH}
    blocking = [c for c in checks if c["errors"]]
    if not confirm:
        return {"dry_run": True, **report,
                "next": "Show this payload to the user; rerun with --confirm only after explicit approval."}
    if blocking:
        fail(f"Refusing to write: schema errors in items {[c['index'] for c in blocking]}. Run `check` and fix.")
    if duplicates and not allow_duplicate:
        fail(f"Refusing to write: items {sorted(duplicates)} already exist in Zotero (see dry-run 'duplicates').")
    log, created, failed = [], {}, {}
    for start in range(0, len(items), BATCH):
        batch = items[start:start + BATCH]
        token = uuid.uuid4().hex
        resp = request("POST", f"{web_base()}{library_prefix()}/items", body=batch, retry_unsafe=True,
                       headers={**web_headers(write=True), "Zotero-Write-Token": token}, timeout=120)
        if resp.status == 412:
            log.append(_write_log("POST", endpoint, 412, note="write token already used: batch may already be "
                                  "saved; search the library before retrying"))
            break
        if resp.status != 200:
            log.append(_write_log("POST", endpoint, resp.status, error=resp.text[:300]))
            break
        body = resp.json() or {}
        success = body.get("success") or {k: v.get("key") for k, v in (body.get("successful") or {}).items()}
        for local_index, key in success.items():
            created[start + int(local_index)] = key
        for local_index, key in (body.get("unchanged") or {}).items():
            created[start + int(local_index)] = key
        for local_index, err in (body.get("failed") or {}).items():
            failed[start + int(local_index)] = {"code": err.get("code"), "message": err.get("message")}
        log.append(_write_log("POST", endpoint, 200, library_version=resp.header("Last-Modified-Version"),
                              created=[created[k] for k in sorted(created) if k >= start], failed=len(body.get("failed") or {})))
    return {"dry_run": False, "created": [{"index": i, "itemKey": k} for i, k in sorted(created.items())],
            "failed": [{"index": i, **e} for i, e in sorted(failed.items())], "log": log}


def get_item(key: str) -> dict:
    resp = request("GET", f"{web_base()}{library_prefix()}/items/{key}", headers=web_headers(), timeout=60)
    if resp.status != 200:
        fail(f"GET item {key} returned {resp.status}: {resp.text[:200]}")
    return resp.json()


def patch(key: str, changes: dict, version: int, *, confirm: bool, action: str = "update") -> dict:
    current = get_item(key)
    data = current["data"]
    endpoint = f"PATCH {library_prefix()}/items/{key}"
    if int(data["version"]) != version:
        fail(f"Item {key} is at version {data['version']}, not {version}: it changed since you showed the diff. "
             "Re-fetch, re-show and re-confirm.")
    if "itemType" in changes and changes["itemType"] != data["itemType"]:
        target = changes["itemType"]
    else:
        target = data["itemType"]
    merged = {**data, **changes, "itemType": target}
    checks = [] if action == "trash" else check_items(
        [{k: v for k, v in merged.items() if k not in ("key", "version", "dateAdded", "dateModified")}], for_create=False)
    diff = [{"field": f, "before": data.get(f), "after": v} for f, v in changes.items() if data.get(f) != v]
    if not confirm:
        return {"dry_run": True, "action": action, "endpoint": endpoint, "version": version, "diff": diff,
                "check": checks, "next": "Show the diff; rerun with --confirm after explicit approval."}
    if checks and checks[0]["errors"]:
        fail(f"Refusing to write: {checks[0]['errors']}")
    resp = request("PATCH", f"{web_base()}{library_prefix()}/items/{key}", body=changes,
                   headers={**web_headers(write=True), "If-Unmodified-Since-Version": str(version)}, timeout=60)
    if resp.status == 412:
        fail(f"412: item {key} changed on the server after version {version}; re-fetch and re-confirm.")
    if resp.status != 204:
        fail(f"PATCH {key} returned {resp.status}: {resp.text[:300]}")
    return {"dry_run": False, "action": action, "diff": diff,
            "log": [_write_log("PATCH", endpoint, 204, itemKey=key, new_version=resp.header("Last-Modified-Version"))]}


# --------------------------------------------------------------------------- cli

def cmd_whoami(_args) -> dict:
    key = env("ZOTERO_API_KEY")
    result = {"ZOTERO_API_KEY": mask(key), "ZOTERO_LIBRARY_ID": env("ZOTERO_LIBRARY_ID"),
              "ZOTERO_LIBRARY_TYPE": env("ZOTERO_LIBRARY_TYPE", "user"), "local_api": local_available()}
    if key:
        resp = request("GET", f"{web_base()}/keys/current", headers=web_headers(), timeout=30)
        if resp.status == 200:
            info = resp.json()
            info.pop("key", None)
            result.update({"userID": info.get("userID"), "username": info.get("username"), "access": info.get("access")})
            if result["ZOTERO_LIBRARY_TYPE"] == "user" and str(info.get("userID")) != str(result["ZOTERO_LIBRARY_ID"]):
                result["warning"] = "ZOTERO_LIBRARY_ID differs from the key's userID"
        else:
            result["key_error"] = f"/keys/current returned {resp.status} (invalid or revoked key)"
    return result


def cmd_search(args) -> dict:
    base, headers, name = read_base(args.source)
    if args.doi or args.isbn:
        needle = normalize_doi(args.doi) if args.doi else normalize_isbn(args.isbn)
        if not needle:
            fail("Not a valid DOI/ISBN (ISBN checksum failed?).")
        queries = [needle] if args.doi else [needle, args.isbn.replace("-", "")]
        hits = {}
        for q in queries:
            resp = request("GET", base + "/items/top", headers=headers, timeout=60,
                           params={"q": q, "qmode": "everything", "includeTrashed": 1, "format": "json", "limit": 25})
            for item in resp.json() if resp.status == 200 else []:
                summary = summarize(item)
                # `everything` also matches full text and notes: keep only exact identifier hits.
                if (args.doi and summary["DOI"] == needle) or (args.isbn and needle in summary["ISBN"]):
                    hits[summary["key"]] = summary
        return {"source": name, "query": needle, "results": list(hits.values())}
    if not args.title and not args.author:
        fail("Give --doi, --isbn, --title and/or --author.")
    items, name = snapshot(args.source)
    ref = {"title": args.title, "authors": [args.author] if args.author else [], "year": args.year}
    if args.title:
        result = match_refs([ref], items)[0]
        return {"source": name, "status": result["status"], "best": result["best"], "alternatives": result["alternatives"]}
    hits = [i for i in items if i["creators"] and surname_match(args.author, i["creators"][0]) == 1
            and (not args.year or year_of(i["date"]) == args.year)]
    return {"source": name, "results": hits[:50]}


def cmd_match(args) -> dict:
    data = load_json_file(args.audit_json)
    refs = data["references"] if isinstance(data, dict) else data
    items, name = snapshot(args.source)
    results = match_refs(refs, items)
    counts = defaultdict(int)
    for r in results:
        counts[r["status"]] += 1
    return {"source": name, "library_items": len(items), "summary": dict(counts), "matches": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", choices=["auto", "local", "web"], default="auto", help="read source (default auto: local first)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami")
    p = sub.add_parser("search")
    p.add_argument("--doi"), p.add_argument("--isbn"), p.add_argument("--title"), p.add_argument("--author"), p.add_argument("--year")
    p = sub.add_parser("match")
    p.add_argument("audit_json", help="output of cite_audit.py extract/audit, or a JSON list of references")
    p = sub.add_parser("get")
    p.add_argument("keys", nargs="+")
    p = sub.add_parser("template")
    p.add_argument("item_type")
    p = sub.add_parser("check")
    p.add_argument("payload")
    p = sub.add_parser("create")
    p.add_argument("payload")
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--collection")
    p.add_argument("--audit-tags", action="store_true", help="add citation-audited and validated-YYYY-MM-DD tags")
    p.add_argument("--allow-duplicate", action="store_true")
    p = sub.add_parser("update")
    p.add_argument("key"), p.add_argument("patch")
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--confirm", action="store_true")
    p = sub.add_parser("trash")
    p.add_argument("key")
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    if args.command == "whoami":
        emit(cmd_whoami(args))
    elif args.command == "search":
        emit(cmd_search(args))
    elif args.command == "match":
        emit(cmd_match(args))
    elif args.command == "get":
        emit([{"key": i["key"], "version": i["version"], "data": i["data"]} for i in map(get_item, args.keys)])
    elif args.command == "template":
        resp = request("GET", f"{web_base()}/items/new", params={"itemType": args.item_type}, headers=API_HEADERS)
        if resp.status != 200:
            fail(f"Unknown itemType {args.item_type!r} ({resp.status}).")
        emit(resp.json())
    elif args.command == "check":
        payload = load_json_file(args.payload)
        emit(check_items(payload if isinstance(payload, list) else [payload]))
    elif args.command == "create":
        payload = load_json_file(args.payload)
        emit(create(payload if isinstance(payload, list) else [payload], confirm=args.confirm,
                    collection=args.collection, audit_tags=args.audit_tags, allow_duplicate=args.allow_duplicate))
    elif args.command == "update":
        emit(patch(args.key, load_json_file(args.patch), args.version, confirm=args.confirm))
    elif args.command == "trash":
        emit(patch(args.key, {"deleted": 1}, args.version, confirm=args.confirm, action="trash"))


if __name__ == "__main__":
    main()
