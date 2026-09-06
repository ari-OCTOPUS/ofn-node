"""Adapter + RunGate wiring for the RUN_REJECTED side log.

Complementary to ``test_run_gate.py`` / ``test_chaos_owner_absent.py``
(those files stay owned by their existing coverage). A refused start
lands here, never in the run store, and never as a send.
"""

from __future__ import annotations

import hashlib
import os
import unittest
from pathlib import Path

from ofn.adapters.reject_log import RejectLog
from ofn.adapters.run_gate import RunGate
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.adapters import halt_flag
from ofn.kernel import events as ev
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.rejection import make_rejection
from tests.tmpdir import temp_dir

_NOW = 1780000000
_AC = hashlib.sha256(b"reject-log fixture").hexdigest()


def _env(key: str = "idem-log", *, rand: str = "a1b2c3d4e5f6a7b8"):
    return create_envelope(
        goal="reject-log fixture", risk_tier="GREEN", authority_level="A1",
        idempotency_key=key, acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=rand, deadline_iso="2026-09-09T12:00:00Z")


class RejectLogDurability(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.log = RejectLog(self.root / "rej")

    def _one(self, key: str = "k1"):
        env = _env(key)
        return make_rejection(
            run_id=env.run_id, reason="halt_active",
            now_epoch_s=_NOW, idempotency_key=env.idempotency_key), env

    def test_record_then_replay_round_trip(self):
        rec, env = self._one()
        rid = self.log.record(rec)
        self.assertTrue(rid.startswith("rej-"))
        rows = list(self.log.replay())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], ev.RUN_REJECTED)
        self.assertEqual(rows[0]["run_id"], env.run_id)
        self.assertEqual(rows[0]["payload"]["reason"], "halt_active")
        self.assertEqual(rows[0]["refusal_id"], rid)

    def test_reopen_replays_the_same_line(self):
        rec, env = self._one()
        rid = self.log.record(rec)
        again = RejectLog(self.root / "rej")
        rows = list(again.replay())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["refusal_id"], rid)
        self.assertEqual(rows[0]["run_id"], env.run_id)

    def test_file_is_0600_on_posix(self):
        if os.name == "nt":
            self.skipTest("POSIX file mode is not a Windows fact")
        self.log.record(self._one()[0])
        path = self.root / "rej" / "refusals.jsonl"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.root / "rej").stat().st_mode & 0o777, 0o700)

    def test_symlink_log_refused(self):
        target = self.root / "elsewhere"
        target.write_text("nope\n", encoding="utf-8")
        planted = self.root / "linkdir"
        planted.mkdir()
        (planted / "refusals.jsonl").symlink_to(target)
        with self.assertRaises(FailClosedError):
            RejectLog(planted)
        self.assertEqual(target.read_text(encoding="utf-8"), "nope\n")

    def test_non_rejection_kind_refused(self):
        env = _env("badkind")
        with self.assertRaises(FailClosedError):
            self.log.record(ev.make_event(
                ev.TOOL_INVOKED, env.run_id, now_epoch_s=_NOW,
                payload={"reason": "halt_active",
                         "idempotency_key": env.idempotency_key}))

    def test_sealed_payload_refused(self):
        env = _env("sealed")
        with self.assertRaises(FailClosedError):
            self.log.record({
                "kind": ev.RUN_REJECTED,
                "run_id": env.run_id,
                "ts": _NOW,
                "payload": {"reason": "halt_active",
                            "idempotency_key": "quote_sent"},
            })

    def test_grants_send_is_false(self):
        self.assertIs(self.log.grants_send_payload(), False)
        with self.assertRaises(FailClosedError):
            self.log.grants_send_payload({"next": "send_authorized"})


class GateWiresRejectLogWithoutTouchingRunStore(unittest.TestCase):
    def setUp(self):
        self.root = Path(temp_dir(self))
        self.flag = self.root / "halt.flag"
        self.store = RunStore(self.root / "runs")
        self.rej = RejectLog(self.root / "rej")
        self.gate = RunGate(self.store, self.flag, reject_log=self.rej)

    def test_halt_records_rejection_and_writes_no_run(self):
        env = _env("wired")
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            self.gate.start_run(env, now_epoch_s=_NOW)
        self.assertEqual(list(self.store.replay()), [])
        rows = list(self.rej.replay())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], ev.RUN_REJECTED)
        self.assertEqual(rows[0]["run_id"], env.run_id)
        self.assertEqual(rows[0]["payload"]["idempotency_key"],
                         env.idempotency_key)

    def test_unwired_gate_still_writes_nothing_to_either_ledger(self):
        bare = RunGate(self.store, self.flag)  # no reject_log
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            bare.start_run(_env("unwired"), now_epoch_s=_NOW)
        self.assertEqual(list(self.store.replay()), [])
        self.assertEqual(list(self.rej.replay()), [])

    def test_key_not_burned_after_recorded_refusal(self):
        env = _env("reburn")
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            self.gate.start_run(env, now_epoch_s=_NOW)
        halt_flag.clear_halt(self.flag)
        run_id = self.gate.start_run(env, now_epoch_s=_NOW)
        self.assertEqual(run_id, env.run_id)
        kinds = [e["kind"] for e in self.store.events_for(run_id)]
        self.assertEqual(kinds, [ev.RUN_CREATED])
        self.assertEqual(len(list(self.rej.replay())), 1)
        # the side log is not a run: RUN_REJECTED still cannot enter the store
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.RUN_REJECTED, run_id, now_epoch_s=_NOW + 1,
                payload={"reason": "halt_active",
                         "idempotency_key": env.idempotency_key}))

    def test_in_flight_append_survives_halt_with_log_wired(self):
        first = self.gate.start_run(_env("inflight"), now_epoch_s=_NOW)
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
        self.assertEqual(len(list(self.rej.replay())), 1)
        self.assertNotIn(ev.RUN_REJECTED,
                         [e["kind"] for e in self.store.replay()])

    def test_ready_is_not_authorized(self):
        env = _env("ready")
        halt_flag.write_halt(self.flag)
        with self.assertRaises(HaltActive):
            self.gate.start_run(env, now_epoch_s=_NOW)
        row = list(self.rej.replay())[0]
        for sealed in ev.FORBIDDEN_EFFECT_KINDS:
            self.assertNotEqual(row["kind"], sealed)
            self.assertNotIn(sealed, row["payload"])


if __name__ == "__main__":
    unittest.main()
