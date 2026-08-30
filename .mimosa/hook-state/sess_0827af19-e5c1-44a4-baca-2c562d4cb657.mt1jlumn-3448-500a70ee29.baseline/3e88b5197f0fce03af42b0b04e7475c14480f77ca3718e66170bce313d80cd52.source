#!/usr/bin/env python3
"""telegram_draft — متنِ کارت. **هیچ transport ای.**

عمداً در این ماژول هیچ تابعی به‌نامِ `send`، هیچ import ِ شبکه، و هیچ ارجاعی
به `approval_channel` وجود ندارد. نه «فلگش خاموش است» — **راهش ساخته نشده**.
تستِ `t_29` همین را می‌سنجد: سطحِ ماژول اسکن می‌شود و هر نامی که بوی ارسال
بدهد تست را قرمز می‌کند.

هر draft قبل از ساخته‌شدن از فیلترِ راز/PII رد می‌شود — **قبل**، نه بعد. اگر
بعد بود، متنِ خام یک لحظه در حافظه و احتمالاً در لاگ می‌نشست.

$0 · stdlib · pure-data · صفر ارسال.
"""
from __future__ import annotations

from . import contracts
from . import validator

SCHEMA = contracts.DRAFT_SCHEMA
DEFAULT_TTL_S = 24 * 3600.0


def _rows(status: str, metrics: dict, decision: str) -> list:
    m = metrics or {}
    return [
        f"وضعیت: {status}",
        "دامنه: رقابتِ شرکت‌های بزرگ AI",
        f"داده: {int(m.get('observation_count') or 0)} منبع / "
        f"{int(m.get('candidates_found') or 0)} کاندیدا",
        f"کشفِ معتبر: {int(m.get('actionable_discovery_count') or 0)}",
        f"فرضیه‌ها: {int(m.get('asymmetry_hypotheses') or 0)} مورد، هنوز تأییدنشده",
        f"تصمیمِ مرز: {decision}",
        f"خرج: {float(m.get('spend_amount') or 0):g}",
        f"اثرِ بیرونی: {int(m.get('external_effect_count') or 0)}",
    ]


def from_translation(receipt: dict, result: dict, *, now=None) -> dict:
    """draft از رسیدِ ترجمه + نتیجهٔ خام. متن کوتاه و صادق.

    ⚠️ عمداً هیچ‌جا نمی‌گوید «کشف شد». اگر وضعیت NO_VALID_DISCOVERY است، متن
    همان را می‌گوید — چون مالک باید بتواند از روی کارت تصمیم بگیرد، و کارتی
    که واقعیت را نرم کند تصمیمِ او را خراب می‌کند."""
    status = str((receipt or {}).get("source_status") or "UNKNOWN")
    decision = str((receipt or {}).get("decision") or "UNKNOWN")
    metrics = dict((result or {}).get("metrics") or {})
    obs = (result or {}).get("observe_summary") or {}
    if isinstance(obs, dict):
        metrics.setdefault("observation_count", obs.get("observation_count"))

    body_lines = ["🌍 اختاپوس — کشفِ دنیای واقعی", ""] + _rows(status, metrics, decision)
    note = str((result or {}).get("note") or "").strip()
    if note:
        body_lines += ["", note[:240]]
    if status in contracts.NON_ACTIONABLE:
        body_lines += ["", "هیچ اقدامی پیشنهاد نشد. این نتیجه معتبر است."]

    raw = "\n".join(body_lines)
    scan = validator.scan_sensitive(raw)
    body = validator.redact(raw)

    draft = {
        "schema": SCHEMA,
        "draft_id": f"wdd-{contracts.content_hash(body)[:16]}",
        "title": "کشفِ دنیای واقعی — گزارشِ دور",
        "body": body,
        "source_status": status,
        "discovery_id": None,
        "action_id": (receipt or {}).get("action_id"),
        "requires_owner_approval": True,
        "send_attempted": False,
        "transport": None,
        "expires_at": (float(now) + DEFAULT_TTL_S) if isinstance(now, (int, float)) else None,
        "content_hash": contracts.content_hash(body),
        "redaction": {"secrets_found": scan["secrets"],
                      "emails_found": len(scan["emails"]),
                      "phones_found": len(scan["phones"])},
        # دکمه‌ها **ساخته نمی‌شوند** در این دور — فقط توصیفِ آنچه روزی لازم است
        "proposed_buttons": [
            {"label": "مشاهده جزئیات", "verb": "wd:show"},
            {"label": "تأیید آزمایش E0", "verb": "wd:e0"},
            {"label": "رد", "verb": "wd:no"},
        ],
        "buttons_wired": False,
    }
    return draft


def from_plan(action_plan: dict, *, now=None) -> dict:
    """draft از نقشهٔ عملِ پل (مسیرِ A3). همان قواعد."""
    raw = "\n".join([
        "🧰 اختاپوس — کارتِ رأی",
        "",
        f"کلاس: {(action_plan or {}).get('classification')}",
        f"تصمیم: {(action_plan or {}).get('decision')}",
        f"دلیل: {str((action_plan or {}).get('reason') or '')[:200]}",
        "",
        "این کارت **مجوز نیست**. اجرا فقط با رأیِ امضاشده.",
    ])
    body = validator.redact(raw)
    return {"schema": SCHEMA,
            "draft_id": f"wdd-{contracts.content_hash(body)[:16]}",
            "title": "کارتِ رأیِ عمل", "body": body,
            "source_status": None, "discovery_id": None,
            "action_id": (action_plan or {}).get("action_id"),
            "requires_owner_approval": True, "send_attempted": False,
            "transport": None,
            "expires_at": (float(now) + DEFAULT_TTL_S) if isinstance(now, (int, float)) else None,
            "content_hash": contracts.content_hash(body),
            "proposed_buttons": [], "buttons_wired": False}
