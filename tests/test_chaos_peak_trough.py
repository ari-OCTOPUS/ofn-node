"""Owner-absent chaos for peak_class / trough_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe,
a sample never becomes a send, and a recorded extremum never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.peak_class import (
    NEITHER,
    TROUGH,
    admit_peak,
    bind_peak,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)
from ofn.kernel.trough_pin import (
    pin_allows_send,
    pin_trough,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_SLOT = "env-peak-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_family(None, 0, 1))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, 4, -1, 2, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, -1, 2, slot=_SLOT))
        self.assertIsNot(classify_family(None, 0, 1), False)
        self.assertIsNot(classify_family(None, 0, 1), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_family(4, -1, 2, timeout=True))
        self.assertIsNone(admit_peak("sample", 4, -1, 2, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 4, -1, 2, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(admit_peak("classify", 4, -1, 2, halted=True), True)
        self.assertIs(admit_peak("sample", 4, -1, 2, halted=True), False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_neither_and_sealed_do_not_grant_send(self):
        bind = bind_peak("classify", 1, 2, 3, slot=_SLOT)
        self.assertEqual(bind.family, NEITHER)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_peak(
                "classify", 4, -1, 2, slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_trough_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_peak("classify", 4, -1, 2, slot=_SLOT)
        pin_trough(table, first)
        second = bind_peak("classify", 1, 5, 0, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_trough(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(4, -1, 2)
        b = classify_family(4, -1, 2)
        self.assertEqual(a, b)
        self.assertEqual(a, TROUGH)
        first = bind_peak("classify", 4, -1, 2, slot=_SLOT)
        second = bind_peak("classify", 4, -1, 2, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
