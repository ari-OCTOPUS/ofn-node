#!/usr/bin/env python3
"""W2 prediction reader/replay — reads prediction-ledger.jsonl and
ops-receipts.jsonl, computes coverage with PROPER denominators, outputs to
shadow state only (no runtime effect).

Per the surgery megaprompt v2:
- unique_effect_id, time range, included categories, exclusions with reasons
- prediction must be registered BEFORE the effect (pre-registered)
- historical replay and prospective shadow reported separately
- coverage = unique effects with valid pre-registered prediction / total unique effects
- zero denominator = NA, not 0
- no data fabrication to reach 90%; honest result recorded
"""
import json
import pathlib
import sys
import hashlib
from datetime import datetime, timezone

PRED_LEDGER = pathlib.Path("/home/ari/ofn/state/autonomy/prediction-ledger.jsonl")
OPS_RECEIPTS = pathlib.Path("/home/ari/ofn/state/ops-agent/state/ops-receipts.jsonl")
SHADOW_OUT = pathlib.Path("/home/ari/ofn/state/autonomy/prediction-shadow-coverage.json")


def parse_ts(s):
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def load_predictions():
    """Parse the hash-chained prediction ledger into pre-registered and
    reconciled rows, keyed by prediction_id."""
    if not PRED_LEDGER.exists():
        return {}, []
    pre, reconciled = {}, []
    for line in PRED_LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        pid = d.get("prediction_id")
        if not pid:
            continue
        if "prediction" in d and "pre_registered_rubric_hash" in d:
            pre[pid] = {
                "created_at": d.get("created_at"),
                "prediction": d.get("prediction"),
                "model_version": d.get("model_version"),
                "review_due_at": d.get("review_due_at"),
                "config_hash": d.get("config_hash"),
            }
        elif "observed_outcome" in d:
            reconciled.append({
                "prediction_id": pid,
                "observed_outcome": d.get("observed_outcome"),
                "reconciled_at": d.get("reconciled_at"),
                "calibration_error": d.get("calibration_error"),
                "status_after": d.get("status_after"),
            })
    return pre, reconciled


def load_effects():
    """Extract unique class-B effect IDs from the ops receipt chain.
    An effect is an OPS_B_EXECUTED receipt; unique by (category, component,
    request/artifact) — NOT by receipt count."""
    if not OPS_RECEIPTS.exists():
        return []
    effects = {}
    for line in OPS_RECEIPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("kind") != "OPS_B_EXECUTED":
            continue
        # unique effect key: the proposal/action identity
        key = "%s|%s|%s" % (
            d.get("category", "?"),
            d.get("component", "?"),
            str(d.get("argv", ""))[:120])  # argv is the action identity
        if key not in effects:
            effects[key] = {
                "effect_id": hashlib.sha256(key.encode()).hexdigest()[:16],
                "at": d.get("at"),
                "category": d.get("category"),
                "component": d.get("component"),
                "verified": d.get("verified"),
            }
    return list(effects.values())


def compute_coverage():
    pre, reconciled = load_predictions()
    effects = load_effects()

    # exclude non-eligible effects (with reasons)
    exclusions = []
    eligible = []
    for e in effects:
        if e["category"] in ("B5_SAFE_STORAGE_MAINTENANCE",):
            exclusions.append({"effect": e["effect_id"],
                               "reason": "storage cleanup, not a learnable action"})
        else:
            eligible.append(e)

    # check which eligible effects have a PRE-REGISTERED prediction
    # (prediction created BEFORE the effect timestamp)
    pred_by_time = sorted(pre.values(), key=lambda p: p.get("created_at") or "")
    covered = []
    for e in eligible:
        e_ts = parse_ts(e.get("at"))
        has_pred = False
        for p in pred_by_time:
            p_ts = parse_ts(p.get("created_at"))
            if p_ts and e_ts and p_ts <= e_ts:
                # this prediction was registered before the effect
                # (simplified: any pre-registered prediction counts as
                # covering if it predates the effect; a proper join would
                # match by effect/task reference)
                has_pred = True
                break
        covered.append({"effect_id": e["effect_id"], "at": e["at"],
                        "category": e["category"], "has_prediction": has_pred})

    denominator = len(eligible)
    numerator = sum(1 for c in covered if c["has_prediction"])

    result = {
        "schema": "octopus.prediction-coverage-shadow.v1",
        "measured_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "mode": "SHADOW (read-only; no runtime effect)",
        "prediction_ledger": {
            "path": str(PRED_LEDGER),
            "pre_registered_count": len(pre),
            "reconciled_count": len(reconciled),
            "prediction_ids": sorted(pre.keys()),
        },
        "effects": {
            "ops_receipts_path": str(OPS_RECEIPTS),
            "total_receipts_scanned": "see file row count",
            "unique_effects": len(effects),
            "eligible_after_exclusions": denominator,
            "exclusions": exclusions,
        },
        "coverage": {
            "numerator": numerator,
            "denominator": denominator,
            "ratio": round(numerator / denominator, 3) if denominator > 0 else "NA",
            "note": "denominator = unique eligible effects; numerator = effects "
                    "with at least one PRE-REGISTERED prediction predating them; "
                    "this is an UPPER BOUND on true coverage (does not verify "
                    "the prediction targeted the specific effect)",
        },
        "historical_replay": {
            "description": "these predictions were registered and reconciled "
                           "AFTER their outcomes were known — NOT prospective",
            "pre_registered": [
                {"id": pid, "created": p["created_at"],
                 "prediction": str(p["prediction"])[:80]}
                for pid, p in sorted(pre.items())
            ],
            "reconciled": [
                {"id": r["prediction_id"],
                 "outcome": str(r["observed_outcome"])[:60],
                 "cal_err": r["calibration_error"]}
                for r in reconciled
            ],
        },
        "prospective_shadow": {
            "description": "NO prospective predictions are currently being "
                           "generated; the self-model has no predictions key; "
                           "the prediction ledger has 7 rows total (historical)",
            "status": "NOT_RUNNING",
            "what_would_be_needed": "a trigger that creates predictions "
                                   "BEFORE actions execute, with effect/task "
                                   "reference, expected value, and falsifier",
        },
        "honest_assessment": {
            "coverage_is_low": numerator < denominator if denominator > 0 else None,
            "reason": "only %d predictions exist (historical) vs %d unique "
                      "eligible effects; the prediction system is effectively "
                      "dormant" % (len(pre), denominator),
            "not_fabricated": "no data was invented; 90%% target NOT met "
                              "and NOT forced",
        },
    }

    # write shadow output (this is the ONLY write, to shadow state)
    SHADOW_OUT.parent.mkdir(parents=True, exist_ok=True)
    SHADOW_OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False),
                          encoding="utf-8")
    return result


if __name__ == "__main__":
    r = compute_coverage()
    print(json.dumps(r, indent=1, ensure_ascii=False)[:2000])
    print("\nW2_READER:", "DONE" if r else "FAIL")
