"""Contract tests for below_pin (P1 complementary).

A pinned height is not a send. Same triple is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.below_pin import (
    ALREADY_PINNED,
    PINNED,
    at_is_send,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_signed_is_zero,
    peek_below,
    pin_allows_above,
    pin_allows_below,
    pin_allows_send,
    pin_below,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.above_class import (
    ABOVE,
    AT,
    BELOW,
    AboveBind,
    bind_above,
)

_SLOT = "env-above-0001"
_PLANE = 10


def _bind(height: int, *, intent: str = "classify") -> AboveBind:
    return bind_above(intent, height, plane=_PLANE, slot=_SLOT)


class PinBelows(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_below(table, _bind(7)), PINNED)
        self.assertEqual(peek_below(table, _SLOT), "below:7:10")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_below(table, _bind(7))
        self.assertEqual(pin_below(table, _bind(7)), ALREADY_PINNED)

    def test_different_height_fails_closed(self):
        table: dict[str, str] = {}
        pin_below(table, _bind(7))
        with self.assertRaises(FailClosedError) as ctx:
            pin_below(table, _bind(14))
        self.assertIn("below_collision", str(ctx.exception))

    def test_above_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(14)
        self.assertEqual(bind.family, ABOVE)
        self.assertEqual(pin_below(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_below(bind))
        self.assertFalse(pin_allows_above(bind))

    def test_below_mark_allows_below_not_send(self):
        bind = _bind(7, intent="mark")
        self.assertEqual(bind.family, BELOW)
        self.assertTrue(pin_allows_below(bind))
        self.assertFalse(pin_allows_above(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_above_mark_allows_above_not_send(self):
        bind = _bind(14, intent="mark")
        self.assertEqual(bind.family, ABOVE)
        self.assertTrue(pin_allows_above(bind))
        self.assertFalse(pin_allows_below(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_at_mark_does_not_allow_below_or_above(self):
        bind = _bind(10, intent="mark")
        self.assertEqual(bind.family, AT)
        self.assertFalse(pin_allows_below(bind))
        self.assertFalse(pin_allows_above(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_below({}, _SLOT))
        self.assertIsNone(peek_below({}, None))
        self.assertIsNot(peek_below({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_below({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 10, plane=_PLANE, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, plane=_PLANE, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 10, plane=_PLANE, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 10, plane=_PLANE, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(10)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(10)
        pin_below(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_below(table, _bind(10))
        other = bind_above("classify", 14, plane=_PLANE, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = AboveBind(
            intent="classify", family=BELOW, height=7, plane=_PLANE,
            signed=9, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_below(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_below(None, _bind(10))  # type: ignore[arg-type]

    def test_signed_height_pins(self):
        table: dict[str, str] = {}
        bind = bind_above("classify", -2, plane=0, slot=_SLOT)
        self.assertEqual(pin_below(table, bind), PINNED)
        self.assertEqual(peek_below(table, _SLOT), "below:-2:0")


class StructuralRefusals(unittest.TestCase):
    def test_flags(self):
        self.assertFalse(grants_send())
        self.assertFalse(halt_blocks_pin())
        self.assertFalse(ready_is_authorized())
        self.assertFalse(claims_immutable())
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(proposal_is_execution())
        self.assertFalse(promotes_ready_to_send())
        self.assertFalse(wires_into_run_store())
        self.assertFalse(consumes_nonce())
        self.assertFalse(unknown_is_false())
        self.assertFalse(missing_signed_is_zero())
        self.assertFalse(at_is_send())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
