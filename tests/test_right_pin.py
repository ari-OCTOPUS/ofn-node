"""Contract tests for right_pin (P1 complementary).

A pinned side is not a send. Same triple is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.left_class import (
    AT,
    LEFT,
    RIGHT,
    LeftBind,
    bind_left,
)
from ofn.kernel.right_pin import (
    ALREADY_PINNED,
    PINNED,
    at_is_send,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_signed_is_zero,
    peek_right,
    pin_allows_left,
    pin_allows_right,
    pin_allows_send,
    pin_right,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-left-0001"
_ORIGIN = 10


def _bind(index: int, *, intent: str = "classify") -> LeftBind:
    return bind_left(intent, index, origin=_ORIGIN, slot=_SLOT)


class PinRights(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_right(table, _bind(7)), PINNED)
        self.assertEqual(peek_right(table, _SLOT), "left:7:10")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_right(table, _bind(7))
        self.assertEqual(pin_right(table, _bind(7)), ALREADY_PINNED)

    def test_different_index_fails_closed(self):
        table: dict[str, str] = {}
        pin_right(table, _bind(7))
        with self.assertRaises(FailClosedError) as ctx:
            pin_right(table, _bind(14))
        self.assertIn("right_collision", str(ctx.exception))

    def test_right_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(14)
        self.assertEqual(bind.family, RIGHT)
        self.assertEqual(pin_right(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_left(bind))
        self.assertFalse(pin_allows_right(bind))

    def test_left_mark_allows_left_not_send(self):
        bind = _bind(7, intent="mark")
        self.assertEqual(bind.family, LEFT)
        self.assertTrue(pin_allows_left(bind))
        self.assertFalse(pin_allows_right(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_right_mark_allows_right_not_send(self):
        bind = _bind(14, intent="mark")
        self.assertEqual(bind.family, RIGHT)
        self.assertTrue(pin_allows_right(bind))
        self.assertFalse(pin_allows_left(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_at_mark_does_not_allow_left_or_right(self):
        bind = _bind(10, intent="mark")
        self.assertEqual(bind.family, AT)
        self.assertFalse(pin_allows_left(bind))
        self.assertFalse(pin_allows_right(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_right({}, _SLOT))
        self.assertIsNone(peek_right({}, None))
        self.assertIsNot(peek_right({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_right({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 10, origin=_ORIGIN, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, origin=_ORIGIN, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 10, origin=_ORIGIN, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 10, origin=_ORIGIN, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(10)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(10)
        pin_right(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_right(table, _bind(10))
        other = bind_left("classify", 14, origin=_ORIGIN, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = LeftBind(
            intent="classify", family=LEFT, index=7, origin=_ORIGIN,
            signed=9, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_right(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_right(None, _bind(10))  # type: ignore[arg-type]

    def test_signed_index_pins(self):
        table: dict[str, str] = {}
        bind = bind_left("classify", -2, origin=0, slot=_SLOT)
        self.assertEqual(pin_right(table, bind), PINNED)
        self.assertEqual(peek_right(table, _SLOT), "left:-2:0")


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
