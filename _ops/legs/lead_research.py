#!/usr/bin/env python3
"""lead_research.py — Lane G (منشور TG-UI ۲۰۲۶-۰۷-۳۱، رأی ۱۳): مرحلهٔ تحقیقِ لید.

شکافِ «RESEARCH وجود ندارد» ِ نقشهٔ لید را می‌بندد: چک‌لیستِ قطعیِ $0 که بینِ sense و
score می‌نشیند. هیچ شبکه، هیچ خرج، هیچ effector — فقط تحلیلِ همان dict ِ لید.

خروجیِ enrich چهار چیز می‌دهد:
  · score_hints — سیگنال‌های بولی (آدرس؟ دامنهٔ رنگ؟ متراژ؟ بودجه؟ زمان‌بندی؟ کانالِ رضایت‌دار؟)
  · missing    — چیزهای غایب (زیرمجموعهٔ CRITICAL ⇒ مسیرِ «گیر» ِ منشور: کار BLOCKED + سؤالِ آزاد)
  · questions  — سؤال‌های فارسیِ آماده برای کارتِ 🚧 (ریپلای = رفعِ مانع، مکانیکِ leg_tasks موجود)
  · summary    — یک‌خطیِ خوانا برای کارتِ لید

polish ِ اختیاری با LLMِ محلی از راهِ ask_fn ِ تزریقی (هرگز paid؛ شکست = همان summary ِ قطعی).
stdlib-only؛ خالص (بدونِ I/O).
"""
from __future__ import annotations

# چیزهای حیاتی — غیبتشان یعنی لید قابلِ امتیازدهی/پیش‌نویس نیست ⇒ مسیرِ گیر (BLOCKED + سؤال).
CRITICAL = ("address", "scope")

_PAINT_KWS = ("paint", "repaint", "render", "coating", "facade", "fitout", "fit out",
              "fit-out", "refurbish", "remedial", "نقاشی", "رنگ")
_SIZE_KWS = ("m2", "sqm", "m²", "متر", "متراژ", "storey", "units", "rooms")
_TIMELINE_KWS = ("urgent", "asap", "deadline", "by ", "next week", "next month",
                 "فوری", "هفته", "ماهِ", "تاریخ")
_BUDGET_HINTS = ("budget", "$", "aud", "بودجه", "قیمت", "تومان", "دلار")

_QUESTIONS = {
    "address": "آدرس یا حداقل محله/suburb پروژه کجاست؟",
    "scope": "دامنهٔ کار چیست؟ (رنگ‌آمیزی داخلی/خارجی، چند اتاق/طبقه، وضعیتِ سطح)",
    "size": "متراژ یا ابعادِ تقریبیِ کار چقدر است؟",
    "budget": "نشانه‌ای از بودجه یا ارزشِ کار داریم؟",
    "timeline": "زمان‌بندیِ موردِ نظرِ مشتری چیست؟",
    "contact": "کانالِ تماسِ رضایت‌دار (ایمیل/تلفنِ خودِ مشتری) چیست؟",
}


def _txt(lead: dict) -> str:
    return " ".join(str(lead.get(k, "") or "") for k in
                    ("description", "address", "applicant")).lower()


def _has_scope(text: str) -> bool:
    return any(k in text for k in _PAINT_KWS)


def _consented_contact(lead: dict) -> bool:
    """کانالِ رضایت‌دار: پاکتِ candidate (consent.outreach_allowed) یا contact ِ صریح.
    فقط hint است — حکمِ نهاییِ ارسال همیشه با consent_firewall/گیت است، نه این‌جا."""
    cand = lead.get("candidate") if isinstance(lead.get("candidate"), dict) else {}
    consent = cand.get("consent") if isinstance(cand.get("consent"), dict) else {}
    if consent.get("outreach_allowed") is True:
        return True
    contact = lead.get("contact") if isinstance(lead.get("contact"), dict) else {}
    return bool(contact.get("email") or contact.get("phone"))


def enrich(candidate: dict, *, ask_fn=None) -> dict:
    """چک‌لیستِ قطعیِ تحقیق روی یک لید (شکلِ lead_sense: حداقل description).

    خروجی: {"score_hints": {...}, "missing": [...], "questions": [...], "summary": str}
    هرگز استثنا؛ ورودیِ خراب = همه‌چیز missing (fail-honest، نه fail-open)."""
    lead = candidate if isinstance(candidate, dict) else {}
    text = _txt(lead)

    hints = {
        "has_address": bool(str(lead.get("address") or "").strip()),
        "has_scope": _has_scope(text),
        "has_size": bool(lead.get("size_m2")) or any(k in text for k in _SIZE_KWS),
        "has_budget_signal": (lead.get("cost_of_development") is not None
                              or lead.get("expected_aud") is not None
                              or any(k in text for k in _BUDGET_HINTS)),
        "has_timeline": any(k in text for k in _TIMELINE_KWS),
        "has_consented_contact": _consented_contact(lead),
    }
    key_of = {"address": "has_address", "scope": "has_scope", "size": "has_size",
              "budget": "has_budget_signal", "timeline": "has_timeline",
              "contact": "has_consented_contact"}
    missing = [name for name, hk in key_of.items() if not hints[hk]]
    questions = [_QUESTIONS[m] for m in missing]

    known = [n for n, hk in key_of.items() if hints[hk]]
    summary = ("تحقیق: دارد=" + (",".join(known) or "هیچ")
               + " · غایب=" + (",".join(missing) or "هیچ"))
    if callable(ask_fn):
        try:   # polish ِ محلیِ اختیاری — هرگز paid، شکست = summary ِ قطعی
            polished = ask_fn(
                "یک‌خطی و فارسی خلاصه کن (بدونِ حدس، فقط همین داده):\n"
                + str(lead.get("description", ""))[:400] + "\n" + summary)
            if isinstance(polished, str) and polished.strip():
                summary = polished.strip()[:200]
        except Exception:  # noqa: BLE001
            pass

    return {"score_hints": hints, "missing": missing,
            "questions": questions, "summary": summary}


def is_stuck(enriched: dict) -> bool:
    """آیا چیزی از CRITICAL غایب است؟ (⇒ مسیرِ گیر: BLOCKED + سؤالِ آزادِ فارسی در 🎨)"""
    missing = (enriched or {}).get("missing") or []
    return any(m in missing for m in CRITICAL)


def stuck_question(enriched: dict) -> str:
    """سؤالِ فارسیِ کارتِ 🚧 — فقط غایب‌های CRITICAL (سؤالِ کوتاه، نه بازجویی)."""
    missing = (enriched or {}).get("missing") or []
    qs = [_QUESTIONS[m] for m in CRITICAL if m in missing]
    return " و ".join(qs) if qs else "توضیحِ بیشتری از خودِ کار لازم دارم."


if __name__ == "__main__":
    import json
    demo = enrich({"description": "repaint of house exterior", "address": ""})
    print(json.dumps(demo, ensure_ascii=False, indent=2))
