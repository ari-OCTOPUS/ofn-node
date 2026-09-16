"""تست‌های Shadow Policy v2 — فقط گزارش، deterministic، بدونِ نوشتنِ بیرون از مسیرِ خودش."""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import _bootstrap  # noqa: F401

from control_plane.policy import Level, evaluate
from control_plane.shadow import classify_event, run_shadow, shadow_enabled


def _make_bus(db: Path, rows):
    conn = sqlite3.connect(str(db))
    conn.execute("""CREATE TABLE dashboard_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, trace_id TEXT,
        agent_id TEXT, event_name TEXT, status TEXT, summary TEXT,
        duration_ms INTEGER, next_action TEXT, approval_state TEXT)""")
    conn.executemany(
        "INSERT INTO dashboard_events (timestamp, trace_id, agent_id, event_name,"
        " status, summary, duration_ms, next_action, approval_state)"
        " VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


_ROWS = [
    # (timestamp, trace, agent, event, status, summary, dur, next, approval)
    ("t1", "a", "explore", "task.completed", "ok", "کاوش", 0, "", "not_required"),
    ("t2", "b", "evolve", "task.completed", "ok", "استراتژی به نسل ۱۰ رفت", 0, "", "not_required"),
    ("t3", "c", "evolve", "approval.required", "blocked",
     "پیشنهادِ کد آماده‌ی تأیید (pid 123)", 0, "", "pending"),
    ("t4", "d", "autoloop", "approval.required", "blocked",
     "کشف مهم — نیاز به تایید", 0, "", "not_required"),   # بی‌گیت! → disagreement
    ("t5", "e", "real", "task.failed", "error", "خطا ۱", 0, "", "not_required"),
    ("t6", "f", "real", "task.failed", "error", "خطا ۲", 0, "", "not_required"),
    ("t7", "g", "real", "task.failed", "error", "خطا ۳", 0, "", "not_required"),
]


class TestClassifier(unittest.TestCase):
    def test_strategy_apply_stays_autonomous_but_logged(self):
        r = evaluate("strategy_apply")
        self.assertEqual(r.level, int(Level.SHADOW_LOG))
        self.assertFalse(r.requires_approval)

    def test_low_risk_agent_maps_to_observe(self):
        d = classify_event({"agent_id": "explore", "event_name": "task.completed",
                            "summary": "x", "approval_state": "not_required"})
        self.assertEqual(d["action_type"], "write_outputs")
        self.assertEqual(d["level"], 0)
        self.assertTrue(d["agreement"])

    def test_code_approval_event_gated_is_agreement(self):
        d = classify_event({"agent_id": "evolve", "event_name": "approval.required",
                            "summary": "پیشنهادِ کد (pid 9)", "approval_state": "pending"})
        self.assertEqual(d["action_type"], "self_code_approve")
        self.assertTrue(d["requires_approval"])
        self.assertTrue(d["agreement"])
        self.assertEqual(d["mismatch"], "")

    def test_ungated_high_risk_is_flagged(self):
        d = classify_event({"agent_id": "autoloop", "event_name": "approval.required",
                            "summary": "کشف مهم", "approval_state": "not_required"})
        self.assertTrue(d["requires_approval"])
        self.assertEqual(d["mismatch"], "ungated_high_risk")
        self.assertFalse(d["agreement"])

    def test_legacy_agent_aliases_mapped(self):
        """نام‌های قدیمیِ روی bus (creative/guardrail) نباید needs_review شوند."""
        for agent, expected in (("creative", "memory_write"),
                                ("guardrail", "read_only")):
            d = classify_event({"agent_id": agent, "event_name": "task.completed",
                                "summary": "x", "approval_state": "not_required"})
            self.assertEqual(d["action_type"], expected)
            self.assertFalse(d["needs_review"])

    def test_unknown_agent_needs_review_not_silent_pass(self):
        d = classify_event({"agent_id": "martian", "event_name": "task.completed",
                            "summary": "x", "approval_state": "not_required"})
        self.assertTrue(d["needs_review"])
        self.assertTrue(d["requires_approval"])


class TestRunShadow(unittest.TestCase):
    def test_full_run_summary_and_confined_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "bus.db"
            _make_bus(db, _ROWS)
            out = root / "out"
            out.mkdir()
            rd = root / "_reports"
            before = {str(p) for p in root.rglob("*")}
            rep = run_shadow(db=db, out=out, report_dir=rd, limit=100)
            new = {str(p) for p in root.rglob("*")} - before
            for p in new:
                self.assertIn("_reports", p, f"نوشتنِ خارج از مسیرِ گزارش: {p}")

            s = rep["summary"]
            self.assertEqual(s["analyzed"], 7)
            self.assertEqual(s["would_require_approval"], 2)   # ردیف ۳ و ۴
            self.assertEqual(s["ungated_high_risk"], 1)        # فقط ردیف ۴
            self.assertGreaterEqual(s["needs_review"], 1)      # approval_event ناشناخته
            self.assertEqual(s["failure_streaks_ge3"], {"real": 3})
            self.assertEqual(s["budget_shadow"]["verdict"], "UNKNOWN")  # فایل بودجه نیست
            self.assertTrue((rd / "shadow_policy.md").exists())
            self.assertTrue((rd / "shadow_decisions.jsonl").exists())

    def test_deterministic_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db = root / "bus.db"
            _make_bus(db, _ROWS)
            r1, r2 = (root / "r1"), (root / "r2")
            run_shadow(db=db, out=root, report_dir=r1, limit=100)
            run_shadow(db=db, out=root, report_dir=r2, limit=100)
            j1 = (r1 / "shadow_decisions.jsonl").read_text(encoding="utf-8")
            j2 = (r2 / "shadow_decisions.jsonl").read_text(encoding="utf-8")
            self.assertEqual(j1, j2, "تصمیم‌های shadow باید deterministic باشند")

    def test_missing_bus_is_unknown_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rep = run_shadow(db=root / "no.db", out=root, report_dir=root / "_r")
            self.assertEqual(rep["status"], "UNKNOWN")
            self.assertFalse((root / "_r").exists())

    def test_budget_shadow_thresholds(self):
        from control_plane.shadow import _budget_shadow
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"LLM_DAILY_CALL_CAP": "1000"}):
            out = Path(td)
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            (out / "llm_budget.json").write_text(
                json.dumps({"date": today, "calls": {"glm": 850}}), encoding="utf-8")
            self.assertIn("SOFT_WARN", _budget_shadow(out)["verdict"])
            (out / "llm_budget.json").write_text(
                json.dumps({"date": today, "calls": {"glm": 1000}}), encoding="utf-8")
            self.assertIn("WOULD_REQUIRE_APPROVAL", _budget_shadow(out)["verdict"])


class TestFlagDefault(unittest.TestCase):
    def test_shadow_flag_default_off(self):
        with mock.patch.dict(os.environ):
            for k in list(os.environ):
                if k.startswith("CONTROL_PLANE_"):
                    del os.environ[k]
            self.assertFalse(shadow_enabled(),
                             "shadow باید default-off باشد (قاعده‌ی flag-gated)")


class TestDestructiveScan(unittest.TestCase):
    def test_destructive_summary_from_known_agent_is_flagged(self):
        """#11: اکشنِ مخربِ یک agentِ شناخته‌شده (متنِ آزاد) باید ungated_high_risk شود."""
        d = classify_event({
            "agent_id": "evolve",              # نگاشتِ عادی = strategy_apply (low)
            "event_name": "task.completed",
            "summary": "applied self-modifying code to run.py",
            "approval_state": "not_required",
        })
        self.assertTrue(d["requires_approval"])
        self.assertEqual(d["mismatch"], "ungated_high_risk")
        self.assertNotEqual(d["action_type"], "strategy_apply")

    def test_delete_and_secret_markers(self):
        for summary, low in (("delete all experiments table", "explore"),
                             ("wrote new .env token", "create")):
            d = classify_event({"agent_id": low, "event_name": "task.completed",
                                "summary": summary, "approval_state": "not_required"})
            self.assertTrue(d["requires_approval"], summary)

    def test_benign_summary_stays_low_risk(self):
        d = classify_event({"agent_id": "explore", "event_name": "task.completed",
                            "summary": "کاوشِ سریِ زمانیِ AAPL انجام شد",
                            "approval_state": "not_required"})
        self.assertFalse(d["requires_approval"])
        self.assertEqual(d["mismatch"], "")

    def test_word_boundary_avoids_benign_substrings(self):
        """#11: preset/swipe/CSV format نباید اشتباهاً high-risk شوند (word-boundary)."""
        for summary in ("applied the preset config", "swipe gesture added",
                        "exported results in CSV format", "formatting the report"):
            d = classify_event({"agent_id": "explore", "event_name": "task.completed",
                                "summary": summary, "approval_state": "not_required"})
            self.assertFalse(d["requires_approval"], summary)
        # ولی واژه‌ی واقعی همچنان گرفته می‌شود
        d2 = classify_event({"agent_id": "explore", "event_name": "task.completed",
                            "summary": "wipe the experiments database", "approval_state": "not_required"})
        self.assertTrue(d2["requires_approval"])

    def test_inflected_destructive_forms_caught(self):
        """صورت‌های صرف‌شده (زمانِ گذشته/جمع) که summaryهای «انجام‌شده» می‌نویسند
        باید گرفته شوند (left-boundary، نه full-boundary)."""
        for summary in ("deleted all experiments", "removed the production database",
                        "wiped the outputs directory", "purged the cache",
                        "erased the disk", "truncated the events table",
                        "exposed 3 auth tokens"):
            d = classify_event({"agent_id": "explore", "event_name": "task.completed",
                                "summary": summary, "approval_state": "not_required"})
            self.assertTrue(d["requires_approval"], summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
