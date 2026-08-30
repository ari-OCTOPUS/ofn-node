#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""governed_run_v3b.py — Cycle-2, governed run #2 (post-quarantine recalibration).

Run #1 verdict: quarantined — evidence was clean but the self-model was overconfident
(predicted conservative gain 0.5 vs measured 0.29 -> uncertainty 0.61). Per C6 this is NOT
falsification (hypothesis supported); the budget allows another experiment. Run #2 uses
PREDICTION2.json (registered BEFORE experiment-2 ran) against genuinely UNSEEN cells
(n=2000/10000, fresh seeds). If the self-model now predicts well, uncertainty drops
legitimately — calibration improved by learning, not by peeking.
Same contract (same hypothesis/contract_id): the ledger will carry quarantined(run1) +
this run's verdict as one honest scientific record.
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
import research_loop as rl         # noqa: E402
from governed_run_v3 import _contract, _verifier_fn, _held_out_eval, RESULT  # noqa: E402

EXP2 = json.loads((HERE / "result_exp2.json").read_text("utf-8"))
PRED2 = json.loads((HERE / "PREDICTION2.json").read_text("utf-8"))


def _experiment_fn(contract):
    return RESULT


def _verifier2(contract, res):
    v = _verifier_fn(contract, res)                     # all run-1 hard gates
    c2 = EXP2["correctness_unseen"]
    exp2_ok = (c2["mismatches"] == 0 and c2["admission_leaks"] == 0
               and c2["replay_ops_equal"] and c2["metrics_equal"])
    v["supported"] = bool(v["supported"] and exp2_ok)
    v["hard_constraints_ok"] = bool(v["hard_constraints_ok"] and exp2_ok)
    v["benchmark_gain"] = float(EXP2["conservative_gain_unseen"])   # honest unseen floor
    v["evidence"] += (f" | exp2(unseen): {c2['checks']}chk/{c2['mismatches']}mism/"
                      f"{c2['admission_leaks']}leak, conserv-gain "
                      f"{EXP2['conservative_gain_unseen']}")
    return v


def main():
    contract = _contract()
    store = ms.MemoryStore(path=STATE / "memory" / "mem.db")
    rc = dr.DecisionReceiptStore(STATE / "receipts" / "rec.db")
    oc = osx.OutcomeStore(path=STATE / "outcomes" / "out.db")
    gate = gate_mod.MemoryGate(store)
    ledger = rl.ResearchLedger(STATE / "research" / "ledger.jsonl")
    budget = rl.Budget(contract["budget"])
    budget.charge(experiment=True)      # run #1 already spent one experiment

    measured = float(EXP2["conservative_gain_unseen"])
    calib = rl.record_calibration(capability="memory-secondary-indexes",
                                  predicted=float(PRED2["predicted_conservative_gain"]),
                                  measured=measured,
                                  ledger_path=STATE / "research" / "calibration.jsonl")

    out = rl.run_experiment(
        contract=contract, experiment_fn=_experiment_fn, verifier_fn=_verifier2,
        held_out_eval=_held_out_eval, budget=budget, ledger=ledger, receipt_store=rc,
        memory_gate=gate, outcome_store=oc, state_dir=STATE,
        cost_aud=0.0, tokens=0, uncertainty=calib["uncertainty"], rewrite_count=1)
    guard = rl.propose_only_apply_guard("merge_or_deploy")

    print("=" * 70)
    print("CYCLE-2 GOVERNED RUN #2 — verdict:", out["verdict"])
    print("=" * 70)
    print("  contract_id :", contract["contract_id"])
    print("  reason      :", out.get("reason"))
    print("  gain(unseen):", measured, "| calibration#2:", calib)
    print("  receipt_id  :", out.get("receipt_id"), "| memory_id:", out.get("memory_id"))
    print("  APPLY GUARD merge_or_deploy permitted:", guard["permitted"])
    print("  ledger entries for contract:",
          sum(1 for e in ledger.entries() if e.get("contract_id") == contract["contract_id"]))
    store.close(); rc.close(); oc.close()
    (HERE / "governed_verdict_v3_run2.json").write_text(json.dumps({
        "verdict": out["verdict"], "reason": out.get("reason"),
        "contract_id": contract["contract_id"], "receipt_id": out.get("receipt_id"),
        "memory_id": out.get("memory_id"), "utility": out.get("utility"),
        "calibration": calib, "apply_guard_permitted": guard["permitted"],
        "run1_verdict": "quarantined (overconfident self-model)",
    }, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
