#!/usr/bin/env python3
"""asset_map.py — نظارتِ دارایی (ASSET-OVERSIGHT): اختاپوس همهٔ داراییِ مالک را در
هر پا *می‌بیند* و فقط *پیشنهاد* می‌دهد (مالک تأیید می‌کند؛ هرگز اجرای خودکار).

این ماژول یک aggregatorِ فقط‌خواندنی است:
  asset_map_status() -> {"assets":[...], "categories":N, "stale_count":N,
                         "proposals":[...], "as_of":ts}

هر پا (crypto/mining/accounting/ziman/revenue) پیش‌تر یک status dictِ PII-safe می‌دهد
{leg, live, signal, age_days, note}. این‌جا فقط **سیگنال‌های امن** (leg/category/live/
age_days/signal) از هر پا برداشته و به یک نقشه جمع می‌شود — نه مقدار، نه محتوای فایل.

خط قرمزِ مطلق:
  • هرگز عددِ پول/net-worth محاسبه یا echo نمی‌شود — پاها مقدار نمی‌دهند و این ماژول
    xlsx/pdf/بانک را باز نمی‌کند. فقط «چه داراییی هست + تازگی + شکاف»، نه «چقدر».
  • فقط کلیدهای whitelistِ خروجی از هر منبع عبور می‌کنند (leg/category/live/age_days/
    signal). هر کلیدِ دیگری (مثلاً amount_aud, note حاوی مسیر) دور ریخته می‌شود.
  • proposals صرفاً رشتهٔ *advisory* است (propose-only) — هرگز اکشنِ اجراپذیر.

fail-soft: هر پا در try مستقل؛ یک پای خراب کلِ نقشه را نمی‌کشد (unavailable علامت می‌خورد).
propose-only · $0 آفلاین · stdlib-only · صفر side-effect · صفر trade/پول.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# آستانهٔ عمومیِ کهنگی برای «stale» در سطحِ نقشه (پاها آستانهٔ خودشان را هم دارند؛
# این فقط برای شمارش/پیشنهادِ refresh در نقشه است). داده > این سن → کاندیدِ refresh.
ASSET_STALE_DAYS = 30.0

# کلیدهایی که مجازند از خروجیِ هر پا به نقشه عبور کنند (whitelistِ سختِ ضدِ leak).
_SAFE_KEYS = ("leg", "category", "live", "age_days", "signal")


def _now_iso() -> str:
    """timestampِ ISO از opslib (fail-soft به datetime اگر opslib نبود)."""
    try:
        import opslib
        return opslib.now_iso()
    except Exception:  # noqa: BLE001
        import datetime as _dt
        return _dt.datetime.now().isoformat(timespec="seconds")


# ─── آداپترهای PII-safe برای هر پا (فقط سیگنالِ امن، صفر مقدار) ──────────────────
def _crypto_status() -> dict:
    """پای Crypto — دادهٔ بازار (بی‌PII). مستقیم crypto_status()."""
    import crypto_leg
    return crypto_leg.crypto_status()


def _mining_status() -> dict:
    """پای Mining — skeletonِ صادق (بی‌منبعِ ماشینی). مستقیم mining_status()."""
    import mining_leg
    return mining_leg.mining_status()


def _accounting_status() -> dict:
    """پای Accounting — ⚠️ PII: فقط تعداد/mtimeِ workbook (صفر مقدار). accounting_status()."""
    import accounting_leg
    return accounting_leg.accounting_status()


def _ziman_status() -> dict:
    """پای Ziman — موجودی/کاتالوگ. از status_snapshotِ ZimanLeg فقط سیگنالِ *شمارشی*
    (خانواده‌ها/drafts) برداشته می‌شود؛ هیچ قیمت/ظرفیتِ عمومیِ تأییدنشده echo نمی‌شود."""
    import ziman_leg
    leg = ziman_leg.ZimanLeg()
    snap = leg.status_snapshot()
    fams = snap.get("product_families") or []
    drafts = snap.get("drafts_count", 0)
    cat = snap.get("catalog") or {}
    loaded = bool(cat.get("loaded"))
    n_products = cat.get("product_count") if loaded else None
    sig = f"families={len(fams)} drafts={drafts}" + (
        f" products={n_products}" if n_products is not None else "")
    return {"leg": "ziman", "live": loaded, "signal": sig, "age_days": None,
            "note": "موجودی propose-only؛ فقط شمارش (صفر قیمت/PII)."}


def _revenue_status() -> dict:
    """درآمدِ Lead (Track B) — ⚠️ فقط شمارش/پوشش، **هرگز مبلغ**. از confirmed_revenue
    فقط claimed/confirmed/attribution_coverage خوانده می‌شود؛ by_cell/by_partner (که مبلغ
    دارند) عمداً دست‌نخورده می‌مانند."""
    import attribution
    rev = attribution.confirmed_revenue()
    claimed = int(rev.get("claimed", 0) or 0)
    confirmed = int(rev.get("confirmed", 0) or 0)
    cov = rev.get("attribution_coverage")
    sig = f"claimed={claimed} confirmed={confirmed} coverage={cov}"
    return {"leg": "revenue", "live": confirmed > 0, "signal": sig, "age_days": None,
            "note": "فقط شمارشِ انتساب — هیچ مبلغی خوانده/echo نمی‌شود (خط‌قرمزِ پول/PII)."}


def _default_sources() -> dict:
    """نگاشتِ پیش‌فرضِ leg → (category, callable). تزریق‌پذیر برای تست."""
    return {
        "crypto":     ("digital-assets",   _crypto_status),
        "mining":     ("mining-hardware",  _mining_status),
        "accounting": ("financial-books",  _accounting_status),
        "ziman":      ("inventory",        _ziman_status),
        "revenue":    ("revenue",          _revenue_status),
    }


def _safe_entry(leg: str, category: str, raw: dict) -> dict:
    """فقط کلیدهای whitelist را از statusِ خام بردار (ضدِ leakِ amount/note/مسیر).
    age_days → float یا None؛ live → bool؛ signal → str (کوتاه‌شده)."""
    a = raw.get("age_days")
    try:
        age = round(float(a), 1) if a is not None else None
    except (TypeError, ValueError):
        age = None
    sig = raw.get("signal")
    sig = str(sig)[:120] if sig is not None else "unknown"
    return {"leg": leg, "category": category, "live": bool(raw.get("live")),
            "age_days": age, "signal": sig}


def asset_map_status(sources: dict | None = None) -> dict:
    """نقشهٔ نظارتِ داراییِ کل — فقط‌خواندنی، fail-soft، propose-only.

    sources: اختیاری {leg: (category, callable)} برای تست؛ None = پاهای واقعی.
    هر callable یک status dictِ PII-safe می‌دهد یا raise می‌کند (→ unavailable).

    خروجی: {"assets":[{leg,category,live,age_days,signal}], "categories":N,
             "stale_count":N, "proposals":[str], "as_of":ts}
    هرگز مبلغ/net-worth محاسبه یا echo نمی‌شود — فقط «چه هست + تازگی + شکاف».
    """
    src = sources if sources is not None else _default_sources()
    assets: list[dict] = []
    unavailable: list[str] = []
    for leg, spec in src.items():
        try:
            category, fn = spec
        except (TypeError, ValueError):
            category, fn = "unknown", spec
        try:
            raw = fn()
            if not isinstance(raw, dict):
                raise TypeError("status is not a dict")
            assets.append(_safe_entry(leg, category, raw))
        except Exception as e:  # noqa: BLE001 — یک پای خراب نباید نقشه را بکشد
            unavailable.append(leg)
            assets.append({"leg": leg, "category": category, "live": False,
                           "age_days": None,
                           "signal": f"unavailable ({type(e).__name__})"})

    categories = len({a["category"] for a in assets})
    stale = [a for a in assets
             if a["age_days"] is not None and a["age_days"] > ASSET_STALE_DAYS]

    # ── proposals: صرفاً advisory (propose-only) — مالک تصمیم می‌گیرد، هرگز اجرا نمی‌شود.
    proposals: list[str] = []
    for a in stale:
        proposals.append(
            f"{a['leg']} ({a['category']}) داده ≈{a['age_days']:.0f} روز کهنه → "
            f"منبع را refresh کن (پیشنهاد، نه اجرا).")
    for leg in unavailable:
        proposals.append(
            f"{leg} status در دسترس نیست → سلامتِ پا را بررسی کن (پیشنهاد، نه اجرا).")
    # همیشه: صداقت دربارهٔ نبودِ عددِ ثروتِ تجمیعی.
    proposals.append(
        "هیچ عددِ net-worthِ تجمیعی وجود ندارد — پاها سیگنال گزارش می‌کنند نه مبلغ؛ "
        "اگر عدد می‌خواهی یک valuationِ دستیِ مالک اضافه کن (این ماژول مبلغ نمی‌خواند).")

    return {
        "assets": assets,
        "categories": categories,
        "stale_count": len(stale),
        "unavailable": unavailable,
        "proposals": proposals,
        "propose_only": True,
        "as_of": _now_iso(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(asset_map_status(), ensure_ascii=False, indent=2))
