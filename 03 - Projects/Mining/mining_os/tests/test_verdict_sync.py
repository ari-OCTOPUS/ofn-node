"""تستِ سینکِ canonical verdict → VERDICT_QUEUE.md.

پوشش: append بدونِ نشانگر (حفظِ جدولِ انسانی) · dedup آخرین‌تصمیم · idempotent/replace ·
fail-soft روی فایلِ غایب · گِیتِ فلگ (off = بدونِ سینک، on = یک سینک). همه روی tmp، بدونِ
لمسِ فایل‌های واقعیِ vault.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

from mining_os.ui import tg_mining


def _write_log(path: Path, records: list) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


class TestVerdictSync(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name)
        self.log = self.d / "verdict-actions.jsonl"
        self.queue = self.d / "VERDICT_QUEUE.md"
        # یک فایلِ صف با «جدولِ انسانی» که هرگز نباید خراب شود
        self.queue.write_text(
            "# Q\n\n## Human\n\n| ID | تصمیم |\n|---|---|\n| VQ-MIN-001 | keep |\n",
            encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_queue_is_failsoft(self):
        _write_log(self.log, [{"id": "MIN-V1", "decision": "ok", "ts": "2026-07-19T09:00:00Z"}])
        self.assertFalse(tg_mining.sync_verdicts_to_queue(self.log, self.d / "nope.md"))

    def test_append_preserves_human_table(self):
        _write_log(self.log, [{"id": "MIN-V1", "decision": "ok", "source": "tg-mining",
                               "ts": "2026-07-19T09:00:00Z"}])
        self.assertTrue(tg_mining.sync_verdicts_to_queue(self.log, self.queue))
        txt = self.queue.read_text(encoding="utf-8")
        self.assertIn("## Human", txt)                       # جدولِ انسانی حفظ شد
        self.assertIn("| VQ-MIN-001 | keep |", txt)
        self.assertIn("MINING-AUTO-VERDICTS:BEGIN", txt)
        self.assertIn("MIN-V1", txt)
        self.assertIn("✅ ok", txt)

    def test_latest_decision_wins_dedup(self):
        _write_log(self.log, [
            {"id": "MIN-V1", "decision": "ok", "ts": "2026-07-19T09:00:00Z"},
            {"id": "MIN-V1", "decision": "no", "ts": "2026-07-19T10:00:00Z"},
        ])
        tg_mining.sync_verdicts_to_queue(self.log, self.queue)
        txt = self.queue.read_text(encoding="utf-8")
        self.assertIn("❌ no", txt)
        self.assertNotIn("✅ ok", txt)                       # رکوردِ قدیمی نباید بماند
        self.assertEqual(txt.count("| MIN-V1 |"), 1)

    def test_idempotent_and_single_block(self):
        _write_log(self.log, [{"id": "MIN-V1", "decision": "ok", "ts": "2026-07-19T09:00:00Z"}])
        tg_mining.sync_verdicts_to_queue(self.log, self.queue)
        once = self.queue.read_text(encoding="utf-8")
        tg_mining.sync_verdicts_to_queue(self.log, self.queue)
        twice = self.queue.read_text(encoding="utf-8")
        self.assertEqual(once, twice)                                    # idempotent
        self.assertEqual(twice.count("MINING-AUTO-VERDICTS:BEGIN"), 1)   # بلوک تکرار نشد

    def test_flag_off_record_verdict_skips_sync(self):
        os.environ.pop(tg_mining._SYNC_FLAG, None)
        called, orig_sync, orig_log = [], tg_mining.sync_verdicts_to_queue, tg_mining._VERDICT_LOG
        tg_mining.sync_verdicts_to_queue = lambda *a, **k: called.append(1)
        tg_mining._VERDICT_LOG = self.log            # به state واقعی دست نزن
        try:
            self.assertTrue(tg_mining.record_verdict("MIN-OFF", "ok"))
        finally:
            tg_mining.sync_verdicts_to_queue, tg_mining._VERDICT_LOG = orig_sync, orig_log
        self.assertEqual(called, [])                 # flag off → سینک صدا زده نشد

    def test_flag_on_record_verdict_invokes_sync_once(self):
        called, orig_sync, orig_log = [], tg_mining.sync_verdicts_to_queue, tg_mining._VERDICT_LOG
        tg_mining.sync_verdicts_to_queue = lambda *a, **k: called.append(1)
        tg_mining._VERDICT_LOG = self.log
        os.environ[tg_mining._SYNC_FLAG] = "1"
        try:
            self.assertTrue(tg_mining.record_verdict("MIN-ON", "ok"))
        finally:
            tg_mining.sync_verdicts_to_queue, tg_mining._VERDICT_LOG = orig_sync, orig_log
            os.environ.pop(tg_mining._SYNC_FLAG, None)
        self.assertEqual(called, [1])                # flag on → دقیقاً یک سینک


if __name__ == "__main__":
    unittest.main()
