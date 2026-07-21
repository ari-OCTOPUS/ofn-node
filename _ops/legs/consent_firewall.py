#!/usr/bin/env python3
"""consent_firewall.py — Trust-Engine P0: دیوارِ باربرِ رضایت (structural، fail-closed).

قراردادِ حاکم: `03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/PHASE-B-CONTRACTS/`
  · 02_CANONICAL_LEAD_CONTRACT.json (قیدهای اسکیما)
  · 05_CONSENT_STATE_MACHINE.md (گاردها، گذارها)

این ماژول تنها مرجعِ کدیِ تصمیمِ «آیا اجازهٔ تماسِ خروجی هست؟» است. تابعِ خالص، بدونِ I/O،
بدونِ شبکه، stdlib-only. نامتغیرهای غیرقابل‌مذاکره (هم‌راستا با اسکیمای draft-07):

  R1. `market_signal` هرگز نمی‌تواند `outreach_allowed=True` بگیرد. یک سیگنال، لید نیست.
  R2. رضایتِ غایب/نامعلوم (`basis ∈ {none, unknown, ""}`) → fail-closed `outreach_allowed=False`.
  R3. `public_b2b` ≠ رضایتِ مسکونی — فقط با `basis=inferred_business` و تماسِ منتشرشدهٔ نقشی،
      آن هم از مسیرِ capped ماژول ۱ (این‌جا فقط اجازه را می‌دهیم؛ سقف/ارسال جای دیگر).
  R4. هر استثنا/ابهام در ارزیابی → `outreach_allowed=False` (هرگز fail-open).

این فایل هرگز چیزی نمی‌فرستد، نمی‌نویسد، یا خرج نمی‌کند — فقط رأی می‌دهد.
"""
from __future__ import annotations

# ── واژگانِ canonical (عینِ اسکیما) ──────────────────────────────────────────────
CANDIDATE_TYPES = ("consented_inbound", "public_b2b", "market_signal")
CONSENT_BASES = ("explicit", "inferred_business", "none", "unknown")

# نگاشتِ کانالِ منبع → نوعِ کاندیدِ پیش‌فرض (fail-closed: ناشناخته → market_signal).
_CHANNEL_DEFAULT_TYPE = {
    "telegram_manual": "consented_inbound",
    "website_form": "consented_inbound",
    "missed_call": "consented_inbound",
    "meta_lead_ad": "consented_inbound",
    "synthetic_test": "consented_inbound",   # لیدِ آزمایشی؛ در EffectorGate سختاً بلاک می‌شود
    "facebook_group": "market_signal",
    "nsw_da": "market_signal",
    "domain_listing": "market_signal",
    "other": "market_signal",
}

_RETENTION_BY_TYPE = {
    "consented_inbound": "consented_customer",
    "public_b2b": "b2b_prospect_12m",
    "market_signal": "signal_30d",
}


def classify(candidate: dict) -> str:
    """نوعِ کاندید را قطعی و fail-closed تعیین کن.

    اولویت: نوعِ صریحِ معتبرِ اعلام‌شده > نگاشتِ کانال > `market_signal` (سخت‌گیرانه‌ترین).
    هر ابهام → market_signal (کم‌ترین امتیاز؛ هرگز outreach)."""
    try:
        declared = str((candidate.get("candidate_type") or "")).strip()
        if declared in CANDIDATE_TYPES:
            return declared
        channel = str(((candidate.get("source") or {}).get("channel") or "")).strip()
        return _CHANNEL_DEFAULT_TYPE.get(channel, "market_signal")
    except Exception:  # noqa: BLE001 — هر خطا → سخت‌گیرانه‌ترین
        return "market_signal"


def evaluate(candidate: dict) -> dict:
    """رأیِ رضایت را برگردان. هرگز استثنا پرتاب نمی‌کند؛ هر خطا → fail-closed.

    خروجی (همیشه با کلیدهای زیر):
      candidate_type · consent_basis · outreach_allowed · retention_class ·
      compliance_reason · reasons (ردِ audit) · fail_closed (bool)
    """
    reasons: list[str] = []
    try:
        ctype = classify(candidate)
        consent = candidate.get("consent") or {}
        basis = str((consent.get("basis") or "")).strip().lower()
        if basis not in CONSENT_BASES:
            reasons.append(f"basis نامعتبر «{basis}» → unknown (fail-closed)")
            basis = "unknown"
        evidence = str((consent.get("evidence") or "")).strip()

        allowed = False   # پیش‌فرضِ همیشه بسته (R2/R4)

        if ctype == "market_signal":
            # R1: یک سیگنال هرگز outreach نمی‌شود — ساختاری، بدونِ استثنا.
            reasons.append("market_signal → outreach هرگز (R1)")
            allowed = False
        elif basis in ("none", "unknown"):
            reasons.append(f"basis={basis} → رضایتِ غایب/نامعلوم، fail-closed (R2)")
            allowed = False
        elif ctype == "consented_inbound":
            if basis == "explicit":
                reasons.append("consented_inbound + basis=explicit → مجاز (خودشان درخواست کردند)")
                allowed = True
            else:
                reasons.append(f"consented_inbound اما basis={basis} (نه explicit) → fail-closed")
                allowed = False
        elif ctype == "public_b2b":
            # R3: فقط تماسِ کسب‌وکاریِ منتشرشدهٔ نقشی، basis=inferred_business.
            if basis == "inferred_business" and evidence:
                reasons.append("public_b2b + inferred_business + evidence → مجاز (capped، ماژول ۱)")
                allowed = True
            else:
                reasons.append("public_b2b بدونِ inferred_business/evidence → fail-closed (R3)")
                allowed = False
        else:
            reasons.append(f"نوعِ ناشناخته «{ctype}» → fail-closed")
            allowed = False

        return {
            "candidate_type": ctype,
            "consent_basis": basis,
            "outreach_allowed": bool(allowed),
            "retention_class": _RETENTION_BY_TYPE.get(ctype, "signal_30d"),
            "compliance_reason": str(consent.get("compliance_reason") or "unspecified")[:80],
            "reasons": reasons,
            "fail_closed": not bool(allowed),
        }
    except Exception as e:  # noqa: BLE001 — R4: هر خطا → کاملاً بسته
        return {
            "candidate_type": "market_signal",
            "consent_basis": "unknown",
            "outreach_allowed": False,
            "retention_class": "signal_30d",
            "compliance_reason": "firewall_exception",
            "reasons": [f"exception در ارزیابی → fail-closed (R4): {type(e).__name__}"],
            "fail_closed": True,
        }


def may_outreach(candidate: dict) -> bool:
    """میان‌بُرِ بولی — همان `evaluate(...)['outreach_allowed']`، هرگز fail-open."""
    try:
        return bool(evaluate(candidate).get("outreach_allowed"))
    except Exception:  # noqa: BLE001
        return False


if __name__ == "__main__":
    import json
    samples = [
        {"candidate_type": "market_signal", "consent": {"basis": "none"},
         "source": {"channel": "nsw_da"}},
        {"candidate_type": "consented_inbound", "consent": {"basis": "explicit",
         "evidence": "submitted_quote_form"}, "source": {"channel": "telegram_manual"}},
        {"source": {"channel": "facebook_group"}, "consent": {"basis": "none"}},
        {"candidate_type": "public_b2b", "consent": {"basis": "inferred_business",
         "evidence": "office_contact_published"}},
        {"broken": True},   # → fail-closed
    ]
    for s in samples:
        print(json.dumps(evaluate(s), ensure_ascii=False))
