"""Contract tests for invert_pin (P1 complementary).

A pinned μ is not a send. Same encoding is already_pinned.
A different value on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.invert_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    measured_one_is_unknown,
    measured_zero_is_unknown,
    missing_mu_is_zero,
    peek_invert,
    pin_allows_sample,
    pin_allows_send,
    pin_invert,
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
from ofn.kernel.mobius_class import (
    MINUS,
    PLUS,
    ZERO,
    MobiusBind,
    bind_mobius,
)

_SLOT = "env-mob-0001"


def _bind(value: int, *, intent: str = "classify") -> MobiusBind:
    return bind_mobius(intent, value, slot=_SLOT)


class PinInverts(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_invert(table, _bind(6)), PINNED)
        self.assertEqual(peek_invert(table, _SLOT), "6:1:plus")

    def test_same_value_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_invert(table, _bind(6))
        self.assertEqual(pin_invert(table, _bind(6)), ALREADY_PINNED)

    def test_minus_encoding(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_invert(table, _bind(30)), PINNED)
        self.assertEqual(peek_invert(table, _SLOT), "30:-1:minus")

    def test_zero_encoding(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_invert(table, _bind(4)), PINNED)
        self.assertEqual(peek_invert(table, _SLOT), "4:0:zero")

    def test_different_value_fails_closed(self):
        table: dict[str, str] = {}
        pin_invert(table, _bind(6))
        with self.assertRaises(FailClosedError) as ctx:
            pin_invert(table, _bind(4))
        self.assertIn("invert_collision", str(ctx.exception))

    def test_zero_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(4)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_invert(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_plus_sample_allows_sample_not_send(self):
        bind = _bind(6, intent="sample")
        self.assertEqual(bind.family, PLUS)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_minus_sample_does_not_allow_sample(self):
        bind = _bind(30, intent="sample")
        self.assertEqual(bind.family, MINUS)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_invert({}, _SLOT))
        self.assertIsNone(peek_invert({}, None))
        self.assertIsNot(peek_invert({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_invert({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 6, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 6, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 6, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(6)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(6)
        pin_invert(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_invert(table, _bind(6))
        other = bind_mobius("classify", 4, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = MobiusBind(
            intent="classify", family=PLUS, value=4,
            mu=1, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_invert(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_invert(None, _bind(6))  # type: ignore[arg-type]


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
        self.assertFalse(missing_mu_is_zero())
        self.assertFalse(measured_zero_is_unknown())
        self.assertFalse(measured_one_is_unknown())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
