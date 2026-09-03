"""Kernel-pure store class — complementary to run_store / write_fence.

Append-only. Rewrite never admitted. Append after close refused.
Second BUDGET_DEBIT refused. HALT stops RUN_CREATED starts, not
in-flight appends. Ready is not authorized. Not wired into the
run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import (
    BUDGET_DEBIT,
    EXECUTION_RECEIPT,
    RUN_CLOSED,
    RUN_CREATED,
    RUN_REJECTED,
)
from ofn.kernel.store_class import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    StoreDecision,
    admit_store,
    burns_idempotency_key,
    claims_immutable,
    classify_status,
    classify_timeout,
    grants_send,
    halt_blocks_inflight_append,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    rewrites_ledger,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_inflight_append(self):
        self.assertFalse(halt_blocks_inflight_append())

    def test_does_not_rewrite_ledger(self):
        self.assertFalse(rewrites_ledger())

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

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_burn_idempotency_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_store).parameters
        self.assertEqual(
            list(params),
            [
                "intended", "kind", "activity", "closed", "halted",
                "timed_out", "prior_debit",
            ],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="append", kind=RUN_CREATED, timed_out=False,
                grants_send=True)
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="append", kind="send_authorized", timed_out=False,
                grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=True, reason="halt_start", status="VERIFIED",
                intended="append", kind=RUN_CREATED, timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="append", kind=RUN_CREATED, timed_out=False)
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="append", kind=RUN_CREATED, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("rewrite_forbidden", REFUSAL_REASONS)
        self.assertIn("append_after_close", REFUSAL_REASONS)
        self.assertIn("second_debit", REFUSAL_REASONS)
        self.assertIn("halt_start", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_append_requires_verified(self):
        for status in ("SUSPECTED", "UNKNOWN"):
            with self.subTest(status=status):
                with self.assertRaises(FailClosedError):
                    StoreDecision(
                        allowed=True, reason=None, status=status,
                        intended="append", kind=RUN_CREATED, timed_out=False)

    def test_allowed_cannot_be_rewrite(self):
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="rewrite", kind=RUN_CREATED, timed_out=False)

    def test_allowed_decision_refuses_sealed_kind(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    StoreDecision(
                        allowed=True, reason=None, status="VERIFIED",
                        intended="append", kind=name, timed_out=False)

    def test_non_sealed_refusal_cannot_carry_a_sealed_kind(self):
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=False, reason="unknown_activity", status="UNKNOWN",
                intended="append", kind="send_authorized", timed_out=True)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = StoreDecision(
            allowed=False, reason="sealed_effect", status="UNKNOWN",
            intended="append", kind="send_authorized", timed_out=False)
        self.assertEqual(d.kind, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            StoreDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="replay", kind=RUN_CREATED, timed_out="false")  # type: ignore[arg-type]


class ClosedVocabularies(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))

    def test_activities(self):
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))

    def test_intents(self):
        self.assertEqual(
            INTENTS, frozenset({"append", "replay", "reopen", "rewrite"}))


class StatusDerivation(unittest.TestCase):
    def test_idle_is_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False), "VERIFIED")

    def test_concurrent_is_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity_is_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False), "UNKNOWN")

    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True), "UNKNOWN")

    def test_timeout_outranks_idle(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=True), "UNKNOWN")

    def test_unknown_activity_token_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_status(activity="racing", timed_out=False)
        self.assertNotIn("FALSE", str(ctx.exception))


class AppendOnlyAndClose(unittest.TestCase):
    def test_append_idle_verified_is_admitted(self):
        d = admit_store(intended="append", kind=RUN_CREATED)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_rewrite_is_never_admitted(self):
        d = admit_store(intended="rewrite", kind=RUN_CREATED)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "rewrite_forbidden")
        self.assertFalse(rewrites_ledger())
        self.assertFalse(d.grants_send)

    def test_append_after_close_is_refused(self):
        d = admit_store(intended="append", kind=EXECUTION_RECEIPT, closed=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "append_after_close")
        self.assertFalse(d.grants_send)

    def test_second_debit_is_refused(self):
        d = admit_store(
            intended="append", kind=BUDGET_DEBIT, prior_debit=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "second_debit")
        self.assertFalse(d.grants_send)

    def test_first_debit_is_admitted(self):
        d = admit_store(
            intended="append", kind=BUDGET_DEBIT, prior_debit=False)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_append_timeout_is_unknown_not_suspected(self):
        d = admit_store(
            intended="append", kind=EXECUTION_RECEIPT,
            activity="concurrent", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)

    def test_append_concurrent_is_refused(self):
        d = admit_store(
            intended="append", kind=EXECUTION_RECEIPT, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)


class HaltStopsStartsOnly(unittest.TestCase):
    def test_halt_refuses_run_created_append(self):
        d = admit_store(intended="append", kind=RUN_CREATED, halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_start")
        self.assertFalse(d.grants_send)

    def test_halt_does_not_refuse_inflight_receipt(self):
        d = admit_store(
            intended="append", kind=EXECUTION_RECEIPT, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertFalse(halt_blocks_inflight_append())

    def test_halt_does_not_refuse_run_closed(self):
        d = admit_store(intended="append", kind=RUN_CLOSED, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_halt_does_not_refuse_rejected_side_log(self):
        d = admit_store(intended="append", kind=RUN_REJECTED, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)


class ReplayAndReopenAreReadSide(unittest.TestCase):
    def test_replay_is_admitted_even_when_closed(self):
        d = admit_store(intended="replay", kind=RUN_CREATED, closed=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_reopen_is_admitted_under_halt(self):
        d = admit_store(intended="reopen", kind=RUN_CREATED, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_replay_is_byte_identical(self):
        a = admit_store(intended="replay", kind=EXECUTION_RECEIPT)
        b = admit_store(intended="replay", kind=EXECUTION_RECEIPT)
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)
        self.assertFalse(a.grants_send)

    def test_replay_timeout_is_unknown_and_still_admitted(self):
        d = admit_store(
            intended="replay", kind=RUN_CREATED, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)


class UnknownFailsClosed(unittest.TestCase):
    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_store(
                intended="append", kind=RUN_CREATED, activity="racing")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_store(intended="truncate", kind=RUN_CREATED)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_kind_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_store(intended="append", kind="NOT_A_KIND")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_empty_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_store(intended="append", kind="  ")

    def test_bool_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_store(intended="append", kind=True)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_store(intended="append", kind=RUN_CREATED, timed_out=1)
        with self.assertRaises(FailClosedError):
            admit_store(
                intended="append", kind=RUN_CREATED, timed_out="true")

    def test_closed_halted_prior_debit_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_store(intended="append", kind=RUN_CREATED, closed=1)
        with self.assertRaises(FailClosedError):
            admit_store(intended="append", kind=RUN_CREATED, halted="true")
        with self.assertRaises(FailClosedError):
            admit_store(
                intended="append", kind=BUDGET_DEBIT, prior_debit=1)


class SealedNameRefusesStore(unittest.TestCase):
    def test_sealed_kind_aliases(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "SEND_AUTHORIZED",
            "quote-sent",
            "campaign-envelope-ready",
        ):
            with self.subTest(name=name):
                d = admit_store(intended="append", kind=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_and_authorized_stay_distinct_subjects(self):
        ready = admit_store(
            intended="append", kind="campaign_envelope_ready")
        auth = admit_store(intended="append", kind="send_authorized")
        self.assertNotEqual(ready.kind, auth.kind)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
