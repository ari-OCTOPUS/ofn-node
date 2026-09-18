"""Owner-absent chaos for head_class / tail_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a take never becomes a send, and a recorded end never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.head_class import (
    TAIL,
    admit_head,
    bind_head,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)
from ofn.kernel.tail_pin import (
    pin_allows_send,
    pin_tail,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_SLOT = "env-head-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_family(None, index=0))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, 4, index=0, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, index=0, slot=_SLOT))
        self.assertIsNot(classify_family(None, index=0), False)
        self.assertIsNot(classify_family(None, index=0), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_family(4, index=3, timeout=True))
        self.assertIsNone(admit_head("take", 4, index=3, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 4, index=3, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_head("classify", 4, index=3, halted=True),
            True)
        self.assertIs(
            admit_head("inspect", 4, index=1, halted=True),
            True)
        self.assertIs(
            admit_head("take", 4, index=3, halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_past_and_sealed_do_not_grant_send(self):
        bind = bind_head("classify", 4, index=4, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_head(
                "classify", 4, index=3,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_tail_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_head("classify", 4, index=3, slot=_SLOT)
        pin_tail(table, first)
        second = bind_head("classify", 4, index=0, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_tail(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(4, index=3)
        b = classify_family(4, index=3)
        self.assertEqual(a, b)
        self.assertEqual(a, TAIL)
        first = bind_head("classify", 4, index=3, slot=_SLOT)
        second = bind_head("classify", 4, index=3, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
