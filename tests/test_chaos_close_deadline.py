"""Owner-absent chaos — close + deadline, without touching #82's file.

Scenario 6/7 companions: HALT is not a parameter here (it stops STARTS).
A closed or expired run does not stop a sibling arm. Recovery is a new
run_id. Ready ≠ authorized.
"""

from __future__ import annotations

import unittest

from ofn.kernel.close_gate import CloseGate, halt_blocks_close
from ofn.kernel.deadline_window import DeadlineIndex, halt_blocks_deadline
from ofn.kernel.errors import FailClosedError

_NOW = 1_780_000_000
_DEADLINE = 1_780_000_100
_RUN_A = "run-1780000000-a1b2c3d4e5f6a7b8"
_RUN_B = "run-1780000000-b1b2c3d4e5f6a7b8"
_RUN_C = "run-1780000001-c1b2c3d4e5f6a7b8"


class ScenarioCloseDoesNotHaltSiblings(unittest.TestCase):
    def test_closed_arm_refuses_while_siblings_append(self):
        gate = CloseGate()
        for rid in (_RUN_A, _RUN_B, _RUN_C):
            gate.note_open(rid)
        gate.note_closed(_RUN_A, ref="evt-deadarm00000000")
        with self.assertRaises(FailClosedError):
            gate.refuse_append(_RUN_A)
        gate.refuse_append(_RUN_B)
        gate.refuse_append(_RUN_C)
        self.assertTrue(gate.may_append(_RUN_B))
        self.assertTrue(gate.may_append(_RUN_C))

    def test_recovery_closes_then_starts_a_new_id(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_closed(_RUN_A)
        with self.assertRaises(FailClosedError):
            gate.note_open(_RUN_A)  # same id is not recovery
        self.assertTrue(gate.note_open(_RUN_B))
        self.assertNotEqual(_RUN_A, _RUN_B)


class ScenarioDeadlineExpiresOneArmOnly(unittest.TestCase):
    def test_equal_deadline_parks_that_run_only(self):
        idx = DeadlineIndex()
        idx.bind(_RUN_A, _NOW)          # equal at _NOW → closed
        idx.bind(_RUN_B, _DEADLINE)     # still open
        with self.assertRaises(FailClosedError):
            idx.refuse_if_closed(_RUN_A, _NOW)
        idx.refuse_if_closed(_RUN_B, _NOW)
        self.assertTrue(idx.is_open(_RUN_B, _NOW))
        self.assertFalse(idx.is_open(_RUN_A, _NOW))


class HaltDoesNotBlockInFlight(unittest.TestCase):
    def test_close_and_deadline_have_no_halt_switch(self):
        self.assertFalse(halt_blocks_close())
        self.assertFalse(halt_blocks_deadline())
        gate = CloseGate()
        idx = DeadlineIndex()
        gate.note_open(_RUN_A)
        idx.bind(_RUN_A, _DEADLINE)
        gate.note_closed(_RUN_A)
        idx.refuse_if_closed(_RUN_A, _NOW)
        self.assertTrue(gate.is_closed(_RUN_A))
        self.assertTrue(idx.is_open(_RUN_A, _NOW))


if __name__ == "__main__":
    unittest.main()
