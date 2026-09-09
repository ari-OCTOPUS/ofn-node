"""Contract tests for shed_pin (P1 complementary).

A pinned shed line is not a send. Same triple is already_pinned.
A different depth on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.backlog_class import (
    AT,
    BELOW,
    OVER,
    BacklogBind,
    bind_backlog,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.shed_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    over_is_negative,
    peek_shed,
    pin_allows_send,
    pin_allows_shed,
    pin_shed,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    room_is_zero,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-bl-0001"
_LINE = 8


def _bind(depth: int, *, intent: str = "classify") -> BacklogBind:
    return bind_backlog(intent, depth, threshold=_LINE, slot=_SLOT)


class PinSheds(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_shed(table, _bind(11)), PINNED)
        self.assertEqual(peek_shed(table, _SLOT), "11:8:over")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_shed(table, _bind(11))
        self.assertEqual(pin_shed(table, _bind(11)), ALREADY_PINNED)

    def test_different_depth_fails_closed(self):
        table: dict[str, str] = {}
        pin_shed(table, _bind(11))
        with self.assertRaises(FailClosedError) as ctx:
            pin_shed(table, _bind(3))
        self.assertIn("shed_collision", str(ctx.exception))

    def test_below_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        self.assertEqual(bind.family, BELOW)
        self.assertEqual(pin_shed(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_shed(bind))

    def test_at_shed_allows_shed_not_send(self):
        bind = _bind(8, intent="shed")
        self.assertEqual(bind.family, AT)
        self.assertTrue(pin_allows_shed(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_over_shed_allows_shed_not_send(self):
        bind = _bind(11, intent="shed")
        self.assertEqual(bind.family, OVER)
        self.assertTrue(pin_allows_shed(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_below_shed_does_not_allow_shed(self):
        bind = _bind(3, intent="shed")
        self.assertEqual(bind.family, BELOW)
        self.assertFalse(pin_allows_shed(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_shed({}, _SLOT))
        self.assertIsNone(peek_shed({}, None))
        self.assertIsNot(peek_shed({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_shed({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 3, threshold=_LINE, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, threshold=_LINE, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, threshold=_LINE, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 3, threshold=_LINE, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        pin_shed(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_shed(table, _bind(3))
        other = bind_backlog("classify", 11, threshold=_LINE, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = BacklogBind(
            intent="classify", family=AT, depth=11,
            threshold=_LINE, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_shed(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_shed(None, _bind(3))  # type: ignore[arg-type]


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
        self.assertFalse(room_is_zero())
        self.assertFalse(over_is_negative())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
