#!/usr/bin/env python3
"""Create a non-owning trace graph over existing direction/goal/mission/action records."""
from __future__ import annotations

from . import contracts


def build(snapshot: dict, compass: dict, *, action_receipt: dict | None = None,
          mission: dict | None = None) -> dict:
    pre = (snapshot.get("goal_cycle") or {}).get("prereg") or {}
    journal = (snapshot.get("goal_cycle") or {}).get("journal") or {}
    verdict = (snapshot.get("goal_cycle") or {}).get("verdict") or {}
    trace_id = str((mission or {}).get("trace_id") or
                   contracts.stable_id("trace", compass.get("compass_id"), pre.get("prereg_id")))
    links = [
        contracts.new_link(trace_id=trace_id, stage="direction",
                           ref=contracts.stable_id("direction", compass.get("direction")),
                           status="ACTIVE" if compass.get("direction") else "BLOCKED",
                           authority_level="AUTHORITATIVE",
                           evidence=["GOALS-OCTOPUS.md"]),
        contracts.new_link(trace_id=trace_id, stage="goal",
                           ref=str(compass.get("goal_key") or ""),
                           status="FROZEN" if pre else "MISSING",
                           authority_level="AUTHORITATIVE" if pre else "MISSING",
                           evidence=[str(pre.get("prereg_id") or "")]),
        contracts.new_link(trace_id=trace_id, stage="prereg",
                           ref=str(pre.get("prereg_id") or ""),
                           status="RECORDED" if pre else "MISSING",
                           authority_level="AUTHORITATIVE" if pre else "MISSING",
                           evidence=["state/test_cycle/prereg.jsonl"]),
    ]
    if mission:
        links.append(contracts.new_link(
            trace_id=trace_id, stage="mission", ref=str(mission.get("mission_id") or mission.get("id") or ""),
            status=str(mission.get("status") or mission.get("state") or "UNKNOWN"),
            authority_level="AUTHORITATIVE", evidence=["mission-contract"]))
    else:
        links.append(contracts.new_link(
            trace_id=trace_id, stage="mission", ref="", status="NOT_LINKED",
            authority_level="MISSING", reason="goal-cycle-has-no-canonical-mission-link"))
    links.append(contracts.new_link(
        trace_id=trace_id, stage="action",
        ref=str((action_receipt or {}).get("action_id") or ""),
        status=str((action_receipt or {}).get("status") or "NOT_INTEGRATED"),
        authority_level="AUTHORITATIVE" if action_receipt else "MISSING",
        reason="" if action_receipt else "action-bridge-has-no-runtime-caller"))
    links.append(contracts.new_link(
        trace_id=trace_id, stage="receipt",
        ref=str((action_receipt or {}).get("idempotency_key") or ""),
        status="RECORDED" if action_receipt else "MISSING",
        authority_level="AUTHORITATIVE" if action_receipt else "MISSING"))
    links.append(contracts.new_link(
        trace_id=trace_id, stage="verdict", ref=str(verdict.get("prereg_id") or ""),
        status=str(verdict.get("verdict") or "PENDING"),
        authority_level="AUTHORITATIVE" if verdict else "MISSING",
        evidence=["state/test_cycle/verdicts.jsonl"] if verdict else []))
    links.append(contracts.new_link(
        trace_id=trace_id, stage="memory", ref="", status="NOT_LINKED",
        authority_level="MISSING", reason="verified-outcome-to-memory-link-not-proven-for-this-cycle"))
    complete = all(l["authority"] == "AUTHORITATIVE" and
                   l["status"] not in ("MISSING", "NOT_LINKED", "NOT_INTEGRATED", "PENDING")
                   for l in links)
    return {"schema": "unified-control.graph.v1", "trace_id": trace_id,
            "links": links, "end_to_end_complete": complete,
            "missing_stages": [l["stage"] for l in links
                               if l["authority"] != "AUTHORITATIVE" or
                               l["status"] in ("MISSING", "NOT_LINKED", "NOT_INTEGRATED", "PENDING")]}
