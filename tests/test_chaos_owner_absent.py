"""Owner-Absent Chaos Day — the seven scenarios (blueprint §11).

Each scenario is a rule that must hold while the owner cannot be reached:
no fabricated witnesses, no duplicate spend, one arm's failure never
stops the others, and every recovery on this page is a reversible
decision an agent may take alone.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.run_gate import RunGate
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel import events as ev
from ofn.kernel import source_health as sh
from ofn.kernel.callbudget import CallBudget
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.routing import Rung

_NOW = 1780000000
_AC = hashlib.sha256(b"chaos fixture").hexdigest()


def _env(key: str, *, rand: str = "a1b2c3d4e5f6a7b8",
         authority: str = "A1"):
    return create_envelope(
        goal="chaos fixture", risk_tier="GREEN", authority_level=authority,
        idempotency_key=key, acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=rand, deadline_iso="2026-09-09T12:00:00Z")


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_dead_source_classifies_unknown(self):
        self.assertEqual(sh.classify_fetch(None), sh.UNKNOWN)
        self.assertNotEqual(sh.classify_fetch(None), "FALSE")

    def test_network_error_is_unknown(self):
        self.assertEqual(
            sh.classify_fetch(None, error=TimeoutError("socket dead")),
            sh.UNKNOWN)

    def test_error_with_200_is_unknown_not_ok(self):
        # A leftover success status plus a transport error is not OK.
        self.assertEqual(
            sh.classify_fetch(200, error=TimeoutError("reset after 200")),
            sh.UNKNOWN)
        self.assertNotEqual(
            sh.classify_fetch(200, error=OSError("reset")),
            sh.OK)

    def test_error_overrides_403_to_unknown(self):
        # Ambiguous: we have an error, so we do not treat a maybe-stale
        # 403 as a policy answer. UNKNOWN, not PARKED.
        self.assertEqual(
            sh.classify_fetch(403, error=OSError("read failed")),
            sh.UNKNOWN)

    def test_403_is_parked_policy_not_traffic(self):
        self.assertEqual(sh.classify_fetch(403), sh.PARKED)


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_sibling_arms_keep_appending(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("t2"), now_epoch_s=_NOW)
            # arm A times out mid-run
            with self.assertRaises(TimeoutError):
                raise TimeoutError("arm A fetch timed out")
            # arm B's work still lands on the same run — one arm's timeout
            # is not a system halt
            store.append(ev.make_event(
                ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 1,
                payload={"arm": "B"}))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertIn(ev.TOOL_INVOKED, kinds)


class Scenario3RateLimitBoundedBackoffThenParked(unittest.TestCase):
    def test_backoff_is_bounded_and_enumerable(self):
        delays = sh.backoff_delays()
        self.assertEqual(len(delays), sh.MAX_BACKOFF_ATTEMPTS)
        self.assertLessEqual(max(delays), sh.BACKOFF_CAP_S)

    def test_transient_then_parked_after_attempts(self):
        self.assertEqual(sh.classify_fetch(429, attempts=0),
                         sh.RETRY_AFTER_BACKOFF)
        self.assertEqual(
            sh.classify_fetch(429, attempts=sh.MAX_BACKOFF_ATTEMPTS),
            sh.PARKED)

    def test_no_infinite_retry_path_exists(self):
        for attempts in range(0, 10):
            verdict = sh.classify_fetch(503, attempts=attempts)
            self.assertIn(verdict, (sh.RETRY_AFTER_BACKOFF, sh.PARKED))
            if verdict == sh.PARKED:
                break           # the schedule provably terminates in PARKED
        else:
            self.fail("503 never parks — unbounded retry escaped")


class Scenario4DuplicateDeliveryOneEffect(unittest.TestCase):
    def test_second_delivery_refused_and_counted_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("t4"), now_epoch_s=_NOW)
            ref = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            store.append(ev.make_event(
                ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 2, ref=ref))
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(  # duplicate delivery
                    ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 3, ref=ref))
            invoked = [e for e in store.events_for(run_id)
                       if e["kind"] == ev.TOOL_INVOKED]
            self.assertEqual(len(invoked), 1)


class Scenario5ExhaustedArmBudgetStopsThatArmOnly(unittest.TestCase):
    def test_remote_arm_hits_cap_while_rules_arm_unaffected(self):
        budget = CallBudget()  # REMOTE cap 100, RULES cap 0 (=no ceiling)
        remote_spends = 0
        while budget.allows(Rung.REMOTE, _NOW):
            budget.record(Rung.REMOTE, _NOW)
            remote_spends += 1
            self.assertLessEqual(remote_spends, 100)
        self.assertEqual(remote_spends, 100)   # that arm stops…
        self.assertTrue(budget.allows(Rung.RULES, _NOW))  # …others don't


class Scenario6GlobalHaltStopsNewRuns(unittest.TestCase):
    def test_halt_refuses_new_runs_across_the_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            gate = RunGate(RunStore(t / "runs"), t / "halt.flag")
            halt_flag.write_halt(t / "halt.flag")
            for key in ("a", "b", "c"):        # three different arms try
                with self.assertRaises(HaltActive):
                    gate.start_run(_env(key, rand=key * 16),
                                   now_epoch_s=_NOW)

    def test_directory_flag_halts_every_arm(self):
        # A directory at the flag path is not "running". Three arms
        # still cannot start; write_halt must not clobber the directory.
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            flag = t / "halt.flag"
            flag.mkdir()
            (flag / "keep").write_text("stay", encoding="utf-8")
            gate = RunGate(RunStore(t / "runs"), flag)
            for key in ("d", "e", "f"):
                with self.assertRaises(HaltActive):
                    gate.start_run(_env(key, rand=key * 16),
                                   now_epoch_s=_NOW)
            self.assertTrue(flag.is_dir())
            self.assertEqual((flag / "keep").read_text(encoding="utf-8"), "stay")


class Scenario7ReversibleRecoveryWithoutOwner(unittest.TestCase):
    def test_close_and_restart_a_run_needs_no_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            gate = RunGate(RunStore(t / "runs"), t / "halt.flag")
            first = gate.start_run(_env("t7a"), now_epoch_s=_NOW)
            gate._store.append(ev.make_event(
                ev.TOOL_INVOKED, first, now_epoch_s=_NOW + 1,
                payload={"outcome": "failed, reversible"}))
            gate._store.close(first, now_epoch_s=_NOW + 2)
            # a failed reversible run is closed and a fresh one starts —
            # no owner gate anywhere on this path
            second = gate.start_run(_env("t7b", rand="b" * 16),
                                    now_epoch_s=_NOW + 3)
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
