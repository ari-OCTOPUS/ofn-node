"""تستِ منطقِ خالصِ رابطِ تلگرام (بدونِ شبکه) — brain/telegram_bot."""
from tests import _bootstrap  # noqa: F401

import os
import unittest

from brain import telegram_bot as tb


class TestOwnerGate(unittest.TestCase):
    def setUp(self):
        self._chat = os.environ.get("TELEGRAM_CHAT_ID")
        os.environ["TELEGRAM_CHAT_ID"] = "12345"

    def tearDown(self):
        if self._chat is None:
            os.environ.pop("TELEGRAM_CHAT_ID", None)
        else:
            os.environ["TELEGRAM_CHAT_ID"] = self._chat

    def test_owner_only(self):
        self.assertTrue(tb._is_owner("12345"))
        self.assertTrue(tb._is_owner(12345))       # int هم
        self.assertFalse(tb._is_owner("99999"))    # غریبه رد
        self.assertFalse(tb._is_owner(""))

    def test_is_configured(self):
        os.environ["TELEGRAM_BOT_TOKEN"] = "t"
        try:
            self.assertTrue(tb.is_configured())
        finally:
            os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        self.assertFalse(tb.is_configured())       # بدونِ توکن


class TestBuilders(unittest.TestCase):
    def test_status_text_has_project_and_attention(self):
        s = {"paused": False, "last_tick": "14:30", "generation": 3,
             "frontier": 27, "pending": 0, "budget": "10/1000"}
        txt = tb.build_status_text(s)
        self.assertIn("4d_system", txt)
        self.assertIn("چیزی لازم نیست", txt)       # صفر منتظر → آرام
        self.assertIn("نسل 3", txt)

    def test_status_text_flags_pending(self):
        s = {"paused": True, "last_tick": "—", "generation": 0,
             "frontier": None, "pending": 2, "budget": "0/1000"}
        txt = tb.build_status_text(s)
        self.assertIn("2 پیشنهادِ کد", txt)
        self.assertIn("مکث", txt)

    def test_pending_text_empty_and_full(self):
        self.assertIn("هیچ", tb.build_pending_text([]))
        props = [{"id": "p1", "target": "data/x.py", "rationale": "بهبود"}]
        self.assertIn("data/x.py", tb.build_pending_text(props))

    def test_pending_kb_has_approve_reject(self):
        kb = tb._pending_kb([{"id": "p1", "target": "data/x.py"}])
        flat = str(kb)
        self.assertIn("approve:p1", flat)
        self.assertIn("reject:p1", flat)


class TestRouting(unittest.TestCase):
    def test_help_on_unknown(self):
        txt, _ = tb.route_command("/wat")
        self.assertIn("دستورها", txt)

    def test_goal_command(self):
        txt, kb = tb.route_command("/goal")
        self.assertIn("چرا", txt)
        self.assertIsNotNone(kb)

    def test_callback_status_returns_keyboard(self):
        txt, kb, alert = tb.route_callback("status")
        self.assertIn("4d_system", txt)
        self.assertIsNotNone(kb)

    def test_pause_resume_toggle(self):
        import tempfile
        import config.settings as settings
        from pathlib import Path
        orig = settings.OUTPUT_DIR
        td = tempfile.TemporaryDirectory()
        settings.OUTPUT_DIR = Path(td.name)
        try:
            from brain.daemon import _pause_path
            tb.route_callback("pause")
            self.assertTrue(_pause_path().exists())
            tb.route_callback("resume")
            self.assertFalse(_pause_path().exists())
        finally:
            settings.OUTPUT_DIR = orig
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
