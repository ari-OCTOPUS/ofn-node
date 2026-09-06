"""Kernel-pure arm isolate — one timeout parks one arm; others continue.

Independent of ``run_store.py`` / ``source_health.py`` (owned by open
PRs). HALT stops STARTS, not in-flight isolation. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.arm_isolate import (
    PARKED,
    RUNNING,
    UNKNOWN,
    ArmIndex,
    grants_send,
    halt_blocks_isolate,
    timeout_is_not_a_second_writer,
    unpark_without_owner,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.timeout_verdict import COMPLETED, TIMEOUT


class UnseenIsUnknownNotParked(unittest.TestCase):
    def test_fresh_index_is_unknown(self):
        idx = ArmIndex()
        self.assertEqual(idx.status("planner"), UNKNOWN)
        self.assertTrue(idx.continue_eligible("planner"))
        self.assertEqual(len(idx), 0)
        self.assertEqual(idx.replay(), ())

    def test_unknown_is_not_false_and_not_parked(self):
        idx = ArmIndex()
        self.assertNotEqual(idx.status("research"), PARKED)
        self.assertNotEqual(idx.status("research"), "FALSE")


class TimeoutParksOnlyThatArm(unittest.TestCase):
    def test_note_timeout_latches_park(self):
        idx = ArmIndex()
        self.assertEqual(idx.note_timeout("planner"), PARKED)
        self.assertEqual(idx.status("planner"), PARKED)
        self.assertFalse(idx.continue_eligible("planner"))
        # progress after park does not unpark
        self.assertEqual(idx.note_progress("planner"), PARKED)
        self.assertEqual(idx.status("planner"), PARKED)

    def test_others_remain_eligible(self):
        idx = ArmIndex()
        idx.note_progress("research")
        idx.note_progress("builder")
        idx.note_timeout("planner")
        kept = idx.others_continue(
            "planner", ("planner", "research", "builder", "validator"))
        self.assertEqual(kept, ("research", "builder", "validator"))
        self.assertEqual(idx.status("research"), RUNNING)
        self.assertEqual(idx.status("builder"), RUNNING)
        self.assertEqual(idx.status("validator"), UNKNOWN)
        self.assertTrue(idx.continue_eligible("validator"))

    def test_others_continue_is_read_only(self):
        idx = ArmIndex()
        before = idx.replay()
        kept = idx.others_continue("planner", ("research",))
        self.assertEqual(kept, ("research",))
        self.assertEqual(idx.replay(), before)
        self.assertEqual(idx.status("planner"), UNKNOWN)
        self.assertEqual(len(idx), 0)


class ClassifiedTimeoutParks(unittest.TestCase):
    def test_overrun_parks_and_completed_does_not(self):
        idx = ArmIndex()
        self.assertEqual(
            idx.note_classified(
                "planner", elapsed_s=10, budget_s=10, completed=False),
            PARKED,
        )
        self.assertEqual(
            idx.note_classified(
                "research", elapsed_s=3, budget_s=10, completed=True),
            COMPLETED,
        )
        self.assertEqual(idx.status("research"), RUNNING)
        self.assertEqual(idx.status("planner"), PARKED)

    def test_timeout_constant_matches_classifier(self):
        self.assertEqual(TIMEOUT, "TIMEOUT")


class UnparkIsRefused(unittest.TestCase):
    def test_unpark_fails_closed(self):
        idx = ArmIndex()
        idx.note_timeout("planner")
        with self.assertRaises(FailClosedError):
            idx.unpark("planner")
        self.assertEqual(idx.status("planner"), PARKED)
        self.assertFalse(unpark_without_owner())


class SealedAndMalformed(unittest.TestCase):
    def test_sealed_arm_name_refused(self):
        idx = ArmIndex()
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    idx.note_timeout(name)

    def test_empty_and_non_str_arm_refused(self):
        idx = ArmIndex()
        for bad in ("", "   ", None, 1, True):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    idx.status(bad)

    def test_roster_must_be_a_sequence(self):
        idx = ArmIndex()
        with self.assertRaises(FailClosedError):
            idx.others_continue("planner", {"research"})  # type: ignore[arg-type]


class PeekAndReplayDoNotWrite(unittest.TestCase):
    def test_peek_equals_status_and_does_not_create(self):
        idx = ArmIndex()
        self.assertEqual(idx.peek_status("planner"), UNKNOWN)
        self.assertEqual(len(idx), 0)

    def test_replay_is_note_order(self):
        idx = ArmIndex()
        idx.note_progress("research")
        idx.note_timeout("planner")
        self.assertEqual(
            idx.replay(),
            (("research", RUNNING), ("planner", PARKED)),
        )


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_isolate(self):
        self.assertFalse(halt_blocks_isolate())
        params = inspect.signature(ArmIndex.note_timeout).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        idx = ArmIndex()
        idx.note_timeout("planner")
        self.assertEqual(idx.status("planner"), PARKED)

    def test_timeout_is_not_a_second_writer(self):
        self.assertFalse(timeout_is_not_a_second_writer())


if __name__ == "__main__":
    unittest.main()
