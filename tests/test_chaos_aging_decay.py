"""Owner-absent chaos for aging_class / decay_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a decay never becomes a send, and a recorded age never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.aging_class import (
    FRESH,
    admit_aging,
    bind_aging,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    remaining_of,
    try_bind,
)
from ofn.kernel.decay_pin import (
    pin_allows_send,
    pin_decay,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted

_AFTER = 8
_SLOT = "env-age-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_family(None, decay_after=_AFTER))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, 3, decay_after=_AFTER, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, decay_after=_AFTER, slot=_SLOT))
        self.assertIsNone(remaining_of(None, decay_after=_AFTER))
        self.assertIsNot(classify_family(None, decay_after=_AFTER), False)
        self.assertIsNot(remaining_of(None, decay_after=_AFTER), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(
            classify_family(3, decay_after=_AFTER, timeout=True))
        self.assertIsNone(
            admit_aging("decay", 8, decay_after=_AFTER, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, decay_after=_AFTER, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_aging("classify", 3, decay_after=_AFTER, halted=True),
            True)
        self.assertIs(
            admit_aging("inspect", 3, decay_after=_AFTER, halted=True),
            True)
        self.assertIs(
            admit_aging("decay", 8, decay_after=_AFTER, halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_fresh_and_sealed_do_not_grant_send(self):
        bind = bind_aging(
            "classify", 3, decay_after=_AFTER, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_aging(
                "classify", 3, decay_after=_AFTER,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_decay_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_aging("classify", 3, decay_after=_AFTER, slot=_SLOT)
        pin_decay(table, first)
        second = bind_aging("classify", 8, decay_after=_AFTER, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_decay(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(3, decay_after=_AFTER)
        b = classify_family(3, decay_after=_AFTER)
        self.assertEqual(a, b)
        self.assertEqual(a, FRESH)
        first = bind_aging("classify", 3, decay_after=_AFTER, slot=_SLOT)
        second = bind_aging("classify", 3, decay_after=_AFTER, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
