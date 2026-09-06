"""Contract tests for budget_class (P1 complementary).

Observe/debit is admitted only when VERIFIED and the request
fits. Credit and grant_send are refused. Zero ceiling
authorizes only a zero request. Timeout is UNKNOWN, not a
concurrent-spend proof. Ready ≠ authorized. Distinct from
token_ceiling.py and run_store.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.budget_class import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    SURFACES,
    BudgetDecision,
    admit_budget,
    claims_immutable,
    classify_status,
    classify_timeout,
    grants_send,
    halt_blocks_budget,
    mints_credit,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    request_fits,
    timeout_proves_concurrent,
    unknown_is_false,
    unknown_tokens_are_zero,
)
from ofn.kernel.errors import FailClosedError


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_budget(self):
        self.assertFalse(halt_blocks_budget())

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
        self.assertNotEqual(classify_timeout(), "FALSE")

    def test_unknown_tokens_are_not_zero(self):
        self.assertFalse(unknown_tokens_are_zero())

    def test_does_not_mint_credit(self):
        self.assertFalse(mints_credit())

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(admit_budget).parameters
        self.assertEqual(
            list(params),
            [
                "intended",
                "activity",
                "surface",
                "ceiling",
                "already",
                "request",
                "timed_out",
            ],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "halt",
            "halted",
            "quote_sent",
        ):
            self.assertNotIn(forbidden, params)

    def test_vocabularies_are_closed(self):
        self.assertEqual(
            INTENTS,
            frozenset({"observe", "debit", "credit", "grant_send"}),
        )
        self.assertEqual(SURFACES, frozenset({"run_budget", "node_quota"}))
        self.assertIn("idle", ACTIVITIES)
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertIn("ceiling_exhausted", REFUSAL_REASONS)
        self.assertIn("grant_send_forbidden", REFUSAL_REASONS)


class AdmitObserveDebit(unittest.TestCase):
    def test_observe_when_verified(self):
        d = admit_budget(intended="observe", activity="idle")
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_debit_zero_on_zero_ceiling(self):
        d = admit_budget(
            intended="debit",
            activity="idle",
            ceiling=0,
            already=0,
            request=0,
        )
        self.assertTrue(d.allowed)
        self.assertTrue(request_fits(ceiling=0, already=0, request=0))

    def test_debit_within_remaining(self):
        d = admit_budget(
            intended="debit",
            activity="idle",
            surface="run_budget",
            ceiling=10,
            already=3,
            request=7,
        )
        self.assertTrue(d.allowed)
        self.assertEqual(d.surface, "run_budget")

    def test_observe_each_surface_when_verified(self):
        for surface in SURFACES:
            with self.subTest(surface=surface):
                d = admit_budget(
                    intended="observe", activity="idle", surface=surface)
                self.assertTrue(d.allowed)
                self.assertEqual(d.surface, surface)


class RefuseUnsafe(unittest.TestCase):
    def test_credit_refused(self):
        d = admit_budget(intended="credit", activity="idle", request=1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "credit_forbidden")
        self.assertFalse(d.grants_send)

    def test_grant_send_refused(self):
        d = admit_budget(intended="grant_send", activity="idle")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "grant_send_forbidden")

    def test_zero_ceiling_nonzero_request_exhausted(self):
        d = admit_budget(
            intended="debit",
            activity="idle",
            ceiling=0,
            already=0,
            request=1,
        )
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "ceiling_exhausted")
        self.assertFalse(request_fits(ceiling=0, already=0, request=1))

    def test_over_remaining_exhausted(self):
        d = admit_budget(
            intended="debit",
            activity="idle",
            ceiling=10,
            already=8,
            request=3,
        )
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "ceiling_exhausted")


class TimeoutAndUnknown(unittest.TestCase):
    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True),
            "UNKNOWN",
        )
        d = admit_budget(
            intended="debit",
            activity="concurrent",
            ceiling=10,
            request=1,
            timed_out=True,
        )
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")

    def test_unknown_activity_is_unknown_not_false(self):
        d = admit_budget(intended="observe", activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.status, "FALSE")

    def test_suspected_concurrent_blocks_debit(self):
        d = admit_budget(
            intended="debit", activity="concurrent", ceiling=10, request=1)
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, "SUSPECTED")
        self.assertEqual(d.reason, "suspected_concurrent")

    def test_credit_still_refused_when_unknown(self):
        d = admit_budget(intended="credit", activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "credit_forbidden")

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_budget(
                intended="observe", activity="idle", timed_out=1)

    def test_bool_tokens_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_budget(
                intended="debit", activity="idle", ceiling=True, request=0)

    def test_negative_tokens_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_budget(
                intended="debit", activity="idle", ceiling=10, request=-1)

    def test_none_tokens_fail_closed(self):
        with self.assertRaises(FailClosedError):
            admit_budget(
                intended="debit", activity="idle", ceiling=None, request=0)

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_budget(intended="refund", activity="idle")

    def test_unknown_surface_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_budget(
                intended="observe", activity="idle", surface="wire")


class SealedNames(unittest.TestCase):
    def test_sealed_intent_fails_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "Send_Authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    admit_budget(intended=name, activity="idle")

    def test_sealed_surface_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_budget(
                intended="observe",
                activity="idle",
                surface="campaign_envelope_ready",
            )

    def test_decision_cannot_grant_send(self):
        with self.assertRaises(FailClosedError):
            BudgetDecision(
                allowed=True,
                reason=None,
                status="VERIFIED",
                intended="observe",
                surface="run_budget",
                timed_out=False,
                grants_send=True,
            )


class DistinctFromCeiling(unittest.TestCase):
    def test_module_is_not_token_ceiling(self):
        import ofn.kernel.budget_class as budget
        import ofn.kernel.token_ceiling as ceiling
        self.assertFalse(hasattr(ceiling, "admit_budget"))
        self.assertIsNot(budget.admit_budget, getattr(ceiling, "check", None))

    def test_run_store_does_not_import_budget_class(self):
        import ofn.adapters.run_store as run_store
        source = inspect.getsource(run_store)
        self.assertNotIn("budget_class", source)
        self.assertNotIn("admit_budget", source)
