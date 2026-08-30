"""تستِ digestِ پیام‌رسانی (≤ چند بار در روز) — brain/notify."""
from tests import _bootstrap  # noqa: F401

import os
import tempfile
import unittest
from pathlib import Path

import config.settings as settings
from brain import notify


class TestNotifyDigest(unittest.TestCase):
    def setUp(self):
        self._orig_out = settings.OUTPUT_DIR
        self._td = tempfile.TemporaryDirectory()
        settings.OUTPUT_DIR = Path(self._td.name)
        # تلگرام تنظیم‌نشده در تست → ارسال واقعی رخ نمی‌دهد، فقط منطقِ صف
        self._had_tok = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        self._had_chat = os.environ.pop("TELEGRAM_CHAT_ID", None)

    def tearDown(self):
        settings.OUTPUT_DIR = self._orig_out
        self._td.cleanup()
        if self._had_tok is not None:
            os.environ["TELEGRAM_BOT_TOKEN"] = self._had_tok
        if self._had_chat is not None:
            os.environ["TELEGRAM_CHAT_ID"] = self._had_chat

    def test_queue_grows(self):
        self.assertEqual(notify.digest_status()["queued"], 0)
        notify.queue_for_digest("notify", "c1", "w", "r", "cons")
        notify.queue_for_digest("warning", "c2", "w", "r", "cons")
        self.assertEqual(notify.digest_status()["queued"], 2)

    def test_flush_empty_is_noop(self):
        self.assertFalse(notify.flush_digest(force=True)["sent"])

    def test_flush_not_configured_keeps_queue(self):
        notify.queue_for_digest("notify", "c1", "w", "r", "cons")
        res = notify.flush_digest(force=True)   # تلگرام تنظیم‌نشده → نمی‌فرستد
        self.assertFalse(res["sent"])
        self.assertEqual(notify.digest_status()["queued"], 1)   # صف حفظ شد

    def test_daily_cap_field(self):
        os.environ["NOTIFY_MAX_PER_DAY"] = "2"
        try:
            self.assertEqual(notify.digest_status()["cap"], 2)
        finally:
            del os.environ["NOTIFY_MAX_PER_DAY"]

    def test_cap_blocks_when_sent_today_reached(self):
        # شبیه‌سازی: سقف پر شده → flush نمی‌فرستد حتی با صفِ ناخالی (بدونِ force)
        os.environ["NOTIFY_MAX_PER_DAY"] = "1"
        try:
            notify.queue_for_digest("notify", "c", "w", "r", "cons")
            d = notify._load_digest()
            d["sent_today"] = 1
            notify._save_digest(d)
            res = notify.flush_digest(force=False)
            self.assertFalse(res["sent"])
            self.assertIn("سقف", res["reason"])
        finally:
            del os.environ["NOTIFY_MAX_PER_DAY"]


if __name__ == "__main__":
    unittest.main()
