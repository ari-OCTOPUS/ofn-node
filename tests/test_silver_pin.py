"""Contract tests for silver_pin (P1 complementary).

A pinned Pell is not a send. Same encoding is already_pinned.
A different value on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Same pair is replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.pell_class import (
    OTHER,
    PELL,
    ZERO,
    PellBind,
    bind_pell,
)
from ofn.kernel.silver_pin import (
    ALREADY_PINNED,
    PINNED,
    catalan_is_pell,
    claims_immutable,
    consumes_nonce,
    fibonacci_is_pell,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    lucas_is_pell,
    measured_zero_is_pell,
    missing_index_is_zero,
    negative_is_other,
    peek_silver,
    pin_allows_sample,
    pin_allows_send,
    pin_silver,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    retcon_refused,
    stride_is_pell,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-pel-0001"


def _bind(value: int, *, intent: str = "classify") -> PellBind:
    return bind_pell(intent, value, slot=_SLOT)


class PinSilvers(unittest.TestCase):
    def test_first_pin_pell(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_silver(table, _bind(12)), PINNED)
        self.assertEqual(peek_silver(table, _SLOT), "12:4:pell")

    def test_same_pell_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_silver(table, _bind(12))
        self.assertEqual(pin_silver(table, _bind(12)), ALREADY_PINNED)

    def test_one_pins_as_index_one(self):
        table: dict[str, str] = {}
        bind = _bind(1)
        self.assertEqual(bind.family, PELL)
        self.assertEqual(pin_silver(table, bind), PINNED)
        self.assertEqual(peek_silver(table, _SLOT), "1:1:pell")

    def test_zero_pins_as_zero_not_pell(self):
        table: dict[str, str] = {}
        bind = _bind(0)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_silver(table, bind), PINNED)
        self.assertEqual(peek_silver(table, _SLOT), "0:-:zero")
        self.assertFalse(measured_zero_is_pell())

    def test_other_pins_without_index(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_silver(table, bind), PINNED)
        self.assertEqual(peek_silver(table, _SLOT), "3:-:other")
        self.assertFalse(fibonacci_is_pell())
        self.assertFalse(catalan_is_pell())
        self.assertFalse(lucas_is_pell())
        self.assertFalse(stride_is_pell())

    def test_different_value_fails_closed(self):
        table: dict[str, str] = {}
        pin_silver(table, _bind(12))
        with self.assertRaises(FailClosedError) as ctx:
            pin_silver(table, _bind(5))
        self.assertIn("silver_collision", str(ctx.exception))

    def test_other_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(4)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_silver(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_pell_sample_allows_sample_not_send(self):
        bind = _bind(5, intent="sample")
        self.assertEqual(bind.family, PELL)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_silver({}, _SLOT))
        self.assertIsNone(peek_silver({}, None))
        self.assertIsNot(peek_silver({}, _SLOT), False)
        self.assertFalse(missing_index_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_silver({}, "send_authorized")

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
        self.assertEqual(try_pin(table, "classify", 5, slot=_SLOT), PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(5)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(5)
        pin_silver(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_silver(table, _bind(5))
        other = bind_pell("classify", 12, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = PellBind(
            intent="classify", family=PELL, value=12,
            index=3, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_silver(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_silver(None, _bind(5))  # type: ignore[arg-type]


class StructuralRefusals(unittest.TestCase):
    def test_flags(self):
        self.assertFalse(grants_send())
        self.assertFalse(rearms_send())
        self.assertFalse(halt_blocks_pin())
        self.assertFalse(ready_is_authorized())
        self.assertFalse(claims_immutable())
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(proposal_is_execution())
        self.assertFalse(promotes_ready_to_send())
        self.assertFalse(wires_into_run_store())
        self.assertFalse(consumes_nonce())
        self.assertFalse(unknown_is_false())
        self.assertFalse(missing_index_is_zero())
        self.assertFalse(measured_zero_is_pell())
        self.assertFalse(fibonacci_is_pell())
        self.assertFalse(catalan_is_pell())
        self.assertFalse(lucas_is_pell())
        self.assertFalse(stride_is_pell())
        self.assertFalse(negative_is_other())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
