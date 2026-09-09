"""Owner-absent chaos for cascade_class / stop_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a record never becomes a send, a recorded cascade never becomes
authorized, children do not promote isolated into cascade, and zero
children cannot fan out.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.cascade_class import (
    CASCADE,
    ISOLATED,
    admit_cascade,
    bind_cascade,
    children_do_not_promote,
    classify_intent,
    classify_propagation,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
    zero_children_cannot_cascade,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.stop_pin import (
    pin_allows_send,
    pin_stop,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_STOP = "env-cst-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_propagation(None, 2))
        self.assertIsNone(classify_propagation("cascade", None))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, "cascade", 2, stop=_STOP))
        self.assertIsNone(try_bind("classify", None, 2, stop=_STOP))
        self.assertIsNot(classify_propagation(None, 2), False)
        self.assertIsNot(classify_propagation(None, 2), CASCADE)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_propagation("cascade", 2, timeout=True))
        self.assertIsNone(admit_cascade("record", "cascade", 2, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", "cascade", 2, stop=_STOP, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(admit_cascade("classify", "isolated", 3, halted=True), True)
        self.assertIs(admit_cascade("inspect", "cascade", 0, halted=True), True)
        self.assertIs(admit_cascade("record", "cascade", 2, halted=True), False)
        params = inspect.signature(classify_propagation).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_isolated_and_sealed_do_not_grant_send(self):
        bind = bind_cascade("classify", "isolated", 3, stop=_STOP)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_propagation("send_authorized", 1)
        self.assertTrue(children_do_not_promote())
        self.assertTrue(zero_children_cannot_cascade())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_cascade("classify", "cascade", 2, stop="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_stop_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_cascade("classify", "isolated", 2, stop=_STOP)
        pin_stop(table, first)
        second = bind_cascade("classify", "cascade", 2, stop=_STOP)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_stop(table, second)
        self.assertEqual(first.family, ISOLATED)
        self.assertEqual(second.family, CASCADE)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_propagation("cascade", 2)
        b = classify_propagation("cascade", 2)
        self.assertEqual(a, b)
        self.assertEqual(a, CASCADE)
        first = bind_cascade("classify", "isolated", 3, stop=_STOP)
        second = bind_cascade("classify", "isolated", 3, stop=_STOP)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())
        self.assertEqual(classify_propagation("cascade", 0), ISOLATED)


if __name__ == "__main__":
    unittest.main()
