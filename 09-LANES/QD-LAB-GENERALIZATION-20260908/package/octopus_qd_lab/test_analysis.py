"""Post-run evidence-binding regression tests; never alter the frozen experiment."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from dataclasses import asdict
from analyze import validate_tests_record, verify_run_bundle
from experiment import dump_json, digest_file
from map_elites import Config, run
from octopus_bridge import ReceiptLedger


class TestRecordChecks(unittest.TestCase):
    def good(self):
        return {"tests_run": 1, "failures": 0, "errors": 0, "skipped": 0,
                "successful": True, "test_hashes": {"test.py": "a"*64}, "scope": "local"}

    def test_positive_suite(self):
        self.assertTrue(validate_tests_record(self.good()))

    def test_truthy_text_rejected(self):
        for bad in ("false", "true", 1, None):
            t = self.good()
            t["successful"] = bad
            with self.assertRaises(ValueError):
                validate_tests_record(t)

    def test_missing_empty_failed_skipped_rejected(self):
        for key, value in (("tests_run", 0), ("tests_run", True), ("failures", 1),
                           ("errors", 1), ("skipped", 1), ("test_hashes", {})):
            t = self.good()
            t[key] = value
            with self.assertRaises(ValueError):
                validate_tests_record(t)
        t = self.good()
        del t["errors"]
        with self.assertRaises(ValueError):
            validate_tests_record(t)


class RunBindingChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.dir = root / "full_seed7"
        self.dir.mkdir()
        config = Config(grid=8, batch=4, initial=8, generations=1)
        self.study = {"config": asdict(config), "scientific_code_sha256": {"test_fixture": "a"*64}}
        self.path = root / "study.json"
        dump_json(self.path, self.study)
        with ReceiptLedger(self.dir / "receipts.jsonl") as ledger:
            ledger.append("protocol_bound", {"study_sha256": digest_file(self.path),
                                            "scientific_code_sha256": self.study["scientific_code_sha256"]}, 0)
            archive, history, stats = run(7, config, "full", ledger, verbose=False)
            archive.save(self.dir / "archive.npz")
            dump_json(self.dir / "history.json", history)
            dump_json(self.dir / "operators.json", stats)
            payload = {"archive_sha256": digest_file(self.dir / "archive.npz"),
                       "history_sha256": digest_file(self.dir / "history.json"),
                       "operators_sha256": digest_file(self.dir / "operators.json"),
                       "metrics": history[-1], "tests_ok": True}
            last = ledger.append("run_completed", payload, 1)
        self.summary = {"mode": "full", "seed": 7, "config": asdict(config), "final": history[-1],
                        "receipt_anchor": {"head": last["hash"], "count": 5},
                        "file_hashes": {n: digest_file(self.dir / n) for n in
                                       ("archive.npz", "history.json", "operators.json", "receipts.jsonl")}}
        self.save()

    def save(self):
        dump_json(self.dir / "run_summary.json", self.summary)

    def verify(self):
        return verify_run_bundle(self.dir, self.study, self.path)

    def test_valid_bundle(self):
        _, _, check = self.verify()
        self.assertIs(check["metrics_bound_to_history_receipts_and_archive"], True)

    def test_unhashed_summary_metric_tampering_rejected(self):
        self.summary["final"]["qd_score"] += 20
        self.save()
        with self.assertRaises(ValueError):
            self.verify()

    def test_empty_hash_manifest_rejected(self):
        self.summary["file_hashes"] = {}
        self.save()
        with self.assertRaises(ValueError):
            self.verify()

    def test_identity_tampering_rejected(self):
        self.summary["seed"] = 11
        self.save()
        with self.assertRaises(ValueError):
            self.verify()

    def test_rehashed_history_without_receipt_change_rejected(self):
        path = self.dir / "history.json"
        h = json.loads(path.read_text())
        h[-1]["qd_score"] += 10
        dump_json(path, h)
        self.summary["file_hashes"]["history.json"] = digest_file(path)
        self.save()
        with self.assertRaises(ValueError):
            self.verify()


if __name__ == "__main__":
    unittest.main()
