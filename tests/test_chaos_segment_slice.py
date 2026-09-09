"""Owner-absent chaos for segment_class / slice_pin.

While the owner cannot be reached: missing stays UNKNOWN, a timeout
does not invent a writer, HALT does not block classify/observe, a
cut never becomes a send, and a recorded slice never becomes
authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.segment_class import (
    FIT,
    admit_segment,
    bind_segment,
    classify_intent,
    classify_kind,
    classify_span,
    grants_send,
    halt_blocks_classify,
    later_disarm_supersedes,
    ready_is_authorized,
    try_bind,
)
from ofn.kernel.slice_pin import (
    pin_allows_send,
    pin_slice,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
)

_LENGTH = 8
_SLOT = "env-seg-chaos1"


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertIsNone(classify_span(None, 3, _LENGTH))
        self.assertEqual(classify_intent(None), "UNKNOWN")
        self.assertEqual(classify_kind(None), "UNKNOWN")
        self.assertIsNone(
            try_bind(
                None, "header", start=0, end=3, length=_LENGTH, slot=_SLOT))
        self.assertIsNone(
            try_bind(
                "classify", None, start=0, end=3, length=_LENGTH, slot=_SLOT))
        self.assertIsNot(classify_span(None, 3, _LENGTH), False)


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_is_unknown(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_span(0, 3, _LENGTH, timeout=True))
        self.assertIsNone(
            admit_segment(
                "cut", "header", start=0, end=3, length=_LENGTH,
                timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", "header", start=0, end=3, length=_LENGTH,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertIs(
            admit_segment(
                "classify", "header", start=0, end=3, length=_LENGTH,
                halted=True),
            True)
        self.assertIs(
            admit_segment(
                "cut", "header", start=0, end=3, length=_LENGTH,
                halted=True),
            False)
        params = inspect.signature(classify_span).parameters
        self.assertNotIn("halted", params)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_overflow_and_sealed_do_not_grant_send(self):
        bind = bind_segment(
            "classify", "trailer", start=0, end=12, length=_LENGTH,
            slot=_SLOT)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(grants_send())
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        with self.assertRaises(FailClosedError):
            bind_segment(
                "classify", "header", start=0, end=3, length=_LENGTH,
                slot="campaign_envelope_ready")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_slice_collision_is_fail_closed(self):
        table: dict[str, str] = {}
        first = bind_segment(
            "classify", "header", start=0, end=3, length=_LENGTH, slot=_SLOT)
        pin_slice(table, first)
        second = bind_segment(
            "classify", "header", start=0, end=5, length=_LENGTH, slot=_SLOT)
        self.assertIs(retcon_refused(table, second), True)
        with self.assertRaises(FailClosedError):
            pin_slice(table, second)


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_reclassify_is_deterministic_and_later_disarm_holds(self):
        a = classify_span(0, 3, _LENGTH)
        b = classify_span(0, 3, _LENGTH)
        self.assertEqual(a, b)
        self.assertEqual(a, FIT)
        first = bind_segment(
            "classify", "header", start=0, end=3, length=_LENGTH, slot=_SLOT)
        second = bind_segment(
            "classify", "header", start=0, end=3, length=_LENGTH, slot=_SLOT)
        self.assertEqual(first, second)
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
