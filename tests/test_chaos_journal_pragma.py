"""Owner-absent chaos for journal_class / pragma_class.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block classify,
NORMAL never becomes FULL, WAL sidecars are never unlinked, and
a durability verdict never becomes a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.journal_class import (
    admit_journal, grants_send as journal_grants_send,
    halt_blocks_journal, timeout_proves_concurrent,
)
from ofn.kernel.pragma_class import (
    admit_pragma, classify_unknown_pragma, grants_send as pragma_grants_send,
    halt_blocks_pragma,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_pragma_is_unknown(self):
        d = admit_pragma(name="busy_timeout", value="0")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_pragma")
        self.assertEqual(classify_unknown_pragma(), "UNKNOWN")
        self.assertNotEqual(classify_unknown_pragma(), "FALSE")


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_on_wal_open_is_unknown(self):
        d = admit_journal(
            artifact="wal",
            intended="open",
            activity="concurrent",
            timed_out=True,
        )
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_admit_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_journal())
        self.assertFalse(halt_blocks_pragma())
        d = admit_pragma(name="journal_mode", value="WAL")
        self.assertTrue(d.allowed)
        self.assertNotIn("halted", inspect.signature(admit_pragma).parameters)
        self.assertNotIn("halted", inspect.signature(admit_journal).parameters)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_refused_normal_does_not_grant_send(self):
        d = admit_pragma(name="synchronous", value="NORMAL")
        self.assertFalse(d.allowed)
        self.assertFalse(pragma_grants_send())
        self.assertFalse(journal_grants_send())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_sealed_names_cannot_become_a_pragma(self):
        d = admit_pragma(
            name="campaign_envelope_ready", value="send_authorized")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            admit_journal(
                artifact="quote_sent", intended="open", activity="idle")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_normal_is_not_rewritten_to_full(self):
        d = admit_pragma(name="synchronous", value="NORMAL")
        self.assertEqual(d.value, "NORMAL")
        self.assertEqual(d.reason, "sync_not_full")
        self.assertNotEqual(d.value, "FULL")


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_wal_full_is_deterministic(self):
        a = admit_pragma(name="journal_mode", value="WAL")
        b = admit_pragma(name="journal_mode", value="WAL")
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)
        c = admit_journal(
            artifact="events_jsonl", intended="fsync", activity="idle")
        d = admit_journal(
            artifact="events_jsonl", intended="fsync", activity="idle")
        self.assertEqual(c, d)
        self.assertTrue(c.allowed)
        unlink = admit_journal(
            artifact="wal", intended="unlink", activity="idle")
        self.assertFalse(unlink.allowed)


if __name__ == "__main__":
    unittest.main()
