"""Alert notifier: both layers, with the flag gate enforced.

The notifier is the one path that sends on its own, so the contract is:
  - local log always happens
  - telegram happens only when OFN_ALERT_TELEGRAM=1
  - misconfiguration (flag on, creds missing) is surfaced, not swallowed
  - nothing ever raises — a notifier that crashes hides the alert
"""

from __future__ import annotations

import os
import tempfile
import unittest
import urllib.request

from ofn.adapters import alert


class TestLocalLogAlways(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = os.path.join(self.tmp.name, "alerts.log")

    def test_log_written_when_telegram_disabled(self):
        out = alert.notify("test alert", log_path=self.log, env={})
        self.assertTrue(out["logged"])
        self.assertEqual(out["telegram"], "disabled")
        self.assertTrue(os.path.exists(self.log))
        with open(self.log) as f:
            line = f.read()
        self.assertIn("test alert", line)

    def test_log_written_even_when_telegram_on_but_offline(self):
        # Flag on, creds present, but no network (the test env cannot reach
        # Telegram). The local log must still be there.
        env = {"OFN_ALERT_TELEGRAM": "1",
               "OFN_BOT_TOKEN_OWNER": "fake-token",
               "OFN_OWNER_USER_IDS": "12345"}
        out = alert.notify("crash", log_path=self.log, env=env)
        self.assertTrue(out["logged"])
        self.assertTrue(os.path.exists(self.log))

    def test_newlines_collapsed_to_one_log_line(self):
        alert.notify("line1\nline2\nline3", log_path=self.log, env={})
        with open(self.log) as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("line1 line2 line3", lines[0])


class TestFlagGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = os.path.join(self.tmp.name, "alerts.log")

    def test_telegram_not_attempted_when_flag_off(self):
        env = {"OFN_BOT_TOKEN_OWNER": "real-token",
               "OFN_OWNER_USER_IDS": "12345"}
        # Flag absent
        out = alert.notify("x", log_path=self.log, env=env)
        self.assertEqual(out["telegram"], "disabled")

    def test_telegram_not_attempted_when_flag_not_one(self):
        env = {"OFN_ALERT_TELEGRAM": "0",  # explicitly off
               "OFN_BOT_TOKEN_OWNER": "t", "OFN_OWNER_USER_IDS": "1"}
        out = alert.notify("x", log_path=self.log, env=env)
        self.assertEqual(out["telegram"], "disabled")

    def test_misconfiguration_surfaced(self):
        """Flag on but creds missing — must surface, not swallow."""
        env = {"OFN_ALERT_TELEGRAM": "1"}  # no token, no ids
        out = alert.notify("x", log_path=self.log, env=env)
        self.assertEqual(out["telegram"], "misconfigured")

    def test_misconfiguration_logged(self):
        env = {"OFN_ALERT_TELEGRAM": "1"}
        alert.notify("x", log_path=self.log, env=env)
        with open(self.log) as f:
            content = f.read()
        self.assertIn("missing", content)


class TestNoCrash(unittest.TestCase):
    """The notifier must never raise, even in hostile conditions."""

    def test_unwritable_log_does_not_crash(self):
        out = alert.notify("x", log_path="/nonexistent/path/a.log", env={})
        self.assertTrue(out["ok"])

    def test_main_returns_zero(self):
        self.assertEqual(alert.main(["ofn", "crashed"]), 0)


if __name__ == "__main__":
    unittest.main()
