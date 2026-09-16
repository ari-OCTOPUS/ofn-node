# -*- coding: utf-8 -*-
"""Small testable hypotheses. API proposals are untrusted; local evidence wins."""
from __future__ import annotations

from typing import Any

from .contracts import Hypothesis, append_jsonl, new_ids
from . import STATE_DIR

_HYP = {
    "memory": Hypothesis(
        hypothesis_id="",
        target_layer="memory",
        target_id="P0-MEMORY-GATE",
        problem="Memory gate tests crash/fail: F3 rejects missing confidence; get() returns None on PENDING rows (t_h TypeError).",
        evidence_refs=[
            "_ops/state/waves/WAVE1-PREFLIGHT-2026-08-21.json",
            "_ops/memory/memory_store.py:insert F3",
            "_ops/memory/memory_store.py:get ADMITTED-only",
            "_ops/tests/test_memory_gate.py HEAD vs working tree",
        ],
        root_cause_candidate=(
            "Two stacked contracts: (1) F3 requires confidence on insert; "
            "(2) A1 two-phase admission stages unattributed writes PENDING, "
            "invisible to get/search until promote(). Tests called submit() then "
            "subscripted get() without confidence and without promote()."
        ),
        predicted_result=(
            "Adding confidence to commit-path tests + _commit()/promote() before "
            "get/search, plus t_k F3 and t_l staging regression, turns the suite green "
            "without changing production admission rules."
        ),
        files_allowed=["_ops/tests/test_memory_gate.py"],
        tests_required=["_ops/tests/test_memory_gate.py"],
        risk="LOW",
        rollback="Restore HEAD test_memory_gate.py in the worktree.",
        time_budget_minutes=30,
    ),
    "brain": Hypothesis(
        hypothesis_id="",
        target_layer="brain",
        target_id="P1-BRAIN-CALIBRATION",
        problem="calibration-latest.json is written but improve.py does not consume it (S-A03).",
        evidence_refs=["loop:S-A03", "_ops/state/cortex/calibration-latest.json",
                       "_ops/cortex/improve.py HEAD gather_signals"],
        root_cause_candidate="gather_signals never read calibration-latest; generate_proposals never emitted a calibration proposal.",
        predicted_result="After a bounded read of calibration-latest, generate_proposals emits a propose-only calibration item when n/brier present.",
        files_allowed=["_ops/cortex/improve.py",
                       "_ops/tests/test_improve_reads_calibration.py"],
        tests_required=["_ops/tests/test_improve_reads_calibration.py"],
        risk="LOW",
        rollback="Revert improve.py calibration block; delete the new test.",
        time_budget_minutes=30,
    ),
    "heart": Hypothesis(
        hypothesis_id="",
        target_layer="heart",
        target_id="P1-HEART-ORPHAN",
        problem="LOOP-LIVE-ORPHAN-MISSING-SUPERVISION: watchdog code exists, organism never calls it.",
        evidence_refs=["_ops/orphan_watchdog.py", "NEED-20260821-004",
                       "LOOP-LIVE-ORPHAN-MISSING-SUPERVISION"],
        root_cause_candidate="No organism-tick caller; recovery_plan can restart. Observe-only path must classify without restart side effects.",
        predicted_result="organism tick calls tick(observe_only=True); missing gateway yields missing_gateway_observed not restart; orphan child still never restarted.",
        files_allowed=["_ops/orphan_watchdog.py", "_ops/organism.py",
                       "_ops/tests/test_orphan_watchdog.py"],
        tests_required=["_ops/tests/test_orphan_watchdog.py"],
        risk="LOW",
        rollback="Remove organism hook; drop observe_only branch.",
        time_budget_minutes=30,
    ),
}


def make_hypothesis(layer: str, diagnosis: dict[str, Any]) -> Hypothesis:
    h = _HYP[layer]
    _, hid, _ = new_ids(layer)
    h.hypothesis_id = hid
    ranked = (diagnosis.get("by_layer") or {}).get(layer) or {}
    if ranked:
        h.target_id = str(ranked.get("id") or h.target_id)
    rec = h.to_dict()
    rec["diagnosis_score"] = ranked.get("priority_score")
    append_jsonl(STATE_DIR / "hypotheses.jsonl", rec)
    return h
