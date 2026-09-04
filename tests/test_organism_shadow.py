"""Contracts using a captured board snapshot, never fabricated measurements."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io

from ofn.adapters import organism_shadow as bridge
from ofn.adapters import self_model_producer as producer
from shadow_homeostasis.canonical import digest
from shadow_homeostasis.evidence_store import EvidenceStore, LedgerError

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "09-LANES/BOARD-EXEC-001-INTEGRATION-001/SOURCE-SNAPSHOT.json"
GITATTRIBUTES = ROOT / "shadow_homeostasis" / ".gitattributes"
_SHADOW = ROOT / "shadow_homeostasis"

# windows-latest job 101053713534 @930e0cc94f91a861b6797ffe874d077f31832427
# (PR #194, 2026-09-04). Autocrlf rewrites LF→CRLF. That is a checkout
# artefact, not a source change. The LF blob is the contract.
# Pin: shadow_homeostasis/.gitattributes. This-host LF→CRLF of
# registry.py MATCH prior GAP-193 witness cfa730c9… .
_FREEZE_LF = {
    "registry.py": "e3ef142d2254c0e430b98c39f244dfb14e7e4ecd33ef58b8ad3d348daefa767b",
    "metacontrol.py": "a731adcddc37517d813157ce9355686e9a4eb9d61c378dfb71b494746d5a97cf",
}
_FREEZE_CRLF = {
    "registry.py": "cfa730c9d9cda268f89b69c7b11ef8a1dec8f5d9d390a0db36f1d098d2e96ae4",
    "metacontrol.py": "43abbc04c15fcd9c9f2a34ddb6a4a91f1c7a93ad35d54c907653aefebc75c826",
}


def _canonical_bytes(data: bytes) -> bytes:
    """LF identity. CRLF checkout is not a contract edit."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _canonical_sha256(data: bytes) -> str:
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


class OrganismShadowTests(unittest.TestCase):
    def setUp(self):
        self.capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
        self.model = self.capture["model"]
        self.now = self.capture["generated_epoch"]
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "advisory"

    def assess(self, model=None, **kwargs):
        return bridge.assess_snapshot(self.model if model is None else model,
                                      now_epoch=self.now, **kwargs)

    def test_captured_source_identity_and_frozen_files(self):
        self.assertEqual(self.capture["source_sha256"], "8e2a1b3c256a58013e2dab212a27984f03d30b6dd09b0808d9df192a915293ec")
        # Preferred pin: .gitattributes eol=lf.
        # Second witness: LF-canonical hash, so a runner that still
        # converts checkout bytes cannot fake a source-hash miss.
        # Pattern: tests/test_brain_schema.py / test_runtime_truth_contract_frozen.py.
        for name, sha in _FREEZE_LF.items():
            raw = (_SHADOW / name).read_bytes()
            self.assertEqual(_canonical_sha256(raw), sha)

    def test_windows_crlf_checkout_is_a_known_hash_not_the_source(self):
        """Second witness: the windows-latest failure hash is LF→CRLF, not a new source."""
        for name, crlf_sha in _FREEZE_CRLF.items():
            lf = _canonical_bytes((_SHADOW / name).read_bytes())
            crlf = lf.replace(b"\n", b"\r\n")
            self.assertEqual(hashlib.sha256(crlf).hexdigest(), crlf_sha)
            self.assertNotEqual(crlf_sha, _FREEZE_LF[name])
            self.assertEqual(_canonical_sha256(crlf), _FREEZE_LF[name])

    def test_hashed_shadow_checkout_is_pinned_lf(self):
        self.assertTrue(GITATTRIBUTES.is_file())
        text = GITATTRIBUTES.read_text(encoding="utf-8")
        self.assertIn("eol=lf", text)
        self.assertIn("*.py", text)

    def test_content_edit_breaks_freeze(self):
        for name, sha in _FREEZE_LF.items():
            mutated = _canonical_bytes((_SHADOW / name).read_bytes()) + b"\n# mutated\n"
            self.assertNotEqual(_canonical_sha256(mutated), sha)

    def test_lone_cr_normalizes_to_lf_identity(self):
        for name, sha in _FREEZE_LF.items():
            lf = _canonical_bytes((_SHADOW / name).read_bytes())
            lone_cr = lf.replace(b"\n", b"\r")
            self.assertEqual(_canonical_sha256(lone_cr), sha)

    def test_actual_rows_deterministic_and_input_preserved(self):
        before = copy.deepcopy(self.model)
        one, two = self.assess(), self.assess()
        self.assertEqual(one, two)
        self.assertEqual(before, self.model)
        self.assertEqual(len(one["source_observations"]), 20)
        self.assertEqual(one["signal"]["source_authentication"], "UNVERIFIED")
        self.assertFalse(one["executable"])
        self.assertEqual(one["action_authority"], "NONE")
        self.assertEqual(one["assessment_hash"], digest({k:v for k,v in one.items() if k != "assessment_hash"}))

    def test_missing_physiology_not_reported_healthy(self):
        result = self.assess()
        self.assertEqual(result["body_state"], "UNKNOWN")
        self.assertEqual(result["resources"]["state"], "UNKNOWN")
        self.assertIsNone(result["resources"]["measured_cpu_pct"])
        self.assertEqual(result["business_legs"], [])
        self.assertEqual(result["calibration"]["n"], 0)
        self.assertIsNone(result["calibration"]["brier_score"])
        self.assertIsNone(result["node_id"])
        self.assertIsNone(result["boot_id"])
        self.assertEqual(result["topology"]["connectivity_state"], "UNKNOWN")
        self.assertIsNone(result["topology"]["measured_isolation"])
        self.assertIsNone(result["topology"]["measured_degradation"])

    def test_absent_capability_times_not_filled_with_now(self):
        result = self.assess()
        rows = [r for r in result["pipeline"]["observations"] if "capability_" in r["metric"]]
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(r["occurred_at"] is None and r["quality"] != "VALID" for r in rows))

    def test_boolean_and_contradictory_liveness_contracts(self):
        for group in ("processes", "capabilities"):
            for invalid in ("true", 1, None, False):
                model = copy.deepcopy(self.model)
                model[group][0]["value"] = invalid
                result = self.assess(model)
                row = next(r for r in result["source_observations"] if r["sensor_id"] == model[group][0]["sensor_id"])
                self.assertEqual(row["status"], "unknown")

    def test_malformed_clock_and_freshness_fail_closed(self):
        for invalid in (True, float("nan"), float("inf"), 10**1000, "180"):
            with self.assertRaises(ValueError):
                bridge.assess_snapshot(self.model, now_epoch=invalid)
            with self.assertRaises(ValueError):
                self.assess(process_max_age=invalid)
        with self.assertRaises(ValueError):
            self.assess(process_max_age=-1)

    def test_untrusted_source_text_not_retained(self):
        model = copy.deepcopy(self.model)
        model["processes"][0]["source"] = "not-an-authorized-source"
        model["processes"][0]["detail"] = "DO_NOT_RETAIN_FREE_TEXT"
        result = self.assess(model)
        serialized = json.dumps(result)
        self.assertNotIn("DO_NOT_RETAIN_FREE_TEXT", serialized)
        self.assertNotIn("not-an-authorized-source", serialized)

    def test_bounded_contract_and_unique_ids(self):
        model = copy.deepcopy(self.model)
        model["processes"].append(model["processes"][0])
        with self.assertRaises(ValueError):
            self.assess(model)
        with self.assertRaises(ValueError):
            self.assess({"processes": self.model["processes"] * 11})
        with self.assertRaises(ValueError):
            self.assess(node_id="../other")

    def test_tampering_rejected_before_journal(self):
        assessment = self.assess()
        assessment["body_state"] = "NOMINAL"
        with self.assertRaises(ValueError):
            bridge.record_assessment(assessment, self.root)
        self.assertFalse((self.root / "journal.jsonl").exists())

    def test_persistence_idempotent_and_checkpoint_consistent(self):
        assessment = self.assess()
        one = bridge.record_assessment(assessment, self.root)
        raw = (self.root / "journal.jsonl").read_bytes()
        two = bridge.record_assessment(assessment, self.root)
        self.assertEqual(one, two)
        self.assertEqual(raw, (self.root / "journal.jsonl").read_bytes())
        self.assertEqual(one["logical_records"], 4)
        checkpoint = json.loads((self.root / "checkpoint.json").read_text())
        self.assertEqual(checkpoint["next_input_index"], 1)
        self.assertEqual(checkpoint["committed_head_hash"], one["journal_head"])
        self.assertEqual(one["owner_requests"][0]["state"], "PENDING")
        self.assertEqual(len(one["recall"]), 1)

    def test_executable_provenance_cannot_cross_writer(self):
        with self.assertRaises(ValueError):
            bridge.record_assessment(self.assess(), self.root, code_provenance={"executable": True})
        self.assertFalse((self.root / "journal.jsonl").exists())

    def test_torn_journal_not_repaired(self):
        assessment = self.assess()
        bridge.record_assessment(assessment, self.root)
        path = self.root / "journal.jsonl"
        with path.open("ab") as handle:
            handle.write(b"{torn")
        broken = path.read_bytes()
        with self.assertRaises(LedgerError):
            bridge.record_assessment(assessment, self.root)
        self.assertEqual(path.read_bytes(), broken)

    def test_checkpoint_corruption_not_repaired(self):
        assessment = self.assess()
        bridge.record_assessment(assessment, self.root)
        path = self.root / "checkpoint.json"
        raw = json.loads(path.read_text())
        raw["committed_head_hash"] = "0" * 64
        path.write_text(json.dumps(raw))
        before = (self.root / "journal.jsonl").read_bytes()
        with self.assertRaises(ValueError):
            bridge.record_assessment(assessment, self.root)
        self.assertEqual((self.root / "journal.jsonl").read_bytes(), before)
        self.assertEqual(json.loads(path.read_text()), raw)

    def test_storage_budget_failure_preserves_journal(self):
        assessment = self.assess()
        bridge.record_assessment(assessment, self.root)
        before = (self.root / "journal.jsonl").read_bytes()
        with patch.object(bridge.ArtifactBudget, "require", side_effect=ValueError("cap")):
            with self.assertRaises(ValueError):
                bridge.record_assessment(assessment, self.root)
        self.assertEqual((self.root / "journal.jsonl").read_bytes(), before)

    def test_producer_read_path_has_no_journal_writes(self):
        with patch.object(bridge, "record_assessment", side_effect=AssertionError("write on read path")):
            result = producer.produce(repo_root=ROOT)
        self.assertIn("organism_shadow", result)
        self.assertNotIn("organism_shadow_persistence", result)

    def test_failed_code_witness_is_explicitly_unverifiable(self):
        with patch.object(producer.runtime_provenance, "code_witness", return_value={"matched":False}):
            result = producer.produce(repo_root=ROOT)
        self.assertEqual(result["status"], "unverifiable")
        self.assertIn("runtime_code_witness_unverified", result["warnings"])

    def test_cli_persistence_failure_returns_nonzero_with_failure_artifact(self):
        output = self.root / "self-model.json"
        with patch.object(bridge, "record_assessment", side_effect=ValueError("test-owned fault")):
            with contextlib.redirect_stdout(io.StringIO()):
                result = producer.main(["--repo", str(ROOT), "--output", str(output)])
        saved = json.loads(output.read_text())
        self.assertEqual(result, 1)
        self.assertEqual(saved["status"], "unverifiable")
        self.assertEqual(saved["organism_shadow_persistence"]["state"], "FAILED_PRESERVE_JOURNAL")
        self.assertIn("organism_shadow_persistence_failed", saved["warnings"])

    @unittest.skipIf(os.name == "nt", "POSIX board permissions/link contract")
    def test_all_child_symlink_paths_rejected_without_writes(self):
        self.root.mkdir(mode=0o700)
        target = self.root.parent / "external"
        target.write_bytes(b"keep")
        for name in ("WRITER.jsonl", "WRITER.jsonl.lock", "journal.jsonl", "journal.jsonl.lock",
                     "checkpoint.json", "checkpoint.json.pending", "OWNER-INBOX.md", "OWNER-INBOX.md.pending"):
            link = self.root / name
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                bridge.record_assessment(self.assess(), self.root)
            self.assertEqual(target.read_bytes(), b"keep")
            link.unlink()  # Exactly this test-owned symlink, never target contents.

    @unittest.skipIf(os.name == "nt", "POSIX board permissions contract")
    def test_nonprivate_directory_rejected(self):
        self.root.mkdir(mode=0o755)
        with self.assertRaises(ValueError):
            bridge.record_assessment(self.assess(), self.root)
        self.assertFalse((self.root / "journal.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
