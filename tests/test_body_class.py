"""Kernel-pure body class — complementary to census / artifact_ref.

Presence admission only. Missing is UNKNOWN. One-vantage
body_missing refuses. Sealed send/ready names refuse. Timeout is
UNKNOWN, not a concurrent-write proof. Ready is not authorized.
Not wired into the run store. Does not hash a body.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.body_class import (
    CLASSES,
    REFUSAL_REASONS,
    BodyDecision,
    admit_body,
    burns_idempotency_key,
    claims_immutable,
    classify_body,
    classify_timeout,
    copies_canonical,
    grants_send,
    halt_blocks_classify,
    hashes_body,
    one_host_proves_missing,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    try_classify,
    unknown_body_is_missing,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError


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

    def test_unknown_body_is_not_missing(self):
        self.assertFalse(unknown_body_is_missing())

    def test_one_host_does_not_prove_missing(self):
        self.assertFalse(one_host_proves_missing())

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
        params = inspect.signature(admit_body).parameters
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
            BodyDecision(
                allowed=True, reason=None, body_class="ON_THIS_HOST",
                location="on_this_host", timed_out=False, grants_send=True)
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=False, reason="sealed_effect", body_class="UNKNOWN",
                location="send_authorized", timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=True, reason="sealed_effect", body_class="ON_THIS_HOST",
                location="on_this_host", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=False, reason=None, body_class="UNKNOWN",
                location="on_this_host", timed_out=False)
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=False, reason="send_authorized", body_class="UNKNOWN",
                location="on_this_host", timed_out=False)

    def test_closed_vocabularies(self):
        self.assertEqual(
            CLASSES, frozenset({"ON_THIS_HOST", "NOT_ON_THIS_HOST", "UNKNOWN"}))
        self.assertEqual(
            REFUSAL_REASONS, frozenset({"sealed_effect", "missing_claim"}))


class ClassifyAndAdmit(unittest.TestCase):
    def test_missing_is_unknown_not_false(self):
        self.assertIsNone(classify_body(None))
        d = admit_body(None)
        self.assertEqual(d.body_class, "UNKNOWN")
        self.assertIsNone(d.location)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertIsNot(d.body_class, False)

    def test_on_this_host_verified(self):
        self.assertEqual(classify_body("on_this_host"), "ON_THIS_HOST")
        d = admit_body("on_this_host")
        self.assertEqual(d.body_class, "ON_THIS_HOST")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_hyphen_and_alias_tokens(self):
        self.assertEqual(classify_body("present-here"), "ON_THIS_HOST")
        self.assertEqual(
            classify_body("body-not-on-this-host"), "NOT_ON_THIS_HOST")
        self.assertEqual(classify_body("absent_here"), "NOT_ON_THIS_HOST")

    def test_disk_absence_is_not_on_this_host(self):
        d = admit_body("body_not_on_this_host")
        self.assertEqual(d.body_class, "NOT_ON_THIS_HOST")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertNotEqual(d.body_class, "UNKNOWN")

    def test_body_missing_fails_closed_on_classify(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_body("body_missing")
        self.assertIn("body_missing", str(ctx.exception))
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_body_missing_is_known_refusal_on_admit(self):
        d = admit_body("body_missing")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "missing_claim")
        self.assertEqual(d.body_class, "UNKNOWN")
        self.assertFalse(d.grants_send)
        for token in ("missing", "gone"):
            refused = admit_body(token)
            self.assertFalse(refused.allowed)
            self.assertEqual(refused.reason, "missing_claim")

    def test_empty_and_non_str_fail_closed(self):
        with self.assertRaises(FailClosedError):
            classify_body("")
        with self.assertRaises(FailClosedError):
            classify_body("   ")
        with self.assertRaises(FailClosedError):
            classify_body(0)
        with self.assertRaises(FailClosedError):
            classify_body(["on_this_host"])

    def test_unknown_token_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_body("somewhere")
        with self.assertRaises(FailClosedError):
            admit_body("somewhere")

    def test_sealed_names_refuse(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
        ):
            with self.assertRaises(FailClosedError):
                classify_body(name)
            d = admit_body(name)
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)

    def test_timeout_forces_unknown_keeps_token(self):
        d = admit_body("on_this_host", timed_out=True)
        self.assertEqual(d.body_class, "UNKNOWN")
        self.assertEqual(d.location, "on_this_host")
        self.assertTrue(d.allowed)
        self.assertTrue(d.timed_out)
        self.assertFalse(d.grants_send)

    def test_timeout_must_be_exact_bool(self):
        with self.assertRaises(FailClosedError):
            admit_body("on_this_host", timed_out=1)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            admit_body(None, timed_out="yes")  # type: ignore[arg-type]

    def test_timed_out_located_class_refused_by_constructor(self):
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=True, reason=None, body_class="ON_THIS_HOST",
                location="on_this_host", timed_out=True)

    def test_located_class_requires_location(self):
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=True, reason=None, body_class="ON_THIS_HOST",
                location=None, timed_out=False)
        with self.assertRaises(FailClosedError):
            BodyDecision(
                allowed=True, reason=None, body_class="NOT_ON_THIS_HOST",
                location=None, timed_out=False)

    def test_try_classify_missing_is_none(self):
        self.assertIsNone(try_classify(None))
        self.assertEqual(try_classify("on_this_host"), "ON_THIS_HOST")

    def test_try_classify_bad_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            try_classify("body_missing")


if __name__ == "__main__":
    unittest.main()
