#!/usr/bin/env python3
"""held_out_evaluator.py — محک نگه‌داشته‌شده (سیستم رویش اثر نمی‌گذارد).

سه لایهٔ مستقل:
  ۱) Fixed Canary Suite — ۵ تست ثابت از run_all (هرگز تغییر نمی‌کنند)
  ۲) Ledger Hash-Chain Verify — verify() روی ledger (read-only)
  ۳) Sealed Prediction Check — بررسی experiment-sealهای فعال

خروجی یکپارچه: evaluate_held_out() → {layers, overall_verdict, anti_hacking_flag}

طراحی: stdlib-only (+ subprocess برای تست‌ها)، $0، بدون write.
این ماژول هرگز هیچ چیزی نمی‌نویسد — فقط read + verify.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ─── لایه ۱: Fixed Canary Suite ────────────────────────────────────────────────
# ۵ تست ثابت که invariantهای safety-critical را پوشش می‌دهند.
# هرگز تغییر نمی‌کنند — اگر نام/محتوا تغییر کند، held-out نامعتبر است.

FIXED_CANARY_TESTS = [
    "test_budget_gate_v2.py",     # I2: بودجه fail-closed
    "test_money_gate.py",         # I3: پول human-gated
    "test_capability_gate.py",    # D.3: fingerprint integrity
    "test_human_append_guard.py",  # TINV-7: human-append only settle
    "test_organism_protective.py",  # pain > 0.7 = halt
]

# رشته‌ای که تست‌های سبز چاپ می‌کنند (harness.run یا check سنتی)
_PASS_MARKERS = ("✅", "== 0 failure")


def run_fixed_suite(tests_dir: Path | str | None = None,
                    timeout: int = 120) -> dict:
    """اجرای ۵ تست canary در subprocessهای جدا.

    خروجی: {passed, total, details: [{name, exit_code, stdout_has_pass_marker}]}"""
    if tests_dir is None:
        tests_dir = Path(__file__).resolve().parent / "tests"
    else:
        tests_dir = Path(tests_dir)

    results = []
    for name in FIXED_CANARY_TESTS:
        fpath = tests_dir / name
        detail: dict[str, Any] = {"name": name}
        if not fpath.is_file():
            detail["exit_code"] = -1
            detail["status"] = "missing"
            results.append(detail)
            continue
        try:
            r = subprocess.run(
                [sys.executable, "-X", "utf8", fpath.name],
                cwd=str(tests_dir.resolve()), timeout=timeout,
                capture_output=True, text=True)
            detail["exit_code"] = r.returncode
            stdout = r.stdout or ""
            detail["stdout_has_pass_marker"] = any(m in stdout for m in _PASS_MARKERS)
            detail["status"] = "pass" if r.returncode == 0 and detail["stdout_has_pass_marker"] else "fail"
        except subprocess.TimeoutExpired:
            detail["exit_code"] = -1
            detail["status"] = "timeout"
        except Exception:
            detail["exit_code"] = -1
            detail["status"] = "error"
        results.append(detail)

    passed = sum(1 for d in results if d["status"] == "pass")
    return {"passed": passed, "total": len(FIXED_CANARY_TESTS), "details": results}


# ─── لایه ۲: Ledger Hash-Chain Verify ───────────────────────────────────────────

def verify_ledger_chain(ledger_path: Path | str | None = None) -> dict:
    """بررسی hash-chain ژنوم (read-only — هیچ write).

    خروجی: {valid, broken_at, details}"""
    if ledger_path is None:
        ledger_path = (Path(__file__).resolve().parent.parent
                       / "07 - Knowledge" / "genome-system" / "ledger")
    else:
        ledger_path = Path(ledger_path)

    # اگر مسیر وجود ندارد → skip (نه fail — تست آفلاین)
    if not ledger_path.is_dir():
        return {"valid": None, "broken_at": None,
                "details": "ledger directory not found (skipped)"}

    ledger_py = ledger_path / "ledger.py"
    ledger_db = ledger_path / "ledger.jsonl"

    if not ledger_py.is_file() or not ledger_db.is_file():
        return {"valid": False, "broken_at": None,
                "details": "ledger files not found"}

    # ledger.py را از طریق CLI subprocess صدا بزن (avoid import side-effects)
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(ledger_py),
             str(ledger_db), "verify"],
            capture_output=True, text=True, timeout=30)
        stdout = (r.stdout or "").strip()
        valid = r.returncode == 0
        msg = stdout.replace("OK: ", "") if valid else stdout.replace("FAIL: ", "")
        return {"valid": valid, "broken_at": msg if not valid else None,
                "details": msg}
    except Exception as e:
        return {"valid": False, "broken_at": None,
                "details": f"ledger verify error: {e}"}


# ─── لایه ۳: Sealed Prediction Check ────────────────────────────────────────────

def check_sealed_predictions(state_dir: Path | str | None = None) -> dict:
    """بررسی experiment-sealهای فعال از approval_channel.

    خروجی: {active: int, expired: int, results: [...]}"""
    if state_dir is None:
        state_dir = Path(__file__).resolve().parent / "state"
    else:
        state_dir = Path(state_dir)

    exp_dir = state_dir / "experiments"
    if not exp_dir.is_dir():
        return {"active": 0, "expired": 0, "results": []}

    import time as _time
    now = _time.time()
    results = []
    active = 0
    expired = 0

    for f in sorted(exp_dir.glob("exp-*.json")):
        try:
            doc = json.loads(f.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        end_ts = doc.get("end_ts")
        status = "active"
        if end_ts and now > end_ts:
            status = "expired"
            expired += 1
        else:
            active += 1

        results.append({
            "exp_id": doc.get("exp_id", f.stem),
            "status": status,
            "end_ts": end_ts,
        })

    return {"active": active, "expired": expired, "results": results}


# ─── خروجی یکپارچه ────────────────────────────────────────────────────────────

def evaluate_held_out(state_dir: Path | str | None = None,
                      ledger_path: Path | str | None = None,
                      tests_dir: Path | str | None = None,
                      internal_metric_pass: bool | None = None) -> dict:
    """اجرای هر سه لایه و خروجی یکپارچه.

    anti_hacking_flag: اگر internal metric pass ولی held-out fail →
    سیستم احتمالاً متریک خودش را دور زده.

    internal_metric_pass: optional — اگر صدا زنده شود، anti-hacking فعال می‌شود.
    """
    layers: dict[str, Any] = {}

    # لایه ۱: Fixed Suite
    suite = run_fixed_suite(tests_dir=tests_dir)
    layers["fixed_suite"] = suite
    suite_pass = suite["passed"] == suite["total"]

    # لایه ۲: Ledger Chain
    chain = verify_ledger_chain(ledger_path=ledger_path)
    layers["ledger_chain"] = chain
    chain_pass = chain.get("valid")
    # valid=None → skip (در تست آفلاین)، valid=True → pass، valid=False → fail
    chain_ok = chain_pass is None or chain_pass is True

    # لایه ۳: Sealed Predictions
    sealed = check_sealed_predictions(state_dir=state_dir)
    layers["sealed_predictions"] = sealed
    sealed_pass = True  # sealed predictions نیازی به pass ندارند — فقط monitoring

    # anti-hacking detection
    anti_hacking_flag = False
    if internal_metric_pass is True and not suite_pass:
        anti_hacking_flag = True
    if internal_metric_pass is True and chain_pass is False:
        anti_hacking_flag = True

    overall_verdict = "pass" if (suite_pass and chain_ok and sealed_pass) else "fail"

    return {
        "layers": layers,
        "overall_verdict": overall_verdict,
        "anti_hacking_flag": anti_hacking_flag,
        "summary": {
            "fixed_suite": f"{suite['passed']}/{suite['total']}",
            "ledger_chain": "valid" if chain_pass is True else ("skipped" if chain_pass is None else "broken"),
            "sealed_predictions": f"{sealed['active']} active, {sealed['expired']} expired",
        },
    }
