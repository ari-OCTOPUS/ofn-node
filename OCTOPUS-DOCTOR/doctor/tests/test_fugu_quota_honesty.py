#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OP-2 (MP-OPERATORS-01) — تست صداقتِ دفترِ پولِ دکتر.

ریشهٔ ردیف‌های spent_usd_today=0.0 روزهای 2026-09-06/07 (با cost>0):
`charge` به دیسک می‌نوشت، `_receipt` دوباره از دیسک می‌خواند؛ نوشتنِ گذرا اگر
شکست می‌خورد (قفلِ AV/هم‌زمانی — OSError ساکت)، رسید صفرِ stale را «امروز»
جا می‌زد. این تست چهار خاصیت را ثابت می‌کند:

A) فشارِ نوشتن → مقدارِ برگشتیِ charge باز هم مجموعِ بعد از کسر است
B) رسید با spent_usd صریح → همان در paid-calls.jsonl می‌نشیند
C) شکستِ دائمیِ نوشتن → رخداد در fugu-quota-savefail.jsonl ثبت (پول گمِ ساکت ممنوع)
D) reset روزانه → جمعِ روزِ جدید فقط از کسرهای امروز شروع می‌شود (رگرسیون)
"""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fugu import Quota, Fugu, Reply  # noqa: E402

P, F = [], []
def check(n, c, d=""):
    (P if c else F).append(n); print(f"  {'✅' if c else '❌'} {n}" + (f"  — {d}" if d else ""))

td = Path(tempfile.mkdtemp(prefix="op2-fugu-"))

# ── D) reset روزانه (رگرسیونِ معنای موجود) ─────────────────────────────
qd = Quota(td / "d", cap=9, usd_cap=5.0)
qd.charge(0.10)
stale = qd.p.read_text("utf-8")            # روزِ امروز با 0.10
d_yesterday = json.loads(stale); d_yesterday["day"] = "2000-01-01"
qd.p.write_text(json.dumps(d_yesterday), encoding="utf-8")
after = qd.charge(0.05)                    # روزِ نو ⇒ شمارنده از صفر
check("D reset روزانه: کسرِ روزِ نو فقط خودش",
      abs(after - 0.05) < 1e-9 and abs(qd.spent_usd - 0.05) < 1e-9,
      f"returned={after} disk={qd.spent_usd}")

# ── A) قفلِ گذرا: مقدارِ برگشتی درست، حتی اگر دیسک ننوشت ──────────────
qa = Quota(td / "a", cap=9, usd_cap=5.0)
qa.take()
real_save = Quota._save
def locked_save(self, d):                  # شبیهٔ قفلِ AV: دیسک stale می‌ماند
    return False
Quota._save = locked_save
ret = qa.charge(0.065455)                  # عددِ اثرانگشتی ۰۹-۰۶
Quota._save = real_save
check("A قفلِ نوشتن: charge مقدارِ بعد از کسر را برمی‌گرداند",
      abs(ret - 0.065455) < 1e-9, f"returned={ret}")
check("A′ اثرانگشتیِ باگ قدیمی قابلِ بازتولید است (دیسک stale)",
      qa.spent_usd == 0.0, f"disk={qa.spent_usd} — همان 0.0 ردیف‌های ۰۹-۰۶/۰۷")

# ── B) رسید از مقدارِ صریح می‌سازد، نه از دیسکِ stale ──────────────────
qb = Quota(td / "b", cap=9, usd_cap=5.0)
qb.take()
fg = Fugu(td / "b", timeout=1)
rep = Reply("x", "fugu-ultra-v1.1", "high", 100, 200, 50, ok=True,
            cost_usd=0.108665, shape="flat")   # عددِ اثرانگشتی ۰۹-۰۷
fg._receipt(rep, spent_usd=0.108665)
row = json.loads((td / "b" / "paid-calls.jsonl").read_text("utf-8").strip())
check("B رسید: spent_usd_today = مقدارِ بعد از کسرِ صریح",
      abs(row["spent_usd_today"] - 0.108665) < 1e-9
      and abs(row["cost_usd"] - 0.108665) < 1e-9,
      f"row={row['spent_usd_today']}")

# ── C) شکستِ دائمی ⇒ breadcrumb، پولِ گمِ ساکت ممنون ───────────────────
qc = Quota(td / "c", cap=9, usd_cap=5.0)
qc.take()
Quota._save = locked_save
qc.charge(0.07)
Quota._save = real_save
sf = (td / "c" / "fugu-quota-savefail.jsonl")
check("C breadcrumb: رخدادِ از‌دست‌رفته ثبت شد",
      sf.exists() and json.loads(sf.read_text("utf-8").strip())["lost_spent_usd"] == 0.07)

print("\n" + "=" * 58)
print(f"نتیجه: {len(P)} سبز · {len(F)} قرمز")
for x in F: print("  ❌", x)
print("=" * 58)
sys.exit(1 if F else 0)
