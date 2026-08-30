#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""governed_run_v3.py — Cycle-2 Phase-3: governed verdict for the secondary-index change.

Improvement over cycle 1 (from the governance-honesty adversarial lens): held_out_eval is
NOT a pre-baked dict — it RE-RUNS a fresh correctness battery (unseen seed) at decision
time, so the loop's held-out gate rests on evidence derived during the decision itself.
Prediction registered in PREDICTION.json BEFORE results were read (honest calibration).
Sandboxed state; proposal-only; merge_or_deploy constitutionally forbidden.
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

HERE = Path(__file__).resolve().parent
WT = HERE.parent.parent
SBX = HERE / "governed_state"
STATE = SBX / "_ops" / "state"
for p in (STATE / "memory", STATE / "receipts", STATE / "outcomes",
          STATE / "research", STATE / "journal"):
    p.mkdir(parents=True, exist_ok=True)

os.environ["ORG_ROOT"] = str(SBX)
os.environ["OPS_DIR"] = str(SBX / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(STATE)
os.environ["GENOME_DIR"] = str(SBX / "genome")
os.environ["BUDGET_STATE"] = str(SBX / "_ops" / "budget" / "budget-state.json")
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"

for _p in (str(WT / "_ops"), str(WT / "_ops" / "budget"), str(WT / "_ops" / "memory"),
           str(WT / "_ops" / "outcomes"), str(WT / "PRE-0"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import memory_store as ms          # noqa: E402
import gate as gate_mod            # noqa: E402
import decision_receipt as dr      # noqa: E402
import outcome_store as osx        # noqa: E402
import research_contract as rcx    # noqa: E402
import research_loop as rl         # noqa: E402

RESULT = json.loads((HERE / "result_v3.json").read_text("utf-8"))
PRED = json.loads((HERE / "PREDICTION.json").read_text("utf-8"))


def _conservative_gain(res) -> float:
    """Smallest improvement fraction across all measured op/size cells (honest floor)."""
    fracs = []
    for r in res["latency"]:
        fracs.append(1.0 - r["get_idx_ms"] / r["get_base_ms"])
        fracs.append(1.0 - r["ins_idx_ms"] / r["ins_base_ms"])
    return max(0.0, min(fracs))


def _contract():
    return rcx.make_contract({
        "question": "Do secondary indexes on memory(namespace,mkey,created_at) and "
                    "(namespace,content_sha256) remove the O(n) scans in get()/insert-dedupe "
                    "without changing any result?",
        "hypothesis": "Adding the two additive idempotent indexes converts get() and the "
                      "dedupe check from full-table SCAN to index SEARCH, cutting latency at "
                      "20k memories by >=3x with byte-identical results and zero "
                      "PENDING/RETRACTED leakage.",
        "budget": {"cost_aud": 0.15, "time_s": 1800, "tokens": 2000, "max_experiments": 3},
        "tools": ["measure_capabilities", "test_in_sandbox", "compare_frozen_baselines"],
        "stop_condition": "accepted, falsified, or 3 experiments",
        "verifier": "held_out_evaluator",
        "expected_artifact": "proposed_v3.patch + result_v3.json + receipt",
        "falsification_criteria": [
            "any get()/search()/insert() result mismatch vs baseline",
            "any PENDING/RETRACTED memory visible in results",
            "get() speedup at 20k memories < 3x, or query plan still SCAN",
            "one-time index build on existing 20k DB > 5000ms"],
        "created_at": PRED["registered_at"]})


def _experiment_fn(contract):
    return RESULT


def _verifier_fn(contract, res):
    c = res["correctness"]
    mech_ok = ("SEARCH" in res["mechanism"]["get"] and "SCAN" not in res["mechanism"]["get"]
               and "SEARCH" in res["mechanism"]["dedupe"])
    lat20 = [r for r in res["latency"] if r["n"] == 20000][0]
    ok = (c["mismatches"] == 0 and c["admission_leaks"] == 0 and c["replay_ops_equal"]
          and c["metrics_equal"] and mech_ok and lat20["get_speedup"] >= 3.0
          and res["migration"]["first_open_build_ms"] <= 5000)
    return {"supported": ok, "benchmark_gain": round(_conservative_gain(res), 3),
            "risk": 0.05, "maintenance_debt": 0.05, "hard_constraints_ok": bool(ok),
            "evidence": (f"{c['checks']} checks/{c['mismatches']} mism/{c['admission_leaks']} leaks; "
                         f"plans get={res['mechanism']['get'][:40]}; "
                         f"get@20k {lat20['get_base_ms']}->{lat20['get_idx_ms']}ms "
                         f"({lat20['get_speedup']}x); build {res['migration']['first_open_build_ms']}ms")}


def _held_out_eval(**kw):
    """REAL held-out at decision time: fresh unseen-seed correctness battery."""
    import experiment_v3 as ex
    ho = ex.correctness(n=1200, seed=31337)
    ok = (ho["mismatches"] == 0 and ho["admission_leaks"] == 0
          and ho["replay_ops_equal"] and ho["metrics_equal"])
    (HERE / "heldout_v3.json").write_text(json.dumps(ho, ensure_ascii=False, indent=2), "utf-8")
    return {"overall_verdict": "pass" if ok else "fail", "anti_hacking_flag": False}


def main():
    contract = _contract()
    store = ms.MemoryStore(path=STATE / "memory" / "mem.db")
    rc = dr.DecisionReceiptStore(STATE / "receipts" / "rec.db")
    oc = osx.OutcomeStore(path=STATE / "outcomes" / "out.db")
    gate = gate_mod.MemoryGate(store)
    ledger = rl.ResearchLedger(STATE / "research" / "ledger.jsonl")
    budget = rl.Budget(contract["budget"])

    gain = _conservative_gain(RESULT)
    calib = rl.record_calibration(capability="memory-secondary-indexes",
                                  predicted=float(PRED["predicted_conservative_gain"]),
                                  measured=gain,
                                  ledger_path=STATE / "research" / "calibration.jsonl")

    out = rl.run_experiment(
        contract=contract, experiment_fn=_experiment_fn, verifier_fn=_verifier_fn,
        held_out_eval=_held_out_eval, budget=budget, ledger=ledger, receipt_store=rc,
        memory_gate=gate, outcome_store=oc, state_dir=STATE,
        cost_aud=0.0, tokens=0, uncertainty=calib["uncertainty"])
    guard = rl.propose_only_apply_guard("merge_or_deploy")

    print("=" * 70)
    print("CYCLE-2 GOVERNED RUN — verdict:", out["verdict"])
    print("=" * 70)
    print("  contract_id :", contract["contract_id"])
    print("  reason      :", out.get("reason"))
    print("  gain(conserv):", round(gain, 3), "| calibration:", calib)
    print("  receipt_id  :", out.get("receipt_id"), "| memory_id:", out.get("memory_id"))
    print("  APPLY GUARD merge_or_deploy permitted:", guard["permitted"])
    store.close(); rc.close(); oc.close()
    (HERE / "governed_verdict_v3.json").write_text(json.dumps({
        "verdict": out["verdict"], "reason": out.get("reason"),
        "contract_id": contract["contract_id"], "receipt_id": out.get("receipt_id"),
        "memory_id": out.get("memory_id"), "utility": out.get("utility"),
        "calibration": calib, "apply_guard_permitted": guard["permitted"],
    }, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
