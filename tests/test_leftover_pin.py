"""Contract tests for leftover_pin (P1 complementary).

A pinned leftover is not a send. Same triple is already_pinned.
A different leftover on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.leftover_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    leftover_is_zero,
    peek_leftover,
    pin_allows_consume,
    pin_allows_send,
    pin_leftover,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.remainder_class import (
    EXACT,
    PARTIAL,
    RemainderBind,
    bind_remainder,
)

_SLOT = "env-rem-0001"
_STRIDE = 8


def _bind(length: int, *, intent: str = "classify") -> RemainderBind:
    return bind_remainder(intent, length, stride=_STRIDE, slot=_SLOT)


class PinLeftovers(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_leftover(table, _bind(19)), PINNED)
        self.assertEqual(peek_leftover(table, _SLOT), "3:8:partial")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_leftover(table, _bind(19))
        self.assertEqual(pin_leftover(table, _bind(19)), ALREADY_PINNED)

    def test_different_leftover_fails_closed(self):
        table: dict[str, str] = {}
        pin_leftover(table, _bind(19))
        with self.assertRaises(FailClosedError) as ctx:
            pin_leftover(table, _bind(17))
        self.assertIn("leftover_collision", str(ctx.exception))

    def test_partial_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(19)
        self.assertEqual(bind.family, PARTIAL)
        self.assertEqual(pin_leftover(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_consume(bind))

    def test_exact_consume_allows_consume_not_send(self):
        bind = _bind(16, intent="consume")
        self.assertEqual(bind.family, EXACT)
        self.assertTrue(pin_allows_consume(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_partial_consume_does_not_allow_consume(self):
        bind = _bind(19, intent="consume")
        self.assertEqual(bind.family, PARTIAL)
        self.assertFalse(pin_allows_consume(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_leftover({}, _SLOT))
        self.assertIsNone(peek_leftover({}, None))
        self.assertIsNot(peek_leftover({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_leftover({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 16, stride=_STRIDE, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, stride=_STRIDE, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 16, stride=_STRIDE, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 16, stride=_STRIDE, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(16)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(16)
        pin_leftover(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_leftover(table, _bind(16))
        other = bind_remainder("classify", 19, stride=_STRIDE, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = RemainderBind(
            intent="classify", family=EXACT, leftover=3, length=19,
            stride=_STRIDE, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_leftover(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_leftover(None, _bind(16))  # type: ignore[arg-type]


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
        self.assertFalse(leftover_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
