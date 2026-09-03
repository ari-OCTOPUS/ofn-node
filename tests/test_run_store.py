"""Contract tests for the run store + halt flag (P1 skeleton).

The promises checked here are the blueprint's P1 exit conditions:
append-only, append-after-close rejected (also after reopen), replay with
no second effect, one verdict → one budget effect, and a kill switch that
can go RED (a gate that cannot fail is a decoration).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from ofn.adapters import halt_flag
from ofn.adapters.run_store import HaltActive, RunStore
from ofn.kernel import events as ev
from ofn.kernel.envelope import TaskEnvelope, create_envelope, mint_run_id
from ofn.kernel.errors import FailClosedError

_NOW = 1780000000
_AC = hashlib.sha256(b"acceptance: fixture").hexdigest()


def _env(key: str = "idem-1", *, rand: str = "a1b2c3d4e5f6a7b8",
         budget_tokens: int = 0, budget_aud_cents: int = 0,
         deadline_iso: str = "2026-09-09T12:00:00Z"):
    return create_envelope(
        goal="fixture goal", risk_tier="GREEN", authority_level="A1",
        idempotency_key=key, acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=rand, deadline_iso=deadline_iso,
        budget_tokens=budget_tokens, budget_aud_cents=budget_aud_cents)


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

    def test_non_utf8_flag_halts_instead_of_throwing(self):
        # A present flag that is not valid UTF-8 must HALT, not raise.
        self.flag.write_bytes(b"\xff\xfe not utf-8")
        self.assertTrue(halt_flag.halt_flag_active(self.flag))


class EventVocabulary(unittest.TestCase):
    def test_nine_kinds_fixed(self):
        self.assertEqual(len(ev.EVENT_KINDS), 9)

    def test_unknown_kind_refused(self):
        with self.assertRaises(FailClosedError):
            ev.make_event("SOMETHING_ELSE", "run-x", now_epoch_s=_NOW)

    def test_budget_debit_without_ref_refused_at_construction(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(ev.BUDGET_DEBIT, "run-x", now_epoch_s=_NOW)

    def test_forbidden_effect_kinds_are_not_in_the_vocabulary(self):
        for name in ev.FORBIDDEN_EFFECT_KINDS:
            self.assertNotIn(name, ev.EVENT_KINDS)
            with self.assertRaises(FailClosedError):
                ev.make_event(name, "run-x", now_epoch_s=_NOW)

    def test_payload_key_cannot_smuggle_a_sealed_effect(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.PROPOSAL_CREATED, "run-x", now_epoch_s=_NOW,
                payload={"quote_sent": "no"})

    def test_payload_value_cannot_smuggle_campaign_ready(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.POLICY_DECISION, "run-x", now_epoch_s=_NOW,
                payload={"next": "campaign_envelope_ready"})

    def test_nested_mapping_cannot_smuggle_quote_sent(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.PROPOSAL_CREATED, "run-x", now_epoch_s=_NOW,
                payload={"inner": {"next": "quote_sent"}})

    def test_nested_list_cannot_smuggle_send_authorized(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.POLICY_DECISION, "run-x", now_epoch_s=_NOW,
                payload={"states": ["draft", "send_authorized"]})


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

    def test_close_event_with_ref_still_closes(self):
        # Bugbot: _index used to skip RUN_CLOSED when ref was present, so
        # append-after-close was not structural for that path.
        run_id = self.store.create(_env("close-ref"), now_epoch_s=_NOW)
        self.store.append(ev.make_event(
            ev.RUN_CLOSED, run_id, now_epoch_s=_NOW + 1,
            ref="close-reason-1"))
        with self.assertRaises(FailClosedError):
            self.store.append(ev.make_event(
                ev.POLICY_DECISION, run_id, now_epoch_s=_NOW + 2))

    def test_close_with_ref_survives_reopen(self):
        run_id = self.store.create(_env("close-ref-reopen"), now_epoch_s=_NOW)
        self.store.append(ev.make_event(
            ev.RUN_CLOSED, run_id, now_epoch_s=_NOW + 1,
            ref="close-reason-2"))
        reopened = RunStore(self.root / "runs")
        with self.assertRaises(FailClosedError):
            reopened.append(ev.make_event(
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


class DuplicateDeliveryRejected(unittest.TestCase):
    def test_same_kind_and_ref_delivered_twice_second_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("dup-key"), now_epoch_s=_NOW)
            ref = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "once"}))
            store.append(ev.make_event(
                ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 2, ref=ref))
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(          # the duplicate delivery
                    ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 3, ref=ref))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertEqual(kinds.count(ev.TOOL_INVOKED), 1)  # one effect

    def test_rule_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("dup-key-2"), now_epoch_s=_NOW)
            ref = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            store.append(ev.make_event(
                ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 2, ref=ref))
            reopened = RunStore(root)
            with self.assertRaises(FailClosedError):
                reopened.append(ev.make_event(
                    ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 3, ref=ref))

class DeduplicationKeySemantics(unittest.TestCase):
    """Directive: same-id/different-payload, cross-run collision — the
    dedup keys are (a) envelope idempotency_key at create(), (b) the
    (kind, ref) pair for ref-carrying events, (c) receipt→run binding."""

    def test_same_idem_key_different_payload_collapses_to_one_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            a = store.create(_env("same"), now_epoch_s=_NOW)
            b = store.create(_env("same", rand="ffffffffffffffff"),
                             now_epoch_s=_NOW + 9)   # different rand → different run_id candidate
            self.assertEqual(a, b)
            created = [e for e in store.replay() if e["kind"] == ev.RUN_CREATED]
            self.assertEqual(len(created), 1)
            # the second submission's payload was NOT recorded anywhere
            self.assertNotIn("ffffffffffffffff",
                             json.dumps(created[0]))

    def test_cross_run_budget_debit_against_foreign_receipt_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_a = store.create(_env("run-a"), now_epoch_s=_NOW)
            run_b = store.create(_env("run-b", rand="b1b2c3d4e5f6a7b8"),
                                 now_epoch_s=_NOW)
            receipt_a = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_a, now_epoch_s=_NOW + 1))
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(     # run B settles run A's receipt
                    ev.BUDGET_DEBIT, run_b, now_epoch_s=_NOW + 2,
                    ref=receipt_a))

    def test_cross_run_duplicate_delivery_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_a = store.create(_env("run-a"), now_epoch_s=_NOW)
            run_b = store.create(_env("run-b", rand="b1b2c3d4e5f6a7b8"),
                                 now_epoch_s=_NOW)
            ref = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_a, now_epoch_s=_NOW + 1))
            store.append(ev.make_event(
                ev.TOOL_INVOKED, run_a, now_epoch_s=_NOW + 2, ref=ref))
            with self.assertRaises(FailClosedError):   # same (kind,ref), other run
                store.append(ev.make_event(
                    ev.TOOL_INVOKED, run_b, now_epoch_s=_NOW + 3, ref=ref))


class ReplayFailsClosedOnCorrupt(unittest.TestCase):
    def test_corrupt_line_on_replay_is_fail_closed_not_json_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env(), now_epoch_s=_NOW)
            log = root / "events.jsonl"
            with log.open("a", encoding="utf-8") as f:
                f.write("{not-json\n")
            with self.assertRaises(FailClosedError):
                list(store.replay())

    def test_corrupt_line_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env(), now_epoch_s=_NOW)
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write("{not-json\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)


class StoreRootIsOwnerPrivate(unittest.TestCase):
    def test_new_store_root_is_0700_on_posix(self):
        if os.name == "nt":
            self.skipTest("POSIX directory mode is not a Windows fact")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            RunStore(root)
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)


class PerRunTokenCeilingInStore(unittest.TestCase):
    def test_zero_budget_refuses_positive_token_debit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("tok-0"), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(
                    ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2,
                    ref=receipt, payload={"tokens": 1}))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertNotIn(ev.BUDGET_DEBIT, kinds)

    def test_ceiling_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("tok-10", budget_tokens=10),
                                  now_epoch_s=_NOW)
            r1 = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            store.append(ev.make_event(
                ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2,
                ref=r1, payload={"tokens": 8}))
            reopened = RunStore(root)
            r2 = reopened.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 3))
            with self.assertRaises(FailClosedError):
                reopened.append(ev.make_event(
                    ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 4,
                    ref=r2, payload={"tokens": 3}))  # 8+3 > 10

    def test_zero_token_debit_on_zero_budget_is_a_noop(self):
        # Missing `tokens` is 0 — a verdict can settle without a spend.
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("tok-noop"), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            eid = store.append(ev.make_event(
                ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2, ref=receipt))
            self.assertTrue(eid)


class SchemaFailClosedAndForbiddenKinds(unittest.TestCase):
    """Raw dicts must not smuggle unknown or send-state kinds into the
    ledger. Missing kind/run_id is FailClosedError, not KeyError."""

    def test_unknown_kind_refused_at_store_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("schema-unk"), now_epoch_s=_NOW)
            with self.assertRaises(FailClosedError):
                store.append({"kind": "NOT_A_KIND", "run_id": run_id,
                              "payload": {}, "ref": None})
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertEqual(kinds, [ev.RUN_CREATED])

    def test_send_authorized_kind_refused_at_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("schema-send"), now_epoch_s=_NOW)
            with self.assertRaises(FailClosedError):
                store.append({"kind": "send_authorized", "run_id": run_id,
                              "payload": {}, "ref": None})
            log = (root / "events.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("send_authorized", log)

    def test_quote_sent_kind_refused_at_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("schema-qs"), now_epoch_s=_NOW)
            with self.assertRaises(FailClosedError):
                store.append({"kind": "quote_sent", "run_id": run_id,
                              "payload": {}, "ref": None})

    def test_object_missing_kind_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("missing-kind"), now_epoch_s=_NOW)
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"run_id": "run-1780000000-aaaaaaaaaa",
                                    "payload": {}}) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_object_missing_run_id_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("missing-rid"), now_epoch_s=_NOW)
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"kind": ev.TOOL_INVOKED,
                                    "payload": {}}) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_events_jsonl_is_0600_on_posix(self):
        if os.name == "nt":
            self.skipTest("POSIX file mode is not a Windows fact")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("mode-600"), now_epoch_s=_NOW)
            mode = (root / "events.jsonl").stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)


class ReceiptIdentityAndRollbackPersist(unittest.TestCase):
    def test_receipt_sha256_is_stamped_from_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("rcpt-stamp"), now_epoch_s=_NOW)
            eid = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "fixture receipt"}))
            rec = next(e for e in store.events_for(run_id)
                       if e["event_id"] == eid)
            expected = hashlib.sha256(
                json.dumps({"what": "fixture receipt"},
                           ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            self.assertEqual(rec["payload"]["receipt_sha256"], expected)

    def test_forged_receipt_digest_refused_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("rcpt-forge"), now_epoch_s=_NOW)
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(
                    ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                    payload={"what": "x", "receipt_sha256": "0" * 64}))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertNotIn(ev.EXECUTION_RECEIPT, kinds)

    def test_matching_receipt_digest_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("rcpt-ok"), now_epoch_s=_NOW)
            digest = hashlib.sha256(
                json.dumps({"what": "ok"},
                           ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            eid = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "ok", "receipt_sha256": digest}))
            self.assertTrue(eid)

    def test_a3_rollback_ref_persisted_on_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            env = create_envelope(
                goal="fixture goal", risk_tier="RED", authority_level="A3",
                idempotency_key="a3-rb", acceptance_criteria_hash=_AC,
                now_epoch_s=_NOW, rand="c1c2c3d4e5f6a7b8",
                deadline_iso="2026-09-09T12:00:00Z",
                rollback_plan="delete drafts",
                rollback_ref="rb-20260902-persist")
            run_id = store.create(env, now_epoch_s=_NOW)
            created = next(e for e in store.events_for(run_id)
                           if e["kind"] == ev.RUN_CREATED)
            self.assertEqual(created["payload"]["rollback_ref"],
                             "rb-20260902-persist")
            self.assertEqual(created["payload"]["rollback_plan"],
                             "delete drafts")
            # survives reopen
            reopened = RunStore(Path(tmp) / "runs")
            again = next(e for e in reopened.events_for(run_id)
                         if e["kind"] == ev.RUN_CREATED)
            self.assertEqual(again["payload"]["rollback_ref"],
                             "rb-20260902-persist")


class AllowlistPersistAndToolGate(unittest.TestCase):
    def test_allowed_tools_persisted_and_survive_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            env = create_envelope(
                goal="fixture goal", risk_tier="GREEN", authority_level="A1",
                idempotency_key="allow-1", acceptance_criteria_hash=_AC,
                now_epoch_s=_NOW, rand="d1d2d3d4e5f6a7b8",
                deadline_iso="2026-09-09T12:00:00Z",
                allowed_tools=("score", "draft"))
            store = RunStore(root)
            run_id = store.create(env, now_epoch_s=_NOW)
            created = next(e for e in store.events_for(run_id)
                           if e["kind"] == ev.RUN_CREATED)
            self.assertEqual(created["payload"]["allowed_tools"],
                             ["score", "draft"])
            reopened = RunStore(root)
            again = next(e for e in reopened.events_for(run_id)
                         if e["kind"] == ev.RUN_CREATED)
            self.assertEqual(again["payload"]["allowed_tools"],
                             ["score", "draft"])

    def test_tool_outside_allowlist_refused_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = create_envelope(
                goal="fixture goal", risk_tier="GREEN", authority_level="A1",
                idempotency_key="allow-2", acceptance_criteria_hash=_AC,
                now_epoch_s=_NOW, rand="e1e2e3d4e5f6a7b8",
                deadline_iso="2026-09-09T12:00:00Z",
                allowed_tools=("score",))
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(env, now_epoch_s=_NOW)
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(
                    ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 1,
                    payload={"tool": "smtp"}))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertNotIn(ev.TOOL_INVOKED, kinds)

    def test_named_tool_in_allowlist_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = create_envelope(
                goal="fixture goal", risk_tier="GREEN", authority_level="A1",
                idempotency_key="allow-3", acceptance_criteria_hash=_AC,
                now_epoch_s=_NOW, rand="f1f2f3d4e5f6a7b8",
                deadline_iso="2026-09-09T12:00:00Z",
                allowed_tools=("score",))
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(env, now_epoch_s=_NOW)
            eid = store.append(ev.make_event(
                ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 1,
                payload={"tool": "score"}))
            self.assertTrue(eid)

    def test_payload_smuggling_send_authorized_refused_at_construction(self):
        with self.assertRaises(FailClosedError):
            ev.make_event(
                ev.TOOL_INVOKED, "run-x", now_epoch_s=_NOW,
                payload={"send_authorized": True})

    def test_payload_value_quote_sent_refused_at_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("smuggle"), now_epoch_s=_NOW)
            with self.assertRaises(FailClosedError):
                store.append({
                    "kind": ev.TOOL_INVOKED, "run_id": run_id,
                    "payload": {"state": "quote_sent"}, "ref": None,
                })
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertEqual(kinds, [ev.RUN_CREATED])


class EventIdUniquenessAndSeqIntegrity(unittest.TestCase):
    def test_duplicate_event_id_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("eid-dup"), now_epoch_s=_NOW)
            first = next(store.replay())
            clone = dict(first)
            clone["seq"] = first["seq"] + 1
            clone["kind"] = ev.PROPOSAL_CREATED
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(clone, sort_keys=True) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_seq_gap_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("seq-gap"), now_epoch_s=_NOW)
            first = next(store.replay())
            forged = {
                "event_id": "evt-forged00000000",
                "seq": first["seq"] + 5,
                "kind": ev.PROPOSAL_CREATED,
                "run_id": run_id,
                "ts": _NOW + 1,
                "payload": {},
                "ref": None,
            }
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(forged, sort_keys=True) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_event_for_unknown_run_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("orphan"), now_epoch_s=_NOW)
            first = next(store.replay())
            forged = {
                "event_id": "evt-orphan00000000",
                "seq": first["seq"] + 1,
                "kind": ev.PROPOSAL_CREATED,
                "run_id": "run-1780000000-notareal00",
                "ts": _NOW + 1,
                "payload": {},
                "ref": None,
            }
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(forged, sort_keys=True) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)


class AudCeilingDeadlineAndLogPath(unittest.TestCase):
    """Money cap, deadline, and events.jsonl path are structural —
    persisted fields that never ran a check were decorations."""

    def test_zero_aud_refuses_positive_debit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("aud-0"), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(
                    ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2,
                    ref=receipt, payload={"aud_cents": 1}))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertNotIn(ev.BUDGET_DEBIT, kinds)

    def test_aud_ceiling_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(
                _env("aud-10", budget_aud_cents=1000), now_epoch_s=_NOW)
            r1 = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            store.append(ev.make_event(
                ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2,
                ref=r1, payload={"aud_cents": 800}))
            reopened = RunStore(root)
            r2 = reopened.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 3))
            with self.assertRaises(FailClosedError):
                reopened.append(ev.make_event(
                    ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 4,
                    ref=r2, payload={"aud_cents": 201}))  # 800+201 > 1000

    def test_zero_aud_debit_on_zero_budget_is_a_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(_env("aud-noop"), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1))
            eid = store.append(ev.make_event(
                ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2, ref=receipt))
            self.assertTrue(eid)

    def test_create_after_deadline_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            # Bypass the factory: create_envelope now refuses an expired
            # mint. This test stays a store-gate witness so a later
            # factory regression cannot hide a store hole.
            past = TaskEnvelope(
                version=1,
                run_id=mint_run_id(_NOW, "a1b2c3d4e5f6a7b8"),
                goal="fixture goal", risk_tier="GREEN",
                authority_level="A1", idempotency_key="late-create",
                acceptance_criteria_hash=_AC, budget_tokens=0,
                budget_aud_cents=0, deadline_iso="2020-01-01T00:00:00Z",
                allowed_tools=(), parent_evidence=(),
            )
            with self.assertRaises(FailClosedError):
                store.create(past, now_epoch_s=_NOW)
            self.assertFalse((root / "events.jsonl").exists())

    def test_append_at_or_after_deadline_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            run_id = store.create(
                _env("late-append", deadline_iso="2026-09-09T12:00:00Z"),
                now_epoch_s=_NOW)
            # Equal to the deadline is closed (fail closed).
            deadline_epoch = store._deadline_epoch_s("2026-09-09T12:00:00Z")
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(
                    ev.PROPOSAL_CREATED, run_id, now_epoch_s=deadline_epoch))
            with self.assertRaises(FailClosedError):
                store.append(ev.make_event(
                    ev.PROPOSAL_CREATED, run_id, now_epoch_s=deadline_epoch + 1))
            kinds = [e["kind"] for e in store.events_for(run_id)]
            self.assertEqual(kinds, [ev.RUN_CREATED])

    def test_late_idempotent_retry_returns_existing(self):
        # A late retry of the same key is not a new start.
        with tempfile.TemporaryDirectory() as tmp:
            store = RunStore(Path(tmp) / "runs")
            env = _env("late-idem", deadline_iso="2026-09-09T12:00:00Z")
            first = store.create(env, now_epoch_s=_NOW)
            late = store.create(env, now_epoch_s=2_000_000_000)
            self.assertEqual(first, late)
            self.assertEqual(len(list(store.replay())), 1)

    def test_events_jsonl_symlink_refuses_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            root.mkdir()
            target = Path(tmp) / "elsewhere.jsonl"
            target.write_text("", encoding="utf-8")
            log = root / "events.jsonl"
            try:
                log.symlink_to(target)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(FailClosedError):
                RunStore(root)
            self.assertEqual(target.read_text(encoding="utf-8"), "")

    def test_events_jsonl_symlink_refuses_append_after_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("then-swap"), now_epoch_s=_NOW)
            log = root / "events.jsonl"
            real = Path(tmp) / "moved.jsonl"
            log.rename(real)
            try:
                log.symlink_to(real)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(FailClosedError):
                store.create(_env("after-swap", rand="b1b2c3d4e5f6a7b8"),
                             now_epoch_s=_NOW)
            self.assertNotIn("after-swap", real.read_text(encoding="utf-8"))

    def test_events_jsonl_symlink_refuses_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("then-link"), now_epoch_s=_NOW)
            log = root / "events.jsonl"
            real = Path(tmp) / "moved.jsonl"
            log.rename(real)
            try:
                log.symlink_to(real)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(FailClosedError):
                RunStore(root)


class ReceiptDigestVerifiedOnLoad(unittest.TestCase):
    """Stamp-on-write is not a second witness. Load and replay must
    recompute the digest; a tampered payload with a leftover stamp is
    not a receipt."""

    def test_tampered_receipt_payload_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("rcpt-tamper"), now_epoch_s=_NOW)
            store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "honest"}))
            log = root / "events.jsonl"
            lines = log.read_text(encoding="utf-8").splitlines()
            rec = json.loads(lines[-1])
            rec["payload"]["what"] = "forged"
            lines[-1] = json.dumps(rec, sort_keys=True)
            log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_missing_receipt_digest_on_reopen_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("rcpt-nodigest"), now_epoch_s=_NOW)
            first = next(store.replay())
            forged = {
                "event_id": "evt-nodigest000000",
                "seq": first["seq"] + 1,
                "kind": ev.EXECUTION_RECEIPT,
                "run_id": run_id,
                "ts": _NOW + 1,
                "payload": {"what": "no stamp"},
                "ref": None,
            }
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(forged, sort_keys=True) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_tampered_receipt_fails_closed_on_replay_of_open_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("rcpt-replay"), now_epoch_s=_NOW)
            store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "honest"}))
            log = root / "events.jsonl"
            lines = log.read_text(encoding="utf-8").splitlines()
            rec = json.loads(lines[-1])
            rec["payload"]["what"] = "forged"
            lines[-1] = json.dumps(rec, sort_keys=True)
            log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            with self.assertRaises(FailClosedError):
                list(store.replay())


class DuplicateIdempotencyOnLoad(unittest.TestCase):
    def test_two_run_created_same_idem_different_run_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("shared-idem"), now_epoch_s=_NOW)
            first = next(store.replay())
            twin = dict(first)
            twin["event_id"] = "evt-twin0000000000"
            twin["seq"] = first["seq"] + 1
            twin["run_id"] = "run-1780000000-bbbbbbbbbb"
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(twin, sort_keys=True) + "\n")
            with self.assertRaises(FailClosedError):
                RunStore(root)


class ReplaySeqContinuity(unittest.TestCase):
    def test_seq_gap_on_replay_of_open_store_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("replay-gap"), now_epoch_s=_NOW)
            first = next(store.replay())
            forged = {
                "event_id": "evt-replaygap00000",
                "seq": first["seq"] + 5,
                "kind": ev.PROPOSAL_CREATED,
                "run_id": run_id,
                "ts": _NOW + 1,
                "payload": {},
                "ref": None,
            }
            with (root / "events.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps(forged, sort_keys=True) + "\n")
            with self.assertRaises(FailClosedError):
                list(store.replay())


def _plant(root: Path, rec: dict) -> None:
    with (root / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")


class LoadPathDebitAndDedupInvariants(unittest.TestCase):
    """Append-time debit/dedup rules must also hold on reopen.

    A planted JSONL line is not a store API call — load is the second
    witness. Ready/authorized/sent remain absent from the ledger.
    """

    def test_orphan_budget_debit_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("orphan-debit"), now_epoch_s=_NOW)
            first = next(store.replay())
            _plant(root, {
                "event_id": "evt-orphandebit000",
                "seq": first["seq"] + 1,
                "kind": ev.BUDGET_DEBIT,
                "run_id": run_id,
                "ts": _NOW + 1,
                "payload": {"tokens": 0},
                "ref": "evt-doesnotexist0000",
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_second_debit_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("dbl-debit-load"), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "once"}))
            store.append(ev.make_event(
                ev.BUDGET_DEBIT, run_id, now_epoch_s=_NOW + 2, ref=receipt))
            last = list(store.replay())[-1]
            _plant(root, {
                "event_id": "evt-seconddebit000",
                "seq": last["seq"] + 1,
                "kind": ev.BUDGET_DEBIT,
                "run_id": run_id,
                "ts": _NOW + 3,
                "payload": {"tokens": 0},
                "ref": receipt,
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_cross_run_debit_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_a = store.create(_env("load-a"), now_epoch_s=_NOW)
            run_b = store.create(_env("load-b", rand="b1b2c3d4e5f6a7b8"),
                                 now_epoch_s=_NOW)
            receipt_a = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_a, now_epoch_s=_NOW + 1,
                payload={"what": "a"}))
            last = list(store.replay())[-1]
            _plant(root, {
                "event_id": "evt-crossload00000",
                "seq": last["seq"] + 1,
                "kind": ev.BUDGET_DEBIT,
                "run_id": run_b,
                "ts": _NOW + 2,
                "payload": {"tokens": 0},
                "ref": receipt_a,
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_duplicate_kind_ref_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("dup-load"), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "once"}))
            store.append(ev.make_event(
                ev.TOOL_INVOKED, run_id, now_epoch_s=_NOW + 2, ref=receipt,
                payload={"tool": "score"}))
            last = list(store.replay())[-1]
            _plant(root, {
                "event_id": "evt-dupkindref0000",
                "seq": last["seq"] + 1,
                "kind": ev.TOOL_INVOKED,
                "run_id": run_id,
                "ts": _NOW + 3,
                "payload": {"tool": "score"},
                "ref": receipt,
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_token_ceiling_breach_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(
                _env("ceil-load", budget_tokens=5), now_epoch_s=_NOW)
            receipt = store.append(ev.make_event(
                ev.EXECUTION_RECEIPT, run_id, now_epoch_s=_NOW + 1,
                payload={"what": "over"}))
            last = list(store.replay())[-1]
            _plant(root, {
                "event_id": "evt-overceil000000",
                "seq": last["seq"] + 1,
                "kind": ev.BUDGET_DEBIT,
                "run_id": run_id,
                "ts": _NOW + 2,
                "payload": {"tokens": 6},
                "ref": receipt,
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_a3_without_rollback_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            store.create(_env("a3-seed"), now_epoch_s=_NOW)
            first = next(store.replay())
            payload = dict(first["payload"])
            payload["authority_level"] = "A3"
            payload.pop("rollback_plan", None)
            payload.pop("rollback_ref", None)
            payload["idempotency_key"] = "a3-planted"
            _plant(root, {
                "event_id": "evt-a3norb00000000",
                "seq": first["seq"] + 1,
                "kind": ev.RUN_CREATED,
                "run_id": "run-1780000000-cccccccccc",
                "ts": _NOW,
                "payload": payload,
                "ref": None,
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)

    def test_nested_smuggle_on_load_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runs"
            store = RunStore(root)
            run_id = store.create(_env("nest-load"), now_epoch_s=_NOW)
            first = next(store.replay())
            _plant(root, {
                "event_id": "evt-nestsmuggle000",
                "seq": first["seq"] + 1,
                "kind": ev.PROPOSAL_CREATED,
                "run_id": run_id,
                "ts": _NOW + 1,
                "payload": {"inner": {"next": "campaign_envelope_ready"}},
                "ref": None,
            })
            with self.assertRaises(FailClosedError):
                RunStore(root)
