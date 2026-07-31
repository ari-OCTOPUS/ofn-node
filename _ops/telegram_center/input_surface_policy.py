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
    گروه + هر فرمانِ / (هسته‌ای یا نه) → deny + redirect به DM  (۲۰۲۶-۰۷-۳۱)
    گروه + کارِ بین-پایی          → clarify (کدام پا؟)
    غیرمالک + هر جهش              → deny

**صداکننده:** `center.py` در `handle_update` (۲۰۲۶-۰۷-۳۰) این ماژول را روی
هر update صدا می‌زند و تصمیمش را اجرا می‌کند. (تا ۲۰۲۶-۰۷-۳۱ این سرِصفحه
می‌گفت «صداکننده ندارد و عمداً» — آن هنگام درست بود؛ حالا که وصل شد، اگر این
سطر را نخوانده باشی ماژول را «یتیم» پنداشته و پاکش می‌کنی.)

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

# ۸ پایِ مجاز در گروه (از TELEGRAM-ACCESS-CONTRACT.v1.json:117 allowed_topics).
# system و mirror عمداً بیرون‌اند — آن‌ها پا نیستند، حتی اگر در center-config
# باشند. این فهرست منبعِ حقیقتِ «چه چیزی در گروه پا شمرده می‌شود» است.
ALLOWED_LEG_TOPICS = frozenset({
    "lead", "ziman", "mining", "crypto",
    "accounting", "studio_pf", "knowledge", "cartographer",
})

# نامِ فارسیِ هر پا. کلیدهای واقعیِ تاپیک (center-config) همه لاتین‌اند، ولی مالک
# فارسی می‌نویسد — پس تشخیصِ بین-پایی که فقط کلیدِ لاتین را بگردد، در عمل کور است.
#
# ⚠️ این دقیقاً همان باگی بود که تستِ سبز نگرفت: بندِ cross-leg با
# «وضعیتِ mining چطوره؟» سنجیده می‌شد — واژهٔ **لاتین** داخلِ جملهٔ فارسی. جملهٔ
# واقعیِ runbook گیت ۶ («ماینینگ را متوقف کن») از گیت رد می‌شد و
# `leg_scoped` می‌گرفت. الگو روی نمونه‌ای کالیبره شده بود که قطعاً می‌گیرد.
#
# فهرست عمداً **کوتاه و متمایز** است: هر واژهٔ پرکاربردِ عمومی («حساب»، «ارز»،
# «سیستم») بیرون گذاشته شده، چون بیش‌بست هم به‌اندازهٔ کم‌بست بد است — clarify ِ
# بی‌مورد یعنی مالک یاد می‌گیرد گیت را جدی نگیرد.
LEG_ALIASES = {
    "lead":       ("لید", "نقاشی", "painting"),
    "ziman":      ("زیمان", "زیمن", "گالری"),
    "mining":     ("ماینینگ", "ماینر", "استخراج"),
    "crypto":     ("کریپتو", "اتورو", "etoro"),
    "accounting": ("حسابداری",),
    "studio_pf":  ("استودیو", "اونلی‌فنز", "اونلی فنز", "onlyfans"),
    "knowledge":  ("دانش",),
    "cartographer": ("نقشه‌کش", "کارتوگراف"),
    "mirror":     ("آینه",),
}

_CMD = re.compile(r"^\s*/([A-Za-z_][A-Za-z0-9_]*)")
# (۲۰۲۶-۰۷-۳۱) فرمانِ فارسی هم شناخته شود — تا /وضعیت و /بودجه در گروه گیر کنند.
_CMD_FA = re.compile(r"^\s*/([\u0600-\u06FF][\u0600-\u06FF\s]*)")
# فعلِ callback: pw: pwc: tr: tk: ap: … — با / شروع نمی‌شوند ولی کارِ هسته‌ای‌اند.
_CB_VERB = re.compile(r"^([A-Za-z][A-Za-z0-9_]{0,15}):")
_CORE_WORDS = re.compile(
    r"(کلِ? سیستم|همهٔ? پاها|بودجه|خرج|راز|توکن|ری[‌\s]*استارت|"
    r"خاموش کن|قطع کن|تأیید کن|فلگ|کشفِ? دنیا|دکتر|حافظه)", re.I)


def _verb_of(text: str) -> "str | None":
    """فعلِ فرمان: /x یا /فارسی. None یعنی فرمان نیست (متنِ آزاد)."""
    t = str(text or "")
    m = _CMD.match(t)
    if m:
        return m.group(1).lower()
    m = _CMD_FA.match(t)
    if m:
        return m.group(1).strip()
    return None


def _callback_verb_of(text: str) -> "str | None":
    """فعلِ callback (pw: pwc: tr: …). در گروه فعلاً استفاده نمی‌شود (دکمه‌های
    core دیگر در گروه رندر نمی‌شوند چون فرمانِ / ممنوع است) ولی برای آینده
    و برای تست نگه داشته شده است."""
    m = _CB_VERB.match(str(text or ""))
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
    # (۲۰۲۶-۰۷-۳۱، رفعِ boundary-1/group-1) — تا امروز فقط CORE_VERBS رد می‌شد؛
    # هر فرمانِ / دیگری (/now, /menu, /missions, /lead, …) از گیت رد می‌شد،
    # leg_scoped می‌گرفت، و بعد در _handle_message روی جدولِ کاملِ فرمان‌های مالک
    # اجرا می‌شد. یعنی ۳۱ از ۳۹ فرمانِ probingشده در گروه اجرا می‌شدند.
    # قانونِ اصولی: در گروه، **هیچ** فرمانِ / مجاز نیست — کارِ پا از مسیرِ
    # طبیعی (leg_commands: «وضعیت»/«صف»/…) یا دکمه‌ها می‌رود، نه از /.
    # (callback verbها مثلِ tk:/pw: عمداً بی‌اثر نشدند — آن‌ها از دکمه‌هایی
    # می‌آیند که خودِ سیستم در جایِ مجاز گذاشته، و دکمه‌های core با همین قانون
    # دیگر در گروه رندر نمی‌شوند.)
    if verb:
        return {"allow": False, "mode": "deny", "leg": leg,
                "redirect": "outer_dm",
                "reason": f"slash-command-in-group:/{verb}"}
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
    """تاپیک → کلیدِ پا. General (thread=None) و ناشناخته هر دو `None`.

    (۲۰۲۶-۰۷-۳۱، رفعِ group-6/boundary-7) — تا امروز هر کلیدِ داخلِ topics
    پذیرفته می‌شد، حتی system/mirror که قرارداد (allowed_topics = ۸) آن‌ها را
    جزءِ پاها نمی‌داند. نتیجه: تاپیکِ ۲۸ (system) و ۲۰۵ (mirror) به‌عنوان پا
    شناخته می‌شدند و فرمانِ هسته‌ای از آن‌ها مجاز می‌گرفت. حالا فقط ۸ پایِ
    مصوب پذیرفته می‌شوند — بقیه (حتی اگر در center-config باشند) None می‌شوند."""
    if thread_id is None or not isinstance(topics, dict):
        return None
    for key, tid in topics.items():
        try:
            if int(tid) == int(thread_id):
                return str(key) if key in ALLOWED_LEG_TOPICS else None
        except (TypeError, ValueError):
            continue
    return None


def _surface_forms(key: str) -> tuple:
    """همهٔ شکل‌هایی که یک پا ممکن است با آن‌ها نامیده شود — کلید + نامِ فارسی."""
    k = str(key).lower()
    return (k,) + tuple(a.lower() for a in LEG_ALIASES.get(k, ()))


def _mentions_other_leg(text: str, leg: str, topics: dict) -> "str | None":
    """نامِ پای دیگری در تاپیکِ این پا؟ ⇒ clarify، نه اجرا.

    عمداً clarify و نه deny: مالک احتمالاً منظورِ درستی دارد، فقط جای اشتباه
    نوشته. ولی حدس‌زدنِ اینکه کدام پا را می‌خواهد، همان چیزی است که یک بار
    «مسیریابی به فلگِ خاموش» ساخت.

    هر دو طرف با نامِ فارسی سنجیده می‌شوند: هم پایی که نامش برده شده، هم پایی
    که تاپیک مالِ اوست — وگرنه «نقاشی» در تاپیکِ lead به‌اشتباه بین-پایی
    شمرده می‌شد (بیش‌بست) در حالی که همان پاست."""
    t = str(text or "").lower()
    mine = set(_surface_forms(leg))
    for key in (topics or {}):
        if str(key).lower() == str(leg).lower():
            continue
        for form in _surface_forms(key):
            if not form or form in mine:
                continue          # شکلِ مشترک بینِ دو پا ⇒ مبهم، نه شاهدِ بین-پایی
            if re.search(rf"\b{re.escape(form)}\b", t):
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
