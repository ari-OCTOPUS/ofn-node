"""Owner-absent chaos for stride_class / step_pin.

While the owner cannot be reached: missing stays UNKNOWN, a
timeout does not invent a writer, HALT does not block classify
or pin, admit is a START, ready never becomes authorized, and
a later disarm still supersedes an older authorization claim.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.halt import is_halted
from ofn.kernel.step_pin import (
    PINNED,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_step,
    pin_allows_send,
    pin_step,
    timeout_proves_concurrent_write,
    try_pin,
)
from ofn.kernel.stride_class import (
    SKIP,
    UNIT,
    UNKNOWN,
    admit_stride,
    bind_stride,
    classify_family,
    classify_intent,
    halt_blocks_admit,
    halt_blocks_classify,
    halt_blocks_observe,
    try_bind,
)


class Scenario1MissingIsUnknownNotFalse(unittest.TestCase):
    def test_missing_is_unknown(self):
        self.assertEqual(classify_intent(None), UNKNOWN)
        self.assertNotEqual(classify_intent(None), "FALSE")
        self.assertIsNone(classify_family(None))
        self.assertIsNone(try_bind(None, 1, from_index=0, slot="s"))
        self.assertIsNone(admit_stride(None, 1))


class Scenario2TimeoutDoesNotProveWriter(unittest.TestCase):
    def test_timeout_flag_is_structurally_false(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertIsNone(classify_family(1, timeout=True))
        self.assertIsNone(admit_stride("admit", 1, timeout=True))
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 1, from_index=0, slot="s",
                    timeout=True))
        self.assertEqual(table, {})


class Scenario3HaltStopsStartsNotClassify(unittest.TestCase):
    def test_corrupt_halt_is_halted_and_classify_has_no_halt_param(self):
        self.assertTrue(is_halted("???"))
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_observe())
        self.assertTrue(halt_blocks_admit())
        self.assertFalse(halt_blocks_pin())
        self.assertEqual(classify_family(1), UNIT)
        self.assertEqual(classify_family(4), SKIP)
        params = inspect.signature(classify_family).parameters
        self.assertNotIn("halted", params)
        self.assertIs(admit_stride("classify", 1, halted=True), True)
        self.assertIs(admit_stride("admit", 1, halted=True), False)


class Scenario4ArmFailureDoesNotInventSend(unittest.TestCase):
    def test_refused_bind_does_not_grant_send(self):
        with self.assertRaises(FailClosedError):
            classify_intent("send_authorized")
        self.assertFalse(grants_send())
        bind = bind_stride("admit", 1, from_index=0, slot="s")
        self.assertFalse(pin_allows_send(bind))


class Scenario5ReadyStaysUnsent(unittest.TestCase):
    def test_ready_cannot_become_a_stride(self):
        with self.assertRaises(FailClosedError):
            classify_intent("campaign_envelope_ready")
        with self.assertRaises(FailClosedError):
            bind_stride(
                "classify", 1, from_index=0,
                slot="campaign_envelope_ready")
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario6DisagreementIsRecordedNotGuessed(unittest.TestCase):
    def test_collision_is_named_and_table_unchanged(self):
        table: dict[str, str] = {}
        first = bind_stride("classify", 1, from_index=0, slot="s")
        self.assertEqual(pin_step(table, first), PINNED)
        other = bind_stride("classify", 3, from_index=0, slot="s")
        with self.assertRaises(FailClosedError) as ctx:
            pin_step(table, other)
        self.assertIn("step_collision", str(ctx.exception))
        self.assertEqual(peek_step(table, "s"), "unit:1:0")


class Scenario7RecoveryNeedsNoOwner(unittest.TestCase):
    def test_rebind_is_deterministic_and_later_disarm_holds(self):
        a = classify_family(1)
        b = classify_family(1)
        self.assertEqual(a, b)
        self.assertEqual(a, UNIT)
        self.assertTrue(later_disarm_supersedes())
        table: dict[str, str] = {}
        bind = bind_stride("classify", 1, from_index=5, slot="s")
        pin_step(table, bind)
        self.assertEqual(pin_step(table, bind), "already_pinned")
        self.assertEqual(bind.next_index, 6)


if __name__ == "__main__":
    unittest.main()
