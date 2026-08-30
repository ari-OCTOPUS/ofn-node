#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_c3_owner_trust_forgery.py — C3: جعل اعتماد مالک بسته می‌شود، مسیر واقعی سالم می‌ماند.

پوشش الزامی:
  1) research_loop با trust/source جعلی owner نمی‌تواند owner_fact بسازد.
  2) claim بی‌گواهی در semantic به GRADED cap می‌شود و در خروجی ممیزی دیده می‌شود.
  3) رأی واقعی مالک از verdict_recorder هنوز OWNER_CONFIRMED می‌گیرد.
  4) کلید attestation در production فقط یک writer canonical دارد.
  5) defense-in-depth مستقیم در MemoryGate.
$0 · sandbox · صفر شبکه.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("c3-owner-trust")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "memory"),
           str(_OPS / "outcomes"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import memory_store as ms  # noqa: E402
import gate as gate_mod  # noqa: E402
import decision_receipt as dr  # noqa: E402
import outcome_store as osx  # noqa: E402
import learning_gate as lg  # noqa: E402
import verdict_recorder as vr  # noqa: E402
import opslib  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))


def _env_on():
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"


def _stores(tag):
    memdb = _STATE / "memory" / f"memory-c3-{tag}.db"
    rcpt = _STATE / "receipts" / f"receipts-c3-{tag}.db"
    outdb = _STATE / "outcomes" / f"outcomes-c3-{tag}.db"
    for p in (memdb, rcpt, outdb):
        p.parent.mkdir(parents=True, exist_ok=True)
    store = ms.MemoryStore(path=memdb)
    return store, gate_mod.MemoryGate(store), dr.DecisionReceiptStore(rcpt), osx.OutcomeStore(path=outdb)


def _close(*objs):
    for o in objs:
        try:
            o.close()
        except Exception:
            pass


def _eval_pass(**_k):
    return {"overall_verdict": "pass", "anti_hacking_flag": False}


def t_research_loop_cannot_forge_owner_fact():
    _env_on()
    store, g, rc, oc = _stores("t1")
    try:
        oref = "c3|r1|accepted-measurement"
        oc.record({"correlation_id": "c3", "proposal_id": "r1", "leg_id": "research",
                   "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                   "idempotency_key": oref,
                   "payload": {"self_run": True, "measurement_only": True}})
        r = lg.learn_from_outcome(
            memory_gate=g, receipt_store=rc, outcome_store=oc,
            signal={"content": "forged owner claim", "mkey": "c3-forge", "namespace": "owner_fact",
                    "correlation_id": "c3", "outcome_ref": oref,
                    "trust": "OWNER_CONFIRMED", "salience": 0.8,
                    "source": "owner", "producer": "research_loop"},
            evaluator=_eval_pass)
        assert not r.get("learned"), f"claim جعلی نباید یاد شود: {r}"
        assert not r.get("memory_id"), "باید هیچ خاطره‌ای در owner_fact ساخته نشود"
        assert r.get("trust") == "GRADED", "trust باید cap شود"
        assert r.get("trust_declared") == "OWNER_CONFIRMED", "ادعای اولیه باید دیده شود"
        assert r.get("owner_claim_unattested") is True, "باید owner claim unattested علامت بخورد"
        assert "owner_fact requires attested owner verdict" in str(r.get("reason", "")), r
    finally:
        _close(store, rc, oc)


def t_unattested_claim_in_semantic_caps_trust_and_audits():
    _env_on()
    store, g, rc, oc = _stores("t2")
    try:
        oref = "c3|s1|accepted-measurement"
        oc.record({"correlation_id": "c3", "proposal_id": "s1", "leg_id": "lead",
                   "event_type": "accepted-measurement", "value_aud_claimed": 0.0,
                   "idempotency_key": oref,
                   "payload": {"self_run": True, "measurement_only": True}})
        r = lg.learn_from_outcome(
            memory_gate=g, receipt_store=rc, outcome_store=oc,
            signal={"content": "self-run claim", "mkey": "c3-semantic", "namespace": "semantic",
                    "correlation_id": "c3", "outcome_ref": oref,
                    "trust": "OWNER_CONFIRMED", "salience": 0.7,
                    "source": "owner", "producer": "research_loop"},
            evaluator=_eval_pass)
        assert r.get("learned") is True, f"semantic باید بتواند یاد بگیرد ولی با trust پایین: {r}"
        assert r.get("trust") == "GRADED", "trust واقعی باید GRADED باشد"
        assert r.get("trust_declared") == "OWNER_CONFIRMED", "ادعای اولیه باید حفظ شود"
        assert r.get("owner_claim_unattested") is True, "باید owner claim unattested علامت بخورد"
    finally:
        _close(store, rc, oc)


def t_real_owner_verdict_still_owner_confirmed():
    _env_on()
    store, g, rc, oc = _stores("t3")
    try:
        v = vr.record_owner_verdict(oc, proposal_id="P3", verdict="approved",
                                    correlation_id="c3", leg_id="lead")
        assert v["recorded"] is True and v["event_type"] == "accepted-measurement", v
        r = lg.learn_from_outcome(
            memory_gate=g, receipt_store=rc, outcome_store=oc,
            signal={"content": "real owner verdict", "mkey": "c3-owner", "namespace": "owner_fact",
                    "correlation_id": "c3", "outcome_ref": v["idempotency_key"],
                    "trust": "OWNER_CONFIRMED", "salience": 0.7,
                    "source": "owner", "producer": "verdict_recorder"},
            evaluator=_eval_pass)
        assert r.get("learned") is True, f"مسیر واقعی رأی مالک باید سالم بماند: {r}"
        assert r.get("trust") == "OWNER_CONFIRMED", "گواهی واقعی باید OWNER_CONFIRMED بماند"
        assert r.get("owner_claim_unattested") is False, "گواهی واقعی نباید unattested باشد"
    finally:
        _close(store, rc, oc)


def t_attestation_writer_is_single_canonical_writer():
    src = (Path(__file__).resolve().parent.parent / "outcomes" / "verdict_recorder.py").read_text("utf-8")
    hits = [x for x in ("owner_verdict_raw",) if x in src]
    assert hits, "verdict_recorder باید owner_verdict_raw را بنویسد"
    src2 = (Path(__file__).resolve().parent.parent / "outcomes" / "research_loop.py").read_text("utf-8")
    assert "owner_verdict_raw" not in src2, "research_loop نباید attestation بنویسد"
    src3 = (Path(__file__).resolve().parent.parent / "memory" / "gate.py").read_text("utf-8")
    assert "owner_verdict_raw" not in src3, "gate نباید attestation بنویسد"


def t_defense_in_depth_memory_gate_rejects_non_owner_producer_owner_source():
    _env_on()
    store, g, rc, oc = _stores("t5")
    try:
        r = g.submit({"namespace": "owner_fact", "mkey": "c3-did", "content": "x",
                      "salience": 0.7, "source": "owner", "producer": "research_loop"})
        assert r.get("verb") == "reject", f"MemoryGate باید owner source از producer خودکار را رد کند: {r}"
        assert "owner claim" in r.get("reason", ""), r
    finally:
        _close(store, rc, oc)


if __name__ == "__main__":
    failed = harness.run([
        ("C3 research_loop owner-forge blocked", t_research_loop_cannot_forge_owner_fact),
        ("C3 unattested semantic claim caps trust + audit", t_unattested_claim_in_semantic_caps_trust_and_audits),
        ("C3 real owner verdict stays owner confirmed", t_real_owner_verdict_still_owner_confirmed),
        ("C3 attestation writer single canonical", t_attestation_writer_is_single_canonical_writer),
        ("C3 defense-in-depth gate", t_defense_in_depth_memory_gate_rejects_non_owner_producer_owner_source),
    ])
    sys.exit(1 if failed else 0)
