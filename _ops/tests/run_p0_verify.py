#!/usr/bin/env python3
"""run_p0_verify.py — minimal eval harness for the 2026-08-04 P0 fix set.

فقط تست‌های local/no-network/no-outbound مربوط به P0 (#53 latent_space،
#30 arm_gate) + intel_spine/telegram/webapp/obsidian adapters را اجرا می‌کند.

چرا این فایل لازم بود: هر ۵ تستِ سفارشی (غیر از test_arm_gate.py که
unittest است) با ✅/💥 روی stdout چاپ می‌کنند. کنسولِ ویندوز پیش‌فرض
cp1252 است، پس `python test_x.py` ساده بعد از چاپِ همهٔ چک‌ها با
UnicodeEncodeError کرش می‌کند و exit code=1 می‌دهد — یک "سرخِ دروغین":
منطقِ تست واقعاً pass شده بود، فقط چاپِ نتیجه کرش کرد. این harness دقیقاً
همان راه‌حلی را که RUN-ORGANISM.bat برای همین مشکل دارد (PYTHONIOENCODING=
utf-8 + PYTHONUTF8=1) به هر ساب‌پروسس تست تزریق می‌کند تا نتیجه صادقانه
دیده شود.

no network, no subprocess جز خودِ python test files، no state واقعی
(هر تست temp dir خودش را می‌سازد).

Usage: python run_p0_verify.py
Exit: 0 اگر همه pass، 1 اگر حداقل یکی fail.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# (label, filename) — همان ترتیبِ فازهای C/D/E در master instruction.
SUITE = [
    ("arm_gate (baseline, unittest)", "test_arm_gate.py"),
    ("arm_gate (#30 P0 sensitive-default)", "test_arm_gate_p0.py"),
    ("latent_space (baseline)", "test_latent_space.py"),
    ("latent_space (#53 P0 fail-closed)", "test_latent_space_fail_closed.py"),
    ("intel_spine (L0-L8 + redaction + no-outbound)", "test_intel_spine.py"),
    ("adapters (telegram/webapp/obsidian)", "test_adapters_obsidian.py"),
]


def run_one(fname: str) -> tuple[bool, str]:
    path = _HERE / fname
    if not path.exists():
        return False, f"MISSING: {path}"
    env = {}
    import os
    env.update(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(path)],
        cwd=str(_HERE),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    ok = proc.returncode == 0
    tail = (proc.stdout or "").strip().splitlines()[-3:]
    detail = " | ".join(tail) if tail else (proc.stderr or "").strip()[:200]
    return ok, detail


def main() -> bool:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=== P0 minimal eval harness - 2026-08-04 ===\n")
    all_ok = True
    for label, fname in SUITE:
        ok, detail = run_one(fname)
        all_ok = all_ok and ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {label} ({fname})")
        print(f"       {detail}")
    print()
    print("ALL GREEN" if all_ok else "AT LEAST ONE FAILURE — see detail above")
    return all_ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
