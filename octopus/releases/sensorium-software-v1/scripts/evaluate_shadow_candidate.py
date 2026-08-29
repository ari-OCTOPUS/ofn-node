#!/usr/bin/env python3
"""Offline T4 evaluation of the shadow candidate against live outcomes.

Read-only on the production prediction ledger. Writes only under
/var/lib/octopus/state/shadow_candidate/. Does not import planner.
Does not change live Policy, skill window, or octopus-world-model.service.
"""

from __future__ import annotations

import ast
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")

from octopus_cognition.ledger import ChainedLedger  # noqa: E402
from octopus_cognition.metacontrol.skill import DomainSkillTracker  # noqa: E402
from octopus_cognition.skill_bootstrap import (  # noqa: E402
    block_bootstrap_skill,
    complementary_metrics,
    m2_evidence_permitted,
)
from octopus_cognition.world_model.interaction_candidate import (  # noqa: E402
    VERSION,
    InteractionMeanReversionModel,
    apply_delta,
    interaction_guard,
)

LIVE_WM = Path("/var/lib/octopus/state/world_model")
OUT_DIR = Path("/var/lib/octopus/state/shadow_candidate")
STATE_KEYS = ("compute_pressure", "memory_pressure", "storage_integrity", "sensor_coverage")
LIVE_SCRIPTS = (
    "world_model_shadow.py",
    "skill_tracker_loop.py",
    "metacontrol_shadow.py",
    "stability_monitor.py",
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def mse(left: dict[str, float], right: dict[str, float]) -> float | None:
    diffs: list[float] = []
    for key in STATE_KEYS:
        if key not in left or key not in right:
            continue
        diffs.append((float(left[key]) - float(right[key])) ** 2)
    if not diffs:
        return None
    return sum(diffs) / len(diffs)


def _imports_planner(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "planner" in alias.name:
                    return True
        elif isinstance(node, ast.ImportFrom) and node.module and "planner" in node.module:
            return True
    return False


def usable_pairs(bodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outcomes = {
        b.get("prediction_id"): b
        for b in bodies
        if b.get("schema") == "octopus.prediction-outcome.v1"
    }
    pairs: list[dict[str, Any]] = []
    for pred in bodies:
        if pred.get("schema") != "octopus.prediction.v1":
            continue
        outcome = outcomes.get(pred.get("prediction_id"))
        if not outcome:
            continue
        if not outcome.get("usable"):
            continue
        issued = int(pred.get("issued_at_ns") or 0)
        resolved = int(outcome.get("resolved_at_ns") or 0)
        if issued <= 0 or resolved <= 0 or resolved < issued:
            continue
        state = pred.get("state") or {}
        observed = outcome.get("observed") or {}
        if any(k not in state or k not in observed for k in STATE_KEYS):
            continue
        action = str(pred.get("action") or "NO_ACTION_OBSERVE_ONLY")
        baseline = pred.get("baseline") or state
        cand = apply_delta({k: float(state[k]) for k in STATE_KEYS}, action)
        cand_loss = mse(cand, {k: float(observed[k]) for k in STATE_KEYS})
        base_loss = mse({k: float(baseline[k]) for k in STATE_KEYS}, {k: float(observed[k]) for k in STATE_KEYS})
        if cand_loss is None or base_loss is None:
            continue
        pairs.append(
            {
                "prediction_id": pred.get("prediction_id"),
                "issued_at_ns": issued,
                "resolved_at_ns": resolved,
                "action": action,
                "state": {k: float(state[k]) for k in STATE_KEYS},
                "observed": {k: float(observed[k]) for k in STATE_KEYS},
                "candidate_pred": cand,
                "persistence_pred": {k: float(baseline[k]) for k in STATE_KEYS},
                "candidate_loss": cand_loss,
                "persistence_loss": base_loss,
            }
        )
    return pairs


def bootstrap_skill(pairs: list[dict[str, Any]], rounds: int = 1000, seed: int = 266) -> dict[str, Any]:
    """Acceptance CI for serial telemetry. IID bootstrap is not used."""
    return block_bootstrap_skill(pairs, rounds=rounds, seed=seed)


def shuffled_skill(pairs: list[dict[str, Any]], seed: int = 7) -> dict[str, Any]:
    rng = random.Random(seed)
    observed = [p["observed"] for p in pairs]
    shuffled = observed[:]
    rng.shuffle(shuffled)
    cand_losses: list[float] = []
    base_losses: list[float] = []
    for pred, obs in zip(pairs, shuffled, strict=True):
        cl = mse(pred["candidate_pred"], obs)
        bl = mse(pred["persistence_pred"], obs)
        if cl is None or bl is None:
            continue
        cand_losses.append(cl)
        base_losses.append(bl)
    n = len(cand_losses)
    cand = sum(cand_losses) / n if n else None
    base = sum(base_losses) / n if n else None
    skill = None if cand is None or base is None or base <= 1e-12 else 1.0 - cand / base
    return {
        "samples": n,
        "candidate_loss": cand,
        "persistence_loss": base,
        "skill": skill,
        "decision": "DENY",
        "reason": "shuffled_outcomes_must_deny",
    }


def calibration(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    if not pairs:
        return {"error": None, "status": "unknown", "per_key": {}}
    per_key: dict[str, float] = {}
    for key in STATE_KEYS:
        errs = [abs(p["candidate_pred"][key] - p["observed"][key]) for p in pairs]
        per_key[key] = sum(errs) / len(errs)
    overall = sum(per_key.values()) / len(per_key)
    return {
        "error": overall,
        "status": "known",
        "acceptable": overall <= 0.20,
        "per_key": per_key,
        "note": "MAE of candidate vs observed; not imputed",
    }


def evaluate() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = ChainedLedger(LIVE_WM, "octopus.prediction-ledger.head.v1")
    ok, brk, detail = ledger.verify()
    bodies = ledger.bodies()
    pairs = usable_pairs(bodies)
    tracker = DomainSkillTracker(window=10000, minimum=50)
    for p in pairs:
        tracker.record(p["candidate_loss"], p["persistence_loss"])
    report = tracker.report()
    cand_loss = sum(p["candidate_loss"] for p in pairs) / len(pairs) if pairs else None
    base_loss = sum(p["persistence_loss"] for p in pairs) / len(pairs) if pairs else None
    skill_point = None
    if cand_loss is not None and base_loss is not None:
        if base_loss <= 1e-12 and cand_loss <= 1e-12:
            skill_point = 0.0
        elif base_loss <= 1e-12:
            skill_point = None
        else:
            skill_point = 1.0 - cand_loss / base_loss
    boot = bootstrap_skill(pairs)
    cal = calibration(pairs)
    shuffled = shuffled_skill(pairs) if len(pairs) >= 50 else {"decision": "DENY", "reason": "insufficient_samples"}
    guard = interaction_guard()
    leakage_bad = [p["prediction_id"] for p in pairs if int(p["resolved_at_ns"]) < int(p["issued_at_ns"])]
    live_policy_import = _imports_planner(Path("/opt/octopus/cognition/src/octopus_cognition/world_model/policy.py"))
    live_scripts = {name: _imports_planner(Path("/opt/octopus/scripts") / name) for name in LIVE_SCRIPTS}
    candidate_path = Path("/opt/octopus/cognition/src/octopus_cognition/world_model/interaction_candidate.py")
    eval_path = Path("/opt/octopus/scripts/evaluate_shadow_candidate.py")
    m1_path = Path("/var/lib/octopus/state/engineering-completeness/gates/M1_INTEGRITY.json")
    m1_gate_result = "BLOCKED"
    if m1_path.is_file():
        try:
            m1_gate_result = str(json.loads(m1_path.read_text(encoding="utf-8")).get("gate_result") or "BLOCKED")
        except (OSError, json.JSONDecodeError, TypeError):
            m1_gate_result = "BLOCKED"
    m2_ok = m2_evidence_permitted(m1_gate_result)
    missingness_rate = None if not bodies else 1.0 - (len(pairs) / max(1, sum(1 for b in bodies if b.get("schema") == "octopus.prediction.v1")))
    extra = complementary_metrics(
        pairs,
        calibration_error=cal.get("error"),
        missingness_rate=missingness_rate,
        per_domain_skill={"sensorium_health": skill_point},
    )

    plan_allowed = (
        m2_ok
        and len(pairs) >= 50
        and skill_point is not None
        and skill_point > 0
        and boot.get("lower") is not None
        and float(boot["lower"]) > 0
        and cal.get("status") == "known"
        and bool(cal.get("acceptable"))
        and shuffled.get("decision") == "DENY"
        and bool(guard.get("pass"))
        and not leakage_bad
        and not live_policy_import
        and not any(live_scripts.values())
        and extra.get("per_domain_worst_case_skill") is not None
        and float(extra["per_domain_worst_case_skill"]) > 0
    )
    payload = {
        "schema": "octopus.shadow-candidate-eval.v1",
        "written_at": datetime.now(timezone.utc).isoformat(),
        "role": "shadow_only",
        "live_policy_consumes_candidate": False,
        "planner_imported": False,
        "planner_invocations": 0,
        "executed_actions": 0,
        "candidate": {
            "version": VERSION,
            "class": InteractionMeanReversionModel.__name__,
            "code_path": str(candidate_path),
            "code_sha256": _sha256(candidate_path),
            "evaluator_sha256": _sha256(eval_path) if eval_path.is_file() else None,
        },
        "baseline": {"version": "persistence-v1"},
        "ledger": {"ok": ok, "break": brk, "detail": detail, "no_live_append": True},
        "usable_pairs": len(pairs),
        "candidate_loss": cand_loss,
        "persistence_loss": base_loss,
        "skill_point_estimate": skill_point,
        "bootstrap": boot,
        "bootstrap_method_required": "block_bootstrap",
        "skill_lower_bound": boot.get("lower"),
        "m1_gate_result": m1_gate_result,
        "m2_evidence_permitted": m2_ok,
        "complementary": extra,
        "tracker": {
            "samples": report.samples,
            "score": report.score,
            "lower_bound": report.lower_bound,
            "eligible": report.eligible,
            "reason": report.reason,
        },
        "calibration": cal,
        "missingness": {
            "live_homeostasis_unknown_untouched": True,
            "pairs_require_complete_state_keys": list(STATE_KEYS),
        },
        "domain": "sensorium_health",
        "shuffled": shuffled,
        "interaction_guard": guard,
        "leakage_guard": {
            "outcome_before_prediction": leakage_bad,
            "pass": not leakage_bad,
        },
        "no_live_policy_dependency": True,
        "live_scripts_import_planner": live_scripts,
        "actions_seen": sorted({p["action"] for p in pairs}),
        "decision": (
            "PLAN_ALLOWED_ADVISORY"
            if plan_allowed
            else ("NOT_EVIDENCE_M1_BLOCKED" if not m2_ok else "DENY")
        ),
        "plan_allowed_advisory_met": plan_allowed,
        "note": (
            "M1 Integrity is a hard prerequisite. Skill on a Doctor-FAIL system is not evidence. "
            "Live action is NO_ACTION_OBSERVE_ONLY only. Interaction is proven on the guard, not by varying live actuators. "
            "Do not lower skill thresholds if lower bound is not positive."
        ),
    }
    OUT_DIR.joinpath("CANDIDATE_VALIDATION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    OUT_DIR.joinpath("SKILL_REPORT.json").write_text(
        json.dumps(
            {
                "schema": "octopus.skill-report.v1",
                "evaluated_model": VERSION,
                "baseline_model": "persistence-v1",
                "usable_pairs": len(pairs),
                "candidate_loss": cand_loss,
                "baseline_loss": base_loss,
                "skill_point_estimate": skill_point,
                "skill_lower_bound": boot.get("lower"),
                "calibration_error": cal.get("error"),
                "calibration_status": cal.get("status"),
                "decision": payload["decision"],
                "planning_evidence": bool(plan_allowed),
                "written_at": payload["written_at"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    payload = evaluate()
    print(json.dumps({"decision": payload["decision"], "usable_pairs": payload["usable_pairs"], "skill": payload["skill_point_estimate"], "lower": payload["skill_lower_bound"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
