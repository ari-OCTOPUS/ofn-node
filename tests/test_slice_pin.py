"""Contract tests for slice_pin (P1 complementary).

A pinned slice is not a send. Same quadruple is already_pinned.
A different slice on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.segment_class import (
    EMPTY,
    FIT,
    OVERFLOW,
    SegmentBind,
    bind_segment,
)
from ofn.kernel.slice_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_slice,
    pin_allows_cut,
    pin_allows_send,
    pin_slice,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-seg-0001"
_LENGTH = 8


def _bind(
    *,
    kind: str = "header",
    start: int = 0,
    end: int = 3,
    intent: str = "classify",
) -> SegmentBind:
    return bind_segment(
        intent, kind, start=start, end=end, length=_LENGTH, slot=_SLOT)


class PinSlices(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_slice(table, _bind()), PINNED)
        self.assertEqual(peek_slice(table, _SLOT), "header:0:3:8")

    def test_same_quadruple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_slice(table, _bind())
        self.assertEqual(pin_slice(table, _bind()), ALREADY_PINNED)

    def test_different_end_fails_closed(self):
        table: dict[str, str] = {}
        pin_slice(table, _bind(end=3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_slice(table, _bind(end=5))
        self.assertIn("slice_collision", str(ctx.exception))

    def test_overflow_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(kind="trailer", start=0, end=12)
        self.assertEqual(bind.span, OVERFLOW)
        self.assertEqual(pin_slice(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_cut(bind))

    def test_empty_cut_does_not_allow_cut_or_send(self):
        bind = _bind(start=3, end=3, intent="cut")
        self.assertEqual(bind.span, EMPTY)
        self.assertFalse(pin_allows_cut(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_fit_cut_allows_cut_not_send(self):
        bind = _bind(kind="body", start=2, end=5, intent="cut")
        self.assertEqual(bind.span, FIT)
        self.assertTrue(pin_allows_cut(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_slice({}, _SLOT))
        self.assertIsNone(peek_slice({}, None))
        self.assertIsNot(peek_slice({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_slice({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, None, "header", start=0, end=3, length=_LENGTH,
                slot=_SLOT))
        self.assertIsNone(
            try_pin(
                table, "classify", None, start=0, end=3, length=_LENGTH,
                slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", "header", start=0, end=3, length=_LENGTH,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(
                table, "classify", "header", start=0, end=3, length=_LENGTH,
                slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind()
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind()
        pin_slice(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_slice(table, _bind(end=3))
        other = bind_segment(
            "classify", "header", start=0, end=5, length=_LENGTH, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = SegmentBind(
            intent="classify", kind="header", span=EMPTY,
            start=0, end=3, length=_LENGTH, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_slice(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_slice(None, _bind())  # type: ignore[arg-type]


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
