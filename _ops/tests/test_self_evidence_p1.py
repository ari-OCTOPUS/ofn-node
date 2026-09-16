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
        self.assertGreaterEqual(r.get("evidence_bound_n", 0), 14)
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
        self.assertGreaterEqual(r.get("evidence_bound_n", 0), 14)
        eb_items = [it for it in r["items"] if it.get("evidence_bound")]
        self.assertGreaterEqual(len(eb_items), 4)
        needles = ("dashboard", "stop-condition", "poll-health", "calibration", "trace-based", "shadow-eval", "regression suite", "routing logic", "blind-vs-informed", "kill switch", "watchdog", "approval gates", "secrets isolated", "dry-run", "rollback path")
        blob = " ".join(it["item"].lower() for it in eb_items)
        hits = sum(1 for n in needles if n in blob)
        self.assertGreaterEqual(hits, 10, blob)



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




class KillSwitchProbeTests(unittest.TestCase):
    def test_missing_opslib_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "opslib.py"
        with mock.patch.object(sa, "_opslib_py_path", return_value=missing):
            item = sa._probe_kill_switch()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))
        self.assertNotEqual(item["status"], "Done")

    def test_stubbed_opslib_without_stop_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "opslib.py"
        py.write_text("# empty stub\nOPS = None\n", encoding="utf-8")
        with mock.patch.object(sa, "_opslib_py_path", return_value=py):
            item = sa._probe_kill_switch()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_stop_halted_frozen_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "opslib.py"
        body = chr(10).join([
            "STOP_ORGANISM = OPS / 'STOP-ORGANISM'",
            "def halted(*, for_debate=False):",
            "    return None",
            "def frozen():",
            "    return False",
            "def master_halted():",
            "    return None",
            "",
        ])
        py.write_text(body, encoding="utf-8")
        with mock.patch.object(sa, "_opslib_py_path", return_value=py):
            item = sa._probe_kill_switch()
        self.assertEqual(item["status"], "Done", item)
        self.assertTrue(item.get("evidence_bound"))
        self.assertIn("STOP_ORGANISM=True", item["evidence"])


class WatchdogProbeTests(unittest.TestCase):
    def test_missing_watchdog_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        with mock.patch.object(sa, "_watchdog_py_path", return_value=root / "watchdog.py"):
            with mock.patch.object(sa, "_organism_watchdog_ps1_path", return_value=root / "x.ps1"):
                with mock.patch.object(sa, "_cortex_watchdog_json_path", return_value=root / "cw.json"):
                    item = sa._probe_watchdog()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_watchdog_without_defs_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "watchdog.py"
        py.write_text("# stub\n", encoding="utf-8")
        (root / "x.ps1").write_text("# short\n", encoding="utf-8")
        with mock.patch.object(sa, "_watchdog_py_path", return_value=py):
            with mock.patch.object(sa, "_organism_watchdog_ps1_path", return_value=root / "x.ps1"):
                with mock.patch.object(sa, "_cortex_watchdog_json_path", return_value=root / "cw.json"):
                    item = sa._probe_watchdog()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_watchdog_live_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "watchdog.py"
        body = chr(10).join([
            "def beat_health():",
            "    return True",
            "def monitor():",
            "    return None",
            "def should_revive():",
            "    return False",
            "",
        ])
        py.write_text(body, encoding="utf-8")
        ps1 = root / "organism-watchdog.ps1"
        ps1.write_text("# organism watchdog script with enough body to count as real content here\n", encoding="utf-8")
        cw = root / "cortex-watchdog.json"
        _write_json(cw, {"status": "alive", "attempts": [], "last_check": 1})
        with mock.patch.object(sa, "_watchdog_py_path", return_value=py):
            with mock.patch.object(sa, "_organism_watchdog_ps1_path", return_value=ps1):
                with mock.patch.object(sa, "_cortex_watchdog_json_path", return_value=cw):
                    item = sa._probe_watchdog()
        self.assertEqual(item["status"], "Done", item)
        self.assertIn("beat_health=True", item["evidence"])


class ApprovalGatesProbeTests(unittest.TestCase):
    def test_missing_opslib_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        with mock.patch.object(sa, "_opslib_py_path", return_value=root / "opslib.py"):
            with mock.patch.object(sa, "_human_append_guard_py_path", return_value=root / "hag.py"):
                item = sa._probe_approval_gates()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_gate_incomplete_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "opslib.py"
        py.write_text("live_gate_open = True  # not a def\n", encoding="utf-8")
        hag = root / "hag.py"
        hag.write_text("# tiny\n", encoding="utf-8")
        with mock.patch.object(sa, "_opslib_py_path", return_value=py):
            with mock.patch.object(sa, "_human_append_guard_py_path", return_value=hag):
                item = sa._probe_approval_gates()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_full_gates_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "opslib.py"
        body = chr(10).join([
            "GO_LIVE_FLAG = OPS / 'ACTIVATION-GO-LIVE.flag'",
            "def live_gate_open(activation_flag):",
            "    return True, 'ok'",
            "def organ_gate(name):",
            "    return True",
            "",
        ])
        py.write_text(body, encoding="utf-8")
        hag = root / "human_append_guard.py"
        hag.write_text(chr(10).join([
            "def assert_human_append(path):",
            "    return True",
            "def is_human(meta):",
            "    return True",
            "",
        ]), encoding="utf-8")
        with mock.patch.object(sa, "_opslib_py_path", return_value=py):
            with mock.patch.object(sa, "_human_append_guard_py_path", return_value=hag):
                item = sa._probe_approval_gates()
        self.assertEqual(item["status"], "Done", item)
        self.assertIn("def_live_gate_open=True", item["evidence"])


class SecretsIsolationProbeTests(unittest.TestCase):
    def test_missing_agentignore_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / ".agentignore"
        with mock.patch.object(sa, "_agentignore_path", return_value=missing):
            item = sa._probe_secrets_isolation()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_agentignore_without_patterns_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        p = root / ".agentignore"
        p.write_text("# only comments\n.git/\n", encoding="utf-8")
        with mock.patch.object(sa, "_agentignore_path", return_value=p):
            item = sa._probe_secrets_isolation()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_env_key_secret_is_done(self):
        root = Path(tempfile.mkdtemp())
        p = root / ".agentignore"
        p.write_text("*.env\n*key*\nsecrets-export/\n*.seed\n", encoding="utf-8")
        with mock.patch.object(sa, "_agentignore_path", return_value=p):
            item = sa._probe_secrets_isolation()
        self.assertEqual(item["status"], "Done", item)
        self.assertIn("env=True", item["evidence"])


class DryRunProbeTests(unittest.TestCase):
    def test_missing_both_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        with mock.patch.object(sa, "_governor_epoch_py_path", return_value=root / "ge.py"):
            with mock.patch.object(sa, "_sim_heart_py_path", return_value=root / "sh.py"):
                item = sa._probe_dry_run()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_only_allocate_dry_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        ge = root / "governor_epoch.py"
        ge.write_text("def allocate_dry(snap):\n    return {}\n", encoding="utf-8")
        with mock.patch.object(sa, "_governor_epoch_py_path", return_value=ge):
            with mock.patch.object(sa, "_sim_heart_py_path", return_value=root / "missing.py"):
                item = sa._probe_dry_run()
        self.assertEqual(item["status"], "Partial")
        self.assertNotEqual(item["status"], "Done")

    def test_fixture_allocate_and_simulate_is_done(self):
        root = Path(tempfile.mkdtemp())
        ge = root / "governor_epoch.py"
        ge.write_text("def allocate_dry(snap):\n    return {}\n# shadow\n", encoding="utf-8")
        sh = root / "sim_heart.py"
        sh.write_text("def simulate(x):\n    return {}\ndef run_sim():\n    return {}\n", encoding="utf-8")
        with mock.patch.object(sa, "_governor_epoch_py_path", return_value=ge):
            with mock.patch.object(sa, "_sim_heart_py_path", return_value=sh):
                item = sa._probe_dry_run()
        self.assertEqual(item["status"], "Done", item)
        self.assertIn("def_allocate_dry=True", item["evidence"])


class RollbackProbeTests(unittest.TestCase):
    def test_missing_doctor_is_not_done(self):
        missing = Path(tempfile.mkdtemp()) / "doctor.py"
        with mock.patch.object(sa, "_doctor_py_path", return_value=missing):
            item = sa._probe_rollback()
        self.assertEqual(item["status"], "Missing")
        self.assertTrue(item.get("evidence_bound"))

    def test_stubbed_doctor_without_checkpoint_is_not_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "doctor.py"
        py.write_text("rollback: str = ''\nmeasured_lift = 0\n", encoding="utf-8")
        with mock.patch.object(sa, "_doctor_py_path", return_value=py):
            item = sa._probe_rollback()
        self.assertNotEqual(item["status"], "Done")
        self.assertTrue(item.get("evidence_bound"))

    def test_fixture_rollback_lift_checkpoint_is_done(self):
        root = Path(tempfile.mkdtemp())
        py = root / "doctor.py"
        body = chr(10).join([
            "class RFC:",
            "    rollback: str = ''",
            "def apply_merge(self, rfc):",
            "    measured_lift = 0.1",
            "    if os.environ.get('OCTOPUS_WIRE_MERGE_CHECKPOINT'):",
            "        self._write_checkpoint_tag(rfc)",
            "",
        ])
        py.write_text(body, encoding="utf-8")
        with mock.patch.object(sa, "_doctor_py_path", return_value=py):
            item = sa._probe_rollback()
        self.assertEqual(item["status"], "Done", item)
        self.assertIn("CHECKPOINT=True", item["evidence"])




class EvidenceJsonPathGateTests(unittest.TestCase):
    """evidence_bound Done requires readable on-disk evidence JSON (fail-closed)."""

    def test_missing_path_demotes_done(self):
        missing = Path(tempfile.mkdtemp()) / "nope.json"
        item = sa._item("x", "Done", "prior", "P0", "none", "s",
                        evidence_bound=True, evidence_json=missing)
        self.assertEqual(item["status"], "Missing")
        self.assertIn("fail-closed", item["evidence"])
        self.assertIn("evidence-path-missing-file", item["evidence"])

    def test_empty_json_demotes_done(self):
        root = Path(tempfile.mkdtemp())
        empty = root / "empty.json"
        empty.write_text("", encoding="utf-8")
        item = sa._item("x", "Done", "prior", "P0", "none", "s",
                        evidence_bound=True, evidence_json=empty)
        self.assertEqual(item["status"], "Missing")
        self.assertIn("evidence-json-empty", item["evidence"])

    def test_invalid_json_demotes_done(self):
        root = Path(tempfile.mkdtemp())
        bad = root / "bad.json"
        bad.write_text("{not-json", encoding="utf-8")
        item = sa._item("x", "Done", "prior", "P0", "none", "s",
                        evidence_bound=True, evidence_json=bad)
        self.assertEqual(item["status"], "Missing")
        self.assertIn("evidence-json-invalid", item["evidence"])

    def test_valid_json_keeps_done(self):
        root = Path(tempfile.mkdtemp())
        good = root / "good.json"
        _write_json(good, {"schema": "probe-evidence/1", "ok": True})
        item = sa._item("x", "Done", "prior", "P0", "none", "s",
                        evidence_bound=True, evidence_json=good)
        self.assertEqual(item["status"], "Done")
        self.assertEqual(item.get("evidence_json"), str(good))
        self.assertEqual(item["evidence"], "prior")

    def test_non_done_not_gated(self):
        missing = Path(tempfile.mkdtemp()) / "nope.json"
        item = sa._item("x", "Partial", "prior", "P0", "none", "s",
                        evidence_bound=True, evidence_json=missing)
        self.assertEqual(item["status"], "Partial")

    def test_pack_dir_missing_demotes_via_gate(self):
        missing_dir = Path(tempfile.mkdtemp()) / "no-pack"
        with mock.patch.object(sa, "_evidence_pack_dir", return_value=missing_dir):
            item = sa._gate_evidence_bound_done({
                "item": "x", "status": "Done", "evidence": "prior",
                "priority": "P0", "gap_type": "none", "section": "s",
                "evidence_bound": True,
            })
        self.assertEqual(item["status"], "Missing")
        self.assertIn("fail-closed", item["evidence"])

    def test_pack_dir_with_valid_json_keeps_done(self):
        root = Path(tempfile.mkdtemp())
        _write_json(root / "pack.json", {"schema": "ok", "n": 1})
        with mock.patch.object(sa, "_evidence_pack_dir", return_value=root):
            item = sa._gate_evidence_bound_done({
                "item": "x", "status": "Done", "evidence": "prior",
                "priority": "P0", "gap_type": "none", "section": "s",
                "evidence_bound": True,
            })
        self.assertEqual(item["status"], "Done")
        self.assertTrue(str(item.get("evidence_json", "")).endswith("pack.json"))



if __name__ == "__main__":
    # keep harness-style + unittest dual entry
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
