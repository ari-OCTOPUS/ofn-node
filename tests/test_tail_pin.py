"""Contract tests for tail_pin (P1 complementary).

A pinned end is not a send. Same triple is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.head_class import (
    HEAD,
    SINGLE,
    TAIL,
    HeadBind,
    bind_head,
)
from ofn.kernel.tail_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    empty_is_zero,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_tail,
    peek_writes,
    pin_allows_send,
    pin_allows_take,
    pin_tail,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-head-0001"


def _bind(length: int, index: int, *, intent: str = "classify") -> HeadBind:
    return bind_head(intent, length, index=index, slot=_SLOT)


class PinTails(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_tail(table, _bind(4, 3)), PINNED)
        self.assertEqual(peek_tail(table, _SLOT), "tail:4:3")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_tail(table, _bind(4, 3))
        self.assertEqual(pin_tail(table, _bind(4, 3)), ALREADY_PINNED)

    def test_different_family_fails_closed(self):
        table: dict[str, str] = {}
        pin_tail(table, _bind(4, 3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_tail(table, _bind(4, 0))
        self.assertIn("tail_collision", str(ctx.exception))

    def test_head_pins_and_is_not_a_take(self):
        table: dict[str, str] = {}
        bind = _bind(4, 0)
        self.assertEqual(bind.family, HEAD)
        self.assertEqual(pin_tail(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_take(bind))

    def test_tail_take_allows_take_not_send(self):
        bind = _bind(4, 3, intent="take")
        self.assertEqual(bind.family, TAIL)
        self.assertTrue(pin_allows_take(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_single_take_allows_take_not_send(self):
        bind = _bind(1, 0, intent="take")
        self.assertEqual(bind.family, SINGLE)
        self.assertTrue(pin_allows_take(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_head_take_does_not_allow_take(self):
        bind = _bind(4, 0, intent="take")
        self.assertEqual(bind.family, HEAD)
        self.assertFalse(pin_allows_take(bind))
        self.assertFalse(grants_send())

    def test_past_take_does_not_allow_take(self):
        bind = _bind(4, 4, intent="take")
        self.assertFalse(pin_allows_take(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_tail({}, _SLOT))
        self.assertIsNone(peek_tail({}, None))
        self.assertIsNot(peek_tail({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_tail({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 4, index=3, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, index=3, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 4, index=3, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 4, index=3, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(4, 3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(4, 3)
        pin_tail(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_tail(table, _bind(4, 3))
        other = bind_head("classify", 4, index=0, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = HeadBind(
            intent="classify", family=TAIL, length=4,
            index=0, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_tail(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_tail(None, _bind(4, 3))  # type: ignore[arg-type]


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
        self.assertFalse(empty_is_zero())
        self.assertFalse(peek_writes())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
