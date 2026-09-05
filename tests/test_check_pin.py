"""Contract tests for check_pin (P1 complementary).

A pinned even/odd is not a send. Same pair is
already_pinned. A different family on the same slot fails closed.
peek never writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.check_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    even_is_authorized,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_check,
    pin_allows_record,
    pin_allows_send,
    pin_check,
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
from ofn.kernel.parity_class import (
    EVEN,
    ODD,
    ParityBind,
    bind_parity,
)

_SLOT = "env-par-0001"


def _bind(count: int, *, intent: str = "classify") -> ParityBind:
    return bind_parity(intent, count, slot=_SLOT)


class PinChecks(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_check(table, _bind(4)), PINNED)
        self.assertEqual(peek_check(table, _SLOT), "even:4")

    def test_same_pair_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_check(table, _bind(4))
        self.assertEqual(pin_check(table, _bind(4)), ALREADY_PINNED)

    def test_different_count_fails_closed(self):
        table: dict[str, str] = {}
        pin_check(table, _bind(4))
        with self.assertRaises(FailClosedError) as ctx:
            pin_check(table, _bind(6))
        self.assertIn("parity_collision", str(ctx.exception))

    def test_odd_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(5)
        self.assertEqual(bind.family, ODD)
        self.assertEqual(pin_check(table, bind), PINNED)
        self.assertEqual(peek_check(table, _SLOT), "odd:5")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_record(bind))

    def test_even_record_allows_record_not_send(self):
        bind = _bind(2, intent="record")
        self.assertEqual(bind.family, EVEN)
        self.assertTrue(pin_allows_record(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_odd_record_allows_record_not_send(self):
        bind = _bind(3, intent="record")
        self.assertEqual(bind.family, ODD)
        self.assertTrue(pin_allows_record(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_classify_even_does_not_allow_record(self):
        bind = _bind(0, intent="classify")
        self.assertEqual(bind.family, EVEN)
        self.assertFalse(pin_allows_record(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_check({}, _SLOT))
        self.assertIsNone(peek_check({}, None))
        self.assertIsNot(peek_check({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_check({}, "send_authorized")

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
        pin_check(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_check(table, _bind(4))
        other = bind_parity("classify", 5, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = ParityBind(
            intent="classify", family=EVEN, count=5, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_check(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_check(None, _bind(4))  # type: ignore[arg-type]


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
        self.assertFalse(even_is_authorized())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
