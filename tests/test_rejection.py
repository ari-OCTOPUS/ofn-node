"""Kernel-pure RUN_REJECTED / RefusalIndex (complementary P1).

The run store and chaos files are owned by open PRs. This module
locks the vocabulary on main: a refused start is a fact, not a run,
not a send, and not a burned idempotency key.
"""

from __future__ import annotations

import hashlib
import inspect
import unittest

from ofn.kernel import events as ev
from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.rejection import (
    REFUSAL_REASONS,
    RefusalIndex,
    blocks_later_start,
    grants_send,
    halt_blocks_rejection,
    make_rejection,
)

_NOW = 1780000000
_AC = hashlib.sha256(b"rejection fixture").hexdigest()


def _env(key: str = "idem-rej", *, rand: str = "a1b2c3d4e5f6a7b8"):
    return create_envelope(
        goal="rejection fixture", risk_tier="GREEN", authority_level="A1",
        idempotency_key=key, acceptance_criteria_hash=_AC,
        now_epoch_s=_NOW, rand=rand, deadline_iso="2026-09-09T12:00:00Z")


def _rej(**overrides):
    env = _env()
    kwargs = dict(
        run_id=env.run_id, reason="halt_active",
        now_epoch_s=_NOW, idempotency_key=env.idempotency_key,
    )
    kwargs.update(overrides)
    return make_rejection(**kwargs)


class FactoryVocabulary(unittest.TestCase):
    def test_kind_is_run_rejected_not_a_send(self):
        rec = _rej()
        self.assertEqual(rec["kind"], ev.RUN_REJECTED)
        self.assertNotIn(rec["kind"], ev.FORBIDDEN_EFFECT_KINDS)
        self.assertFalse(grants_send())

    def test_payload_names_halt_not_ready_or_sent(self):
        rec = _rej()
        self.assertEqual(rec["payload"]["reason"], "halt_active")
        for sealed in ev.FORBIDDEN_EFFECT_KINDS:
            self.assertNotIn(sealed, rec["payload"])
            self.assertNotEqual(rec["payload"]["reason"], sealed)

    def test_unknown_reason_refused(self):
        with self.assertRaises(FailClosedError):
            _rej(reason="because_i_said_so")

    def test_sealed_reason_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    _rej(reason=name)

    def test_malformed_run_id_refused(self):
        with self.assertRaises(FailClosedError):
            _rej(run_id="not-a-run")

    def test_empty_idempotency_key_refused(self):
        with self.assertRaises(FailClosedError):
            _rej(idempotency_key="")

    def test_sealed_idempotency_key_refused(self):
        with self.assertRaises(FailClosedError):
            _rej(idempotency_key="quote_sent")

    def test_reasons_are_a_closed_set(self):
        self.assertEqual(REFUSAL_REASONS, frozenset({"halt_active"}))


class StructuralPromises(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertIs(grants_send(), False)
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_blocks_later_start_is_structurally_false(self):
        self.assertIs(blocks_later_start(), False)

    def test_halt_does_not_block_recording_the_refusal(self):
        self.assertIs(halt_blocks_rejection(), False)


class IndexIsAuditNotGate(unittest.TestCase):
    def test_note_then_replay_is_read_only(self):
        idx = RefusalIndex()
        rec = _rej()
        self.assertEqual(idx.note(rec), 1)
        snap = idx.replay()
        self.assertEqual(len(snap), 1)
        self.assertEqual(snap[0]["kind"], ev.RUN_REJECTED)
        # mutating the snapshot must not mutate the index
        snap[0]["payload"]["reason"] = "mutated"
        self.assertEqual(idx.replay()[0]["payload"]["reason"], "halt_active")

    def test_duplicate_attempts_are_recorded_not_merged(self):
        idx = RefusalIndex()
        rec = _rej()
        idx.note(rec)
        idx.note(rec)
        self.assertEqual(len(idx), 2)
        self.assertEqual(idx.count_for(rec["run_id"]), 2)

    def test_hand_built_send_kind_refused(self):
        idx = RefusalIndex()
        with self.assertRaises(FailClosedError):
            idx.note({"kind": "quote_sent", "run_id": _env().run_id,
                      "ts": _NOW, "payload": {"reason": "halt_active",
                                              "idempotency_key": "k"}})

    def test_unknown_kind_refused(self):
        idx = RefusalIndex()
        with self.assertRaises(FailClosedError):
            idx.note({"kind": ev.RUN_CREATED, "run_id": _env().run_id,
                      "ts": _NOW, "payload": {"reason": "halt_active",
                                              "idempotency_key": "k"}})

    def test_last_reason_and_missing(self):
        idx = RefusalIndex()
        rec = _rej()
        self.assertIsNone(idx.last_reason(rec["run_id"]))
        idx.note(rec)
        self.assertEqual(idx.last_reason(rec["run_id"]), "halt_active")

    def test_index_does_not_grant_send(self):
        self.assertFalse(grants_send())
        self.assertFalse(blocks_later_start())


if __name__ == "__main__":
    unittest.main()
