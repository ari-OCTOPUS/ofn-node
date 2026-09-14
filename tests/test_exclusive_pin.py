"""Contract tests for exclusive_pin (P1 complementary).

A pinned inclusion is not a send. Same triple is already_pinned.
A different kind on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.exclusive_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    exclusive_on_bound_is_on,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_exclusive,
    pin_allows_sample,
    pin_allows_send,
    pin_exclusive,
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
from ofn.kernel.inclusive_class import (
    EXCLUSIVE,
    INCLUSIVE,
    ON,
    OUT,
    InclusiveBind,
    bind_inclusive,
)

_SLOT = "env-inc-0001"
_BOUND = 10


def _bind(
    value: int,
    *,
    intent: str = "classify",
    kind: str = EXCLUSIVE,
    bound: int = _BOUND,
) -> InclusiveBind:
    return bind_inclusive(
        intent, value, bound=bound, kind=kind, slot=_SLOT)


class PinExclusive(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_exclusive(table, _bind(10)), PINNED)
        self.assertEqual(peek_exclusive(table, _SLOT), "exclusive:10:out")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_exclusive(table, _bind(10))
        self.assertEqual(pin_exclusive(table, _bind(10)), ALREADY_PINNED)

    def test_different_kind_fails_closed(self):
        table: dict[str, str] = {}
        pin_exclusive(table, _bind(10, kind=EXCLUSIVE))
        with self.assertRaises(FailClosedError) as ctx:
            pin_exclusive(table, _bind(10, kind=INCLUSIVE))
        self.assertIn("exclusive_collision", str(ctx.exception))

    def test_exclusive_out_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(10)
        self.assertEqual(bind.family, OUT)
        self.assertEqual(pin_exclusive(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_sample(bind))

    def test_inclusive_on_sample_allows_sample_not_send(self):
        bind = _bind(10, intent="sample", kind=INCLUSIVE)
        self.assertEqual(bind.family, ON)
        self.assertTrue(pin_allows_sample(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_exclusive_sample_does_not_allow_sample(self):
        bind = _bind(10, intent="sample", kind=EXCLUSIVE)
        self.assertEqual(bind.family, OUT)
        self.assertFalse(pin_allows_sample(bind))
        self.assertFalse(grants_send())
        self.assertFalse(exclusive_on_bound_is_on())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_exclusive({}, _SLOT))
        self.assertIsNone(peek_exclusive({}, None))
        self.assertIsNot(peek_exclusive({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_exclusive({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, None, 10, bound=_BOUND, kind=EXCLUSIVE, slot=_SLOT))
        self.assertIsNone(
            try_pin(
                table, "classify", None, bound=_BOUND, kind=EXCLUSIVE,
                slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 10, bound=_BOUND, kind=EXCLUSIVE,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(
                table, "classify", 10, bound=_BOUND, kind=EXCLUSIVE,
                slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(10)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(10)
        pin_exclusive(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_exclusive(table, _bind(10, kind=EXCLUSIVE))
        other = bind_inclusive(
            "classify", 10, bound=_BOUND, kind=INCLUSIVE, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = InclusiveBind(
            intent="classify", kind=EXCLUSIVE, family=ON, value=10,
            bound=_BOUND, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_exclusive(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_exclusive(None, _bind(10))  # type: ignore[arg-type]


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
        self.assertFalse(exclusive_on_bound_is_on())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
