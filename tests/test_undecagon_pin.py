"""Contract tests for undecagon_pin (P1 complementary).

A pinned 11-gon is not a send. Same triple is already_pinned.
A different figure on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.hendecagonal_class import (
    HENDECA,
    OTHER,
    ZERO,
    HendecaBind,
    bind_hendeca,
)
from ofn.kernel.undecagon_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_index_is_zero,
    peek_undecagon,
    pin_allows_sample,
    pin_allows_send,
    pin_undecagon,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-hd-0001"


def _bind(value: int, *, intent: str = "classify") -> HendecaBind:
    return bind_hendeca(intent, value, slot=_SLOT)


class PinUndecagon(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_undecagon(table, _bind(30)), PINNED)
        self.assertEqual(peek_undecagon(table, _SLOT), "30:3:hendeca")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_undecagon(table, _bind(30))
        self.assertEqual(pin_undecagon(table, _bind(30)), ALREADY_PINNED)

    def test_different_figure_fails_closed(self):
        table: dict[str, str] = {}
        pin_undecagon(table, _bind(30))
        with self.assertRaises(FailClosedError) as ctx:
            pin_undecagon(table, _bind(11))
        self.assertIn("undecagon_collision", str(ctx.exception))

    def test_other_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(2)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_undecagon(table, bind), PINNED)
        self.assertEqual(peek_undecagon(table, _SLOT), "2::other")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_sample_hendeca_allows_sample_not_send(self):
        bind = _bind(11, intent="sample")
        self.assertEqual(bind.family, HENDECA)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_undecagon({}, _SLOT))
        self.assertIsNone(peek_undecagon({}, None))
        self.assertIsNot(peek_undecagon({}, _SLOT), False)
        self.assertFalse(missing_index_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_undecagon({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 11, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 11, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 11, slot=_SLOT), PINNED)

    def test_retcon_missing_is_none(self):
        self.assertIsNone(retcon_refused({}, _bind(11)))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(11)
        pin_undecagon(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_undecagon(table, _bind(11))
        other = bind_hendeca("classify", 30, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = HendecaBind(
            intent="classify", family=HENDECA, value=30, index=2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_undecagon(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_undecagon(None, _bind(11))  # type: ignore[arg-type]


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
        self.assertFalse(missing_index_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
