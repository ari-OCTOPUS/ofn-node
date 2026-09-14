"""Owner-absent chaos for near_class / far_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a mark never becomes a send, and a recorded distance never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.far_pin import (
    pin_allows_send,
    pin_far,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)
from ofn.kernel.halt import is_halted
from ofn.kernel.near_class import (
    NEAR,
    admit_near,
    bind_near,
    classify_family,
    classify_intent,
    distance_of,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)

_ORIGIN = 10
_RADIUS = 3
_SLOT = "env-near-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(
            classify_family(None, origin=_ORIGIN, radius=_RADIUS))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(
            try_bind(None, 12, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT))
        self.assertIsNone(
            try_bind("classify", None, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT))
        self.assertIsNone(distance_of(None, origin=_ORIGIN, radius=_RADIUS))
        self.assertIsNot(
            classify_family(None, origin=_ORIGIN, radius=_RADIUS), False)
        self.assertIsNot(distance_of(None, origin=_ORIGIN, radius=_RADIUS), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(
            classify_family(12, origin=_ORIGIN, radius=_RADIUS, timeout=True))
        self.assertIsNone(
            admit_near(
                "mark", 12, origin=_ORIGIN, radius=_RADIUS, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 12, origin=_ORIGIN, radius=_RADIUS,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_near(
                "classify", 12, origin=_ORIGIN, radius=_RADIUS, halted=True),
            True)
        self.assertIs(
            admit_near(
                "inspect", 14, origin=_ORIGIN, radius=_RADIUS, halted=True),
            True)
        self.assertIs(
            admit_near(
                "mark", 12, origin=_ORIGIN, radius=_RADIUS, halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_far_and_sealed_do_not_grant_send(self):
        bind = bind_near(
            "classify", 14, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_near(
                "classify", 12, origin=_ORIGIN, radius=_RADIUS,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_far_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_near(
            "classify", 12, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        pin_far(table, first)
        second = bind_near(
            "classify", 14, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_far(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(12, origin=_ORIGIN, radius=_RADIUS)
        b = classify_family(12, origin=_ORIGIN, radius=_RADIUS)
        self.assertEqual(a, b)
        self.assertEqual(a, NEAR)
        first = bind_near(
            "classify", 12, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        second = bind_near(
            "classify", 12, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
