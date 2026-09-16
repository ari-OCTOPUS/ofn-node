"""تست‌های v4 Kill Switch — flag-gated، تأیید سخت، فقط قراردادِ فایلیِ موجودِ daemon."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import _bootstrap  # noqa: F401

from control_plane.killswitch import (audit_tail, cancel_stop, kill_switch_live,
                                      killswitch_status, pause_daemon,
                                      resume_daemon, stop_daemon)
from control_plane.policy import Level, evaluate


def _clean_cp_env(tc: unittest.TestCase, live: bool = False):
    patcher = mock.patch.dict(os.environ)
    patcher.start()
    tc.addCleanup(patcher.stop)
    for k in list(os.environ):
        if k.startswith("CONTROL_PLANE_"):
            del os.environ[k]
    if live:
        os.environ["CONTROL_PLANE_KILL_SWITCH_LIVE"] = "1"


class TestPolicyLevels(unittest.TestCase):
    def test_kill_switch_is_level_5_pause_is_4(self):
        self.assertEqual(evaluate("kill_switch").level, int(Level.KILL_SWITCH))
        self.assertEqual(evaluate("pause_subsystem").level,
                         int(Level.PAUSE_SUBSYSTEM))


class TestFlagOffNeverTouchesFiles(unittest.TestCase):
    def test_all_actions_refused_and_no_files_created(self):
        _clean_cp_env(self, live=False)
        self.assertFalse(kill_switch_live())
        with tempfile.TemporaryDirectory() as td:
            out, audit = Path(td) / "out", Path(td) / "audit"
            out.mkdir()
            for res in (
                pause_daemon(confirmed=True, out=out, audit_dir=audit),
                resume_daemon(confirmed=True, out=out, audit_dir=audit),
                stop_daemon(confirmed=True, confirm_text="STOP", out=out,
                            audit_dir=audit),
                cancel_stop(confirmed=True, out=out, audit_dir=audit),
            ):
                self.assertFalse(res["result"]["ok"])
                self.assertIn("خاموش", res["result"]["reason"])
            self.assertEqual(list(out.iterdir()), [],
                             "flag-off نباید هیچ فایلِ کنترلی بسازد")
            # ولی همه‌ی تلاش‌ها audit شده‌اند
            self.assertEqual(len(audit_tail(10, audit_dir=audit)), 4)


class TestHardConfirmation(unittest.TestCase):
    def setUp(self):
        _clean_cp_env(self, live=True)

    def test_not_confirmed_refused(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            res = pause_daemon(confirmed=False, out=out, audit_dir=out / "a")
            self.assertFalse(res["result"]["ok"])
            self.assertFalse((out / "daemon.pause").exists())

    def test_stop_requires_exact_phrase(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            for bad in ("", "stop", "Stop", "توقف", "STOP!"):
                res = stop_daemon(confirmed=True, confirm_text=bad,
                                  out=out, audit_dir=out / "a")
                self.assertFalse(res["result"]["ok"], f"نباید با {bad!r} قبول شود")
            self.assertFalse((out / "daemon.stop").exists())
            res = stop_daemon(confirmed=True, confirm_text="STOP",
                              out=out, audit_dir=out / "a")
            self.assertTrue(res["result"]["ok"])
            self.assertTrue((out / "daemon.stop").exists())


class TestPauseResumeStopCycle(unittest.TestCase):
    def setUp(self):
        _clean_cp_env(self, live=True)

    def test_pause_creates_resume_removes(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            a = out / "a"
            r1 = pause_daemon(confirmed=True, out=out, audit_dir=a)
            self.assertTrue(r1["result"]["ok"])
            self.assertTrue((out / "daemon.pause").exists())
            # idempotent
            r2 = pause_daemon(confirmed=True, out=out, audit_dir=a)
            self.assertTrue(r2["result"]["ok"])
            r3 = resume_daemon(confirmed=True, out=out, audit_dir=a)
            self.assertTrue(r3["result"]["ok"])
            self.assertFalse((out / "daemon.pause").exists())
            # resume بدونِ مکث هم ok (idempotent)
            r4 = resume_daemon(confirmed=True, out=out, audit_dir=a)
            self.assertTrue(r4["result"]["ok"])

    def test_cancel_stop_removes_pending_stop(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            a = out / "a"
            stop_daemon(confirmed=True, confirm_text="STOP", out=out, audit_dir=a)
            self.assertTrue((out / "daemon.stop").exists())
            res = cancel_stop(confirmed=True, out=out, audit_dir=a)
            self.assertTrue(res["result"]["ok"])
            self.assertFalse((out / "daemon.stop").exists())

    def test_every_record_has_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            a = out / "a"
            pause_daemon(confirmed=True, out=out, audit_dir=a)
            stop_daemon(confirmed=True, confirm_text="STOP", out=out, audit_dir=a)
            for rec in audit_tail(10, audit_dir=a):
                self.assertTrue(rec.get("rollback"),
                                "هر عملِ v4 باید rollback صریح داشته باشد")

    def test_status_reflects_files(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "daemon_state.json").write_text(
                json.dumps({"last_tick_at": "2026-07-11T15:35:52",
                            "stopped_at": "2026-07-11T15:35:52"}), encoding="utf-8")
            st = killswitch_status(out)
            self.assertTrue(st["flag_live"])
            self.assertEqual(st["daemon"]["status"], "STOPPED")
            self.assertEqual(st["stop_phrase"], "STOP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
