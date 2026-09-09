"""Contract tests for nest_pin (P1 complementary).

A pinned Catalan is not a send. Same encoding is already_pinned.
A different value on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Same pair is replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.catalan_class import (
    CATALAN,
    OTHER,
    ZERO,
    CatalanBind,
    bind_catalan,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.nest_pin import (
    ALREADY_PINNED,
    PINNED,
    binomial_choose_is_catalan,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    measured_zero_is_catalan,
    missing_index_is_zero,
    negative_is_other,
    peek_nest,
    pin_allows_sample,
    pin_allows_send,
    pin_nest,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-cat-0001"


def _bind(value: int, *, intent: str = "classify") -> CatalanBind:
    return bind_catalan(intent, value, slot=_SLOT)


class PinNests(unittest.TestCase):
    def test_first_pin_catalan(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_nest(table, _bind(14)), PINNED)
        self.assertEqual(peek_nest(table, _SLOT), "14:4:catalan")

    def test_same_catalan_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_nest(table, _bind(14))
        self.assertEqual(pin_nest(table, _bind(14)), ALREADY_PINNED)

    def test_one_pins_as_index_zero(self):
        table: dict[str, str] = {}
        bind = _bind(1)
        self.assertEqual(bind.family, CATALAN)
        self.assertEqual(pin_nest(table, bind), PINNED)
        self.assertEqual(peek_nest(table, _SLOT), "1:0:catalan")

    def test_zero_pins_as_zero_not_catalan(self):
        table: dict[str, str] = {}
        bind = _bind(0)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_nest(table, bind), PINNED)
        self.assertEqual(peek_nest(table, _SLOT), "0:-:zero")
        self.assertFalse(measured_zero_is_catalan())

    def test_other_pins_without_index(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_nest(table, bind), PINNED)
        self.assertEqual(peek_nest(table, _SLOT), "3:-:other")
        self.assertFalse(binomial_choose_is_catalan())

    def test_different_value_fails_closed(self):
        table: dict[str, str] = {}
        pin_nest(table, _bind(14))
        with self.assertRaises(FailClosedError) as ctx:
            pin_nest(table, _bind(5))
        self.assertIn("nest_collision", str(ctx.exception))

    def test_other_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(4)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_nest(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_catalan_sample_allows_sample_not_send(self):
        bind = _bind(5, intent="sample")
        self.assertEqual(bind.family, CATALAN)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_nest({}, _SLOT))
        self.assertIsNone(peek_nest({}, None))
        self.assertIsNot(peek_nest({}, _SLOT), False)
        self.assertFalse(missing_index_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_nest({}, "send_authorized")

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
        pin_nest(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_nest(table, _bind(5))
        other = bind_catalan("classify", 14, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = CatalanBind(
            intent="classify", family=CATALAN, value=14,
            index=3, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_nest(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_nest(None, _bind(5))  # type: ignore[arg-type]


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
        self.assertFalse(measured_zero_is_catalan())
        self.assertFalse(binomial_choose_is_catalan())
        self.assertFalse(negative_is_other())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
