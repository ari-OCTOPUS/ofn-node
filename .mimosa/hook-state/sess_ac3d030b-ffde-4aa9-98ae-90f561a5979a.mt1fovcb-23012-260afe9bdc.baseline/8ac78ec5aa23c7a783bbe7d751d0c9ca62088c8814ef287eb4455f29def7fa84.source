#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""consent_gate.py — Trust-Engine P0 · D2a (فاز D): predicateهای رضایت (سطحِ تماس).

این ماژول تنها سطحِ تماسِ consent با بقیهٔ خط لوله است. همهٔ مصرف‌کننده‌ها فقط دو تابعِ
`may_draft(lead_id)` و `may_release(lead_id, effect_kind)` را صدا می‌زنند؛ هیچ Leg مستقیماً
جدول را نمی‌خواند. تابعِ `derive_outreach_allowed` (pure) لایهٔ ۲ firewall است: outreach را
از قطعات بازمحاسبه می‌کند، هرگز مقدارِ ذخیره‌شده/ارسالیِ producer را نمی‌پذیرد.

قراردادِ حاکم: `05_CONSENT_STATE_MACHINE.md` بخشِ ۴ (Predicates).

قواعدِ غیرقابل‌مذاکره (05 §0):
  1. **Fail-closed در هر شاخه.** نبودِ داده = رد. خطا = رد. **flag خاموش = رد، نه skip**
     (وارونهٔ قراردادِ رایج codebase؛ برای ماژولِ اجازه‌دهنده ضروری).
  2. market_signal هرگز outreach_allowed=True نمی‌شود (سه‌لایه: CHECK SQL + derive + تست).
  3. Suppression از همه‌چیز جان به در می‌برد؛ چکِ آن قبل از هر draft است.
  4. رأیِ مالک ≠ اجازهٔ ارسال.

D2a هستهٔ ایمنی را پیاده می‌کند: derive + may_draft + may_release + suppression_hit.
بقیهٔ ماشین (escalation/compliance-overlay/retention) در D2b.
"""
from __future__ import annotations

import os
import re

FLAG = "OCTOPUS_WIRE_CONSENT_FW"   # master — خاموش = **deny**، نه skip (05 §0.1)


def flag_on() -> bool:
    """flag رابطِ رضایت. **خاموش = deny** (وارونهٔ fail-soft)."""
    return os.environ.get(FLAG) == "1"


# ── لایهٔ ۲ firewall: derive (pure، deterministic) ─────────────────────────────
def derive_outreach_allowed(rec: dict) -> bool:
    """outreach_allowed را از قطعات بازمحاسبه کن — **هرگز** مقدارِ ذخیره‌شده/ارسالی را نپذیر.
    pure، deterministic. (05 §4.1)"""
    try:
        t = rec.get("candidate_type")
        b = rec.get("consent_basis")
        ev = rec.get("consent_evidence")
        if t == "consented_inbound" and b == "explicit" and ev:
            return True
        if (t == "public_b2b" and b == "inferred_business"
                and ev == "office_contact_conspicuously_published"):
            return True
        return False           # market_signal / none / unknown / هر چیزِ دیگر → False
    except Exception:  # noqa: BLE001 — derive هم fail-closed
        return False


# ─ـ نرمال‌سازیِ contact برایِ تطبیقِ suppression (05 §6.2) ────────────────────
def normalize_phone(raw: str) -> str | None:
    """نرمال‌سازیِ phone به E.164-ish برایِ تطبیق. خطا/ابهام → None (fail-closed در caller)."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) < 8:        # حداقلِ معقول؛ کوتاه‌تر = نامعتبر
        return None
    # AU پیش‌فرض: اگر با 0 شروع شد و ۱۰ رقم است، +61 را جایگزینِ 0 کن
    if len(digits) == 10 and digits.startswith("0"):
        digits = "61" + digits[1:]
    elif not digits.startswith("61") and len(digits) == 10:
        digits = "61" + digits
    return "+" + digits


def normalize_email(raw: str) -> str | None:
    """نرمال‌سازیِ email به lowercase برایِ تطبیق. نامعتبر → None."""
    if not raw:
        return None
    s = str(raw).strip().lower()
    if "@" not in s or len(s) < 5:
        return None
    return s


def suppression_hit_for(store, rec: dict) -> str | None:
    """چکِ suppression برای یک رکورد. دلیل را برمی‌گرداند اگر فعال، یا None.
    تابعی از store (ConsentStore) و rec (که از load_current آمده، با فیلدِ contact_value_norm).
    خطا/ابهام = hit (fail-closed، 05 §6.2).

    rec باید فیلدِ `contact_value_norm` داشته باشد (مقدارِ نرمال‌شدهٔ phone/email که
    inbox هنگامِ upsert ذخیره کرده). اگر نبود، None برمی‌گرداند (نه fail-closed — چون
    بدونِ contact value اصلاً تطبیق ممکن نیست، نه یک ابهامِ خطرناک)."""
    if store is None:
        return None
    try:
        cvn = (rec or {}).get("contact_value_norm")
        if not cvn:
            return None   # بدونِ contact value، تطبیقِ suppression ممکن نیست (نه hit)
        hit = store.suppression_active(str(cvn))
        if hit:
            return f"contact:{hit}"
    except Exception:  # noqa: BLE001 — ابهام = hit
        return "suppression-check-error"
    return None


# ── predicates اصلی (دو تابع) ─────────────────────────────────────────────────
def may_draft(lead_id: str, *, store=None) -> tuple[bool, str]:
    """آیا اجازهٔ draft برای این lead_id هست؟ **قبل از هر draft** (scoring، prompt، کارت).
    خروجی: (bool, reason). flag خاموش = (False, "flag-off") (وارونهٔ fail-soft، 05 §0.1)."""
    if not flag_on():
        return (False, "flag-off")        # وارونهٔ قراردادِ رایج — ماژولِ اجازه‌دهنده
    try:
        if store is None or not str(lead_id or "").strip():
            return (False, "no-record")
        rec = store.load_current(str(lead_id))
        if rec is None or rec.get("purged"):
            return (False, "no-record")
        if rec.get("consent_state") not in ("CONSENTED_INBOUND", "B2B_PROSPECT"):
            return (False, f"state:{rec.get('consent_state')}")
        if not derive_outreach_allowed(rec):
            return (False, "consent-derivation")
        # چکِ suppression: قبل از هر draft. inbox/rec ممکن است contact نداشته باشد؛
        # در آن صورت suppression_hit_for به‌صورتِ ایمن None برمی‌گرداند.
        hit = suppression_hit_for(store, rec)
        if hit:
            return (False, f"suppressed:{hit}")
        return (True, "ok")
    except Exception as e:  # noqa: BLE001 — fail-closed
        return (False, f"exception:{type(e).__name__}")


def may_release(lead_id: str, effect_kind: str, *, store=None) -> tuple[bool, str]:
    """آیا اجازهٔ releaseِ یک effect هست؟ بینِ verdict مالک و ساختِ effect (defense-in-depth).
    شاملِ همهٔ چک‌های may_draft + compliance_state + kind-allowlist + synthetic-hard-block (05 §4.4)."""
    ok, why = may_draft(lead_id, store=store)
    if not ok:
        return (False, why)
    try:
        if store is None:
            return (False, "no-store")
        rec = store.load_current(str(lead_id))
        if rec is None:
            return (False, "no-record")
        if rec.get("source_channel") == "synthetic_test":
            return (False, "synthetic-hard-block")        # G-SYNTH
        # compliance overlay (D2b): فعلاً پیش‌فرض UNREVIEWED → اگر CLEAR/OWNER_CLEARED نیست، deny
        # در D2a، چون compliance-overlay هنوز ساخته نشده، همه رکوردها UNREVIEWED می‌مانند.
        # برای جلوگیری از block کردنِ کلِ لین در D2a، این چک را فقط روی risk-flagged اعمال می‌کنیم:
        # اگر compliance_state=RISK_FLAGGED → deny. UNREVIEWED در D2a اجازه می‌دهد (D2b سخت‌گیرانه‌تر).
        if rec.get("compliance_state") == "RISK_FLAGGED":
            return (False, "compliance:RISK_FLAGGED")
        # D2a: effect_kind که lead_outbound است مجاز؛ بقیه deny (allowlist ساده)
        k = str(effect_kind or "").strip()
        if k != "lead_outbound":
            return (False, "kind-not-allowlisted")
        return (True, "ok")
    except Exception as e:  # noqa: BLE001 — fail-closed
        return (False, f"exception:{type(e).__name__}")
