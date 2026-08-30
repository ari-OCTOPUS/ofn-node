#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""governed_run.py — C6 Phase-3: drive the governed research loop on REAL evidence.

Runs the first genuine research mission through _ops/outcomes/research_loop.run_experiment:
the sandbox A/B result (result.json) is the experiment output; the verifier reads its real
correctness+latency; a held-out corpus gates admission; a DecisionReceipt + research ledger +
durable research-journal are produced; the finding enters memory ONLY via the C3 learning_gate.
NOTHING is applied/merged/deployed — proven by propose_only_apply_guard. Fully sandboxed:
all state under _sandbox/evolution_v1/governed_state (env set BEFORE importing opslib).
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
_WT = _HERE.parent.parent
_SBX = _HERE / "governed_state_final"   # fresh dir (never delete the prior run; vault §1)
_STATE = _SBX / "_ops" / "state"
for p in (_STATE / "memory", _STATE / "receipts", _STATE / "outcomes",
          _STATE / "research", _STATE / "journal"):
    p.mkdir(parents=True, exist_ok=True)

# ── ISOLATION: point every organism path at the sandbox BEFORE importing opslib ──
os.environ["ORG_ROOT"] = str(_SBX)
os.environ["OPS_DIR"] = str(_SBX / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE)
os.environ["GENOME_DIR"] = str(_SBX / "genome")
os.environ["BUDGET_STATE"] = str(_SBX / "_ops" / "budget" / "budget-state.json")
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"

for _p in (str(_WT / "_ops"), str(_WT / "_ops" / "budget"), str(_WT / "_ops" / "memory"),
           str(_WT / "_ops" / "outcomes"), str(_WT / "PRE-0")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import memory_store as ms          # noqa: E402
import gate as gate_mod            # noqa: E402
import decision_receipt as dr      # noqa: E402
import outcome_store as osx        # noqa: E402
import research_contract as rcx    # noqa: E402
import research_loop as rl         # noqa: E402

RESULT = json.loads((_HERE / "result.json").read_text("utf-8"))


def _contract():
    return rcx.make_contract({
        "question": "Does batching MemoryStore.search()'s per-candidate hydration into one "
                    "query cut recall latency without changing results?",
        "hypothesis": "Replacing the N+1 per-candidate hydration loop in MemoryStore.search "
                      "with a single batched IN(...) query reduces recall latency >=10% with "
                      "byte-identical results.",
        "budget": {"cost_aud": 0.15, "time_s": 600, "tokens": 2000, "max_experiments": 3},
        "tools": ["measure_capabilities", "test_in_sandbox", "compare_frozen_baselines"],
        "stop_condition": "accepted, falsified, or 3 experiments",
        "verifier": "held_out_evaluator",
        "expected_artifact": "sandbox A/B: correctness-identical + latency delta + receipt",
        "falsification_criteria": [
            "any result mismatch vs baseline (different ids or order)",
            "median recall latency improvement < 10% vs baseline",
            "held-out corpus does not reproduce the gain"],
        "created_at": RESULT.get("created_at", "2026-07-23T00:00:00Z")})


def _experiment_fn(contract):
    return RESULT   # the real, already-measured sandbox A/B evidence


def _verifier_fn(contract, result):
    corr = result["correctness"]["all_identical"]
    imp = float(result["conservative_improvement_frac"])
    return {"supported": bool(corr and imp >= 0.10),
            "benchmark_gain": round(imp, 3), "risk": 0.05,
            "hard_constraints_ok": bool(corr), "maintenance_debt": 0.05,
            "evidence": (f"{result['correctness']['total_checks']} checks / "
                         f"{result['correctness']['total_mismatches']} mismatch; "
                         f"{result['mechanism']['baseline_executes']}->"
                         f"{result['mechanism']['opt_executes']} executes; "
                         f"improvement {imp*100:.1f}% (n=5000 floor)")}


def _held_out_eval(**kw):
    ho_ok = RESULT["correctness"]["heldout"]["correctness_ok"]
    return {"overall_verdict": "pass" if ho_ok else "fail", "anti_hacking_flag": False}


def main():
    contract = _contract()
    store = ms.MemoryStore(path=_STATE / "memory" / "mem.db")
    rc = dr.DecisionReceiptStore(_STATE / "receipts" / "rec.db")
    oc = osx.OutcomeStore(path=_STATE / "outcomes" / "out.db")
    gate = gate_mod.MemoryGate(store)
    ledger = rl.ResearchLedger(_STATE / "research" / "ledger.jsonl")
    budget = rl.Budget(contract["budget"])

    # honest self-calibration: Phase-1 profiler predicted ~0.11 (n=5000 lower bound);
    # measured conservative = result.json. Under/over-confidence -> decision uncertainty.
    imp = float(RESULT["conservative_improvement_frac"])
    calib = rl.record_calibration(capability="memory-recall-batched-hydration",
                                  predicted=0.11, measured=imp,
                                  ledger_path=_STATE / "research" / "calibration.jsonl")

    out = rl.run_experiment(
        contract=contract, experiment_fn=_experiment_fn, verifier_fn=_verifier_fn,
        held_out_eval=_held_out_eval, budget=budget, ledger=ledger, receipt_store=rc,
        memory_gate=gate, outcome_store=oc, state_dir=_STATE,
        cost_aud=0.0, tokens=0, uncertainty=calib["uncertainty"])

    guard = rl.propose_only_apply_guard("merge_or_deploy")

    print("=" * 70)
    print("C6 GOVERNED RUN — verdict:", out["verdict"])
    print("=" * 70)
    print("  contract_id :", contract["contract_id"])
    print("  reason      :", out.get("reason"))
    print("  benchmark_gain:", _verifier_fn(contract, RESULT)["benchmark_gain"],
          "| calibration:", calib, "| utility U:", out.get("utility"))
    print("  receipt_id  :", out.get("receipt_id"))
    print("  memory_id   :", out.get("memory_id"))
    mem = store.get("semantic", f"research-{contract['contract_id']}")
    print("  in memory?  :", bool(mem), "(via C3 learning_gate)")
    print("  APPLY GUARD merge_or_deploy permitted:", guard["permitted"], "->", guard["note"])
    print("  ledger entries:", len(ledger.entries()))
    jp = _STATE / "journal" / "research-journal.jsonl"
    print("  research-journal:", jp.exists(),
          f"({len(jp.read_text('utf-8').splitlines()) if jp.exists() else 0} lines)")
    store.close(); rc.close(); oc.close()

    # persist a compact verdict summary for the report / approval card
    (_HERE / "governed_verdict.json").write_text(json.dumps({
        "verdict": out["verdict"], "reason": out.get("reason"),
        "contract_id": contract["contract_id"], "receipt_id": out.get("receipt_id"),
        "memory_id": out.get("memory_id"), "utility": out.get("utility"),
        "calibration": calib, "apply_guard_permitted": guard["permitted"],
    }, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
