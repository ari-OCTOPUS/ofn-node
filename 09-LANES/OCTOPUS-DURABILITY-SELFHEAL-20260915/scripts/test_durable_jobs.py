#!/usr/bin/env python3
"""Fixture tests for durable_jobs — OPT2 §7.3 (lease expiry / heartbeat / replay / DLQ /
closure) and §5 fault-injection (kill, crash-after-PERSISTED, fsync-fail).

Run: python3 test_durable_jobs.py   (stdlib unittest; exit 0 = all green)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import durable_jobs as dj  # noqa: E402

_NOW = 1_800_000_000.0  # fixed clock
_SEQ = iter(range(1, 10000))
NOW = _NOW


def row(state, lease_expiry=_NOW - 999, attempt=0, **kw):
    r = {"job_id": f"job-test-{next(_SEQ)}", "state": state, "attempt": attempt,
         "idempotency_key": "idem-1", "ts": _NOW - 999, "lease_expiry": lease_expiry}
    r.update(kw)
    return r


class TestContract(unittest.TestCase):
    def test_healthy_leased_no_transition(self):
        r = row("LEASED", lease_expiry=NOW + 60, heartbeat_at=NOW - 5, owner_pid=os.getpid())
        self.assertIsNone(dj.evaluate(r, NOW))

    def test_lease_expiry_no_heartbeat_reclaims_to_queued(self):
        r = row("LEASED", lease_expiry=NOW - 10, owner_pid=None)
        t = dj.evaluate(r, NOW)
        self.assertEqual((t["from"], t["to"], t["why"]),
                         ("LEASED", "QUEUED", "LEASE_EXPIRED_RECLAIMED"))

    def test_max_receive_goes_to_dlq_not_loop(self):
        r = row("LEASED", lease_expiry=NOW - 10, attempt=3, owner_pid=None)
        t = dj.evaluate(r, NOW)
        self.assertEqual(t["to"], "DLQ")
        self.assertIn("max receives", t["why"])

    def test_running_owner_alive_is_left_alone(self):
        r = row("RUNNING", lease_expiry=NOW - 10, heartbeat_at=NOW - 3,
                owner_pid=os.getpid())
        self.assertIsNone(dj.evaluate(r, NOW))

    def test_persisted_fresh_no_transition(self):
        r = row("PERSISTED", ts=NOW - 60)
        self.assertIsNone(dj.evaluate(r, NOW))

    def test_persisted_stuck_retry_once_then_failed(self):
        r = row("PERSISTED", ts=NOW - dj.CLOSURE_TTL_S - 10)
        t1 = dj.evaluate(r, NOW)
        self.assertEqual(t1["why"], "CLOSURE_RETRY_ONCE")
        self.assertEqual(t1["to"], "PERSISTED")
        r2 = dict(r, closure_retry_at=NOW - 10)
        t2 = dj.evaluate(r2, NOW)
        self.assertEqual((t2["to"], t2["why"]), ("FAILED", "CLOSE_UNCONFIRMED"))

    def test_unknown_gets_disposition_not_parked(self):
        t = dj.evaluate(row("UNKNOWN"), NOW)
        self.assertEqual((t["to"], t["why"]), ("FAILED", "UNKNOWN_DISPOSITION_REQUIRED"))

    def test_terminal_rows_untouched(self):
        for s in dj.TERMINAL:
            self.assertIsNone(dj.evaluate(row(s), NOW))

    def test_state_machine_allowed_shape(self):
        # every transition the reaper can emit is in the ALLOWED graph
        cases = [row("LEASED", attempt=0), row("LEASED", attempt=3),
                 row("PERSISTED", ts=NOW - dj.CLOSURE_TTL_S - 1),
                 row("UNKNOWN")]
        for c in cases:
            t = dj.evaluate(c, NOW)
            if t:
                self.assertIn(t["to"], dj.ALLOWED[t["from"]])


class TestIdempotency(unittest.TestCase):
    def test_replay_has_exactly_one_final_effect(self):
        with tempfile.TemporaryDirectory() as d:
            reg = dj.IdempotencyRegistry(Path(d) / "idem.jsonl")
            self.assertTrue(reg.register("k1", "SENT"))
            self.assertFalse(reg.register("k1", "SENT_AGAIN"))  # replay blocked
            self.assertEqual(reg.outcome_of("k1"), "SENT")
            # crash + reload: registry still knows k1 (durable)
            reg2 = dj.IdempotencyRegistry(Path(d) / "idem.jsonl")
            self.assertFalse(reg2.register("k1", "AFTER_CRASH"))

    def test_crash_after_persisted_before_ack(self):
        # scenario: worker persisted result, died before ack; replay must not duplicate
        with tempfile.TemporaryDirectory() as d:
            reg = dj.IdempotencyRegistry(Path(d) / "idem.jsonl")
            reg.register("idem-9", "PERSISTED:resultsha")
            # on replay the consumer asks the registry first:
            duplicated = reg.register("idem-9", "PERSISTED:resultsha")
            self.assertFalse(duplicated)  # -> consumer sees prior outcome, skips effect


class TestLedgerFaults(unittest.TestCase):
    def test_fsync_fail_aborts_not_swallows(self):
        with tempfile.TemporaryDirectory() as d:
            ledger_path = Path(d) / "transitions.jsonl"
            ledger = dj.TransitionsLedger(ledger_path)
            ledger.append({"x": 1})
            # fault injection: the ledger FILE itself read-only (open must fail)
            os.chmod(ledger_path, 0o400)
            try:
                with self.assertRaises(OSError):
                    ledger.append({"x": 2})  # must raise, never silent
            finally:
                os.chmod(ledger_path, 0o640)

    def test_process_kill_returns_job_to_queued(self):
        # kill simulation: owner pid = a dead process (spawn+reap a child)
        pid = os.fork()
        if pid == 0:
            os._exit(0)
        os.waitpid(pid, 0)                     # child now dead
        r = row("RUNNING", lease_expiry=NOW - 1, owner_pid=pid, heartbeat_at=NOW - 999)
        t = dj.evaluate(r, NOW)
        self.assertEqual((t["to"], t["why"]), ("QUEUED", "LEASE_EXPIRED_RECLAIMED"))


class TestReapDryRun(unittest.TestCase):
    def test_dry_run_touches_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [row("LEASED", attempt=0), row("CLOSED")]
            ledger = dj.TransitionsLedger(Path(d) / "t.jsonl")
            ts = dj.reap(rows, ledger=ledger, now=NOW, apply=False)
            self.assertEqual(len(ts), 1)
            self.assertEqual(ts[0]["to"], "QUEUED")
            # ledger never created/written in dry-run
            self.assertFalse(Path(d, "t.jsonl").exists())

    def test_apply_writes_append_only_and_reconciles(self):
        with tempfile.TemporaryDirectory() as d:
            rows = [row("LEASED", attempt=0), row("UNKNOWN")]
            ledger = dj.TransitionsLedger(Path(d) / "t.jsonl")
            ts1 = dj.reap(rows, ledger=ledger, now=NOW, apply=True)
            self.assertEqual(len(ts1), 2)                     # LEASED->QUEUED + UNKNOWN->FAILED
            # reconcile into derived view, then re-evaluate: nothing re-emitted
            derived = dj.apply_transitions(rows, ts1)
            ts2 = dj.reap(derived, ledger=ledger, now=NOW, apply=True)
            self.assertEqual(len(ts2), 0)
            self.assertEqual(Path(d, "t.jsonl").read_text().count("\n"), 2)  # append-only


if __name__ == "__main__":
    unittest.main(verbosity=1)
