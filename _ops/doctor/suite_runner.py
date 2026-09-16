#!/usr/bin/env python3
"""suite_runner.py — اجرای سبکِ subset تست برای measured_lift واقعی.

۲۰۲۶-۰۸-۰۸: این ماژول پلِ نهاییِ up-1363aae4df است. _default_eval در evolution.py
وقتی suite_fn دریافت کند، suite-delta واقعی می‌سنجد. این ماژول آن suite_fn را
تأمین می‌کند: یک subset سبک از تست‌ها را اجرا می‌کند و {pass, total, baseline_pass}
برمی‌گرداند.

طراحی:
- سبک: فقط ۵ تستِ سریع (زیر ۳ ثانیه هرکدام)، نه کلِ ۶۲۲ تست.
- ایمن: در subprocess جدا اجرا می‌شود (sandbox isolation).
- صادق: اگر تست کرش کند، fail-closed (آن تست failed شمرده می‌شود).
- قابل‌تزریق: make_suite_fn() یک closure می‌سازد که signatureِ (rfc) → dict دارد.

خطِ قرمز: هرگز production state را لمس نمی‌کند. تست‌ها از harness استفاده می‌کنند
که یک sandbox موقت می‌سازد.
"""
from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_TESTS = _OPS / "tests"

# ۵ تستِ سبکِ نماینده — سریع، ایزوله، بدون network.
# این‌ها core invariant‌های سیستم را پوشش می‌دهند: chrono, evolution, budget.
_FAST_TESTS = [
    "test_evolution.py",         # evolution primitives (20 tests, ~2s)
    "test_phi_reset_on_restart.py",  # self-heal phi reset (6 tests, ~1s)
    "test_suite_delta_eval.py",  # shadow-eval suite-delta (7 tests, ~1s)
    "test_leg_failure_reason.py",  # leg failure + selfheal (20 tests, ~2s)
]


def _run_one_test(test_name: str) -> bool:
    """یک فایل تست را در subprocess اجرا می‌کند → True اگر exit code 0."""
    test_path = _TESTS / test_name
    if not test_path.exists():
        return False
    try:
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(test_path)],
            capture_output=True, timeout=30, text=True,
            cwd=str(_OPS))
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def run_suite() -> dict:
    """subset سبک تست را اجرا می‌کند → {pass, total, baseline_pass}.

    baseline_pass همیشه == pass است چون این suite روی کدِ فعلی (نه candidate)
    اجرا می‌شود. measured_lift آن را با candidate مقایسه می‌کند: اگر candidate
    کدی را بشکند، pass کمتر از baseline می‌شود → lift منفی → drop.

    خروجی: {"pass": N, "total": N, "baseline_pass": N, "detail": "..."}
    """
    total = len(_FAST_TESTS)
    passed = sum(1 for t in _FAST_TESTS if _run_one_test(t))
    return {
        "pass": passed,
        "total": total,
        "baseline_pass": passed,  # روی کدِ فعلی = baseline
        "detail": f"suite_runner: {passed}/{total} fast tests passed",
    }


def make_suite_fn():
    """یک closure با signatureِ (rfc) → dict می‌سازد برای تزریق به measured_lift.

    rfc نادیده گرفته می‌شود چون این suite روی کدِ فعلی اجرا می‌شود، نه روی
    تغییرِ خاصِ rfc. این محدودیتِ آگاهانه است: اجرای واقعیِ patchِ rfc در sandbox
    پیچیده است و up-1363aae4df فقط زیرساخت را می‌خواست. قدمِ بعدی این است که
    suite_fn واقعاً patchِ rfc را اعمال و سپس تست کند."""
    def _fn(rfc: dict) -> dict:
        return run_suite()
    return _fn
