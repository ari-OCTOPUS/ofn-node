"""Contract tests for decay_pin (P1 complementary).

A pinned age is not a send. Same triple is already_pinned.
A different age on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.aging_class import (
    DECAYED,
    DUE,
    FRESH,
    AgingBind,
    bind_aging,
)
from ofn.kernel.decay_pin import (
    ALREADY_PINNED,
    PINNED,
    age_is_zero,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_decay,
    peek_writes,
    pin_allows_decay,
    pin_allows_send,
    pin_decay,
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

_SLOT = "env-age-0001"
_AFTER = 8


def _bind(age: int, *, intent: str = "classify") -> AgingBind:
    return bind_aging(intent, age, decay_after=_AFTER, slot=_SLOT)


class PinDecays(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_decay(table, _bind(3)), PINNED)
        self.assertEqual(peek_decay(table, _SLOT), "3:8:fresh")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_decay(table, _bind(3))
        self.assertEqual(pin_decay(table, _bind(3)), ALREADY_PINNED)

    def test_different_age_fails_closed(self):
        table: dict[str, str] = {}
        pin_decay(table, _bind(3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_decay(table, _bind(8))
        self.assertIn("decay_collision", str(ctx.exception))

    def test_fresh_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        self.assertEqual(bind.family, FRESH)
        self.assertEqual(pin_decay(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_decay(bind))

    def test_due_decay_allows_decay_not_send(self):
        bind = _bind(8, intent="decay")
        self.assertEqual(bind.family, DUE)
        self.assertTrue(pin_allows_decay(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_decayed_decay_allows_decay_not_send(self):
        bind = _bind(12, intent="decay")
        self.assertEqual(bind.family, DECAYED)
        self.assertTrue(pin_allows_decay(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_fresh_decay_does_not_allow_decay(self):
        bind = _bind(3, intent="decay")
        self.assertEqual(bind.family, FRESH)
        self.assertFalse(pin_allows_decay(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_decay({}, _SLOT))
        self.assertIsNone(peek_decay({}, None))
        self.assertIsNot(peek_decay({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_decay({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, 3, decay_after=_AFTER, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, decay_after=_AFTER, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, decay_after=_AFTER, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", 3, decay_after=_AFTER, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        pin_decay(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_decay(table, _bind(3))
        other = bind_aging("classify", 8, decay_after=_AFTER, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = AgingBind(
            intent="classify", family=FRESH, age_ticks=3,
            decay_after=_AFTER, remaining=1, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_decay(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_decay(None, _bind(3))  # type: ignore[arg-type]


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
        self.assertFalse(age_is_zero())
        self.assertFalse(peek_writes())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
