"""Kernel-pure envelope class — complementary to envelope.py / start_permit.

A proposed mint is a START. Validate and replay are not STARTS.
This module does not mint a run_id and is not wired into the
run store. Ready is not authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.envelope_class import (
    ACTIVITIES,
    INTENTS,
    REFUSAL_REASONS,
    STATUSES,
    SUPPORTED_VERSION,
    EnvelopeDecision,
    admit_envelope,
    claims_immutable,
    classify_status,
    classify_timeout,
    grants_send,
    halt_blocks_validate,
    mints_run_id,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

_RUN = "run-1780000000-abcdefghij"


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_validate(self):
        self.assertFalse(halt_blocks_validate())

    def test_does_not_mint_run_id(self):
        self.assertFalse(mints_run_id())

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
        params = inspect.signature(admit_envelope).parameters
        self.assertEqual(
            list(params),
            ["intended", "version", "run_id", "activity", "halted", "timed_out"],
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
            EnvelopeDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="validate", run_id=_RUN, timed_out=False,
                grants_send=True)
        with self.assertRaises(FailClosedError):
            EnvelopeDecision(
                allowed=False, reason="sealed_effect", status="UNKNOWN",
                intended="validate", run_id="send_authorized",
                timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            EnvelopeDecision(
                allowed=True, reason="halt_active", status="VERIFIED",
                intended="mint", run_id=_RUN, timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            EnvelopeDecision(
                allowed=False, reason=None, status="UNKNOWN",
                intended="mint", run_id=_RUN, timed_out=False)
        with self.assertRaises(FailClosedError):
            EnvelopeDecision(
                allowed=False, reason="send_authorized", status="UNKNOWN",
                intended="mint", run_id=_RUN, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("halt_active", REFUSAL_REASONS)
        self.assertIn("unknown_version", REFUSAL_REASONS)
        self.assertIn("malformed_id", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_allowed_mint_requires_verified(self):
        for status in ("SUSPECTED", "UNKNOWN"):
            with self.subTest(status=status):
                with self.assertRaises(FailClosedError):
                    EnvelopeDecision(
                        allowed=True, reason=None, status=status,
                        intended="mint", run_id=_RUN, timed_out=False)

    def test_allowed_decision_refuses_sealed_run_id(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    EnvelopeDecision(
                        allowed=True, reason=None, status="VERIFIED",
                        intended="validate", run_id=name, timed_out=False)

    def test_non_sealed_refusal_cannot_carry_a_sealed_run_id(self):
        with self.assertRaises(FailClosedError):
            EnvelopeDecision(
                allowed=False, reason="unknown_activity", status="UNKNOWN",
                intended="mint", run_id="send_authorized", timed_out=True)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = EnvelopeDecision(
            allowed=False, reason="sealed_effect", status="UNKNOWN",
            intended="validate", run_id="send_authorized", timed_out=False)
        self.assertEqual(d.run_id, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            EnvelopeDecision(
                allowed=True, reason=None, status="VERIFIED",
                intended="validate", run_id=_RUN, timed_out="false")  # type: ignore[arg-type]


class ClosedVocabularies(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(STATUSES, frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"}))

    def test_activities(self):
        self.assertEqual(ACTIVITIES, frozenset({"idle", "concurrent", "unknown"}))

    def test_intents(self):
        self.assertEqual(INTENTS, frozenset({"mint", "validate", "replay"}))

    def test_supported_version_is_one(self):
        self.assertEqual(SUPPORTED_VERSION, 1)


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


class MintIsAStart(unittest.TestCase):
    def test_mint_idle_verified_is_admitted(self):
        d = admit_envelope(intended="mint", version=1, run_id=_RUN)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "VERIFIED")
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)

    def test_mint_halted_is_refused(self):
        d = admit_envelope(
            intended="mint", version=1, run_id=_RUN, halted=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "halt_active")
        self.assertFalse(d.grants_send)

    def test_mint_unknown_is_refused(self):
        d = admit_envelope(
            intended="mint", version=1, run_id=_RUN, activity="unknown")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_mint_concurrent_is_refused(self):
        d = admit_envelope(
            intended="mint", version=1, run_id=_RUN, activity="concurrent")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "suspected_concurrent")
        self.assertEqual(d.status, "SUSPECTED")
        self.assertFalse(d.grants_send)

    def test_mint_timeout_is_unknown_not_suspected(self):
        d = admit_envelope(
            intended="mint", version=1, run_id=_RUN,
            activity="concurrent", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_activity")
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class ValidateAndReplayAreNotStarts(unittest.TestCase):
    def test_validate_continues_under_halt(self):
        d = admit_envelope(
            intended="validate", version=1, run_id=_RUN, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertFalse(halt_blocks_validate())

    def test_replay_continues_under_halt(self):
        d = admit_envelope(
            intended="replay", version=1, run_id=_RUN, halted=True)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_validate_timeout_is_unknown_and_still_admitted(self):
        d = admit_envelope(
            intended="validate", version=1, run_id=_RUN, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_replay_is_byte_identical(self):
        a = admit_envelope(intended="replay", version=1, run_id=_RUN)
        b = admit_envelope(intended="replay", version=1, run_id=_RUN)
        self.assertEqual(a, b)
        self.assertTrue(a.allowed)
        self.assertFalse(a.grants_send)


class VersionAndShape(unittest.TestCase):
    def test_unknown_version_is_refused_not_false(self):
        d = admit_envelope(intended="mint", version=2, run_id=_RUN)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "unknown_version")
        self.assertFalse(d.grants_send)

    def test_bool_version_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_envelope(intended="mint", version=True, run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_str_version_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_envelope(intended="mint", version="1", run_id=_RUN)

    def test_malformed_run_id_is_refused(self):
        d = admit_envelope(
            intended="mint", version=1, run_id="not-a-run")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "malformed_id")
        self.assertFalse(d.grants_send)


class UnknownFailsClosed(unittest.TestCase):
    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_envelope(
                intended="mint", version=1, run_id=_RUN, activity="racing")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_envelope(intended="send", version=1, run_id=_RUN)
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_empty_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_envelope(intended="mint", version=1, run_id="  ")

    def test_bool_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_envelope(intended="mint", version=1, run_id=True)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_envelope(
                intended="mint", version=1, run_id=_RUN, timed_out=1)
        with self.assertRaises(FailClosedError):
            admit_envelope(
                intended="mint", version=1, run_id=_RUN, timed_out="true")

    def test_halted_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_envelope(
                intended="mint", version=1, run_id=_RUN, halted=1)


class SealedNameRefusesEnvelope(unittest.TestCase):
    def test_sealed_run_id_aliases(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "SEND_AUTHORIZED",
            "quote-sent",
            "campaign-envelope-ready",
        ):
            with self.subTest(name=name):
                d = admit_envelope(intended="validate", version=1, run_id=name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertFalse(d.grants_send)

    def test_ready_and_authorized_stay_distinct_subjects(self):
        ready = admit_envelope(
            intended="validate", version=1,
            run_id="campaign_envelope_ready")
        auth = admit_envelope(
            intended="validate", version=1, run_id="send_authorized")
        self.assertNotEqual(ready.run_id, auth.run_id)
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
