"""Owner-absent chaos for backlog_class / shed_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a shed never becomes a send, and a recorded backlog never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.backlog_class import (
    OVER,
    admit_backlog,
    bind_backlog,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    room_to_shed,
    try_bind,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.shed_pin import (
    pin_allows_send,
    pin_shed,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_LINE = 8
_SLOT = "env-bl-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_family(None, threshold=_LINE))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, 3, threshold=_LINE, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, threshold=_LINE, slot=_SLOT))
        self.assertIsNone(room_to_shed(None, threshold=_LINE))
        self.assertIsNot(classify_family(None, threshold=_LINE), False)
        self.assertIsNot(room_to_shed(None, threshold=_LINE), 0)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(
            classify_family(3, threshold=_LINE, timeout=True))
        self.assertIsNone(
            admit_backlog("shed", 11, threshold=_LINE, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, threshold=_LINE, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_backlog("classify", 11, threshold=_LINE, halted=True),
            True)
        self.assertIs(
            admit_backlog("inspect", 11, threshold=_LINE, halted=True),
            True)
        self.assertIs(
            admit_backlog("shed", 11, threshold=_LINE, halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_over_and_sealed_do_not_grant_send(self):
        bind = bind_backlog(
            "classify", 11, threshold=_LINE, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_backlog(
                "classify", 3, threshold=_LINE,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_shed_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_backlog("classify", 3, threshold=_LINE, slot=_SLOT)
        pin_shed(table, first)
        second = bind_backlog("classify", 11, threshold=_LINE, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_shed(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(11, threshold=_LINE)
        b = classify_family(11, threshold=_LINE)
        self.assertEqual(a, b)
        self.assertEqual(a, OVER)
        first = bind_backlog("classify", 11, threshold=_LINE, slot=_SLOT)
        second = bind_backlog("classify", 11, threshold=_LINE, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
