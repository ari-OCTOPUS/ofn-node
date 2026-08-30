"""World Model — facts/hypotheses/predictions. No policy or action types."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any

from .observation import Observation, Quality, parse_dt
from .trust import eligibility


def build_world_state(
    observations: list[Observation],
    assessment: dict[str, Any],
    *,
    decision_time: datetime,
    valid_at: datetime | None = None,
    known_at: datetime | None = None,
) -> dict[str, Any]:
    dt = parse_dt(decision_time)
    va = parse_dt(valid_at) or dt
    ka = parse_dt(known_at) or dt
    facts: list[dict[str, Any]] = []
    hypotheses: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    uncertainties: list[dict[str, Any]] = []
    contradictions: list[str] = list(assessment.get("contradictions") or [])
    evidence_ids: list[str] = []

    # order-independence: sort by observation_id
    ordered = sorted(observations, key=lambda o: o.observation_id)
    for o in ordered:
        if parse_dt(o.occurred_at) and dt and parse_dt(o.occurred_at) > dt:
            uncertainties.append({"kind": "future_excluded", "id": o.observation_id})
            continue
        if o.quality == Quality.RESTART_ARTIFACT_SUSPECTED.value:
            hypotheses.append({
                "id": o.observation_id,
                "claim": f"{o.metric}={o.value}",
                "confidence": 0.3,
                "label": "hypothesis",
                "reason": "restart artifact is not a fact",
            })
            evidence_ids.append(o.observation_id)
            continue
        if o.quality == Quality.CONFLICTING.value:
            contradictions.append(f"conflict:{o.metric}:{o.observation_id}")
            uncertainties.append({"kind": "conflict", "metric": o.metric, "id": o.observation_id})
            continue
        if eligibility(o):
            facts.append({
                "id": o.observation_id,
                "metric": o.metric,
                "value": o.value,
                "unit": o.unit,
                "beat": o.beat,
            })
            evidence_ids.append(o.observation_id)
        else:
            uncertainties.append({"kind": o.quality, "id": o.observation_id, "metric": o.metric})

    predictions.append({
        "horizon_s": 113.0,
        "expiry": (dt + timedelta(seconds=113)).isoformat() if dt else None,
        "claim": "next beat telemetry may remain overwrite-only without T22 store",
        "confidence": 0.4,
    })
    n_facts = len(facts)
    n_unc = len(uncertainties) + len(hypotheses)
    conf = round(n_facts / max(1, n_facts + n_unc), 4)
    blob = json.dumps({"dt": dt.isoformat() if dt else "", "facts": [f["id"] for f in facts]}, sort_keys=True)
    return {
        "schema": "world-state.v1",
        "state_id": "ws-" + hashlib.sha256(blob.encode()).hexdigest()[:16],
        "valid_at": va.isoformat() if va else None,
        "known_at": ka.isoformat() if ka else None,
        "decision_time": dt.isoformat() if dt else None,
        "entities": {"organism": {"kind": "octopus_laptop"}},
        "facts": facts,
        "hypotheses": hypotheses,
        "predictions": predictions,
        "uncertainties": uncertainties,
        "contradictions": contradictions,
        "evidence_ids": evidence_ids,
        "homeostatic_assessment_id": assessment.get("assessment_id"),
        "confidence": conf,
        "executable": False,
    }
