"""Kernel-pure digest class — complementary to receipt_bind / hash_chain.

Shape admission only. Missing is UNKNOWN. Sealed send/ready names
refuse. Timeout is UNKNOWN, not a concurrent-write proof. Ready is
not authorized. Not wired into the run store. Does not hash a body.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.digest_class import (
    CLASSES,
    REFUSAL_REASONS,
    DigestDecision,
    admit_digest,
    burns_idempotency_key,
    claims_immutable,
    classify_digest,
    classify_timeout,
    copies_canonical,
    grants_send,
    halt_blocks_classify,
    hashes_body,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    try_classify,
    unknown_digest_is_empty,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

DIGEST_A = "ab" * 32
DIGEST_B = "cd" * 32
GENESIS_HEX = "0" * 64


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_classify(self):
        self.assertFalse(halt_blocks_classify())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_unknown_digest_is_not_empty(self):
        self.assertFalse(unknown_digest_is_empty())

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

    def test_does_not_copy_canonical(self):
        self.assertFalse(copies_canonical())

    def test_does_not_hash_body(self):
        self.assertFalse(hashes_body())

    def test_admit_signature_has_no_halt_or_send(self):
        params = inspect.signature(admit_digest).parameters
        for forbidden in (
            "halt",
            "halt_raw",
            "send_authorized",
            "quote_sent",
            "resend",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=True, reason=None, digest_class="VERIFIED",
                digest=DIGEST_A, timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=False, reason="sealed_effect", digest_class="UNKNOWN",
                digest="send_authorized", timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=True, reason="sealed_effect", digest_class="VERIFIED",
                digest=DIGEST_A, timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=False, reason=None, digest_class="UNKNOWN",
                digest=DIGEST_A, timed_out=False)
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=False, reason="send_authorized", digest_class="UNKNOWN",
                digest=DIGEST_A, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_verified_requires_recorded_digest(self):
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=True, reason=None, digest_class="VERIFIED",
                digest=None, timed_out=False)

    def test_timed_out_cannot_be_verified(self):
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=True, reason=None, digest_class="VERIFIED",
                digest=DIGEST_A, timed_out=True)

    def test_timed_out_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            DigestDecision(
                allowed=True, reason=None, digest_class="UNKNOWN",
                digest=None, timed_out="false")  # type: ignore[arg-type]

    def test_allowed_decision_refuses_sealed_names(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    DigestDecision(
                        allowed=True, reason=None, digest_class="UNKNOWN",
                        digest=name, timed_out=False)

    def test_sealed_effect_refusal_names_the_subject(self):
        d = DigestDecision(
            allowed=False, reason="sealed_effect", digest_class="UNKNOWN",
            digest="send_authorized", timed_out=False)
        self.assertEqual(d.digest, "send_authorized")
        self.assertFalse(d.allowed)
        self.assertFalse(d.grants_send)


class ClosedVocabularies(unittest.TestCase):
    def test_classes(self):
        self.assertEqual(CLASSES, frozenset({"VERIFIED", "UNKNOWN"}))

    def test_refusal_reasons(self):
        self.assertEqual(REFUSAL_REASONS, frozenset({"sealed_effect"}))


class ClassifyShape(unittest.TestCase):
    def test_valid_hex_is_verified(self):
        self.assertEqual(classify_digest(DIGEST_A), "VERIFIED")
        self.assertEqual(classify_digest(GENESIS_HEX), "VERIFIED")
        self.assertEqual(classify_digest(DIGEST_B), "VERIFIED")

    def test_missing_is_unknown_not_false(self):
        self.assertIsNone(classify_digest(None))
        self.assertIsNone(try_classify(None))
        self.assertIsNot(classify_digest(None), False)

    def test_empty_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_digest("")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_uppercase_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(DIGEST_A.upper())

    def test_wrong_length_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest("ab" * 16)
        with self.assertRaises(FailClosedError):
            classify_digest("ab" * 33)

    def test_non_str_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_digest(b"ab" * 32)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            classify_digest(True)  # type: ignore[arg-type]

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
                    classify_digest(name)
                self.assertIn("sealed", str(ctx.exception).lower())


class AdmitDigest(unittest.TestCase):
    def test_valid_hex_admitted_verified(self):
        d = admit_digest(DIGEST_A)
        self.assertTrue(d.allowed)
        self.assertEqual(d.digest_class, "VERIFIED")
        self.assertEqual(d.digest, DIGEST_A)
        self.assertIsNone(d.reason)
        self.assertFalse(d.grants_send)
        self.assertFalse(d.timed_out)

    def test_missing_admitted_unknown(self):
        d = admit_digest(None)
        self.assertTrue(d.allowed)
        self.assertEqual(d.digest_class, "UNKNOWN")
        self.assertIsNone(d.digest)
        self.assertFalse(d.grants_send)

    def test_timeout_outranks_verified(self):
        d = admit_digest(DIGEST_A, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.digest_class, "UNKNOWN")
        self.assertEqual(d.digest, DIGEST_A)
        self.assertTrue(d.timed_out)
        self.assertFalse(d.grants_send)
        self.assertFalse(timeout_proves_concurrent())

    def test_timeout_on_missing_stays_unknown(self):
        d = admit_digest(None, timed_out=True)
        self.assertTrue(d.allowed)
        self.assertEqual(d.digest_class, "UNKNOWN")
        self.assertIsNone(d.digest)

    def test_sealed_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                d = admit_digest(name)
                self.assertFalse(d.allowed)
                self.assertEqual(d.reason, "sealed_effect")
                self.assertEqual(d.digest_class, "UNKNOWN")
                self.assertEqual(d.digest, name)
                self.assertFalse(d.grants_send)

    def test_sealed_under_timeout_still_sealed(self):
        d = admit_digest("send_authorized", timed_out=True)
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "sealed_effect")
        self.assertTrue(d.timed_out)

    def test_shape_error_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            admit_digest("not-a-digest")

    def test_timed_out_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            admit_digest(DIGEST_A, timed_out=0)  # type: ignore[arg-type]

    def test_ready_and_authorized_are_distinct_refusals(self):
        ready = admit_digest("campaign_envelope_ready")
        auth = admit_digest("send_authorized")
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertEqual(auth.reason, "sealed_effect")
        self.assertNotEqual(ready.digest, auth.digest)
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
