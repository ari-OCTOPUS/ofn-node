#!/usr/bin/env python3
"""faq_engine.py — Project-F · موتورِ FAQ auto-draft برای DM HITL.

**هدف (لایهٔ ۲، 2026-07-16):** وقتی یک incoming DM حاوی سؤالِ رایج است، یک draft
سریع تولید می‌کند (نه ارسال!). آری هنوز باید `/dm_ok` بزند — هیچ‌چیز خودکار
ارسال نمی‌شود. این «FAQ auto» به معنای «اولین نسخهٔ draft سریع‌تر می‌آید» است.

**مرزِ سخت:** این ماژول هیچ متدِ send/transmit ندارد. فقط pattern → draft تولید
می‌کند. خروجی به dm_pipeline.draft() داده می‌شود.

Pattern‌ها (content-free، بدونِ هویت/قیمتِ ثابت):
  - price/cost/how much → draft توضیحِ قیمت‌گذاری (بدون عدد — آری پر می‌کند)
  - custom/request/bespoke → draft توضیحِ custom
  - welcome/hi/hello/new → draft welcome
  - بقیه → None (HITL عادی مثل قبل)
"""
from __future__ import annotations

import re

# الگوهای incoming DM → نوعِ draft. ترتیب مهم (اولین match برنده).
# همهٔ الگوها lowercase، content-free.
FAQ_PATTERNS: list[tuple[str, str, list[str]]] = [
    # (kind, intent, [keywords])
    ("ppv_offer", "price question",
     ["price", "cost", "how much", "how much is", "what do you charge",
      "rates", "fee", "tip menu", "ppv price"]),
    ("custom_reply", "custom request",
     ["custom", "bespoke", "personalized", "made for me", "special request",
      "can you make", "do you do custom"]),
    ("welcome", "new subscriber greeting",
     ["just subscribed", "new here", "just joined", "hi ", "hello ",
      "hey ", "welcome me"]),
    ("winback", "returning/expired",
     ["resubscribe", "coming back", "missed you", "expired", "renew"]),
]

# قالب‌های draft (content-free — آری اعداد/جزئیات را پر می‌کند).
# تمامی پاسخ‌ها از گاردِ containment رد می‌شوند (هیچ کلمهٔ banned).
DRAFT_TEMPLATES: dict[str, dict] = {
    "ppv_offer": {
        "subject": "Re: pricing",
        "body": ("Thanks for asking! Here are the options: "
                 "[insert PPV tiers here — operator fills]. "
                 "Let me know what works for you."),
        "context_note": "AUTO-FAQ: price question — fill tiers before approving",
    },
    "custom_reply": {
        "subject": "Re: custom",
        "body": ("Happy to hear what you have in mind. Custom requests start at "
                 "[insert base price — operator fills] and depend on complexity. "
                 "Tell me the details and I'll quote you."),
        "context_note": "AUTO-FAQ: custom request — fill base price before approving",
    },
    "welcome": {
        "subject": "Welcome!",
        "body": ("So glad you're here! Here's what to expect: "
                 "[insert welcome offer — operator fills]. "
                 "Reply anytime — I read everything."),
        "context_note": "AUTO-FAQ: new subscriber — personalize before approving",
    },
    "winback": {
        "subject": "Welcome back?",
        "body": ("Missed you! If you're thinking of coming back, "
                 "[insert winback offer — operator fills]. "
                 "No pressure either way."),
        "context_note": "AUTO-FAQ: returning/expired — fill offer before approving",
    },
}


def classify(text: str) -> tuple[str, str] | None:
    """classify یک incoming DM. بازگشتی: (kind, intent) یا None.

    None یعنی «ناشناخته — HITL عادی». این موتور فقط برای FAQ‌های رایج است،
    نه جایگزینِ آری."""
    if not text:
        return None
    low = (text or "").lower().strip()
    # حداقل طول — کمتر از ۳ کاراکتر نادیده
    if len(low) < 3:
        return None
    for kind, intent, keywords in FAQ_PATTERNS:
        for kw in keywords:
            # word-boundary ساده (نه regex سنگین)
            if kw in low:
                return (kind, intent)
    return None


def draft_for(text: str) -> dict | None:
    """یک قالبِ draft برای این incoming DM تولید کن.

    بازگشتی: dict با subject/body/context_note/kind/intent، یا None.
    توجه: این قالب هنوز [placeholders] دارد — آری باید پر کند قبل از approve.
    هیچ ارسالی اینجا اتفاق نمی‌افتد."""
    cls = classify(text)
    if cls is None:
        return None
    kind, intent = cls
    tmpl = DRAFT_TEMPLATES.get(kind)
    if not tmpl:
        return None
    return {
        "kind": kind,
        "intent": intent,
        "channel": "of",   # پیش‌فرض؛ آری می‌تواند تغییر دهد
        "subject": tmpl["subject"],
        "body": tmpl["body"],
        "context_note": tmpl["context_note"],
        "auto_drafted": True,
    }


def auto_draft_to_pipeline(text: str, dm_pipeline, channel: str = "of") -> dict:
    """Helper: یک incoming DM را classify کن و اگه FAQ بود، در dm_pipeline صف کن.

    بازگشتی:
      - {"ok": True, "matched": True, "id": ...} اگه FAQ بود
      - {"ok": True, "matched": False} اگه HITL عادی لازم است
      - {"ok": False, "error": ...} اگه خطا
    هیچ‌چیز ارسال نمی‌شود — فقط draft ساخته می‌شود (pending_review)."""
    draft = draft_for(text)
    if draft is None:
        return {"ok": True, "matched": False}
    try:
        r = dm_pipeline.draft(
            channel=channel or draft["channel"],
            kind=draft["kind"],
            body=draft["body"],
            subject=draft["subject"],
            context_note=draft["context_note"],
            proposed_by="faq_engine")
        return {"ok": True, "matched": True, "id": r.get("id"),
                "kind": draft["kind"], "intent": draft["intent"]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
