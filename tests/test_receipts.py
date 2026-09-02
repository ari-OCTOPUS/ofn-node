"""Typed ExecutionReceipt + ReceiptIndex — second witness of receipt dedup.

Independent of ``ofn.adapters.receipt`` (JSON digest) and of
``run_store.py`` (owned by an open PR). HALT stops STARTS, not in-flight
receipts. Ready ≠ authorized. Proposal ≠ execution.
"""

from __future__ import annotations

import hashlib
import unittest

from ofn.kernel.envelope import create_envelope
from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import EXECUTION_RECEIPT, PROPOSAL_CREATED
from ofn.kernel.receipts import (
    OUTCOMES, RECEIPT_ID_RE, ExecutionReceipt, ReceiptIndex, create_receipt,
    grants_send, halt_blocks_receipt_mint, mint_receipt_id,
)

_AC = hashlib.sha256(b"typed receipt fixture").hexdigest()
_NOW = 1780000000
_RAND = "a1b2c3d4e5f6a7b8"
_RUN = create_envelope(
    goal="score three leads", risk_tier="GREEN", authority_level="A1",
    idempotency_key="idem-rcp-1", acceptance_criteria_hash=_AC,
    now_epoch_s=_NOW, rand=_RAND, deadline_iso="2026-09-09T12:00:00Z",
).run_id


def _rcp(**overrides):
    kwargs = dict(
        run_id=_RUN, tool="score", outcome="ok",
        now_epoch_s=_NOW, rand=_RAND,
    )
    kwargs.update(overrides)
    return create_receipt(**kwargs)


class FactoryMintsAtTheBoundary(unittest.TestCase):
    def test_id_format_and_ts_bind(self):
        r = _rcp()
        self.assertTrue(RECEIPT_ID_RE.match(r.receipt_id))
        self.assertEqual(r.receipt_id, f"rcp-{_NOW}-{_RAND}")
        self.assertEqual(r.ts, _NOW)
        self.assertEqual(r.kind, EXECUTION_RECEIPT)

    def test_kind_is_execution_not_proposal(self):
        self.assertNotEqual(EXECUTION_RECEIPT, PROPOSAL_CREATED)
        self.assertEqual(_rcp().kind, EXECUTION_RECEIPT)
        self.assertNotEqual(_rcp().kind, PROPOSAL_CREATED)

    def test_bool_timestamp_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_receipt_id(True, _RAND)  # type: ignore[arg-type]

    def test_short_rand_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_receipt_id(_NOW, "short")

    def test_direct_construct_with_foreign_id_fails(self):
        with self.assertRaises(FailClosedError):
            ExecutionReceipt(
                receipt_id="not-a-receipt", run_id=_RUN,
                tool="score", outcome="ok", ts=_NOW)


class OutcomesAreClosedAndNotSends(unittest.TestCase):
    def test_known_outcomes(self):
        for outcome in ("ok", "rejected", "failed"):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, OUTCOMES)
                self.assertEqual(_rcp(outcome=outcome, rand="b" * 16).outcome, outcome)

    def test_sent_is_not_an_outcome(self):
        self.assertNotIn("sent", OUTCOMES)
        with self.assertRaises(FailClosedError):
            _rcp(outcome="sent")

    def test_authorized_is_not_an_outcome(self):
        with self.assertRaises(FailClosedError):
            _rcp(outcome="authorized")

    def test_tool_cannot_be_a_sealed_name(self):
        for tool in ("send_authorized", "quote_sent", "campaign_envelope_ready",
                     "send-authorized"):
            with self.subTest(tool=tool):
                with self.assertRaises(FailClosedError):
                    _rcp(tool=tool)

    def test_detail_cannot_smuggle_ready(self):
        with self.assertRaises(FailClosedError):
            _rcp(detail="campaign_envelope_ready")

    def test_blank_tool_fails_closed(self):
        with self.assertRaises(FailClosedError):
            _rcp(tool="  ")

    def test_foreign_run_id_fails_closed(self):
        with self.assertRaises(FailClosedError):
            _rcp(run_id="run-not-minted")


class BindingAndContentAreDifferentClaims(unittest.TestCase):
    def test_hash_is_sha256_hex(self):
        r = _rcp()
        for digest in (r.binding_hash(), r.content_hash()):
            self.assertEqual(len(digest), 64)
            int(digest, 16)

    def test_same_contract_same_binding(self):
        a = _rcp()
        b = _rcp()
        self.assertEqual(a.binding_hash(), b.binding_hash())
        self.assertEqual(a.content_hash(), b.content_hash())

    def test_different_rand_same_content_different_binding(self):
        a = _rcp(rand="aaaaaaaaaa")
        b = _rcp(rand="bbbbbbbbbb")
        self.assertNotEqual(a.receipt_id, b.receipt_id)
        self.assertEqual(a.content_hash(), b.content_hash())
        self.assertNotEqual(a.binding_hash(), b.binding_hash())

    def test_newline_in_detail_cannot_collide_with_separator(self):
        sneaky = _rcp(detail="alpha\ntool=smtp", rand="c" * 16)
        honest = _rcp(detail="alpha", rand="d" * 16)
        self.assertNotEqual(sneaky.content_hash(), honest.content_hash())
        self.assertNotEqual(sneaky.binding_hash(), honest.binding_hash())


class IndexIsAppendOnlyAndIdempotent(unittest.TestCase):
    def test_replay_same_id_same_contract_is_one_row(self):
        idx = ReceiptIndex()
        first = idx.record(_rcp())
        second = idx.record(_rcp())
        self.assertIs(first, second)
        self.assertEqual(len(idx), 1)
        self.assertEqual(idx.replay(), (first,))

    def test_same_id_different_contract_fails_closed(self):
        idx = ReceiptIndex()
        idx.record(_rcp(tool="score"))
        clash = ExecutionReceipt(
            receipt_id=f"rcp-{_NOW}-{_RAND}", run_id=_RUN,
            tool="draft", outcome="ok", ts=_NOW)
        with self.assertRaises(FailClosedError):
            idx.record(clash)
        self.assertEqual(len(idx), 1)

    def test_same_effect_two_ids_fails_closed(self):
        idx = ReceiptIndex()
        first = idx.record(_rcp(rand="aaaaaaaaaa"))
        with self.assertRaises(FailClosedError):
            idx.record(_rcp(rand="bbbbbbbbbb"))
        self.assertEqual(idx.get(first.receipt_id), first)
        self.assertEqual(len(idx), 1)

    def test_different_effects_append(self):
        idx = ReceiptIndex()
        a = idx.record(_rcp(tool="score", rand="aaaaaaaaaa"))
        b = idx.record(_rcp(tool="draft", rand="bbbbbbbbbb"))
        self.assertEqual(len(idx), 2)
        self.assertEqual(idx.replay(), (a, b))

    def test_replay_has_no_write_path(self):
        idx = ReceiptIndex()
        idx.record(_rcp())
        snap = idx.replay()
        self.assertEqual(len(snap), 1)
        # Tuple is the second witness: callers cannot append through replay.
        with self.assertRaises(AttributeError):
            snap.append(_rcp(rand="z" * 16))  # type: ignore[attr-defined]
        self.assertEqual(len(idx), 1)

    def test_unknown_id_is_none_not_false(self):
        idx = ReceiptIndex()
        missing = idx.get(f"rcp-{_NOW}-zzzzzzzzzz")
        self.assertIsNone(missing)
        self.assertIsNot(missing, False)

    def test_blank_get_fails_closed(self):
        with self.assertRaises(FailClosedError):
            ReceiptIndex().get("  ")

    def test_non_receipt_record_fails_closed(self):
        with self.assertRaises(FailClosedError):
            ReceiptIndex().record({"tool": "score"})  # type: ignore[arg-type]


class AlgorithmsAreIndependentWitnesses(unittest.TestCase):
    def test_kernel_hash_is_not_the_adapter_json_digest(self):
        # Two claims, two algorithms. Unifying them would drop a witness.
        from ofn.adapters.receipt import receipt_digest
        r = _rcp()
        adapter = receipt_digest({
            "tool": r.tool, "outcome": r.outcome, "ts": r.ts,
        })
        self.assertNotEqual(adapter, r.binding_hash())
        self.assertNotEqual(adapter, r.content_hash())


class ReadyIsNotAReceiptAndHaltDoesNotBlockMint(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send(None))
        self.assertFalse(grants_send(_rcp()))
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_grants_send_rejects_foreign_type(self):
        with self.assertRaises(FailClosedError):
            grants_send({"send_authorized": True})  # type: ignore[arg-type]

    def test_halt_does_not_block_in_flight_receipts(self):
        self.assertFalse(halt_blocks_receipt_mint())
        # In-flight record still works — HALT is a start gate, not here.
        idx = ReceiptIndex()
        recorded = idx.record(_rcp())
        self.assertEqual(len(idx), 1)
        self.assertEqual(recorded.outcome, "ok")
        self.assertFalse(grants_send(recorded))


if __name__ == "__main__":
    unittest.main()
