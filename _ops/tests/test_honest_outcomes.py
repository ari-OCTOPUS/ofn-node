#!/usr/bin/env python3
"""test_honest_outcomes.py — T2 (2026-07-25، مگاپرامپت): سنجهٔ «خودبهبودی» خودش را تأیید می‌کرد.

گواه از outcomes.jsonl: ۲۳۰ سطر، ۰ سطر با «بعدِ اندازه‌گیری‌شده»؛ ۸۳ بستار روی فقط
۴ کلیدِ متمایز؛ ۲۰ جفتِ (ts,key) هم‌زمان هم true و هم false. علت: measure فقط ۲۰ سطر
آخر را می‌خواند، یک id چند بار با baselineهای متفاوت در پنجره بود و _close_intents
روی همه حلقه می‌زد؛ و تنها کلیدِ متحرکِ baselineهای اولیه total_discoveries بود
(شمارندهٔ خودِ ارگانیسم = خودارجاعی).

سه لایه پشتِ OCTOPUS_HONEST_OUTCOMES (خاموش = بایت‌به‌بایتِ قدیم):
  ۱) نویسنده: dedupe نیت‌ها بر اساسِ id، قدیمی‌ترین baseline.
  ۲) خواننده: مخرجِ improvement_rate = نیتِ متمایزِ دارای نتیجهٔ نهایی (آخرین رأی per key).
  ۳) معنا: total_discoveries درون‌زاد است — لاگ می‌شود ولی رأی نمی‌دهد.

توقعِ صادقانه: با فلگ روشن rate_pct می‌افتد (صفر/None) — این موفقیت است، نه رگرسیون.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
sys.path.insert(0, str(OPS / "cortex"))
sys.path.insert(0, str(OPS / "budget"))

import opslib  # noqa: E402

_TMP = Path(tempfile.mkdtemp(prefix="oct-t2-outcomes-"))
_FAKE_OPS = _TMP / "_ops"
_FAKE_STATE = _FAKE_OPS / "state"
_FAKE_STATE.mkdir(parents=True, exist_ok=True)
opslib.ORG_ROOT = _TMP
opslib.OPS = _FAKE_OPS
opslib.STATE_DIR = _FAKE_STATE
opslib.ALERTS_MD = _FAKE_OPS / "governor" / "governor-alerts.md"

import goal_directed as gd  # noqa: E402
import improve as imp  # noqa: E402

fails = []


def check(cond, msg):
    if cond:
        print(f"  ✅ {msg}")
    else:
        fails.append(msg)
        print(f"  ❌ {msg}")


def _flag(on: bool):
    if on:
        os.environ["OCTOPUS_HONEST_OUTCOMES"] = "1"
    else:
        os.environ.pop("OCTOPUS_HONEST_OUTCOMES", None)


def _write_rows(rows):
    p = _FAKE_STATE / "cortex" / "outcomes.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), "utf-8")
    return p


# ═══ ۱) نویسنده: dedupe — سه نیت با یک id و baselineهای متفاوت ════════════════
outcomes = _write_rows([
    {"ts": "t1", "id": "X", "title": "کارت", "baseline": {"confirmed_revenue": 5}},
    {"ts": "t2", "id": "X", "title": "کارت", "baseline": {"confirmed_revenue": 0}},
    {"ts": "t3", "id": "X", "title": "کارت", "baseline": {"confirmed_revenue": 0}},
])
gd.OUTCOMES = outcomes
gd._baseline_metrics = lambda: {"confirmed_revenue": 3}   # نو: ۳ — قدیمی‌ترین baseline (۵) → moved=False

_flag(True)
before = outcomes.read_text("utf-8").count("\n")
res = gd.measure()
after_rows = [json.loads(x) for x in outcomes.read_text("utf-8").splitlines() if x.strip()]
closures = [r for r in after_rows if r.get("kind") == "closure"]
check(len(closures) == 1, f"لایهٔ ۱: دقیقاً یک بستار برای idِ تکراری نوشته شد (نه {len(closures)})")
if closures:
    check(closures[0].get("moved") is False,
          "baselineِ قدیمی‌تر (۵) ملاک است: با now=3 بیت=False — نه flip با baselineهای متفاوت")
# هیچ (ts,key) تکراریِ متناقض
pairs = {}
contradiction = False
for r in closures:
    k = (r.get("ts"), r.get("key"))
    if k in pairs and pairs[k] != r.get("moved"):
        contradiction = True
    pairs[k] = r.get("moved")
check(not contradiction, "لایهٔ ۱: هیچ (ts,key) تکراریِ متناقضی تولید نشد")

# ═══ ۲) معنا: رشدِ فقط total_discoveries → moved=False (با فلگ روشن) ════════════
outcomes2 = _write_rows([
    {"ts": "t1", "id": "Y", "title": "کارت",
     "baseline": {"confirmed_revenue": 0, "revenue_cells": 0, "total_discoveries": 5}},
])
gd.OUTCOMES = outcomes2
gd._baseline_metrics = lambda: {"confirmed_revenue": 0, "revenue_cells": 0, "total_discoveries": 9}

_flag(True)
res2 = gd.measure()
check(res2.get("moved") is False,
      "لایهٔ ۳: رشدِ فقط total_discoveries (درون‌زاد) moved را True نمی‌کند")
rows2 = [json.loads(x) for x in outcomes2.read_text("utf-8").splitlines() if x.strip()]
cl2 = [r for r in rows2 if r.get("kind") == "closure"]
check(len(cl2) == 1 and cl2[0].get("moved") is False, "بستار=False ثبت شد")
check(bool(cl2) and "endogenous_delta" in cl2[0],
      "درون‌زاد در رکورد لاگ شد (endogenous_delta) — شفافیت بدونِ رأی")

# فلگ خاموش = رفتارِ قدیم (بایت‌به‌بایت): moved=True با رشدِ درون‌زاد
outcomes3 = _write_rows([
    {"ts": "t1", "id": "Y", "title": "کارت",
     "baseline": {"confirmed_revenue": 0, "revenue_cells": 0, "total_discoveries": 5}},
])
gd.OUTCOMES = outcomes3
_flag(False)
res3 = gd.measure()
check(res3.get("moved") is True,
      "فلگ خاموش: رفتارِ قدیم — رشدِ درون‌زاد moved=True (بایت‌به‌بایت)")

# ═══ ۳) خواننده: مخرجِ نیتِ متمایز ═════════════════════════════════════════════
imp.STATE = _FAKE_STATE
outcomes4 = _write_rows([
    {"ts": "a", "key": "A", "moved": True, "kind": "closure"},
    {"ts": "a", "key": "A", "moved": False, "kind": "closure"},   # متناقضِ قدیمی
    {"ts": "a", "key": "B", "moved": True, "kind": "closure"},
    {"ts": "a", "key": "B", "moved": True, "kind": "closure"},    # تکرارِ موافق
])
_flag(False)
off = imp.improvement_rate()
check(off.get("closed") == 4 and off.get("moved") == 3,
      f"فلگ خاموش: شمارشِ خامِ قدیم (closed=4, moved=3 — {off.get('rate_pct')}٪)")

_flag(True)
on = imp.improvement_rate()
check(on.get("closed") == 2, "لایهٔ ۲: مخرج = نیتِ متمایز (۲ نه ۴)")
check(on.get("moved") == 1, "لایهٔ ۲: آخرین رأی per key برنده است (A=False، B=True)")
check(on.get("rate_pct") == 50.0, f"rate_pct={on.get('rate_pct')} (عددِ پایینِ راست، نه بالای دروغ)")

# ═══ ۴) نبودِ داده → None (نه صفرِ ساختگی) ════════════════════════════════════
_write_rows([])
on_none = imp.improvement_rate()
check(on_none.get("rate_pct") is None, "داده نبود → rate_pct=None (قاعدهٔ صداقت حفظ شد)")

_flag(False)

print(f"\n{'PASS' if not fails else 'FAIL'} — test_honest_outcomes")
for f in fails:
    print(f"  - {f}")
sys.exit(1 if fails else 0)
