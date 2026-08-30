#!/usr/bin/env python3
"""personal_ledger.py — دفترِ شخصی/مشترکِ آرمین+عباس + واحدِ ATO-NSW (propose-only، 2026-07-16).

سه دفتر روی یک فایل: آرمین (مالک) · عباس (همکار، بارضایت) · واحدِ مالیاتیِ ATO-NSW (نمای
تجمیعی). حسابِ مشترک = خرج‌هایی که party=="joint" با split بینِ آرمین/عباس. دامنهٔ کامل:
income/expense/asset/liability → ثروتِ خالصِ هرکس + جریانِ نقدی + تسویهٔ مشترک + رول‌آپِ مالیاتی.

مرزهای سخت:
  - رصد + گزارش + پیشنهادِ تسویه؛ هرگز پول جابه‌جا/انتقال نمی‌شود، رمزِ بانک وارد نمی‌شود.
  - دربارهٔ مالیات مشاورهٔ شخصی نمی‌دهد — فقط دادهٔ دسته‌بندی‌شده/تجمیعی برای ATO.
  - خروجی هرگز descِ تراکنش یا لیستِ خام را echo نمی‌کند؛ فقط ترازِ تجمیعی (گِرد به ۲).
  - دادهٔ عباس شخصِ ثالثِ بارضایت است (CONSENT.md)؛ ledger.json واقعی gitignore + محلی.

منبع: 03 - Projects/Accounting/personal/ledger.json (نبود → propose «قالب را پر کن»).
$0 · stdlib + opslib · fail-soft.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

PARTIES = ("armin", "abbas")            # دو شخص؛ joint = مشترکِ این دو
TYPES = ("income", "expense", "asset", "liability")

# دسته‌بندیِ کانونی (قابلِ ویرایش در فایل؛ این پیش‌فرض است)
CATEGORIES = {
    "income": ["salary_wages", "business_income", "rental_income",
               "interest_dividends", "other_income"],
    "expense": ["rent_mortgage", "utilities", "insurance", "subscriptions",
                "loan_repayments", "groceries", "dining", "transport",
                "health_medical", "shopping", "entertainment", "travel",
                "education", "gifts", "bank_fees", "misc"],
    "asset": ["cash_bank", "savings", "crypto", "vehicle", "property",
              "receivables", "other_asset"],
    "liability": ["credit_card", "personal_loan", "mortgage_owing",
                  "payable", "other_liability"],
}


def _ledger_path() -> Path:
    return (opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "ledger.json")


def _load(path: Path | None = None) -> dict | None:
    p = path or _ledger_path()
    try:
        d = json.loads(p.read_text("utf-8")) if p.exists() else None
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def _num(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _blank_party() -> dict:
    return {"income": 0.0, "expense": 0.0, "asset": 0.0, "liability": 0.0}


def compute(ledger: dict) -> dict:
    """سه دفتر را از entries حساب کن — فقط تجمیعی، نه تراکنشِ منفرد.

    - per_party[armin|abbas]: مجموعِ income/expense/asset/liability + cashflow + net_worth.
    - joint_settlement: خالصِ «کی به کی» روی entryهای party=="joint" (طبقِ split و paid_by).
    - entity_ato: رول‌آپِ واحدِ مالیاتی — کلِ income/expense (به تفکیکِ دسته) + GST اگر بود.
    """
    entries = ledger.get("entries") or []
    dflt = ledger.get("default_split") or {"armin": 50, "abbas": 50}
    per = {p: _blank_party() for p in PARTIES}
    by_cat = {}                                  # entity: expense/income by category
    gst_total = 0.0
    net_owed_to_armin = 0.0                       # مثبت=عباس به آرمین بدهکار
    n = {"party": 0, "joint": 0}
    for e in entries:
        if not isinstance(e, dict):
            continue
        amt = _num(e.get("amount"))
        typ = str(e.get("type", "expense")).lower()
        if typ not in TYPES:
            typ = "expense"
        party = str(e.get("party", "")).lower()
        cat = str(e.get("category", "uncategorized"))
        gst_total += _num(e.get("gst"))
        # رول‌آپِ واحدِ مالیاتی (income/expense به تفکیکِ دسته)
        if typ in ("income", "expense"):
            by_cat.setdefault(typ, {}).setdefault(cat, 0.0)
            by_cat[typ][cat] += amt
        if party == "joint":
            n["joint"] += 1
            split = e.get("split") or dflt
            a_share = amt * _num(split.get("armin", 50)) / 100.0
            b_share = amt * _num(split.get("abbas", 50)) / 100.0
            payer = str(e.get("paid_by", "armin")).lower()
            # سهمِ هرکس به دفترِ شخصیِ خودش هم می‌رود (برای net_worth/cashflow)
            per["armin"][typ] = per["armin"].get(typ, 0.0) + a_share
            per["abbas"][typ] = per["abbas"].get(typ, 0.0) + b_share
            # تسویه فقط برای expense معنی دارد (کی پرداخت، کی سهمش را بدهکار)
            if typ == "expense":
                if payer == "armin":
                    net_owed_to_armin += b_share
                elif payer == "abbas":
                    net_owed_to_armin -= a_share
        elif party in PARTIES:
            n["party"] += 1
            per[party][typ] = per[party].get(typ, 0.0) + amt

    def _finish(d):
        cf = round(d["income"] - d["expense"], 2)
        nw = round(d["asset"] - d["liability"], 2)
        return {**{k: round(v, 2) for k, v in d.items()}, "cashflow": cf, "net_worth": nw}

    per_out = {p: _finish(per[p]) for p in PARTIES}
    entity = {
        "income_total": round(sum(by_cat.get("income", {}).values()), 2),
        "expense_total": round(sum(by_cat.get("expense", {}).values()), 2),
        "by_category": {t: {c: round(v, 2) for c, v in cats.items()}
                        for t, cats in by_cat.items()},
        "gst_total": round(gst_total, 2),
    }
    entity["net_before_tax"] = round(entity["income_total"] - entity["expense_total"], 2)
    return {
        "per_party": per_out,
        "joint_settlement": {"net_owed_to_armin": round(net_owed_to_armin, 2),
                             "currency": ledger.get("currency", "AUD")},
        "entity_ato": entity,
        "counts": n,
        "currency": ledger.get("currency", "AUD"),
    }


def settlement_proposal(js: dict) -> str:
    net, cur = js.get("net_owed_to_armin", 0.0), js.get("currency", "AUD")
    if abs(net) < 0.01:
        return "حسابِ مشترک تسویه است — کسی به کسی بدهکار نیست."
    if net > 0:
        return (f"پیشنهاد (تأییدِ خودت لازم): عباس حدودِ {net:.2f} {cur} به تو (آرمین) بدهکار است. "
                f"وقتی تسویه شد دستی ثبت کن — اختاپوس پول جابه‌جا نمی‌کند.")
    return (f"پیشنهاد (تأییدِ خودت لازم): تو (آرمین) حدودِ {abs(net):.2f} {cur} به عباس بدهکاری. "
            f"پرداخت دستِ خودت؛ اختاپوس فقط یادآوری می‌کند.")


def personal_status(path: Path | None = None) -> dict:
    """وضعیتِ propose-only. نبودِ ledger → propose «قالب را پر کن». هرگز تراکنشِ منفرد."""
    d = _load(path)
    if d is None:
        return {"leg": "personal-ledger", "live": False, "signal": "ledger نیست",
                "note": "ledger.json نیست — از ledger.example.json کپی و دونه‌دونه پر کن (propose-only)."}
    b = compute(d)
    return {
        "leg": "personal-ledger", "live": True,
        "signal": f"entries={b['counts']['party']+b['counts']['joint']}",
        "balance": b,                        # فقط تجمیعی — نه تراکنشِ منفرد
        "proposal": settlement_proposal(b["joint_settlement"]),
        "note": "۳ دفتر (آرمین/عباس/واحدِ ATO-NSW) + تسویهٔ مشترک. رصد+پیشنهاد؛ صفر حرکتِ مالی. "
                "دادهٔ مالیاتی = فقط رول‌آپ، نه مشاورهٔ مالیاتی (CONSENT.md).",
    }


if __name__ == "__main__":
    print(json.dumps(personal_status(), ensure_ascii=False, indent=2))
