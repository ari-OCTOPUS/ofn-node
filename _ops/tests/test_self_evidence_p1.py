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
        self.assertGreaterEqual(r.get("evidence_bound_n", 0), 8)
        self.assertFalse(r.get("static_by_construction"))
        eb = [it for it in r["items"] if it.get("evidence_bound")]
        self.assertGreaterEqual(len(eb), 4)
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




class DashboardProbeTests(unittest.TestCase):
    def test_missing_vitals_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        with mock.patch.object(sa, "_heartstate_path", return_value=root / "hs.json"):
            with mock.patch.object(sa, "_work_health_path", return_value=root / "wh.json"):
                with mock.patch.object(sa, "_read", return_value=None):
                    item = sa._probe_dashboard()
        self.assertTrue(item.get("evidence_bound"))
        self.assertEqual(item["status"], "Missing")
        self.assertNotEqual(item["status"], "Done")

    def test_stubbed_schema_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        hs = root / "heartstate-latest.json"
        wh = root / "work-health.json"
        _write_json(hs, {"schema": "wrong", "ts": "t"})
        _write_json(wh, {"nope": 1})
        with mock.patch.object(sa, "_heartstate_path", return_value=hs):
            with mock.patch.object(sa, "_work_health_path", return_value=wh):
                item = sa._probe_dashboard()
        self.assertEqual(item["status"], "Partial")
        self.assertNotEqual(item["status"], "Done")

    def test_fixture_heartstate_and_work_health_is_done(self):
        root = Path(tempfile.mkdtemp())
        hs = root / "heartstate-latest.json"
        wh = root / "work-health.json"
        _write_json(hs, {"schema": "heartstate.v1", "ts": "2026-08-22T00:00:00"})
        _write_json(wh, {"month_aud": 1.0, "gate0": False})
        with mock.patch.object(sa, "_heartstate_path", return_value=hs):
            with mock.patch.object(sa, "_work_health_path", return_value=wh):
                item = sa._probe_dashboard()
        self.assertEqual(item["status"], "Done", item)
        self.assertTrue(item.get("evidence_bound"))
        self.assertIn("heartstate.v1", item["evidence"])
        self.assertIn("work-health", item["evidence"])


class StopConditionProbeTests(unittest.TestCase):
    def test_missing_calibration_py_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "calibration.py"
        with mock.patch.object(sa, "_calibration_py_path", return_value=missing):
            item = sa._probe_stop_condition()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_wrong_caps_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "calibration.py"
        py.write_text(
            "PENDING_SOFT_CAP = 9\nPENDING_HARD_CAP = 5\nREJECT_FORGET_N = 3\n"
            "def should_skip_bottleneck(db, bottleneck_key):\n    return False, ''\n"
            "def attention_gate(db, pending_count, severity):\n    return True, ''\n",
            encoding="utf-8",
        )
        with mock.patch.object(sa, "_calibration_py_path", return_value=py):
            item = sa._probe_stop_condition()
        self.assertEqual(item["status"], "Partial")
        self.assertNotEqual(item["status"], "Done")

    def test_fixture_caps_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "calibration.py"
        py.write_text(
            "PENDING_SOFT_CAP = 3\nPENDING_HARD_CAP = 5\nREJECT_FORGET_N = 3\n"
            "def should_skip_bottleneck(db, bottleneck_key):\n    return False, ''\n"
            "def attention_gate(db, pending_count, severity):\n    return True, ''\n",
            encoding="utf-8",
        )
        with mock.patch.object(sa, "_calibration_py_path", return_value=py):
            item = sa._probe_stop_condition()
        self.assertEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))
        self.assertIn("REJECT_FORGET_N=3", item["evidence"])


class PollHealthProbeTests(unittest.TestCase):
    def test_missing_poll_health_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "poll-health.json"
        with mock.patch.object(sa, "_poll_health_path", return_value=missing):
            item = sa._probe_poll_health()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_counters_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        ph = root / "poll-health.json"
        _write_json(ph, {"consecutive_failures": 0, "counters": {}, "last_progress_at": 0})
        with mock.patch.object(sa, "_poll_health_path", return_value=ph):
            item = sa._probe_poll_health()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_poll_health_is_done(self):
        root = Path(tempfile.mkdtemp())
        ph = root / "poll-health.json"
        _write_json(ph, {
            "consecutive_failures": 0,
            "counters": {"poll_started_total": 10, "poll_completed_total": 9},
            "last_progress_at": 1787370000.5,
        })
        with mock.patch.object(sa, "_poll_health_path", return_value=ph):
            item = sa._probe_poll_health()
        self.assertEqual(item["status"], "Done")
        self.assertIn("fails=0", item["evidence"])
        self.assertIn("started=10", item["evidence"])


class InsightPollAndBrierCardTests(unittest.TestCase):
    def test_load_disk_evidence_reads_poll_health_counters(self):
        root = Path(tempfile.mkdtemp())
        cortex = root / "state" / "cortex"
        tg = root / "state" / "telegram"
        cortex.mkdir(parents=True)
        tg.mkdir(parents=True)
        _write_json(cortex / "calibration-latest.json",
                    {"schema": "calibration.v1", "n": 4, "brier": 0.25, "ts": "t"})
        (cortex / "self-claims.jsonl").write_text('{"a":1}\n', encoding="utf-8")
        _write_json(tg / "poll-health.json", {
            "consecutive_failures": 2,
            "counters": {"poll_started_total": 5, "poll_completed_total": 3},
            "last_progress_at": 100.0,
        })
        ev = si.load_disk_evidence(root)
        self.assertTrue(ev["ok"])
        self.assertEqual(ev["brier"], 0.25)
        self.assertEqual(ev["poll_health"]["consecutive_failures"], 2)
        self.assertEqual(ev["poll_health"]["poll_started_total"], 5)

    def test_card_surfaces_brier_and_n(self):
        root = Path(tempfile.mkdtemp())
        state = root / "state"
        cortex = state / "cortex"
        cortex.mkdir(parents=True)
        _write_json(cortex / "calibration-latest.json",
                    {"schema": "calibration.v1", "n": 11, "brier": 0.123456, "ts": "t"})
        (cortex / "self-claims.jsonl").write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
        # journal with empty hypotheses so card renders calibration section
        (state / "self-insight.jsonl").write_text(
            json.dumps({"schema": "self-insight.v1", "ts": 1.0, "hypotheses": [],
                        "calibration": {}} ) + "\n",
            encoding="utf-8",
        )
        text = si.card(root)
        self.assertIn("Brier=0.123456", text)
        self.assertIn("n=11", text)

    def test_run_once_journal_includes_poll_health(self):
        root = Path(tempfile.mkdtemp())
        cortex = root / "state" / "cortex"
        tg = root / "state" / "telegram"
        cortex.mkdir(parents=True)
        tg.mkdir(parents=True)
        _write_json(cortex / "calibration-latest.json",
                    {"schema": "calibration.v1", "n": 3, "brier": 0.4, "ts": "t"})
        (cortex / "self-claims.jsonl").write_text('{"a":1}\n', encoding="utf-8")
        _write_json(tg / "poll-health.json", {
            "consecutive_failures": 1,
            "counters": {"poll_started_total": 7, "poll_completed_total": 6},
            "last_progress_at": 50.0,
        })
        out = si.run_once_journal(root, limit=5)
        self.assertTrue(out["evidence_ok"])
        self.assertEqual(out["disk_evidence"]["brier"], 0.4)
        self.assertEqual(out["disk_evidence"]["poll_health"]["consecutive_failures"], 1)


class RunAuditEvidenceBoundFloorTests(unittest.TestCase):
    def test_run_audit_has_at_least_four_evidence_bound(self):
        r = sa.run_audit(write=False)
        self.assertGreaterEqual(r.get("evidence_bound_n", 0), 8)
        eb_items = [it for it in r["items"] if it.get("evidence_bound")]
        self.assertGreaterEqual(len(eb_items), 4)
        needles = ("dashboard", "stop-condition", "poll-health", "calibration", "trace-based", "shadow-eval", "regression suite", "routing logic", "blind-vs-informed")
        blob = " ".join(it["item"].lower() for it in eb_items)
        hits = sum(1 for n in needles if n in blob)
        self.assertGreaterEqual(hits, 6, blob)



class ShadowBeforePromoteProbeTests(unittest.TestCase):
    def test_missing_doctor_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "doctor.py"
        with mock.patch.object(sa, "_doctor_py_path", return_value=missing):
            item = sa._probe_shadow_before_promote()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))
        self.assertNotEqual(item["status"], "Done")

    def test_stubbed_doctor_without_sandbox_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "doctor.py"
        py.write_text("# empty stub\nclass Doctor:\n    pass\n", encoding="utf-8")
        with mock.patch.object(sa, "_doctor_py_path", return_value=py):
            item = sa._probe_shadow_before_promote()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_sandbox_lift_tempfile_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "doctor.py"
        body = chr(10).join([
            "import tempfile",
            "def run_sandbox(self, rfc):",
            "    d = tempfile.mkdtemp(prefix='doctor-sandbox-')",
            "    return {'measured_lift': 0.1}",
            "# measured_lift used by evolution",
            "",
        ])
        py.write_text(body, encoding="utf-8")
        with mock.patch.object(sa, "_doctor_py_path", return_value=py):
            item = sa._probe_shadow_before_promote()
        self.assertEqual(item["status"], "Done", item)
        self.assertTrue(item.get("evidence_bound"))
        self.assertIn("run_sandbox=True", item["evidence"])


class RegressionSuiteProbeTests(unittest.TestCase):
    def test_missing_run_all_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "run_all.py"
        with mock.patch.object(sa, "_run_all_py_path", return_value=missing):
            item = sa._probe_regression_suite()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_thin_tests_list_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        ra = root / "run_all.py"
        ra.write_text('TESTS = ["test_a.py"]' + chr(10), encoding="utf-8")
        (root / "test_a.py").write_text("#" + chr(10), encoding="utf-8")
        with mock.patch.object(sa, "_run_all_py_path", return_value=ra):
            item = sa._probe_regression_suite()
        self.assertEqual(item["status"], "Partial")
        self.assertNotEqual(item["status"], "Done")

    def test_fixture_suite_with_held_out_and_cap_is_done(self):
        root = Path(tempfile.mkdtemp())
        names = [f"test_{i}.py" for i in range(25)]
        names[0] = "test_held_out_evaluator.py"
        names[1] = "test_capability_gate.py"
        for n in names:
            (root / n).write_text("#" + chr(10), encoding="utf-8")
        ra = root / "run_all.py"
        body_lines = ["TESTS = ["] + [f'    "{n}",' for n in names] + ["]"]
        ra.write_text(chr(10).join(body_lines) + chr(10), encoding="utf-8")
        with mock.patch.object(sa, "_run_all_py_path", return_value=ra):
            item = sa._probe_regression_suite()
        self.assertEqual(item["status"], "Done", item)
        self.assertTrue(item.get("evidence_bound"))
        self.assertIn("held_out=True", item["evidence"])


class DeterministicRoutingProbeTests(unittest.TestCase):
    def test_missing_e2e_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "test_telegram_poll_e2e.py"
        with mock.patch.object(sa, "_routing_e2e_path", return_value=missing):
            item = sa._probe_deterministic_routing_tests()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_e2e_without_matrix_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "test_telegram_poll_e2e.py"
        py.write_text("# no tests here" + chr(10), encoding="utf-8")
        with mock.patch.object(sa, "_routing_e2e_path", return_value=py):
            item = sa._probe_deterministic_routing_tests()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_dispatch_matrix_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "test_telegram_poll_e2e.py"
        src = chr(10).join([
            "# dispatch matrix",
            "def t_a_menu():",
            "    ch.poll_once()",
            "    assert 'menu:'",
            "def t_b_now():",
            "    ch.poll_once()",
            "def t_c_foreign():",
            "    callback_query = {}",
            "    ch.poll_once()",
            "def t_d_drop():",
            "    ch.poll_once()",
            "MENU = 'menu:overview'",
            "",
        ])
        py.write_text(src, encoding="utf-8")
        with mock.patch.object(sa, "_routing_e2e_path", return_value=py):
            item = sa._probe_deterministic_routing_tests()
        self.assertEqual(item["status"], "Done", item)
        self.assertIn("t_defs=4", item["evidence"])


class BlindInformedProbeTests(unittest.TestCase):
    def test_missing_sog_math_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "sog_math.py"
        with mock.patch.object(sa, "_sog_math_path", return_value=missing):
            item = sa._probe_blind_informed()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_sog_math_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "sog_math.py"
        py.write_text("def unrelated():" + chr(10) + "    return 1" + chr(10), encoding="utf-8")
        with mock.patch.object(sa, "_sog_math_path", return_value=py):
            item = sa._probe_blind_informed()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_blind_informed_syms_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "sog_math.py"
        body = chr(10).join([
            "# blind vs informed",
            "def delta_self(fl):",
            "    return 0.0",
            "def e_shadow(fl):",
            "    return 0.0",
            "def mc_witness_core(**kw):",
            "    return {}",
            "",
        ])
        py.write_text(body, encoding="utf-8")
        with mock.patch.object(sa, "_sog_math_path", return_value=py):
            item = sa._probe_blind_informed()
        self.assertEqual(item["status"], "Done", item)
        self.assertTrue(item.get("evidence_bound"))


if __name__ == "__main__":
    # keep harness-style + unittest dual entry
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
