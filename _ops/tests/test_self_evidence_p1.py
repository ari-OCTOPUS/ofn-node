#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_audit/self_insight must bind Done to real on-disk evidence."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("self-evidence-p1")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import self_audit as sa  # noqa: E402
import self_insight as si  # noqa: E402


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


class CalibrationProbeTests(unittest.TestCase):
    def test_missing_calibration_is_not_done(self):
        with mock.patch.object(sa, "_calibration_latest_path",
                               return_value=Path(tempfile.mkdtemp()) / "nope.json"):
            with mock.patch.object(sa, "_self_claims_path",
                                   return_value=Path(tempfile.mkdtemp()) / "nope.jsonl"):
                item = sa._probe_calibration_evidence()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))
        self.assertNotEqual(item["status"], "Done")

    def test_stubbed_schema_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        cal = root / "calibration-latest.json"
        claims = root / "self-claims.jsonl"
        _write_json(cal, {"schema": "stub.v0", "n": 99, "brier": 0.1})
        claims.write_text('{"k":1}\n', encoding="utf-8")
        with mock.patch.object(sa, "_calibration_latest_path", return_value=cal):
            with mock.patch.object(sa, "_self_claims_path", return_value=claims):
                item = sa._probe_calibration_evidence()
        self.assertEqual(item["status"], "Partial")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_n_zero_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        cal = root / "calibration-latest.json"
        claims = root / "self-claims.jsonl"
        _write_json(cal, {"schema": "calibration.v1", "n": 0, "brier": 0.1})
        claims.write_text('{"k":1}\n', encoding="utf-8")
        with mock.patch.object(sa, "_calibration_latest_path", return_value=cal):
            with mock.patch.object(sa, "_self_claims_path", return_value=claims):
                item = sa._probe_calibration_evidence()
        self.assertEqual(item["status"], "Partial")
        self.assertNotEqual(item["status"], "Done")

    def test_fixture_evidence_is_done(self):
        root = Path(tempfile.mkdtemp())
        cal = root / "calibration-latest.json"
        claims = root / "self-claims.jsonl"
        _write_json(cal, {"schema": "calibration.v1", "n": 7, "brier": 0.33})
        claims.write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
        with mock.patch.object(sa, "_calibration_latest_path", return_value=cal):
            with mock.patch.object(sa, "_self_claims_path", return_value=claims):
                item = sa._probe_calibration_evidence()
        self.assertEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))
        self.assertIn("brier=0.330000", item["evidence"])
        self.assertIn("lines=2", item["evidence"])

    def test_real_vault_calibration_reads_or_honest_missing(self):
        """Against live STATE: Done only if files really parse."""
        item = sa._probe_calibration_evidence()
        self.assertTrue(item.get("evidence_bound"))
        cal_p = sa._calibration_latest_path()
        claims_p = sa._self_claims_path()
        if cal_p.exists() and claims_p.exists():
            data = json.loads(cal_p.read_text(encoding="utf-8"))
            if (data.get("schema") == "calibration.v1"
                    and isinstance(data.get("n"), (int, float)) and int(data["n"]) > 0
                    and isinstance(data.get("brier"), (int, float))
                    and sum(1 for l in claims_p.read_text(encoding="utf-8").splitlines()
                            if l.strip()) > 0):
                self.assertEqual(item["status"], "Done", item)
            else:
                self.assertNotEqual(item["status"], "Done", item)
        else:
            self.assertNotEqual(item["status"], "Done", item)


class TraceBasedProbeTests(unittest.TestCase):
    def test_missing_vitals_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "doctor-vitals.json"
        with mock.patch.object(sa, "_doctor_vitals_path", return_value=missing):
            item = sa._probe_trace_based_analysis()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_vitals_schema_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        p = root / "doctor-vitals.json"
        _write_json(p, {"schema": "wrong", "missions_open": {"value": 0, "provenance": "exogenous"}})
        with mock.patch.object(sa, "_doctor_vitals_path", return_value=p):
            item = sa._probe_trace_based_analysis()
        self.assertEqual(item["status"], "Partial")
        self.assertNotEqual(item["status"], "Done")

    def test_fixture_vitals_with_exogenous_is_done(self):
        root = Path(tempfile.mkdtemp())
        p = root / "doctor-vitals.json"
        _write_json(p, {
            "schema": "doctor-vitals.v1",
            "missions_merged": {"value": 1, "provenance": "exogenous"},
        })
        with mock.patch.object(sa, "_doctor_vitals_path", return_value=p):
            with mock.patch.object(sa, "_grep", return_value=True):
                item = sa._probe_trace_based_analysis()
        self.assertEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))


class RunAuditEvidenceFlagTests(unittest.TestCase):
    def test_run_audit_reports_evidence_bound_and_not_static_only(self):
        r = sa.run_audit(write=False)
        self.assertGreaterEqual(r.get("evidence_bound_n", 0), 2)
        self.assertFalse(r.get("static_by_construction"))
        eb = [it for it in r["items"] if it.get("evidence_bound")]
        self.assertGreaterEqual(len(eb), 2)
        for it in eb:
            # evidence_bound probes never invent Done without a status gate
            self.assertIn(it["status"], ("Done", "Partial", "Missing", "Unknown"))


class InsightDiskEvidenceTests(unittest.TestCase):
    def test_missing_files_evidence_ok_false(self):
        root = Path(tempfile.mkdtemp())
        ev = si.load_disk_evidence(root)
        self.assertFalse(ev["ok"])
        out = si.run_once_journal(root, limit=5)
        self.assertFalse(out["evidence_ok"])
        self.assertIn("disk_evidence", out)

    def test_stubbed_calibration_evidence_ok_false(self):
        root = Path(tempfile.mkdtemp())
        cortex = root / "state" / "cortex"
        cortex.mkdir(parents=True)
        _write_json(cortex / "calibration-latest.json",
                    {"schema": "nope", "n": 5, "brier": 0.2})
        (cortex / "self-claims.jsonl").write_text('{"x":1}\n', encoding="utf-8")
        ev = si.load_disk_evidence(root)
        self.assertFalse(ev["ok"])
        self.assertIn("schema", ev.get("error", ""))

    def test_fixture_evidence_ok_true(self):
        root = Path(tempfile.mkdtemp())
        cortex = root / "state" / "cortex"
        cortex.mkdir(parents=True)
        _write_json(cortex / "calibration-latest.json",
                    {"schema": "calibration.v1", "n": 9, "brier": 0.19, "ts": "t"})
        (cortex / "self-claims.jsonl").write_text('{"a":1}\n{"b":2}\n{"c":3}\n',
                                                    encoding="utf-8")
        ev = si.load_disk_evidence(root)
        self.assertTrue(ev["ok"])
        self.assertEqual(ev["n"], 9)
        self.assertEqual(ev["n_claims_file"], 3)
        out = si.run_once_journal(root, limit=5)
        self.assertTrue(out["evidence_ok"])
        self.assertEqual(out["disk_evidence"]["brier"], 0.19)


if __name__ == "__main__":
    # keep harness-style + unittest dual entry
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
