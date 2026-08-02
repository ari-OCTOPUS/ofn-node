#!/usr/bin/env python3
"""input_surface_policy — «این پیام از کجا آمد و اجازهٔ چه دارد؟»

مکملِ `surface_router`، و عمداً جدا از آن: آن یکی می‌گوید خروجی **کجا برود**،
این یکی می‌گوید ورودی **چه اجازه‌ای دارد**.

قراردادِ مرجع: `_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json`
+ TG-UI-CHARTER-2026-07-31 (رأی allow-list ِ گروه).

    outer + DM + مالک            → گفت‌وگوی کامل با کلِ اختاپوس (همه‌چیز مجاز)
    inner + DM + مالک            → سلامت، هشدار، approval، رسید
    outer + گروه + تاپیکِ پا     → فقط همان پا (leg-scoped)
    outer + گروه + system/mirror → core_conversation (اتاقِ آینه/سیستم؛ پا نیست)
    گروه + General/تاپیکِ ناشناخته → deny + redirect به DM
    گروه + هر فرمانِ اسلشی        → deny (فرمانِ اسلشی فقط در DM — لاتین و فارسی)
    گروه + دکمهٔ غیرِ leg-card     → deny («این دکمه فقط در DM کار می‌کند»)
    گروه + کارِ بین-پایی          → clarify (کدام پا؟)
    غیرمالک + هر جهش              → deny

قراردادِ گروه از ۰۷-۳۱ **deny-by-default برای هر چیزِ فرمان‌گونه** است:
اسلش‌کامند (هر خطی)، واژه‌های هسته‌ای، و دکمه‌های خارج از
`GROUP_CALLBACK_VERBS` همه رد می‌شوند. متنِ آزادِ فارسی/سؤال/رسانه/ریپلای در
تاپیکِ پا همچنان مجاز است — آن‌جا میزِ کارِ همان پاست و مدلِ Task به جملهٔ
دلخواه نیاز دارد. فقط ۸ پای قرارداد (`CONTRACT_LEGS`) leg_scoped می‌گیرند؛
system/mirror با اینکه در نگاشتِ تاپیک‌ها هستند، پا نیستند.

دو صداکننده در `center.py`: گیتِ اصلیِ `handle_update` (هر آپدیت، fail-open
روی استثنا) و مسیرِ جایگزینِ callback ِ `oc:` در `_handle_callback`.

$0 · stdlib · تابعِ خالص · صفر I/O · صفر side effect · هرگز raise نمی‌کند.
"""
from __future__ import annotations

import re

MODES = ("core_conversation", "status_approval", "leg_scoped",
         "clarify", "deny")

# ۸ پای قراردادِ ratified شده — فقط این‌ها leg_scoped می‌گیرند. هر کلیدِ دیگری
# در نگاشتِ تاپیک‌ها (system، mirror، …) پا نیست؛ core_conversation می‌گیرد تا
# اتاقِ آینه کار کند ولی صفِ Task ِ پاها آن را نبلعد.
CONTRACT_LEGS = frozenset({
    "lead", "ziman", "mining", "crypto", "accounting",
    "studio_pf", "knowledge", "cartographer",
})

# فرمان‌های هسته‌ای — امروز فقط برای غنی‌کردنِ `reason` (تفکیکِ «هسته‌ای» از
# «اسلشیِ عادی» در تله‌متری). حکمِ deny دیگر به این فهرست بسته نیست: **هر**
# اسلش‌کامندی در گروه رد می‌شود.
CORE_VERBS = frozenset({
    "panic", "stop", "resume", "restart", "halt", "kill", "power",
    "budget", "spend", "pay", "approve", "deny", "verdict",
    "flag", "arm", "disarm", "deploy", "merge", "push",
    "secret", "token", "env", "capabilities", "capability",
    "goal", "goals", "mission", "cycle", "scorecard",
    "discovery", "world", "doctor", "brain", "ask", "chat",
    "memory", "recall", "learn", "improve", "patch", "code",
})

# فعل‌هایی که در گروه، **داخلِ تاپیکِ خودِ پا**، همیشه مجازند — allow-list ِ
# صریح. `is_leg_verb` این‌ها را قبل از قواعدِ سخت‌گیرانه سفید می‌کند، پس هر
# قاعدهٔ deny ِ آینده باید **پایین‌ترِ** آن شاخه اضافه شود وگرنه اثر ندارد —
# و این عمدی است: سخت‌شدنِ آیندهٔ گیت نباید این ۱۲ فعل را بشکند.
LEG_VERBS = frozenset({
    "status", "وضعیت", "blocker", "بلاکر", "next", "قدم",
    "pause", "resume_leg", "outcome", "نتیجه", "lead", "لید",
})

# دکمه‌هایی که مشروعاً در تاپیک‌های گروه زندگی می‌کنند: کارت‌های Task ِ پا +
# کارت‌های تصمیم/approval. هر verb ِ دیگری (pw، pwc، oc، hm، map، …) در گروه
# رد می‌شود — دکمه‌های هسته‌ای فقط در DM.
#
# ۲۰۲۶-۰۸-۰۱ — `mo` (زیر-OSِ Mining) اضافه شد. تحلیلِ امنیتیِ مستقل: تمام
# عملیاتِ `mo:*` یا فقط‌خواندنیِ ناوبری (menu/pane) یا ثبتِ verdict/نیت در
# فایلِ حالتِ ماینینگ‌اند — صفر پول (D-11)، صفر SSH (D-20)، صفر شبکه.
# کم‌ریسک‌تر از `tk` که از قبل مجاز است (tk عملیاتِ mutatingِ بیشتری دارد:
# لغو/شروع/بازخوردِ کار). فعال‌سازی‌اش همچنان پشتِ `OCTOPUS_WIRE_MINING_UI` است.
GROUP_CALLBACK_VERBS = frozenset({
    "tk", "lg", "ok", "no", "later", "ap", "ms", "tr", "dg", "mo",
})

# نامِ مستعارِ لِینِ خواهر (۰۷-۳۱) برای همان ۸ پای قرارداد — یک منبعِ حقیقت.
ALLOWED_LEG_TOPICS = CONTRACT_LEGS

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

# اسلش‌کامند — لاتین **و فارسی**. نسخهٔ ASCII-only سوراخِ «/توان /رفتار» را
# باز می‌گذاشت (gap group-1): فرمانِ فارسی از کنارِ گیت رد می‌شد.
# حرفِ اول می‌تواند رقم هم باشد (/2fa و /1 فرمانِ معتبرِ تلگرام‌اند) — وگرنه
# گیتِ «هیچ اسلشی در گروه» با یک فرمانِ رقم-اول دور می‌خورد (یافتهٔ بازبینِ ۰۷-۳۱).
_CMD = re.compile(r"^\s*/([\w؀-ۿ][\w؀-ۿ]*)")
# (۲۰۲۶-۰۷-۳۱) فرمانِ فارسی هم شناخته شود — تا /وضعیت و /بودجه در گروه گیر کنند.
_CMD_FA = re.compile(r"^\s*/([\u0600-\u06FF][\u0600-\u06FF\s]*)")
# فعلِ callback: pw: pwc: tr: tk: ap: … — با / شروع نمی‌شوند ولی کارِ هسته‌ای‌اند.
_CB_VERB = re.compile(r"^([A-Za-z][A-Za-z0-9_]{0,15}):")
_CORE_WORDS = re.compile(
    r"(کلِ? سیستم|همهٔ? پاها|بودجه|خرج|راز|توکن|ری[‌\s]*استارت|"
    r"خاموش کن|قطع کن|تأیید کن|فلگ|کشفِ? دنیا|دکتر|حافظه)", re.I)

# نرمال‌سازیِ فعلِ پا — همان روحِ leg_commands._norm ولی بدون import (این ماژول
# stdlib ِ خالص می‌ماند): فشرده‌سازیِ فاصله + حذفِ نقطه‌گذاریِ انتهایی.
_TRAIL_PUNCT = re.compile(r"[\s؟?!.…۔]+$")
_WS = re.compile(r"[\s‌]+")


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


def is_leg_verb(text: str) -> bool:
    """آیا متن دقیقاً یکی از ۱۲ فعلِ مجازِ پاست؟ (exact-match، نه زیررشته —
    «وضعیتِ سایتِ مشتری را بررسی کن» فعل نیست، Task است.)"""
    t = _WS.sub(" ", str(text or "")).strip().lower()
    t = _TRAIL_PUNCT.sub("", t)
    return t in LEG_VERBS


def _cb_verb(data: str) -> str:
    """`tk:s:lead:TASK-1` → `tk`. خالی/بدشکل → رشتهٔ خالی."""
    return str(data or "").split(":", 1)[0].strip().lower()


def classify(update: dict, *, bot_role: str, owner_id, group_id,
             topics: dict) -> dict:
    """{allow, mode, leg, redirect, reason}. هر ابهام ⇒ deny یا clarify.

    `update` شکلِ خامِ تلگرام است. `topics` نگاشتِ `{leg_key: topic_id}` از
    center-config. `bot_role` یکی از `outer`/`inner`.

    هیچ‌جا استثنا پرتاب نمی‌شود — ورودیِ خصمانه فقط `deny` می‌گیرد."""
    if not isinstance(update, dict):
        return _deny("bad-update")
    cb = update.get("callback_query")
    cb = cb if isinstance(cb, dict) else None
    raw_msg = update.get("message")
    raw_msg = raw_msg if isinstance(raw_msg, dict) else None
    msg = raw_msg if raw_msg is not None else \
        ((cb or {}).get("message") if isinstance((cb or {}).get("message"), dict) else None)
    if msg is None:
        return _deny("bad-message")
    chat = msg.get("chat") if isinstance(msg.get("chat"), dict) else {}
    frm = (raw_msg if raw_msg is not None else cb or {}).get("from")
    frm = frm if isinstance(frm, dict) else {}
    text = str((raw_msg or {}).get("text") or (cb or {}).get("data") or "")

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
                    and cb is None:
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
    key = _topic_key_of(thread, topics)
    if key is None:
        # General (بدونِ thread) یا تاپیکِ ناشناخته — هر دو یک حکم دارند.
        return {"allow": False, "mode": "deny", "leg": None,
                "redirect": "outer_dm",
                "reason": "group-general-or-unknown-topic"}
    leg = key if key in CONTRACT_LEGS else None

    # ── دکمه‌ها: allow-list ِ سراسریِ گروه ──────────────────────────────────
    # قبلاً callback از کنارِ گیتِ verb رد می‌شد (داده «/» ندارد) و pw:panic از
    # تاپیکِ پا leg_scoped می‌گرفت (gap boundary-2). حالا فقط کارت‌هایی که
    # مشروعاً در گروه زندگی می‌کنند مجازند؛ باقی → «فقط در DM».
    if cb is not None:
        v = _cb_verb(text)
        if v in GROUP_CALLBACK_VERBS:
            if leg is not None:
                return {"allow": True, "mode": "leg_scoped", "leg": leg,
                        "redirect": None, "reason": f"group-callback-{v}-{leg}"}
            return {"allow": True, "mode": "core_conversation", "leg": None,
                    "redirect": None, "reason": f"group-callback-{v}-{key}"}
        return {"allow": False, "mode": "deny", "leg": leg,
                "redirect": "outer_dm",
                "reason": f"callback-dm-only:{v or 'empty'}"}

    # ── متن: اسلش‌کامند در گروه مطلقاً ممنوع — هسته‌ای یا نه، لاتین یا فارسی ─
    verb = _verb_of(text)
    if verb:
        flavor = "core-command" if verb in CORE_VERBS else "slash-command"
        return {"allow": False, "mode": "deny", "leg": leg,
                "redirect": "outer_dm",
                "reason": f"{flavor}-in-group:/{verb}"}

    # ── تاپیکِ شناخته ولی غیرِ پا (system/mirror) → گفت‌وگوی مرکز ──────────
    # نه deny (اتاقِ آینه topic 205 باید کار کند — center روی topic=='mirror'
    # در _handle_ask سوییچ می‌کند) و نه leg_scoped (صفِ Task نباید جمله‌های
    # آینه را ببلعد — center روی mode=='leg_scoped' گیت می‌کند).
    if leg is None:
        return {"allow": True, "mode": "core_conversation", "leg": None,
                "redirect": None, "reason": f"group-non-leg-topic-{key}"}

    other = _mentions_other_leg(text, leg, topics)
    if other:
        return {"allow": False, "mode": "clarify", "leg": leg,
                "redirect": None,
                "reason": f"cross-leg:{other}-mentioned-in-{leg}-topic"}

    # allow-list ِ صریحِ فعل‌های پا — بالاتر از هر قاعدهٔ سخت‌گیرانهٔ متنی، تا
    # سخت‌شدنِ آیندهٔ گیت این ۱۲ فعل را نشکند (boundary-1: LEG_VERBS مصرف‌کننده
    # ندارد → حالا دارد). قاعدهٔ deny ِ جدید = زیرِ این خط.
    if is_leg_verb(text):
        return {"allow": True, "mode": "leg_scoped", "leg": leg,
                "redirect": None, "reason": f"leg-verb-{leg}"}

    if _CORE_WORDS.search(text):
        return {"allow": False, "mode": "deny", "leg": leg,
                "redirect": "outer_dm", "reason": "core-topic-in-group"}

    # پیش‌فرضِ متنِ آزاد در تاپیکِ پا: مجاز. این میزِ کارِ همان پاست — مدلِ
    # Task جملهٔ دلخواهِ فارسی/سؤال/رسانه/ریپلای می‌خواهد؛ deny-by-default فقط
    # برای چیزهای فرمان‌گونه است (اسلش/دکمه/واژهٔ هسته‌ای) که بالاتر رد شدند.
    return {"allow": True, "mode": "leg_scoped", "leg": leg,
            "redirect": None, "reason": f"group-topic-{leg}"}


def _topic_key_of(thread_id, topics: dict) -> "str | None":
    """تاپیک → کلیدِ config. General (thread=None) و ناشناخته هر دو `None`."""
    if thread_id is None or not isinstance(topics, dict):
        return None
    for key, tid in topics.items():
        try:
            if int(tid) == int(thread_id):
                # کلیدِ خام برمی‌گردد (system/mirror هم) — فیلترِ «پا بودن»
                # کارِ _leg_of است؛ این‌جا فقط نگاشتِ تاپیک→کلید است.
                return str(key)
        except (TypeError, ValueError):
            continue
    return None


def _leg_of(thread_id, topics: dict) -> "str | None":
    """تاپیک → کلیدِ **پا**. فقط ۸ پای قرارداد؛ system/mirror پا نیستند."""
    key = _topic_key_of(thread_id, topics)
    return key if key in CONTRACT_LEGS else None


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
    if reason.startswith("callback-dm-only"):
        return "این دکمه فقط در DM کار می‌کند."
    if r == "outer_dm":
        if "core-command" in reason or "core-topic" in reason \
                or "slash-command" in reason:
            return ("این‌جا فقط دربارهٔ همین پا حرف می‌زنیم. برای کارِ هسته‌ای "
                    "در چتِ خصوصی بنویس.")
        return ("این تاپیک به هیچ پایی وصل نیست. برای گفت‌وگوی عمومی چتِ خصوصی."
                )
    if (decision or {}).get("mode") == "clarify":
        return "کدام پا را می‌گویی؟ در تاپیکِ خودش بنویس تا context درست باشد."
    return ""
