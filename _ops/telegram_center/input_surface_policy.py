#!/usr/bin/env python3
"""input_surface_policy — «این پیام از کجا آمد و اجازهٔ چه دارد؟»

مکملِ `surface_router`، و عمداً جدا از آن: آن یکی می‌گوید خروجی **کجا برود**،
این یکی می‌گوید ورودی **چه اجازه‌ای دارد**. تا امروز فقط خروجی سیاست داشت، پس
گروه می‌توانست فرمانِ هسته‌ای بگیرد حتی وقتی هیچ خروجیِ هسته‌ای به آن نمی‌رفت.

قراردادِ مرجع: `_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json`

    outer + DM + مالک            → گفت‌وگوی کامل با کلِ اختاپوس
    inner + DM + مالک            → سلامت، هشدار، approval، رسید
    outer + گروه + تاپیکِ پا     → فقط همان پا (leg-scoped)
    گروه + General/تاپیکِ ناشناخته → deny + redirect به DM
    گروه + فرمانِ هسته‌ای         → deny + redirect به DM
    گروه + کارِ بین-پایی          → clarify (کدام پا؟)
    غیرمالک + هر جهش              → deny

⚠️ **این ماژول صداکننده ندارد و عمداً.** وصل‌کردنش یعنی ویرایشِ `center.py` که
امروز هانکِ کامیت‌نشدهٔ یک جلسهٔ موازی دارد (§۵ قاعدهٔ درختِ مشترک). این‌جا
آماده و اثبات‌شده می‌ماند تا آن هانک‌ها کامیت شوند.

$0 · stdlib · تابعِ خالص · صفر I/O · صفر side effect.
"""
from __future__ import annotations

import re

MODES = ("core_conversation", "status_approval", "leg_scoped",
         "clarify", "deny")

# فرمان‌هایی که هرگز از گروه پذیرفته نمی‌شوند — حتی از مالک، حتی read-only.
# دلیل: گروه یک سطحِ **مشترک** است؛ چیزی که آن‌جا تایپ می‌شود در تاریخچهٔ یک
# فضای چندنفره می‌ماند و context ِ پا را با context ِ هسته قاطی می‌کند.
CORE_VERBS = frozenset({
    "panic", "stop", "resume", "restart", "halt", "kill", "power",
    "budget", "spend", "pay", "approve", "deny", "verdict",
    "flag", "arm", "disarm", "deploy", "merge", "push",
    "secret", "token", "env", "capabilities", "capability",
    "goal", "goals", "mission", "cycle", "scorecard",
    "discovery", "world", "doctor", "brain", "ask", "chat",
    "memory", "recall", "learn", "improve", "patch", "code",
})

# فعل‌هایی که در گروه، **داخلِ تاپیکِ خودِ پا**، مجازند.
LEG_VERBS = frozenset({
    "status", "وضعیت", "blocker", "بلاکر", "next", "قدم",
    "pause", "resume_leg", "outcome", "نتیجه", "lead", "لید",
})

_CMD = re.compile(r"^\s*/([A-Za-z_][A-Za-z0-9_]*)")
_CORE_WORDS = re.compile(
    r"(کلِ? سیستم|همهٔ? پاها|بودجه|خرج|راز|توکن|ری[‌\s]*استارت|"
    r"خاموش کن|قطع کن|تأیید کن|فلگ|کشفِ? دنیا|دکتر|حافظه)", re.I)


def _verb_of(text: str) -> "str | None":
    m = _CMD.match(str(text or ""))
    return m.group(1).lower() if m else None


def classify(update: dict, *, bot_role: str, owner_id, group_id,
             topics: dict) -> dict:
    """{allow, mode, leg, redirect, reason}. هر ابهام ⇒ deny یا clarify.

    `update` شکلِ خامِ تلگرام است. `topics` نگاشتِ `{leg_key: topic_id}` از
    center-config. `bot_role` یکی از `outer`/`inner`.

    هیچ‌جا استثنا پرتاب نمی‌شود — ورودیِ خصمانه فقط `deny` می‌گیرد."""
    if not isinstance(update, dict):
        return _deny("bad-update")
    msg = update.get("message") or update.get("callback_query", {}).get("message") or {}
    if not isinstance(msg, dict):
        return _deny("bad-message")
    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    frm = (update.get("message") or update.get("callback_query") or {}).get("from") or {}
    text = str((update.get("message") or {}).get("text")
               or (update.get("callback_query") or {}).get("data") or "")

    chat_id = chat.get("id")
    chat_type = str(chat.get("type") or "").lower()
    is_dm = chat_type == "private"
    is_group = chat_id is not None and group_id is not None and chat_id == group_id

    # ── مالک بودن ───────────────────────────────────────────────────────────
    try:
        is_owner = owner_id is not None and int(frm.get("id")) == int(owner_id)
    except (TypeError, ValueError):
        is_owner = False
    if not is_owner:
        # غیرمالک هیچ جهشی ندارد. حتی خواندن هم در این قرارداد owner-only است.
        return _deny("non-owner")

    role = str(bot_role or "").strip().lower()

    # ── DM ──────────────────────────────────────────────────────────────────
    if is_dm:
        if role == "outer":
            return {"allow": True, "mode": "core_conversation", "leg": None,
                    "redirect": None, "reason": "outer-dm-owner"}
        if role == "inner":
            # چتِ آزاد در inner جایش نیست — ولی deny نمی‌شود، هدایت می‌شود.
            if _verb_of(text) in (None,) and len(text.strip()) > 0 \
                    and not update.get("callback_query"):
                return {"allow": False, "mode": "clarify", "leg": None,
                        "redirect": "outer_dm",
                        "reason": "inner-dm-free-chat→outer"}
            return {"allow": True, "mode": "status_approval", "leg": None,
                    "redirect": None, "reason": "inner-dm-owner"}
        return _deny(f"unknown-bot-role:{role!r}")

    # ── گروه ────────────────────────────────────────────────────────────────
    if not is_group:
        # نه DM، نه گروهِ شناخته‌شده. مثلاً یک سوپرگروهِ دیگر.
        return _deny("unknown-chat")
    if role != "outer":
        return _deny("inner-bot-in-group")

    thread = msg.get("message_thread_id")
    leg = _leg_of(thread, topics)
    if leg is None:
        # General (بدونِ thread) یا تاپیکِ ناشناخته — هر دو یک حکم دارند.
        return {"allow": False, "mode": "deny", "leg": None,
                "redirect": "outer_dm",
                "reason": "group-general-or-unknown-topic"}

    verb = _verb_of(text)
    if verb and verb in CORE_VERBS:
        return {"allow": False, "mode": "deny", "leg": leg,
                "redirect": "outer_dm", "reason": f"core-command-in-group:/{verb}"}
    if _CORE_WORDS.search(text):
        return {"allow": False, "mode": "deny", "leg": leg,
                "redirect": "outer_dm", "reason": "core-topic-in-group"}

    other = _mentions_other_leg(text, leg, topics)
    if other:
        return {"allow": False, "mode": "clarify", "leg": leg,
                "redirect": None,
                "reason": f"cross-leg:{other}-mentioned-in-{leg}-topic"}

    return {"allow": True, "mode": "leg_scoped", "leg": leg,
            "redirect": None, "reason": f"group-topic-{leg}"}


def _leg_of(thread_id, topics: dict) -> "str | None":
    """تاپیک → کلیدِ پا. General (thread=None) و ناشناخته هر دو `None`."""
    if thread_id is None or not isinstance(topics, dict):
        return None
    for key, tid in topics.items():
        try:
            if int(tid) == int(thread_id):
                return str(key)
        except (TypeError, ValueError):
            continue
    return None


def _mentions_other_leg(text: str, leg: str, topics: dict) -> "str | None":
    """نامِ پای دیگری در تاپیکِ این پا؟ ⇒ clarify، نه اجرا.

    عمداً clarify و نه deny: مالک احتمالاً منظورِ درستی دارد، فقط جای اشتباه
    نوشته. ولی حدس‌زدنِ اینکه کدام پا را می‌خواهد، همان چیزی است که یک بار
    «مسیریابی به فلگِ خاموش» ساخت."""
    t = str(text or "").lower()
    for key in (topics or {}):
        k = str(key).lower()
        if k and k != str(leg).lower() and re.search(rf"\b{re.escape(k)}\b", t):
            return str(key)
    return None


def _deny(reason: str) -> dict:
    return {"allow": False, "mode": "deny", "leg": None,
            "redirect": None, "reason": reason}


def redirect_text(decision: dict) -> str:
    """متنِ کوتاهِ هدایت. هرگز اجرا نمی‌کند، فقط می‌گوید کجا برود."""
    r = (decision or {}).get("redirect")
    reason = str((decision or {}).get("reason") or "")
    if r == "outer_dm":
        if "core-command" in reason or "core-topic" in reason:
            return ("این‌جا فقط دربارهٔ همین پا حرف می‌زنیم. برای کارِ هسته‌ای "
                    "در چتِ خصوصی بنویس.")
        return ("این تاپیک به هیچ پایی وصل نیست. برای گفت‌وگوی عمومی چتِ خصوصی."
                )
    if (decision or {}).get("mode") == "clarify":
        return "کدام پا را می‌گویی؟ در تاپیکِ خودش بنویس تا context درست باشد."
    return ""
