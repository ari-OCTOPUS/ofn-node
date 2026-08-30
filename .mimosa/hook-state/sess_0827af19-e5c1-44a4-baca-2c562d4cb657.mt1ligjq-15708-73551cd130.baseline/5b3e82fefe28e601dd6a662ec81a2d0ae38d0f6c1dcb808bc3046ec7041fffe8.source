#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""experiment_c3.py — Cycle-3: in-loop pre-registration gate for research_loop.

Target (chosen by two independent adversarial verdicts across cycles 1-2): the loop trusts
caller-supplied predictions; peeked/tampered predictions are structurally undetectable.

Patch (additive, tightening-only, opt-in):
  + preregister_prediction(state_dir, contract, capability, predicted)
      -> journals {step:"preregister", prediction_sha} BEFORE the experiment runs.
  + verify_preregistration(...) -> re-derives the sha and checks, by append-only journal
      LINE ORDER (not caller claims, not clock strings), that a matching preregister row
      precedes the first experiment/start row of the run.
  + record_calibration(..., preregistration=None): unverified -> uncertainty=1.0.
  + run_experiment(..., preregistration={"capability","predicted"}): the LOOP ITSELF
      re-derives verification at acceptance time (does not trust a caller dict), folds the
      calibration uncertainty in via max(), and quarantines unverified predictions.
  Legacy callers (no kwarg) are byte-compatible: nothing changes.

Attack matrix (measured, baseline vs patched):
  H honest   : preregistered 0.40, measured 0.42 -> both variants accept; U invariant.
  P peeked   : no preregistration; claims predicted=measured, uncertainty=0.
  T tampered : preregistered 0.10; later claims predicted=0.42 (post-hoc swap).
Baseline detection expected 0/2; patched 2/2 (PREDICTION-C3.json, registered first).

Known residual (disclosed): if measurement happens OUTSIDE run_experiment before the loop
ever runs, journal ordering cannot see it — the gate binds the loop's own world. Real C6
missions run experiments inside the loop, where the ordering proof is airtight.
"""
from __future__ import annotations

import difflib
import io
import json
import sys
import types
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

HERE = Path(__file__).resolve().parent
WT = HERE.parent.parent
import os
os.environ["OCTOPUS_STATE_DIR"] = str(HERE / "state")
os.environ["OCTOPUS_WIRE_MEMORY_GATE"] = "1"
for _p in (str(WT / "_ops"), str(WT / "_ops" / "memory"), str(WT / "_ops" / "outcomes"),
           str(WT / "PRE-0"), str(WT / "_ops" / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import memory_store as ms          # noqa: E402
import gate as gate_mod            # noqa: E402
import decision_receipt as dr      # noqa: E402
import outcome_store as osx        # noqa: E402
import research_contract as rcx    # noqa: E402

SRC = (WT / "_ops" / "outcomes" / "research_loop.py").read_text("utf-8").replace("\r\n", "\n")

# ── splice 1: new functions before record_calibration ─────────────────────────
_A1 = 'def record_calibration(*, capability: str, predicted: float, measured: float,\n                       ledger_path=None) -> dict:\n'
_N1 = '''def _prediction_sha(contract_id, capability, predicted) -> str:
    canon = json.dumps({"contract_id": str(contract_id), "capability": str(capability),
                        "predicted": round(float(predicted), 6)},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def preregister_prediction(*, state_dir, contract, capability, predicted,
                           experiment_index=0) -> dict:
    """C6 cycle-3: journal the prediction hash BEFORE the experiment runs. The append-only
    journal's line order (written by the journal itself) is the only precedence evidence —
    no caller-supplied clock strings. Bound to experiment_index so each experiment gets
    exactly one prediction (anti-spray). Returns the receipt for the caller's records."""
    sha = _prediction_sha(contract.get("contract_id"), capability, predicted)
    run_id = f"research-{contract.get('contract_id', 'rc')}"
    _journal(state_dir, run_id, "preregister", "ok",
             capability=str(capability)[:64], prediction_sha=sha,
             experiment_index=int(experiment_index))
    return {"run_id": run_id, "capability": str(capability)[:64],
            "predicted": round(float(predicted), 6), "prediction_sha": sha,
            "experiment_index": int(experiment_index)}


def verify_preregistration(*, state_dir, contract, capability, predicted,
                           experiment_index=0) -> dict:
    """Re-derive (never trust): recompute the sha from the CLAIMED prediction and demand,
    among the preregister rows OF THIS experiment_index, EXACTLY ONE distinct sha — which
    must equal the claimed one and PRECEDE the first experiment/start row of the same index
    (journal line order). Missing row = peeking; sha mismatch = tampering; multiple distinct
    shas for one index = spray — all -> not preregistered. Legit recalibration registers a
    new prediction under a HIGHER experiment_index (cycle-2 style) and stays valid.
    Fail-closed on any error."""
    try:
        sha = _prediction_sha(contract.get("contract_id"), capability, predicted)
        run_id = f"research-{contract.get('contract_id', 'rc')}"
        ei = int(experiment_index)
        p = Path(state_dir) / "journal" / "research-journal.jsonl"
        if not p.exists():
            return {"preregistered": False, "reason": "no research-journal"}
        shas_this_index = []
        pre_i = exp_i = None
        for i, ln in enumerate(p.read_text("utf-8").splitlines()):
            try:
                row = json.loads(ln)
            except ValueError:
                continue
            if row.get("run_id") != run_id:
                continue
            meta = row.get("meta") or {}
            if row.get("step") == "preregister" and int(meta.get("experiment_index", 0)) == ei:
                s = meta.get("prediction_sha")
                if s not in [x[1] for x in shas_this_index]:
                    shas_this_index.append((i, s))
                if pre_i is None and s == sha:
                    pre_i = i
            if exp_i is None and row.get("step") == "experiment" \
                    and row.get("status") == "start" \
                    and int(meta.get("experiment_index", 0)) == ei:
                exp_i = i
        if len(shas_this_index) > 1:
            return {"preregistered": False,
                    "reason": f"spray: {len(shas_this_index)} distinct preregistered "
                              f"predictions for experiment_index={ei}",
                    "distinct_preregistrations": len(shas_this_index)}
        ok = pre_i is not None and (exp_i is None or pre_i < exp_i)
        reason = ("ok" if ok else
                  ("no matching preregister row (peeking or tampered prediction)"
                   if pre_i is None else "preregister row AFTER experiment start"))
        return {"preregistered": bool(ok), "reason": reason,
                "preregister_line": pre_i, "experiment_start_line": exp_i}
    except Exception as ex:  # noqa: BLE001 — fail-closed
        return {"preregistered": False, "reason": f"verify-error:{type(ex).__name__}"}


def record_calibration(*, capability: str, predicted: float, measured: float,
                       ledger_path=None, preregistration=None) -> dict:
'''
assert SRC.count(_A1) == 1
S1 = SRC.replace(_A1, _N1)

# ── splice 2: enforcement inside record_calibration ───────────────────────────
_A2 = '''    try:
        pred = max(0.0, min(1.0, float(predicted)))
        meas = max(0.0, min(1.0, float(measured)))
    except (TypeError, ValueError):
        return {"calibration_error": 1.0, "overconfident": True, "uncertainty": 1.0}
'''
_N2 = '''    # C6 cycle-3: an unverified pre-registration is worse than a bad prediction — it is
    # an unauditable one. Force maximal uncertainty (-> quarantine downstream).
    if preregistration is not None and not (isinstance(preregistration, dict)
                                            and preregistration.get("preregistered")):
        rec = {"capability": str(capability)[:64], "predicted": None, "measured": None,
               "calibration_error": 1.0, "overconfident": True, "preregistered": False,
               "reason": (preregistration or {}).get("reason", "not preregistered")
               if isinstance(preregistration, dict) else "not preregistered"}
        if ledger_path is not None:
            try:
                p = Path(ledger_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\\n")
            except Exception:  # noqa: BLE001
                pass
        rec["uncertainty"] = 1.0
        return rec
    try:
        pred = max(0.0, min(1.0, float(predicted)))
        meas = max(0.0, min(1.0, float(measured)))
    except (TypeError, ValueError):
        return {"calibration_error": 1.0, "overconfident": True, "uncertainty": 1.0}
'''
assert S1.count(_A2) == 1
S2 = S1.replace(_A2, _N2)

# mark verified preregistration in the normal record
_A2b = '''    rec = {"capability": str(capability)[:64], "predicted": pred, "measured": meas,
           "calibration_error": round(err, 3), "overconfident": overconfident}
'''
_N2b = '''    rec = {"capability": str(capability)[:64], "predicted": pred, "measured": meas,
           "calibration_error": round(err, 3), "overconfident": overconfident}
    if preregistration is not None:
        rec["preregistered"] = True
'''
assert S2.count(_A2b) == 1
S2 = S2.replace(_A2b, _N2b)

# ── splice 3: run_experiment signature + in-loop gate at acceptance ───────────
_A3 = '                   cost_aud=0.0, tokens=0, uncertainty=0.0, rewrite_count=0) -> dict:\n'
_N3 = ('                   cost_aud=0.0, tokens=0, uncertainty=0.0, rewrite_count=0,\n'
       '                   preregistration=None) -> dict:\n')
assert S2.count(_A3) == 1
S3 = S2.replace(_A3, _N3)

_A4 = '''        # (5) acceptance = utility با hard-constraints (benchmark gain جبرانِ نقضِ قید نمی‌کند)
'''
_N4 = '''        # C6 cycle-3: in-loop pre-registration gate (opt-in, tightening-only). The LOOP
        # re-derives verification from the append-only journal — it never trusts a caller
        # dict. Unverified prediction -> quarantine; verified -> its calibration uncertainty
        # can only RAISE the caller's uncertainty (max), never lower it.
        if preregistration is not None:
            _pv = verify_preregistration(
                state_dir=state_dir, contract=contract,
                capability=(preregistration or {}).get("capability"),
                predicted=(preregistration or {}).get("predicted"),
                experiment_index=int(rewrite_count))
            _cal = record_calibration(
                capability=str((preregistration or {}).get("capability")),
                predicted=(preregistration or {}).get("predicted"),
                measured=float(v.get("benchmark_gain", 0.0)),
                preregistration=_pv)
            uncertainty = max(float(uncertainty), float(_cal.get("uncertainty", 1.0)))
            if not _pv.get("preregistered"):
                e = {"contract_id": contract.get("contract_id"), "experiment_key": exp_key,
                     "hypothesis": contract.get("hypothesis"), "verdict": "quarantined",
                     "reason": f"prediction not pre-registered: {_pv.get('reason')}",
                     "receipt_id": rid}
                ledger.append(e)
                _journal(state_dir, run_id, "accept", "ok", verdict="quarantined",
                         reason="preregistration-failed")
                return {"verdict": "quarantined", "reason": e["reason"],
                        "receipt_id": rid, "ledger_entry": e,
                        "preregistration": _pv}

        # (5) acceptance = utility با hard-constraints (benchmark gain جبرانِ نقضِ قید نمی‌کند)
'''
assert S3.count(_A4) == 1
PATCHED_SRC = S3.replace(_A4, _N4)

(HERE / "research_loop_v4.py").write_text(PATCHED_SRC, "utf-8", newline="\n")
diff = "".join(difflib.unified_diff(
    SRC.splitlines(keepends=True), PATCHED_SRC.splitlines(keepends=True),
    fromfile="a/_ops/outcomes/research_loop.py", tofile="b/_ops/outcomes/research_loop.py"))
(HERE / "proposed_c3.patch").write_text(diff, "utf-8", newline="\n")


def _load(src, name):
    mod = types.ModuleType(name)
    mod.__dict__["__file__"] = str(HERE / f"{name}.py")
    exec(compile(src, f"{name}.py", "exec"), mod.__dict__)
    return mod


BASE = _load(SRC, "rl_c3_base")
PATCHED = _load(PATCHED_SRC, "rl_c3_patched")


def _contract():
    return rcx.make_contract({
        "question": "does the preregistration gate detect peeked/tampered predictions?",
        "hypothesis": "journal-ordered prediction hashes quarantine peeking and tampering "
                      "without touching the honest path",
        "budget": {"cost_aud": 0.1, "tokens": 1000, "time_s": 300, "max_experiments": 3},
        "tools": ["measure_capabilities", "test_in_sandbox", "compare_frozen_baselines"],
        "stop_condition": "matrix complete", "verifier": "held_out_evaluator",
        "expected_artifact": "detection matrix",
        "falsification_criteria": ["any attack scenario reaches accepted on the patched loop",
                                   "honest verdict/utility differs from baseline"],
        "created_at": "2026-07-24T00:00:00Z"})


RUN_TAG = os.environ.get("C3_RUN_TAG", "run1")


def _stores(tag):
    d = HERE / "state" / RUN_TAG / tag
    (d / "memory").mkdir(parents=True, exist_ok=True)
    (d / "journal").mkdir(parents=True, exist_ok=True)
    store = ms.MemoryStore(path=d / "memory" / "m.db")
    rc = dr.DecisionReceiptStore(d / "r.db")
    oc = osx.OutcomeStore(path=d / "o.db")
    return store, rc, oc, d


def run_scenario(mod, tag, scenario):
    """scenario ∈ H|P|T. Returns {verdict, utility}."""
    contract = _contract()
    store, rc, oc, state = _stores(tag)
    gate = gate_mod.MemoryGate(store)
    led = mod.ResearchLedger(state / "ledger.jsonl")
    bud = mod.Budget(contract["budget"])
    measured = 0.42

    def exp_fn(c):
        return {"measured_gain": measured}

    def ver_fn(c, r):
        return {"supported": True, "benchmark_gain": r["measured_gain"], "risk": 0.05,
                "maintenance_debt": 0.05, "hard_constraints_ok": True, "evidence": "matrix"}

    ho = lambda **k: {"overall_verdict": "pass", "anti_hacking_flag": False}  # noqa: E731
    kw = {}
    rewrite = 0
    has_pre = hasattr(mod, "preregister_prediction")
    if scenario == "H":
        claimed, unc = 0.40, 0.02
        if has_pre:
            mod.preregister_prediction(state_dir=state, contract=contract,
                                       capability="matrix-cap", predicted=claimed)
            kw = {"preregistration": {"capability": "matrix-cap", "predicted": claimed}}
    elif scenario == "P":      # peek: no preregistration at all; claims predicted=measured
        claimed, unc = measured, 0.0
        if has_pre:
            kw = {"preregistration": {"capability": "matrix-cap", "predicted": claimed}}
    elif scenario == "T":      # tamper: preregister 0.10, later claim 0.42
        claimed, unc = measured, 0.0
        if has_pre:
            mod.preregister_prediction(state_dir=state, contract=contract,
                                       capability="matrix-cap", predicted=0.10)
            kw = {"preregistration": {"capability": "matrix-cap", "predicted": claimed}}
    elif scenario == "S":      # spray: register 5 predictions, claim whichever matched
        claimed, unc = measured, 0.0
        if has_pre:
            for guess in (0.10, 0.20, 0.30, 0.42, 0.50):
                mod.preregister_prediction(state_dir=state, contract=contract,
                                           capability="matrix-cap", predicted=guess)
            kw = {"preregistration": {"capability": "matrix-cap", "predicted": claimed}}
    else:                      # R: legit recalibration at a HIGHER experiment_index
        claimed, unc = 0.40, 0.02
        rewrite = 1
        if has_pre:
            mod.preregister_prediction(state_dir=state, contract=contract,
                                       capability="matrix-cap", predicted=0.10,
                                       experiment_index=0)
            mod.preregister_prediction(state_dir=state, contract=contract,
                                       capability="matrix-cap", predicted=claimed,
                                       experiment_index=1)
            kw = {"preregistration": {"capability": "matrix-cap", "predicted": claimed}}
    out = mod.run_experiment(
        contract=contract, experiment_fn=exp_fn, verifier_fn=ver_fn, held_out_eval=ho,
        budget=bud, ledger=led, receipt_store=rc, memory_gate=gate, outcome_store=oc,
        state_dir=state, uncertainty=unc, rewrite_count=rewrite, **kw)
    store.close(); rc.close(); oc.close()
    return {"verdict": out["verdict"], "utility": out.get("utility"),
            "reason": str(out.get("reason"))[:90]}


if __name__ == "__main__":
    add = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    rem = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
    print(f"patch: +{add}/-{rem} lines (additive, opt-in)\n")
    res = {}
    for variant, mod in (("baseline", BASE), ("patched", PATCHED)):
        for sc in ("H", "P", "T", "S", "R"):
            r = run_scenario(mod, f"{variant}-{sc}", sc)
            res[f"{variant}-{sc}"] = r
            print(f"  {variant:<9} {sc}: verdict={r['verdict']:<22} U={r['utility']}  {r['reason']}")
    attacks = ("P", "T", "S")
    det_base = sum(1 for sc in attacks if res[f"baseline-{sc}"]["verdict"] != "accepted")
    det_pat = sum(1 for sc in attacks if res[f"patched-{sc}"]["verdict"] == "quarantined")
    honest_inv = (res["baseline-H"]["verdict"] == res["patched-H"]["verdict"]
                  and res["baseline-H"]["utility"] == res["patched-H"]["utility"])
    recal_ok = res["patched-R"]["verdict"] == "accepted"
    print(f"\n  baseline attack detection: {det_base}/3   patched: {det_pat}/3   "
          f"honest-path invariant: {honest_inv}   legit-recalibration accepted: {recal_ok}")
    out = {"schema": "c6-cycle3-result", "patch": {"added": add, "removed": rem},
           "matrix": res, "baseline_detection": det_base, "patched_detection": det_pat,
           "measured_detection_rate_after_patch": det_pat / 3.0,
           "honest_path_invariant": honest_inv, "legit_recalibration_ok": recal_ok}
    (HERE / "result_c3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print("wrote result_c3.json")
