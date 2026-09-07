"""Kernel-pure dual-ceiling token claim — complementary to token_ceiling.

Both per_run and node must be recorded as exact bools. Missing
is not a fit. Disagreement is SPLIT, not a silent pick.
Timeout is UNKNOWN, not a concurrent-spend proof.
Ready is not authorized. Distinct from token_ceiling,
budget_class, callbudget, quota, and spend_fence.
Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.token_class import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    VERDICTS,
    TokenClaim,
    claims_immutable,
    classify_status,
    classify_timeout,
    classify_token,
    classify_verdict,
    grants_send,
    halt_blocks_token,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    silently_picks_split,
    timeout_proves_concurrent,
    unknown_is_false,
    unknown_is_fit,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_token(self):
        self.assertFalse(halt_blocks_token())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_is_not_a_fit(self):
        self.assertFalse(unknown_is_fit())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        self.assertNotEqual(classify_timeout(), "FALSE")

    def test_does_not_silently_pick_split(self):
        self.assertFalse(silently_picks_split())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(classify_token).parameters
        self.assertEqual(
            list(params),
            ["per_run", "node", "intended", "activity", "timed_out"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "winner",
            "pick",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=True, reason=None, per_run=True, node=True,
                verdict="FIT", status="VERIFIED", intended="classify",
                timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=False, reason="grant_send_forbidden",
                per_run=True, node=True, verdict="FIT",
                status="VERIFIED", intended="grant_send",
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=True, reason="unknown_activity",
                per_run=True, node=True, verdict="FIT",
                status="VERIFIED", intended="classify", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=False, reason=None, per_run=True, node=True,
                verdict="FIT", status="VERIFIED", intended="classify",
                timed_out=False)
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=False, reason="send_authorized",
                per_run=True, node=True, verdict="FIT",
                status="VERIFIED", intended="classify", timed_out=False)
        self.assertIn("grant_send_forbidden", REFUSAL_REASONS)
        self.assertIn("sealed_effect", REFUSAL_REASONS)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=True, node=True, intended="classify",
                activity="idle", timed_out=None)
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=True, node=True, intended="classify",
                activity="idle", timed_out=1)

    def test_vocabularies_are_closed(self):
        self.assertEqual(INTENTS, frozenset({"classify", "grant_send"}))
        self.assertEqual(VERDICTS, frozenset({"FIT", "MISS", "SPLIT"}))
        self.assertEqual(
            STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertEqual(
            ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))


class DualWitness(unittest.TestCase):
    def test_both_true_is_fit_and_not_a_send(self):
        claim = classify_token(
            per_run=True, node=True, intended="classify", activity="idle")
        self.assertTrue(claim.allowed)
        self.assertIsNone(claim.reason)
        self.assertTrue(claim.per_run)
        self.assertTrue(claim.node)
        self.assertEqual(claim.verdict, "FIT")
        self.assertEqual(claim.status, "VERIFIED")
        self.assertFalse(claim.grants_send)

    def test_both_false_is_miss_and_not_a_send(self):
        claim = classify_token(
            per_run=False, node=False, intended="classify", activity="idle")
        self.assertTrue(claim.allowed)
        self.assertEqual(claim.verdict, "MISS")
        self.assertFalse(claim.grants_send)

    def test_disagreement_is_split_not_a_silent_pick(self):
        a = classify_token(
            per_run=True, node=False, intended="classify", activity="idle")
        b = classify_token(
            per_run=False, node=True, intended="classify", activity="idle")
        self.assertEqual(a.verdict, "SPLIT")
        self.assertEqual(b.verdict, "SPLIT")
        self.assertTrue(a.per_run)
        self.assertFalse(a.node)
        self.assertFalse(b.per_run)
        self.assertTrue(b.node)
        self.assertNotEqual(a.per_run, a.node)
        self.assertFalse(silently_picks_split())
        self.assertFalse(a.grants_send)
        self.assertFalse(b.grants_send)

    def test_verdict_helper_matches_recorded_pair(self):
        self.assertEqual(classify_verdict(per_run=True, node=True), "FIT")
        self.assertEqual(classify_verdict(per_run=False, node=False), "MISS")
        self.assertEqual(classify_verdict(per_run=True, node=False), "SPLIT")
        self.assertEqual(classify_verdict(per_run=False, node=True), "SPLIT")

    def test_constructor_refuses_mismatched_verdict(self):
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=True, reason=None, per_run=True, node=False,
                verdict="FIT", status="VERIFIED", intended="classify",
                timed_out=False)

    def test_dual_record_per_run_and_node_and_grants_send(self):
        claim = classify_token(
            per_run=True, node=True, intended="classify", activity="idle")
        self.assertTrue(hasattr(claim, "per_run"))
        self.assertTrue(hasattr(claim, "node"))
        self.assertTrue(hasattr(claim, "grants_send"))
        self.assertFalse(claim.grants_send)


class MissingIsNotAFit(unittest.TestCase):
    def test_missing_per_run_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_token(
                per_run=None, node=True, intended="classify",
                activity="idle")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("not a fit", str(ctx.exception).lower())

    def test_missing_node_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_token(
                per_run=True, node=None, intended="classify",
                activity="idle")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_bool_subclasses_rejected(self):
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=1, node=True, intended="classify", activity="idle")
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=True, node=0, intended="classify", activity="idle")
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run="true", node=True, intended="classify",
                activity="idle")


class GrantSendRefused(unittest.TestCase):
    def test_grant_send_refused_even_on_fit(self):
        claim = classify_token(
            per_run=True, node=True, intended="grant_send",
            activity="idle")
        self.assertFalse(claim.allowed)
        self.assertEqual(claim.reason, "grant_send_forbidden")
        self.assertEqual(claim.verdict, "FIT")
        self.assertFalse(claim.grants_send)

    def test_constructor_cannot_allow_grant_send(self):
        with self.assertRaises(FailClosedError):
            TokenClaim(
                allowed=True, reason=None, per_run=True, node=True,
                verdict="FIT", status="VERIFIED", intended="grant_send",
                timed_out=False)


class TimeoutAndActivity(unittest.TestCase):
    def test_timeout_is_unknown_not_suspected(self):
        claim = classify_token(
            per_run=True, node=True, intended="classify",
            activity="concurrent", timed_out=True)
        self.assertFalse(claim.allowed)
        self.assertEqual(claim.status, "UNKNOWN")
        self.assertEqual(claim.reason, "unknown_activity")
        self.assertTrue(claim.timed_out)
        self.assertEqual(classify_timeout(), "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(claim.verdict, "FIT")
        self.assertFalse(claim.grants_send)

    def test_unknown_activity_is_unknown(self):
        claim = classify_token(
            per_run=False, node=True, intended="classify",
            activity="unknown")
        self.assertFalse(claim.allowed)
        self.assertEqual(claim.status, "UNKNOWN")
        self.assertEqual(claim.verdict, "SPLIT")
        self.assertEqual(classify_status(activity="unknown", timed_out=False),
                         "UNKNOWN")

    def test_concurrent_is_suspected_not_a_send(self):
        claim = classify_token(
            per_run=True, node=True, intended="classify",
            activity="concurrent")
        self.assertFalse(claim.allowed)
        self.assertEqual(claim.status, "SUSPECTED")
        self.assertEqual(claim.reason, "suspected_concurrent")
        self.assertFalse(claim.grants_send)

    def test_unknown_activity_name_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_token(
                per_run=True, node=True, intended="classify",
                activity="DEAD_SOURCE")
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
                classify_token(
                    per_run=True, node=True, intended=sealed,
                    activity="idle")
            self.assertIn("sealed", str(ctx.exception).lower())

    def test_ready_is_not_authorized_as_a_claim(self):
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=True, node=True,
                intended="campaign_envelope_ready", activity="idle")
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=True, node=True,
                intended="send_authorized", activity="idle")
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
