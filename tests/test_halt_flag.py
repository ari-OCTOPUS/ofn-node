"""halt_flag adapter — second witness of the file-side kill switch.

``tests/test_run_store.py`` and ``tests/test_run_gate.py`` already cover
parts of this adapter and are owned by open PRs. This module locks the
I/O edges on main without touching those files: symlink, non-UTF-8,
directory, atomic write, owner-private mode, stray clear. HALT is a
start gate, not a send grant.
"""

from __future__ import annotations

import inspect
import os
import stat
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.kernel.errors import FailClosedError
from tests.tmpdir import temp_dir


class HaltFlagAdapter(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.flag = self.root / "halt.flag"

    def test_missing_file_is_running(self):
        self.assertFalse(halt_flag.halt_flag_active(self.flag))

    def test_write_then_clear(self):
        halt_flag.write_halt(self.flag)
        self.assertTrue(halt_flag.halt_flag_active(self.flag))
        self.assertEqual(self.flag.read_text(encoding="utf-8"), "1\n")
        halt_flag.clear_halt(self.flag)
        self.assertFalse(halt_flag.halt_flag_active(self.flag))
        self.assertFalse(self.flag.exists())

    def test_write_is_canonical_one_not_a_chatty_reason(self):
        halt_flag.write_halt(self.flag, reason="operator-note-must-not-land")
        raw = self.flag.read_bytes()
        self.assertEqual(raw, b"1\n")
        self.assertNotIn(b"\r", raw)

    def test_legacy_crlf_one_is_still_halted(self):
        # A Windows text-mode leftover is unparsable-as-chatty, not RUNNING.
        # strip() folds "1\r\n" to "1" → HALTED. UNKNOWN/foreign is also HALTED.
        self.flag.write_bytes(b"1\r\n")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))
        self.assertNotEqual(self.flag.read_bytes(), b"1\n")

    def test_symlink_is_halted_and_clear_unlinks_the_link(self):
        target = self.root / "elsewhere"
        target.write_text("0\n", encoding="utf-8")
        self.flag.symlink_to(target)
        self.assertTrue(halt_flag.halt_flag_active(self.flag))
        halt_flag.clear_halt(self.flag)
        self.assertFalse(self.flag.exists())
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "0\n")

    def test_non_utf8_is_halted(self):
        self.flag.write_bytes(b"\xff\xfe not utf-8")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_directory_is_halted_and_write_refuses(self):
        self.flag.mkdir()
        (self.flag / "keep").write_text("stay", encoding="utf-8")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))
        with self.assertRaises(FailClosedError):
            halt_flag.write_halt(self.flag)
        self.assertTrue(self.flag.is_dir())
        self.assertEqual((self.flag / "keep").read_text(encoding="utf-8"),
                         "stay")
        with self.assertRaises(FailClosedError):
            halt_flag.clear_halt(self.flag)
        self.assertTrue(self.flag.is_dir())

    def test_stray_clear_is_not_an_owner_decision(self):
        with self.assertRaises(FailClosedError):
            halt_flag.clear_halt(self.flag)

    def test_parent_is_owner_private(self):
        nested = self.root / "priv" / "halt.flag"
        halt_flag.write_halt(nested)
        self.assertTrue(halt_flag.halt_flag_active(nested))
        self.assertEqual(nested.read_bytes(), b"1\n")
        if os.name == "nt":
            self.skipTest("POSIX directory/file mode is not a Windows fact")
        mode = stat.S_IMODE(os.stat(nested.parent).st_mode)
        self.assertEqual(mode, 0o700)
        file_mode = stat.S_IMODE(os.stat(nested).st_mode)
        self.assertEqual(file_mode, 0o600)

    def test_write_and_clear_have_no_resend_knob(self):
        write_params = inspect.signature(halt_flag.write_halt).parameters
        clear_params = inspect.signature(halt_flag.clear_halt).parameters
        self.assertNotIn("resend", write_params)
        self.assertNotIn("send_authorized", write_params)
        self.assertNotIn("resend", clear_params)
        self.assertNotIn("send_authorized", clear_params)


if __name__ == "__main__":
    unittest.main()
