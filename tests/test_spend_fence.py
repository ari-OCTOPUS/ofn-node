"""Kernel-pure spend fence — a token FIT is not a send.

Observe is admitted. promote_send and quote are never
admitted, including on FIT. Timeout is UNKNOWN, not a
concurrent-write proof. Ready is not authorized.
Distinct from send_fence (campaign-ready wall),
token_ceiling, budget_class, and token_class.
Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.spend_fence import (
    INTENTS,
    REFUSAL_REASONS,
    SpendDecision,
    admit_spend,
    claims_immutable,
    classify_timeout,
    fit_is_send,
    grants_send,
    halt_blocks_fence,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
)
from ofn.kernel.token_class import VERDICTS


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_fence(self):
        self.assertFalse(halt_blocks_fence())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_fit_is_not_a_send(self):
        self.assertFalse(fit_is_send())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_spend).parameters
        self.assertEqual(
            list(params),
            ["intended", "activity", "verdict", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "winner",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            SpendDecision(
                allowed=True, reason=None, verdict="FIT",
                status="VERIFIED", intended="observe", timed_out=False,
                grants_send=True)
        with self.assertRaises(FailClosedError):
            SpendDecision(
                allowed=False, reason="promote_send_forbidden",
                verdict="FIT", status="VERIFIED", intended="promote_send",
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            SpendDecision(
                allowed=True, reason="promote_send_forbidden",
                verdict="FIT", status="VERIFIED", intended="observe",
                timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            SpendDecision(
                allowed=False, reason=None, verdict="FIT",
                status="VERIFIED", intended="observe", timed_out=False)
        self.assertIn("promote_send_forbidden", REFUSAL_REASONS)
        self.assertIn("quote_forbidden", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)

    def test_vocabularies_are_closed(self):
        self.assertEqual(
            INTENTS, frozenset({"observe", "promote_send", "quote"}))


class ObserveAdmitted(unittest.TestCase):
    def test_observe_fit_is_not_a_send(self):
        d = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.verdict, "FIT")
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)
        self.assertFalse(fit_is_send())

    def test_observe_every_known_verdict(self):
        for name in VERDICTS:
            d = admit_spend(
                intended="observe", activity="idle", verdict=name)
            self.assertEqual(d.verdict, name)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_dual_record_allowed_and_grants_send(self):
        d = admit_spend(
            intended="observe", activity="idle", verdict="MISS")
        self.assertTrue(hasattr(d, "allowed"))
        self.assertTrue(hasattr(d, "grants_send"))
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class PromoteAndQuoteRefused(unittest.TestCase):
    def test_promote_send_refused_even_on_fit(self):
        d = admit_spend(
            intended="promote_send", activity="idle", verdict="FIT")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "promote_send_forbidden")
        self.assertEqual(d.verdict, "FIT")
        self.assertFalse(d.grants_send)

    def test_quote_refused_even_on_fit(self):
        d = admit_spend(
            intended="quote", activity="idle", verdict="FIT")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "quote_forbidden")
        self.assertFalse(d.grants_send)

    def test_constructor_cannot_allow_promote_or_quote(self):
        with self.assertRaises(FailClosedError):
            SpendDecision(
                allowed=True, reason=None, verdict="FIT",
                status="VERIFIED", intended="promote_send",
                timed_out=False)
        with self.assertRaises(FailClosedError):
            SpendDecision(
                allowed=True, reason=None, verdict="FIT",
                status="VERIFIED", intended="quote", timed_out=False)


class TimeoutAndActivity(unittest.TestCase):
    def test_timeout_is_unknown_not_suspected(self):
        d = admit_spend(
            intended="observe", activity="concurrent", verdict="FIT",
            timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertTrue(d.timed_out)
        self.assertEqual(classify_timeout(), "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(d.grants_send)

    def test_unknown_activity_is_unknown(self):
        d = admit_spend(
            intended="observe", activity="unknown", verdict="SPLIT")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")

    def test_concurrent_is_suspected(self):
        d = admit_spend(
            intended="observe", activity="concurrent", verdict="FIT")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "SUSPECTED")
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_spend(
                intended="observe", activity="idle", verdict="FIT",
                timed_out=None)
        with self.assertRaises(FailClosedError):
            admit_spend(
                intended="observe", activity="idle", verdict="FIT",
                timed_out=1)

    def test_unknown_verdict_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_spend(
                intended="observe", activity="idle", verdict="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())


class SealedNames(unittest.TestCase):
    def test_sealed_intent_fails_closed(self):
        for sealed in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
        ):
            with self.assertRaises(FailClosedError) as ctx:
                admit_spend(
                    intended=sealed, activity="idle", verdict="FIT")
            self.assertIn("sealed", str(ctx.exception).lower())

    def test_sealed_verdict_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_spend(
                intended="observe", activity="idle",
                verdict="send_authorized")
        self.assertIn("sealed", str(ctx.exception).lower())

    def test_ready_is_not_authorized_as_a_fence(self):
        with self.assertRaises(FailClosedError):
            admit_spend(
                intended="campaign_envelope_ready", activity="idle",
                verdict="FIT")
        with self.assertRaises(FailClosedError):
            admit_spend(
                intended="send_authorized", activity="idle",
                verdict="FIT")
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
