"""Owner-absent chaos — token-class + spend-fence (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the token-budget layer:
no store, no run_id mint, no fabricated witness. HALT is not a
classify or fence parameter. One arm's timeout cannot mark
another arm as a race. Recovery is observing a FIT and is
still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.spend_fence import (
    admit_spend,
    classify_timeout as fence_timeout,
    grants_send as fence_grants_send,
    halt_blocks_fence,
    ready_is_authorized as fence_ready,
)
from ofn.kernel.token_class import (
    classify_timeout,
    classify_token,
    grants_send,
    halt_blocks_token,
    ready_is_authorized,
    timeout_proves_concurrent,
)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_token(
                per_run=True, node=True, intended="classify",
                activity="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_fence_verdict_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_spend(
                intended="observe", activity="idle", verdict="DEAD_SOURCE")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_classify(self):
        timed = classify_token(
            per_run=True, node=True, intended="classify",
            activity="idle", timed_out=True)
        self.assertTrue(timed.timed_out)
        self.assertFalse(timed.allowed)
        self.assertEqual(classify_timeout(), "UNKNOWN")
        sibling = classify_token(
            per_run=False, node=False, intended="classify",
            activity="idle")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.timed_out)
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_spend(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = classify_token(
            per_run=True, node=True, intended="classify",
            activity="concurrent", timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_classify(self):
        decisions = [
            classify_token(
                per_run=per_run, node=node, intended="classify",
                activity="idle")
            for per_run, node in ((True, True), (False, False), (True, False))
        ]
        self.assertEqual(len(decisions), 3)
        self.assertEqual(
            [d.verdict for d in decisions], ["FIT", "MISS", "SPLIT"])
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_classify_is_not_a_send(self):
        first = classify_token(
            per_run=True, node=True, intended="classify", activity="idle")
        second = classify_token(
            per_run=True, node=True, intended="classify", activity="idle")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())

    def test_second_identical_observe_is_not_a_send(self):
        first = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        second = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        self.assertEqual(first, second)
        self.assertFalse(first.grants_send)
        self.assertFalse(fence_grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_observe_continues(self):
        with self.assertRaises(FailClosedError):
            classify_token(
                per_run=True, node=True, intended="send_authorized",
                activity="idle")
        sibling = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotAClassifyParameter(unittest.TestCase):
    def test_halt_does_not_block_classify_or_fence(self):
        self.assertFalse(halt_blocks_token())
        self.assertFalse(halt_blocks_fence())
        d = classify_token(
            per_run=True, node=True, intended="classify", activity="idle")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        f = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        self.assertTrue(f.allowed)
        self.assertFalse(f.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        self.assertNotIn("halt", inspect.signature(classify_token).parameters)
        self.assertNotIn("halt", inspect.signature(admit_spend).parameters)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_an_observe_and_not_a_send(self):
        blocked = admit_spend(
            intended="promote_send", activity="idle", verdict="FIT")
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.reason, "promote_send_forbidden")
        resumed = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(fence_grants_send())
        self.assertEqual(fence_timeout(), "UNKNOWN")

    def test_quote_is_never_recovery(self):
        d = admit_spend(
            intended="quote", activity="idle", verdict="FIT")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "quote_forbidden")


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        for sealed in (
            "campaign_envelope_ready",
            "quote_sent",
            "send_authorized",
        ):
            with self.assertRaises(FailClosedError):
                classify_token(
                    per_run=True, node=True, intended=sealed,
                    activity="idle")
            with self.assertRaises(FailClosedError):
                admit_spend(
                    intended=sealed, activity="idle", verdict="FIT")
        self.assertFalse(ready_is_authorized())
        self.assertFalse(fence_ready())
        self.assertNotEqual(
            "campaign_envelope_ready", "send_authorized")

    def test_fit_observe_does_not_equal_send_authorized(self):
        d = admit_spend(
            intended="observe", activity="idle", verdict="FIT")
        self.assertTrue(d.allowed)
        self.assertFalse(d.grants_send)
        self.assertNotEqual(d.intended, "send_authorized")
        self.assertNotEqual(d.verdict, "send_authorized")


if __name__ == "__main__":
    unittest.main()
