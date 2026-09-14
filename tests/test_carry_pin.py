"""Contract tests for carry_pin (P1 complementary).

A pinned carry is not a send. Same quintuple is already_pinned.
A different carry on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.carry_pin import (
    ALREADY_PINNED,
    PINNED,
    carry_is_zero,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_carry,
    pin_allows_consume,
    pin_allows_send,
    pin_carry,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.overflow_class import (
    FITS,
    OVERFLOW,
    OverflowBind,
    bind_overflow,
)

_SLOT = "env-ovf-0001"
_CAP = 8


def _bind(used: int, add: int, *, intent: str = "classify") -> OverflowBind:
    return bind_overflow(
        intent, used, add=add, capacity=_CAP, slot=_SLOT)


class PinCarries(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_carry(table, _bind(6, 3)), PINNED)
        self.assertEqual(peek_carry(table, _SLOT), "1:6:3:8:overflow")

    def test_same_quintuple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_carry(table, _bind(6, 3))
        self.assertEqual(pin_carry(table, _bind(6, 3)), ALREADY_PINNED)

    def test_different_carry_fails_closed(self):
        table: dict[str, str] = {}
        pin_carry(table, _bind(6, 3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_carry(table, _bind(7, 3))
        self.assertIn("carry_collision", str(ctx.exception))

    def test_overflow_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(6, 3)
        self.assertEqual(bind.family, OVERFLOW)
        self.assertEqual(pin_carry(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_consume(bind))

    def test_fits_consume_allows_consume_not_send(self):
        bind = _bind(5, 3, intent="consume")
        self.assertEqual(bind.family, FITS)
        self.assertTrue(pin_allows_consume(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_overflow_consume_does_not_allow_consume(self):
        bind = _bind(6, 3, intent="consume")
        self.assertEqual(bind.family, OVERFLOW)
        self.assertFalse(pin_allows_consume(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_carry({}, _SLOT))
        self.assertIsNone(peek_carry({}, None))
        self.assertIsNot(peek_carry({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_carry({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 5, add=3, capacity=_CAP, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, add=3, capacity=_CAP, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 5, add=3, capacity=_CAP, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 5, add=3, capacity=_CAP, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(5, 3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(5, 3)
        pin_carry(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_carry(table, _bind(5, 3))
        other = bind_overflow(
            "classify", 6, add=3, capacity=_CAP, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = OverflowBind(
            intent="classify", family=FITS, carry=1, used=6,
            add=3, capacity=_CAP, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_carry(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_carry(None, _bind(5, 3))  # type: ignore[arg-type]


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
        self.assertFalse(carry_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
