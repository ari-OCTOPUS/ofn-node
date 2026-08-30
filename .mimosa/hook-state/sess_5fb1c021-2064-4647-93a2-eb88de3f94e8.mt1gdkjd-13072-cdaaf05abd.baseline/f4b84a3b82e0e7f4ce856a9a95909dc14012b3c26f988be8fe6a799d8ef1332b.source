#!/usr/bin/env python3
"""
run.py — نقطه‌ی ورود CLI.

نمونه‌ها:
  python run.py "اثر هوش مصنوعی بر بازار کار ۲۰۲۶"
  python run.py "..." --auto-approve     # تأیید انسانی خودکار (برای تست)
  python run.py "..." --auto-reject      # رد خودکارِ انسان (تست مسیر توقف)

کلید قطعِ بیرونی: در میانه‌ی اجرا فایل logs/STOP بساز تا سیستم متوقف شود.
"""
from __future__ import annotations
import sys, os

# اجازه‌ی import از ریشه‌ی پروژه
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# بارگذاری ساده‌ی .env (بدون وابستگی اضافه)
def _load_env():
    p = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

from src.orchestrator import Orchestrator


def main():
    args = [a for a in sys.argv[1:]]
    approver = None
    if "--auto-approve" in args:
        approver = lambda action, ctx: True
        args.remove("--auto-approve")
    elif "--auto-reject" in args:
        approver = lambda action, ctx: False
        args.remove("--auto-reject")

    topic = " ".join(args) or "نمونه: مزایا و ریسک‌های سیستم‌های چندعاملی"
    orch = Orchestrator(hitl_approver=approver)
    result = orch.run(topic)
    print(f"\n=== نتیجه نهایی: {result['status']} ===")


if __name__ == "__main__":
    main()
