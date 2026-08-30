#!/usr/bin/env python3
"""test_bridge_beat.py — تست consumer-side bridge_beat + integration با bridge.

این تست کل حلقه‌ی publish → consume را تأیید می‌کند. مهم‌ترین اعتبارسنجی
این است که pf_os واقعاً به organism (از طریق file-based pub/sub) وصل است.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

from pf_os import bridge as BR  # noqa: E402
from pf_os import bridge_beat as BB  # noqa: E402
from pf_os import config  # noqa: E402


class TestBridgeBeat(unittest.TestCase):
    """consumer-side beat — الگوی کپی‌شده از wiring.py cockpit_requests_beat."""

    def _prime_cursor_at_zero(self):
        """prime cursor = 0 (activation before pf_os publishes). production pattern."""
        (self._state / "saba-bridge.cursor").write_text("0", encoding="utf-8")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._state = Path(self._tmp.name)
        # bridge و bridge_beat هر دو مسیر را override کنند
        self._bridge_file = self._state / "saba-bridge.jsonl"
        self._orig_bridge_path = BR.bridge_path
        BR.bridge_path = lambda: self._bridge_file
        # flag را روشن کن برای beat
        os.environ[config.WIRE_BRIDGE] = "1"
        self._orig_state_dir = BB._state_dir
        BB._state_dir = lambda: self._state

    def tearDown(self):
        BR.bridge_path = self._orig_bridge_path
        BB._state_dir = self._orig_state_dir
        os.environ.pop(config.WIRE_BRIDGE, None)
        self._tmp.cleanup()

    def test_flag_off_returns_skipped(self):
        os.environ.pop(config.WIRE_BRIDGE, None)
        r = BB.saba_bridge_beat(state_dir=self._state)
        self.assertEqual(r.get("skipped"), "flag-off")

    def test_no_file_returns_skipped(self):
        # هنوز فایل نیست
        r = BB.saba_bridge_beat(state_dir=self._state)
        self.assertEqual(r.get("skipped"), "no-bridge-file")

    def test_first_activation_ffwd(self):
        """اولین فراخوانی باید cursor را ffwd کنه (بدونِ replayِ backlog)."""
        BR.publish("notify", "first event before activation")
        r = BB.saba_bridge_beat(state_dir=self._state)
        self.assertEqual(r.get("skipped"), "first-activation-ffwd")
        # cursor ساخته شده
        self.assertTrue((self._state / "saba-bridge.cursor").exists())

    def test_consume_after_ffwd(self):
        """بعد از ffwd، event‌های جدید consumed می‌شوند."""
        self._prime_cursor_at_zero()
        # pf_os events می‌فرستد
        BR.publish("notify", "event 1")
        BR.publish("halt", "creator halted")
        BR.publish("draft_submitted", "new draft")
        # consume
        seen = []
        r = BB.saba_bridge_beat(handler=lambda rec: seen.append(rec),
                                state_dir=self._state)
        self.assertEqual(len(r.get("ran", [])), 3)
        self.assertEqual(len(seen), 3)
        kinds = [s["kind"] for s in seen]
        self.assertIn("notify", kinds)
        self.assertIn("halt", kinds)
        self.assertIn("draft_submitted", kinds)

    def test_at_most_once(self):
        """cursor قبل از exec advance می‌شود — event‌ها فقط یکبار consumed."""
        self._prime_cursor_at_zero()
        BR.publish("notify", "single event")
        seen1 = []
        r1 = BB.saba_bridge_beat(handler=lambda rec: seen1.append(rec),
                                 state_dir=self._state)
        self.assertEqual(len(seen1), 1)
        # فراخوانیِ دوباره — نباید چیزی consumed کنه
        seen2 = []
        r2 = BB.saba_bridge_beat(handler=lambda rec: seen2.append(rec),
                                 state_dir=self._state)
        self.assertEqual(len(seen2), 0)

    def test_pii_in_record_rejected(self):
        """defense-in-depth: record با PII باید skip شود."""
        self._prime_cursor_at_zero()
        # دستی یک record با PII بنویس (الگوی worst case)
        import json as _j
        with open(self._bridge_file, "a", encoding="utf-8") as f:
            f.write(_j.dumps({"ts": "x", "kind": "notify",
                              "text": "talking to ari", "source": "evil"}) + "\n")
            f.write(_j.dumps({"ts": "x", "kind": "notify",
                              "text": "clean", "source": "pf_os"}) + "\n")
        r = BB.saba_bridge_beat(state_dir=self._state)
        self.assertIn(len(r.get("ran", [])), (0, 1))  # clean only
        self.assertTrue(any("pii-reject" in s for s in r.get("skipped", [])))

    def test_lock_taken_skips(self):
        """lock فایلِ PID دیگر → skip."""
        # bridge file باید موجود باشه تا قبل از lock-check نرسه
        BR.publish("notify", "primer")
        # شبیه‌سازی: lock فایل با PID دیگر و mtime تازه
        lockp = self._state / "saba-bridge.lock"
        lockp.write_text("999999:2026-01-01T00:00:00", encoding="utf-8")
        # mtime تازه
        import time as _t
        os.utime(lockp, (_t.time(), _t.time()))
        r = BB.saba_bridge_beat(state_dir=self._state)
        self.assertEqual(r.get("skipped"), "locked-by-other")


def _prime_cursor(state_dir):
    """prime cursor = 0 (module-level helper)."""
    (Path(state_dir) / "saba-bridge.cursor").write_text("0", encoding="utf-8")


class TestPublishConsumeIntegration(unittest.TestCase):
    """integration کامل: bridge.publish → bridge_beat.saba_bridge_beat → handler."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._state = Path(self._tmp.name)
        self._bridge_file = self._state / "saba-bridge.jsonl"
        self._orig_bridge_path = BR.bridge_path
        BR.bridge_path = lambda: self._bridge_file
        os.environ[config.WIRE_BRIDGE] = "1"
        self._orig_state_dir = BB._state_dir
        BB._state_dir = lambda: self._state

    def tearDown(self):
        BR.bridge_path = self._orig_bridge_path
        BB._state_dir = self._orig_state_dir
        os.environ.pop(config.WIRE_BRIDGE, None)
        self._tmp.cleanup()

    def test_full_loop_with_real_pf_os_events(self):
        """پلِ واقعی: pf_os رویدادها را publish می‌کند، organism را می‌خواند."""
        # prime cursor (شبیه‌سازی activation قبلی توسط organism)
        _prime_cursor(self._state)
        # pf_os یک سری رویداد می‌فرستد (همه content-free)
        BR.notify_draft_submitted("DRAFT-001", pending_count=1)
        BR.notify_halt()
        BR.notify_resume()
        BR.notify_boundary("no body shots")
        BR.notify_brain_tick(tick_n=5, source="heuristic")
        BR.notify_kpi("2026-W29", gross_aud=42.5, posts=3)
        BR.notify_learning_observed("cozy-socks", n_obs=5)
        # organism consume می‌کند
        received = []
        r = BB.saba_bridge_beat(handler=lambda rec: received.append(rec),
                                state_dir=self._state)
        # همه‌ی ۷ رویداد باید consumed شوند
        self.assertEqual(len(received), 7)
        kinds = [x["kind"] for x in received]
        self.assertEqual(set(kinds), {"draft_submitted", "halt", "resume",
                                      "boundary", "brain_tick_done",
                                      "kpi", "learning_observed"})
        # همه باید source=pf_os داشته باشند
        self.assertTrue(all(x.get("source") == "pf_os" for x in received))
        # هیچ PII در محتوای consumed
        for x in received:
            self.assertNotIn("ari", str(x).lower())
            self.assertNotIn("saba", str(x).lower())
            self.assertNotIn("sydney", str(x).lower())


if __name__ == "__main__":
    unittest.main()
