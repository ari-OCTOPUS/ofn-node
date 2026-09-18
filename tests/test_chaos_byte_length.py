"""Owner-absent chaos for byte_class / length_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe, a
measure never becomes a send, and a recorded length never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.byte_class import (
    BOUNDED,
    admit_bytes,
    bind_bytes,
    classify_family,
    classify_intent,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.length_pin import (
    pin_allows_send,
    pin_length,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_BOUND = 8
_SLOT = "env-byte-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_family(None, bound=_BOUND))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertIsNone(try_bind(None, b"ab", bound=_BOUND, slot=_SLOT))
        self.assertIsNone(try_bind("classify", None, bound=_BOUND, slot=_SLOT))
        self.assertIsNot(classify_family(None, bound=_BOUND), False)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(
            classify_family(b"abcd", bound=_BOUND, timeout=True))
        self.assertIsNone(
            admit_bytes("measure", b"abcd", bound=_BOUND, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", b"abcd", bound=_BOUND, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_bytes("classify", b"ab", bound=_BOUND, halted=True),
            True)
        self.assertIs(
            admit_bytes("measure", b"ab", bound=_BOUND, halted=True),
            False)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_oversize_and_sealed_do_not_grant_send(self):
        bind = bind_bytes(
            "classify", b"0123456789", bound=_BOUND, slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_bytes(
                "classify", b"ab", bound=_BOUND,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_length_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_bytes("classify", b"ab", bound=_BOUND, slot=_SLOT)
        pin_length(table, first)
        second = bind_bytes("classify", b"abcd", bound=_BOUND, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_length(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(b"abcd", bound=_BOUND)
        b = classify_family(b"abcd", bound=_BOUND)
        self.assertEqual(a, b)
        self.assertEqual(a, BOUNDED)
        first = bind_bytes("classify", b"abcd", bound=_BOUND, slot=_SLOT)
        second = bind_bytes("classify", b"abcd", bound=_BOUND, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
