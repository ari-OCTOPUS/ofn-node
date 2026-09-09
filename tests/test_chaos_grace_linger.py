"""Owner-absent chaos for grace_class / linger_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a linger never becomes a send, and a recorded grace never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.grace_class import (
    LIVE,
    admit_grace,
    bind_grace,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    remaining_of,
    try_bind,
)
from ofn.kernel.halt import is_halted
from ofn.kernel.linger_pin import (
    pin_allows_send,
    pin_linger,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_DUE = 8
_LINGER = 4
_SLOT = "env-grace-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(
            classify_family(None, due_after=_DUE, linger_after=_LINGER))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(
            try_bind(None, 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", None, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT))
        self.assertIsNone(
            remaining_of(None, due_after=_DUE, linger_after=_LINGER))
        self.assertIsNot(
            classify_family(None, due_after=_DUE, linger_after=_LINGER), False)
        self.assertIsNot(
            remaining_of(None, due_after=_DUE, linger_after=_LINGER), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(
            classify_family(
                3, due_after=_DUE, linger_after=_LINGER, timeout=True))
        self.assertIsNone(
            admit_grace(
                "linger", 8, due_after=_DUE, linger_after=_LINGER,
                timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_grace(
                "classify", 3, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            True)
        self.assertIs(
            admit_grace(
                "inspect", 3, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            True)
        self.assertIs(
            admit_grace(
                "linger", 8, due_after=_DUE, linger_after=_LINGER,
                halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_live_and_sealed_do_not_grant_send(self):
        bind = bind_grace(
            "classify", 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_grace(
                "classify", 3, due_after=_DUE, linger_after=_LINGER,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_linger_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_grace(
            "classify", 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        pin_linger(table, first)
        second = bind_grace(
            "classify", 8, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_linger(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(3, due_after=_DUE, linger_after=_LINGER)
        b = classify_family(3, due_after=_DUE, linger_after=_LINGER)
        self.assertEqual(a, b)
        self.assertEqual(a, LIVE)
        first = bind_grace(
            "classify", 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        second = bind_grace(
            "classify", 3, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
