# -*- coding: utf-8 -*-
"""Project-F worker — ماژول قفل‌دار (بدون هویت، بدون اجرا تا GATE 0).

قواعد سخت (از حافظهٔ پروژه):
- بیرون از پوشهٔ اصلی پروژه فقط اسم رمز «Project-F» — هیچ echo هویتی.
- تا وقتی GATE.yaml → gate0: open است، هیچ اقدام اجرایی انجام نمی‌شود؛
  فقط گزارش وضعیت (status.md) و یادآوری گام بعدی. verdict فقط انسان.
- kill switch: فایل STOP کنار همین فایل → خروج تمیز.

حالت‌ها:
  python worker.py --selftest   → چک سلامت (برای دکمهٔ test مغز کنترل)
  python worker.py              → حلقهٔ status هر ۱ ساعت (فقط نوشتن status.md محلی)
"""
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GATE = ROOT / "GATE.yaml"
STATUS = ROOT / "status.md"
STOP = ROOT / "STOP"


def gate_state() -> dict:
    st = {"gate0": "open", "branch": ""}
    if GATE.exists():
        for line in GATE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("gate0:"):
                st["gate0"] = line.split(":", 1)[1].strip().lower() or "open"
            elif line.startswith("branch:"):
                st["branch"] = line.split(":", 1)[1].strip()
    return st


def write_status():
    st = gate_state()
    locked = st["gate0"] != "closed"
    body = [
        "# Project-F — وضعیت ماژول",
        f"- زمان: {datetime.now().isoformat(timespec='minutes')}",
        f"- GATE 0: {'🔒 باز — هیچ اجرایی مجاز نیست' if locked else '🟢 بسته (Branch ' + (st['branch'] or '?') + ')'}",
        "",
        "## گام بعدی (verdict انسان)",
        "1. پیام GATE 0 + پرسش مجدد به پارتنر؛ ثبت Branch A/B.",
        "2. اگر Branch A: امضای توافق دونفره.",
        "3. سپس: آشتی سندهای master → زیرساخت Day-Zero → …",
        "",
        f"_ماژول در حالت {'قفل (status-only)' if locked else 'آماده (همچنان propose-only)'} — این فایل تنها خروجی آن است._",
    ]
    STATUS.write_text("\n".join(body) + "\n", encoding="utf-8")
    return locked


def main():
    if "--selftest" in sys.argv:
        locked = write_status()
        print(f"selftest ok — GATE 0 {'open/قفل' if locked else 'closed'} · status.md نوشته شد")
        return 0
    print("Project-F worker روشن شد (status-only تا GATE 0).")
    while not STOP.exists():
        write_status()
        for _ in range(360):  # ~۱ ساعت، با چک STOP هر ۱۰ ثانیه
            if STOP.exists():
                break
            time.sleep(10)
    print("STOP دیده شد — خروج تمیز.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
