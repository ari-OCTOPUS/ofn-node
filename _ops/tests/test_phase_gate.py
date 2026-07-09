#!/usr/bin/env python3
"""test_phase_gate.py — تستِ ماژول phase_gate.py + review_bus.py.

$0 آفلاین: state_dir با tmpdir، held-out/baseline با import واقعی.
git_clean و suite_green در این تست fake می‌شوند (git/subprocess inject نیست).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

import phase_gate
import review_bus


def _make_state(state_dir: Path) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)


# ── review_bus تست‌ها ──────────────────────────────────────────────────────────

def t_submit_and_get_review():
    """submit_review + get_review roundtrip."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        path = review_bus.submit_review("phase-0", "PHASE_RESULT",
                                         {"summary": "test"}, state_dir=sd)
        assert Path(path).is_file()
        got = review_bus.get_review("phase-0", "PHASE_RESULT", state_dir=sd)
        assert got is not None
        assert got["phase_id"] == "phase-0"
        assert got["review_type"] == "PHASE_RESULT"
        assert got["payload"]["summary"] == "test"


def t_submit_invalid_type_raises():
    """review_type نامعتبر → ValueError."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        raised = False
        try:
            review_bus.submit_review("p", "INVALID", {}, state_dir=sd)
        except ValueError:
            raised = True
        assert raised, "ValueError expected for invalid review_type"


def t_get_review_not_found():
    """review ناموجود → None."""
    with tempfile.TemporaryDirectory() as td:
        got = review_bus.get_review("nonexistent", "AUDIT_REPORT",
                                     state_dir=Path(td))
        assert got is None


def t_verify_handoff_phase0():
    """فاز ۰ فقط PHASE_RESULT نیاز دارد."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        review_bus.submit_review("phase-0", "PHASE_RESULT", {},
                                 state_dir=sd)
        result = review_bus.verify_handoff("phase-0", "phase-1", state_dir=sd)
        assert result["complete"] is True
        assert len(result["missing"]) == 0


def t_verify_handoff_missing():
    """فاز ۱ بدون AUDIT_REPORT → incomplete."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        result = review_bus.verify_handoff("phase-1", "phase-2", state_dir=sd)
        assert result["complete"] is False
        assert "AUDIT_REPORT" in result["missing"]


def t_mark_human_verdict():
    """verdict انسانی ثبت می‌شود."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        review_bus.submit_review("p", "PHASE_RESULT", {}, state_dir=sd)
        rv = review_bus.mark_human_verdict("p", "approved", "looks good",
                                            state_dir=sd)
        assert rv["verdict"] == "approved"
        assert rv["updated"] == 1
        # verify
        reviews = review_bus.get_all_reviews("p", state_dir=sd)
        assert all(r.get("verdict") == "approved" for r in reviews)


def t_handoff_ready():
    """handoff_ready وقتی همه reviewed → True."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        review_bus.submit_review("p", "PHASE_RESULT", {}, state_dir=sd)
        review_bus.mark_human_verdict("p", "approved", state_dir=sd)
        hr = review_bus.handoff_ready("p", state_dir=sd)
        assert hr["ready"] is True


def t_handoff_not_ready_unreviewed():
    """review بدون verdict → not ready."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        review_bus.submit_review("p", "PHASE_RESULT", {}, state_dir=sd)
        hr = review_bus.handoff_ready("p", state_dir=sd)
        assert hr["ready"] is False
        assert hr["unreviewed"] == 1


def t_handoff_not_ready_rejected():
    """review rejected → not ready."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        review_bus.submit_review("p", "PHASE_RESULT", {}, state_dir=sd)
        review_bus.mark_human_verdict("p", "rejected", "bad", state_dir=sd)
        hr = review_bus.handoff_ready("p", state_dir=sd)
        assert hr["ready"] is False
        assert hr["rejected"] == 1


# ── phase_gate تست‌ها ──────────────────────────────────────────────────────────

def t_phase_state_default():
    """state پیش‌فرض خالی است."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        state = phase_gate.get_phase_state(sd)
        assert state["current_phase"] is None
        assert state["transitions"] == []


def t_pre_phase_no_baseline():
    """بدون baseline → blocker."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        _make_state(sd)
        # fake: git clean + held-out skip + suite skip
        result = phase_gate.pre_phase_check(
            "test-phase",
            requirements={"baseline_required": True,
                          "held_out_required": False,
                          "suite_green": False,
                          "git_clean": False},
            state_dir=sd)
        assert result["ready"] is False
        assert any("baseline" in b for b in result["blockers"])


def t_pre_phase_all_requirements_off():
    """همه requirements خاموش → ready."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        _make_state(sd)
        result = phase_gate.pre_phase_check(
            "test-phase",
            requirements={"baseline_required": False,
                          "held_out_required": False,
                          "suite_green": False,
                          "git_clean": False},
            state_dir=sd)
        assert result["ready"] is True


def t_post_phase_no_metrics():
    """بدون pre-registered metrics → pass (nothing to fail)."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        _make_state(sd)
        result = phase_gate.post_phase_check(
            "test-phase", state_dir=sd,
            ledger_path="/nonexistent")
        assert result["passed"] is True


def t_transition_gate_structure():
    """transition_gate ساختار درست دارد."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td)
        _make_state(sd)
        result = phase_gate.transition_gate(
            "phase-0", "phase-1", state_dir=sd,
            ledger_path="/nonexistent",
            requirements={"baseline_required": False,
                          "held_out_required": False,
                          "suite_green": False,
                          "git_clean": False})
        assert "transition_allowed" in result
        assert "from_phase" in result
        assert "to_phase" in result
        assert "human_verdict_required" in result
        assert result["human_verdict_required"] is True


if __name__ == "__main__":
    failed = harness.run([
        ("submit + get roundtrip", t_submit_and_get_review),
        ("invalid type → ValueError", t_submit_invalid_type_raises),
        ("review ناموجود = None", t_get_review_not_found),
        ("handoff phase-0 complete", t_verify_handoff_phase0),
        ("handoff missing AUDIT_REPORT", t_verify_handoff_missing),
        ("human verdict ثبت", t_mark_human_verdict),
        ("handoff ready", t_handoff_ready),
        ("handoff unreviewed = not ready", t_handoff_not_ready_unreviewed),
        ("handoff rejected = not ready", t_handoff_not_ready_rejected),
        ("phase state default", t_phase_state_default),
        ("pre-phase no baseline → blocker", t_pre_phase_no_baseline),
        ("pre-phase all off → ready", t_pre_phase_all_requirements_off),
        ("post-phase no metrics → pass", t_post_phase_no_metrics),
        ("transition_gate structure", t_transition_gate_structure),
    ])
    sys.exit(1 if failed else 0)
