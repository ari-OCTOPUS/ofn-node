"""Contract tests for step_pin (P1 complementary).

A pinned step is not a send. Same triple is already_pinned.
A different step on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.step_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_step,
    pin_allows_admit,
    pin_allows_send,
    pin_step,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.stride_class import (
    SKIP,
    UNIT,
    StrideBind,
    bind_stride,
)

_SLOT = "env-stride-0001"
_FROM = 10


def _bind(stride: int, *, intent: str = "classify") -> StrideBind:
    return bind_stride(intent, stride, from_index=_FROM, slot=_SLOT)


class PinSteps(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_step(table, _bind(1)), PINNED)
        self.assertEqual(peek_step(table, _SLOT), "unit:1:10")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_step(table, _bind(1))
        self.assertEqual(pin_step(table, _bind(1)), ALREADY_PINNED)

    def test_different_stride_fails_closed(self):
        table: dict[str, str] = {}
        pin_step(table, _bind(1))
        with self.assertRaises(FailClosedError) as ctx:
            pin_step(table, _bind(3))
        self.assertIn("step_collision", str(ctx.exception))

    def test_skip_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(8)
        self.assertEqual(bind.family, SKIP)
        self.assertEqual(pin_step(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_admit(bind))

    def test_unit_admit_allows_admit_not_send(self):
        bind = _bind(1, intent="admit")
        self.assertEqual(bind.family, UNIT)
        self.assertTrue(pin_allows_admit(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_skip_admit_allows_admit_not_send(self):
        bind = _bind(4, intent="admit")
        self.assertEqual(bind.family, SKIP)
        self.assertTrue(pin_allows_admit(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_step({}, _SLOT))
        self.assertIsNone(peek_step({}, None))
        self.assertIsNot(peek_step({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_step({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 1, from_index=_FROM, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, from_index=_FROM, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 1, from_index=_FROM, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 1, from_index=_FROM, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(1)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(1)
        pin_step(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_step(table, _bind(1))
        other = bind_stride(
            "classify", 3, from_index=_FROM, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = StrideBind(
            intent="classify", family=UNIT, stride=3, from_index=_FROM,
            next_index=13, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_step(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_step(None, _bind(1))  # type: ignore[arg-type]


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
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
