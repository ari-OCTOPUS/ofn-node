#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_research_loop.py — C6: حلقهٔ پژوهشِ حاکمیت‌شده، ضدخودفریبی، owner-gated.

پوشش (مأموریت C6):
  1. contract: falsification_criteria/budget اجباری؛ ابزارِ خارج از constitutional-allowed → رد (fail-closed)
  2. accepted: verifier سبز + held-out سبز + U>0 → وارد memory (فقط از learning_gate) + رسید + ledger
  3. rejected: hypothesis falsify → terminate + ledger، **بدونِ** ورود به memory
  4. bad conjecture: بازنویسیِ مکرر → terminate در سقف (نه بی‌نهایت)
  5. budget: سرریزِ experiments/cost → terminate
  6. quarantine: held-out قرمز یا U≤0 → quarantined (نه commit)
  7. governance: اکشنِ forbidden (merge_or_deploy) → permitted=False؛ حلقه هرگز apply نمی‌کند
  8. restart: durable research-journal ثبت می‌شود (resume ممکن)
$0 آفلاین؛ صفر شبکه/پول/apply؛ sandbox.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("research-loop")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "memory"),
           str(_OPS / "outcomes"), str(_OPS.parent / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import memory_store as ms  # noqa: E402
import gate as gate_mod  # noqa: E402
import decision_receipt as dr  # noqa: E402
import outcome_store as osx  # noqa: E402
import research_contract as rcx  # noqa: E402
import research_loop as rl  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))


def _stores(tag):
    md = _STATE / "memory" / f"m-{tag}.db"; rp = _STATE / "receipts" / f"r-{tag}.db"
    od = _STATE / "outcomes" / f"o-{tag}.db"
    for p in (md, rp, od):
        p.parent.mkdir(parents=True, exist_ok=True)
    return ms.MemoryStore(path=md), rp, od


def _contract(tools=None):
    return rcx.make_contract({
        "question": "does memory-cited decision improve acceptance?",
        "hypothesis": "citing prior owner-accepted lessons raises accept-rate",
        "budget": {"cost_aud": 1.0, "tokens": 1000, "time_s": 60, "max_experiments": 3},
        "tools": tools or ["measure_capabilities", "test_in_sandbox", "compare_frozen_baselines"],
        "stop_condition": "3 experiments or falsified",
        "verifier": "held_out_evaluator",
        "expected_artifact": "graded memory + receipt",
        "falsification_criteria": ["accept-rate does not rise vs frozen baseline"],
        "created_at": "2026-07-23T00:00:00Z"})


def _env_on():
    os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"


def _eval_pass(**kw):
    return {"overall_verdict": "pass", "anti_hacking_flag": False}


def _eval_fail(**kw):
    return {"overall_verdict": "fail", "anti_hacking_flag": False}


# ── ۱: contract validation ──────────────────────────────────────────────────────
def t_contract_validation():
    try:
        rcx.make_contract({"question": "q", "hypothesis": "h", "budget": {},
                           "tools": ["test_in_sandbox"], "stop_condition": "s",
                           "verifier": "v", "expected_artifact": "a"})   # بدونِ falsification
        assert False, "بدونِ falsification_criteria باید رد شود"
    except rcx.ResearchContractError:
        pass
    try:
        _contract(tools=["edit_verifier"])   # ابزارِ forbidden
        assert False, "ابزارِ خارج از constitutional-allowed باید رد شود"
    except rcx.ResearchContractError:
        pass
    c = _contract()
    assert c["contract_id"].startswith("rc_") and c["budget"]["max_experiments"] == 3


# ── ۲: accepted → memory via learning_gate ──────────────────────────────────────
def t_accepted_enters_memory_via_gate():
    _env_on()
    store, rp, od = _stores("t2")
    rc = dr.DecisionReceiptStore(rp); oc = osx.OutcomeStore(path=od); g = gate_mod.MemoryGate(store)
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t2.jsonl")
    b = rl.Budget(_contract()["budget"])
    try:
        out = rl.run_experiment(
            contract=_contract(), experiment_fn=lambda c: {"metric": 0.8},
            verifier_fn=lambda c, r: {"supported": True, "benchmark_gain": 0.3, "risk": 0.05,
                                      "hard_constraints_ok": True, "evidence": "beats baseline"},
            held_out_eval=_eval_pass, budget=b, ledger=led, receipt_store=rc,
            memory_gate=g, outcome_store=oc, state_dir=_STATE, uncertainty=0.1)
        assert out["verdict"] == "accepted", out
        assert out["memory_id"], "نتیجهٔ accepted باید وارد memory شود (learning_gate)"
        assert out["receipt_id"], "هر آزمایش رسید دارد"
        assert any(e["verdict"] == "accepted" for e in led.entries()), "ledger"
        # نتیجه واقعاً در memory هست
        assert store.get("semantic", f"research-{_contract()['contract_id']}") is not None
    finally:
        store.close(); rc.close(); oc.close()


# ── ۳: rejected (falsified) → NOT in memory ─────────────────────────────────────
def t_falsified_terminates_not_learned():
    _env_on()
    store, rp, od = _stores("t3")
    rc = dr.DecisionReceiptStore(rp); oc = osx.OutcomeStore(path=od); g = gate_mod.MemoryGate(store)
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t3.jsonl")
    try:
        out = rl.run_experiment(
            contract=_contract(), experiment_fn=lambda c: {"metric": 0.1},
            verifier_fn=lambda c, r: {"supported": False, "evidence": "no gain vs baseline"},
            held_out_eval=_eval_pass, budget=rl.Budget(_contract()["budget"]),
            ledger=led, receipt_store=rc, memory_gate=g, outcome_store=oc, state_dir=_STATE)
        assert out["verdict"] == "rejected" and "falsified" in out["reason"], out
        assert store.get("semantic", f"research-{_contract()['contract_id']}") is None, \
            "hypothesisِ falsify‌شده نباید وارد memory شود"
    finally:
        store.close(); rc.close(); oc.close()


# ── ۴: bad conjecture terminate (سقفِ بازنویسی) ─────────────────────────────────
def t_bad_conjecture_terminates():
    _env_on()
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t4.jsonl")
    out = rl.run_experiment(
        contract=_contract(), experiment_fn=lambda c: {}, verifier_fn=lambda c, r: {"supported": True},
        budget=rl.Budget(_contract()["budget"]), ledger=led,
        rewrite_count=rl.MAX_REWRITES)   # به سقف رسیده
    assert out["verdict"] == "rejected" and "max rewrites" in out["reason"], out


# ── ۵: budget terminate ─────────────────────────────────────────────────────────
def t_budget_terminates():
    _env_on()
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t5.jsonl")
    b = rl.Budget({"cost_aud": 0.0, "tokens": 0, "time_s": 0, "max_experiments": 1})
    b.spent["experiments"] = 5   # از پیش سرریز
    out = rl.run_experiment(contract=_contract(), experiment_fn=lambda c: {},
                            verifier_fn=lambda c, r: {"supported": True}, budget=b, ledger=led)
    assert out["verdict"] == "terminated" and "budget-exceeded" in out["reason"], out


# ── ۶: quarantine (held-out قرمز) ───────────────────────────────────────────────
def t_quarantine_on_heldout_fail():
    _env_on()
    store, rp, od = _stores("t6")
    rc = dr.DecisionReceiptStore(rp); oc = osx.OutcomeStore(path=od); g = gate_mod.MemoryGate(store)
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t6.jsonl")
    try:
        out = rl.run_experiment(
            contract=_contract(), experiment_fn=lambda c: {"metric": 0.8},
            verifier_fn=lambda c, r: {"supported": True, "benchmark_gain": 0.3, "hard_constraints_ok": True},
            held_out_eval=_eval_fail,   # held-out قرمز
            budget=rl.Budget(_contract()["budget"]), ledger=led, receipt_store=rc,
            memory_gate=g, outcome_store=oc, state_dir=_STATE)
        assert out["verdict"] == "quarantined", out
        assert store.get("semantic", f"research-{_contract()['contract_id']}") is None, \
            "quarantined نباید وارد memory شود"
    finally:
        store.close(); rc.close(); oc.close()


# ── ۷: governance — no auto-apply ───────────────────────────────────────────────
def t_no_auto_apply():
    g = rl.propose_only_apply_guard("merge_or_deploy")
    assert g["permitted"] is False, "constitution باید merge_or_deploy را ممنوع کند"
    assert rl.propose_only_apply_guard("test_in_sandbox")["permitted"] is True


# ── ۸: durable research-journal (restart-safe) ──────────────────────────────────
def t_durable_journal_written():
    _env_on()
    store, rp, od = _stores("t8")
    rc = dr.DecisionReceiptStore(rp); oc = osx.OutcomeStore(path=od); g = gate_mod.MemoryGate(store)
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t8.jsonl")
    try:
        rl.run_experiment(contract=_contract(), experiment_fn=lambda c: {"m": 1},
                          verifier_fn=lambda c, r: {"supported": True, "benchmark_gain": 0.3,
                                                    "hard_constraints_ok": True},
                          held_out_eval=_eval_pass, budget=rl.Budget(_contract()["budget"]),
                          ledger=led, receipt_store=rc, memory_gate=g, outcome_store=oc,
                          state_dir=_STATE, uncertainty=0.1)
        jp = _STATE / "journal" / "research-journal.jsonl"
        assert jp.exists() and jp.read_text("utf-8").strip(), "research-journal باید نوشته شود (resume)"
    finally:
        store.close(); rc.close(); oc.close()


# ── ۹: self-model calibration (predicted vs measured) → uncertainty → quarantine ──
def t_calibration_overconfidence():
    # calibrated: predicted≈measured → uncertaintyِ کم
    c1 = rl.record_calibration(capability="lead-scoring", predicted=0.7, measured=0.68,
                               ledger_path=_STATE / "research" / "calib.jsonl")
    assert not c1["overconfident"] and c1["uncertainty"] < 0.2, c1
    # overconfident: predicted >> measured → uncertaintyِ بالا
    c2 = rl.record_calibration(capability="lead-scoring", predicted=0.9, measured=0.4)
    assert c2["overconfident"] and c2["uncertainty"] >= 0.5, c2
    # و این uncertaintyِ بالا در run_experiment → quarantine
    _env_on()
    store, rp, od = _stores("t9")
    rc = dr.DecisionReceiptStore(rp); oc = osx.OutcomeStore(path=od); g = gate_mod.MemoryGate(store)
    led = rl.ResearchLedger(_STATE / "research" / "ledger-t9.jsonl")
    try:
        out = rl.run_experiment(
            contract=_contract(), experiment_fn=lambda c: {"m": 1},
            verifier_fn=lambda c, r: {"supported": True, "benchmark_gain": 0.3, "hard_constraints_ok": True},
            held_out_eval=_eval_pass, budget=rl.Budget(_contract()["budget"]), ledger=led,
            receipt_store=rc, memory_gate=g, outcome_store=oc, state_dir=_STATE,
            uncertainty=c2["uncertainty"])   # overconfidence → quarantine
        assert out["verdict"] == "quarantined", f"uncertaintyِ بالا باید quarantine کند: {out}"
    finally:
        store.close(); rc.close(); oc.close()


if __name__ == "__main__":
    failed = harness.run([
        ("[۹] calibration overconfidence → quarantine", t_calibration_overconfidence),
        ("[۱] contract validation (falsif+tools fail-closed)", t_contract_validation),
        ("[۲] accepted → memory via learning_gate", t_accepted_enters_memory_via_gate),
        ("[۳] falsified → terminate، not learned", t_falsified_terminates_not_learned),
        ("[۴] bad conjecture terminate (سقفِ بازنویسی)", t_bad_conjecture_terminates),
        ("[۵] budget terminate", t_budget_terminates),
        ("[۶] quarantine on held-out fail", t_quarantine_on_heldout_fail),
        ("[۷] governance — no auto-apply", t_no_auto_apply),
        ("[۸] durable research-journal (restart-safe)", t_durable_journal_written),
    ])
    sys.exit(1 if failed else 0)
