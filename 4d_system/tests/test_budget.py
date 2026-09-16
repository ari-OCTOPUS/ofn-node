"""تستِ سقفِ بودجه‌ی روزانه‌ی LLM (brain/budget)."""
from tests import _bootstrap  # noqa: F401

import tempfile
import unittest
from pathlib import Path

import config.settings as settings
from brain import budget


class TestBudget(unittest.TestCase):
    def setUp(self):
        self._orig_out = settings.OUTPUT_DIR
        self._td = tempfile.TemporaryDirectory()
        settings.OUTPUT_DIR = Path(self._td.name)

    def tearDown(self):
        settings.OUTPUT_DIR = self._orig_out
        self._td.cleanup()

    def test_records_and_cloud_vs_local(self):
        budget.record_call("fugu")
        budget.record_call("glm")
        budget.record_call("ollama")     # محلی — جزوِ سقفِ ابری نیست
        st = budget.status()
        self.assertEqual(st["cloud_calls"], 2)          # fugu + glm
        self.assertEqual(st["by_provider"]["ollama"], 1)

    def test_cap_enforced(self):
        import os
        os.environ["LLM_DAILY_CALL_CAP"] = "3"
        try:
            for _ in range(3):
                self.assertTrue(budget.cloud_allowed())
                budget.record_call("fugu")
            self.assertFalse(budget.cloud_allowed())     # سقف پر
            self.assertEqual(budget.remaining_cloud(), 0)
        finally:
            del os.environ["LLM_DAILY_CALL_CAP"]

    def test_cap_zero_disables_cloud(self):
        import os
        os.environ["LLM_DAILY_CALL_CAP"] = "0"
        try:
            self.assertFalse(budget.cloud_allowed())
        finally:
            del os.environ["LLM_DAILY_CALL_CAP"]

    def test_daily_reset(self):
        budget.record_call("glm")
        d = budget._load()
        d["date"] = "2000-01-01"                          # روزِ قدیمی
        budget._save(d)
        # بارگذاری با تاریخِ کهنه → صفر می‌شود
        self.assertEqual(budget.status()["cloud_calls"], 0)


if __name__ == "__main__":
    unittest.main()
