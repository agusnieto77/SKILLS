#!/usr/bin/env python3
"""Validate a reference against external bibliographic sources (stdlib only).

  doi DOI      [--title T --author A --year Y]   Crossref/DataCite (by registration agency) + OpenAlex
  isbn ISBN    [--title T --author A --year Y]   Open Library + Library of Congress/WorldCat (Citoid) + Google Books
  pmid PMID    [--title T --author A --year Y]   PubMed + Crossref when PubMed lists a DOI
  search --title T [--author A] [--year Y]       Crossref + OpenAlex candidates (leads only, never validation)
  payload IDENTIFIER                             Zotero JSON for a DOI/ISBN/PMID/URL (Citoid), schema-checked
  integrity [--dois D1,D2] [--from JSON...]      retractions, expressions of concern, corrections (batched)

Verdicts: validated (2+ independent sources agree and match the manuscript),
single-source (only one source answered: needs a second, e.g. publisher site),
conflict (sources disagree with each other), mismatch (sources agree, manuscript
differs: show the diff), not-found.

Optional env: CROSSREF_MAILTO (polite pool), OPENALEX_API_KEY, GOOGLE_BOOKS_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zotlib import (  # noqa: E402
    emit, env, fail, get_json, isbns_in, normalize_doi, normalize_isbn, request, surname_match,
    title_similarity, year_of,
)

TIMEOUT = 25


def _ua_headers() -> dict:
    mailto = env("CROSSREF_MAILTO")
    return {"User-Agent": f"zotero-citations/3.0{f' (mailto:{mailto})' if mailto else ''}"}


def _record(source: str, **fields) -> dict:
    record = {"source": source, "title": None, "authors": [], "year": None, "container": None, "volume": None,
              "issue": None, "pages": None, "publisher": None, "type": None, "doi": None, "isbn": [], "url": None}
    record.update({k: v for k, v in fields.items() if v not in (None, "", [])})
    return record


# --------------------------------------------------------------------------- sources

def registration_agency(doi: str) -> str | None:
    data = get_json(f"https://doi.org/ra/{urllib.parse.quote(doi, safe='/')}", timeout=TIMEOUT)
    if not data:
        return None
    entry = data[0]
    return None if entry.get("status") else entry.get("RA")


def crossref_doi(doi: str) -> dict | None:
    data = get_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}", headers=_ua_headers(),
                    timeout=TIMEOUT, params={"mailto": env("CROSSREF_MAILTO")})
    return _from_crossref(data["message"]) if data else None


def _from_crossref(m: dict) -> dict:
    parts = (m.get("published-print") or m.get("published-online") or m.get("issued") or {}).get("date-parts") or [[None]]
    online = ((m.get("published-online") or {}).get("date-parts") or [[None]])[0][0]
    return _record(
        "crossref", title=(m.get("title") or [None])[0], authors=[a.get("family") or a.get("name") for a in m.get("author", [])],
        year=str(parts[0][0]) if parts[0][0] else None, container=(m.get("container-title") or [None])[0],
        volume=m.get("volume"), issue=m.get("issue"), pages=m.get("page"), publisher=m.get("publisher"),
        type=m.get("type"), doi=normalize_doi(m.get("DOI")), isbn=sorted(isbns_in(" ".join(m.get("ISBN", [])))),
        url=m.get("URL"), online_year=str(online) if online else None, notices=_notices(m.get("updated-by")),
    )


def datacite_doi(doi: str) -> dict | None:
    data = get_json(f"https://api.datacite.org/dois/{urllib.parse.quote(doi, safe='/')}", timeout=TIMEOUT)
    if not data:
        return None
    a = data["data"]["attributes"]
    return _record(
        "datacite", title=(a.get("titles") or [{}])[0].get("title"),
        authors=[c.get("familyName") or c.get("name") for c in a.get("creators", [])],
        year=str(a.get("publicationYear")) if a.get("publicationYear") else None, publisher=_publisher(a.get("publisher")),
        type=(a.get("types") or {}).get("resourceTypeGeneral"), doi=normalize_doi(a.get("doi")), url=a.get("url"),
    )


def _publisher(value):
    return value.get("name") if isinstance(value, dict) else value


def csl_negotiation(doi: str, agency: str) -> dict | None:
    """Content negotiation works for Crossref, DataCite and mEDRA DOIs alike."""
    resp = request("GET", f"https://doi.org/{urllib.parse.quote(doi, safe='/')}", timeout=TIMEOUT,
                   headers={"Accept": "application/vnd.citationstyles.csl+json", **_ua_headers()})
    if resp.status != 200:
        return None
    try:
        m = resp.json()
    except ValueError:
        return None
    issued = ((m.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    return _record(
        f"doi-negotiation ({agency})", title=m.get("title"), authors=[a.get("family") or a.get("literal") for a in m.get("author", [])],
        year=str(issued) if issued else None, container=m.get("container-title"), volume=m.get("volume"),
        issue=m.get("issue"), pages=m.get("page"), publisher=m.get("publisher"), type=m.get("type"),
        doi=normalize_doi(m.get("DOI")),
    )


def openalex_doi(doi: str) -> dict | None:
    key = env("OPENALEX_API_KEY")
    data = get_json(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='/')}", timeout=TIMEOUT,
                    params={"api_key": key} if key else None)
    return _from_openalex(data) if data else None


def _from_openalex(w: dict) -> dict:
    biblio = w.get("biblio") or {}
    pages = "-".join(p for p in (biblio.get("first_page"), biblio.get("last_page")) if p) or None
    source = ((w.get("primary_location") or {}).get("source") or {})
    return _record(
        "openalex", title=w.get("title"),
        authors=[_family((a.get("author") or {}).get("display_name")) for a in w.get("authorships", [])],
        full_names=[(a.get("author") or {}).get("display_name") for a in w.get("authorships", [])],
        year=str(w.get("publication_year")) if w.get("publication_year") else None, container=source.get("display_name"),
        volume=biblio.get("volume"), issue=biblio.get("issue"), pages=pages, type=w.get("type"),
        doi=normalize_doi(w.get("doi")), url=w.get("id"), is_retracted=w.get("is_retracted"),
    )


def openlibrary_isbn(isbn: str) -> dict | None:
    data = get_json("https://openlibrary.org/api/books", timeout=TIMEOUT,
                    params={"bibkeys": f"ISBN:{isbn}", "jscmd": "data", "format": "json"})
    book = (data or {}).get(f"ISBN:{isbn}")
    if not book:
        return None
    ids = book.get("identifiers", {})
    return _record(
        "openlibrary", title=": ".join(p for p in (book.get("title"), book.get("subtitle")) if p),
        authors=[_family(a.get("name")) for a in book.get("authors", [])],
        full_names=[a.get("name") for a in book.get("authors", [])], year=year_of(book.get("publish_date")),
        publisher=", ".join(p["name"] for p in book.get("publishers", [])), type="book",
        isbn=sorted(isbns_in(" ".join(ids.get("isbn_13", []) + ids.get("isbn_10", [])))), url=book.get("url"),
    )


def googlebooks_isbn(isbn: str) -> dict | None:
    key = env("GOOGLE_BOOKS_API_KEY")
    # The keyless quota is shared by every anonymous client and is often exhausted:
    # do not burn retries on it, report it as unavailable.
    resp = request("GET", "https://www.googleapis.com/books/v1/volumes", timeout=TIMEOUT, retries=0,
                   params={"q": f"isbn:{isbn}", **({"key": key} if key else {})})
    if resp.status in (403, 429):
        raise ConnectionError(f"quota exhausted ({resp.status}); set GOOGLE_BOOKS_API_KEY")
    items = (resp.json() or {}).get("items") or [] if resp.status == 200 else []
    if not items:
        return None
    v = items[0]["volumeInfo"]
    ids = " ".join(i.get("identifier", "") for i in v.get("industryIdentifiers", []))
    return _record(
        "googlebooks", title=": ".join(p for p in (v.get("title"), v.get("subtitle")) if p),
        authors=[_family(a) for a in v.get("authors", [])], full_names=v.get("authors"), year=year_of(v.get("publishedDate")),
        publisher=v.get("publisher"), type="book", isbn=sorted(isbns_in(ids)),
    )


def _family(display: str | None) -> str | None:
    """Family name from 'Given Family' or 'Family, Given' display strings."""
    if not display:
        return None
    return display.split(",")[0].strip() if "," in display else display.split()[-1]


def citoid(identifier: str) -> list[dict] | None:
    resp = request("GET", f"https://en.wikipedia.org/api/rest_v1/data/citation/zotero/{urllib.parse.quote(identifier, safe='')}",
                   headers=_ua_headers(), timeout=TIMEOUT)
    if resp.status != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    return data if isinstance(data, list) and data else None


def citoid_isbn(isbn: str) -> dict | None:
    """Citoid resolves ISBNs through library catalogs (LoC/WorldCat), independent of Open Library."""
    items = citoid(isbn)
    if not items:
        return None
    item = items[0]
    return _record(
        f"citoid ({item.get('libraryCatalog') or 'library catalog'})", title=item.get("title"),
        authors=[c.get("lastName") or c.get("name") for c in item.get("creators", [])], year=year_of(item.get("date")),
        publisher=item.get("publisher"), type=item.get("itemType"), isbn=sorted(isbns_in(item.get("ISBN"))),
    )


def pubmed(pmid: str) -> dict | None:
    data = get_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", timeout=TIMEOUT,
                    params={"db": "pubmed", "id": pmid, "retmode": "json"})
    entry = ((data or {}).get("result") or {}).get(str(pmid))
    if not entry or entry.get("error"):
        return None
    doi = next((i["value"] for i in entry.get("articleids", []) if i.get("idtype") == "doi"), None)
    return _record(
        "pubmed", title=(entry.get("title") or "").rstrip("."), authors=[a["name"].rsplit(" ", 1)[0] for a in entry.get("authors", [])],
        year=year_of(entry.get("pubdate")), container=entry.get("fulljournalname") or entry.get("source"),
        volume=entry.get("volume"), issue=entry.get("issue"), pages=entry.get("pages"), type="journal-article",
        doi=normalize_doi(doi),
    )


# --------------------------------------------------------------------------- agreement

def agree(a: dict, b: dict) -> dict:
    title = title_similarity(a["title"], b["title"])
    author = surname_match((a["authors"] or [None])[0], (b["authors"] or [None])[0]) if a["authors"] and b["authors"] else None
    years = {a.get("year"), b.get("year"), a.get("online_year"), b.get("online_year")} - {None}
    year_ok = a.get("year") == b.get("year") or bool(
        a.get("year") and b.get("year") and ({a["year"], a.get("online_year")} & {b["year"], b.get("online_year")}))
    ok = title >= 0.9 and (author is None or author >= 0.7) and year_ok
    return {"sources": [a["source"], b["source"]], "agree": ok, "title_similarity": round(title, 3),
            "first_author": author, "years": sorted(years)}


def compare_expected(consensus: dict, expected: dict) -> list[dict]:
    diffs = []
    if expected.get("title"):
        sim = title_similarity(expected["title"], consensus["title"])
        if sim < 0.9:
            diffs.append({"field": "title", "manuscript": expected["title"], "sources": consensus["title"], "similarity": round(sim, 3)})
    if expected.get("author") and consensus["authors"]:
        if surname_match(expected["author"], consensus["authors"][0]) < 0.7:
            diffs.append({"field": "first_author", "manuscript": expected["author"], "sources": consensus["authors"][0]})
    if expected.get("year") and consensus.get("year"):
        valid = {consensus["year"], consensus.get("online_year")} - {None}
        if year_of(expected["year"]) not in valid:
            diffs.append({"field": "year", "manuscript": expected["year"], "sources": sorted(valid)})
    return diffs


def verdict(records: list[dict], expected: dict, errors: list[str]) -> dict:
    found = [r for r in records if r]
    result = {"records": found, "unavailable": errors}
    if not found:
        return {"verdict": "not-found", **result}
    result["integrity"] = integrity_of(found)
    pairs = [agree(a, b) for i, a in enumerate(found) for b in found[i + 1:]]
    result["agreement"] = pairs
    consensus = found[0]
    result["diffs_vs_manuscript"] = compare_expected(consensus, expected)
    if len(found) == 1:
        return {"verdict": "single-source", **result}
    if not all(p["agree"] for p in pairs):
        return {"verdict": "conflict", **result}
    return {"verdict": "mismatch" if result["diffs_vs_manuscript"] else "validated", **result}


# --------------------------------------------------------------------------- integrity

# Crossref `update-type` vocabulary (Retraction Watch data is merged into Crossref).
RETRACTED_TYPES = {"retraction", "partial_retraction", "withdrawal", "removal", "retration"}
CONCERN_TYPES = {"expression_of_concern"}
CORRECTED_TYPES = {"correction", "erratum", "corrigendum", "corrected", "addendum", "clarification"}
VERSION_TYPES = {"new_version", "new_edition"}
STATUS_RANK = ["retracted", "expression-of-concern", "corrected", "new-version", "clean"]


def _notices(updated_by: list | None) -> list[dict]:
    notices = []
    for update in updated_by or []:
        date = ((update.get("updated") or {}).get("date-parts") or [[None]])[0]
        notices.append({"type": update.get("type"), "label": update.get("label"),
                        "notice_doi": normalize_doi(update.get("DOI")), "source": update.get("source"),
                        "date": "-".join(str(p) for p in date if p) or None})
    return notices


def integrity_status(notices: list[dict], is_retracted: bool | None) -> str:
    types = {n["type"] for n in notices}
    if is_retracted or types & RETRACTED_TYPES:
        return "retracted"
    if types & CONCERN_TYPES:
        return "expression-of-concern"
    if types & CORRECTED_TYPES:
        return "corrected"
    if types & VERSION_TYPES:
        return "new-version"
    return "clean"


def integrity_of(records: list[dict]) -> dict:
    notices = [n for r in records for n in r.get("notices", [])]
    retracted = any(r.get("is_retracted") for r in records)
    checked = [r["source"] for r in records if r["source"] in ("crossref", "openalex")]
    return {"status": integrity_status(notices, retracted) if checked else "unknown", "notices": notices,
            "checked_with": checked}


def _dois_from_files(paths: list[str]) -> dict[str, list[int]]:
    """DOIs from cite_audit output (references) and/or match output (Zotero best matches)."""
    found: dict[str, list[int]] = {}
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        for ref in data.get("references", []):
            if ref.get("doi"):
                found.setdefault(ref["doi"], []).append(ref.get("index"))
        for match in data.get("matches", []):
            doi = normalize_doi((match.get("best") or {}).get("DOI"))
            if doi:
                found.setdefault(doi, []).append(match.get("index"))
    return {doi: sorted({i for i in idx if i is not None}) for doi, idx in found.items()}


def integrity(dois: dict[str, list[int]]) -> dict:
    """Batch check: Crossref `updated-by` notices + OpenAlex `is_retracted`, 50 DOIs per request."""
    notices: dict[str, list[dict]] = {}
    retracted: dict[str, bool] = {}
    errors, checked = [], {"crossref": set(), "openalex": set()}
    keys = sorted(dois)
    key = env("OPENALEX_API_KEY")
    for start in range(0, len(keys), 50):
        chunk = keys[start:start + 50]
        try:
            data = get_json("https://api.crossref.org/works", headers=_ua_headers(), timeout=60,
                            params={"filter": ",".join(f"doi:{d}" for d in chunk), "rows": 100,
                                    "select": "DOI,updated-by", "mailto": env("CROSSREF_MAILTO")})
            for item in ((data or {}).get("message") or {}).get("items", []):
                doi = normalize_doi(item.get("DOI"))
                notices[doi] = _notices(item.get("updated-by"))
                checked["crossref"].add(doi)
        except ConnectionError as err:
            errors.append(f"crossref: {err}")
        try:
            data = get_json("https://api.openalex.org/works", timeout=60,
                            params={"filter": "doi:" + "|".join(chunk), "select": "doi,is_retracted", "per_page": 100,
                                    **({"api_key": key} if key else {})})
            for work in (data or {}).get("results", []):
                doi = normalize_doi(work.get("doi"))
                retracted[doi] = bool(work.get("is_retracted"))
                checked["openalex"].add(doi)
        except ConnectionError as err:
            errors.append(f"openalex: {err}")
    results = []
    for doi in keys:
        sources = [s for s in ("crossref", "openalex") if doi in checked[s]]
        status = integrity_status(notices.get(doi, []), retracted.get(doi)) if sources else "unknown"
        results.append({"doi": doi, "status": status, "notices": notices.get(doi, []),
                        "openalex_is_retracted": retracted.get(doi), "checked_with": sources, "ref_indexes": dois[doi]})
    results.sort(key=lambda r: (STATUS_RANK.index(r["status"]) if r["status"] in STATUS_RANK else 9, r["doi"]))
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"summary": counts, "unavailable": errors, "results": results,
            "note": "Only works with a DOI can be checked; 'unknown' means no source answered for that DOI."}


def _call(fn, *args, errors: list[str]):
    try:
        record = fn(*args)
    except ConnectionError as err:
        errors.append(f"{fn.__name__}: {err}")
        return None
    return record


# --------------------------------------------------------------------------- commands

def validate_doi(raw: str, expected: dict) -> dict:
    doi = normalize_doi(raw)
    if not doi:
        fail(f"{raw!r} is not a DOI.")
    errors: list[str] = []
    agency = _call(registration_agency, doi, errors=errors)
    if agency is None and not errors:
        return {"doi": doi, "verdict": "not-found", "note": "doi.org reports the DOI does not exist (typo or invented DOI)."}
    records = []
    if agency == "Crossref":
        records.append(_call(crossref_doi, doi, errors=errors))
    elif agency == "DataCite":
        records.append(_call(datacite_doi, doi, errors=errors))
    else:
        records.append(_call(csl_negotiation, doi, agency or "unknown", errors=errors))
    records.append(_call(openalex_doi, doi, errors=errors))
    return {"doi": doi, "registration_agency": agency, **verdict(records, expected, errors)}


def validate_isbn(raw: str, expected: dict) -> dict:
    isbn = normalize_isbn(raw)
    if not isbn:
        return {"isbn": raw, "verdict": "not-found", "note": "ISBN checksum is invalid (typo or invented ISBN)."}
    errors: list[str] = []
    records = [_call(fn, isbn, errors=errors) for fn in (openlibrary_isbn, citoid_isbn, googlebooks_isbn)]
    return {"isbn": isbn, **verdict(records, expected, errors)}


def validate_pmid(pmid: str, expected: dict) -> dict:
    errors: list[str] = []
    record = _call(pubmed, pmid, errors=errors)
    records = [record]
    if record and record.get("doi"):
        records.append(_call(crossref_doi, record["doi"], errors=errors))
    return {"pmid": pmid, **verdict(records, expected, errors)}


def search(title: str, author: str | None, year: str | None) -> dict:
    errors, candidates = [], []
    params = {"query.bibliographic": " ".join(p for p in (title, year) if p), "rows": 5,
              "select": "DOI,title,author,issued,published-print,published-online,container-title,type,publisher,page,volume,issue,ISBN,URL",
              "mailto": env("CROSSREF_MAILTO")}
    if author:
        params["query.author"] = author
    try:
        data = get_json("https://api.crossref.org/works", params=params, headers=_ua_headers(), timeout=TIMEOUT)
        candidates += [_from_crossref(m) for m in ((data or {}).get("message") or {}).get("items", [])]
    except ConnectionError as err:
        errors.append(f"crossref: {err}")
    key = env("OPENALEX_API_KEY")
    try:
        data = get_json("https://api.openalex.org/works", timeout=TIMEOUT,
                        params={"search": title, "per_page": 5, **({"api_key": key} if key else {})})
        candidates += [_from_openalex(w) for w in (data or {}).get("results", [])]
    except ConnectionError as err:
        errors.append(f"openalex: {err}")
    for c in candidates:
        t = title_similarity(title, c["title"])
        a = surname_match(author, (c["authors"] or [None])[0]) if author and c["authors"] else 0.5
        y = 1.0 if not year or year_of(year) in {c["year"], c.get("online_year")} else 0.0
        c["score"] = round(0.6 * t + 0.25 * a + 0.15 * y, 3)
    candidates.sort(key=lambda c: -c["score"])
    return {"note": "Search hits are leads: confirm the chosen one with `doi`/`isbn` before creating anything.",
            "unavailable": errors, "candidates": candidates[:6]}


def payload(identifier: str) -> dict:
    from zotero_client import check_items  # local import: keeps validate_ref usable without Zotero env

    ident = normalize_doi(identifier) or normalize_isbn(identifier) or identifier.strip()
    items = citoid(ident)
    if not items:
        return {"identifier": ident, "payload": None, "note": "Citoid could not resolve it; build the payload from the "
                "`template` command and the validated records instead."}
    for item in items:
        for field in ("key", "version", "accessDate", "libraryCatalog"):
            item.pop(field, None)
        item["tags"] = [t for t in item.get("tags", []) if t.get("type") != 1]  # drop catalog subject tags
    return {"identifier": ident, "payload": items, "check": check_items(items),
            "note": "Citoid data is a draft: reconcile with the validated records (dates, title case) before `create`."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doi", "isbn", "pmid"):
        p = sub.add_parser(name)
        p.add_argument("identifier")
        p.add_argument("--title"), p.add_argument("--author"), p.add_argument("--year")
    p = sub.add_parser("search")
    p.add_argument("--title", required=True), p.add_argument("--author"), p.add_argument("--year")
    p = sub.add_parser("payload")
    p.add_argument("identifier")
    p = sub.add_parser("integrity")
    p.add_argument("--dois", help="comma-separated DOIs")
    p.add_argument("--from", dest="sources", nargs="*", default=[], help="cite_audit and/or match JSON files")
    args = parser.parse_args()
    if args.command == "search":
        emit(search(args.title, args.author, args.year))
        return
    if args.command == "payload":
        emit(payload(args.identifier))
        return
    if args.command == "integrity":
        dois = _dois_from_files(args.sources)
        for raw in (args.dois or "").split(","):
            doi = normalize_doi(raw)
            if doi:
                dois.setdefault(doi, [])
        if not dois and not args.sources:
            fail("No DOIs given (use --dois or --from audit.json match.json).")
        if not dois:
            emit({"summary": {}, "unavailable": [], "results": [],
                  "note": "No DOIs in the manuscript or its Zotero matches: retractions cannot be checked "
                          "(report it as 'sin DOI: no verificable', never as clean)."})
            return
        emit(integrity(dois))
        return
    expected = {"title": args.title, "author": args.author, "year": args.year}
    handler = {"doi": validate_doi, "isbn": validate_isbn, "pmid": validate_pmid}[args.command]
    emit(handler(args.identifier, expected))


if __name__ == "__main__":
    main()
