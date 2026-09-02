"""Contract tests for the run store + halt flag (P1 skeleton).

The promises checked here are the blueprint's P1 exit conditions:
append-only, append-after-close rejected (also after reopen), replay with
no second effect, one verdict → one budget effect, and a kill switch that
can go RED (a gate that cannot fail is a decoration).
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel import events as ev
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError

_NOW = 1780000000
_AC = hashlib.sha256(b"acceptance: fixture").hexdigest()


def _env(key: str = "idem-1", *, rand: str = "a1b2c3d4e5f6a7b8"):
    return create_envelope(
        goal="fixture goal", risk_tier="GREEN", authority_level="A1",
        idempotency_key=key, acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=rand, deadline_iso="2026-09-09T12:00:00Z")


class HaltBehaviour(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.flag = Path(self._tmp.name) / "halt.flag"
        self.addCleanup(self._tmp.cleanup)

    def test_absent_flag_means_running(self):
        self.assertFalse(halt_flag.halt_flag_active(self.flag))

    def test_armed_flag_halts(self):
        halt_flag.write_halt(self.flag)
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_corrupt_flag_halts_fail_closed(self):
        self.flag.write_text("maybe??", encoding="utf-8")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_empty_flag_file_halts(self):
        self.flag.write_text("", encoding="utf-8")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))

    def test_explicit_off_word_means_running(self):
        self.flag.write_text("off", encoding="utf-8")
        self.assertFalse(halt_flag.halt_flag_active(self.flag))

    def test_clear_requires_an_armed_flag(self):
        with self.assertRaises(FailClosedError):
            halt_flag.clear_halt(self.flag)  # stray clear is not an owner decision

    def test_write_then_clear_resumes(self):
        halt_flag.write_halt(self.flag)
        halt_flag.clear_halt(self.flag)
        self.assertFalse(halt_flag.halt_flag_active(self.flag))


class EventVocabulary(unittest.TestCase):
    def test_nine_kinds_fixed(self):
        self.assertEqual(len(ev.EVENT_KINDS), 9)

    def test_unknown_kind_refused(self):
        with self.assertRaises(FailClosedError):
            ev.make_event("SOMETHING_ELSE", "run-x", now_epoch_s=_NOW)

    def test_budget_debit_without_ref_refused_at_construction(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(ev.BUDGET_DEBIT, "run-x", now_epoch_s=_NOW)


class StoreLifecycle(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.store = RunStore(self.root / "runs")

    def test_create_append_close(self):
        env = _env()
        run_id = self.store.create(env, now_epoch_s=_NOW)
        self.store.append(ev.make_event(
            ev.PROPOSAL_CREATED, run_id, now_epoch_s=_NOW + 1,
            payload={"what": "draft"}))
        self.store.close(run_id, now_epoch_s=_NOW + 2)
        kinds = [e["kind"] for e in self.store.events_for(run_id)]
        self.assertEqual(kinds, [ev.RUN_CREATED, ev.PROPOSAL_CREATED, ev.RUN_CLOSED])

    def test_append_after_close_rejected(self):
        run_id = self.store.create(_env(), now_epoch_s=_NOW)
        self.store.close(run_id, now_epoch_s=_NOW + 1)
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.POLICY_DECISION, run_id, now_epoch_s=_NOW + 2))

    def test_after_close_rejection_survives_reopen(self):
        run_id = self.store.create(_env(), now_epoch_s=_NOW)
        self.store.close(run_id, now_epoch_s=_NOW + 1)
        reopened = RunStore(self.root / "runs")
        with self.assertRaises(FailClosedError):
            reopened.append(ev.make_event(
                ev.POLICY_DECISION, run_id, now_epoch_s=_NOW + 2))

    def test_duplicate_idempotency_collapses_to_one_run(self):
        a = self.store.create(_env("same-key"), now_epoch_s=_NOW)
        b = self.store.create(_env("same-key", rand="ffffffffffffffff"),
                              now_epoch_s=_NOW + 5)
        self.assertEqual(a, b)
        created = [e for e in self.store.replay() if e["kind"] == ev.RUN_CREATED]
        self.assertEqual(len(created), 1)

    def test_unknown_run_rejected(self):
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.TOOL_INVOKED, "run-1780000000-notregistered00",
                now_epoch_s=_NOW))

    def test_halted_create_writes_nothing(self):
        with self.assertRaises(HaltActive):
            self.store.create(_env("halted-key"), halted=True, now_epoch_s=_NOW)
        self.assertEqual(list(self.store.replay()), [])
        # and the idempotency key was NOT burned: a later create works
        run_id = self.store.create(_env("halted-key"), now_epoch_s=_NOW)
        self.assertTrue(run_id)

    def test_run_created_only_via_create(self):
        run_id = self.store.create(_env(), now_epoch_s=_NOW)
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.RUN_CREATED, run_id, now_epoch_s=_NOW + 1,
                payload={"idempotency_key": "idem-1"}))


class OneVerdictOneBudgetEffect(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.store = RunStore(self.root / "runs")
        self.run_id = self.store.create(_env(), now_epoch_s=_NOW)

    def _receipt(self) -> str:
        return self.store.append(ev.make_event(
            ev.EXECUTION_RECEIPT, self.run_id, now_epoch_s=_NOW + 1,
            payload={"what": "fixture receipt"}))

    def test_debit_requires_a_real_receipt(self):
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.BUDGET_DEBIT, self.run_id, now_epoch_s=_NOW + 2,
                ref="evt-doesnotexist0000"))

    def test_second_debit_against_same_receipt_refused(self):
        receipt = self._receipt()
        self.store.append(ev.make_event(
            ev.BUDGET_DEBIT, self.run_id, now_epoch_s=_NOW + 2, ref=receipt))
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.BUDGET_DEBIT, self.run_id, now_epoch_s=_NOW + 3, ref=receipt))

    def test_rule_survives_reopen(self):
        receipt = self._receipt()
        self.store.append(ev.make_event(
            ev.BUDGET_DEBIT, self.run_id, now_epoch_s=_NOW + 2, ref=receipt))
        reopened = RunStore(self.root / "runs")
        with self.assertRaises(FailClosedError):
            reopened.append(ev.make_event(
                ev.BUDGET_DEBIT, self.run_id, now_epoch_s=_NOW + 3, ref=receipt))


class ReplayIsReadOnly(unittest.TestCase):
    def test_replay_never_writes_and_never_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env(), now_epoch_s=_NOW)
            store.append(ev.make_event(
                ev.PROPOSAL_CREATED, run_id, now_epoch_s=_NOW + 1))
            log = root / "events.jsonl"
            size_before = log.stat().st_size
            first = list(store.replay())
            second = list(store.replay())
            self.assertEqual(first, second)
            self.assertEqual(log.stat().st_size, size_before)
            # a brand-new instance over the same file replays identically
            self.assertEqual(list(RunStore(root).replay()), first)


if __name__ == "__main__":
    unittest.main()
