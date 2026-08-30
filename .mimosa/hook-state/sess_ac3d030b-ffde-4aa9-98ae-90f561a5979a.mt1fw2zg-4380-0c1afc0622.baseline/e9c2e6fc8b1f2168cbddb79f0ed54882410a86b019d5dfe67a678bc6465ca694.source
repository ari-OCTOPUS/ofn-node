#!/usr/bin/env python3
"""attributor.py — دسته‌بندِ قطعیِ تراکنش‌ها (CATEGORIZER) برای حسابدارِ چندایجنتی — 2026-07-16.

مدلِ واقعی: آرمین برای عباس روزمزد $۲۵۰ کار می‌کند (حقوق از حسابِ عباس). داده مالکیتِ
مخلوط دارد + یک موردِ بحرانیِ TRANSFER: پولِ کسب‌وکار به حسابِ آرمین می‌آید ولی او همان را
به عباس می‌فرستد (pass-through — باید transfer برچسب بخورد، از درآمد/هزینه EXCLUDED، هرگز
دوباره‌شمرده نشود).

روش‌های تحقیقِ ۲۰۲۷ (از محصولاتِ واقعی Ramp/Midday/HighRadius):
  · روش ۷ — تصمیم یک enumِ categorical است {auto | needs_review}، نه یک «اطمینانِ عددیِ»
    قلابی (LLM اطمینانش صرف‌نظر از درستی حول ۷۰–۸۰٪ خوشه می‌زند — Ramp).
  · روش ۶ — آبشارِ «قاعدهٔ قطعی-اول»؛ فقط پس‌ماند نامطمئن است و needs_review می‌شود.
  · روش ۸ — گیتِ سختِ انسانی: دسته‌بند هرگز خودش تأیید نمی‌کند — پیشنهاد می‌دهد، مالک تأیید.

مرزهای سخت (این ماژول):
  - PROPOSE-ONLY مطلق: هرگز پول جابه‌جا نمی‌شود، هرگز کارِ خودش را auto-confirm نمی‌کند.
    وضعیتِ «confirmed» فقط از مسیرِ apply_corrections (ورودیِ مالک) می‌آید، نه از خودِ ایجنت.
  - وقتی نامطمئن → needs_review؛ روی پولِ واقعی هرگز حدس نمی‌زند.
  - خروجی هیچ مبلغِ خامی را echo نمی‌کند مگر خودِ txn (که amount_cents دارد)؛ counts فقط شمارش.

شِمای ورودی (از txn_store، ایجنتِ دیگر می‌سازد — این شکل فرض می‌شود):
  txn = {id, date("YYYY-MM-DD"), amount_cents(int علامت‌دار), desc, source, account,
         owner:"unknown", ptype:"unknown", category, review:"pending", note}
  مثبت = ورودی (inbound)، منفی = خروجی (outbound).

هستهٔ خروجی هر txn پس از attribute: owner / ptype / category / review + basis (citationِ قاعده).

$0 · فقط stdlib (money.py هم‌بسته) · fail-soft.
"""
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import money  # noqa: E402  — هر کارِ سنت از money.py (int cents، نه float)

# ── ثابت‌های قاعده (قابل‌توسعه) ─────────────────────────────────────────────
WAGE_UNIT_CENTS = money.to_cents("250")          # نرخِ روزمزدِ $۲۵۰ = ۲۵۰۰۰ سنت
WAGE_HINTS = ("armin", "آرمین", "حقوق", "wage", "salary")
# نشانه‌های pass-through در desc (همه → needs_review، هرگز auto، هرگز حرکتِ پول → over-tag امن)
TRANSFER_HINTS = ("transfer", "passthrough", "pass-through", "pass through",
                  "عباس→", "→عباس", "به عباس", "to abbas", "→")
# نقشهٔ فروشنده (starter map — قابل‌توسعه): کلیدواژه → (category, ptype)
VENDOR_RULES = {
    "materials": ("bunnings", "dulux", "masters", "paint", "hardware"),
    "transport": ("fuel", "petrol"),
}
# تلورانسِ «تقریباً برابر» برای جفتِ pass-through: بیشترِ $۲ یا ۲٪ (کارمزدِ احتمالی)
_TOL_FLOOR_CENTS = money.to_cents("2")


# ── کمک‌های fail-soft ───────────────────────────────────────────────────────
def _amt(t: dict) -> int:
    """amount_cents علامت‌دار به‌صورتِ int؛ هر خطا → 0."""
    try:
        return int(t.get("amount_cents") or 0)
    except (TypeError, ValueError):
        return 0


def _desc(t: dict) -> str:
    return str(t.get("desc") or "").lower()


def _acct(t: dict) -> str:
    return str(t.get("account") or "").strip().lower()


def _date(t: dict):
    """date("YYYY-MM-DD") → datetime.date؛ نامعتبر → None (→ جفت‌سازی رد می‌شود، محافظه‌کار)."""
    try:
        return _dt.date.fromisoformat(str(t.get("date") or "")[:10])
    except (TypeError, ValueError):
        return None


def _near_equal(a_abs: int, b_abs: int) -> bool:
    tol = max(_TOL_FLOOR_CENTS, int(round(0.02 * max(a_abs, b_abs))))
    return abs(a_abs - b_abs) <= tol


def _has_transfer_hint(desc: str) -> bool:
    return any(h in desc for h in TRANSFER_HINTS)


def _is_wage(desc: str, cents: int) -> bool:
    """desc نامِ آرمین/حقوق را دارد و مبلغ مضربِ دقیقِ $۲۵۰ است (مضربِ روزمزد)."""
    if cents == 0:
        return False
    if abs(cents) % WAGE_UNIT_CENTS != 0:
        return False
    return any(h in desc for h in WAGE_HINTS)


def _vendor_hit(desc: str):
    """اولین قاعدهٔ فروشندهٔ منطبق → (category, matched_keyword)؛ وگرنه None."""
    for category, keys in VENDOR_RULES.items():
        for k in keys:
            if k in desc:
                return category, k
    return None


def _set(t: dict, **kw) -> None:
    for k, v in kw.items():
        t[k] = v


def _passthrough_indices(txns: list) -> set:
    """اندیسِ txnهایی که کاندیدِ pass-through هستند: یک inbound (مثبت) که ظرفِ ~۳ روز با یک
    outbound (منفی) تقریباً-برابر روی همان account دنبال می‌شود. جفتِ هر دو سمت علامت می‌خورد.
    قطعی و محافظه‌کار — تاریخِ نامعتبر → جفت نمی‌شود."""
    marked: set = set()
    used_out: set = set()                       # اندیسِ outboundهای مصرف‌شده (یک‌به‌یک)
    items = [(i, t) for i, t in enumerate(txns) if isinstance(t, dict)]
    for i, t in items:
        c = _amt(t)
        if c <= 0:                              # فقط inbound را لنگر می‌کنیم
            continue
        din = _date(t)
        if din is None:
            continue
        acct = _acct(t)
        for j, u in items:
            if j == i or j in used_out:
                continue
            cu = _amt(u)
            if cu >= 0:                          # فقط outbound
                continue
            if _acct(u) != acct:
                continue
            dout = _date(u)
            if dout is None:
                continue
            delta = (dout - din).days
            if delta < 0 or delta > 3:           # outbound بعدِ inbound، تا ۳ روز
                continue
            if not _near_equal(abs(c), abs(cu)):
                continue
            marked.add(i)
            marked.add(j)
            used_out.add(j)
            break
    return marked


# ── API عمومی ───────────────────────────────────────────────────────────────
def attribute(txns: list) -> list:
    """قاعده‌های قطعی را (آبشارِ روش ۶) به هر txn اعمال کن و owner/ptype/category/review + basis
    را ست کن. کپیِ هر dict (بدونِ mutation ورودی). نامطمئن → needs_review (هرگز حدس روی پول).

    اولویتِ آبشار (اول برنده): transfer(جفت) › transfer(desc) › wage › vendor › unmatched.
    transfer اول است چون «هرگز دوباره‌نشمردنِ pass-through» بحرانی‌ترین مرزِ ایمنیِ پول است."""
    if not isinstance(txns, list):
        return []
    pass_idx = _passthrough_indices(txns)
    out = []
    for i, t in enumerate(txns):
        if not isinstance(t, dict):
            out.append(t)
            continue
        r = dict(t)
        desc = _desc(r)
        c = _amt(r)
        if i in pass_idx:
            _set(r, ptype="transfer", category="transfer",
                 review="needs_review", basis="passthrough-candidate:in→out")
        elif _has_transfer_hint(desc):
            _set(r, ptype="transfer", category="transfer",
                 review="needs_review", basis="passthrough-candidate:desc")
        elif _is_wage(desc, c):
            n = abs(c) // WAGE_UNIT_CENTS
            _set(r, owner="armin", ptype="wage", category="wages",
                 review="needs_review", basis=f"wage-pattern:$250x{n}")
        else:
            hit = _vendor_hit(desc)
            if hit:
                cat, name = hit
                _set(r, ptype="expense", category=cat,
                     review="auto", basis=f"vendor:{name}->{cat}")
            else:
                _set(r, review="needs_review", basis="unmatched:needs-owner-label")
        out.append(r)
    return out


def review_queue(txns: list) -> list:
    """همهٔ txnهای review=="needs_review"، مهم‌ترین-اول بر اساسِ |amount_cents| (نزولی).
    این صفِ کاری برای مالک است — دسته‌بند هرگز خودش این‌ها را قطعی نمی‌کند."""
    q = [t for t in txns if isinstance(t, dict) and t.get("review") == "needs_review"]
    return sorted(q, key=lambda t: abs(_amt(t)), reverse=True)


def apply_corrections(txns: list, corrections: dict) -> list:
    """مسیرِ یادگیری/human-in-the-loop: تصحیح‌های مالک را اعمال کن.
    corrections = {id: {owner, ptype, category}} → همان txn را confirmed + basis="owner" کن.
    این تنها مسیری است که review را به «confirmed» می‌رساند (روش ۸ — مالک تأیید، نه ایجنت)."""
    if not isinstance(txns, list) or not isinstance(corrections, dict):
        return txns if isinstance(txns, list) else []
    out = []
    for t in txns:
        if not isinstance(t, dict):
            out.append(t)
            continue
        r = dict(t)
        corr = corrections.get(r.get("id"))
        if isinstance(corr, dict):
            for k in ("owner", "ptype", "category"):
                if k in corr and corr[k] is not None:
                    r[k] = corr[k]
            r["review"] = "confirmed"
            r["basis"] = "owner"
        out.append(r)
    return out


def counts(txns: list) -> dict:
    """شمارشِ تجمیعی (نه مبلغ): {auto, needs_review, confirmed, total, by_ptype}."""
    auto = nr = conf = 0
    by: dict = {}
    total = 0
    for t in txns:
        if not isinstance(t, dict):
            continue
        total += 1
        rv = t.get("review")
        if rv == "auto":
            auto += 1
        elif rv == "needs_review":
            nr += 1
        elif rv == "confirmed":
            conf += 1
        pt = t.get("ptype") or "unknown"
        by[pt] = by.get(pt, 0) + 1
    return {"auto": auto, "needs_review": nr, "confirmed": conf,
            "total": total, "by_ptype": by}


if __name__ == "__main__":
    # دودِ سریع — بدونِ echo مبلغِ خام
    _t = [
        {"id": "1", "date": "2026-07-01", "amount_cents": 75000, "desc": "Armin wage",
         "account": "abbas", "owner": "unknown", "ptype": "unknown", "review": "pending"},
        {"id": "2", "date": "2026-07-02", "amount_cents": 120000, "desc": "job deposit",
         "account": "armin-main", "owner": "unknown", "ptype": "unknown", "review": "pending"},
        {"id": "3", "date": "2026-07-03", "amount_cents": -120000, "desc": "send to abbas",
         "account": "armin-main", "owner": "unknown", "ptype": "unknown", "review": "pending"},
        {"id": "4", "date": "2026-07-04", "amount_cents": -8990, "desc": "BUNNINGS Warehouse",
         "account": "armin-main", "owner": "unknown", "ptype": "unknown", "review": "pending"},
        {"id": "5", "date": "2026-07-05", "amount_cents": -4200, "desc": "unknown cafe xyz",
         "account": "armin-main", "owner": "unknown", "ptype": "unknown", "review": "pending"},
    ]
    a = attribute(_t)
    by_id = {t["id"]: t for t in a}
    assert by_id["1"]["ptype"] == "wage" and by_id["1"]["owner"] == "armin"
    assert by_id["1"]["review"] == "needs_review" and by_id["1"]["basis"] == "wage-pattern:$250x3"
    assert by_id["2"]["ptype"] == "transfer" and by_id["3"]["ptype"] == "transfer"
    assert by_id["4"]["category"] == "materials" and by_id["4"]["review"] == "auto"
    assert by_id["5"]["review"] == "needs_review" and by_id["5"]["ptype"] == "unknown"
    q = review_queue(a)
    assert q and abs(_amt(q[0])) >= abs(_amt(q[-1]))
    c = counts(a)
    assert c["auto"] == 1 and c["needs_review"] == 4 and c["by_ptype"]["transfer"] == 2
    fixed = apply_corrections(a, {"5": {"owner": "armin", "ptype": "expense", "category": "dining"}})
    f5 = {t["id"]: t for t in fixed}["5"]
    assert f5["review"] == "confirmed" and f5["basis"] == "owner" and f5["ptype"] == "expense"
    print("PASS attributor smoke")
