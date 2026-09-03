"""HALT and owner-absent invariants that must hold on main.

Complementary to ``test_chaos_owner_absent.py`` / ``test_run_gate.py``
(those files are owned by open PRs). Layer-3 stops STARTS. In-flight
append+close stays possible so recovery does not need the owner.
401/404 stay UNKNOWN, not FALSE. Ready ≠ authorized.
"""

from __future__ import annotations

import hashlib
import inspect
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.run_gate import RunGate
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel import events as ev
from ofn.kernel import source_health as sh
from ofn.kernel.envelope import create_envelope
from tests.tmpdir import temp_dir

_NOW = 1780000000
_AC = hashlib.sha256(b"halt inflight fixture").hexdigest()


def _env(key: str, *, rand: str = "a1b2c3d4e5f6a7b8"):
    return create_envelope(
        goal="halt inflight fixture", risk_tier="GREEN",
        authority_level="A1", idempotency_key=key,
        acceptance_criteria_hash=_AC, now_epoch_s=_NOW, rand=rand,
        deadline_iso="2026-09-09T12:00:00Z")


class HaltStopsStartsNotInFlight(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.flag = self.root / "halt.flag"
        self.store = RunStore(self.root / "runs")
        self.gate = RunGate(self.store, self.flag)

    def test_halt_refuses_new_run_and_writes_no_rejection_event(self):
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            self.gate.start_run(_env("late"), now_epoch_s=_NOW)
        self.assertEqual(list(self.store.replay()), [])
        # RUN_REJECTED is a vocabulary slot, not a half-born run.
        self.assertNotIn(ev.RUN_REJECTED, ev.FORBIDDEN_EFFECT_KINDS)

    def test_in_flight_append_and_close_survive_halt(self):
        first = self.gate.start_run(_env("in-flight"), now_epoch_s=_NOW)
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            self.gate.start_run(_env("blocked", rand="c" * 16),
                                now_epoch_s=_NOW + 1)
        self.store.append(ev.make_event(
            ev.TOOL_INVOKED, first, now_epoch_s=_NOW + 2,
            payload={"arm": "in-flight"}))
        self.store.close(first, now_epoch_s=_NOW + 3)
        kinds = [e["kind"] for e in self.store.events_for(first)]
        self.assertEqual(
            kinds, [ev.RUN_CREATED, ev.TOOL_INVOKED, ev.RUN_CLOSED])
        created = [e for e in self.store.replay()
                   if e["kind"] == ev.RUN_CREATED]
        self.assertEqual(len(created), 1)

    def test_idempotency_key_not_burned_by_halted_start(self):
        env = _env("burn-check")
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            self.gate.start_run(env, now_epoch_s=_NOW)
        halt_flag.clear_halt(self.flag)
        run_id = self.gate.start_run(env, now_epoch_s=_NOW)
        self.assertEqual(run_id, env.run_id)


class RestartHasNoResendKnob(unittest.TestCase):
    def test_recover_after_restart_accepts_only_now_iso(self):
        params = inspect.signature(RunGate.recover_after_restart).parameters
        self.assertNotIn("resend", params)
        self.assertEqual(list(params), ["self", "now_iso"])


class FourOhOneAndFourOhFourAreUnknown(unittest.TestCase):
    def test_401_404_are_unknown_not_false_or_parked(self):
        self.assertEqual(sh.classify_fetch(401), sh.UNKNOWN)
        self.assertEqual(sh.classify_fetch(404), sh.UNKNOWN)
        self.assertNotEqual(sh.classify_fetch(401), "FALSE")
        self.assertNotEqual(sh.classify_fetch(404), sh.PARKED)
        self.assertNotEqual(sh.classify_fetch(401), sh.OK)


if __name__ == "__main__":
    unittest.main()
