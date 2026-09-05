"""Contract tests for length_pin (P1 complementary).

A pinned length is not a send. Same triple is already_pinned.
A different length on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.byte_class import (
    BOUNDED,
    EMPTY,
    OVERSIZE,
    ByteBind,
    bind_bytes,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.length_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_length,
    pin_allows_measure,
    pin_allows_send,
    pin_length,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-byte-0001"
_BOUND = 8


def _bind(payload: bytes, *, intent: str = "classify") -> ByteBind:
    return bind_bytes(intent, payload, bound=_BOUND, slot=_SLOT)


class PinLengths(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_length(table, _bind(b"abcd")), PINNED)
        self.assertEqual(peek_length(table, _SLOT), "bounded:4:8")

    def test_same_triple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_length(table, _bind(b"abcd"))
        self.assertEqual(pin_length(table, _bind(b"abcd")), ALREADY_PINNED)

    def test_different_size_fails_closed(self):
        table: dict[str, str] = {}
        pin_length(table, _bind(b"ab"))
        with self.assertRaises(FailClosedError) as ctx:
            pin_length(table, _bind(b"abcd"))
        self.assertIn("length_collision", str(ctx.exception))

    def test_oversize_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(b"0123456789")
        self.assertEqual(bind.family, OVERSIZE)
        self.assertEqual(pin_length(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_measure(bind))

    def test_empty_measure_allows_measure_not_send(self):
        bind = _bind(b"", intent="measure")
        self.assertEqual(bind.family, EMPTY)
        self.assertTrue(pin_allows_measure(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_bounded_measure_allows_measure_not_send(self):
        bind = _bind(b"ab", intent="measure")
        self.assertEqual(bind.family, BOUNDED)
        self.assertTrue(pin_allows_measure(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_length({}, _SLOT))
        self.assertIsNone(peek_length({}, None))
        self.assertIsNot(peek_length({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_length({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, b"ab", bound=_BOUND, slot=_SLOT))
        self.assertIsNone(
            try_pin(table, "classify", None, bound=_BOUND, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", b"ab", bound=_BOUND, slot=_SLOT,
                timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, "classify", b"ab", bound=_BOUND, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(b"ab")
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(b"ab")
        pin_length(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_length(table, _bind(b"ab"))
        other = bind_bytes("classify", b"abcd", bound=_BOUND, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = ByteBind(
            intent="classify", family=EMPTY, size=4, bound=_BOUND,
            slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_length(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_length(None, _bind(b"ab"))  # type: ignore[arg-type]


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
