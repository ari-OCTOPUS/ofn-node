"""Owner-absent chaos — census-class composition (independent of #82 chaos).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These
scenarios lock the same seven rules at the inventory layer: no
store, no run_id mint, no fabricated witness. HALT is not a
census parameter. One arm's timeout cannot mark another arm
SUSPECTED. Recovery is observing a row and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.census_class import (
    admit_census,
    classify_timeout,
    grants_send,
    halt_blocks_census,
    prunes_worktree,
    ready_is_authorized,
    timeout_proves_concurrent,
)
from ofn.kernel.errors import FailClosedError


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_activity_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_census(
                path="/tmp/a", activity="DEAD_SOURCE", intended="observe")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_intended_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            admit_census(
                path="/tmp/a", activity="idle", intended="unknown_disk")
        self.assertNotIn("FALSE", str(ctx.exception))


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_observe(self):
        timed = admit_census(
            path="/tmp/arm-a", activity="idle", intended="observe",
            timed_out=True)
        self.assertEqual(timed.status, "UNKNOWN")
        self.assertTrue(timed.allowed)
        sibling = admit_census(
            path="/tmp/arm-b", activity="idle", intended="observe")
        self.assertTrue(sibling.allowed)
        self.assertEqual(sibling.status, "VERIFIED")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent())
        self.assertEqual(classify_timeout(), "UNKNOWN")
        d = admit_census(
            path="/tmp/a", activity="concurrent", intended="write",
            timed_out=True)
        self.assertEqual(d.status, "UNKNOWN")
        self.assertEqual(d.reason, "unknown_activity")
        self.assertNotEqual(d.reason, "suspected_concurrent")
        self.assertFalse(d.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_admit_observe(self):
        decisions = [
            admit_census(
                path=f"/tmp/arm-{arm}", activity="idle", intended="observe")
            for arm in ("a", "b", "c")
        ]
        self.assertEqual(len(decisions), 3)
        for d in decisions:
            self.assertTrue(d.allowed)
            self.assertEqual(d.status, "VERIFIED")
            self.assertFalse(d.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_admit_is_not_a_send(self):
        first = admit_census(
            path="/tmp/a", activity="idle", intended="observe")
        second = admit_census(
            path="/tmp/a", activity="idle", intended="observe")
        self.assertEqual(first, second)
        self.assertTrue(first.allowed)
        self.assertFalse(first.grants_send)
        self.assertFalse(grants_send())


class Scenario5SealedNameStopsThatRowOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_observe_continues(self):
        sealed = admit_census(
            path="send_authorized", activity="idle", intended="write")
        self.assertFalse(sealed.allowed)
        self.assertEqual(sealed.reason, "sealed_effect")
        sibling = admit_census(
            path="/tmp/arm-b", activity="idle", intended="observe")
        self.assertTrue(sibling.allowed)
        self.assertFalse(sibling.grants_send)


class Scenario6GlobalHaltIsNotACensusParameter(unittest.TestCase):
    def test_halt_does_not_block_inventory(self):
        self.assertFalse(halt_blocks_census())
        for arm in ("a", "b", "c"):
            d = admit_census(
                path=f"/tmp/arm-{arm}", activity="idle", intended="observe")
            self.assertTrue(d.allowed)
            self.assertFalse(d.grants_send)

    def test_no_halt_knob_to_rearm_send(self):
        import inspect
        params = inspect.signature(admit_census).parameters
        self.assertNotIn("halt", params)
        self.assertNotIn("halt_raw", params)


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_resume_is_an_observe_and_not_a_send(self):
        blocked = admit_census(
            path="quote_sent", activity="idle", intended="write")
        self.assertFalse(blocked.allowed)
        resumed = admit_census(
            path="/tmp/recovery", activity="idle", intended="observe")
        self.assertTrue(resumed.allowed)
        self.assertFalse(resumed.grants_send)
        self.assertFalse(grants_send())

    def test_prune_is_never_recovery(self):
        d = admit_census(
            path="/tmp/stale", activity="idle", intended="prune")
        self.assertFalse(d.allowed)
        self.assertEqual(d.reason, "prune_forbidden")
        self.assertFalse(prunes_worktree())


class ReadyNeverEqualsAuthorized(unittest.TestCase):
    def test_campaign_ready_and_send_authorized_are_both_sealed(self):
        ready = admit_census(
            path="campaign_envelope_ready", activity="idle",
            intended="observe")
        sent = admit_census(
            path="quote_sent", activity="idle", intended="observe")
        auth = admit_census(
            path="send_authorized", activity="idle", intended="observe")
        for d in (ready, sent, auth):
            self.assertFalse(d.allowed)
            self.assertEqual(d.reason, "sealed_effect")
            self.assertFalse(d.grants_send)
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual(ready.path, auth.path)


if __name__ == "__main__":
    unittest.main()
