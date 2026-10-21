#!/usr/bin/env python3
"""Validate a reference against external bibliographic sources (stdlib only).

  doi DOI      [--title T --author A --year Y]   Crossref/DataCite (by registration agency) + OpenAlex
  isbn ISBN    [--title T --author A --year Y]   Open Library + Library of Congress/WorldCat (Citoid) + Google Books
  pmid PMID    [--title T --author A --year Y]   PubMed + Crossref when PubMed lists a DOI
  work --title T [--author A] [--year Y] [--url URL] [--sources S1,S2]
                                                 works without identifier: library catalogs (Open Library,
                                                 Library of Congress, BNE), LA Referencia, institutional
                                                 repositories (DSpace), Crossref, OpenAlex, the record page (Citoid)
  search --title T [--author A] [--year Y]       Crossref + OpenAlex candidates (leads only, never validation)
  payload IDENTIFIER                             Zotero JSON for a DOI/ISBN/PMID/URL (Citoid), schema-checked
  integrity [--dois D1,D2] [--from JSON...]      retractions, expressions of concern, corrections (batched)

Verdicts: validated (2+ independent sources agree and match the manuscript),
single-source (only one source answered: needs a second, e.g. publisher site),
conflict (sources disagree with each other), mismatch (sources agree, manuscript
differs: show the diff), not-found.

Optional env: CROSSREF_MAILTO (polite pool), OPENALEX_API_KEY, GOOGLE_BOOKS_API_KEY,
ZOTERO_CITATIONS_DSPACE (extra repositories: "name=d7:https://host,name2=os:https://host").
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from zotlib import (  # noqa: E402
    emit, env, fail, get_json, isbns_in, main_title, normalize_doi, normalize_isbn, request, surname_match,
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

# --------------------------------------------------------------------------- works without identifier

CATALOG_RETRIES = 1  # catalogs and repositories: fail fast and report `unavailable`
# Institutional repositories, verified 2026-10: `d7:` DSpace 7 REST, `os:` DSpace <= 6 OpenSearch.
REPOSITORIES = {
    "conicet": "os:https://ri.conicet.gov.ar",
    "ridaa-unq": "os:https://ridaa.unq.edu.ar",
    "filo-uba": "d7:https://repositorio.filo.uba.ar",
    "unne": "d7:https://repositorio.unne.edu.ar",
    "rdu-unc": "d7:https://rdu.unc.edu.ar",
    "rephip-unr": "d7:https://rephip.unr.edu.ar",
}
MODS = "{http://www.loc.gov/mods/v3}"
DC = "{http://purl.org/dc/elements/1.1/}"
ATOM = "{http://www.w3.org/2005/Atom}"


def repositories() -> dict[str, str]:
    repos = dict(REPOSITORIES)
    for spec in filter(None, (env("ZOTERO_CITATIONS_DSPACE") or "").split(",")):
        name, _, target = spec.strip().partition("=")
        if not re.match(r"(d7|os):https?://", target):
            fail(f"ZOTERO_CITATIONS_DSPACE entry {spec!r} must look like name=d7:https://host or name=os:https://host")
        repos[name] = target.rstrip("/")
    return repos


def independence_group(source: str) -> str:
    """Sources fed by the same records count once.

    LA Referencia harvests the national repository networks (Argentina's SNRD among
    them), so it and any institutional repository are one group; a record page read
    through Citoid is its own group unless it belongs to one of those repositories.
    """
    if source == "lareferencia" or source.startswith("repo:"):
        return "repositorios"
    if source.startswith("sitio:"):
        host = source[len("sitio:"):]
        repo_hosts = {urllib.parse.urlparse(spec[3:]).hostname for spec in repositories().values()}
        if host in repo_hosts or host.endswith(("hdl.handle.net", "lareferencia.info")):
            return "repositorios"
    return source


def _cql(text: str) -> str:
    return re.sub(r'["\\]', " ", text).strip()


def _solr(text: str) -> str:
    """Free-text query for Solr-backed search (DSpace, VuFind): `:`, quotes, brackets are syntax there."""
    return re.sub(r"\s+", " ", re.sub(r'[:"()\[\]{}^~*?\\/+!&|-]', " ", text)).strip()


def crossref_search(title: str, author: str | None, year: str | None) -> list[dict]:
    params = {"query.bibliographic": " ".join(p for p in (title, year) if p), "rows": 5,
              "select": "DOI,title,author,issued,published-print,published-online,container-title,type,publisher,page,volume,issue,ISBN,URL",
              "mailto": env("CROSSREF_MAILTO")}
    if author:
        params["query.author"] = author
    data = get_json("https://api.crossref.org/works", params=params, headers=_ua_headers(), timeout=TIMEOUT)
    return [_from_crossref(m) for m in ((data or {}).get("message") or {}).get("items", [])]


def openalex_search(title: str, author: str | None, year: str | None) -> list[dict]:
    key = env("OPENALEX_API_KEY")
    data = get_json("https://api.openalex.org/works", timeout=TIMEOUT,
                    params={"search": title, "per_page": 5, **({"api_key": key} if key else {})})
    return [_from_openalex(w) for w in (data or {}).get("results", [])]


def openlibrary_search(title: str, author: str | None, year: str | None) -> list[dict]:
    data = get_json("https://openlibrary.org/search.json", timeout=TIMEOUT, retries=CATALOG_RETRIES, params={
        "title": title, "author": author, "limit": 5,
        "fields": "title,subtitle,author_name,first_publish_year,publish_year,publisher,isbn,key"})
    records = []
    for doc in (data or {}).get("docs", []):
        years = {str(y) for y in doc.get("publish_year") or []}
        records.append(_record(
            "openlibrary", title=": ".join(p for p in (doc.get("title"), doc.get("subtitle")) if p),
            authors=[_family(a) for a in doc.get("author_name", [])], full_names=doc.get("author_name"),
            # A work groups every edition: report the cited edition's year when it exists.
            year=year_of(year) if year_of(year) in years else str(doc.get("first_publish_year") or "") or None,
            publisher=", ".join((doc.get("publisher") or [])[:2]), type="book",
            isbn=sorted(isbns_in(" ".join((doc.get("isbn") or [])[:10]))),
            url=f"https://openlibrary.org{doc['key']}" if doc.get("key") else None))
    return records


def _sru(url: str, query: str) -> ET.Element | None:
    resp = request("GET", url, timeout=TIMEOUT, retries=CATALOG_RETRIES, params={
        "version": "1.2" if "bne" in url else "1.1", "operation": "searchRetrieve", "query": query,
        "maximumRecords": 5, "recordSchema": "dc" if "bne" in url else "mods"})
    if resp.status != 200:
        return None
    try:
        return ET.fromstring(resp.body)
    except ET.ParseError:
        return None


def loc_search(title: str, author: str | None, year: str | None) -> list[dict]:
    """Library of Congress catalog, SRU (MODS). Only plain http on port 210 answers."""
    query = f'bath.title="{_cql(main_title(title))}"' + (f' and bath.author="{_cql(author)}"' if author else "")
    root = _sru("http://lx2.loc.gov:210/lcdb", query)
    records = []
    for mods in (root.iter(MODS + "mods") if root is not None else []):
        info = next((t for t in mods.findall(MODS + "titleInfo") if not t.get("type")), None)
        title_parts = [info.findtext(MODS + "title"), info.findtext(MODS + "subTitle")] if info is not None else []
        names = [n for n in mods.findall(MODS + "name") if n.get("type") == "personal"
                 and (n.get("usage") == "primary" or "author" in (n.findtext(f"{MODS}role/{MODS}roleTerm") or ""))]
        people = [(n.findtext(MODS + "namePart") or "").strip(" ,.") for n in names]
        lccn = next((i.text for i in mods.findall(MODS + "identifier") if i.get("type") == "lccn"), None)
        origin = mods.findall(MODS + "originInfo")
        records.append(_record(
            "loc", title=": ".join(p.strip(" /:") for p in title_parts if p),
            authors=[_family(p) for p in people], full_names=people,
            year=next((year_of(d.text) for o in origin for d in o.findall(MODS + "dateIssued") if year_of(d.text)), None),
            publisher=next((a.findtext(MODS + "namePart") for o in origin for a in o.findall(MODS + "agent")), None)
            or next((p.text for o in origin for p in o.findall(MODS + "publisher")), None),
            type="book", isbn=sorted(isbns_in(" ".join(i.text or "" for i in mods.findall(MODS + "identifier")
                                                      if i.get("type") == "isbn"))),
            url=f"https://lccn.loc.gov/{lccn.strip()}" if lccn else None))
    return records


def bne_search(title: str, author: str | None, year: str | None) -> list[dict]:
    """Biblioteca Nacional de España, SRU (Alma, Dublin Core)."""
    query = f'alma.title="{_cql(main_title(title))}"' + (f' AND alma.creator="{_cql(author)}"' if author else "")
    root = _sru("https://catalogo.bne.es/view/sru/34BNE_INST", query)
    records = []
    for dc in (root.iter("{info:srw/schema/1/dc-schema}dc") if root is not None else []):
        people = [c.text for c in dc.findall(DC + "creator") + dc.findall(DC + "contributor") if c.text]
        identifiers = [i.text or "" for i in dc.findall(DC + "identifier")]
        records.append(_record(
            "bne", title=re.sub(r"\s*\[[^\]]*\]\s*", " ", dc.findtext(DC + "title") or "").strip(" /:"),
            authors=[_family(re.sub(r"\s*\(?\d{4}-?(\d{4})?\)?\.?$", "", p)) for p in people], full_names=people,
            year=next((year_of(d.text) for d in dc.findall(DC + "date") if year_of(d.text)), None),
            publisher=", ".join(p.text for p in dc.findall(DC + "publisher") if p.text), type="book",
            isbn=sorted(isbns_in(" ".join(identifiers))),
            catalog_id=next((i for i in identifiers if i.startswith("alma:")), None)))
    return records


def lareferencia_search(title: str, author: str | None, year: str | None) -> list[dict]:
    """LA Referencia: Latin American repository network (theses, articles, reports)."""
    query = urllib.parse.urlencode([("lookfor", _solr(title)), ("type", "Title"), ("limit", 5)] + [
        ("field[]", f) for f in ("id", "title", "authors", "publicationDates", "formats", "institutions", "urls")])
    data = get_json(f"https://www.lareferencia.info/vufind/api/v1/search?{query}", timeout=TIMEOUT,
                    retries=CATALOG_RETRIES)
    records = []
    for r in (data or {}).get("records", []):
        people = list(((r.get("authors") or {}).get("primary") or {}).keys())
        records.append(_record(
            "lareferencia", title=r.get("title"), authors=[_family(p) for p in people], full_names=people,
            year=year_of((r.get("publicationDates") or [None])[0]), type=", ".join(r.get("formats") or []),
            publisher=", ".join(r.get("institutions") or []),
            url=((r.get("urls") or [{}])[0]).get("url") or f"https://www.lareferencia.info/vufind/Record/{r.get('id')}"))
    return records


def dspace_search(name: str, spec: str, title: str) -> list[dict]:
    kind, base = spec.split(":", 1)
    if kind == "d7":
        data = get_json(f"{base}/server/api/discover/search/objects", timeout=TIMEOUT, retries=CATALOG_RETRIES,
                        params={"query": _solr(title), "size": 5, "dsoType": "ITEM"})
        objects = (((data or {}).get("_embedded") or {}).get("searchResult") or {}).get("_embedded", {}).get("objects", [])
        records = []
        for obj in objects:
            item = (obj.get("_embedded") or {}).get("indexableObject") or {}
            meta = item.get("metadata") or {}

            def values(field, meta=meta):
                return [v.get("value") for v in meta.get(field, []) if v.get("value")]

            people = values("dc.contributor.author") or values("dc.creator")
            records.append(_record(
                f"repo:{name}", title=item.get("name") or (values("dc.title") or [None])[0],
                authors=[_family(p) for p in people], full_names=people, year=year_of((values("dc.date.issued") or [None])[0]),
                publisher=", ".join(values("dc.publisher")), type=", ".join(values("dc.type")),
                url=f"{base}/handle/{item['handle']}" if item.get("handle") else None))
        return records
    resp = request("GET", f"{base}/open-search/discover", timeout=TIMEOUT, retries=CATALOG_RETRIES,
                   params={"query": _solr(title), "rpp": 5, "format": "atom"})
    if resp.status != 200:
        return []
    try:
        feed = ET.fromstring(resp.body)
    except ET.ParseError:
        return []
    records = []
    for entry in feed.iter(ATOM + "entry"):
        people = [n.text for n in entry.iter(ATOM + "name") if n.text]
        link = entry.find(ATOM + "link")
        records.append(_record(
            f"repo:{name}", title=entry.findtext(ATOM + "title"), authors=[_family(p) for p in people], full_names=people,
            year=year_of(entry.findtext(ATOM + "published") or entry.findtext(DC + "date")),
            url=link.get("href") if link is not None else entry.findtext(ATOM + "id")))
    return records


def citoid_url(url: str) -> list[dict]:
    """The record's own page (journal, repository, catalog) read through Zotero translators."""
    items = citoid(url)
    if not items:
        return []
    item = items[0]
    return [_record(
        f"sitio:{urllib.parse.urlparse(url).hostname}", title=item.get("title"),
        authors=[c.get("lastName") or c.get("name") for c in item.get("creators", []) if c.get("creatorType") == "author"]
        or [c.get("lastName") or c.get("name") for c in item.get("creators", [])],
        year=year_of(item.get("date")), container=item.get("publicationTitle") or item.get("bookTitle"),
        volume=item.get("volume"), issue=item.get("issue"), pages=item.get("pages"),
        publisher=item.get("publisher") or item.get("university"), type=item.get("itemType"),
        doi=normalize_doi(item.get("DOI")), isbn=sorted(isbns_in(item.get("ISBN"))), url=item.get("url") or url)]


def work_sources() -> dict:
    sources = {"crossref": crossref_search, "openalex": openalex_search, "openlibrary": openlibrary_search,
               "loc": loc_search, "bne": bne_search, "lareferencia": lareferencia_search}
    for name, spec in repositories().items():
        sources[f"repo:{name}"] = lambda title, author, year, name=name, spec=spec: dspace_search(name, spec, title)
    return sources


def _score(candidate: dict, title: str, author: str | None, year: str | None) -> dict:
    t = title_similarity(title, candidate["title"])
    a = surname_match(author, (candidate["authors"] or [None])[0]) if author and candidate["authors"] else None
    y = 1.0 if not year or year_of(year) in {candidate["year"], candidate.get("online_year")} else 0.0
    candidate["score"] = round(0.6 * t + 0.25 * (0.5 if a is None else a) + 0.15 * y, 3)
    candidate["qualifies"] = t >= 0.9 and (a is None or a >= 0.7)
    return candidate


def validate_work(title: str, author: str | None, year: str | None, url: str | None = None,
                  only: list[str] | None = None) -> dict:
    """Works without DOI/ISBN: query catalogs and repositories, keep the best match per independence group."""
    sources = work_sources()
    if only:
        unknown = [s for s in only if s not in sources and f"repo:{s}" not in sources and s != "repos"]
        if unknown:
            fail(f"Unknown sources {unknown}; valid: {sorted(sources)} or 'repos'")
        wanted = {s if s in sources else f"repo:{s}" for s in only if s != "repos"}
        if "repos" in only:
            wanted |= {s for s in sources if s.startswith("repo:")}
        sources = {k: v for k, v in sources.items() if k in wanted}
    jobs = {name: (fn, (title, author, year)) for name, fn in sources.items()}
    if url:
        jobs[f"sitio:{urllib.parse.urlparse(url).hostname}"] = (lambda u, *_: citoid_url(u), (url,))
    errors, candidates = [], []

    def run(item):
        name, (fn, args) = item
        try:
            return name, fn(*args), None
        except (ConnectionError, ValueError, ET.ParseError) as err:
            return name, [], f"{name}: {err}"

    with ThreadPoolExecutor(max_workers=8) as pool:
        for _, found, error in pool.map(run, jobs.items()):
            if error:
                errors.append(error)
            candidates += [_score(c, title, author, year) for c in found if c.get("title")]
    best: dict[str, dict] = {}
    for c in sorted((c for c in candidates if c["qualifies"]), key=lambda c: -c["score"]):
        best.setdefault(independence_group(c["source"]), c)
    chosen = sorted(best.values(), key=lambda c: -c["score"])
    leads = sorted((c for c in candidates if c not in chosen and c["score"] >= 0.5), key=lambda c: -c["score"])[:5]
    expected = {"title": title, "author": author, "year": year}
    return {"searched": sorted(jobs), "groups": {independence_group(c["source"]): c["source"] for c in chosen},
            **verdict(chosen, expected, errors), "leads": leads,
            "note": "Each group counts once (LA Referencia + institutional repositories = one). Report the record URLs."}



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
    for name, fn in (("crossref", crossref_search), ("openalex", openalex_search)):
        try:
            candidates += fn(title, author, year)
        except ConnectionError as err:
            errors.append(f"{name}: {err}")
    for c in candidates:
        _score(c, title, author, year)
        c.pop("qualifies")
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
    p = sub.add_parser("work", help="works without DOI/ISBN: catalogs, repositories, record page")
    p.add_argument("--title", required=True), p.add_argument("--author"), p.add_argument("--year")
    p.add_argument("--url", help="landing page of the record (journal, repository, catalog), read via Citoid")
    p.add_argument("--sources", help="comma-separated subset, e.g. loc,bne,lareferencia,repos,conicet")
    p = sub.add_parser("payload")
    p.add_argument("identifier")
    p = sub.add_parser("integrity")
    p.add_argument("--dois", help="comma-separated DOIs")
    p.add_argument("--from", dest="sources", nargs="*", default=[], help="cite_audit and/or match JSON files")
    args = parser.parse_args()
    if args.command == "search":
        emit(search(args.title, args.author, args.year))
        return
    if args.command == "work":
        only = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
        emit(validate_work(args.title, args.author, args.year, args.url, only))
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
