"""تست readback با نمای‌های R16 — رگرسیونِ 1/9 (2026-08-16 PHASE02 STEP0).

ریشه: readback فقط HEAD صفِ فعال را می‌دید؛ ردیفِ نو که لحظه‌ای
dedup/deferred خورده باشد عمداً بیرونِ صف است ⇒ «یافت نشد»ی کاذب.
قرارداد اصلاح‌شده: pending ⇒ HEAD صف؛ وضعیت‌های R16 ⇒ خواندنِ مستقیمِ
همان id (نمای مصرف‌کنندهٔ آن وضعیت). غیبِ واقعی ⇒ خطا می‌ماند.
"""
from tests import _bootstrap  # noqa: F401

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from brain import memory_read_patch as mrp


class TestReadbackR16Views(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "4d_experiments.db"
        conn = sqlite3.connect(str(self.db))
        conn.execute("""CREATE TABLE hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, domain TEXT,
            hypothesis TEXT, rationale TEXT DEFAULT '', status TEXT DEFAULT 'pending',
            tested INTEGER DEFAULT 0, result TEXT DEFAULT '',
            policy_tag TEXT, dedup_of INTEGER)""")
        conn.execute(
            "INSERT INTO hypotheses (timestamp, domain, hypothesis, status)"
            " VALUES ('2026-08-16T05:00:00','d','فرضیهٔ فعال','pending')")
        conn.execute(
            "INSERT INTO hypotheses (timestamp, domain, hypothesis, status, dedup_of)"
            " VALUES ('2026-08-16T05:00:01','d','فرضیهٔ تکراری','dedup',1)")
        conn.execute(
            "INSERT INTO hypotheses (timestamp, domain, hypothesis, status)"
            " VALUES ('2026-08-16T05:00:02','d','فرضیهٔ سقف‌خورده','deferred')")
        conn.commit(); conn.close()

    def tearDown(self):
        self.td.cleanup()

    def _readback(self, hid):
        emitted = {}
        with mock.patch.object(mrp, "_emit_readback",
                               side_effect=lambda ok, h, t, trace_id=None, note="":
                               emitted.update(ok=ok, hid=h, note=note)), \
             mock.patch("memory.store.get_pending_hypotheses",
                        return_value=[{"id": 1}]), \
             mock.patch("config.settings.OUTPUT_DIR", Path(self.td.name)):
            return mrp.readback_hypothesis(hid), emitted

    def test_pending_found_in_queue_head(self):
        ok, em = self._readback(1)
        self.assertTrue(ok)
        self.assertNotIn("r16-view", em["note"])

    def test_dedup_row_verified_by_direct_view(self):
        ok, em = self._readback(2)
        self.assertTrue(ok)
        self.assertIn("r16-view:dedup", em["note"])

    def test_deferred_row_verified_by_direct_view(self):
        ok, em = self._readback(3)
        self.assertTrue(ok)
        self.assertIn("r16-view:deferred", em["note"])

    def test_missing_row_still_fails(self):
        ok, em = self._readback(999)
        self.assertFalse(ok)
        self.assertNotIn("r16-view", em["note"])


if __name__ == "__main__":
    unittest.main()
