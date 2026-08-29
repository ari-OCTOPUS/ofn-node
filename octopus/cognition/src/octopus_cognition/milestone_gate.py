"""Evidence-based milestone gates. Missing evidence is a failed condition."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def gate(conditions: Sequence[Mapping[str, Any]]) -> str:
    unmet = [
        c["id"]
        for c in conditions
        if c.get("observed") != c.get("expected") or c.get("evidence") is None
    ]
    return "PASS" if not unmet else "BLOCKED"


def unmet_ids(conditions: Sequence[Mapping[str, Any]]) -> list[str]:
    return [
        str(c["id"])
        for c in conditions
        if c.get("observed") != c.get("expected") or c.get("evidence") is None
    ]


PREREQUISITES = {
    "M2_CANDIDATE": "M1_INTEGRITY",
    "M3_SAFETY_CASE": "M2_CANDIDATE",
    "M4_A0_ADVISORY": "M3_SAFETY_CASE",
    "M5_PLANNER_SANDBOX": "M4_A0_ADVISORY",
    "M6_HIL": "M5_PLANNER_SANDBOX",
    "M7_BOUNDED_ACTUATOR": "M6_HIL",
    "M8_SCOPE_GROWTH": "M7_BOUNDED_ACTUATOR",
    "M9_OPERATIONS": "M8_SCOPE_GROWTH",
}


def apply_prerequisites(results: dict[str, str]) -> dict[str, str]:
    """M1 is a hard prerequisite of M2. Later milestones are linear after that."""
    out = dict(results)
    for mid, pre in PREREQUISITES.items():
        if mid not in out:
            continue
        if out.get(pre) != "PASS":
            out[mid] = "BLOCKED"
    return out


def evaluate_gate(doc: Mapping[str, Any]) -> dict[str, Any]:
    conditions = list(doc.get("blocking_conditions") or [])
    result = gate(conditions)
    return {
        "schema": "octopus.milestone-gate.v2",
        "milestone": doc.get("milestone"),
        "gate_result": result,
        "unmet": unmet_ids(conditions),
        "authority_change_permitted": False if result != "PASS" else bool(doc.get("authority_change_permitted")),
        "prerequisite_milestones_passed": doc.get("prerequisite_milestones_passed"),
    }
