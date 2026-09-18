"""Contract tests for root_pin (P1 complementary).

A pinned square is not a send. Same encoding is already_pinned.
A different value on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Same pair is replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.root_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    floor_root_is_exact,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    measured_zero_is_square,
    missing_root_is_zero,
    peek_root,
    pin_allows_sample,
    pin_allows_send,
    pin_root,
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
from ofn.kernel.square_class import (
    OTHER,
    SQUARE,
    ZERO,
    SquareBind,
    bind_square,
)

_SLOT = "env-sqr-0001"


def _bind(value: int, *, intent: str = "classify") -> SquareBind:
    return bind_square(intent, value, slot=_SLOT)


class PinRoots(unittest.TestCase):
    def test_first_pin_square(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_root(table, _bind(9)), PINNED)
        self.assertEqual(peek_root(table, _SLOT), "9:3:square")

    def test_same_square_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_root(table, _bind(9))
        self.assertEqual(pin_root(table, _bind(9)), ALREADY_PINNED)

    def test_zero_pins_as_zero_not_square(self):
        table: dict[str, str] = {}
        bind = _bind(0)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_root(table, bind), PINNED)
        self.assertEqual(peek_root(table, _SLOT), "0:0:zero")
        self.assertFalse(measured_zero_is_square())

    def test_other_pins_without_exact_root(self):
        table: dict[str, str] = {}
        bind = _bind(2)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_root(table, bind), PINNED)
        self.assertEqual(peek_root(table, _SLOT), "2:-:other")
        self.assertFalse(floor_root_is_exact())

    def test_different_value_fails_closed(self):
        table: dict[str, str] = {}
        pin_root(table, _bind(9))
        with self.assertRaises(FailClosedError) as ctx:
            pin_root(table, _bind(4))
        self.assertIn("root_collision", str(ctx.exception))

    def test_other_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(8)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_root(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_square_sample_allows_sample_not_send(self):
        bind = _bind(4, intent="sample")
        self.assertEqual(bind.family, SQUARE)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_root({}, _SLOT))
        self.assertIsNone(peek_root({}, None))
        self.assertIsNot(peek_root({}, _SLOT), False)
        self.assertFalse(missing_root_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_root({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 4, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 4, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(try_pin(table, "classify", 4, slot=_SLOT), PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(4)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(4)
        pin_root(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_root(table, _bind(4))
        other = bind_square("classify", 9, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = SquareBind(
            intent="classify", family=SQUARE, value=9,
            root=2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_root(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_root(None, _bind(4))  # type: ignore[arg-type]


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
        self.assertFalse(missing_root_is_zero())
        self.assertFalse(measured_zero_is_square())
        self.assertFalse(floor_root_is_exact())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
