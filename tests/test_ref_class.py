"""Kernel-pure ref class — complementary to typed_event / event_id.

Shape admission only. Missing is UNKNOWN. Sealed send/ready names
refuse. Proposal names refuse. Timeout is UNKNOWN, not a
concurrent-write proof. Ready is not authorized. Not wired into
the run store. Does not hash a body.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.ref_class import (
    CLASSES,
    REFUSAL_REASONS,
    RefDecision,
    admit_ref,
    burns_idempotency_key,
    claims_immutable,
    classify_ref,
    classify_timeout,
    copies_canonical,
    grants_send,
    halt_blocks_classify,
    hashes_body,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    second_debit_is_first,
    timeout_proves_concurrent,
    try_classify,
    unknown_is_false,
    unknown_ref_is_empty,
    wires_into_run_store,
)

REF_A = "evt-" + ("ab" * 8)
REF_B = "evt-" + ("cd" * 8)
REF_ZERO = "evt-" + ("0" * 16)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_ref_is_not_empty(self):
        self.assertFalse(unknown_ref_is_empty())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_burn_idempotency_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_copy_canonical(self):
        self.assertFalse(copies_canonical())

    def test_does_not_hash_body(self):
        self.assertFalse(hashes_body())

    def test_second_debit_is_not_first(self):
        self.assertFalse(second_debit_is_first())

    def test_admit_signature_has_no_halt_or_send(self):
        params = inspect.signature(admit_ref).parameters
        for forbidden in (
            "halt",
            "halt_raw",
            "send_authorized",
            "quote_sent",
            "resend",
            "campaign_envelope_ready",
            "prior_debit",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=True, reason=None, ref_class="VERIFIED",
                ref=REF_A, timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=False, reason="sealed_effect", ref_class="UNKNOWN",
                ref="send_authorized", timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=True, reason="sealed_effect", ref_class="VERIFIED",
                ref=REF_A, timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=False, reason=None, ref_class="UNKNOWN",
                ref=REF_A, timed_out=False)
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=False, reason="send_authorized", ref_class="UNKNOWN",
                ref=REF_A, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertIn("proposal_not_receipt", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_verified_requires_recorded_ref(self):
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=True, reason=None, ref_class="VERIFIED",
                ref=None, timed_out=False)

    def test_timed_out_cannot_be_verified(self):
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=True, reason=None, ref_class="VERIFIED",
                ref=REF_A, timed_out=True)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            RefDecision(
                allowed=True, reason=None, ref_class="UNKNOWN",
                ref=None, timed_out="false")  # type: ignore[arg-type]

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    RefDecision(
                        allowed=True, reason=None, ref_class="UNKNOWN",
                        ref=name, timed_out=False)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = RefDecision(
            allowed=False, reason="sealed_effect", ref_class="UNKNOWN",
            ref="send_authorized", timed_out=False)
        self.assertEqual(d.ref, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)

    def test_proposal_refusal_names_the_subject(self):
        d = RefDecision(
            allowed=False, reason="proposal_not_receipt",
            ref_class="UNKNOWN", ref="PROPOSAL_CREATED", timed_out=False)
        self.assertEqual(d.ref, "PROPOSAL_CREATED")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)


class ClosedVocabularies(unittest.TestCase):
    def test_classes(self):
        self.assertEqual(CLASSES, frozenset({"VERIFIED", "UNKNOWN"}))

    def test_refusal_reasons(self):
        self.assertEqual(
            REFUSAL_REASONS,
            frozenset({"sealed_effect", "proposal_not_receipt"}))


class ClassifyShape(unittest.TestCase):
    def test_valid_event_id_is_verified(self):
        self.assertEqual(classify_ref(REF_A), "VERIFIED")
        self.assertEqual(classify_ref(REF_ZERO), "VERIFIED")
        self.assertEqual(classify_ref(REF_B), "VERIFIED")

    def test_missing_is_unknown_not_false(self):
        self.assertIsNone(classify_ref(None))
        self.assertIsNone(try_classify(None))
        self.assertIsNot(classify_ref(None), False)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_ref("")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_uppercase_hex_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_ref("evt-" + ("AB" * 8))

    def test_wrong_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_ref("evt-" + ("ab" * 4))
        with self.assertRaises(FailClosedError):
            classify_ref("evt-" + ("ab" * 9))

    def test_run_id_family_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_ref("run-1234567890-abcdefghij")

    def test_receipt_id_family_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_ref("rcp-1234567890-abcdefghij")

    def test_kind_name_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_ref("EXECUTION_RECEIPT")
        with self.assertRaises(FailClosedError):
            classify_ref("BUDGET_DEBIT")

    def test_non_str_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_ref(b"evt-abababababababab")  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            classify_ref(True)  # type: ignore[arg-type]

    def test_sealed_name_fails_closed(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
            "QUOTE-SENT",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError) as ctx:
                    classify_ref(name)
                self.assertIn("sealed", str(ctx.exception).lower())

    def test_proposal_name_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_ref("PROPOSAL_CREATED")
        self.assertIn("proposal", str(ctx.exception).lower())


class AdmitRef(unittest.TestCase):
    def test_valid_event_id_admitted_verified(self):
        d = admit_ref(REF_A)
        self.assertTrue(d.allowed)
        self.assertEqual(d.ref_class, "VERIFIED")
        self.assertEqual(d.ref, REF_A)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertFalse(d.timed_out)

    def test_missing_admitted_unknown(self):
        d = admit_ref(None)
        self.assertTrue(d.allowed)
        self.assertEqual(d.ref_class, "UNKNOWN")
        self.assertIsNone(d.ref)
        self.assertFalse(d.grants_send)

    def test_timeout_outranks_verified(self):
        d = admit_ref(REF_A, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.ref_class, "UNKNOWN")
        self.assertEqual(d.ref, REF_A)
        self.assertTrue(d.timed_out)
        self.assertFalse(d.grants_send)
        self.assertFalse(timeout_proves_concurrent())

    def test_timeout_on_missing_stays_unknown(self):
        d = admit_ref(None, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.ref_class, "UNKNOWN")
        self.assertIsNone(d.ref)

    def test_sealed_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                d = admit_ref(name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertEqual(d.ref_class, "UNKNOWN")
                self.assertEqual(d.ref, name)
                self.assertFalse(d.grants_send)

    def test_proposal_refused(self):
        d = admit_ref("PROPOSAL_CREATED")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "proposal_not_receipt")
        self.assertFalse(d.grants_send)
        self.assertFalse(proposal_is_execution())

    def test_sealed_under_timeout_still_sealed(self):
        d = admit_ref("send_authorized", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertTrue(d.timed_out)

    def test_shape_error_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_ref("not-a-ref")

    def test_timed_out_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            admit_ref(REF_A, timed_out=0)  # type: ignore[arg-type]

    def test_ready_and_authorized_are_distinct_refusals(self):
        ready = admit_ref("campaign_envelope_ready")
        auth = admit_ref("send_authorized")
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.ref, auth.ref)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
