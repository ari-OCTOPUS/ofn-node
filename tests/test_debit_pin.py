"""Kernel-pure debit pin — one verdict → one budget effect.

FIRST pins a classified event_id ref. Missing is UNKNOWN. Sealed
send/ready names refuse. Proposal names refuse. prior_debit refuses
as second_debit. Timeout is UNKNOWN, not a concurrent-write proof.
Ready is not authorized. Does not invent a debit. Not wired into
the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.debit_pin import (
    DEBIT_CLASSES,
    REFUSAL_REASONS,
    DebitPin,
    burns_idempotency_key,
    claims_immutable,
    classify_debit,
    classify_timeout,
    grants_send,
    halt_blocks_pin,
    invents_debit,
    later_disarm_supersedes,
    pin_debit,
    promotes_ready_to_send,
    proposal_is_execution,
    ready_is_authorized,
    second_debit_is_first,
    timeout_proves_concurrent,
    try_pin,
    unknown_is_false,
    wires_into_run_store,
)
from ofn.kernel.errors import FailClosedError

REF_A = "evt-" + ("ab" * 8)
REF_B = "evt-" + ("cd" * 8)
REF_C = "evt-" + ("12" * 8)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_proposal_is_not_execution(self):
        self.assertFalse(proposal_is_execution())

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_does_not_burn_idempotency_key(self):
        self.assertFalse(burns_idempotency_key())

    def test_not_wired_into_run_store(self):
        self.assertFalse(wires_into_run_store())

    def test_does_not_invent_debit(self):
        self.assertFalse(invents_debit())

    def test_second_debit_is_not_first(self):
        self.assertFalse(second_debit_is_first())

    def test_later_disarm_supersedes(self):
        self.assertTrue(later_disarm_supersedes())

    def test_pin_signature_has_no_halt_or_send(self):
        params = inspect.signature(pin_debit).parameters
        for forbidden in (
            "halt",
            "halt_raw",
            "send_authorized",
            "quote_sent",
            "resend",
            "campaign_envelope_ready",
        ):
            self.assertNotIn(forbidden, params)
        self.assertIn("prior_debit", params)
        self.assertIn("timed_out", params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="FIRST", allowed=True,
                reason=None, timed_out=False, prior_debit=False,
                grants_send=True)

    def test_allowed_must_not_carry_a_reason(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="FIRST", allowed=True,
                reason="second_debit", timed_out=False, prior_debit=False)

    def test_refused_requires_known_reason(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="UNKNOWN", allowed=False,
                reason=None, timed_out=False, prior_debit=True)
        self.assertIn("second_debit", REFUSAL_REASONS)
        self.assertNotIn("send_authorized", REFUSAL_REASONS)

    def test_first_requires_recorded_ref(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=None, debit_class="FIRST", allowed=True,
                reason=None, timed_out=False, prior_debit=False)

    def test_timed_out_cannot_be_first(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="FIRST", allowed=True,
                reason=None, timed_out=True, prior_debit=False)

    def test_allowed_cannot_record_prior_debit(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="FIRST", allowed=True,
                reason=None, timed_out=False, prior_debit=True)

    def test_second_debit_requires_prior_flag(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="UNKNOWN", allowed=False,
                reason="second_debit", timed_out=False, prior_debit=False)

    def test_present_id_cannot_be_unknown_without_timeout(self):
        with self.assertRaises(FailClosedError):
            DebitPin(
                ref=REF_A, debit_class="UNKNOWN", allowed=True,
                reason=None, timed_out=False, prior_debit=False)


class ClosedVocabularies(unittest.TestCase):
    def test_debit_classes(self):
        self.assertEqual(DEBIT_CLASSES, frozenset({"FIRST", "UNKNOWN"}))


class ClassifyDebit(unittest.TestCase):
    def test_valid_ref_is_first(self):
        self.assertEqual(classify_debit(REF_A), "FIRST")
        self.assertEqual(classify_debit(REF_B), "FIRST")

    def test_missing_is_unknown(self):
        self.assertIsNone(classify_debit(None))
        self.assertIsNone(try_pin(None))

    def test_prior_debit_fails_closed_in_classify(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_debit(REF_A, prior_debit=True)
        self.assertIn("one verdict", str(ctx.exception).lower())

    def test_prior_debit_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            classify_debit(REF_A, prior_debit=1)  # type: ignore[arg-type]

    def test_sealed_fails_closed_in_classify(self):
        with self.assertRaises(FailClosedError):
            classify_debit("send_authorized")
        with self.assertRaises(FailClosedError):
            classify_debit("quote_sent")

    def test_proposal_fails_closed_in_classify(self):
        with self.assertRaises(FailClosedError):
            classify_debit("PROPOSAL_CREATED")


class PinDebit(unittest.TestCase):
    def test_first_admitted(self):
        p = pin_debit(REF_A)
        self.assertTrue(p.allowed)
        self.assertEqual(p.debit_class, "FIRST")
        self.assertEqual(p.ref, REF_A)
        self.assertIsNone(p.reason)
        self.assertFalse(p.grants_send)
        self.assertFalse(p.prior_debit)
        self.assertFalse(invents_debit())

    def test_second_observe_is_not_a_second_debit(self):
        first = pin_debit(REF_A)
        again = pin_debit(REF_A)
        self.assertEqual(first, again)
        self.assertEqual(again.debit_class, "FIRST")
        self.assertFalse(again.grants_send)
        self.assertFalse(second_debit_is_first())

    def test_distinct_refs_are_distinct_first_pins(self):
        a = pin_debit(REF_A)
        b = pin_debit(REF_B)
        self.assertEqual(a.debit_class, "FIRST")
        self.assertEqual(b.debit_class, "FIRST")
        self.assertNotEqual(a, b)

    def test_missing_is_unknown(self):
        p = pin_debit(None)
        self.assertTrue(p.allowed)
        self.assertEqual(p.debit_class, "UNKNOWN")
        self.assertIsNone(p.ref)
        self.assertFalse(p.grants_send)

    def test_timeout_outranks_first(self):
        p = pin_debit(REF_A, timed_out=True)
        self.assertTrue(p.allowed)
        self.assertEqual(p.debit_class, "UNKNOWN")
        self.assertEqual(p.ref, REF_A)
        self.assertTrue(p.timed_out)
        self.assertFalse(timeout_proves_concurrent())
        self.assertFalse(invents_debit())

    def test_prior_debit_refused(self):
        p = pin_debit(REF_A, prior_debit=True)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "second_debit")
        self.assertEqual(p.debit_class, "UNKNOWN")
        self.assertTrue(p.prior_debit)
        self.assertFalse(p.grants_send)
        self.assertFalse(second_debit_is_first())

    def test_prior_debit_under_timeout_still_second(self):
        p = pin_debit(REF_A, timed_out=True, prior_debit=True)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "second_debit")
        self.assertTrue(p.timed_out)
        self.assertTrue(p.prior_debit)

    def test_sealed_left_refused(self):
        p = pin_debit("campaign_envelope_ready")
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")
        self.assertEqual(p.debit_class, "UNKNOWN")
        self.assertFalse(p.grants_send)

    def test_proposal_refused(self):
        p = pin_debit("PROPOSAL_CREATED")
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "proposal_not_receipt")
        self.assertFalse(proposal_is_execution())

    def test_sealed_outranks_prior_debit(self):
        p = pin_debit("send_authorized", prior_debit=True)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")

    def test_proposal_outranks_prior_debit(self):
        p = pin_debit("PROPOSAL_CREATED", prior_debit=True)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "proposal_not_receipt")

    def test_sealed_under_timeout_still_sealed(self):
        p = pin_debit("quote_sent", timed_out=True)
        self.assertFalse(p.allowed)
        self.assertEqual(p.reason, "sealed_effect")
        self.assertTrue(p.timed_out)

    def test_try_pin_present_ref(self):
        p = try_pin(REF_A)
        self.assertIsNotNone(p)
        assert p is not None
        self.assertEqual(p.debit_class, "FIRST")

    def test_shape_error_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_debit("not-a-ref")

    def test_prior_debit_on_bad_shape_still_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_debit("not-a-ref", prior_debit=True)

    def test_ready_cannot_become_authorized_via_debit(self):
        ready = pin_debit("campaign_envelope_ready")
        auth = pin_debit("send_authorized")
        self.assertFalse(ready.allowed)
        self.assertFalse(auth.allowed)
        self.assertEqual(ready.reason, "sealed_effect")
        self.assertNotEqual(ready.ref, auth.ref)
        self.assertFalse(ready_is_authorized())
        self.assertTrue(later_disarm_supersedes())

    def test_prior_debit_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            pin_debit(REF_A, prior_debit=0)  # type: ignore[arg-type]

    def test_timed_out_must_be_bool(self):
        with self.assertRaises(FailClosedError):
            pin_debit(REF_A, timed_out=0)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
