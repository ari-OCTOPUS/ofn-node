#!/usr/bin/env python3
"""Build a single read-only compass from owner direction, current goal and heart regulation.

The heart controls cadence/risk pressure, never semantic direction. Owner guidance can focus
thinking but cannot silently replace the frozen goal. A stale self-model lowers readiness.
"""
from __future__ import annotations

from . import contracts


def _candidate_key(prereg: dict) -> str:
    """Reviewed deterministic identity; free text cannot invent an action class."""
    goal = str(prereg.get("goal") or "").lower()
    metric = f"{prereg.get('metric_path')}:{prereg.get('metric_key')}".lower()
    if "attribution.claimed" in metric or "پولِ مطالبه" in goal:
        return "money-claimed"
    if "recall-trend" in metric or "بازیابی" in goal:
        return "recall-events"
    if "tool-requests" in metric or "درخواستِ ابزار" in goal:
        return "tool-precision"
    return ""


def build(snapshot: dict) -> dict:
    directions = list(snapshot.get("directions") or [])
    gc = snapshot.get("goal_cycle") or {}
    prereg = gc.get("prereg") or {}
    cortex = (snapshot.get("cortex") or {}).get("data") or {}
    heart = snapshot.get("heart") or {}
    inn = snapshot.get("innervation") or {}
    guidance = snapshot.get("owner_guidance") or {}

    direction = str(prereg.get("direction") or (directions[0] if directions else ""))
    goal = str(prereg.get("goal") or "")
    readiness = "READY"
    reasons = []
    if not direction:
        readiness, reasons = "BLOCKED", ["no-owner-direction"]
    if not goal:
        readiness = "BLOCKED"
        reasons.append("no-frozen-goal")
    if (snapshot.get("self_model") or {}).get("authority") != "AUTHORITATIVE":
        readiness = "DEGRADED" if readiness == "READY" else readiness
        reasons.append("stale-self-model")
    if heart.get("authority") != "AUTHORITATIVE":
        readiness = "DEGRADED" if readiness == "READY" else readiness
        reasons.append("heart-advisory-shadow")
    coverage = inn.get("coverage_pct")
    if isinstance(coverage, (int, float)) and coverage < 100:
        readiness = "DEGRADED" if readiness == "READY" else readiness
        reasons.append(f"innervation-{coverage:g}-pct")

    return {
        "schema": contracts.COMPASS_SCHEMA,
        "compass_id": contracts.stable_id("compass", direction, goal,
                                           prereg.get("prereg_id")),
        "direction": direction,
        "goal": goal,
        "goal_key": prereg.get("goal_key"),
        "candidate_key": _candidate_key(prereg),
        "prereg_id": prereg.get("prereg_id"),
        "metric": {"path": prereg.get("metric_path"), "key": prereg.get("metric_key"),
                   "baseline": prereg.get("baseline"), "target": prereg.get("target")},
        "method": prereg.get("method"),
        "method_index": prereg.get("method_index", 0),
        "heart": {"authority": heart.get("authority"),
                  "period_s": (heart.get("data") or {}).get("period_s"),
                  "production_open": heart.get("production_open"),
                  "regulation_only": True},
        "cortex": {"coherence": cortex.get("coherence"),
                   "rhythm": cortex.get("rhythm"),
                   "alignment": cortex.get("alignment")},
        "owner_guidance": guidance.get("latest"),
        "readiness": readiness,
        "reasons": reasons,
        "semantic_authority": "owner-direction+frozen-prereg",
        "cadence_authority": ("heart" if heart.get("authority") == "AUTHORITATIVE"
                              else "heart-shadow-advisory"),
    }
