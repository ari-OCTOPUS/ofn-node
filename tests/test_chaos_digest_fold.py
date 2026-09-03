"""Owner-absent chaos — digest-class / fold-pin composition.

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the digest/fold layer: no
store, no run_id mint, no fabricated third digest. HALT is not a
classify or pin parameter. One arm's timeout cannot mark another
arm SUSPECTED. Recovery is observing a pair and is still not a send.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.digest_class import (
    admit_digest,
    classify_timeout as digest_timeout,
    grants_send as digest_grants_send,
    halt_blocks_classify,
    hashes_body,
    ready_is_authorized as digest_ready_is_authorized,
    timeout_proves_concurrent as digest_timeout_proves,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.fold_pin import (
    classify_timeout as fold_timeout,
    grants_send as fold_grants_send,
    halt_blocks_pin,
    invents_third_digest,
    pin_fold,
    ready_is_authorized as fold_ready_is_authorized,
    timeout_proves_concurrent as fold_timeout_proves,
)

DIGEST_A = "ab" * 32
DIGEST_B = "cd" * 32
DIGEST_C = "ef" * 32


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_missing_digest_is_not_classified_false(self):
        d = admit_digest(None)
        self.assertEqual(d.digest_class, "UNKNOWN")
        self.assertIsNot(d.digest_class, False)
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)

    def test_unknown_present_string_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_digest("DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("digest", str(ctx.exception).lower())


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_fold(self):
        timed = pin_fold(DIGEST_A, DIGEST_B, timed_out=True)
        self.assertEqual(timed.fold_class, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = pin_fold(DIGEST_A, DIGEST_C)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.fold_class, "PAIRED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(digest_timeout_proves())
        self.assertFalse(fold_timeout_proves())
        self.assertEqual(digest_timeout(), "UNKNOWN")
        self.assertEqual(fold_timeout(), "UNKNOWN")
        d = admit_digest(DIGEST_A, timed_out=True)
        self.assertEqual(d.digest_class, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_digest_and_fold(self):
        decisions = [
            admit_digest(hex_value)
            for hex_value in (DIGEST_A, DIGEST_B, DIGEST_C)
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertEqual(d.digest_class, "VERIFIED")
            self.assertFalse(d.grants_send)
        folds = [
            pin_fold(DIGEST_A, DIGEST_B),
            pin_fold(DIGEST_B, DIGEST_C),
            pin_fold(DIGEST_A, DIGEST_C),
        ]
        for p in folds:
            self.assertTrue(p.allowed)
            self.assertEqual(p.fold_class, "PAIRED")
            self.assertFalse(p.grants_send)
            self.assertFalse(invents_third_digest())


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_digest(DIGEST_A)
        second = admit_digest(DIGEST_A)
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        restated = pin_fold(DIGEST_A, DIGEST_A)
        self.assertEqual(restated.fold_class, "RESTATED")
        self.assertFalse(restated.grants_send)
        self.assertFalse(digest_grants_send())
        self.assertFalse(fold_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_classify_continues(self):
        sealed = admit_digest("send_authorized")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_digest(DIGEST_B)
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.digest_class, "VERIFIED")
        self.assertFalse(sibling.grants_send)
        sealed_fold = pin_fold("quote_sent", DIGEST_A)
        self.assertFalse(sealed_fold.allowed)
        live = pin_fold(DIGEST_A, DIGEST_B)
        self.assertTrue(live.allowed)


class Scenario6GlobalHaltIsNotAClassifyParameter(unittest.TestCase):
    def test_halt_does_not_block_digest_or_fold(self):
        self.assertFalse(halt_blocks_classify())
        self.assertFalse(halt_blocks_pin())
        for hex_value in (DIGEST_A, DIGEST_B, DIGEST_C):
            d = admit_digest(hex_value)
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)
        p = pin_fold(DIGEST_A, DIGEST_B)
        self.assertTrue(p.allowed)
        self.assertFalse(p.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        digest_params = inspect.signature(admit_digest).parameters
        fold_params = inspect.signature(pin_fold).parameters
        for params in (digest_params, fold_params):
            self.assertNotIn("halt", params)
            self.assertNotIn("halt_raw", params)
            self.assertNotIn("send_authorized", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_a_classify_and_not_a_send(self):
        blocked = pin_fold("campaign_envelope_ready", "send_authorized")
        self.assertFalse(blocked.allowed)
        resumed = pin_fold(DIGEST_A, DIGEST_B)
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(digest_grants_send())
        self.assertFalse(fold_grants_send())
        self.assertFalse(hashes_body())
        self.assertFalse(invents_third_digest())

    def test_recovery_does_not_hash_a_body(self):
        d = admit_digest(DIGEST_A)
        self.assertTrue(d.allowed)
        self.assertFalse(hashes_body())
        self.assertFalse(invents_third_digest())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_digest("campaign_envelope_ready")
        sent = admit_digest("quote_sent")
        auth = admit_digest("send_authorized")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(digest_ready_is_authorized())
        self.assertFalse(fold_ready_is_authorized())
        self.assertNotEqual(ready.digest, auth.digest)
        folded = pin_fold("campaign_envelope_ready", "send_authorized")
        self.assertFalse(folded.allowed)
        self.assertEqual(folded.reason, "sealed_effect")


if __name__ == "__main__":
    unittest.main()
