"""Owner-absent chaos — ref-class / debit-pin composition.

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the ref/debit layer: no
store, no run_id mint, no fabricated debit. HALT is not a
classify or pin parameter. One arm's timeout cannot mark another
arm SUSPECTED. Recovery is observing a pin and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.debit_pin import (
    classify_timeout as debit_timeout,
    grants_send as debit_grants_send,
    halt_blocks_pin,
    invents_debit,
    pin_debit,
    ready_is_authorized as debit_ready_is_authorized,
    second_debit_is_first,
    timeout_proves_concurrent as debit_timeout_proves,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.ref_class import (
    admit_ref,
    classify_timeout as ref_timeout,
    grants_send as ref_grants_send,
    halt_blocks_classify,
    hashes_body,
    proposal_is_execution,
    ready_is_authorized as ref_ready_is_authorized,
    timeout_proves_concurrent as ref_timeout_proves,
)

REF_A = "evt-" + ("ab" * 8)
REF_B = "evt-" + ("cd" * 8)
REF_C = "evt-" + ("ef" * 8)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_missing_ref_is_not_classified_false(self):
        d = admit_ref(None)
        self.assertEqual(d.ref_class, "UNKNOWN")
        self.assertIsNot(d.ref_class, False)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_unknown_present_string_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_ref("DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("ref", str(ctx.exception).lower())


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_debit(self):
        timed = pin_debit(REF_A, timed_out=True)
        self.assertEqual(timed.debit_class, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = pin_debit(REF_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.debit_class, "FIRST")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(ref_timeout_proves())
        self.assertFalse(debit_timeout_proves())
        self.assertEqual(ref_timeout(), "UNKNOWN")
        self.assertEqual(debit_timeout(), "UNKNOWN")
        d = admit_ref(REF_A, timed_out=True)
        self.assertEqual(d.ref_class, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_ref_and_debit(self):
        decisions = [
            admit_ref(hex_value)
            for hex_value in (REF_A, REF_B, REF_C)
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertEqual(d.ref_class, "VERIFIED")
            self.assertFalse(d.grants_send)
        pins = [pin_debit(REF_A), pin_debit(REF_B), pin_debit(REF_C)]
        for p in pins:
            self.assertTrue(p.allowed)
            self.assertEqual(p.debit_class, "FIRST")
            self.assertFalse(p.grants_send)
            self.assertFalse(invents_debit())
            self.assertFalse(p.prior_debit)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_ref(REF_A)
        second = admit_ref(REF_A)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        first_pin = pin_debit(REF_A)
        again = pin_debit(REF_A)
        self.assertEqual(first_pin, again)
        self.assertEqual(again.debit_class, "FIRST")
        self.assertFalse(again.grants_send)
        self.assertFalse(ref_grants_send())
        self.assertFalse(debit_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_classify_continues(self):
        sealed = admit_ref("send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_ref(REF_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.ref_class, "VERIFIED")
        self.assertFalse(sibling.grants_send)
        sealed_pin = pin_debit("quote_sent")
        self.assertFalse(sealed_pin.allowed)
        live = pin_debit(REF_A)
        self.assertTrue(live.allowed)


class Scenario6GlobalHaltIsNotAClassifyParameter(unittest.TestCase):
    def test_halt_does_not_block_ref_or_debit(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        for hex_value in (REF_A, REF_B, REF_C):
            d = admit_ref(hex_value)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        p = pin_debit(REF_A)
        self.assertTrue(p.allowed)
        self.assertFalse(p.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        ref_params = inspect.signature(admit_ref).parameters
        debit_params = inspect.signature(pin_debit).parameters
        for params in (ref_params, debit_params):
            self.assertNotIn("halt", params)
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_classify_and_not_a_send(self):
        blocked = pin_debit("campaign_envelope_ready")
        self.assertFalse(blocked.allowed)
        second = pin_debit(REF_A, prior_debit=True)
        self.assertFalse(second.allowed)
        self.assertEqual(second.reason, "second_debit")
        resumed = pin_debit(REF_B)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(ref_grants_send())
        self.assertFalse(debit_grants_send())
        self.assertFalse(hashes_body())
        self.assertFalse(invents_debit())
        self.assertFalse(second_debit_is_first())

    def test_recovery_does_not_hash_a_body(self):
        d = admit_ref(REF_A)
        self.assertTrue(d.allowed)
        self.assertFalse(hashes_body())
        self.assertFalse(invents_debit())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_ref("campaign_envelope_ready")
        sent = admit_ref("quote_sent")
        auth = admit_ref("send_authorized")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(ref_ready_is_authorized())
        self.assertFalse(debit_ready_is_authorized())
        self.assertNotEqual(ready.ref, auth.ref)
        proposal = admit_ref("PROPOSAL_CREATED")
        self.assertFalse(proposal.allowed)
        self.assertEqual(proposal.reason, "proposal_not_receipt")
        self.assertFalse(proposal_is_execution())
        folded = pin_debit("campaign_envelope_ready")
        self.assertFalse(folded.allowed)
        self.assertEqual(folded.reason, "sealed_effect")


if __name__ == "__main__":
    unittest.main()
