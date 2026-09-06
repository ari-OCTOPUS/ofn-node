"""Contract tests for seat_pin (P1 complementary).

A pinned quorum/short is not a send. Same pair is
already_pinned. A different family on the same seat fails closed.
peek never writes. Missing is UNKNOWN, not FALSE.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.quorum_class import (
    QUORUM,
    SHORT,
    QuorumBind,
    bind_quorum,
)
from ofn.kernel.seat_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    peek_seat,
    pin_allows_record,
    pin_allows_send,
    pin_seat,
    promotes_ready_to_send,
    proposal_is_execution,
    quorum_is_authorized,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

_SEAT = "env-qrm-0001"


def _bind(present: int, required: int = 3, *, intent: str = "classify") -> QuorumBind:
    return bind_quorum(intent, present, required, seat=_SEAT)


class PinSeats(unittest.TestCase):
    def test_first_pin(self):
        table: dict[str, str] = {}
        self.assertEqual(pin_seat(table, _bind(3)), PINNED)
        self.assertEqual(peek_seat(table, _SEAT), "quorum:3:3")

    def test_same_pair_is_already_pinned(self):
        table: dict[str, str] = {}
        pin_seat(table, _bind(3))
        self.assertEqual(pin_seat(table, _bind(3)), ALREADY_PINNED)

    def test_different_present_fails_closed(self):
        table: dict[str, str] = {}
        pin_seat(table, _bind(3))
        with self.assertRaises(FailClosedError) as ctx:
            pin_seat(table, _bind(2))
        self.assertIn("quorum_collision", str(ctx.exception))

    def test_short_pins_and_is_not_a_send(self):
        table: dict[str, str] = {}
        bind = _bind(1)
        self.assertEqual(bind.family, SHORT)
        self.assertEqual(pin_seat(table, bind), PINNED)
        self.assertEqual(peek_seat(table, _SEAT), "short:1:3")
        self.assertFalse(pin_allows_send(bind))
        self.assertFalse(pin_allows_record(bind))

    def test_quorum_record_allows_record_not_send(self):
        bind = _bind(3, intent="record")
        self.assertEqual(bind.family, QUORUM)
        self.assertTrue(pin_allows_record(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_short_record_allows_record_not_send(self):
        bind = _bind(1, intent="record")
        self.assertEqual(bind.family, SHORT)
        self.assertTrue(pin_allows_record(bind))
        self.assertFalse(pin_allows_send(bind))

    def test_classify_quorum_does_not_allow_record(self):
        bind = _bind(4, intent="classify")
        self.assertEqual(bind.family, QUORUM)
        self.assertFalse(pin_allows_record(bind))
        self.assertFalse(grants_send())

    def test_peek_missing_is_none_not_false(self):
        self.assertIsNone(peek_seat({}, _SEAT))
        self.assertIsNone(peek_seat({}, None))
        self.assertIsNot(peek_seat({}, _SEAT), False)

    def test_peek_sealed_seat_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_seat({}, "send_authorized")

    def test_try_pin_missing_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(table, None, 3, 3, seat=_SEAT))
        self.assertIsNone(try_pin(table, "classify", None, 3, seat=_SEAT))
        self.assertIsNone(try_pin(table, "classify", 3, None, seat=_SEAT))
        self.assertEqual(table, {})

    def test_try_pin_timeout_is_none(self):
        table: dict[str, str] = {}
        self.assertIsNone(
            try_pin(table, "classify", 3, 3, seat=_SEAT, timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_writes_on_present(self):
        table: dict[str, str] = {}
        self.assertEqual(try_pin(table, "classify", 3, 3, seat=_SEAT), PINNED)

    def test_retcon_missing_is_none(self):
        bind = _bind(3)
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false(self):
        table: dict[str, str] = {}
        bind = _bind(3)
        pin_seat(table, bind)
        self.assertIs(retcon_refused(table, bind), False)

    def test_retcon_disagreement_is_true(self):
        table: dict[str, str] = {}
        pin_seat(table, _bind(3))
        other = bind_quorum("classify", 1, 3, seat=_SEAT)
        self.assertIs(retcon_refused(table, other), True)

    def test_hand_built_drift_fails_closed(self):
        table: dict[str, str] = {}
        drifted = QuorumBind(
            intent="classify",
            family=QUORUM,
            present=1,
            required=3,
            seat=_SEAT,
        )
        with self.assertRaises(FailClosedError):
            pin_seat(table, drifted)

    def test_table_missing_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_seat(None, _bind(3))  # type: ignore[arg-type]


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
        self.assertFalse(quorum_is_authorized())
        self.assertTrue(later_disarm_supersedes())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


if __name__ == "__main__":
    unittest.main()
