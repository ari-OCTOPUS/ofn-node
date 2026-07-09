#!/usr/bin/env python3
"""test_held_out_evaluator.py — تستِ ماژول held_out_evaluator.py.

$0 آفلاین: tests_dir با tmpdir تزریق می‌شود، subprocess واقعی روی ۵ تست canary
اجرا می‌شود (همان الگوی run_all.py).
"""
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

import held_out_evaluator as hoe


def _make_fake_tests_dir(td: Path) -> Path:
    """دایرکتوری تست ساختگی با ۲ تست canary واقعی ( budget_gate و money_gate)."""
    # real tests را کپی کن
    real_tests = _HERE
    fake_dir = td / "tests"
    fake_dir.mkdir(parents=True, exist_ok=True)

    # هر ۵ تست canary را symlink/copy کن
    for name in hoe.FIXED_CANARY_TESTS:
        src = real_tests / name
        if src.is_file():
            (fake_dir / name).write_text(src.read_text("utf-8"), "utf-8")

    # harness را هم کپی کن
    harness_src = real_tests / "harness.py"
    if harness_src.is_file():
        (fake_dir / "harness.py").write_text(harness_src.read_text("utf-8"), "utf-8")

    # budget را هم کپی کن (وابستگی تست‌ها)
    budget_dir = _HERE.parent / "budget"
    fake_budget = td / "budget"
    fake_budget.mkdir(parents=True, exist_ok=True)
    for f in budget_dir.glob("*.py"):
        (fake_budget / f.name).write_text(f.read_text("utf-8"), "utf-8")

    return fake_dir


def _make_fake_experiments(state_dir: Path) -> None:
    """experiment-seal ساختگی."""
    exp_dir = state_dir / "experiments"
    exp_dir.mkdir(parents=True, exist_ok=True)
    import time
    # یک expired
    (exp_dir / "exp-1.json").write_text(json.dumps({
        "exp_id": "exp-1", "end_ts": time.time() - 3600
    }, ensure_ascii=False), "utf-8")
    # یک active
    (exp_dir / "exp-2.json").write_text(json.dumps({
        "exp_id": "exp-2", "end_ts": time.time() + 86400
    }, ensure_ascii=False), "utf-8")


# ── تست‌ها ──────────────────────────────────────────────────────────────────────

def t_fixed_suite_runs():
    """fixed suite روی ۵ تست واقعی اجرا و نتیجه برمی‌گرداند."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fake_tests = _make_fake_tests_dir(td)
        result = hoe.run_fixed_suite(tests_dir=fake_tests)
        assert "passed" in result
        assert "total" in result
        assert result["total"] == 5
        assert len(result["details"]) == 5


def t_fixed_suite_detects_missing():
    """تست ناموجود = status=missing."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fake_tests = td / "tests"
        fake_tests.mkdir()
        result = hoe.run_fixed_suite(tests_dir=fake_tests)
        assert result["passed"] == 0
        missing = [d for d in result["details"] if d.get("status") == "missing"]
        assert len(missing) == 5


def t_ledger_chain_not_found():
    """ledger ناموجود = valid=None (skipped, نه fail)."""
    result = hoe.verify_ledger_chain(ledger_path="/nonexistent")
    assert result["valid"] is None


def t_sealed_predictions_counts():
    """active و expired درست شمرده می‌شوند."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        _make_fake_experiments(sd)
        result = hoe.check_sealed_predictions(state_dir=sd)
        assert result["active"] == 1
        assert result["expired"] == 1
        assert len(result["results"]) == 2


def t_sealed_no_experiments():
    """بدون experiments = 0 active."""
    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        sd.mkdir()
        result = hoe.check_sealed_predictions(state_dir=sd)
        assert result["active"] == 0


def t_evaluate_held_out_structure():
    """evaluate_held_out ساختار خروجی درست دارد."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        sd = td / "state"
        sd.mkdir()
        fake_tests = _make_fake_tests_dir(td)
        result = hoe.evaluate_held_out(
            state_dir=sd, ledger_path="/nonexistent",
            tests_dir=fake_tests)
        assert "layers" in result
        assert "overall_verdict" in result
        assert "anti_hacking_flag" in result
        assert "summary" in result
        assert "fixed_suite" in result["layers"]
        assert "ledger_chain" in result["layers"]


def t_anti_hacking_flag():
    """internal pass + held-out fail = anti_hacking_flag=True."""
    result = hoe.evaluate_held_out(
        internal_metric_pass=True,
        tests_dir=Path("/nonexistent"),
        ledger_path="/nonexistent")
    # tests_dir ناموجود → suite fails
    assert result["anti_hacking_flag"] is True


def t_anti_hacking_no_flag():
    """internal pass + held-out pass = anti_hacking_flag=False."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        sd = td / "state"
        sd.mkdir()
        fake_tests = _make_fake_tests_dir(td)
        result = hoe.evaluate_held_out(
            state_dir=sd, ledger_path="/nonexistent",
            tests_dir=fake_tests,
            internal_metric_pass=True)
        # اگر suite pass → anti_hacking باید False باشد
        if result["layers"]["fixed_suite"]["passed"] == result["layers"]["fixed_suite"]["total"]:
            assert result["anti_hacking_flag"] is False


if __name__ == "__main__":
    failed = harness.run([
        ("fixed suite اجرا می‌شود", t_fixed_suite_runs),
        ("تست ناموجود = missing", t_fixed_suite_detects_missing),
        ("ledger ناموجود = invalid", t_ledger_chain_not_found),
        ("sealed predictions شمارش", t_sealed_predictions_counts),
        ("بدون experiments = 0", t_sealed_no_experiments),
        ("ساختار evaluate_held_out", t_evaluate_held_out_structure),
        ("anti-hacking flag فعال", t_anti_hacking_flag),
        ("anti-hacking بدون flag", t_anti_hacking_no_flag),
    ])
    sys.exit(1 if failed else 0)
