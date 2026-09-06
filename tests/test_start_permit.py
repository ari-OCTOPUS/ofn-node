"""Kernel-pure start permit — complementary to #88 halt vocab and #93 refusal log.

A start is decided before a run_id exists. HALT refuses STARTS. A sealed
send/ready name refuses STARTS even when the switch is off. Clearing HALT
is not send_authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import RUN_CREATED, RUN_REJECTED
from ofn.kernel.start_permit import (
    REFUSAL_REASONS,
    StartDecision,
    burns_idempotency_key,
    decide_start,
    grants_send,
    halt_blocks_in_flight,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_in_flight(self):
        self.assertFalse(halt_blocks_in_flight())

    def test_refused_start_does_not_burn_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(decide_start).parameters
        self.assertEqual(list(params),
                         ["halt_raw", "proposed_kind", "proposed_tool"])
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            StartDecision(allowed=True, reason=None, grants_send=True)
        with self.assertRaises(FailClosedError):
            StartDecision(allowed=False, reason="halt_active",
                          grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            StartDecision(allowed=True, reason="halt_active")

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            StartDecision(allowed=False, reason=None)
        with self.assertRaises(FailClosedError):
            StartDecision(allowed=False, reason="send_authorized")
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)


class AbsentIsAStart(unittest.TestCase):
    def test_none_allows_start(self):
        d = decide_start(halt_raw=None)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertIsNone(d.refusal_kind)

    def test_known_off_words_allow_start(self):
        for raw in ("0", "false", "no", "off", "0\n", " FALSE "):
            with self.subTest(raw=raw):
                d = decide_start(halt_raw=raw, proposed_kind=RUN_CREATED)
                self.assertTrue(d.allowed)
                self.assertFalse(d.grants_send)


class HaltRefusesStart(unittest.TestCase):
    def test_canonical_on_words(self):
        for raw in ("1", "true", "yes", "on", "1\n", " TRUE "):
            with self.subTest(raw=raw):
                d = decide_start(halt_raw=raw)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "halt_active")
                self.assertEqual(d.refusal_kind, RUN_REJECTED)
                self.assertFalse(d.grants_send)

    def test_empty_and_foreign_vocabulary_fail_closed(self):
        for raw in ("", "   \n", "garbage", "2", "maybe", "{}", "halt"):
            with self.subTest(raw=raw):
                d = decide_start(halt_raw=raw)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "halt_active")

    def test_halt_wins_over_a_sealed_name(self):
        d = decide_start(halt_raw="1", proposed_kind="send_authorized")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_active")


class SealedNameRefusesStart(unittest.TestCase):
    def test_sealed_kind_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "SEND_AUTHORIZED",
                     "quote-sent"):
            with self.subTest(name=name):
                d = decide_start(halt_raw=None, proposed_kind=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertEqual(d.refusal_kind, RUN_REJECTED)
                self.assertFalse(d.grants_send)

    def test_sealed_tool_aliases(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                d = decide_start(halt_raw="0", proposed_tool=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")

    def test_ready_is_not_authorized(self):
        ready = decide_start(halt_raw=None,
                             proposed_kind="campaign_envelope_ready")
        auth = decide_start(halt_raw=None, proposed_kind="send_authorized")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertFalse(ready.grants_send)
        self.assertFalse(auth.grants_send)
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class KindGate(unittest.TestCase):
    def test_run_created_is_the_start_kind(self):
        d = decide_start(halt_raw=None, proposed_kind=RUN_CREATED)
        self.assertTrue(d.allowed)

    def test_run_rejected_is_not_a_start(self):
        with self.assertRaises(FailClosedError) as ctx:
            decide_start(halt_raw=None, proposed_kind=RUN_REJECTED)
        self.assertIn("refusal witness", str(ctx.exception))

    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            decide_start(halt_raw=None, proposed_kind="NOT_A_KIND")
        self.assertIn("unknown event kind", str(ctx.exception))

    def test_non_start_spine_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            decide_start(halt_raw=None, proposed_kind="TOOL_INVOKED")

    def test_empty_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            decide_start(halt_raw=None, proposed_kind="")
        with self.assertRaises(FailClosedError):
            decide_start(halt_raw=None, proposed_kind="   ")

    def test_empty_tool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            decide_start(halt_raw=None, proposed_tool="")


class ResumeIsNotASend(unittest.TestCase):
    def test_clearing_halt_allows_start_and_still_not_send(self):
        halted = decide_start(halt_raw="1")
        self.assertFalse(halted.allowed)
        resumed = decide_start(halt_raw=None, proposed_kind=RUN_CREATED)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())


if __name__ == "__main__":
    unittest.main()
