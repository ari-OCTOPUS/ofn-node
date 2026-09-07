"""Contract tests for center_pin (P1 complementary).

A pinned middle is not a send. Same pair is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.mid_class import (
    EVEN_SPLIT,
    ODD_CENTER,
    SINGLE,
    MidBind,
    bind_mid,
)
from ofn.kernel.center_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    empty_is_zero,
    even_split_is_zero,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_center,
    peek_writes,
    pin_allows_center,
    pin_allows_send,
    pin_center,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-mid-0001"


def _bind(length: int, *, intent: str = "classify") -> MidBind:
    return bind_mid(intent, length, slot=_SLOT)


class PinCenters(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_center(table, _bind(5)), PINNED)
        self.assertEqual(peek_center(table, _SLOT), "odd_center:5")

    def test_same_pair_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_center(table, _bind(5))
        self.assertEqual(pin_center(table, _bind(5)), ALREADY_PINNED)

    def test_different_family_fails_closed(self):
        table: dict[str, str] = {}
        pin_center(table, _bind(5))
        with self.assertRaises(FailClosedError) as ctx:
            pin_center(table, _bind(4))
        self.assertIn("center_collision", str(ctx.exception))

    def test_even_split_pins_and_is_not_a_center(self):
        table: dict[str, str] = {}
        bind = _bind(4)
        self.assertEqual(bind.family, EVEN_SPLIT)
        self.assertEqual(pin_center(table, bind), PINNED)
        self.assertEqual(peek_center(table, _SLOT), "even_split:4")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_center(bind))

    def test_odd_center_allows_center_not_send(self):
        bind = _bind(5, intent="center")
        self.assertEqual(bind.family, ODD_CENTER)
        self.assertTrue(pin_allows_center(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_single_center_allows_center_not_send(self):
        bind = _bind(1, intent="center")
        self.assertEqual(bind.family, SINGLE)
        self.assertTrue(pin_allows_center(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_even_split_center_does_not_allow_center(self):
        bind = _bind(4, intent="center")
        self.assertEqual(bind.family, EVEN_SPLIT)
        self.assertFalse(pin_allows_center(bind))
        self.assertFalse(grants_send())

    def test_empty_center_does_not_allow_center(self):
        bind = _bind(0, intent="center")
        self.assertFalse(pin_allows_center(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_center({}, _SLOT))
        self.assertIsNone(peek_center({}, None))
        self.assertIsNot(peek_center({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_center({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 5, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 5, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 5, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(5)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(5)
        pin_center(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_center(table, _bind(5))
        other = bind_mid("classify", 4, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = MidBind(
            intent="classify", family=ODD_CENTER, length=4,
            slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_center(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_center(None, _bind(5))  # type: ignore[arg-type]


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
        self.assertFalse(even_split_is_zero())
        self.assertFalse(peek_writes())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
