#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_doctor_day.py — لانچرِ تسکِ روزانهٔ دکترِ اختاپوس (OCTOPUS-doctor-day).

دکتر عمداً حقِ خواندنِ `.env` را ندارد؛ این لانچر با `env_loader` ِ خودِ ارگانیسم
env را بار می‌کند (idempotent، هرگز مقدارِ راز را چاپ نمی‌کند) و بعد `cli.py day`
را در همان env اجرا می‌کند — بدونِ `--apply`، پس هیچ merge ای ممکن نیست.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # F:\backup\_ops
sys.path.insert(0, str(_HERE / "budget"))
import env_loader  # noqa: E402

env_loader.load_env()                              # فقط نامِ کلیدها گزارش می‌شود، نه مقدار

import os  # noqa: E402
# رأی مالک 2026-09-05 (Q&A): حلقهٔ خود-یادگیری دائمی — MemoryGate همان گیتِ
# production است (TTL + فیلتر secret/PII + لجر)؛ setdefault تا مقدار صریح بیرونی ببرد.
os.environ.setdefault("OCTOPUS_WIRE_MEMORY_GATE", "1")
os.environ.setdefault("OCTOPUS_WIRE_MEMORY_DECISION", "1")
cli = _HERE.parent / "OCTOPUS-DOCTOR" / "doctor" / "cli.py"
r = subprocess.run([sys.executable, "-X", "utf8", str(cli), "day", str(_HERE)],
                   timeout=1800)
raise SystemExit(r.returncode)
