#!/usr/bin/env python3
"""phase_gate.py — دروازهٔ بین‌فازی (Decision Gate).

ORPHAN 2026-07-16: zero live callers (audit R-13) — kept, not deleted; candidate for _Archive on owner verdict.

قبل و بعد از هر فاز چک می‌کند. بدون عبور از این دروازه، فاز بعدی اجرا نمی‌شود.
ترکیب baseline + held-out + review_bus.

API:
  pre_phase_check(phase_id, requirements, state_dir, ledger_path) -> dict
  post_phase_check(phase_id, state_dir, ledger_path) -> dict
  transition_gate(from_phase, to_phase, ...) -> dict
  get_phase_state(state_dir) -> dict

طراحی: stdlib-only، $0. هیچ auto-advance — verdict انسانی لازم است.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ─── state persistence ──────────────────────────────────────────────────────────
_GATE_STATE_FILE = "phase-gate-state.json"


def _read_json_safe(path: Path) -> dict | None:
    try:
        if path.is_file():
            return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _write_json_safe(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def _default_state_dir() -> Path:
    return Path(__file__).resolve().parent / "state"


def _default_ops_dir() -> Path:
    return Path(__file__).resolve().parent


def _default_tests_dir() -> Path:
    return Path(__file__).resolve().parent / "tests"


def _default_ledger_path() -> Path:
    return (Path(__file__).resolve().parent.parent
            / "07 - Knowledge" / "genome-system" / "ledger")


# ─── phase state ────────────────────────────────────────────────────────────────

def get_phase_state(state_dir: Path | str | None = None) -> dict:
    """وضعیت فعلی فازها: کدام فاز، چه زمانی عبور کرد."""
    if state_dir is None:
        state_dir = _default_state_dir()
    else:
        state_dir = Path(state_dir)

    fpath = state_dir / _GATE_STATE_FILE
    return _read_json_safe(fpath) or {
        "current_phase": None,
        "transitions": [],
        "verdicts": {},
    }


def _update_phase_state(state_dir: Path, update: dict) -> dict:
    """به‌روزرسانی state با merge."""
    fpath = state_dir / _GATE_STATE_FILE
    state = get_phase_state(state_dir)
    state.update(update)
    _write_json_safe(fpath, state)
    return state


# ─── git checks ─────────────────────────────────────────────────────────────────

def _git_is_clean(ops_dir: Path) -> dict:
    """آیا git تمیز است (no uncommitted changes)?"""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(ops_dir), capture_output=True, text=True, timeout=30)
        dirty = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
        return {"clean": len(dirty) == 0, "dirty_files": dirty[:10]}
    except Exception as e:
        return {"clean": False, "dirty_files": [], "error": str(e)[:200]}


# ─── suite check ─────────────────────────────────────────────────────────────────

def _suite_all_green(tests_dir: Path, timeout_per_test: int = 120) -> dict:
    """اجرای run_all.py و بررسی سبز بودن."""
    run_all = tests_dir / "run_all.py"
    if not run_all.is_file():
        return {"all_green": False, "reason": "run_all.py not found"}

    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(run_all)],
            cwd=str(tests_dir), capture_output=True, text=True,
            timeout=timeout_per_test * 70)  # 70 test * timeout هرکدام
        stdout = r.stdout or ""
        # شمارش از خروجی
        all_green = "سبز" in stdout and r.returncode == 0
        return {"all_green": all_green, "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        return {"all_green": False, "reason": "timeout"}
    except Exception as e:
        return {"all_green": False, "reason": str(e)[:200]}


# ─── pre-phase check ────────────────────────────────────────────────────────────

def pre_phase_check(phase_id: str,
                    requirements: dict | None = None,
                    state_dir: Path | str | None = None,
                    ledger_path: Path | str | None = None) -> dict:
    """چک‌های قبل از شروع فاز.

    requirements (اختیاری): {baseline_required: bool, held_out_required: bool,
                                suite_green: bool, git_clean: bool}
    """
    if state_dir is None:
        state_dir = _default_state_dir()
    else:
        state_dir = Path(state_dir)
    if ledger_path is None:
        ledger_path = _default_ledger_path()
    else:
        ledger_path = Path(ledger_path)

    reqs = {
        "baseline_required": True,
        "held_out_required": True,
        "suite_green": True,
        "git_clean": True,
    }
    if requirements:
        reqs.update(requirements)

    ops_dir = _default_ops_dir()
    tests_dir = _default_tests_dir()
    blockers: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    # ۱) git clean
    if reqs["git_clean"]:
        git = _git_is_clean(ops_dir)
        checks["git_clean"] = git
        if not git["clean"]:
            blockers.append(f"git not clean: {len(git.get('dirty_files', []))} files")

    # ۲) baseline ثبت‌شده
    if reqs["baseline_required"]:
        try:
            from baseline import get_all_baselines
            baselines = get_all_baselines(state_dir)
            phase_bl = [b for b in baselines if b.get("phase_id") == phase_id]
            checks["baseline_exists"] = len(phase_bl) > 0
            if not phase_bl:
                blockers.append(f"no baseline for {phase_id}")
        except ImportError:
            checks["baseline_exists"] = False
            warnings.append("baseline module not found")

    # ۳) held-out eval
    if reqs["held_out_required"]:
        try:
            from held_out_evaluator import evaluate_held_out
            ho = evaluate_held_out(state_dir=state_dir,
                                   ledger_path=ledger_path,
                                   tests_dir=tests_dir)
            checks["held_out"] = ho
            if ho["overall_verdict"] != "pass":
                blockers.append(f"held-out eval: {ho['overall_verdict']}")
        except ImportError:
            checks["held_out"] = None
            warnings.append("held_out_evaluator module not found")

    # ۴) suite green
    if reqs["suite_green"]:
        suite = _suite_all_green(tests_dir)
        checks["suite_green"] = suite
        if not suite.get("all_green"):
            blockers.append("test suite not green")

    return {
        "ready": len(blockers) == 0,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "phase_id": phase_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# ─── post-phase check ──────────────────────────────────────────────────────────

def post_phase_check(phase_id: str,
                     state_dir: Path | str | None = None,
                     ledger_path: Path | str | None = None,
                     current_values: dict | None = None) -> dict:
    """چک‌های بعد از اتمام فاز.

    ۱) pre-registered metrics پاس شدند؟
    ۲) held-out eval هنوز pass؟
    ۳) no new conflicts در ORGANISM-STATE؟
    ۴) ledger hash-chain هنوز valid؟"""
    if state_dir is None:
        state_dir = _default_state_dir()
    else:
        state_dir = Path(state_dir)
    if ledger_path is None:
        ledger_path = _default_ledger_path()
    else:
        ledger_path = Path(ledger_path)

    ops_dir = _default_ops_dir()
    tests_dir = _default_tests_dir()
    checks: dict[str, Any] = {}
    all_passed = True

    # ۱) pre-registered metrics
    try:
        from baseline import check_pre_registered
        metrics = check_pre_registered(phase_id, state_dir=state_dir,
                                      current_values=current_values)
        checks["pre_registered_metrics"] = metrics
        if not metrics.get("all_passed", True):
            all_passed = False
    except ImportError:
        checks["pre_registered_metrics"] = None

    # ۲) held-out eval (regression check)
    try:
        from held_out_evaluator import evaluate_held_out
        ho = evaluate_held_out(state_dir=state_dir,
                               ledger_path=ledger_path,
                               tests_dir=tests_dir)
        checks["held_out"] = ho
        if ho["overall_verdict"] != "pass":
            all_passed = False
    except ImportError:
        checks["held_out"] = None

    # ۳) no new conflicts
    org_state = _read_json_safe(state_dir / "ORGANISM-STATE.json")
    conflicts = (org_state or {}).get("conflicts") or []
    checks["new_conflicts"] = len(conflicts)
    if conflicts:
        all_passed = False

    # ۴) ledger chain (فقط اگر مسیر واقعی باشد)
    try:
        if ledger_path.is_dir():
            from held_out_evaluator import verify_ledger_chain
            chain = verify_ledger_chain(ledger_path)
            checks["ledger_chain"] = chain
            if not chain.get("valid"):
                all_passed = False
        else:
            checks["ledger_chain"] = {"valid": None, "note": "ledger-path-not-found"}
    except ImportError:
        checks["ledger_chain"] = None

    verdict = "pass" if all_passed else "fail"

    return {
        "passed": all_passed,
        "verdict": verdict,
        "checks": checks,
        "phase_id": phase_id,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


# ─── transition gate ─────────────────────────────────────────────────────────────

def transition_gate(from_phase: str, to_phase: str,
                    state_dir: Path | str | None = None,
                    ledger_path: Path | str | None = None,
                    current_values: dict | None = None,
                    requirements: dict | None = None) -> dict:
    """ترکیب post_phase(from) + pre_phase(to).

    فقط اگر هر دو pass + human verdict → transition_allowed = True.
    هیچ auto-advance — نیاز به verdict انسانی."""
    if state_dir is None:
        state_dir = _default_state_dir()
    else:
        state_dir = Path(state_dir)

    # post-phase check فاز قبل
    post = post_phase_check(from_phase, state_dir=state_dir,
                            ledger_path=ledger_path,
                            current_values=current_values)

    # pre-phase check فاز بعد
    pre = pre_phase_check(to_phase, state_dir=state_dir,
                          ledger_path=ledger_path,
                          requirements=requirements)

    # handoff verify (review_bus)
    handoff_ok = True
    handoff_missing: list[str] = []
    try:
        from review_bus import verify_handoff, handoff_ready
        hf = verify_handoff(from_phase, to_phase, state_dir)
        handoff_ok = hf.get("complete", False)
        handoff_missing = hf.get("missing", [])

        hr = handoff_ready(from_phase, state_dir)
        pre["checks"]["handoff_ready"] = hr
        if not hr.get("ready"):
            handoff_ok = False
    except ImportError:
        pre["warnings"].append("review_bus module not found")

    transition_allowed = (post["passed"] and pre["ready"] and handoff_ok)

    # ثبت transition در state
    result = {
        "transition_allowed": transition_allowed,
        "from_phase": from_phase,
        "to_phase": to_phase,
        "post_phase": {"passed": post["passed"], "verdict": post["verdict"]},
        "pre_phase": {"ready": pre["ready"], "blockers": pre["blockers"]},
        "handoff_complete": handoff_ok,
        "handoff_missing": handoff_missing,
        "human_verdict_required": True,  # هرگز auto-advance
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # اگر transition_allowed، ثبت در state (منتظر human verdict)
    if transition_allowed:
        _update_phase_state(state_dir, {
            "current_phase": to_phase,
            "last_transition": {
                "from": from_phase, "to": to_phase,
                "ts": result["ts"],
                "awaiting_human_verdict": True,
            }
        })

    return result
