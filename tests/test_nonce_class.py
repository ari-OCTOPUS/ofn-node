"""Kernel-pure nonce class — complementary to event_id / dedup / idempotency.

A proposed admit is a START. replay_check is not a START.
This module does not consume the token and is not wired into the
run store. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.nonce_class import (
    ACTIVITIES,
    INTENTS,
    NONCE_RE,
    REFUSAL_REASONS,
    STATUSES,
    NonceDecision,
    admit_nonce,
    claims_immutable,
    classify_status,
    classify_timeout,
    consumes_nonce,
    grants_send,
    halt_blocks_replay_check,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    require_nonce,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)

_RUN = "run-1780000000-abcdefghij"
_NCE = "nce-0123456789abcdef"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_replay_check(self):
        self.assertFalse(halt_blocks_replay_check())

    def test_does_not_consume_nonce(self):
        self.assertFalse(consumes_nonce())

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

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_signature_has_no_send_or_resend_knob(self):
        params = inspect.signature(admit_nonce).parameters
        self.assertEqual(
            list(params),
            ["intended", "nonce", "run_id", "activity", "halted", "timed_out"],
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
            NonceDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="replay_check", nonce=_NCE, run_id=_RUN,
                timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            NonceDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="replay_check", nonce="send_authorized",
                run_id=_RUN, timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            NonceDecision(
                allowed=True, reason="halt_active", status="VERIFIED",
                intended="admit", nonce=_NCE, run_id=_RUN, timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            NonceDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="admit", nonce=_NCE, run_id=_RUN, timed_out=False)
        with self.assertRaises(FailClosedError):
            NonceDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="admit", nonce=_NCE, run_id=_RUN, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertIn("malformed_nonce", REFUSAL_REASONS)
        self.assertIn("malformed_id", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_admit_requires_verified(self):
        with self.assertRaises(FailClosedError):
            NonceDecision(
                allowed=True, reason=None, status="UNKNOWN",
                intended="admit", nonce=_NCE, run_id=_RUN, timed_out=True)

    def test_closed_vocabularies(self):
        self.assertEqual(INTENTS, frozenset({"admit", "replay_check"}))
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))


class ClassifyStatus(unittest.TestCase):
    def test_timeout_outranks_concurrent(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=True),
            "UNKNOWN")

    def test_idle_verified(self):
        self.assertEqual(
            classify_status(activity="idle", timed_out=False),
            "VERIFIED")

    def test_concurrent_suspected(self):
        self.assertEqual(
            classify_status(activity="concurrent", timed_out=False),
            "SUSPECTED")

    def test_unknown_activity(self):
        self.assertEqual(
            classify_status(activity="unknown", timed_out=False),
            "UNKNOWN")

    def test_unknown_activity_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_status(activity="racing", timed_out=False)


class RequireNonce(unittest.TestCase):
    def test_well_formed(self):
        self.assertEqual(require_nonce(_NCE), _NCE)
        self.assertTrue(NONCE_RE.match(_NCE))

    def test_evt_prefix_is_not_a_nonce(self):
        with self.assertRaises(FailClosedError):
            require_nonce("evt-0123456789abcdef")

    def test_uppercase_hex_fails(self):
        with self.assertRaises(FailClosedError):
            require_nonce("nce-0123456789ABCDEF")

    def test_sealed_name_fails(self):
        with self.assertRaises(FailClosedError):
            require_nonce("send_authorized")

    def test_empty_fails(self):
        with self.assertRaises(FailClosedError):
            require_nonce("")
        with self.assertRaises(FailClosedError):
            require_nonce(None)
        with self.assertRaises(FailClosedError):
            require_nonce(True)


class AdmitHappyPath(unittest.TestCase):
    def test_idle_admit(self):
        d = admit_nonce(intended="admit", nonce=_NCE, run_id=_RUN)
        self.assertTrue(d.allowed)
        self.assertIsNone(d.reason)
        self.assertEqual(d.status, "VERIFIED")
        self.assertEqual(d.intended, "admit")
        self.assertFalse(d.grants_send)
        self.assertFalse(d.timed_out)

    def test_replay_check_under_halt(self):
        d = admit_nonce(
            intended="replay_check", nonce=_NCE, run_id=_RUN, halted=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertFalse(d.grants_send)

    def test_replay_check_under_timeout(self):
        d = admit_nonce(
            intended="replay_check", nonce=_NCE, run_id=_RUN, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertTrue(d.timed_out)
        self.assertFalse(d.grants_send)


class AdmitRefusals(unittest.TestCase):
    def test_halt_refuses_admit_only(self):
        d = admit_nonce(
            intended="admit", nonce=_NCE, run_id=_RUN, halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_active")
        self.assertFalse(d.grants_send)

    def test_timeout_refuses_admit_as_unknown(self):
        d = admit_nonce(
            intended="admit", nonce=_NCE, run_id=_RUN, timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_concurrent_refuses_admit(self):
        d = admit_nonce(
            intended="admit", nonce=_NCE, run_id=_RUN, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")

    def test_malformed_nonce(self):
        d = admit_nonce(intended="admit", nonce="nce-short", run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_nonce")

    def test_malformed_run_id(self):
        d = admit_nonce(intended="admit", nonce=_NCE, run_id="run-x")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_id")

    def test_sealed_nonce(self):
        d = admit_nonce(
            intended="admit", nonce="campaign_envelope_ready", run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertFalse(d.grants_send)

    def test_sealed_run_id(self):
        d = admit_nonce(intended="admit", nonce=_NCE, run_id="quote_sent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_sealed_hyphen_alias(self):
        d = admit_nonce(
            intended="admit", nonce="send-authorized", run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")

    def test_unknown_intent_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_nonce(intended="resend", nonce=_NCE, run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_bool_halted_required(self):
        with self.assertRaises(FailClosedError):
            admit_nonce(intended="admit", nonce=_NCE, run_id=_RUN, halted=1)

    def test_bool_timed_out_required(self):
        with self.assertRaises(FailClosedError):
            admit_nonce(
                intended="admit", nonce=_NCE, run_id=_RUN, timed_out="yes")

    def test_unknown_activity_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_nonce(
                intended="admit", nonce=_NCE, run_id=_RUN, activity="racing")


class DistinctFromSiblings(unittest.TestCase):
    def test_nonce_prefix_is_not_event_id(self):
        self.assertTrue(_NCE.startswith("nce-"))
        self.assertFalse(_NCE.startswith("evt-"))

    def test_does_not_import_run_store(self):
        import ofn.kernel.nonce_class as mod
        self.assertFalse(hasattr(mod, "RunStore"))
        src = inspect.getsource(mod)
        self.assertNotIn("adapters.run_store", src)
        self.assertNotIn("from ofn.adapters", src)


if __name__ == "__main__":
    unittest.main()
