"""Contract tests for dozen_pin (P1 complementary).

A pinned 12-gon is not a send. Same triple is already_pinned.
A different figure on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.dodecagonal_class import (
    DODECAGONAL,
    OTHER,
    ZERO,
    DodecaBind,
    bind_dodeca,
)
from ofn.kernel.dozen_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    missing_index_is_zero,
    peek_dozen,
    pin_allows_sample,
    pin_allows_send,
    pin_dozen,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-do-0001"


def _bind(value: int, *, intent: str = "classify") -> DodecaBind:
    return bind_dodeca(intent, value, slot=_SLOT)


class PinDozen(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_dozen(table, _bind(33)), PINNED)
        self.assertEqual(peek_dozen(table, _SLOT), "33:3:dodecagonal")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_dozen(table, _bind(33))
        self.assertEqual(pin_dozen(table, _bind(33)), ALREADY_PINNED)

    def test_different_figure_fails_closed(self):
        table: dict[str, str] = {}
        pin_dozen(table, _bind(33))
        with self.assertRaises(FailClosedError) as ctx:
            pin_dozen(table, _bind(12))
        self.assertIn("dozen_collision", str(ctx.exception))

    def test_other_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(2)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_dozen(table, bind), PINNED)
        self.assertEqual(peek_dozen(table, _SLOT), "2::other")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_sample_dodecagonal_allows_sample_not_send(self):
        bind = _bind(12, intent="sample")
        self.assertEqual(bind.family, DODECAGONAL)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_dozen({}, _SLOT))
        self.assertIsNone(peek_dozen({}, None))
        self.assertIsNot(peek_dozen({}, _SLOT), False)
        self.assertFalse(missing_index_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_dozen({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 12, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 12, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 12, slot=_SLOT), PINNED)

    def test_retcon_missing_is_none(self):
        self.assertIsNone(retcon_refused({}, _bind(12)))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(12)
        pin_dozen(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_dozen(table, _bind(12))
        other = bind_dodeca("classify", 33, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = DodecaBind(
            intent="classify", family=DODECAGONAL, value=33, index=2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_dozen(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_dozen(None, _bind(12))  # type: ignore[arg-type]


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
