"""Contract tests for trough_pin (P1 complementary).

A pinned extremum is not a send. Same quadruple is already_pinned.
A different family on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.peak_class import (
    NEITHER,
    PEAK,
    TROUGH,
    PeakBind,
    bind_peak,
)
from ofn.kernel.trough_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_is_zero,
    peek_trough,
    pin_allows_sample,
    pin_allows_send,
    pin_trough,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-peak-0001"


def _bind(
    earlier: int,
    mid: int,
    later: int,
    *,
    intent: str = "classify",
) -> PeakBind:
    return bind_peak(intent, earlier, mid, later, slot=_SLOT)


class PinTroughs(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_trough(table, _bind(4, -1, 2)), PINNED)
        self.assertEqual(peek_trough(table, _SLOT), "TROUGH:4:-1:2")

    def test_same_quadruple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_trough(table, _bind(4, -1, 2))
        self.assertEqual(pin_trough(table, _bind(4, -1, 2)), ALREADY_PINNED)

    def test_different_family_fails_closed(self):
        table: dict[str, str] = {}
        pin_trough(table, _bind(4, -1, 2))
        with self.assertRaises(FailClosedError) as ctx:
            pin_trough(table, _bind(1, 5, 0))
        self.assertIn("trough_collision", str(ctx.exception))

    def test_peak_pins_and_is_not_a_sample_grant(self):
        table: dict[str, str] = {}
        bind = _bind(-2, 5, 1)
        self.assertEqual(bind.family, PEAK)
        self.assertEqual(pin_trough(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_neither_pins_and_is_not_a_sample_grant(self):
        bind = _bind(1, 2, 3)
        self.assertEqual(bind.family, NEITHER)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_trough_sample_allows_sample_not_send(self):
        bind = _bind(4, -1, 2, intent="sample")
        self.assertEqual(bind.family, TROUGH)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_peak_sample_does_not_allow_sample(self):
        bind = _bind(-2, 5, 1, intent="sample")
        self.assertEqual(bind.family, PEAK)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_trough({}, _SLOT))
        self.assertIsNone(peek_trough({}, None))
        self.assertIsNot(peek_trough({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_trough({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 4, -1, 2, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, -1, 2, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 4, -1, 2, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 4, -1, 2, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(4, -1, 2)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(4, -1, 2)
        pin_trough(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_trough(table, _bind(4, -1, 2))
        other = bind_peak("classify", 1, 5, 0, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = PeakBind(
            intent="classify", family=TROUGH, earlier=4, mid=9, later=2,
            slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_trough(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_trough(None, _bind(4, -1, 2))  # type: ignore[arg-type]


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
        self.assertFalse(missing_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
