#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stop_probe.py — اوراکلِ واحدِ «آیا یک supervisor مجاز به احیا/راه‌اندازی هست؟».

منبعِ یگانه برای همهٔ supervisorها (python + PowerShell watchdogها). تا امروز watchdogهای
`.ps1`ی live/cortex فقط STOP-LIVE/STOP-CORTEXِ خودشان را می‌دیدند و **پنیکِ سراسری (HALT-ALL)
و STOP معمار را نادیده می‌گرفتند** (delta-scan D-G). این ماژول قرارداد را یک‌جا می‌کند:

  should_yield() → (yield: bool, reason)
    yield=True اگر: HALT-ALL یا STOP معمار یا STOP-ORGANISM حاضر باشد (پنیک/کیل مقدم بر همه).

CLI برای `.ps1`:  `python stop_probe.py --global-halt`  → exit 3 اگر پنیکِ سراسری (HALT-ALL/معمار)
فعال باشد، وگرنه exit 0. (پنیکِ سراسری بر هر supervisor مقدم است — کاکپیت/watchdog/launcher.)
fail-closed: هر خطا در خواندن = فرضِ yield (exit 3). stdlib، read-only، صفر side-effect.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402


def global_halt() -> "tuple[bool, str]":
    """پنیکِ سراسری (HALT-ALL / STOP معمار) — بر هر supervisor مقدم است. fail-closed."""
    try:
        m = opslib.master_halted()
        if m:
            return True, m
        return False, "no-global-halt"
    except Exception as e:  # noqa: BLE001 — خطا = فرضِ halt (fail-closed)
        return True, f"probe-error→halt-assumed: {type(e).__name__}"


def should_yield(extra_stops=None) -> "tuple[bool, str]":
    """آیا هر supervisor باید yield کند؟ پنیکِ سراسری + STOP-ORGANISM + هر stopِ اضافه (per-service)."""
    gh, reason = global_halt()
    if gh:
        return True, f"global-halt: {reason}"
    try:
        if opslib.STOP_ORGANISM.exists():
            return True, "STOP-ORGANISM present"
    except Exception:  # noqa: BLE001
        return True, "stop-probe-error→yield"
    for p in (extra_stops or []):
        try:
            if Path(p).exists():
                return True, f"stop present: {Path(p).name}"
        except Exception:  # noqa: BLE001
            return True, "stop-probe-error→yield"
    return False, "proceed"


if __name__ == "__main__":
    # CLI برای watchdogهای PowerShell: exit 3 = پنیکِ سراسری فعال (yield)، exit 0 = ادامه مجاز.
    if "--global-halt" in sys.argv:
        gh, reason = global_halt()
        sys.stderr.write(reason + "\n")
        sys.exit(3 if gh else 0)
    y, r = should_yield()
    sys.stderr.write(r + "\n")
    sys.exit(3 if y else 0)
