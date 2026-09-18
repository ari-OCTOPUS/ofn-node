"""Contract tests for far_pin (P1 complementary).

A pinned distance is not a send. Same quadruple is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.far_pin import (
    ALREADY_PINNED,
    PINNED,
    at_is_send,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_distance_is_zero,
    peek_far,
    pin_allows_far,
    pin_allows_near,
    pin_allows_send,
    pin_far,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.near_class import (
    AT,
    FAR,
    NEAR,
    NearBind,
    bind_near,
)

_SLOT = "env-near-0001"
_ORIGIN = 10
_RADIUS = 3


def _bind(index: int, *, intent: str = "classify") -> NearBind:
    return bind_near(
        intent, index, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)


class PinFars(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_far(table, _bind(12)), PINNED)
        self.assertEqual(peek_far(table, _SLOT), "near:12:10:3")

    def test_same_quadruple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_far(table, _bind(12))
        self.assertEqual(pin_far(table, _bind(12)), ALREADY_PINNED)

    def test_different_index_fails_closed(self):
        table: dict[str, str] = {}
        pin_far(table, _bind(12))
        with self.assertRaises(FailClosedError) as ctx:
            pin_far(table, _bind(14))
        self.assertIn("far_collision", str(ctx.exception))

    def test_far_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(14)
        self.assertEqual(bind.family, FAR)
        self.assertEqual(pin_far(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_near(bind))
        self.assertFalse(pin_allows_far(bind))

    def test_near_mark_allows_near_not_send(self):
        bind = _bind(12, intent="mark")
        self.assertEqual(bind.family, NEAR)
        self.assertTrue(pin_allows_near(bind))
        self.assertFalse(pin_allows_far(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_far_mark_allows_far_not_send(self):
        bind = _bind(14, intent="mark")
        self.assertEqual(bind.family, FAR)
        self.assertTrue(pin_allows_far(bind))
        self.assertFalse(pin_allows_near(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_at_mark_does_not_allow_near_or_far(self):
        bind = _bind(10, intent="mark")
        self.assertEqual(bind.family, AT)
        self.assertFalse(pin_allows_near(bind))
        self.assertFalse(pin_allows_far(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_far({}, _SLOT))
        self.assertIsNone(peek_far({}, None))
        self.assertIsNot(peek_far({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_far({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 10, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT))
        self.assertIsNone(
            try_pin(
                table, "classify", None, origin=_ORIGIN, radius=_RADIUS,
                slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 10, origin=_ORIGIN, radius=_RADIUS,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(
                table, "classify", 10, origin=_ORIGIN, radius=_RADIUS,
                slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(10)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(10)
        pin_far(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_far(table, _bind(10))
        other = bind_near(
            "classify", 14, origin=_ORIGIN, radius=_RADIUS, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = NearBind(
            intent="classify", family=NEAR, index=12, origin=_ORIGIN,
            radius=_RADIUS, distance=9, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_far(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_far(None, _bind(10))  # type: ignore[arg-type]

    def test_signed_index_pins(self):
        table: dict[str, str] = {}
        bind = bind_near(
            "classify", -2, origin=0, radius=3, slot=_SLOT)
        self.assertEqual(pin_far(table, bind), PINNED)
        self.assertEqual(peek_far(table, _SLOT), "near:-2:0:3")


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
        self.assertFalse(missing_distance_is_zero())
        self.assertFalse(at_is_send())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
