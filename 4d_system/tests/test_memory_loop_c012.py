"""تست‌های حلقهٔ حافظهٔ مغز 4d — C-012 فاز صفر (Council Mesh v0.1).

ادعای تست‌شده: «تصمیم‌گیرندهٔ واقعی» (AutomationController — نه تست مصنوعی)
پیش از هر تصمیم (create/conclude/introspect) حافظه را می‌خواند، پس از نوشتن
read-back می‌کند، فرضیهٔ تکراری ثبت نمی‌کند و صفِ راکد (stale) را می‌شمارد.

هر تست روی DB موقت اجرا می‌شود (memory.store.DB_PATH و config.settings.OUTPUT_DIR
به tmp اشاره می‌کنند) — پایگاهِ زنده دست‌نخورده می‌ماند.
"""
from tests import _bootstrap  # noqa: F401

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from brain import memory_read_patch as mrp


def _events_since(db_path: Path, after_id: int) -> list[dict]:
    """رویدادهای dashboard_events با id > after_id (پنجرهٔ یک کار)."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM dashboard_events WHERE id > ? ORDER BY id ASC",
            (after_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


class MemoryLoopC012TestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "mem_loop_test.db"
        db_patch = mock.patch("memory.store.DB_PATH", self.db)
        db_patch.start()
        self.addCleanup(db_patch.stop)
        out_patch = mock.patch("config.settings.OUTPUT_DIR", Path(self.tmp.name))
        out_patch.start()
        self.addCleanup(out_patch.stop)

    def _controller(self):
        from brain.automation import AutomationController
        return AutomationController(use_llm=False)

    def _max_event_id(self) -> int:
        conn = sqlite3.connect(str(self.db))
        try:
            try:
                row = conn.execute("SELECT MAX(id) FROM dashboard_events").fetchone()
            except sqlite3.OperationalError:
                return 0  # DB تازه — پنجره از ابتدا
            return int(row[0] or 0)
        finally:
            conn.close()


class TestDedupAndStale(MemoryLoopC012TestBase):
    """واحدهای dedup و stale — پیش‌نیازِ تصمیمِ create."""

    def test_similarity_ignores_zwnj_and_case(self):
        a = "فرضیه: ترکیبِ «خوشه‌بندیِ ریتم‌ها» با پایشِ novelty"
        b = "فرضیه: ترکیبِ «خوشه‌بندی ریتمها» با پایش novelty"
        self.assertGreaterEqual(mrp.hypothesis_similarity(a, b), 0.90)

    def test_different_texts_are_not_duplicates(self):
        a = "آیا حافظهٔ اپیزودیک محدودیت یادگیری آفلاین را جبران می‌کند؟"
        b = "بررسی سیگنال کمکی برای تفکیک الگو از نوفه در سری‌های ضعیف"
        self.assertFalse(mrp.is_duplicate_hypothesis(a, [{"hypothesis": b}]))

    def test_identical_pending_is_duplicate(self):
        text = "فرضیهٔ آزمایشی یکسان"
        self.assertTrue(
            mrp.is_duplicate_hypothesis(text, [{"hypothesis": text}])
        )

    def test_split_stale_uses_transaction_time(self):
        old_ts = (datetime.now() - timedelta(days=30)).isoformat()
        new_ts = datetime.now().isoformat()
        pending = [
            {"id": 1, "hypothesis": "کهنه", "timestamp": old_ts},
            {"id": 2, "hypothesis": "تازه", "timestamp": new_ts},
            {"id": 3, "hypothesis": "بی‌زمان", "timestamp": None},
        ]
        stale, fresh = mrp.split_stale(pending, stale_days=14)
        self.assertEqual([r["id"] for r in stale], [1])
        # ردیفِ بی‌زمان محافظه‌کارانه «تازه» تلقی می‌شود (fail-open برای صف، نه حذف)
        self.assertEqual(sorted(r["id"] for r in fresh), [2, 3])

    def test_split_stale_compares_naive_and_aware(self):
        aware_now = datetime.now(timezone.utc)
        old_ts = (aware_now - timedelta(days=30)).isoformat()
        naive_new = datetime.now().isoformat()
        pending = [
            {"id": 1, "hypothesis": "کهنهٔ aware", "timestamp": old_ts},
            {"id": 2, "hypothesis": "تازهٔ naive", "timestamp": naive_new},
        ]
        stale, fresh = mrp.split_stale(pending, stale_days=14, now=aware_now)
        self.assertEqual([r["id"] for r in stale], [1])
        self.assertEqual([r["id"] for r in fresh], [2])


class TestRealDecisionMakerReads(MemoryLoopC012TestBase):
    """تصمیم‌گیرندهٔ واقعی: AutomationController روی DB واقعیِ (موقتِ) خودش."""

    def test_create_reads_memory_before_decision(self):
        ctrl = self._controller()
        before = self._max_event_id()
        ctrl._mode_i = 1  # حالتِ بعدی در _MODE_CYCLE = create
        res = ctrl.run_one()
        self.assertEqual(res.get("mode"), "create")
        evs = _events_since(self.db, before)
        started = [e for e in evs if e["event_name"] == "task.started"
                   and e["agent_id"] == "creative"]
        ended = [e for e in evs if e["event_name"] in ("task.completed", "task.failed")
                 and e["agent_id"] == "creative"]
        reads = [e for e in evs if e["event_name"] == "memory.read"]
        self.assertTrue(started and ended, "کارِ create اجرا نشد")
        self.assertTrue(reads, "هیچ memory.readی ثبت نشد — حلقه همچنان write-only")
        self.assertLess(started[0]["id"], reads[0]["id"],
                        "خواندن باید بعد از شروعِ کار باشد")
        self.assertLess(reads[0]["id"], ended[-1]["id"],
                        "خواندن باید «پیش از» پایانِ تصمیم باشد")
        self.assertEqual(started[0]["trace_id"], reads[0]["trace_id"],
                         "خواندن باید در همان traceِ کارِ تصمیم باشد")

    def test_create_dedup_skips_duplicate(self):
        ctrl = self._controller()
        fixed = "فرضیهٔ ثابتِ تستِ dedup — بیش از یک بار ثبت نشود"
        with mock.patch.object(ctrl, "_creative_idea", return_value=fixed):
            first = ctrl._job_create()
            second = ctrl._job_create()
        self.assertNotIn("dedup_skipped", first)
        self.assertTrue(second.get("dedup_skipped"))
        conn = sqlite3.connect(str(self.db))
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM hypotheses WHERE hypothesis = ?", (fixed,)
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(n, 1, "فرضیهٔ تکراری دوباره ثبت شد")

    def test_readback_after_write_from_consumer_path(self):
        ctrl = self._controller()
        before = self._max_event_id()
        with mock.patch.object(ctrl, "_creative_idea",
                               return_value="فرضیهٔ read-back — از مسیر مصرف‌کننده"):
            ctrl._job_create()
        evs = _events_since(self.db, before)
        rb = [e for e in evs if e["event_name"] == "memory.readback"]
        self.assertTrue(rb, "read-back ثبت نشد")
        self.assertEqual(rb[0]["status"], "ok")
        from memory.store import get_pending_hypotheses
        rows = get_pending_hypotheses(limit=50)
        self.assertTrue(any("read-back" in str(r.get("hypothesis", "")) for r in rows),
                        "نوشته در مسیرِ مصرف‌کننده قابلِ بازیابی نیست")

    def test_introspect_reads_experiments(self):
        ctrl = self._controller()
        before = self._max_event_id()
        ctrl._job_introspect()
        evs = _events_since(self.db, before)
        reads = [e for e in evs if e["event_name"] == "memory.read"]
        self.assertTrue(any(e["agent_id"] == "memory:experiments" for e in reads),
                        "introspect بدون خواندن تجربهٔ گذشته تصمیم گرفت")

    def test_conclude_reads_vault_first(self):
        ctrl = self._controller()
        before = self._max_event_id()
        ctrl._job_conclude()  # حتی اگر synthesis شکست بخورد، خواندن باید ثبت شده باشد
        evs = _events_since(self.db, before)
        reads = [e for e in evs if e["event_name"] == "memory.read"
                 and e["agent_id"] == "memory:vault_rag"]
        ended = [e for e in evs if e["event_name"] in ("task.completed", "task.failed")
                 and e["agent_id"] == "conclude"]
        self.assertTrue(reads and ended, "conclude بدون خواندنِ والت اجرا شد")
        self.assertLess(reads[0]["id"], ended[0]["id"],
                        "خواندنِ والت باید پیش از پایانِ conclude باشد")

    def test_telemetry_metrics_meet_phase_zero_targets(self):
        """مینی-سیکل زنده‌مانند: هر سه تصمیم‌گیرنده + متریک‌ها از رویدادهای واقعی."""
        ctrl = self._controller()
        before = self._max_event_id()
        fixed = "فرضیهٔ متریک فاز صفر — از telemetry واقعی"
        with mock.patch.object(ctrl, "_creative_idea", return_value=fixed):
            ctrl._job_introspect()
            ctrl._job_create()
            ctrl._job_conclude()
        m = mrp.telemetry_metrics(after_id=before)
        self.assertGreaterEqual(m["decision_jobs"], 3)
        self.assertEqual(m["decision_jobs_with_read"], m["decision_jobs"])
        self.assertGreaterEqual(m["memory_read_before_decision_ratio"], 0.95)
        self.assertIsNotNone(m["memory_readback_success_ratio"])
        self.assertGreaterEqual(m["memory_readback_success_ratio"], 0.99)


class TestTelemetryQueries(MemoryLoopC012TestBase):
    """خودِ محاسبهٔ متریک — مرزها و حالت‌های تهی."""

    def test_metrics_empty_window(self):
        m = mrp.telemetry_metrics(after_id=self._max_event_id())
        self.assertIsNone(m["memory_read_before_decision_ratio"])
        self.assertIsNone(m["memory_readback_success_ratio"])

    def test_read_after_completion_does_not_count(self):
        """خواندنی که «بعد از» پایانِ کار می‌آید در ratio شمرده نمی‌شود."""
        from brain import events
        trace = events.new_trace_id()
        events.emit("task.completed", "تصمیم بدون خواندنِ قبلی", agent_id="creative",
                    trace_id=trace)
        events.emit("memory.read", "خواندنِ پس از تصمیم", agent_id="memory:experiments",
                    trace_id=trace)
        m = mrp.telemetry_metrics(after_id=0)
        self.assertEqual(m["decision_jobs"], 1)
        self.assertEqual(m["decision_jobs_with_read"], 0)
        self.assertEqual(m["memory_read_before_decision_ratio"], 0.0)


if __name__ == "__main__":
    unittest.main()
