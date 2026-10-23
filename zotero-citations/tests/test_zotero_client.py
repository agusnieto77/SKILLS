import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent


class MockZotero(BaseHTTPRequestHandler):
    """Minimal Zotero Web API: write tokens, versions, batches, per-item failures."""

    calls: list = []
    seen_tokens: set = set()
    item_version = 5
    rate_limit_next = 0
    existing: list = []
    library: list = []  # (version, data) pairs served for snapshot requests
    library_version = 10
    deleted_since: dict = {}

    def log_message(self, *args):
        pass

    def _send(self, status, body=None, headers=None):
        payload = json.dumps(body).encode() if body is not None else b""
        self.send_response(status)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"null")

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        MockZotero.calls.append(("GET", url.path, query, dict(self.headers), None))
        if url.path.endswith("/items/top"):
            q = query.get("q", [""])[0].lower()
            if q:
                hits = [{"key": i["key"], "version": 1, "data": i} for i in self.existing if q in json.dumps(i).lower()]
                return self._send(200, hits, {"Last-Modified-Version": str(self.library_version)})
            since = int(query.get("since", ["0"])[0])
            start, limit = int(query.get("start", ["0"])[0]), int(query.get("limit", ["100"])[0])
            page = [{"key": d["key"], "version": v, "data": d} for v, d in self.library if v > since][start:start + limit]
            return self._send(200, page, {"Last-Modified-Version": str(self.library_version)})
        if url.path.endswith("/deleted"):
            keys = [k for k, v in self.deleted_since.items() if v > int(query.get("since", ["0"])[0])]
            return self._send(200, {"items": keys, "collections": [], "searches": [], "tags": []})
        if "/items/" in url.path:
            key = url.path.rsplit("/", 1)[1]
            data = {"key": key, "version": self.item_version, "itemType": "book", "title": "Old title",
                    "creators": [], "date": "2001", "tags": [], "collections": [], "relations": {}}
            return self._send(200, {"key": key, "version": self.item_version, "data": data},
                              {"Last-Modified-Version": str(self.item_version)})
        return self._send(404, {})

    def do_POST(self):
        body = self._body()
        token = self.headers.get("Zotero-Write-Token")
        MockZotero.calls.append(("POST", self.path, None, dict(self.headers), body))
        if MockZotero.rate_limit_next:
            MockZotero.rate_limit_next -= 1
            return self._send(429, {}, {"Retry-After": "0"})
        if not token or len(token) != 32:
            return self._send(400, {"error": "bad token"})
        if token in MockZotero.seen_tokens:
            return self._send(412, {})
        MockZotero.seen_tokens.add(token)
        if len(body) > 50:
            return self._send(413, {})
        success, failed = {}, {}
        for index, item in enumerate(body):
            if item.get("title") == "FAIL":
                failed[str(index)] = {"key": "", "code": 400, "message": "boom"}
            else:
                success[str(index)] = f"K{len(MockZotero.calls):03d}{index:04d}"[:8]
        return self._send(200, {"success": success, "unchanged": {}, "failed": failed}, {"Last-Modified-Version": "11"})

    def do_PATCH(self):
        body = self._body()
        MockZotero.calls.append(("PATCH", self.path, None, dict(self.headers), body))
        if self.headers.get("If-Unmodified-Since-Version") != str(self.item_version):
            return self._send(412, {})
        return self._send(204, None, {"Last-Modified-Version": str(self.item_version + 1)})


SERVER = ThreadingHTTPServer(("127.0.0.1", 0), MockZotero)
threading.Thread(target=SERVER.serve_forever, daemon=True).start()
CACHE = tempfile.mkdtemp()
os.environ.update({
    "ZOTERO_API_BASE": f"http://127.0.0.1:{SERVER.server_port}",
    "ZOTERO_LOCAL_BASE": "http://127.0.0.1:9/api",  # nothing listens: local API unavailable
    "ZOTERO_API_KEY": "testkeytestkeytestkey123",
    "ZOTERO_LIBRARY_ID": "1",
    "ZOTERO_LIBRARY_TYPE": "user",
    "ZOTERO_SCHEMA_FILE": str(HERE / "fixtures" / "schema-min.json"),
    "ZOTERO_CITATIONS_CACHE": CACHE,
})
sys.path.insert(0, str(HERE.parent / "scripts"))

import zotero_client as zc  # noqa: E402
import zotlib  # noqa: E402


def book(title="A book on unions", **extra):
    return {"itemType": "book", "title": title, "creators": [{"creatorType": "author", "lastName": "Acha", "firstName": "Omar"}],
            "date": "2015", **extra}


class WriteBase(unittest.TestCase):
    def setUp(self):
        MockZotero.calls = []
        MockZotero.seen_tokens = set()
        MockZotero.rate_limit_next = 0
        MockZotero.existing = []

    def posts(self):
        return [c for c in MockZotero.calls if c[0] == "POST"]


class CreateTests(WriteBase):
    def test_dry_run_never_writes(self):
        result = zc.create([book()], confirm=False, collection=None, audit_tags=False, allow_duplicate=False)
        self.assertTrue(result["dry_run"])
        self.assertEqual(self.posts(), [])

    def test_batches_of_50_with_unique_tokens_and_global_indexes(self):
        items = [book(f"Book number {n}") for n in range(120)]
        items[73]["title"] = "FAIL"
        result = zc.create(items, confirm=True, collection="COLL1234", audit_tags=True, allow_duplicate=False)
        posts = self.posts()
        self.assertEqual([len(p[4]) for p in posts], [50, 50, 20])
        tokens = {p[3]["Zotero-Write-Token"] for p in posts}
        self.assertEqual(len(tokens), 3)
        self.assertEqual(len(result["created"]), 119)
        self.assertEqual(result["failed"], [{"index": 73, "code": 400, "message": "boom"}])
        self.assertEqual(result["created"][-1]["index"], 119)
        sent = posts[0][4][0]
        self.assertEqual(sent["collections"], ["COLL1234"])
        self.assertIn({"tag": "citation-audited"}, sent["tags"])

    def test_existing_doi_blocks_creation(self):
        MockZotero.existing = [{"key": "DUPE0001", "itemType": "journalArticle", "title": "X", "DOI": "10.1234/abc", "creators": []}]
        item = {"itemType": "journalArticle", "title": "X", "DOI": "10.1234/ABC", "creators": []}
        dry = zc.create([item], confirm=False, collection=None, audit_tags=False, allow_duplicate=False)
        self.assertEqual([d["key"] for d in dry["duplicates"]["0"]], ["DUPE0001"])
        with self.assertRaises(SystemExit):
            zc.create([item], confirm=True, collection=None, audit_tags=False, allow_duplicate=False)
        self.assertEqual(self.posts(), [])

    def test_schema_errors_block_creation(self):
        with self.assertRaises(SystemExit):
            zc.create([book(abstract="x")], confirm=True, collection=None, audit_tags=False, allow_duplicate=False)
        self.assertEqual(self.posts(), [])

    def test_429_is_retried_with_same_token(self):
        MockZotero.rate_limit_next = 1
        result = zc.create([book()], confirm=True, collection=None, audit_tags=False, allow_duplicate=False)
        posts = self.posts()
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0][3]["Zotero-Write-Token"], posts[1][3]["Zotero-Write-Token"])
        self.assertEqual(len(result["created"]), 1)


class PatchTests(WriteBase):
    def test_stale_version_refuses_before_writing(self):
        with self.assertRaises(SystemExit):
            zc.patch("ITEM0001", {"title": "New"}, 4, confirm=True)
        self.assertFalse([c for c in MockZotero.calls if c[0] == "PATCH"])

    def test_patch_sends_version_precondition_and_diff(self):
        result = zc.patch("ITEM0001", {"title": "New title"}, 5, confirm=True)
        patch = [c for c in MockZotero.calls if c[0] == "PATCH"][0]
        self.assertEqual(patch[3]["If-Unmodified-Since-Version"], "5")
        self.assertEqual(patch[4], {"title": "New title"})
        self.assertEqual(result["diff"], [{"field": "title", "before": "Old title", "after": "New title"}])
        self.assertEqual(result["log"][0]["new_version"], "6")

    def test_server_side_conflict_is_reported(self):
        MockZotero.item_version = 5
        original = MockZotero.do_PATCH

        def conflict(handler):
            handler._body()
            MockZotero.calls.append(("PATCH", handler.path, None, dict(handler.headers), None))
            handler._send(412, {})

        MockZotero.do_PATCH = conflict
        try:
            with self.assertRaises(SystemExit):
                zc.patch("ITEM0001", {"title": "New"}, 5, confirm=True)
        finally:
            MockZotero.do_PATCH = original

    def test_trash_is_a_reversible_patch(self):
        zc.patch("ITEM0001", {"deleted": 1}, 5, confirm=True, action="trash")
        patch = [c for c in MockZotero.calls if c[0] == "PATCH"][0]
        self.assertEqual(patch[4], {"deleted": 1})
        self.assertFalse([c for c in MockZotero.calls if c[0] == "DELETE"])


class CheckTests(unittest.TestCase):
    def test_type_specific_field_names(self):
        result = zc.check_items([
            {"itemType": "report", "title": "R", "publisher": "X"},
            {"itemType": "photograph", "title": "P"},
            {"itemType": "letter", "title": "Carta", "creators": [{"creatorType": "recipient", "lastName": "Girri"}]},
        ])
        self.assertEqual(result[0]["errors"], ["field 'publisher' is called 'institution' in report"])
        self.assertEqual(result[1]["errors"], ["itemType 'photograph' does not exist (use 'artwork')"])
        self.assertEqual(result[2]["errors"], [])

    def test_identifier_and_date_rules(self):
        errors = zc.check_items([book(ISBN="978-0-201-89683-2", DOI="doi:10.1234/x", date="s. f.")])[0]["errors"]
        self.assertTrue(any("ISBN checksum" in e for e in errors))
        self.assertTrue(any("DOI must be bare" in e for e in errors))
        self.assertTrue(any("undated" in e for e in errors))


def library_item(key, title, creators, date, doi=None, isbn=None, trashed=False):
    return {"key": key, "version": 1, "itemType": "book", "title": title, "creators": creators, "date": date,
            "DOI": doi, "ISBN": [isbn] if isbn else [], "container": None, "inTrash": trashed}


class MatchTests(unittest.TestCase):
    LIBRARY = [
        library_item("AAAA1111", "Lucha y organización: repensar en la Argentina la historia de la clase obrera", ["Acha"], "2015"),
        library_item("BBBB2222", "The art of computer programming", ["Knuth"], "1997", isbn="9780201896831"),
        library_item("CCCC3333", "Artificial intelligence and illusions of understanding", ["Messeri", "Crockett"], "2024",
                     doi="10.1038/s41586-024-07146-0"),
        library_item("DDDD4444", "Breve historia contemporánea de la Argentina", ["Romero"], "2012"),
        library_item("EEEE5555", "Libro borrado", ["Nadie"], "2000", trashed=True),
    ]

    def match(self, **ref):
        ref.setdefault("authors", [])
        return zc.match_refs([ref], self.LIBRARY)[0]

    def test_identifiers_win_even_with_isbn10(self):
        self.assertEqual(self.match(doi="10.1038/s41586-024-07146-0", title="whatever")["status"], "exact-doi")
        self.assertEqual(self.match(isbn=zotlib.normalize_isbn("0-201-89683-4"), title="x")["best"]["key"], "BBBB2222")

    def test_fuzzy_title_without_subtitle(self):
        result = self.match(title="Lucha y organización", authors=["Acha"], year="2015")
        self.assertEqual((result["status"], result["best"]["key"]), ("strong", "AAAA1111"))

    def test_other_edition_is_flagged_not_silently_accepted(self):
        result = self.match(title="Breve historia contemporánea de la Argentina", authors=["Romero"], year="2001")
        self.assertEqual(result["status"], "strong-diff")
        self.assertEqual([d["field"] for d in result["best"]["diffs"]], ["year"])

    def test_trash_and_absent(self):
        self.assertEqual(self.match(title="Libro borrado", authors=["Nadie"], year="2000")["status"], "trashed")
        self.assertEqual(self.match(title="Un título que no existe en la biblioteca", authors=["Lobato"], year="2001")["status"], "none")


class OrderedAuthorDiffTests(unittest.TestCase):
    def item(self, authors, **extra):
        return {**library_item("AUTH0001", "A study", authors, "2024"), **extra}

    def reference(self, authors, **extra):
        return {"title": "A study", "year": "2024", "authors": authors, **extra}

    def test_invented_second_author_is_reported_with_same_first_and_count(self):
        diffs = zc.diff_fields(self.reference(["Messeri", "Inventado"]),
                               self.item(["Messeri", "Crockett"]))
        self.assertEqual([(d["field"], d["position"]) for d in diffs], [("authors", 2)])

    def test_reordered_coauthors_are_reported_at_each_position(self):
        diffs = zc.diff_fields(self.reference(["Messeri", "Quirós", "Crockett"]),
                               self.item(["Messeri", "Crockett", "Quirós"]))
        self.assertEqual([d["position"] for d in diffs], [2, 3])

    def test_particle_and_diacritic_variants_are_not_substitutions(self):
        self.assertEqual(zc.diff_fields(self.reference(["de la Cruz", "Quirós", "van Beethoven"]),
                                        self.item(["Cruz", "Quiros", "Beethoven"])), [])

    def test_etal_allows_only_matching_prefix_and_rejects_extra_declaration(self):
        item = self.item(["Messeri", "Crockett", "Quirós"])
        self.assertEqual(zc.diff_fields(self.reference(["Messeri", "Crockett"], etal=True), item), [])
        self.assertTrue(zc.diff_fields(self.reference(["Messeri", "Inventado"], etal=True), item))
        self.assertTrue(zc.diff_fields(self.reference(["Messeri", "Crockett", "Quirós"], etal=True), item))

    def test_corporate_author_is_not_a_person(self):
        item = self.item(["Atlas"], creator_details=[{"literal": "Atlas"}])
        self.assertEqual(zc.diff_fields(self.reference(["Atlas"], corporate=True), item), [])
        self.assertTrue(zc.diff_fields(self.reference(["Atlas"]), item))

    def test_summarize_preserves_consortium_metadata_and_primary_order(self):
        result = zc.summarize({"title": "A study", "creators": [
            {"creatorType": "author", "firstName": "Ana", "lastName": "de la Cruz"},
            {"creatorType": "editor", "lastName": "Editor"},
            {"creatorType": "author", "name": "Atlas Consortium"}]})
        self.assertEqual(result["creators"], ["de la Cruz", "Atlas Consortium"])
        self.assertEqual(result["creator_details"], [{"family": "de la Cruz", "given": "Ana"},
                                                     {"literal": "Atlas Consortium"}])
        self.assertGreater(zc.SNAPSHOT_FORMAT, 2)


class SnapshotSyncTests(WriteBase):
    def test_incremental_refresh_applies_changes_and_deletions(self):
        def entry(key, title, version):
            return (version, {"key": key, "version": version, "itemType": "book", "title": title, "creators": [], "date": "2000"})

        MockZotero.library = [entry("KEEP0001", "Kept", 3), entry("EDIT0001", "Before", 4), entry("GONE0001", "Gone", 5)]
        MockZotero.library_version, MockZotero.deleted_since = 5, {}
        items, _ = zc.snapshot("web")
        self.assertEqual({i["key"] for i in items}, {"KEEP0001", "EDIT0001", "GONE0001"})

        MockZotero.library = [entry("KEEP0001", "Kept", 3), entry("EDIT0001", "After", 7), entry("NEW00001", "New", 8)]
        MockZotero.library_version, MockZotero.deleted_since = 8, {"GONE0001": 6}
        MockZotero.calls = []
        items, _ = zc.snapshot("web")
        self.assertEqual({i["key"]: i["title"] for i in items}, {"KEEP0001": "Kept", "EDIT0001": "After", "NEW00001": "New"})
        fetches = [c for c in MockZotero.calls if c[1].endswith("/items/top") and "since" in c[2]]
        self.assertEqual([c[2]["since"] for c in fetches], [["5"]])


if __name__ == "__main__":
    unittest.main()
