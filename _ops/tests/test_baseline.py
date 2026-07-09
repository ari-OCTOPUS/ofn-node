#!/usr/bin/env python3
"""test_baseline.py — تستِ ماژول baseline.py (ضبط و مقایسهٔ snapshot).

$0 آفلاین: state_dir و ops_dir با tmpdir تزریق می‌شوند.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

import baseline


def _make_fake_state(state_dir: Path) -> None:
    """ORGANISM-STATE.json + fitness-latest.json ساختگی."""
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "ORGANISM-STATE.json").write_text(json.dumps({
        "ts": "2026-07-10T12:00:00",
        "halted": None,
        "frozen": False,
        "stop_organism": False,
        "conflicts": [],
        "suspect_zero_total": 0,
        "germline_lag_h": 5.0,
        "germline_alert": "warn",
        "sigma_effective": 0.8,
        "sigma_zone": "healthy",
        "fitness_authoritative": False,
        "month": {"key": "2026-07", "musd": 100, "usd": 0.1, "aud": 0.15},
        "today": {"musd": 5, "usd": 0.005},
    }, ensure_ascii=False), "utf-8")
    (state_dir / "fitness-latest.json").write_text(json.dumps({
        "cells": {
            "ZIMAN": {"fit": 0.65, "sent": 10, "rejected": 3},
        }
    }, ensure_ascii=False), "utf-8")


def _make_fake_ops(ops_dir: Path) -> None:
    """فایل‌های پولی ساختگی برای fingerprint."""
    budget_dir = ops_dir / "budget"
    budget_dir.mkdir(parents=True, exist_ok=True)
    for name in ("money_gate.py", "capability_gate.py",
                 "organ_gate.py", "budget_gate.py", "fitness.py"):
        (budget_dir / name).write_text(f"# {name}\n", "utf-8")


# ── تست‌ها ──────────────────────────────────────────────────────────────────────

def t_capture_creates_file():
    """capture_baseline فایل JSON در state_dir می‌سازد."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        od = Path(td) / "ops"
        _make_fake_state(sd)
        _make_fake_ops(od)
        path = baseline.capture_baseline("test-phase", "pre", state_dir=sd, ops_dir=od)
        assert Path(path).is_file(), f"فایل ساخته نشد: {path}"
        doc = json.loads(Path(path).read_text("utf-8"))
        assert doc["phase_id"] == "test-phase"
        assert doc["label"] == "pre"
        assert "snapshot" in doc
        assert "money_fingerprint" in doc["snapshot"]


def t_snapshot_has_expected_fields():
    """snapshot تمام fields کلیدی را دارد."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        od = Path(td) / "ops"
        _make_fake_state(sd)
        _make_fake_ops(od)
        path = baseline.capture_baseline("t", "x", state_dir=sd, ops_dir=od)
        doc = json.loads(Path(path).read_text("utf-8"))
        snap = doc["snapshot"]
        for f in ("halted", "frozen", "conflicts", "sigma_effective",
                   "month", "today", "fitness_cells"):
            assert f in snap, f"field {f} missing from snapshot"


def t_compare_identical_passes():
    """مقایسهٔ snapshot یکسان با خودش = pass."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        od = Path(td) / "ops"
        _make_fake_state(sd)
        _make_fake_ops(od)
        path = baseline.capture_baseline("t", "pre", state_dir=sd, ops_dir=od)
        result = baseline.compare_baseline(path, state_dir=sd, ops_dir=od)
        assert result["passed"] is True
        assert result["verdict"] == "pass"
        assert len(result["diffs"]) == 0


def t_compare_detects_new_conflicts():
    """مقایسهٔ snapshot با conflicts جدید = regression."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        od = Path(td) / "ops"
        _make_fake_state(sd)
        _make_fake_ops(od)
        path = baseline.capture_baseline("t", "pre", state_dir=sd, ops_dir=od)
        # conflicts اضافه کن
        state = json.loads((sd / "ORGANISM-STATE.json").read_text("utf-8"))
        state["conflicts"] = [{"type": "FREEZE", "reason": "test"}]
        (sd / "ORGANISM-STATE.json").write_text(
            json.dumps(state, ensure_ascii=False), "utf-8")
        result = baseline.compare_baseline(path, state_dir=sd, ops_dir=od)
        assert result["passed"] is False
        assert result["verdict"] == "regression-detected"


def t_compare_detects_money_change():
    """تغییر فایل پولی = money_changed flag."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        od = Path(td) / "ops"
        _make_fake_state(sd)
        _make_fake_ops(od)
        path = baseline.capture_baseline("t", "pre", state_dir=sd, ops_dir=od)
        # یک فایل پولی را تغییر بده
        (od / "budget" / "money_gate.py").write_text("# changed!\n", "utf-8")
        result = baseline.compare_baseline(path, state_dir=sd, ops_dir=od)
        assert result["money_changed"] is True
        assert result["verdict"] == "money-code-changed"


def t_pre_register_and_check():
    """pre_register_metric و check_pre_registered کار می‌کنند."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        baseline.pre_register_metric(
            "test-phase", "effects_pending", threshold=3.0,
            direction="below", state_dir=sd,
            baseline_value=10.0,
            description="pending باید زیر ۳ بیاید")
        result = baseline.check_pre_registered(
            "test-phase", state_dir=sd,
            current_values={"effects_pending": 2.0})
        assert result["all_passed"] is True
        assert len(result["metrics"]) == 1
        assert result["metrics"][0]["passed"] is True


def t_pre_register_fail_above_threshold():
    """threshold above رد نشده = fail."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        baseline.pre_register_metric(
            "test-phase", "effects_pending", threshold=3.0,
            direction="below", state_dir=sd)
        result = baseline.check_pre_registered(
            "test-phase", state_dir=sd,
            current_values={"effects_pending": 5.0})
        assert result["all_passed"] is False
        assert result["metrics"][0]["passed"] is False


def t_get_all_baselines():
    """get_all_baselines لیست baselineها را برمی‌گرداند."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        od = Path(td) / "ops"
        _make_fake_state(sd)
        _make_fake_ops(od)
        baseline.capture_baseline("p1", "pre", state_dir=sd, ops_dir=od)
        baseline.capture_baseline("p2", "pre", state_dir=sd, ops_dir=od)
        bls = baseline.get_all_baselines(sd)
        assert len(bls) == 2
        assert {b["phase_id"] for b in bls} == {"p1", "p2"}


def t_compare_missing_baseline():
    """baseline ناموجود = pass=False."""
    result = baseline.compare_baseline("/nonexistent/path.json")
    assert result["passed"] is False
    assert result["verdict"] == "baseline-file-not-found"


if __name__ == "__main__":
    failed = harness.run([
        ("capture فایل می‌سازد", t_capture_creates_file),
        ("snapshot fields کامل", t_snapshot_has_expected_fields),
        ("مقایسهٔ یکسان = pass", t_compare_identical_passes),
        ("conflicts جدید = regression", t_compare_detects_new_conflicts),
        ("تغییر فایل پولی = money-changed", t_compare_detects_money_change),
        ("pre-register + check صحیح", t_pre_register_and_check),
        ("pre-register threshold رد", t_pre_register_fail_above_threshold),
        ("get_all_baselines", t_get_all_baselines),
        ("baseline ناموجود = fail", t_compare_missing_baseline),
    ])
    sys.exit(1 if failed else 0)
