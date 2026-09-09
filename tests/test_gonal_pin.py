"""Contract tests for gonal_pin (P1 complementary).

A pinned figure is not a send. Same encoding is already_pinned.
A different figure on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.gonal_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_value_is_zero,
    peek_gonal,
    pin_allows_sample,
    pin_allows_send,
    pin_gonal,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.heptagonal_class import (
    HEPTAGONAL,
    OTHER,
    ZERO,
    HeptagonalBind,
    bind_heptagonal,
)

_SLOT = "env-hep-0001"


def _bind(value: int, *, intent: str = "classify") -> HeptagonalBind:
    return bind_heptagonal(intent, value, slot=_SLOT)


class PinGonals(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_gonal(table, _bind(7)), PINNED)
        self.assertEqual(peek_gonal(table, _SLOT), "7:heptagonal:2")

    def test_same_figure_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_gonal(table, _bind(7))
        self.assertEqual(pin_gonal(table, _bind(7)), ALREADY_PINNED)

    def test_zero_pins_as_zero_index_zero(self):
        table: dict[str, str] = {}
        bind = _bind(0)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_gonal(table, bind), PINNED)
        self.assertEqual(peek_gonal(table, _SLOT), "0:zero:0")

    def test_other_pins_with_dash_index(self):
        table: dict[str, str] = {}
        bind = _bind(2)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_gonal(table, bind), PINNED)
        self.assertEqual(peek_gonal(table, _SLOT), "2:other:-")

    def test_different_figure_fails_closed(self):
        table: dict[str, str] = {}
        pin_gonal(table, _bind(7))
        with self.assertRaises(FailClosedError) as ctx:
            pin_gonal(table, _bind(18))
        self.assertIn("gonal_collision", str(ctx.exception))

    def test_heptagonal_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(7)
        self.assertEqual(bind.family, HEPTAGONAL)
        self.assertEqual(pin_gonal(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_sample_heptagonal_allows_sample_not_send(self):
        bind = _bind(1, intent="sample")
        self.assertEqual(bind.family, HEPTAGONAL)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_sample_zero_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_sample_other_does_not_allow_sample(self):
        bind = _bind(2, intent="sample")
        self.assertFalse(pin_allows_sample(bind))

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_gonal({}, _SLOT))
        self.assertIsNone(peek_gonal({}, None))
        self.assertIsNot(peek_gonal({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_gonal({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 7, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 7, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 7, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(7)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(7)
        pin_gonal(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_gonal(table, _bind(7))
        other = bind_heptagonal("classify", 18, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = HeptagonalBind(
            intent="classify", family=HEPTAGONAL, value=7,
            index=3, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_gonal(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_gonal(None, _bind(7))  # type: ignore[arg-type]


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
        self.assertFalse(missing_value_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
