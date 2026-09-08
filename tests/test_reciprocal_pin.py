"""Contract tests for reciprocal_pin (P1 complementary).

A pinned bag is not a send. Same encoding is already_pinned.
A different bag on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Permuted sides replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.harmonic_class import (
    EXACT,
    MIXED,
    HarmonicBind,
    bind_harmonic,
)
from ofn.kernel.reciprocal_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_harmonic_is_one,
    mixed_mean_is_zero,
    peek_reciprocal,
    pin_allows_sample,
    pin_allows_send,
    pin_reciprocal,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-har-0001"
_EXACT_BAG = (2, 3, 6)
_MIXED_BAG = (2, 3)


def _bind(values, *, intent: str = "classify") -> HarmonicBind:
    return bind_harmonic(intent, values, slot=_SLOT)


class PinReciprocals(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_reciprocal(table, _bind(_EXACT_BAG)), PINNED)
        self.assertEqual(peek_reciprocal(table, _SLOT), "2,3,6:exact:3")

    def test_same_bag_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_reciprocal(table, _bind(_EXACT_BAG))
        self.assertEqual(
            pin_reciprocal(table, _bind(_EXACT_BAG)), ALREADY_PINNED)

    def test_permuted_sides_are_replay(self):
        table: dict[str, str] = {}
        pin_reciprocal(table, _bind(_EXACT_BAG))
        swapped = bind_harmonic("classify", (6, 2, 3), slot=_SLOT)
        self.assertEqual(pin_reciprocal(table, swapped), ALREADY_PINNED)
        self.assertEqual(peek_reciprocal(table, _SLOT), "2,3,6:exact:3")

    def test_different_bag_fails_closed(self):
        table: dict[str, str] = {}
        pin_reciprocal(table, _bind(_EXACT_BAG))
        with self.assertRaises(FailClosedError) as ctx:
            pin_reciprocal(table, _bind(_MIXED_BAG))
        self.assertIn("reciprocal_collision", str(ctx.exception))

    def test_mixed_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(_MIXED_BAG)
        self.assertEqual(bind.family, MIXED)
        self.assertEqual(pin_reciprocal(table, bind), PINNED)
        self.assertEqual(peek_reciprocal(table, _SLOT), "2,3:mixed:-")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_exact_sample_allows_sample_not_send(self):
        bind = _bind(_EXACT_BAG, intent="sample")
        self.assertEqual(bind.family, EXACT)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_mixed_sample_does_not_allow_sample(self):
        bind = _bind(_MIXED_BAG, intent="sample")
        self.assertEqual(bind.family, MIXED)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_ones_encode_exact_one(self):
        table: dict[str, str] = {}
        bind = _bind((1, 1))
        self.assertEqual(bind.harmonic, 1)
        self.assertEqual(pin_reciprocal(table, bind), PINNED)
        self.assertEqual(peek_reciprocal(table, _SLOT), "1,1:exact:1")

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_reciprocal({}, _SLOT))
        self.assertIsNone(peek_reciprocal({}, None))
        self.assertIsNot(peek_reciprocal({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_reciprocal({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, _EXACT_BAG, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", _EXACT_BAG, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", _EXACT_BAG, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(_EXACT_BAG)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(_EXACT_BAG)
        pin_reciprocal(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_reciprocal(table, _bind(_EXACT_BAG))
        other = bind_harmonic("classify", _MIXED_BAG, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = HarmonicBind(
            intent="classify", family=MIXED, harmonic=None,
            values=_EXACT_BAG, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_reciprocal(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_reciprocal(None, _bind(_EXACT_BAG))  # type: ignore[arg-type]


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
        self.assertFalse(missing_harmonic_is_one())
        self.assertFalse(mixed_mean_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
