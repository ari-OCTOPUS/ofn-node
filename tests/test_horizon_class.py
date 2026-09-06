"""Kernel-pure horizon class — complementary to deadline_window / envelope.

Equal is at_edge / UNKNOWN, not closed-as-False. Admit of mint is a
START. Classify is not a START. This module does not mint a run_id
and is not wired into the run store. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.deadline_window import window_open
from ofn.kernel.errors import FailClosedError
from ofn.kernel.horizon_class import (
    ACTIVITIES,
    HORIZON_KINDS,
    INTENTS,
    POSITIONS,
    REFUSAL_REASONS,
    STATUSES,
    HorizonDecision,
    admit_horizon,
    claims_immutable,
    classify_position,
    classify_status,
    classify_timeout,
    copies_deadline_window,
    copies_stale_class,
    copies_ttl_class,
    equal_is_closed,
    grants_send,
    halt_blocks_classify,
    halt_blocks_inflight_admit,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_epoch_is_zero,
    unknown_is_false,
    wires_into_run_store,
)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_halt_does_not_block_inflight_admit(self):
        self.assertFalse(halt_blocks_inflight_admit())

    def test_equal_is_not_closed(self):
        self.assertFalse(equal_is_closed())

    def test_does_not_mint_run_id(self):
        self.assertFalse(mints_run_id())

    def test_does_not_copy_deadline_window(self):
        self.assertFalse(copies_deadline_window())

    def test_does_not_copy_ttl_or_stale(self):
        self.assertFalse(copies_ttl_class())
        self.assertFalse(copies_stale_class())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_epoch_is_not_zero(self):
        self.assertFalse(unknown_epoch_is_zero())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_horizon).parameters
        self.assertEqual(
            list(params),
            [
                "intended", "kind", "now_epoch_s", "horizon_epoch_s",
                "activity", "halted", "timed_out",
            ],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt_raw",
            "immutable",
        ):
            self.assertNotIn(forbidden, params)

    def test_closed_vocabularies(self):
        self.assertEqual(
            HORIZON_KINDS,
            frozenset({
                "mint", "validate", "replay", "store_append", "receipt_bind",
            }),
        )
        self.assertEqual(INTENTS, frozenset({"classify", "admit"}))
        self.assertEqual(
            POSITIONS, frozenset({"inside", "at_edge", "past", "unknown"}))
        self.assertEqual(
            STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertEqual(
            ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertIn("past_horizon", REFUSAL_REASONS)
        self.assertIn("unknown_horizon", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)


class ConstructorGuards(unittest.TestCase):
    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="classify", kind="validate", position="inside",
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=True, reason="past_horizon", status="VERIFIED",
                intended="classify", kind="validate", position="inside",
                timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="admit", kind="mint", position="past",
                timed_out=False)
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="admit", kind="mint", position="past",
                timed_out=False)

    def test_allowed_admit_requires_inside_and_verified(self):
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="admit", kind="mint", position="at_edge",
                timed_out=False)
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=True, reason=None, status="UNKNOWN",
                intended="admit", kind="mint", position="inside",
                timed_out=False)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            HorizonDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="classify", kind="validate", position="inside",
                timed_out=1)  # type: ignore[arg-type]


class PositionRules(unittest.TestCase):
    def test_inside_strictly_before(self):
        self.assertEqual(
            classify_position(
                now_epoch_s=10, horizon_epoch_s=11, timed_out=False),
            "inside")

    def test_at_edge_on_equal(self):
        self.assertEqual(
            classify_position(
                now_epoch_s=10, horizon_epoch_s=10, timed_out=False),
            "at_edge")

    def test_past_strictly_after(self):
        self.assertEqual(
            classify_position(
                now_epoch_s=11, horizon_epoch_s=10, timed_out=False),
            "past")

    def test_missing_now_is_unknown_not_zero(self):
        self.assertEqual(
            classify_position(
                now_epoch_s=None, horizon_epoch_s=10, timed_out=False),
            "unknown")
        self.assertEqual(
            classify_position(
                now_epoch_s=0, horizon_epoch_s=10, timed_out=False),
            "inside")

    def test_missing_horizon_is_unknown(self):
        self.assertEqual(
            classify_position(
                now_epoch_s=10, horizon_epoch_s=None, timed_out=False),
            "unknown")

    def test_timeout_outranks_comparison(self):
        self.assertEqual(
            classify_position(
                now_epoch_s=10, horizon_epoch_s=11, timed_out=True),
            "unknown")
        self.assertEqual(
            classify_position(
                now_epoch_s=10, horizon_epoch_s=10, timed_out=True),
            "unknown")

    def test_equal_is_unknown_not_deadline_closed(self):
        """deadline_window: equal is False. horizon: equal is at_edge."""
        self.assertFalse(window_open(10, 10))
        self.assertEqual(
            classify_position(
                now_epoch_s=10, horizon_epoch_s=10, timed_out=False),
            "at_edge")
        self.assertFalse(equal_is_closed())


class StatusRules(unittest.TestCase):
    def test_idle_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False), "VERIFIED")

    def test_concurrent_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity_unknown(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False), "UNKNOWN")

    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True), "UNKNOWN")


class ClassifyPath(unittest.TestCase):
    def test_classify_inside_is_allowed(self):
        d = admit_horizon(
            intended="classify", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.position, "inside")
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_classify_at_edge_is_allowed_not_a_grant(self):
        d = admit_horizon(
            intended="classify", kind="mint",
            now_epoch_s=10, horizon_epoch_s=10)
        self.assertTrue(d.allowed)
        self.assertEqual(d.position, "at_edge")
        self.assertFalse(d.grants_send)

    def test_classify_past_is_allowed(self):
        d = admit_horizon(
            intended="classify", kind="receipt_bind",
            now_epoch_s=21, horizon_epoch_s=20)
        self.assertTrue(d.allowed)
        self.assertEqual(d.position, "past")

    def test_classify_continues_under_halt(self):
        d = admit_horizon(
            intended="classify", kind="mint",
            now_epoch_s=10, horizon_epoch_s=20, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(halt_blocks_classify())


class AdmitPath(unittest.TestCase):
    def test_admit_inside_idle(self):
        d = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20)
        self.assertTrue(d.allowed)
        self.assertEqual(d.position, "inside")
        self.assertFalse(d.grants_send)

    def test_admit_at_edge_is_unknown_horizon_not_past(self):
        d = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=10, horizon_epoch_s=10)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_horizon")
        self.assertEqual(d.position, "at_edge")
        self.assertNotEqual(d.reason, "past_horizon")

    def test_admit_past_is_past_horizon(self):
        d = admit_horizon(
            intended="admit", kind="replay",
            now_epoch_s=21, horizon_epoch_s=20)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "past_horizon")
        self.assertEqual(d.position, "past")

    def test_admit_missing_now_is_unknown_horizon(self):
        d = admit_horizon(intended="admit", kind="store_append")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_horizon")
        self.assertEqual(d.position, "unknown")

    def test_admit_zero_now_is_a_measurement(self):
        d = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=0, horizon_epoch_s=1)
        self.assertTrue(d.allowed)
        self.assertEqual(d.position, "inside")

    def test_halt_refuses_mint_admit_only(self):
        mint = admit_horizon(
            intended="admit", kind="mint",
            now_epoch_s=10, horizon_epoch_s=20, halted=True)
        self.assertFalse(mint.allowed)
        self.assertEqual(mint.reason, "halt_active")
        validate = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20, halted=True)
        self.assertTrue(validate.allowed)
        self.assertFalse(halt_blocks_inflight_admit())

    def test_timeout_refuses_admit_as_unknown_not_suspected(self):
        d = admit_horizon(
            intended="admit", kind="mint",
            now_epoch_s=10, horizon_epoch_s=20,
            activity="concurrent", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_horizon")
        self.assertEqual(d.position, "unknown")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")

    def test_concurrent_inside_refuses_as_suspected(self):
        d = admit_horizon(
            intended="admit", kind="validate",
            now_epoch_s=10, horizon_epoch_s=20, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertEqual(d.position, "inside")

    def test_unknown_activity_inside_refuses(self):
        d = admit_horizon(
            intended="admit", kind="receipt_bind",
            now_epoch_s=10, horizon_epoch_s=20, activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")


class FailClosedInputs(unittest.TestCase):
    def test_unknown_kind_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_horizon(intended="classify", kind="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_horizon(intended="resend", kind="validate")

    def test_bool_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_horizon(
                intended="classify", kind="validate", now_epoch_s=True)
        with self.assertRaises(FailClosedError):
            admit_horizon(
                intended="classify", kind="validate", horizon_epoch_s=True)

    def test_str_float_epoch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_horizon(
                intended="classify", kind="validate", now_epoch_s="10")
        with self.assertRaises(FailClosedError):
            admit_horizon(
                intended="classify", kind="validate", horizon_epoch_s=10.0)

    def test_halted_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_horizon(
                intended="classify", kind="validate", halted=1)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_horizon(
                intended="classify", kind="validate", timed_out="yes")

    def test_empty_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_horizon(intended="  ", kind="validate")
        with self.assertRaises(FailClosedError):
            admit_horizon(intended="classify", kind="")


class SealedNames(unittest.TestCase):
    def test_sealed_kind_refused(self):
        for name in (
            "send_authorized", "quote_sent", "campaign_envelope_ready",
            "send-authorized",
        ):
            d = admit_horizon(intended="classify", kind=name)
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)

    def test_sealed_intent_refused(self):
        d = admit_horizon(intended="send_authorized", kind="validate")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_ready_and_authorized_are_distinct_sealed(self):
        ready = admit_horizon(
            intended="admit", kind="campaign_envelope_ready")
        auth = admit_horizon(intended="admit", kind="send_authorized")
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.kind, auth.kind)


if __name__ == "__main__":
    unittest.main()
