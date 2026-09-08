"""Contract tests for cubic_pin (P1 complementary).

A pinned cube is not a send. Same encoding is already_pinned.
A different value on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE. Same pair is replay.
"""

from __future__ import annotations

import unittest

from ofn.kernel.cube_class import (
    CUBE,
    OTHER,
    ZERO,
    CubeBind,
    bind_cube,
)
from ofn.kernel.cubic_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    floor_root_is_exact,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    measured_zero_is_cube,
    missing_root_is_zero,
    peek_cubic,
    pin_allows_sample,
    pin_allows_send,
    pin_cubic,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rearms_send,
    retcon_refused,
    signed_is_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_SLOT = "env-cub-0001"


def _bind(value: int, *, intent: str = "classify") -> CubeBind:
    return bind_cube(intent, value, slot=_SLOT)


class PinCubics(unittest.TestCase):
    def test_first_pin_cube(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_cubic(table, _bind(27)), PINNED)
        self.assertEqual(peek_cubic(table, _SLOT), "27:3:cube")

    def test_same_cube_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_cubic(table, _bind(27))
        self.assertEqual(pin_cubic(table, _bind(27)), ALREADY_PINNED)

    def test_signed_cube_pins(self):
        table: dict[str, str] = {}
        bind = _bind(-8)
        self.assertEqual(bind.family, CUBE)
        self.assertEqual(pin_cubic(table, bind), PINNED)
        self.assertEqual(peek_cubic(table, _SLOT), "-8:-2:cube")
        self.assertFalse(signed_is_refused())

    def test_zero_pins_as_zero_not_cube(self):
        table: dict[str, str] = {}
        bind = _bind(0)
        self.assertEqual(bind.family, ZERO)
        self.assertEqual(pin_cubic(table, bind), PINNED)
        self.assertEqual(peek_cubic(table, _SLOT), "0:0:zero")
        self.assertFalse(measured_zero_is_cube())

    def test_other_pins_without_exact_root(self):
        table: dict[str, str] = {}
        bind = _bind(2)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_cubic(table, bind), PINNED)
        self.assertEqual(peek_cubic(table, _SLOT), "2:-:other")
        self.assertFalse(floor_root_is_exact())

    def test_different_value_fails_closed(self):
        table: dict[str, str] = {}
        pin_cubic(table, _bind(27))
        with self.assertRaises(FailClosedError) as ctx:
            pin_cubic(table, _bind(8))
        self.assertIn("cubic_collision", str(ctx.exception))

    def test_other_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(9)
        self.assertEqual(bind.family, OTHER)
        self.assertEqual(pin_cubic(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_cube_sample_allows_sample_not_send(self):
        bind = _bind(8, intent="sample")
        self.assertEqual(bind.family, CUBE)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_zero_sample_does_not_allow_sample(self):
        bind = _bind(0, intent="sample")
        self.assertEqual(bind.family, ZERO)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_cubic({}, _SLOT))
        self.assertIsNone(peek_cubic({}, None))
        self.assertIsNot(peek_cubic({}, _SLOT), False)
        self.assertFalse(missing_root_is_zero())

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_cubic({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 8, slot=_SLOT))
        self.assertIsNone(try_pin(table, "classify", None, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 8, slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(try_pin(table, "classify", 8, slot=_SLOT), PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(8)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(8)
        pin_cubic(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_cubic(table, _bind(8))
        other = bind_cube("classify", 27, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = CubeBind(
            intent="classify", family=CUBE, value=27,
            root=2, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_cubic(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_cubic(None, _bind(8))  # type: ignore[arg-type]


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
        self.assertFalse(measured_zero_is_cube())
        self.assertFalse(floor_root_is_exact())
        self.assertFalse(signed_is_refused())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
