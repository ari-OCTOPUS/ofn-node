"""Owner-absent chaos for quorum_class / seat_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe/inspect,
a record never becomes a send, and a recorded quorum never becomes
authorized. required < 1 does not satisfy.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.quorum_class import (
    QUORUM,
    admit_quorum,
    bind_quorum,
    classify_intent,
    classify_threshold,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    lowering_required_satisfies,
    ready_is_authorized,
    try_bind,
    zero_required_satisfies,
)
from ofn.kernel.seat_pin import (
    pin_allows_send,
    pin_seat,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_SEAT = "env-qrm-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_threshold(None, 3))
        self.assertIsNone(classify_threshold(3, None))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, 3, 3, seat=_SEAT))
        self.assertIsNone(try_bind("classify", None, 3, seat=_SEAT))
        self.assertIsNot(classify_threshold(None, 3), False)
        self.assertIsNot(classify_threshold(None, 3), QUORUM)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_threshold(3, 3, timeout=True))
        self.assertIsNone(admit_quorum("record", 3, 3, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 3, 3, seat=_SEAT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(admit_quorum("classify", 3, 3, halted=True), True)
        self.assertIs(admit_quorum("inspect", 1, 3, halted=True), True)
        self.assertIs(admit_quorum("record", 3, 3, halted=True), False)
        params = inspect.signature(classify_threshold).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_short_and_sealed_do_not_grant_send(self):
        bind = bind_quorum("classify", 1, 3, seat=_SEAT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_threshold(0, 0)
        self.assertFalse(zero_required_satisfies())
        self.assertFalse(lowering_required_satisfies())


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_quorum("classify", 3, 3, seat="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_quorum_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_quorum("classify", 3, 3, seat=_SEAT)
        pin_seat(table, first)
        second = bind_quorum("classify", 1, 3, seat=_SEAT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_seat(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_threshold(3, 3)
        b = classify_threshold(3, 3)
        self.assertEqual(a, b)
        self.assertEqual(a, QUORUM)
        first = bind_quorum("classify", 3, 3, seat=_SEAT)
        second = bind_quorum("classify", 3, 3, seat=_SEAT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
