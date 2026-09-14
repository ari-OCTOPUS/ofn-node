"""Owner-absent chaos for hendecagonal_class / undecagon_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a sample never becomes a send, and a recorded 11-gon never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.hendecagonal_class import (
    HENDECA,
    admit_hendeca,
    bind_hendeca,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    index_of,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)
from ofn.kernel.undecagon_pin import (
    pin_allows_send,
    pin_undecagon,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_SLOT = "env-hd-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_family(None))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, 11, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, slot=_SLOT))
        self.assertIsNone(index_of(None))
        self.assertIsNot(classify_family(None), False)
        self.assertIsNot(index_of(None), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_family(11, timeout=True))
        self.assertIsNone(admit_hendeca("sample", 11, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 11, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(admit_hendeca("classify", 11, halted=True), True)
        self.assertIs(admit_hendeca("inspect", 11, halted=True), True)
        self.assertIs(admit_hendeca("sample", 11, halted=True), False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_other_and_sealed_do_not_grant_send(self):
        bind = bind_hendeca("classify", 2, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_hendeca("classify", 11, slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_undecagon_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_hendeca("classify", 11, slot=_SLOT)
        pin_undecagon(table, first)
        second = bind_hendeca("classify", 30, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_undecagon(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(11)
        b = classify_family(11)
        self.assertEqual(a, b)
        self.assertEqual(a, HENDECA)
        first = bind_hendeca("classify", 11, slot=_SLOT)
        second = bind_hendeca("classify", 11, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
