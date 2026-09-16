# -*- coding: utf-8 -*-
"""Weakest-member scoring. Combines owner P0/P1 targets with scan evidence."""
from __future__ import annotations

from typing import Any

from .contracts import OWNER_TARGETS, priority_score, write_json
from . import STATE_DIR


def diagnose(scan: dict[str, Any]) -> dict[str, Any]:
    blockers = set()
    for b in ((scan.get("wave1_preflight") or {}).get("blockers") or []):
        blockers.add(str(b).lower())
    loop_titles = " ".join(
        str(x.get("title") or "") + " " + str(x.get("loop_id") or "")
        for x in (scan.get("open_loops") or [])
    ).lower()
    need_text = " ".join(str(n.get("request") or "") for n in (scan.get("needs") or [])).lower()

    scored = []
    for t in OWNER_TARGETS:
        extra = 1.0
        blob = (t["problem"] + " " + t["id"]).lower()
        if any(k in loop_titles or k in need_text for k in blob.split()[:4]):
            extra *= 1.15
        if t["id"].startswith("P0") and blockers:
            extra *= 1.2
        score = priority_score(
            severity=t["severity"], user_impact=t["user_impact"],
            evidence_confidence=t["evidence_confidence"] * extra,
            repairability=t["repairability"],
            dependency_value=t["dependency_value"],
            estimated_risk=t["estimated_risk"],
            estimated_runtime=t["estimated_runtime"],
        )
        scored.append({**t, "priority_score": round(score, 3), "boost": round(extra, 3)})
    scored.sort(key=lambda r: r["priority_score"], reverse=True)

    by_layer: dict[str, dict] = {}
    for row in scored:
        by_layer.setdefault(row["layer"], row)  # first = strongest for that lane

    weakest = scored[0] if scored else None
    out = {
        "schema": "diagnosis/1",
        "weakest": weakest,
        "by_layer": by_layer,
        "ranked": scored,
        "root_cause_hints": {
            "memory": "F3 fail-closed + two-phase PENDING hides get(); tests predate promote()",
            "brain": "improve.gather_signals did not read calibration-latest (S-A03)",
            "heart": "orphan_watchdog.tick never called from organism loop (observe-only missing)",
        },
    }
    write_json(STATE_DIR / "capability_scores.json", {
        "ts": scan.get("ts"),
        "ranked": [{"id": r["id"], "layer": r["layer"], "score": r["priority_score"]}
                   for r in scored],
    })
    return out
