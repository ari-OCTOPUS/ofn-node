"""Contract tests for linger_pin (P1 complementary).

A pinned linger is not a send. Same quadruple is already_pinned.
A different elapsed on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.grace_class import (
    GRACE,
    LAPSED,
    LIVE,
    GraceBind,
    bind_grace,
)
from ofn.kernel.linger_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    elapsed_is_zero,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_linger,
    peek_writes,
    pin_allows_linger,
    pin_allows_send,
    pin_linger,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-grace-0001"
_DUE = 8
_LINGER = 4


def _bind(elapsed: int, *, intent: str = "classify") -> GraceBind:
    return bind_grace(
        intent, elapsed, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)


class PinLingers(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_linger(table, _bind(3)), PINNED)
        self.assertEqual(peek_linger(table, _SLOT), "3:8:4:live")

    def test_same_quadruple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_linger(table, _bind(3))
        self.assertEqual(pin_linger(table, _bind(3)), ALREADY_PINNED)

    def test_different_elapsed_fails_closed(self):
        table: dict[str, str] = {}
        pin_linger(table, _bind(3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_linger(table, _bind(8))
        self.assertIn("linger_collision", str(ctx.exception))

    def test_live_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        self.assertEqual(bind.family, LIVE)
        self.assertEqual(pin_linger(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_linger(bind))

    def test_grace_linger_allows_linger_not_send(self):
        bind = _bind(8, intent="linger")
        self.assertEqual(bind.family, GRACE)
        self.assertTrue(pin_allows_linger(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_lapsed_linger_does_not_allow_linger(self):
        bind = _bind(12, intent="linger")
        self.assertEqual(bind.family, LAPSED)
        self.assertFalse(pin_allows_linger(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_live_linger_does_not_allow_linger(self):
        bind = _bind(3, intent="linger")
        self.assertEqual(bind.family, LIVE)
        self.assertFalse(pin_allows_linger(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_linger({}, _SLOT))
        self.assertIsNone(peek_linger({}, None))
        self.assertIsNot(peek_linger({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_linger({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, None, 3, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT))
        self.assertIsNone(
            try_pin(
                table, "classify", None, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", 3, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(
                table, "classify", 3, due_after=_DUE, linger_after=_LINGER,
                slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        pin_linger(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_linger(table, _bind(3))
        other = bind_grace(
            "classify", 8, due_after=_DUE, linger_after=_LINGER, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = GraceBind(
            intent="classify", family=LIVE, elapsed_ticks=3,
            due_after=_DUE, linger_after=_LINGER, remaining=1, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_linger(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_linger(None, _bind(3))  # type: ignore[arg-type]


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
        self.assertFalse(elapsed_is_zero())
        self.assertFalse(peek_writes())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
