"""HALT flag adapter fail-closed cases complementary to kernel tests.

``tests/test_halt_kernel.py`` (open PR) locks the pure predicate.
``tests/test_chaos_owner_absent.py`` / ``tests/test_run_gate.py`` are
owned by other open changes. This file only locks the I/O adapter that
already lives on main: symlink, non-UTF-8, directory, and resume-is-
unlink. HALT stops STARTS. Resume is removal, never a written ``0``.
Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.kernel.errors import FailClosedError
from tests.tmpdir import temp_dir


class SymlinkIsHalted(unittest.TestCase):
    def test_planted_symlink_is_halted_even_if_target_says_off(self):
        root = Path(temp_dir(self))
        target = root / "off.txt"
        target.write_text("0\n", encoding="utf-8")
        flag = root / "halt.flag"
        flag.symlink_to(target)
        self.assertTrue(halt_flag.halt_flag_active(flag))

    def test_clear_unlinks_the_link_not_the_target(self):
        root = Path(temp_dir(self))
        target = root / "payload.txt"
        target.write_text("keep", encoding="utf-8")
        flag = root / "halt.flag"
        flag.symlink_to(target)
        halt_flag.clear_halt(flag)
        self.assertFalse(flag.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "keep")


class NonUtf8IsHalted(unittest.TestCase):
    def test_undecodable_bytes_are_halted(self):
        root = Path(temp_dir(self))
        flag = root / "halt.flag"
        flag.write_bytes(b"\xff\xfe\x00not-utf8")
        self.assertTrue(halt_flag.halt_flag_active(flag))


class DirectoryIsNotAFlag(unittest.TestCase):
    def test_write_halt_refuses_directory(self):
        root = Path(temp_dir(self))
        flag = root / "halt.flag"
        flag.mkdir()
        (flag / "keep").write_text("stay", encoding="utf-8")
        with self.assertRaises(FailClosedError):
            halt_flag.write_halt(flag)
        self.assertTrue(flag.is_dir())
        self.assertEqual((flag / "keep").read_text(encoding="utf-8"), "stay")

    def test_clear_halt_refuses_directory(self):
        root = Path(temp_dir(self))
        flag = root / "halt.flag"
        flag.mkdir()
        with self.assertRaises(FailClosedError):
            halt_flag.clear_halt(flag)
        self.assertTrue(flag.is_dir())

    def test_missing_clear_refuses(self):
        root = Path(temp_dir(self))
        with self.assertRaises(FailClosedError):
            halt_flag.clear_halt(root / "absent.flag")


class WriteHaltIsCanonicalOne(unittest.TestCase):
    def test_reason_is_not_written_into_the_flag(self):
        root = Path(temp_dir(self))
        flag = root / "halt.flag"
        halt_flag.write_halt(flag, reason="chatty-reason-must-not-land")
        self.assertEqual(flag.read_text(encoding="utf-8"), "1\n")
        self.assertTrue(halt_flag.halt_flag_active(flag))

    def test_resume_is_unlink_not_write_zero(self):
        params = inspect.signature(halt_flag.clear_halt).parameters
        self.assertNotIn("resend", params)
        src = inspect.getsource(halt_flag.clear_halt)
        self.assertIn("unlink", src)
        self.assertNotIn("write_text", src)
        self.assertNotIn('"0"', src)


class AbsentIsRunning(unittest.TestCase):
    def test_missing_file_is_not_halted(self):
        root = Path(temp_dir(self))
        self.assertFalse(halt_flag.halt_flag_active(root / "no-such.flag"))


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_write_halt_has_no_send_knob(self):
        params = inspect.signature(halt_flag.write_halt).parameters
        self.assertNotIn("send_authorized", params)
        self.assertNotIn("resend", params)
        self.assertNotIn("quote_sent", params)


if __name__ == "__main__":
    unittest.main()
