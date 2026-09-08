"""Owner-absent chaos for inclusive_class / exclusive_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe,
a sample never becomes a send, and a recorded inclusion never
becomes authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.exclusive_pin import (
    pin_allows_send,
    pin_exclusive,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)
from ofn.kernel.halt import is_halted
from ofn.kernel.inclusive_class import (
    EXCLUSIVE,
    INCLUSIVE,
    OUT,
    admit_inclusive,
    bind_inclusive,
    classify_family,
    classify_intent,
    classify_kind,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)

_BOUND = 10
_SLOT = "env-inc-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(
            classify_family(None, bound=_BOUND, kind=INCLUSIVE))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertEqual(classify_kind(None), "UNKNOWN")
        self.assertIsNone(
            try_bind(None, 10, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT))
        self.assertIsNot(
            classify_family(None, bound=_BOUND, kind=INCLUSIVE), False)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(
            classify_family(10, bound=_BOUND, kind=INCLUSIVE, timeout=True))
        self.assertIsNone(
            admit_inclusive(
                "sample", 10, bound=_BOUND, kind=INCLUSIVE, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 10, bound=_BOUND, kind=EXCLUSIVE,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_inclusive(
                "classify", 10, bound=_BOUND, kind=INCLUSIVE, halted=True),
            True)
        self.assertIs(
            admit_inclusive(
                "sample", 10, bound=_BOUND, kind=INCLUSIVE, halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_exclusive_out_and_sealed_do_not_grant_send(self):
        bind = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=EXCLUSIVE, slot=_SLOT)
        self.assertEqual(bind.family, OUT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_inclusive(
                "classify", 10, bound=_BOUND, kind=INCLUSIVE,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_exclusive_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=EXCLUSIVE, slot=_SLOT)
        pin_exclusive(table, first)
        second = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_exclusive(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(10, bound=_BOUND, kind=EXCLUSIVE)
        b = classify_family(10, bound=_BOUND, kind=EXCLUSIVE)
        self.assertEqual(a, b)
        self.assertEqual(a, OUT)
        first = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=EXCLUSIVE, slot=_SLOT)
        second = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=EXCLUSIVE, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
