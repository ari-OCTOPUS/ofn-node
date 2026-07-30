#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""outcome_ledger.py — تعمیرِ سه‌لایهٔ تابعِ پاداش (§۳ اکتاپوس‌OS).

باگی که ۲۵ جولای در سورس لنگر خورد:

  goal_directed.py:238  measure() فقط ۲۰ سطرِ آخر را می‌خواند
  goal_directed.py:242  همان id چند بار با baselineهای متفاوت در پنجره می‌افتد
  goal_directed.py:263  _close_intents روی همه حلقه می‌زند ⇒ بیت در یک فراخوان flip
                        ⇒ ۲۰ جفتِ (ts,key) هم‌زمان true و false. هر ۴ کلید متناقض.
  goal_directed.py:214  _movement_keys ⇒ تنها کلیدِ متحرک total_discoveries بود —
                        شمارنده‌ای که با تحقیقِ ارگانیسم دربارهٔ *خودش* بالا می‌رود
  improve.py:261        rate = moved/closed ⇒ «۴۵٪» یعنی «از ۸۳ بارْ بستنِ ۴ کارت،
                        ۳۸ بار کارت جابه‌جا شد»

سه لایهٔ تعمیر (به همین ترتیب):
  ۱ نویسنده — intents را بر id یکتا کن، *قدیمی‌ترین* baseline بماند (baselineِ واقعی)
  ۲ خواننده — مخرج = نیتِ متمایزِ دارای نتیجه، نه تعدادِ رکورد
  ۳ معنا    — فقط کلیدِ برون‌زاد رأی بدهد؛ درون‌زاد لاگ شود

انتظارِ صریح: rate_pct **می‌افتد**، احتمالاً به صفر یا None. این موفقیت است.
عددِ پایینِ راست از عددِ بالای دروغ بهتر است.

stdlib-only. fail-soft: هیچ استثنایی به بالا نشت نمی‌کند.
"""
from __future__ import annotations

from dataclasses import dataclass

from honest_metric import Measurement, Provenance

__all__ = [
    "ENDOGENOUS_KEYS", "EXOGENOUS_KEYS", "movement_keys", "moved_bit",
    "dedupe_intents", "close_intents", "improvement_rate", "Closure",
]

# ---------------------------------------------------------------------------
# §۳ لایهٔ معنا — تفکیکِ درون‌زاد از برون‌زاد
# ---------------------------------------------------------------------------
ENDOGENOUS_KEYS: frozenset[str] = frozenset({
    "total_discoveries",     # با تحقیقِ ارگانیسم دربارهٔ خودش بالا می‌رود  ← ریشهٔ باگ
    "proposals_delivered",   # «تحویل» بدونِ ارسالِ واقعی (fake delivery)
    "revenue_cells",         # شمارندهٔ سلول، نه پول
    "beats", "cycles", "consolidation",
})

EXOGENOUS_KEYS: frozenset[str] = frozenset({
    "confirmed_revenue",     # فقط با actor=reconcile-job + زنجیرهٔ سالم
    "proposals_sent",        # ارسالِ واقعی به بیرون
    "proposal_outcomes",     # نتیجهٔ برگشتی
    "proposal_positive",
    "proposal_value_aud",
    "owner_verdicts",        # رأیِ انسان
})


def movement_keys(now: dict, base: dict) -> tuple[str, ...]:
    """کلیدهایی که حق دارند بیتِ moved را روشن کنند.

    سه قاعدهٔ صداقت (دوتای اول از کدِ اصلی حفظ شده، سومی نو است):
      ۱ کلیدِ غایب در baseline هرگز حرکت نمی‌سازد (missing data must not become success)
      ۲ اگر هر دو طرف proposals_sent دارند، جایگزینِ proposals_delivered می‌شود
      ۳ **نو:** فقط کلیدِ برون‌زاد رأی می‌دهد
    """
    keys: list[str] = []
    for k in sorted(EXOGENOUS_KEYS):
        kk = k
        if k == "proposals_delivered" and "proposals_sent" in now and "proposals_sent" in base:
            kk = "proposals_sent"
        if kk in now and kk in base:
            keys.append(kk)
    return tuple(keys)


def moved_bit(now: dict, base: dict) -> tuple[bool, list[str]]:
    """آیا یک متریکِ **برون‌زاد** واقعاً جلو رفت؟ + کدام‌ها."""
    movers: list[str] = []
    for k in movement_keys(now, base):
        try:
            if float(now.get(k, 0)) > float(base.get(k, 0)):
                movers.append(k)
        except (TypeError, ValueError):
            continue
    return (len(movers) > 0), movers


# ---------------------------------------------------------------------------
# §۳ لایهٔ نویسنده — بستارِ بدونِ تناقض
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Closure:
    ts: str
    key: str
    moved: bool
    movers: tuple[str, ...]
    kind: str = "closure"
    schema: str = "outcome-closure.v2"

    def as_dict(self) -> dict:
        return {"ts": self.ts, "key": self.key, "moved": self.moved,
                "movers": list(self.movers), "kind": self.kind, "schema": self.schema}


def dedupe_intents(intents: list[dict]) -> list[dict]:
    """یکتاسازی بر `id` با نگه‌داشتنِ **قدیمی‌ترین** baseline.

    چرا قدیمی‌ترین: baselineِ واقعیِ یک نیت، حالتِ دنیا در لحظهٔ *ثبتِ* آن نیت است.
    نگه‌داشتنِ آخرین baseline یعنی مقایسهٔ دنیا با خودش ⇒ moved همیشه False.
    نگه‌داشتنِ چند تا (کدِ فعلی) ⇒ همان کلید در یک فراخوان هم true هم false می‌گیرد.
    """
    seen: dict[str, dict] = {}
    for r in intents:
        if not isinstance(r, dict):
            continue
        rid = str(r.get("id") or "").strip()
        if not rid or not isinstance(r.get("baseline"), dict):
            continue
        if rid not in seen:            # ترتیبِ فایل = ترتیبِ زمانی ⇒ اولی قدیمی‌ترین است
            seen[rid] = r
    return list(seen.values())


def close_intents(intents: list[dict], prior_rows: list[dict],
                  now: dict, ts: str) -> list[Closure]:
    """بستارِ لبه‌محور، بدونِ امکانِ تناقضِ هم‌زمان.

    تضمینِ ساختاری: خروجی برای هر `key` **حداکثر یک** رکورد دارد.
    """
    out: list[Closure] = []
    try:
        last: dict[str, bool] = {}
        for r in prior_rows:
            if isinstance(r, dict) and "moved" in r and r.get("key"):
                last[str(r["key"])] = bool(r["moved"])

        for r in dedupe_intents(intents):          # ← لایهٔ ۱
            rid = str(r["id"]).strip()
            base = r.get("baseline") or {}
            bit, movers = moved_bit(now, base)     # ← لایهٔ ۳
            if last.get(rid) == bit:
                continue                            # بیت عوض نشده ⇒ ننویس (رشدِ کران‌دار)
            out.append(Closure(ts=ts, key=rid, moved=bit, movers=tuple(movers)))
            last[rid] = bit
    except Exception:                               # noqa: BLE001 — بستار هرگز measure را نمی‌کشد
        return out
    return out


# ---------------------------------------------------------------------------
# §۳ لایهٔ خواننده — مخرجِ درست
# ---------------------------------------------------------------------------
def improvement_rate(rows: list[dict]) -> Measurement:
    """نرخِ واقعیِ خودبهبودی، به‌صورتِ یک `Measurement` صادق.

    مخرج = **نیتِ متمایزِ دارای نتیجهٔ نهایی**، نه تعدادِ رکوردِ بستار.
    هر کلید یک رأی دارد — آخرین بستارش. تکرار رأی اضافه نمی‌سازد.

    نبودِ داده ⇒ value=None و rate_pct=None. صفرِ ساختگی ممنوع.
    """
    final: dict[str, bool] = {}
    try:
        for r in rows:
            if not isinstance(r, dict) or r.get("kind") != "closure":
                continue
            k = r.get("key")
            if k is None:
                continue
            final[str(k)] = bool(r.get("moved"))
    except Exception:                               # noqa: BLE001
        final = {}

    closed = len(final)
    moved = sum(1 for v in final.values() if v)
    rate = (100.0 * moved / closed) if closed else None

    reasons: list[str] = []
    if closed == 0:
        reasons.append("[UNMEASURABLE YET] هیچ نیتی نتیجهٔ نهایی ندارد")
    elif closed < 5:
        reasons.append(f"نمونهٔ کوچک: فقط {closed} نیتِ متمایز")

    return Measurement(
        name="improvement_rate_pct",
        value=rate,
        provenance=Provenance.EXOGENOUS,   # چون فقط کلیدِ برون‌زاد بیت را روشن می‌کند
        receipt=("state/cortex/outcomes.jsonl · بستارِ متمایز per-key · "
                 "بیت فقط از EXOGENOUS_KEYS") if closed else None,
        quality=min(1.0, closed / 10.0),   # اعتماد با تعدادِ نیتِ متمایز بالا می‌رود
        reasons=tuple(reasons),
    )
