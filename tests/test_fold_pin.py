"""Kernel-pure fold pin — pair two digests without inventing a third.

Same digest restates. Different VERIFIED digests pair. Missing is
UNKNOWN. Sealed send/ready names refuse. Timeout is UNKNOWN, not a
concurrent-write proof. Ready is not authorized. Does not hash a
body. Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.fold_pin import (
    FOLD_CLASSES,
    REFUSAL_REASONS,
    FoldPin,
    burns_idempotency_key,
    claims_immutable,
    classify_fold,
    classify_timeout,
    grants_send,
    halt_blocks_pin,
    invents_third_digest,
    later_disarm_supersedes,
    pin_fold,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    timeout_proves_concurrent,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)

DIGEST_A = "ab" * 32
DIGEST_B = "cd" * 32
DIGEST_C = "12" * 32


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

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

    def test_does_not_invent_third_digest(self):
        self.assertFalse(invents_third_digest())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_pin_signature_has_no_halt_or_send(self):
        params = inspect.signature(pin_fold).parameters
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
            FoldPin(
                left=DIGEST_A, right=DIGEST_A, fold_class="RESTATED",
                allowed=True, reason=None, timed_out=False, grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_A, fold_class="RESTATED",
                allowed=True, reason="sealed_effect", timed_out=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_B, fold_class="UNKNOWN",
                allowed=False, reason=None, timed_out=False)
        self.assertIn("sealed_effect", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_restated_requires_identical_sides(self):
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_B, fold_class="RESTATED",
                allowed=True, reason=None, timed_out=False)

    def test_paired_requires_different_sides(self):
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_A, fold_class="PAIRED",
                allowed=True, reason=None, timed_out=False)

    def test_timed_out_cannot_be_restated_or_paired(self):
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_A, fold_class="RESTATED",
                allowed=True, reason=None, timed_out=True)
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_B, fold_class="PAIRED",
                allowed=True, reason=None, timed_out=True)

    def test_two_hex_sides_cannot_be_unknown_without_timeout(self):
        with self.assertRaises(FailClosedError):
            FoldPin(
                left=DIGEST_A, right=DIGEST_B, fold_class="UNKNOWN",
                allowed=True, reason=None, timed_out=False)


class ClosedVocabularies(unittest.TestCase):
    def test_fold_classes(self):
        self.assertEqual(
            FOLD_CLASSES, frozenset({"RESTATED", "PAIRED", "UNKNOWN"}))


class ClassifyFold(unittest.TestCase):
    def test_same_digest_is_restated(self):
        self.assertEqual(classify_fold(DIGEST_A, DIGEST_A), "RESTATED")

    def test_different_digests_are_paired(self):
        self.assertEqual(classify_fold(DIGEST_A, DIGEST_B), "PAIRED")
        self.assertEqual(classify_fold(DIGEST_B, DIGEST_C), "PAIRED")

    def test_missing_either_side_is_unknown(self):
        self.assertIsNone(classify_fold(None, DIGEST_A))
        self.assertIsNone(classify_fold(DIGEST_A, None))
        self.assertIsNone(classify_fold(None, None))
        self.assertIsNone(try_pin(None, DIGEST_A))
        self.assertIsNone(try_pin(DIGEST_A, None))

    def test_order_is_recorded_not_silently_commutative(self):
        ab = pin_fold(DIGEST_A, DIGEST_B)
        ba = pin_fold(DIGEST_B, DIGEST_A)
        self.assertEqual(ab.fold_class, "PAIRED")
        self.assertEqual(ba.fold_class, "PAIRED")
        self.assertEqual(ab.left, DIGEST_A)
        self.assertEqual(ab.right, DIGEST_B)
        self.assertEqual(ba.left, DIGEST_B)
        self.assertEqual(ba.right, DIGEST_A)
        self.assertNotEqual(ab, ba)

    def test_sealed_fails_closed_in_classify(self):
        with self.assertRaises(FailClosedError):
            classify_fold("send_authorized", DIGEST_A)
        with self.assertRaises(FailClosedError):
            classify_fold(DIGEST_A, "quote_sent")


class PinFold(unittest.TestCase):
    def test_restated_admitted(self):
        p = pin_fold(DIGEST_A, DIGEST_A)
        self.assertTrue(p.allowed)
        self.assertEqual(p.fold_class, "RESTATED")
        self.assertEqual(p.left, DIGEST_A)
        self.assertEqual(p.right, DIGEST_A)
        self.assertIsNone(p.reason)
        self.assertFalse(p.grants_send)
        self.assertFalse(invents_third_digest())

    def test_paired_admitted(self):
        p = pin_fold(DIGEST_A, DIGEST_B)
        self.assertTrue(p.allowed)
        self.assertEqual(p.fold_class, "PAIRED")
        self.assertEqual(p.left, DIGEST_A)
        self.assertEqual(p.right, DIGEST_B)
        self.assertFalse(p.grants_send)

    def test_missing_left_is_unknown(self):
        p = pin_fold(None, DIGEST_B)
        self.assertTrue(p.allowed)
        self.assertEqual(p.fold_class, "UNKNOWN")
        self.assertIsNone(p.left)
        self.assertEqual(p.right, DIGEST_B)
        self.assertFalse(p.grants_send)

    def test_missing_right_is_unknown(self):
        p = pin_fold(DIGEST_A, None)
        self.assertTrue(p.allowed)
        self.assertEqual(p.fold_class, "UNKNOWN")
        self.assertEqual(p.left, DIGEST_A)
        self.assertIsNone(p.right)

    def test_timeout_outranks_pair(self):
        p = pin_fold(DIGEST_A, DIGEST_B, timed_out=True)
        self.assertTrue(p.allowed)
        self.assertEqual(p.fold_class, "UNKNOWN")
        self.assertEqual(p.left, DIGEST_A)
        self.assertEqual(p.right, DIGEST_B)
        self.assertTrue(p.timed_out)
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(invents_third_digest())

    def test_timeout_outranks_restate(self):
        p = pin_fold(DIGEST_A, DIGEST_A, timed_out=True)
        self.assertEqual(p.fold_class, "UNKNOWN")
        self.assertTrue(p.allowed)

    def test_sealed_left_refused(self):
        p = pin_fold("campaign_envelope_ready", DIGEST_A)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")
        self.assertEqual(p.fold_class, "UNKNOWN")
        self.assertFalse(p.grants_send)

    def test_sealed_right_refused(self):
        p = pin_fold(DIGEST_A, "send_authorized")
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")

    def test_sealed_under_timeout_still_sealed(self):
        p = pin_fold("quote_sent", DIGEST_B, timed_out=True)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")
        self.assertTrue(p.timed_out)

    def test_try_pin_present_pair(self):
        p = try_pin(DIGEST_A, DIGEST_B)
        self.assertIsNotNone(p)
        assert p is not None
        self.assertEqual(p.fold_class, "PAIRED")

    def test_shape_error_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_fold("not-a-digest", DIGEST_A)

    def test_ready_cannot_become_authorized_via_fold(self):
        ready = pin_fold("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready.allowed)
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertFalse(ready_is_authorized())
        self.assertTrue(later_disarm_supersedes())


if __name__ == "__main__":
    unittest.main()
