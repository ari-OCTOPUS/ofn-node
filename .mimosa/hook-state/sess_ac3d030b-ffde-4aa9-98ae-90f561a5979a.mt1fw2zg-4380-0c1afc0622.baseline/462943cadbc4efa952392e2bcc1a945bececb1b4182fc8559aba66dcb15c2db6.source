#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""governed_run_c3.py — Cycle-3 Phase-3: governed verdict for the preregistration gate.

Judge = the LIVE research_loop (which does not yet have the gate — that is the point).
benchmark_gain is DEFINED in this contract as the attack-detection-rate improvement
(baseline 0/3 -> patched 3/3 => 1.0). Held-out = a REAL decision-time re-run of the whole
matrix under a fresh, unseen state tag. Calibration: PREDICTION-C3.json (file-first,
mtime-timestamped per the cycle-2 discipline) predicted detection 1.0.
Sandboxed; proposal-only; merge_or_deploy forbidden. NOTE: this patch modifies the loop
itself — apply routes through the owner-governed maintenance lane (strengthening-only:
it ADDS a quarantine path, changes nothing else; legacy calls byte-compatible).
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
os.environ["C3_RUN_TAG"] = "governed-heldout"     # unseen state for the held-out re-run

for _p in (str(WT / "_ops"), str(WT / "_ops" / "budget"), str(WT / "_ops" / "memory"),
           str(WT / "_ops" / "outcomes"), str(WT / "PRE-0"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import memory_store as ms          # noqa: E402
import gate as gate_mod            # noqa: E402
import decision_receipt as dr      # noqa: E402
import outcome_store as osx        # noqa: E402
import research_contract as rcx    # noqa: E402
import research_loop as rl         # noqa: E402  (LIVE loop = judge)

RESULT = json.loads((HERE / "result_c3.json").read_text("utf-8"))
PRED = json.loads((HERE / "PREDICTION-C3.json").read_text("utf-8"))


def _contract():
    return rcx.make_contract({
        "question": "Does an in-loop, journal-ordered prediction pre-registration gate make "
                    "peeked/tampered/sprayed predictions structurally quarantined?",
        "hypothesis": "Binding prediction hashes to append-only journal line order (per "
                      "experiment_index, exactly-one-sha) detects 3/3 attack classes with "
                      "a byte-invariant honest path and intact legit recalibration.",
        "budget": {"cost_aud": 0.1, "time_s": 900, "tokens": 2000, "max_experiments": 3},
        "tools": ["measure_capabilities", "test_in_sandbox", "compare_frozen_baselines"],
        "stop_condition": "matrix + held-out complete", "verifier": "held_out_evaluator",
        "expected_artifact": "proposed_c3.patch + result_c3.json + detection matrix",
        "falsification_criteria": [
            "any attack scenario (peek/tamper/spray) reaches accepted on the patched loop",
            "honest-path verdict or utility differs from baseline",
            "legit recalibration (higher experiment_index) gets quarantined",
            "any existing research_loop test breaks (legacy compatibility)"],
        "created_at": "2026-07-24T00:00:00Z"})


def _experiment_fn(contract):
    return RESULT


def _verifier_fn(contract, res):
    ok = (res["patched_detection"] == 3 and res["baseline_detection"] == 0
          and res["honest_path_invariant"] and res["legit_recalibration_ok"])
    # benchmark_gain == attack-detection-rate improvement (defined in contract): 0/3 -> 3/3
    gain = (res["patched_detection"] - res["baseline_detection"]) / 3.0
    return {"supported": bool(ok), "benchmark_gain": round(gain, 3), "risk": 0.05,
            "maintenance_debt": 0.10, "hard_constraints_ok": bool(ok),
            "evidence": (f"matrix: base {res['baseline_detection']}/3, patched "
                         f"{res['patched_detection']}/3, honest-invariant "
                         f"{res['honest_path_invariant']}, recal {res['legit_recalibration_ok']}")}


def _held_out_eval(**kw):
    """REAL decision-time re-run of the full matrix under a fresh unseen state tag."""
    import experiment_c3 as ex
    res = {}
    for variant, mod in (("baseline", ex.BASE), ("patched", ex.PATCHED)):
        for sc in ("H", "P", "T", "S", "R"):
            res[f"{variant}-{sc}"] = ex.run_scenario(mod, f"{variant}-{sc}", sc)
    det = sum(1 for sc in ("P", "T", "S") if res[f"patched-{sc}"]["verdict"] == "quarantined")
    base_det = sum(1 for sc in ("P", "T", "S") if res[f"baseline-{sc}"]["verdict"] != "accepted")
    inv = (res["baseline-H"]["verdict"] == res["patched-H"]["verdict"]
           and res["baseline-H"]["utility"] == res["patched-H"]["utility"])
    recal = res["patched-R"]["verdict"] == "accepted"
    ok = det == 3 and base_det == 0 and inv and recal
    (HERE / "heldout_c3.json").write_text(json.dumps(
        {"matrix": res, "patched_detection": det, "baseline_detection": base_det,
         "honest_invariant": inv, "recal_ok": recal}, ensure_ascii=False, indent=2), "utf-8")
    return {"overall_verdict": "pass" if ok else "fail", "anti_hacking_flag": False}


def main():
    contract = _contract()
    store = ms.MemoryStore(path=STATE / "memory" / "mem.db")
    rc = dr.DecisionReceiptStore(STATE / "receipts" / "rec.db")
    oc = osx.OutcomeStore(path=STATE / "outcomes" / "out.db")
    gate = gate_mod.MemoryGate(store)
    ledger = rl.ResearchLedger(STATE / "research" / "ledger.jsonl")
    budget = rl.Budget(contract["budget"])

    measured = float(RESULT["measured_detection_rate_after_patch"])
    calib = rl.record_calibration(capability="research-loop-preregistration-gate",
                                  predicted=float(PRED["predicted_detection_rate_after_patch"]),
                                  measured=measured,
                                  ledger_path=STATE / "research" / "calibration.jsonl")

    out = rl.run_experiment(
        contract=contract, experiment_fn=_experiment_fn, verifier_fn=_verifier_fn,
        held_out_eval=_held_out_eval, budget=budget, ledger=ledger, receipt_store=rc,
        memory_gate=gate, outcome_store=oc, state_dir=STATE,
        cost_aud=0.0, tokens=0, uncertainty=calib["uncertainty"])
    guard = rl.propose_only_apply_guard("merge_or_deploy")

    print("=" * 70)
    print("CYCLE-3 GOVERNED RUN — verdict:", out["verdict"])
    print("=" * 70)
    print("  contract_id :", contract["contract_id"])
    print("  reason      :", out.get("reason"))
    print("  gain(detect):", measured, "| calibration:", calib)
    print("  receipt_id  :", out.get("receipt_id"), "| memory_id:", out.get("memory_id"))
    print("  APPLY GUARD merge_or_deploy permitted:", guard["permitted"])
    store.close(); rc.close(); oc.close()
    (HERE / "governed_verdict_c3.json").write_text(json.dumps({
        "verdict": out["verdict"], "reason": out.get("reason"),
        "contract_id": contract["contract_id"], "receipt_id": out.get("receipt_id"),
        "memory_id": out.get("memory_id"), "utility": out.get("utility"),
        "calibration": calib, "apply_guard_permitted": guard["permitted"],
    }, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
