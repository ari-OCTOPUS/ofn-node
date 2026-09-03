"""Owner-absent Scenario 2: one arm times out; the others continue.

Complementary hole: a hung agent is TIMEOUT / PARKED for *that* arm.
It is not FALSE, not a concurrent-write proof, and not a global HALT.
Timeout is not used as evidence of a second body.

Independent of ``tests/test_chaos_owner_absent.py`` (owned by an open PR)
and of ``tests/test_chaos_source_health.py`` (owned by another).
"""

from __future__ import annotations

import unittest

from ofn.kernel.arm_isolate import (
    PARKED,
    RUNNING,
    UNKNOWN,
    ArmIndex,
    grants_send,
    halt_blocks_isolate,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.timeout_verdict import (
    TIMEOUT,
    classify_progress,
    concurrent_write_from_timeout,
    timeout_proves_concurrent_write,
)


ROSTER = ("planner", "research", "builder", "validator",
          "memory", "operations", "commerce", "truth")


class Scenario2TimeoutIsolatesOneArm(unittest.TestCase):
    def test_one_timeout_does_not_stop_the_roster(self):
        idx = ArmIndex()
        for arm in ROSTER:
            idx.note_progress(arm)
        verdict = classify_progress(
            elapsed_s=30, budget_s=10, completed=False)
        self.assertEqual(verdict, TIMEOUT)
        idx.note_timeout("research")
        kept = idx.others_continue("research", ROSTER)
        self.assertEqual(
            kept,
            ("planner", "builder", "validator",
             "memory", "operations", "commerce", "truth"),
        )
        self.assertEqual(idx.status("research"), PARKED)
        for arm in kept:
            self.assertEqual(idx.status(arm), RUNNING)
            self.assertTrue(idx.continue_eligible(arm))

    def test_two_timeouts_still_leave_the_rest(self):
        idx = ArmIndex()
        idx.note_timeout("planner")
        idx.note_timeout("commerce")
        kept = idx.others_continue("planner", ROSTER)
        self.assertNotIn("planner", kept)
        self.assertNotIn("commerce", kept)
        self.assertIn("research", kept)
        self.assertIn("truth", kept)


class ScenarioTimeoutIsNotConcurrentWrite(unittest.TestCase):
    def test_elapsed_budget_is_not_a_second_body(self):
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(concurrent_write_from_timeout(TIMEOUT))
        idx = ArmIndex()
        idx.note_timeout("planner")
        # Isolation recorded one park. That is not evidence another
        # worktree is writing. UNKNOWN about a second body stands.
        self.assertEqual(idx.status("builder"), UNKNOWN)
        self.assertTrue(idx.continue_eligible("builder"))


class ScenarioHaltDoesNotFreezeInFlightIsolation(unittest.TestCase):
    def test_note_timeout_has_no_halt_switch(self):
        self.assertFalse(halt_blocks_isolate())
        idx = ArmIndex()
        idx.note_timeout("planner")
        idx.note_progress("research")
        self.assertEqual(idx.status("planner"), PARKED)
        self.assertEqual(idx.status("research"), RUNNING)
        self.assertFalse(grants_send())


class ScenarioUnparkNeedsOwner(unittest.TestCase):
    def test_recovery_without_owner_cannot_unpark(self):
        idx = ArmIndex()
        idx.note_timeout("planner")
        with self.assertRaises(FailClosedError):
            idx.unpark("planner")
        # Other arms still continue; the parked one stays parked.
        self.assertEqual(
            idx.others_continue("planner", ("planner", "research")),
            ("research",),
        )
        self.assertEqual(idx.status("planner"), PARKED)


if __name__ == "__main__":
    unittest.main()
