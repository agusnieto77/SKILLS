import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import evidence  # noqa: E402
import source_check as sc  # noqa: E402


class AuditEvidence(unittest.TestCase):
    def test_hashes_original_bytes_and_occurrence_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, bib = Path(tmp) / "m.md", Path(tmp) / "refs.bib"
            path.write_bytes(b"Texto (Perez, 2001).\r\n")
            bib.write_text("@book{x,title={A}}", encoding="utf-8")
            data = {"citations": [{"raw": "(Perez, 2001)", "paragraph": 0, "origin": "body",
                                    "span": [6, 19], "context": "Texto (Perez, 2001)."}]}
            result = evidence.audit_evidence(data, path, [bib])
            self.assertEqual(result["binding"]["manuscript_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(result["binding"]["bibliographies"][0]["sha256"], hashlib.sha256(bib.read_bytes()).hexdigest())
            self.assertEqual(data["citations"][0]["occurrence"]["location"]["paragraph"], 0)
            self.assertIsNone(data["citations"][0]["occurrence"]["itemKey"])
            previous = {"evidence": result}
            self.assertEqual(evidence.audit_evidence(data, path, [bib], previous)["status"], "current")
            bib.write_text("@book{x,title={Changed}}", encoding="utf-8")
            stale = evidence.audit_evidence(data, path, [bib], previous)
            self.assertEqual(stale["status"], "stale")
            self.assertIn("bibliographies", stale["changed_inputs"])
            path.write_bytes(b"Otra oracion (Perez, 2001).")
            self.assertIn("manuscript_sha256", evidence.audit_evidence(data, path, [bib], previous)["changed_inputs"])

    def test_same_location_different_sentence_has_different_content_hash(self):
        first = {"raw": "@key", "paragraph": 0, "span": [10, 14], "context": "First sentence @key."}
        second = {**first, "context": "Other sentence @key."}
        a, b = evidence.occurrence(first, 0, "m.md"), evidence.occurrence(second, 0, "m.md")
        self.assertEqual(a["id"], b["id"])
        self.assertNotEqual(a["sha256"], b["sha256"])

    def test_audit_and_extract_outputs_bind_inputs_and_previous_audit(self):
        import cite_audit

        with tempfile.TemporaryDirectory() as tmp:
            manuscript, bib = Path(tmp) / "m.tex", Path(tmp) / "refs.bib"
            manuscript.write_text(r"Una afirmacion \cite{one}.", encoding="utf-8")
            bib.write_text("@book{one,author={Perez, Ana},title={Libro},year={2001}}", encoding="utf-8")
            report = cite_audit.audit(manuscript, None, bibliography_paths=[bib])
            self.assertEqual(report["evidence"]["binding"]["manuscript_sha256"], evidence.file_sha256(manuscript))
            self.assertEqual(len(report["citations"][0]["occurrence"]["id"]), 64)
            unchanged = cite_audit.audit(manuscript, None, bibliography_paths=[bib], previous=report)
            self.assertEqual(unchanged["evidence"]["status"], "current")
            bib.write_text("@book{one,author={Perez, Ana},title={Otro libro},year={2001}}", encoding="utf-8")
            changed = cite_audit.audit(manuscript, None, bibliography_paths=[bib], previous=report)
            self.assertEqual(changed["evidence"]["status"], "stale")
            extracted = cite_audit.extract(manuscript, bibliography_paths=[bib])
            self.assertEqual(extracted["evidence"]["binding"]["bibliographies"][0]["sha256"], evidence.file_sha256(bib))


class Provider:
    name = "offline"

    def __init__(self):
        self.content = "La crisis salarial produjo una huelga general en la ciudad."
        self.info = {"status": "ok", "itemKey": "ITEM0001", "item_version": 3,
                     "attachmentKey": "ATT00001", "attachment_version": 8, "indexedPages": 1, "totalPages": 1}

    def load(self, _key):
        return sc.SourceText(self.content), dict(self.info)


class FidelityEvidence(unittest.TestCase):
    def setUp(self):
        self.audit = {"file": "m.md", "evidence": {"binding": {"manuscript_sha256": "a" * 64}},
                      "citations": [{"raw": "(Perez, 2001)", "paragraph": 0, "origin": "body", "span": [50, 63],
                                     "context": "La crisis salarial produjo una huelga general (Perez, 2001).",
                                     "ref_indexes": [0], "authors": ["Perez"], "quotes": []}]}
        self.matches = {"matches": [{"index": 0, "status": "strong", "best": {"key": "ITEM0001", "version": 3}}]}
        self.provider = Provider()

    def check(self, previous=None):
        return sc.check(self.audit, self.matches, self.provider, 2, True, previous=previous)

    def prior(self):
        previous = self.check()
        previous["results"][0]["judgement"] = {"verdict": "fiel", "passage": "La crisis salarial", "page": 1}
        return previous

    def test_binding_covers_hashes_versions_and_location(self):
        result = self.check()
        binding = result["results"][0]["evidence"]["binding"]
        self.assertEqual(binding["source_text_sha256"], hashlib.sha256(self.provider.content.encode()).hexdigest())
        self.assertEqual((binding["itemKey"], binding["attachmentKey"], binding["item_version"], binding["attachment_version"]),
                         ("ITEM0001", "ATT00001", 3, 8))
        self.assertEqual(binding["occurrence"]["location"]["paragraph"], 0)
        self.assertEqual(len(binding["audit_sha256"]), 64)
        self.assertEqual(len(binding["match_sha256"]), 64)
        self.assertIn("checked_at", result["results"][0]["evidence"])

    def test_unchanged_inputs_reuse_only_same_occurrence_judgement(self):
        previous = self.prior()
        row = self.check(previous)["results"][0]
        self.assertEqual(row["evidence"]["status"], "current")
        self.assertEqual(row["judgement"], previous["results"][0]["judgement"])

    def test_each_changed_input_invalidates_previous_conclusion(self):
        for field in ("text", "item_version", "attachment_version", "attachmentKey", "context", "manuscript", "match"):
            with self.subTest(field=field):
                self.setUp()
                previous = self.prior()
                if field == "text":
                    self.provider.content += " Nuevo texto."
                elif field in self.provider.info:
                    self.provider.info[field] = 99 if field.endswith("version") else "ATT00002"
                elif field == "context":
                    self.audit["citations"][0]["context"] = "Una afirmacion completamente diferente."
                elif field == "manuscript":
                    self.audit["evidence"]["binding"]["manuscript_sha256"] = "b" * 64
                else:
                    self.matches["matches"][0]["best"]["title"] = "Cambio"
                row = self.check(previous)["results"][0]
                self.assertEqual(row["evidence"]["status"], "stale")
                self.assertNotIn("judgement", row)
                self.assertIn("previous_judgement", row)

    def test_moved_occurrence_never_inherits_conclusion(self):
        previous = self.prior()
        self.audit["citations"][0]["paragraph"] = 2
        row = self.check(previous)["results"][0]
        self.assertEqual(row["evidence"]["status"], "stale")
        self.assertNotIn("judgement", row)

    def test_missing_fulltext_invalidates_old_judgement(self):
        previous = self.prior()
        with mock.patch.object(self.provider, "load", return_value=(None, {"status": "not-indexed"})):
            row = self.check(previous)["results"][0]
        self.assertEqual(row["status"], "no-fulltext")
        self.assertEqual(row["evidence"]["status"], "stale")
        self.assertNotIn("judgement", row)

    def test_legacy_unbound_conclusion_cannot_be_reused(self):
        previous = copy.deepcopy(self.prior())
        previous["results"][0].pop("evidence")
        row = self.check(previous)["results"][0]
        self.assertEqual(row["evidence"]["status"], "stale")
        self.assertNotIn("judgement", row)

    def test_unknown_versions_prevent_reuse_even_with_unchanged_hashes(self):
        self.provider.info.pop("attachment_version")
        previous = self.prior()
        row = self.check(previous)["results"][0]
        self.assertEqual(row["evidence"]["status"], "stale")
        self.assertFalse(row["evidence"]["reusable"])
        self.assertNotIn("judgement", row)

    def test_manuscript_changed_since_audit_invalidates_without_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            manuscript = Path(tmp) / "m.md"
            manuscript.write_text("Una oracion nueva.", encoding="utf-8")
            self.audit["file"] = str(manuscript)
            row = self.check()["results"][0]
        self.assertEqual(row["evidence"]["status"], "stale")
        self.assertIn("manuscript_since_audit", row["evidence"]["changed_inputs"])

    def test_quote_and_passages_commands_include_source_binding(self):
        for command, arguments in (("quote", ["--text", "La crisis salarial produjo una huelga"]),
                                   ("passages", ["--query", "crisis salarial"])):
            with self.subTest(command=command), mock.patch.object(sc, "ZoteroText", return_value=self.provider), \
                    mock.patch.object(sc, "emit") as emit, mock.patch.object(sys, "argv", ["source_check", command, "ITEM0001", *arguments]):
                sc.main()
            result = emit.call_args.args[0]
            self.assertEqual(result["evidence"]["binding"]["itemKey"], "ITEM0001")
            self.assertEqual(result["evidence"]["binding"]["source_text_sha256"], evidence.text_sha256(self.provider.content))

    def test_check_cli_hashes_exact_json_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_path, match_path = Path(tmp) / "audit.json", Path(tmp) / "match.json"
            audit_path.write_text(json.dumps(self.audit, indent=4), encoding="utf-8")
            match_path.write_text(json.dumps(self.matches, indent=3), encoding="utf-8")
            with mock.patch.object(sc, "ZoteroText", return_value=self.provider), mock.patch.object(sc, "emit") as emit, \
                    mock.patch.object(sys, "argv", ["source_check", "check", str(audit_path), str(match_path)]):
                sc.main()
            binding = emit.call_args.args[0]["results"][0]["evidence"]["binding"]
            self.assertEqual(binding["audit_sha256"], evidence.file_sha256(audit_path))
            self.assertEqual(binding["match_sha256"], evidence.file_sha256(match_path))


class ZoteroMetadata(unittest.TestCase):
    def test_provider_records_parent_and_attachment_versions(self):
        provider = object.__new__(sc.ZoteroText)
        provider.name = "offline"
        responses = [
            {"key": "ITEM0001", "version": 3, "data": {"key": "ITEM0001", "pages": "1-2"}},
            [{"key": "ATT00001", "version": 8, "data": {"key": "ATT00001", "itemType": "attachment",
                                                       "contentType": "application/pdf"}}],
            {"content": "Texto completo", "indexedPages": 1, "totalPages": 2},
        ]
        with mock.patch.object(provider, "_get", side_effect=responses), mock.patch.object(provider, "annotations", return_value=[]):
            source, info = provider.load("ITEM0001")
        self.assertIsNotNone(source)
        self.assertEqual((info["item_version"], info["attachment_version"]), (3, 8))
        self.assertTrue(info["partial_index"])


if __name__ == "__main__":
    unittest.main()
