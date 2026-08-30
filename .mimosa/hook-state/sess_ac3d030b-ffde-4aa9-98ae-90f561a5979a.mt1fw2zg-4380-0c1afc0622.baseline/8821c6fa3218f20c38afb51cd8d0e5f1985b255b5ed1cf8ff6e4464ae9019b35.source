#!/usr/bin/env python3
"""daily-cost.py — خلاصهٔ هزینهٔ روز از paid-calls.jsonl (فقط‌خواندنی، صفر ارسال).

اجرا: python _ops/scripts/daily-cost.py
خروجی: مجموعِ cost_usd امروز + شمارش per-tier + flag/stop status.
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_PAID = _OPS / "state" / "paid-calls.jsonl"


def main() -> int:
    if not _PAID.exists():
        print("paid-calls.jsonl نیست — هنوز تماسِ پولی صورت نگرفته.")
        return 0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = 0.0
    count = 0
    tiers = Counter()
    errors = 0

    try:
        for line in _PAID.read_text("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ts = str(r.get("ts") or "")
            if not ts.startswith(today):
                continue
            count += 1
            tier = str(r.get("tier") or "?")
            tiers[tier] += 1
            try:
                total += float(r.get("cost_usd") or 0.0)
            except (TypeError, ValueError):
                pass
            if r.get("error"):
                errors += 1
    except OSError as e:
        print(f"خطا در خواندن: {type(e).__name__}: {e}")
        return 1

    print(f"📅 تاریخ: {today}")
    print(f"💰 مجموع cost_usd: ${total:.4f}")
    print(f"🔢 شمارش تماس: {count}")
    print(f"📊 per-tier: {dict(tiers)}")
    print(f"❌ خطا: {errors}")

    # Stop-FUGU check
    stop = _OPS / "STOP-FUGU"
    print(f"🛑 STOP-FUGU: {'موجود' if stop.exists() else 'غایب'}")

    # Budget state
    budget = _OPS / "budget" / "budget-state.json"
    if budget.exists():
        try:
            b = json.loads(budget.read_text("utf-8"))
            month_aud = b.get("month", {}).get("aud", 0.0)
            today_usd = b.get("today", {}).get("usd", 0.0)
            print(f"💸 ماه AUD: {month_aud} · امروز USD: {today_usd}")
        except (OSError, ValueError):
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
