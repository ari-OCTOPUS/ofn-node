"""Contract tests for room_pin (P1 complementary).

A pinned remaining room is not a send. Same quadruple is
already_pinned. A different room on the same slot fails closed.
peek never writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.capacity_class import (
    EMPTY,
    FULL,
    HAS_ROOM,
    OVER_CAP,
    CapacityBind,
    bind_capacity,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.room_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_room,
    pin_allows_reserve,
    pin_allows_send,
    pin_room,
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

_SLOT = "env-cap-0001"
_LIMIT = 8


def _bind(used: int, *, intent: str = "classify") -> CapacityBind:
    return bind_capacity(intent, used, limit=_LIMIT, slot=_SLOT)


class PinRooms(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_room(table, _bind(3)), PINNED)
        self.assertEqual(peek_room(table, _SLOT), "5:3:8:has_room")

    def test_same_quadruple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_room(table, _bind(3))
        self.assertEqual(pin_room(table, _bind(3)), ALREADY_PINNED)

    def test_different_room_fails_closed(self):
        table: dict[str, str] = {}
        pin_room(table, _bind(3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_room(table, _bind(4))
        self.assertIn("room_collision", str(ctx.exception))

    def test_over_cap_pins_unknown_room_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(9)
        self.assertEqual(bind.family, OVER_CAP)
        self.assertEqual(pin_room(table, bind), PINNED)
        self.assertEqual(peek_room(table, _SLOT), "unknown:9:8:over_cap")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_reserve(bind))

    def test_empty_reserve_allows_reserve_not_send(self):
        bind = _bind(0, intent="reserve")
        self.assertEqual(bind.family, EMPTY)
        self.assertTrue(pin_allows_reserve(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_has_room_reserve_allows_reserve_not_send(self):
        bind = _bind(3, intent="reserve")
        self.assertEqual(bind.family, HAS_ROOM)
        self.assertTrue(pin_allows_reserve(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_full_reserve_does_not_allow_reserve(self):
        bind = _bind(_LIMIT, intent="reserve")
        self.assertEqual(bind.family, FULL)
        self.assertFalse(pin_allows_reserve(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_room({}, _SLOT))
        self.assertIsNone(peek_room({}, None))
        self.assertIsNot(peek_room({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_room({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 3, limit=_LIMIT, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, limit=_LIMIT, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, limit=_LIMIT, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 3, limit=_LIMIT, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        pin_room(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_room(table, _bind(3))
        other = bind_capacity("classify", 4, limit=_LIMIT, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = CapacityBind(
            intent="classify", family=HAS_ROOM, room=1, used=3,
            limit=_LIMIT, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_room(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_room(None, _bind(3))  # type: ignore[arg-type]


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
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
