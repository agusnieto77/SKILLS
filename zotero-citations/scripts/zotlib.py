"""Shared helpers for the zotero-citations scripts (stdlib only).

Covers: configuration and secret masking, HTTP with Zotero rate-limit handling,
text normalization, identifier normalization (DOI/ISBN) and fuzzy scoring.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "zotero-citations/3.0 (+https://www.zotero.org/support/dev/web_api/v3/start)"


def web_base() -> str:
    return os.environ.get("ZOTERO_API_BASE", "https://api.zotero.org").rstrip("/")


def local_base() -> str:
    # 127.0.0.1, not localhost: on Windows `localhost` tries ::1 first and Zotero only
    # listens on IPv4, which costs ~2 s per request.
    return os.environ.get("ZOTERO_LOCAL_BASE", "http://127.0.0.1:23119/api").rstrip("/")


def cache_dir() -> Path:
    return Path(os.environ.get("ZOTERO_CITATIONS_CACHE") or Path.home() / ".cache" / "zotero-citations")


# Non-bibliographic item types that must never be matched or rendered as references.
NON_BIB_TYPES = {"attachment", "note", "annotation"}


# --------------------------------------------------------------------------- config

def env(name: str, default: str | None = None) -> str | None:
    """Read an env var; on Windows fall back to the user registry hive.

    Processes started before `setx` do not inherit new user variables, which made
    credentials look missing even though they were configured.
    """
    value = os.environ.get(name)
    if value:
        return value
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                return winreg.QueryValueEx(key, name)[0] or default
        except OSError:
            pass
    return default


def mask(secret: str | None) -> str:
    if not secret:
        return "<unset>"
    return f"length {len(secret)}, prefix {secret[:6]}..."


def library_prefix(library_id: str | None = None, library_type: str | None = None) -> str:
    library_id = library_id or env("ZOTERO_LIBRARY_ID")
    library_type = (library_type or env("ZOTERO_LIBRARY_TYPE", "user")).lower()
    if not library_id:
        fail("ZOTERO_LIBRARY_ID is not set (run `zotero_client.py whoami` to discover the userID).")
    if library_type not in ("user", "group"):
        fail(f"ZOTERO_LIBRARY_TYPE must be 'user' or 'group', got {library_type!r}.")
    return f"/{library_type}s/{library_id}"


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def emit(data) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --------------------------------------------------------------------------- http

class HttpResponse:
    def __init__(self, status: int, headers: dict, body: bytes):
        self.status = status
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.body = body

    def header(self, name: str) -> str | None:
        return self.headers.get(name.lower())

    @property
    def text(self) -> str:
        # The local Zotero API omits the charset; everything Zotero/Crossref emits is UTF-8.
        return self.body.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text) if self.body else None


_backoff_until = 0.0


def request(method: str, url: str, *, params: dict | None = None, headers: dict | None = None,
            body=None, timeout: float = 30, retries: int = 4, retry_unsafe: bool = False) -> HttpResponse:
    """HTTP request honoring Zotero `Backoff` and `Retry-After`.

    GET/HEAD retry on 429, 5xx and network errors. Other methods only retry on 429
    (the server rejected them, so nothing was applied) unless `retry_unsafe` is set,
    which callers use for POSTs protected by a Zotero-Write-Token.
    """
    global _backoff_until
    if params:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = f"{url}{'&' if '?' in url else '?'}{query}"
    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    idempotent = method in ("GET", "HEAD") or retry_unsafe
    attempt = 0
    while True:
        wait = _backoff_until - time.time()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = HttpResponse(resp.status, dict(resp.headers), resp.read())
        except urllib.error.HTTPError as err:
            result = HttpResponse(err.code, dict(err.headers or {}), err.read() or b"")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            if idempotent and attempt < retries:
                time.sleep(2 ** attempt)
                attempt += 1
                continue
            raise ConnectionError(f"{method} {url.split('?')[0]} failed: {err}") from err
        backoff = result.header("Backoff")
        if backoff and backoff.isdigit():
            _backoff_until = time.time() + int(backoff)
        retryable = result.status == 429 or (idempotent and result.status >= 500)
        if retryable and attempt < retries:
            retry_after = result.header("Retry-After")
            time.sleep(int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt)
            attempt += 1
            continue
        return result


def get_json(url: str, **kwargs):
    resp = request("GET", url, **kwargs)
    if resp.status != 200:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


# --------------------------------------------------------------------------- text

PARTICLES = {"de", "del", "la", "las", "los", "da", "das", "do", "dos", "di", "van", "von", "der", "den", "le", "du", "y", "e"}


def fold(text: str | None) -> str:
    """Casefold and strip diacritics; keep letters, digits and spaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text.casefold())
    return re.sub(r"\s+", " ", text).strip()


def main_title(title: str | None) -> str:
    return re.split(r"[:.?!]\s", title or "", maxsplit=1)[0]


def title_similarity(a: str | None, b: str | None) -> float:
    fa, fb = fold(a), fold(b)
    if not fa or not fb:
        return 0.0
    full = difflib.SequenceMatcher(None, fa, fb).ratio()
    short = difflib.SequenceMatcher(None, fold(main_title(a)), fold(main_title(b))).ratio()
    # A manuscript often drops or keeps the subtitle; the main title alone is a
    # strong signal only when it is long enough not to be generic.
    if len(fold(main_title(a))) >= 20 and len(fold(main_title(b))) >= 20:
        return max(full, short * 0.97)
    return full


def surname_key(name: str | None) -> str:
    """Normalized family name: folded, particles kept but leading ones dropped."""
    tokens = fold(name).split()
    while len(tokens) > 1 and tokens[0] in PARTICLES:
        tokens = tokens[1:]
    return " ".join(tokens)


def surname_match(a: str | None, b: str | None) -> float:
    ka, kb = surname_key(a), surname_key(b)
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 1.0
    ta, tb = set(ka.split()), set(kb.split())
    # Compound Spanish surnames are often cited with only the first element.
    if ka.split()[0] == kb.split()[0] or ta <= tb or tb <= ta:
        return 0.7
    return 0.0


def year_of(value) -> str | None:
    match = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", str(value or ""))
    return match.group(1) if match else None


def year_match(a, b) -> float:
    ya, yb = year_of(a), year_of(b)
    if not ya and not yb:
        return 1.0
    if not ya or not yb:
        return 0.3
    if ya == yb:
        return 1.0
    return 0.5 if abs(int(ya) - int(yb)) == 1 else 0.0


# --------------------------------------------------------------------------- identifiers

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    match = DOI_RE.search(urllib.parse.unquote(value))
    if not match:
        return None
    return match.group(0).rstrip(".,;)]}>").lower()


def _isbn10_ok(digits: str) -> bool:
    total = sum((10 - i) * (10 if c in "Xx" else int(c)) for i, c in enumerate(digits))
    return total % 11 == 0


def _isbn13_ok(digits: str) -> bool:
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(digits))
    return total % 10 == 0


def normalize_isbn(value: str | None) -> str | None:
    """Return a checksum-valid ISBN-13, or None."""
    if not value:
        return None
    raw = re.sub(r"[^0-9Xx]", "", value)
    if len(raw) == 10 and re.fullmatch(r"\d{9}[\dXx]", raw) and _isbn10_ok(raw):
        core = "978" + raw[:9]
        check = (10 - sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(core)) % 10) % 10
        return core + str(check)
    if len(raw) == 13 and raw.isdigit() and _isbn13_ok(raw):
        return raw
    return None


def isbns_in(value: str | None) -> set[str]:
    """All valid ISBNs in a Zotero ISBN field (which may hold several)."""
    found = set()
    for token in re.findall(r"(?<![\dXx])(?:97[89][\- ]?)?(?:\d[\- ]?){9}[\dXx](?![\dXx])", value or ""):
        isbn = normalize_isbn(token)
        if isbn:
            found.add(isbn)
    return found


def item_doi(data: dict) -> str | None:
    """DOI from the DOI field, or from `extra` for item types lacking that field."""
    doi = normalize_doi(data.get("DOI"))
    if doi:
        return doi
    match = re.search(r"^DOI:\s*(\S+)", data.get("extra") or "", re.I | re.M)
    return normalize_doi(match.group(1)) if match else None


def first_author(creators: list[dict] | None) -> str | None:
    for creator in creators or []:
        if creator.get("creatorType") in ("author", "editor", "artist", "cartographer", "programmer", None):
            return creator.get("lastName") or creator.get("name")
    if creators:
        return creators[0].get("lastName") or creators[0].get("name")
    return None


def load_json_file(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
