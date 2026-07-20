#!/usr/bin/env python3
"""watchdog.py — Phase 5 · S-1: watchdogِ کد (revive-after-death، نه persistence-fight).

اصلِ LifeDoctrine §۴: «You fight to keep Octopus alive. Octopus never fights to stay
alive.» watchdog = ابزارِ مالک برای زنده‌کردن، نه خودِ سیستم برای مقاومت.
kill-switch مطلق: watchdog بی‌قیدوشرط تسلیمِ هر STOP می‌شود (persistence نه resistance).

تولدِ owner-launched: watchdog فقط REVIVE می‌کند — هرگز first-birth. اولین/تشریفاتی
راه‌اندازی فقط Scheduled Task/at-logonِ تأییدِ مالک (هرگز از شلِ ایجنت — INC-1).

منطق (آزمون‌پذیر، $0 آفلاین):
  should_revive(port_alive, stop_flags, state_exists) → bool
    True فقط اگر: port مرده ∧ هیچ stop-flag نیست ∧ state وجود دارد (شواهدِ اجرای قبلی)
    False در غیر اینصورت — به‌ویژه: هر STOP = False (yield).

PS1 موجود (organism-watchdog.ps1) همین منطق را دارد ولی آزمون‌پذیر نیست. این ماژول
قراردادِ testable را استخراج می‌کند؛ PS1 می‌تواند آن را صدا بزند (یا مالک مستقیم).
additive؛ stdlib-only.
"""
from __future__ import annotations

import socket
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent              # _ops
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402

# پرچم‌های STOP (kill-switch مطلق — هرکدام = yield). ترتیب بررسی مهم نیست چون همه yield.
# D-G (2026-07-20): HALT-ALL افزوده شد — watchdog دیگر زیرِ پنیکِ سراسری احیا نمی‌کند
# (پیش‌تر فقط architect-STOP و STOP-ORGANISM را می‌دید؛ HALT-ALL بی‌اثر بود).
STOP_FLAGS = [
    opslib.HALT_ALL,                     # 🔴 پنیکِ سراسری (HALT-ALL) — MUST yield
    _HERE.parent / "STOP",               # architect-level (سطحِ والد)
    opslib.STOP_ORGANISM,                # organism-level
]
ORGANISM_PORT = 8771
STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"


def should_revive(port_alive: bool | None = None,
                  stop_flags: list[Path] | None = None,
                  state_exists: bool | None = None) -> tuple[bool, str]:
    """آیا باید revive شود؟ (port_alive/stop_flags/state_exists قابل‌تزریق برای تست).
    خروجی: (should, reason). هر STOP = (False, yield-reason).

    LifeDoctrine §۴: revive = ابزارِ مالک، نه self-preservationِ سیستم.
    تولدِ owner-launched: اگر state_exists نباشد (اولین بار) → False (first-birth با مالک)."""
    flags = stop_flags if stop_flags is not None else STOP_FLAGS
    # 1) kill-switch مطلق — FIRST check
    for flag in flags:
        if flag.exists():
            return False, f"yield: STOP flag present ({flag.name})"
    # 2) alive → no action
    if port_alive is None:
        port_alive = _port_alive(ORGANISM_PORT)
    if port_alive:
        return False, "alive: organism running"
    # 3) first-birth guard: only revive, never first-launch
    if state_exists is None:
        state_exists = STATE_FILE.exists()
    if not state_exists:
        return False, "no-prior-run: first-birth is owner-only (INC-1)"
    # 4) revive
    return True, "revive: port dead, no STOP, prior run exists"


def _port_alive(port: int, host: str = "127.0.0.1", timeout: float = 1.5) -> bool:
    """چکِ زنده‌بودنِ پورت (bind انحصاری = lockِ liveness). fail-soft: خطا = مرده."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def revive_action() -> str:
    """اقدامِ revive: در منطقِ واقعی، RUN-ORGANISM.bat را detached اجرا می‌کند.
    اینجا فقط برمی‌گرداند چه باید کرد (propose-only — اجرای واقعی = مالک/PS1)."""
    should, reason = should_revive()
    if not should:
        return f"NO-OP: {reason}"
    return (f"REVIVE: would launch RUN-ORGANISM.bat ({reason}). "
            f"⚡ اجرای واقعی = مالک/PS1 (twin of organism-watchdog.ps1)")


if __name__ == "__main__":
    print(revive_action())
