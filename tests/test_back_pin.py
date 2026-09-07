"""Contract tests for back_pin (P1 complementary).

A pinned depth is not a send. Same triple is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.back_pin import (
    ALREADY_PINNED,
    PINNED,
    at_is_send,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_signed_is_zero,
    peek_back,
    pin_allows_back,
    pin_allows_front,
    pin_allows_send,
    pin_back,
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
from ofn.kernel.front_class import (
    AT,
    BACK,
    FRONT,
    FrontBind,
    bind_front,
)

_SLOT = "env-front-0001"
_PLANE = 10


def _bind(depth: int, *, intent: str = "classify") -> FrontBind:
    return bind_front(intent, depth, plane=_PLANE, slot=_SLOT)


class PinBacks(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_back(table, _bind(7)), PINNED)
        self.assertEqual(peek_back(table, _SLOT), "back:7:10")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_back(table, _bind(7))
        self.assertEqual(pin_back(table, _bind(7)), ALREADY_PINNED)

    def test_different_depth_fails_closed(self):
        table: dict[str, str] = {}
        pin_back(table, _bind(7))
        with self.assertRaises(FailClosedError) as ctx:
            pin_back(table, _bind(14))
        self.assertIn("back_collision", str(ctx.exception))

    def test_front_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(14)
        self.assertEqual(bind.family, FRONT)
        self.assertEqual(pin_back(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_back(bind))
        self.assertFalse(pin_allows_front(bind))

    def test_back_mark_allows_back_not_send(self):
        bind = _bind(7, intent="mark")
        self.assertEqual(bind.family, BACK)
        self.assertTrue(pin_allows_back(bind))
        self.assertFalse(pin_allows_front(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_front_mark_allows_front_not_send(self):
        bind = _bind(14, intent="mark")
        self.assertEqual(bind.family, FRONT)
        self.assertTrue(pin_allows_front(bind))
        self.assertFalse(pin_allows_back(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_at_mark_does_not_allow_back_or_front(self):
        bind = _bind(10, intent="mark")
        self.assertEqual(bind.family, AT)
        self.assertFalse(pin_allows_back(bind))
        self.assertFalse(pin_allows_front(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_back({}, _SLOT))
        self.assertIsNone(peek_back({}, None))
        self.assertIsNot(peek_back({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_back({}, "send_authorized")

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
        pin_back(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_back(table, _bind(10))
        other = bind_front("classify", 14, plane=_PLANE, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = FrontBind(
            intent="classify", family=BACK, depth=7, plane=_PLANE,
            signed=9, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_back(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_back(None, _bind(10))  # type: ignore[arg-type]

    def test_signed_depth_pins(self):
        table: dict[str, str] = {}
        bind = bind_front("classify", -2, plane=0, slot=_SLOT)
        self.assertEqual(pin_back(table, bind), PINNED)
        self.assertEqual(peek_back(table, _SLOT), "back:-2:0")


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
