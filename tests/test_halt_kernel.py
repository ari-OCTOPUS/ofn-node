"""Layer-3 kill-switch vocabulary (kernel.halt), complementary tests.

Adapter I/O and RunGate wiring are covered elsewhere and some of those
files are owned by open PRs. This module only locks the pure predicate
on main: absence is RUNNING; corrupt/empty/unknown is HALTED; known-off
words are RUNNING. HALT is a start gate, not a send grant.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.halt import is_halted


class AbsentIsRunning(unittest.TestCase):
    def test_none_is_running(self):
        self.assertFalse(is_halted(None))


class KnownOffWordsAreRunning(unittest.TestCase):
    def test_canonical_off_words(self):
        for raw in ("0", "false", "no", "off",
                    "0\n", " FALSE ", "No", "OFF"):
            with self.subTest(raw=raw):
                self.assertFalse(is_halted(raw))


class KnownOnWordsAreHalted(unittest.TestCase):
    def test_canonical_on_words(self):
        for raw in ("1", "true", "yes", "on",
                    "1\n", " TRUE ", "Yes", "ON"):
            with self.subTest(raw=raw):
                self.assertTrue(is_halted(raw))


class UnparsableIsHalted(unittest.TestCase):
    def test_empty_string_is_halted(self):
        self.assertTrue(is_halted(""))
        self.assertTrue(is_halted("   \n"))

    def test_foreign_vocabulary_is_halted(self):
        for raw in ("garbage", "2", "maybe", "{}", "halt", "running"):
            with self.subTest(raw=raw):
                self.assertTrue(is_halted(raw))


class HaltIsNotASendGrant(unittest.TestCase):
    def test_is_halted_has_only_raw(self):
        params = inspect.signature(is_halted).parameters
        self.assertEqual(list(params), ["raw"])
        self.assertNotIn("resend", params)
        self.assertNotIn("send_authorized", params)


if __name__ == "__main__":
    unittest.main()
