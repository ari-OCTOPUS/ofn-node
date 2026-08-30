#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""speed_to_lead.py — Trust-Engine P0-3 · D4 (فاز D): نیمهٔ first-response (LEG_P0-1).

قراردادِ حاکم: `03 - Projects/Lead-نقاشی/Trust-Engine-v1.1/legs/LEG_P0-1_speed_to_lead.md`.

نقش: یک لیدِ qualified را می‌گیرد و یک **first-response draft** می‌سازد — متنِ پیشنهادیِ
اولیه برای نمایش به مالک. **هرگز چیزی نمی‌فرستد.** خروجی یک LegProposal است که LiveLoop در
کارتِ مالک نمایش می‌دهد (همان مسیرِ فعلیِ `_proposal_card`). مالک با دکمهٔ verdict تصمیم
می‌گیرد (D1 وصل می‌شود). این ماژول فقط «نیمهٔ غایبِ P0-3» را پر می‌کند: تولیدِ draft.

دو-مرحله‌ای (LEG_P0-1 §Mission):
  stage 1 = کارتِ فوری با فکت‌های خام (نام/محله/متن/فوریت) — هم‌الگو با `_proposal_card` موجود.
  stage 2 = draft به همان کارت append می‌شود (وقتی LLM آماده شد).

در D4، stage 1 و draft هم‌جا تولید می‌شوند (ساده‌تر، بدون async). stage-2 async در فازِ آینده.

مهم (الگوهای ایمنی):
  · flag خاموش = no-op مطلق (رفتارِ امروز: lead_quote-only، بدونِ first-response).
  · LLM اختیاری است پشتِ flag؛ اگر نبود یا خطا داد، **fallback template** ثابت برمی‌گردد
    (هرگز «هیچ» — LEG_P0-1 §Failure modes).
  · quiet hours (07:30-20:30 AEST) فقط scheduled-label می‌سازد؛ خودِ ارسال باز است (در D7).
  · PII هرگز در signals/log echo نمی‌شود (الگوی `_safe_card_text`).
  · stdlib-only در بدنه؛ LLM lazy import پشتِ try (fail-soft).
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta

FLAG = "OCTOPUS_WIRE_LEAD_FIRST_RESPONSE"   # پیش‌فرض خاموش
FLAG_LLM = "OCTOPUS_WIRE_LEAD_FIRST_RESPONSE_LLM"   # LLM اختیاری، پیش‌فرض خاموش (fallback template)

# Sydney AEST = UTC+10 (ساده‌شده، بدونِ DST handling در D4 — DST در فازِ آینده)
_AEST = timezone(timedelta(hours=10))
_QUIET_START_H = 7     # 07:30
_QUIET_END_H = 20      # 20:30
_QUIET_START_M = 30
_QUIET_END_M = 30

_SMS_MAX = 320


def enabled() -> bool:
    """flag خاموش (پیش‌فرض) = no-op مطلق. live_loop این را چک می‌کند."""
    return os.environ.get(FLAG) == "1"


def _is_quiet_hours(now=None) -> tuple[bool, str | None]:
    """آیا الان خارج از ساعتِ کاریِ AEST است؟ (LEG_P0-1 §Guard checks).
    خروجی: (quiet, scheduled_at_str). scheduled_at = بازشدنِ پنجرهٔ بعدی."""
    try:
        t = now or datetime.now(_AEST)
        h, m = t.hour, t.minute
        in_window = (h > _QUIET_START_H or (h == _QUIET_START_H and m >= _QUIET_START_M))
        in_window = in_window and (h < _QUIET_END_H or (h == _QUIET_END_H and m <= _QUIET_END_M))
        if in_window:
            return (False, None)
        # scheduled: بازشدنِ پنجرهٔ بعدی (امروز یا فردا)
        next_open = t.replace(hour=_QUIET_START_H, minute=_QUIET_START_M, second=0, microsecond=0)
        if t >= next_open:
            next_open = next_open + timedelta(days=1)
        return (True, next_open.strftime("%a %H:%M AEST"))
    except Exception:  # noqa: BLE001 — ابهامِ timezone = not quiet (ایمن‌ترین)
        return (False, None)


# ── fallback template (بدونِ LLM، LEG_P0-1 §Failure modes) ────────────────────
def _fallback_draft(lead: dict, *, owner_name="Ari", business_name="Upscale Painting") -> dict:
    """draft ثابت وقتی LLM نیست یا خطا داد. هرگز 'هیچ' برنمی‌گرداند.
    خروجی: {message, channel, summary, urgency, reasoning, source: 'fallback'}."""
    name = str((lead.get("contact") or {}).get("name") or lead.get("applicant") or "").strip()
    suburb = str(lead.get("suburb") or "").strip()
    scope = str((lead.get("request") or {}).get("scope_text") or lead.get("description") or "").strip()
    channel_hint = str((lead.get("contact") or {}).get("preferred_channel") or "sms").strip().lower()
    channel = "email" if channel_hint == "email" else "sms"
    greeting = f"Hi {name}" if name else "Hi there"
    loc = f" in {suburb}" if suburb else ""
    msg = (f"{owner_name} from {business_name} here — {greeting}, got your enquiry{loc}. "
           f"I'll take a look and come back within the hour with a time. Reply STOP to opt out.")
    if len(msg) > _SMS_MAX:
        msg = msg[:_SMS_MAX - 3] + "..."
    return {"message": msg, "channel": channel, "summary": f"first-response (fallback){loc}",
            "urgency": "standard", "reasoning": "fallback template (no LLM)", "source": "fallback"}


# ── LLM draft (اختیاری، پشتِ flag، fail-soft) ─────────────────────────────────
def _llm_draft(lead: dict) -> dict | None:
    """draft با LLM. پشتِ OCTOPUS_WIRE_LEAD_FIRST_RESPONSE_LLM. خطا/نبود → None (caller fallback).
    هرگز در بدنهٔ ماژول import نمی‌شود (lazy، الگوی llm_intent)."""
    if os.environ.get(FLAG_LLM) != "1":
        return None
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _mr = str(_Path(__file__).resolve().parent.parent)
        if _mr not in _sys.path:
            _sys.path.insert(0, _mr)
        import model_router   # noqa: WPS433 — lazy
        scope = str((lead.get("request") or {}).get("scope_text") or lead.get("description") or "")
        suburb = str(lead.get("suburb") or "")
        name = str((lead.get("contact") or {}).get("name") or lead.get("applicant") or "")
        prompt = (f"Draft ONE first-response SMS reply to a painting enquiry. "
                  f"Name: {name or 'unknown'}. Suburb: {suburb or 'unknown'}. "
                  f"Enquiry: {scope[:300]}. Max 320 chars, warm professional, "
                  f"start with greeting, end with STOP opt-out, NO price, NO date promise. "
                  f"Output JSON: {{message, summary, urgency}}.")
        # 2026-07-25 فیکس: امضای واقعیِ master = ask(task, prompt, …) و خروجی {"ok","text"}
        # (نه reason=/ {"message"} فاز-D). task="draft" → tierِ محلیِ $0 (TASK_TIERS.get→local).
        r = model_router.ask("draft", prompt, max_tokens=220)
        if not (isinstance(r, dict) and r.get("ok")):
            return None
        text = str(r.get("text") or "").strip()
        if not text:
            return None
        # سعیِ parse JSON از متن؛ نشد → خودِ متن را پیام بگیر (fail-soft)
        obj = None
        try:
            import json as _json   # noqa: WPS433
            obj = _json.loads(text[text.index("{"):text.rindex("}") + 1])
        except Exception:  # noqa: BLE001
            obj = None
        if isinstance(obj, dict) and obj.get("message"):
            return {"message": str(obj["message"])[:_SMS_MAX], "channel": "sms",
                    "summary": str(obj.get("summary") or "first-response")[:200],
                    "urgency": str(obj.get("urgency") or "standard"),
                    "reasoning": "llm", "source": "llm"}
        return {"message": text[:_SMS_MAX], "channel": "sms",
                "summary": "first-response (llm)", "urgency": "standard",
                "reasoning": "llm-str", "source": "llm"}
    except Exception:  # noqa: BLE001 — LLM هرگز مسیر را نمی‌کشد
        return None


# ── urgency detection (ساده، deterministic) ──────────────────────────────────
_URGENT_PATTERNS = re.compile(
    r"\b(urgent|asap|emergency|water damage|flood|leak|mould|mold|end of lease|"
    r"moving|auction|settlement|deadline|tomorrow|today)\b", re.IGNORECASE)


def _detect_urgency(text: str) -> str:
    """urgency flag از متن. deterministic (LEG_P0-1 §LLM: urgency detection)."""
    if _URGENT_PATTERNS.search(text or ""):
        return "urgent"
    return "standard"


# ── main: build first-response proposal ───────────────────────────────────────
def build_first_response(lead: dict, *, owner_name="Ari", business_name="Upscale Painting",
                         now=None) -> dict:
    """یک لیدِ qualified → first-response proposal (draft + کارتِ نمایش).
    **هرگز چیزی نمی‌فرستد.** خروجی یک dict با payload برای LiveLoop._proposal_card.

    خروجی: {ok, kind: 'first_response', lead_id, card, draft, urgency, scheduled_at?, source}
      · card: متنِ کارتِ مالک (HTML، الگوی _proposal_card).
      · draft: {message, channel, summary, urgency, source}.
      · scheduled_at: str اگر quiet hours (نه send، فقط label).
    fail-soft: هرگز استثنا، همیشه dict."""
    try:
        if not enabled():
            return {"ok": False, "reason": "flag-off"}
        lid = str(lead.get("lead_id") or "").strip()
        if not lid:
            return {"ok": False, "reason": "no_lead_id"}
        scope = str((lead.get("request") or {}).get("scope_text") or lead.get("description") or "")
        # urgency
        urgency = _detect_urgency(scope)
        # draft: LLM اگر هست، وگرنه fallback (هرگز None)
        draft = _llm_draft(lead)
        if draft is None:
            draft = _fallback_draft(lead, owner_name=owner_name, business_name=business_name)
        if urgency == "urgent":
            draft["urgency"] = "urgent"
        # quiet hours
        quiet, sched = _is_quiet_hours(now)
        # کارتِ مالک (الگوی LEG_P0-1 §Telegram approval card)
        name = str((lead.get("contact") or {}).get("name") or lead.get("applicant") or "Unknown")
        suburb = str(lead.get("suburb") or "?")
        service = str((lead.get("request") or {}).get("service_hint") or lead.get("service_hint") or "?")
        channel = str(lead.get("source") or lead.get("source_channel") or "?")
        send_label = "now" if not quiet else f"scheduled {sched}"
        card = (f"⚡ <b>NEW LEAD</b> ({channel})\n"
                f"{name} · {suburb} · {service}\n"
                f'"<i>{scope[:200]}</i>"\n'
                f"Urgency: {urgency} | Send: {send_label}\n"
                f"── Draft ({draft['channel']}) ──\n"
                f"{draft['message']}")
        return {"ok": True, "kind": "first_response", "lead_id": lid,
                "card": card, "draft": draft, "urgency": urgency,
                "scheduled_at": sched if quiet else None,
                "source": draft.get("source", "fallback")}
    except Exception as e:  # noqa: BLE001 — fail-soft مطلق
        return {"ok": False, "reason": f"exception:{type(e).__name__}"}
