"""Contract tests for extract_pin (P1 complementary).

A pinned extract is not a send. Same quadruple is already_pinned.
A different extract on the same slot fails closed. peek never
writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.carve_class import (
    FITS,
    OVERHANG,
    PAST,
    CarveBind,
    bind_carve,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.extract_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    extracted_is_zero,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_extract,
    pin_allows_carve,
    pin_allows_send,
    pin_extract,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SLOT = "env-crv-0001"
_HOST = 10


def _bind(
    cut_at: int,
    guest_len: int,
    *,
    intent: str = "classify",
    host_len: int = _HOST,
) -> CarveBind:
    return bind_carve(
        intent, host_len, cut_at=cut_at, guest_len=guest_len, slot=_SLOT)


class PinExtracts(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_extract(table, _bind(8, 3)), PINNED)
        self.assertEqual(peek_extract(table, _SLOT), "8:3:10:overhang")

    def test_same_quadruple_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_extract(table, _bind(8, 3))
        self.assertEqual(pin_extract(table, _bind(8, 3)), ALREADY_PINNED)

    def test_different_extract_fails_closed(self):
        table: dict[str, str] = {}
        pin_extract(table, _bind(8, 3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_extract(table, _bind(0, 2))
        self.assertIn("extract_collision", str(ctx.exception))

    def test_overhang_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(8, 3)
        self.assertEqual(bind.family, OVERHANG)
        self.assertEqual(pin_extract(table, bind), PINNED)
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_carve(bind))

    def test_fits_carve_allows_carve_not_send(self):
        bind = _bind(0, 2, intent="carve")
        self.assertEqual(bind.family, FITS)
        self.assertTrue(pin_allows_carve(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_past_carve_does_not_allow_carve(self):
        bind = _bind(11, 0, intent="carve")
        self.assertEqual(bind.family, PAST)
        self.assertFalse(pin_allows_carve(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_extract({}, _SLOT))
        self.assertIsNone(peek_extract({}, None))
        self.assertIsNot(peek_extract({}, _SLOT), False)

    def test_peek_sealed_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_extract({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, None, _HOST, cut_at=0, guest_len=2, slot=_SLOT))
        self.assertIsNone(
            try_pin(
                table, "classify", None, cut_at=0, guest_len=2, slot=_SLOT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(
                table, "classify", _HOST, cut_at=0, guest_len=2,
                slot=_SLOT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(
                table, "classify", _HOST, cut_at=0, guest_len=2, slot=_SLOT),
            PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(0, 2)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(0, 2)
        pin_extract(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_extract(table, _bind(0, 2))
        other = bind_carve(
            "classify", _HOST, cut_at=8, guest_len=3, slot=_SLOT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = CarveBind(
            intent="classify", family=FITS, cut_at=8, guest_len=3,
            host_len=_HOST, extracted=3, slot=_SLOT)
        with self.assertRaises(FailClosedError):
            pin_extract(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_extract(None, _bind(0, 2))  # type: ignore[arg-type]


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
        self.assertFalse(extracted_is_zero())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
