#!/usr/bin/env python3
"""test_execution_board_dedup.py — dedup بر اساسِ agent_id در execution_board.

گواهِ باگ (۲۰۲۶-۰۸-۰۸): lead-naghshi در سه beatِ پشت‌سرِهم failed شد (phi ۱۹.۸ →
۲۵.۶ → ۳۱.۹) و هر سه به‌عنوان ردیفِ جدا در خطِ «blocked» ظاهر شدند — کلِ خطِ
blocked را پر کردند و دیدِ واقعیِ مالک را مخدوش کردند.

این تست ادعا می‌کند: وقتی یک agent چندین رویدادِ پایانیِ هم‌نوع دارد، فقط آخرین
وضعیتش در هر خط دیده می‌شود.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402

ENV = harness.setup("eb_dedup")

import opslib  # noqa: E402
sys.path.insert(0, str(harness.SELF_OPS / "cortex"))
import execution_board as eb  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


# ── سناریو: سه شکستِ پشت‌سرِهمِ lead-naghshi + یک شکستِ agentِ دیگر ──────────
events = opslib.STATE_DIR / "events.jsonl"
events.parent.mkdir(parents=True, exist_ok=True)

rows = []
for phi in (19.8, 25.6, 31.9):
    rows.append(json.dumps({
        "timestamp": f"2026-08-08T14:4{int(phi):02d}:00",
        "event_name": "task.blocked",
        "status": "failed",
        "agent_id": "leg/lead-naghshi",
        "summary": f"عضو «lead-naghshi» از کار افتاد (phi={phi} — پاسخ‌گو نبود)",
        "trace_id": "",
        "next_action": "",
    }))
# agentِ متفاوت — نباید dedup شود
rows.append(json.dumps({
    "timestamp": "2026-08-08T14:50:00",
    "event_name": "task.blocked",
    "status": "failed",
    "agent_id": "pump/search",
    "summary": "سرچِ عمیق: provider انتخاب نشده",
    "trace_id": "",
    "next_action": "",
}))
events.write_text("\n".join(rows) + "\n", encoding="utf-8")

board = eb.board()
blocked = board.get("blocked", [])
naghshi = [b for b in blocked if "lead-naghshi" in b.get("agent", "")]
search = [b for b in blocked if "pump/search" in b.get("agent", "")]

check(len(naghshi) == 1,
      f"فقط یک ردیفِ lead-naghshi (نه ۳): {len(naghshi)}")
check(len(search) == 1,
      f"agentِ متفاوت dedup نشد: {len(search)}")
if naghshi:
    check("31.9" in naghshi[0].get("summary", ""),
          f"آخرین وضعیت (phi=31.9) نگه داشته شد: {naghshi[0].get('summary','')[:50]}")

print(f"\n{'PASS' if not fails else 'FAIL'} — test_execution_board_dedup")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
