"""Contract tests for common_pin (P1 complementary).

A pinned pair is not a send. Same encoding is already_pinned.
A different pair on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Swapped sides replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.common_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_gcd_is_zero,
    peek_common,
    pin_allows_sample,
    pin_allows_send,
    pin_common,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.coprime_class import (
    COMMON,
    COPRIME,
    CoprimeBind,
    bind_coprime,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-cop-0001"


def _bind(left: int, right: int, *, intent: str = "classify") -> CoprimeBind:
    return bind_coprime(intent, left, right=right, slot=_SLOT)


class PinCommons(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_common(table, _bind(8, 12)), PINNED)
        self.assertEqual(peek_common(table, _SLOT), "8:12:4:common")

    def test_same_pair_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_common(table, _bind(8, 12))
        self.assertEqual(pin_common(table, _bind(8, 12)), ALREADY_PINNED)

    def test_swapped_sides_are_replay(self):
        table: dict[str, str] = {}
        pin_common(table, _bind(8, 12))
        swapped = bind_coprime("classify", 12, right=8, slot=_SLOT)
        self.assertEqual(pin_common(table, swapped), ALREADY_PINNED)
        self.assertEqual(peek_common(table, _SLOT), "8:12:4:common")

    def test_different_pair_fails_closed(self):
        table: dict[str, str] = {}
        pin_common(table, _bind(8, 12))
        with self.assertRaises(FailClosedError) as ctx:
            pin_common(table, _bind(8, 9))
        self.assertIn("common_collision", str(ctx.exception))

    def test_common_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(8, 12)
        self.assertEqual(bind.family, COMMON)
        self.assertEqual(pin_common(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_coprime_sample_allows_sample_not_send(self):
        bind = _bind(8, 9, intent="sample")
        self.assertEqual(bind.family, COPRIME)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_common_sample_does_not_allow_sample(self):
        bind = _bind(8, 12, intent="sample")
        self.assertEqual(bind.family, COMMON)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_common({}, _SLOT))
        self.assertIsNone(peek_common({}, None))
        self.assertIsNot(peek_common({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_common({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 8, right=9, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, right=9, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 8, right=9, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 8, right=9, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(8, 9)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(8, 9)
        pin_common(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_common(table, _bind(8, 9))
        other = bind_coprime("classify", 8, right=12, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = CoprimeBind(
            intent="classify", family=COMMON, gcd=4, left=8,
            right=9, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_common(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_common(None, _bind(8, 9))  # type: ignore[arg-type]


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
        self.assertFalse(missing_gcd_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
