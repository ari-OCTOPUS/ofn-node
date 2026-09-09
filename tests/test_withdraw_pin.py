"""Kernel-pure withdraw pin — complementary to revoke_class.

First pin records. Same quadruple is already_pinned. Collision
fails closed. peek never writes. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.revoke_class import (
    CLASSIFY,
    HELD,
    READY,
    REVOKE,
    RUN,
    WITHDRAWN,
    bind_revoke,
)
from ofn.kernel.withdraw_pin import (
    ALREADY_PINNED,
    PINNED,
    claims_immutable,
    consumes_nonce,
    grants_send,
    halt_blocks_pin,
    later_disarm_supersedes,
    later_withdraw_supersedes,
    peek_withdraw,
    pin_allows_revoke,
    pin_allows_send,
    pin_withdraw,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    retcon_refused,
    timeout_proves_concurrent_write,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
    withdrawn_is_authorized,
)

_RUN = "run-1780000000-armaaaaaaa"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_withdrawn_is_not_authorized(self):
        self.assertFalse(withdrawn_is_authorized())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent_write())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_consume_nonce(self):
        self.assertFalse(consumes_nonce())

    def test_later_withdraw_and_disarm_supersede(self):
        self.assertTrue(later_withdraw_supersedes())
        self.assertTrue(later_disarm_supersedes())

    def test_pin_signature_has_no_send_knob(self):
        params = inspect.signature(pin_withdraw).parameters
        self.assertEqual(list(params), ["table", "bind"])
        for forbidden in (
            "resend", "send_authorized", "quote_sent", "halt_raw",
        ):
            self.assertNotIn(forbidden, params)


class PinAllows(unittest.TestCase):
    def test_pin_never_allows_send(self):
        bind = bind_revoke(
            REVOKE, READY, withdrawn=False, slot="s")
        self.assertFalse(pin_allows_send(bind))
        issued = bind_revoke(
            "issue", _RUN, withdrawn=False, slot="s2")
        self.assertFalse(pin_allows_send(issued))

    def test_pin_allows_revoke_only_when_held(self):
        held = bind_revoke(
            REVOKE, READY, withdrawn=False, slot="s")
        self.assertTrue(pin_allows_revoke(held))
        done = bind_revoke(
            REVOKE, READY, withdrawn=True, slot="s")
        self.assertFalse(pin_allows_revoke(done))
        classify = bind_revoke(
            CLASSIFY, READY, withdrawn=False, slot="s")
        self.assertFalse(pin_allows_revoke(classify))

    def test_bad_bind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_allows_send("nope")  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            pin_allows_revoke(None)  # type: ignore[arg-type]


class PinAndPeek(unittest.TestCase):
    def test_first_pin_then_already_pinned(self):
        table: dict[str, str] = {}
        bind = bind_revoke(
            REVOKE, READY, withdrawn=False, slot="slot-a")
        self.assertEqual(pin_withdraw(table, bind), PINNED)
        self.assertEqual(pin_withdraw(table, bind), ALREADY_PINNED)
        self.assertEqual(
            peek_withdraw(table, "slot-a"),
            "held:revoke:ready:ready")

    def test_collision_fails_closed(self):
        table: dict[str, str] = {}
        first = bind_revoke(
            REVOKE, READY, withdrawn=False, slot="slot-a")
        other = bind_revoke(
            REVOKE, READY, withdrawn=True, slot="slot-a")
        pin_withdraw(table, first)
        with self.assertRaises(FailClosedError) as ctx:
            pin_withdraw(table, other)
        self.assertIn("withdraw_collision", str(ctx.exception))

    def test_peek_missing_is_unknown_not_false(self):
        self.assertIsNone(peek_withdraw({}, "slot-a"))
        self.assertIsNone(peek_withdraw({}, None))
        self.assertIsNot(peek_withdraw({}, "slot-a"), False)

    def test_peek_never_writes(self):
        table: dict[str, str] = {}
        self.assertIsNone(peek_withdraw(table, "slot-a"))
        self.assertEqual(table, {})

    def test_send_slot_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_withdraw({}, "send_authorized")
        with self.assertRaises(FailClosedError):
            peek_withdraw({}, "quote_sent")

    def test_empty_slot_and_bad_table(self):
        with self.assertRaises(FailClosedError):
            peek_withdraw({}, "  ")
        with self.assertRaises(FailClosedError):
            peek_withdraw(None, "s")  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            pin_withdraw(None, bind_revoke(  # type: ignore[arg-type]
                REVOKE, READY, withdrawn=False, slot="s"))

    def test_drifted_encoding_fails_closed(self):
        with self.assertRaises(FailClosedError):
            peek_withdraw({"s": "nope"}, "s")
        with self.assertRaises(FailClosedError):
            peek_withdraw({"s": "held:revoke:ready:"}, "s")
        with self.assertRaises(FailClosedError):
            peek_withdraw({"s": "weird:revoke:ready:ready"}, "s")

    def test_run_subject_round_trip(self):
        table: dict[str, str] = {}
        bind = bind_revoke(
            CLASSIFY, _RUN, withdrawn=True, slot="slot-r")
        self.assertEqual(pin_withdraw(table, bind), PINNED)
        self.assertEqual(
            peek_withdraw(table, "slot-r"),
            f"withdrawn:classify:run:{_RUN}")


class RetconAndTryPin(unittest.TestCase):
    def test_retcon_missing_is_unknown(self):
        bind = bind_revoke(
            REVOKE, READY, withdrawn=False, slot="s")
        self.assertIsNone(retcon_refused({}, bind))

    def test_retcon_match_is_false_disagree_is_true(self):
        table: dict[str, str] = {}
        bind = bind_revoke(
            REVOKE, READY, withdrawn=False, slot="s")
        pin_withdraw(table, bind)
        self.assertIs(retcon_refused(table, bind), False)
        other = bind_revoke(
            REVOKE, READY, withdrawn=True, slot="s")
        self.assertIs(retcon_refused(table, other), True)

    def test_try_pin_timeout_is_unknown_and_does_not_write(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(
            table, REVOKE, READY, withdrawn=False, slot="s",
            timeout=True))
        self.assertEqual(table, {})

    def test_try_pin_missing_is_unknown(self):
        table: dict[str, str] = {}
        self.assertIsNone(try_pin(
            table, None, READY, withdrawn=False, slot="s"))
        self.assertIsNone(try_pin(
            table, REVOKE, None, withdrawn=False, slot="s"))
        self.assertIsNone(try_pin(
            table, REVOKE, READY, withdrawn=None, slot="s"))
        self.assertIsNone(try_pin(
            table, REVOKE, READY, withdrawn=False, slot=None))
        self.assertEqual(table, {})

    def test_try_pin_writes_once(self):
        table: dict[str, str] = {}
        self.assertEqual(
            try_pin(table, REVOKE, READY, withdrawn=False, slot="s"),
            PINNED)
        self.assertEqual(
            try_pin(table, REVOKE, READY, withdrawn=False, slot="s"),
            ALREADY_PINNED)

    def test_try_pin_bad_timeout_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_pin(
                {}, REVOKE, READY, withdrawn=False, slot="s",
                timeout="yes")

    def test_try_pin_send_subject_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_pin(
                {}, REVOKE, "send_authorized", withdrawn=False,
                slot="s")


if __name__ == "__main__":
    unittest.main()
