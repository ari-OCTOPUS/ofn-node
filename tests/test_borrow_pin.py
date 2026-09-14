"""Contract tests for borrow_pin (P1 complementary).

A pinned borrow is not a send. Same encoding is already_pinned.
A different tuple on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.borrow_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_borrow,
    pin_allows_borrow,
    pin_allows_measure,
    pin_allows_send,
    pin_borrow,
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
from ofn.kernel.underflow_class import (
    EXACT,
    UNDERFLOW,
    WRAP,
    UnderflowBind,
    bind_sub,
)

_SLOT = "env-sub-0001"
_FLOOR = 0


def _bind(
    minuend: int,
    subtrahend: int,
    *,
    intent: str = "classify",
    wrap_requested: bool = False,
) -> UnderflowBind:
    return bind_sub(
        intent, minuend, subtrahend, floor=_FLOOR, slot=_SLOT,
        wrap_requested=wrap_requested)


class PinBorrows(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_borrow(table, _bind(8, 3)), PINNED)
        self.assertEqual(peek_borrow(table, _SLOT), "exact:8:3:0:0")

    def test_same_encoding_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_borrow(table, _bind(8, 3))
        self.assertEqual(pin_borrow(table, _bind(8, 3)), ALREADY_PINNED)

    def test_different_operands_fail_closed(self):
        table: dict[str, str] = {}
        pin_borrow(table, _bind(8, 3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_borrow(table, _bind(3, 8))
        self.assertIn("borrow_collision", str(ctx.exception))

    def test_underflow_pins_and_allows_borrow_not_send(self):
        table: dict[str, str] = {}
        bind = _bind(3, 8)
        self.assertEqual(bind.family, UNDERFLOW)
        self.assertEqual(pin_borrow(table, bind), PINNED)
        self.assertTrue(pin_allows_borrow(bind))
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_measure(bind))

    def test_wrap_pins_and_is_not_a_borrow(self):
        bind = _bind(3, 8, wrap_requested=True)
        self.assertEqual(bind.family, WRAP)
        self.assertFalse(pin_allows_borrow(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_exact_measure_allows_measure_not_send(self):
        bind = _bind(8, 3, intent="measure")
        self.assertEqual(bind.family, EXACT)
        self.assertTrue(pin_allows_measure(bind))
        self.assertFalse(pin_allows_borrow(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_borrow({}, _SLOT))
        self.assertIsNone(peek_borrow({}, None))
        self.assertIsNot(peek_borrow({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_borrow({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 8, 3, floor=_FLOOR, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, 3, floor=_FLOOR, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 8, 3, floor=_FLOOR, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 8, 3, floor=_FLOOR, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(8, 3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(8, 3)
        pin_borrow(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_borrow(table, _bind(8, 3))
        other = bind_sub("classify", 3, 8, floor=_FLOOR, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = UnderflowBind(
            intent="classify", family=UNDERFLOW, minuend=8,
            subtrahend=3, floor=_FLOOR, wrap_requested=False,
            slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_borrow(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_borrow(None, _bind(8, 3))  # type: ignore[arg-type]


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
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
