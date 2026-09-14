"""Contract tests for figure_pin (P1 complementary).

A pinned pentagonal is not a send. Same encoding is already_pinned.
A different value on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Same pair is replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.figure_pin import (
    ALREADY_PINNED,
    PINNED,
    catalan_is_pentagonal,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    hexagonal_is_pentagonal,
    later_disarm_supersedes,
    measured_zero_is_pentagonal,
    missing_index_is_zero,
    negative_is_other,
    peek_figure,
    pell_is_pentagonal,
    pin_allows_sample,
    pin_allows_send,
    pin_figure,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    retcon_refused,
    square_is_pentagonal,
    stride_is_pentagonal,
    timeout_proves_concurrent_write,
    triangular_is_pentagonal,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.pentagonal_class import (
    OTHER,
    PENTAGONAL,
    ZERO,
    PentagonalBind,
    bind_pentagonal,
)

_SLOT = "env-pen-0001"


def _bind(value: int, *, intent: str = "classify") -> PentagonalBind:
    return bind_pentagonal(intent, value, slot=_SLOT)


class PinFigures(unittest.TestCase):
    def test_first_pin_pentagonal(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_figure(table, _bind(12)), PINNED)
        self.assertEqual(peek_figure(table, _SLOT), "12:3:pentagonal")

    def test_same_pentagonal_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_figure(table, _bind(12))
        self.assertEqual(pin_figure(table, _bind(12)), ALREADY_PINNED)

    def test_one_pins_as_index_one(self):
        table: dict[str, str] = {}
        bind = _bind(1)
        self.assertEqual(bind.family, PENTAGONAL)
        self.assertEqual(pin_figure(table, bind), PINNED)
        self.assertEqual(peek_figure(table, _SLOT), "1:1:pentagonal")

    def test_zero_pins_as_zero_not_pentagonal(self):
        table: dict[str, str] = {}
        bind = _bind(0)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_figure(table, bind), PINNED)
        self.assertEqual(peek_figure(table, _SLOT), "0:-:zero")
        self.assertFalse(measured_zero_is_pentagonal())

    def test_other_pins_without_index(self):
        table: dict[str, str] = {}
        bind = _bind(2)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_figure(table, bind), PINNED)
        self.assertEqual(peek_figure(table, _SLOT), "2:-:other")
        self.assertFalse(hexagonal_is_pentagonal())
        self.assertFalse(triangular_is_pentagonal())
        self.assertFalse(square_is_pentagonal())
        self.assertFalse(pell_is_pentagonal())
        self.assertFalse(catalan_is_pentagonal())
        self.assertFalse(stride_is_pentagonal())

    def test_different_value_fails_closed(self):
        table: dict[str, str] = {}
        pin_figure(table, _bind(12))
        with self.assertRaises(FailClosedError) as ctx:
            pin_figure(table, _bind(5))
        self.assertIn("figure_collision", str(ctx.exception))

    def test_other_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(4)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_figure(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_pentagonal_sample_allows_sample_not_send(self):
        bind = _bind(5, intent="sample")
        self.assertEqual(bind.family, PENTAGONAL)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_figure({}, _SLOT))
        self.assertIsNone(peek_figure({}, None))
        self.assertIsNot(peek_figure({}, _SLOT), False)
        self.assertFalse(missing_index_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_figure({}, "send_authorized")

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
        pin_figure(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_figure(table, _bind(5))
        other = bind_pentagonal("classify", 12, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = PentagonalBind(
            intent="classify", family=PENTAGONAL, value=12,
            index=2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_figure(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_figure(None, _bind(5))  # type: ignore[arg-type]


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
        self.assertFalse(measured_zero_is_pentagonal())
        self.assertFalse(hexagonal_is_pentagonal())
        self.assertFalse(triangular_is_pentagonal())
        self.assertFalse(square_is_pentagonal())
        self.assertFalse(pell_is_pentagonal())
        self.assertFalse(catalan_is_pentagonal())
        self.assertFalse(stride_is_pentagonal())
        self.assertFalse(negative_is_other())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
