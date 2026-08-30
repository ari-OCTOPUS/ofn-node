#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_card.py — کارتِ لیدی که **مردِ روی نردبان** می‌تواند با یک دست به آن عمل کند.

دلیلِ وجود (گزارشِ WHY-NO-REAL-LEADS-2026-08-01، ردیف‌های ۱۱/۱۲/۱۴):
  · ردیف ۱۱ — کارتِ امروزی (`lead_scorer.ScoredLead.card`, خطوطِ ۲۰۸-۲۲۰) **نه تلفن
    دارد، نه ایمیل، نه نامِ مشتری**؛ کلیدِ `contact` هرگز خوانده نمی‌شود. مالک روی
    نردبان کارتی می‌گیرد که نمی‌گوید به کی زنگ بزند.
  · ردیف ۱۲ — کارت **ویرایش** می‌شود و ویرایشِ تلگرام notification نمی‌دهد.
  · ردیف ۱۴ — بدترین تأخیرِ اندازه‌گیری‌شده تا لحظهٔ دیدنِ چیزی: ۳ ساعت و ۴۵ دقیقه.

این ماژول فقط **می‌سازد و می‌فرستد**؛ هرگز چیزی به مشتری نمی‌رود:

  ⛔ نامتغیرِ سخت: هیچ دکمه‌ای که این ماژول تولید می‌کند نمی‌تواند ارسالی را ماشه بکشد.
     transport ِ خروجی روی این ماشین **مسلح** است (`OCTOPUS_WIRE_LEAD_OUTBOUND=1`،
     `OCTOPUS_SMTP_USE_GMAIL=1` در هر چهار snapshot). یک دکمهٔ send روی چنین ماشینی
     یک لغزشِ انگشت با یک غریبه فاصله دارد. تصمیمِ ارسال مالِ قوسِ جداگانه و گیت‌شدهٔ
     `lead_effect_gate.authorize → outbound_worker` است، نه این کارت.
     `SAFE_VERBS` تنها فعل‌هایی است که تولید می‌شود و `has_send_button()` گاردِ آن.

  ⛔ هرگز دکمهٔ مرده: `keyboard()` بدونِ اعلامِ صریحِ `verbs_ready` (فهرستِ فعل‌هایی که
     dispatcher ِ بالادست **واقعاً** مسیریابی می‌کند) `None` می‌دهد — همان الگویِ
     صادقانهٔ `lead_pipeline._ready_keyboard`.

  ⛔ flag پیش‌فرض خاموش: `OCTOPUS_WIRE_LEAD_CARD_CONTACT`. خاموش ⇒ `enabled()=False`
     و صداکنندهٔ تولیدی (`lead_scorer.ScoredLead.card`) به بدنهٔ **دست‌نخوردهٔ** خودش
     برمی‌گردد؛ خروجی بایت‌به‌بایت همان امروز است. این فلگ عمداً در `PAPER_FULL_FLAGS`
     نیست — غیابش یعنی واقعاً خاموش، نه روشنِ ضمنی.

bidi (زخمِ ثبت‌شدهٔ این مخزن، منشور UX-۹): هر تکهٔ LTR — تلفن، ایمیل، `tel:`،
شناسهٔ لید — داخلِ ایزولهٔ ‏U+2066…U+2069 می‌رود وگرنه در متنِ فارسی وارونه دیده
می‌شود. رقمِ فارسی فقط برای عددهای **متن** (امتیاز/شمارش)؛ شمارهٔ تلفن ASCII می‌ماند
چون رقمِ فارسی نه قابلِ شماره‌گیری است نه توسطِ تلگرام linkify می‌شود.

stdlib-only؛ صفر شبکه؛ صفر I/O ِ نوشتنی؛ صفر خرج.
"""
from __future__ import annotations

import os
import re

FLAG = "OCTOPUS_WIRE_LEAD_CARD_CONTACT"

# جریانِ مسیریابی — همان «lead» که `approval_channel._STREAM_TOPIC` می‌شناسد.
# نامِ تازه نمی‌سازیم: جریانِ ناشناخته یعنی مسیرِ ناشناخته.
STREAM = "lead"

# تحویل همیشه **پیامِ نو** است، هرگز ویرایش (ردیف ۱۲: ویرایش notification نمی‌دهد).
DELIVERY_NEW_MESSAGE = "new_message"

# تنها فعل‌هایی که این ماژول تولید می‌کند. هیچ‌کدام ارسالی را ماشه نمی‌کشد:
#   lcall  → نمایشِ بلوکِ تماس به‌صورتِ پیامِ نو (تا شماره در گوشی قابلِ لمس شود)
#   ldraft → نمایشِ پیش‌نویسِ پاسخِ اول برای **مرور** (فقط render، صفر transport)
SAFE_VERBS = frozenset({"lcall", "ldraft"})

# فعل‌هایی که در این مخزن می‌توانند به اثرِ بیرونی برسند (prop/qt از راهِ
# live_loop→_fire_lead_effect_hook؛ بقیه اسم‌های آشکارِ ارسال). این فهرست
# **سیاهه** است نه سفیده: گاردِ نهایی `SAFE_VERBS` است، این فقط تشخیص را بلندتر می‌کند.
FORBIDDEN_VERBS = frozenset({
    "prop", "qt", "send", "email", "mail", "smtp", "out", "outbound",
    "dispatch", "deliver", "fire", "authorize", "authz", "arm", "approve",
})
# نشانه‌های متنیِ ارسال روی برچسبِ دکمه (فارسی و انگلیسی).
FORBIDDEN_TEXT_MARKS = ("بفرست", "ارسال", "send", "email", "ایمیل کن")

_LRI, _PDI = "⁦", "⁩"
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

_RE_NON_DIGIT = re.compile(r"[^0-9+]")
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def enabled() -> bool:
    """flag خاموش (پیش‌فرض) = این ماژول هیچ اثری روی سطحِ زنده ندارد."""
    return os.environ.get(FLAG, "0") == "1"


# ── کمکی‌های نمایش ──────────────────────────────────────────────────────────────
def _esc(s) -> str:
    """گریزِ HTML — کانالِ تلگرام با parse_mode=HTML می‌فرستد؛ `<` ِ خام پیام را می‌شکند."""
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _ltr(s) -> str:
    """تکهٔ LTR داخلِ متنِ فارسی — بدونِ ایزوله `+61412…` وارونه دیده می‌شود."""
    return _LRI + str(s if s is not None else "") + _PDI


def _fa(n) -> str:
    """رقمِ فارسی برای عددهای متن (امتیاز/شمارش). هرگز برای تلفن یا شناسه."""
    return "؟" if n is None else str(n).translate(_FA_DIGITS)


# ── تماس ────────────────────────────────────────────────────────────────────────
def contact_of(lead) -> dict:
    """اطلاعاتِ تماس از **هر** شکلی که در این مخزن وجود دارد، بدونِ حدس.

    سه شکلِ واقعی: `lead['candidate']['contact']` (فایلِ inbox که
    `lead_candidate_inbox._to_lead_sense_file` می‌نویسد)، `lead['contact']`
    (چیزی که `lead_research`/`outbound_worker` می‌خوانند) و کلیدهای top-level
    (`applicant`, `email`, `phone`). ترتیب: عمیق‌ترین برنده است.

    خروجی همیشه dict با کلیدهای name/email/phone (رشته، شاید خالی).
    """
    d = lead if isinstance(lead, dict) else {}
    cand = d.get("candidate") if isinstance(d.get("candidate"), dict) else {}
    deep = cand.get("contact") if isinstance(cand.get("contact"), dict) else {}
    flat = d.get("contact") if isinstance(d.get("contact"), dict) else {}

    def pick(*keys) -> str:
        for holder in (deep, flat, d):
            for k in keys:
                v = holder.get(k)
                if v is not None and str(v).strip():
                    return str(v).strip()
        return ""

    return {
        "name": pick("name", "organisation", "applicant"),
        "email": pick("email"),
        "phone": pick("phone", "mobile", "tel"),
    }


def tel_uri(phone) -> "str | None":
    """شمارهٔ خام → `tel:` ِ E.164 ِ استرالیا. غیرقابلِ نرمال‌سازی ⇒ None (نه حدس).

    ۰۴۱۲ ۳۴۵ ۶۷۸ / (02) 9876 5432 / +61 412 345 678 / 61412345678 همه پوشش دارند.
    خروجی ASCII می‌ماند — رقمِ فارسی نه شماره‌گیری می‌شود نه linkify.
    """
    raw = _RE_NON_DIGIT.sub("", str(phone or ""))
    if not raw:
        return None
    plus = raw.startswith("+")
    digits = raw.lstrip("+")
    if not digits.isdigit():
        return None
    if plus:
        return "tel:+" + digits if 8 <= len(digits) <= 15 else None
    if digits.startswith("61") and len(digits) in (11, 12):
        return "tel:+" + digits
    if digits.startswith("0") and len(digits) == 10:
        return "tel:+61" + digits[1:]
    if len(digits) in (8, 9):            # شمارهٔ محلیِ بدونِ کد — بدونِ حدسِ ایالت نه
        return None
    return None


def _pretty_phone(uri: str) -> str:
    """`tel:+61412345678` → `+61 412 345 678` (فقط برای چشم؛ URI دست‌نخورده می‌ماند)."""
    n = uri.replace("tel:", "")
    if n.startswith("+61") and len(n) == 12:
        return f"{n[:3]} {n[3:6]} {n[6:9]} {n[9:]}"
    return n


def _valid_email(addr) -> "str | None":
    a = str(addr or "").strip()
    return a if _RE_EMAIL.match(a) else None


# ── دکمه‌ها ─────────────────────────────────────────────────────────────────────
def has_send_button(kb) -> bool:
    """گاردِ نامتغیرِ سخت: آیا این صفحه‌کلید دکمه‌ای دارد که بتواند ارسالی را ماشه بکشد؟

    True یعنی این کارت **نباید** برود. عمداً بدبینانه: هر فعلِ خارج از `SAFE_VERBS`،
    هر عضوِ `FORBIDDEN_VERBS`، هر برچسبِ حاویِ نشانِ ارسال، و هر دکمهٔ `url` (که
    می‌تواند به هر مقصدی برود) مثبت شمرده می‌شود.
    """
    if not isinstance(kb, dict):
        return False
    for row in kb.get("inline_keyboard") or []:
        for btn in row or []:
            if not isinstance(btn, dict):
                continue
            if btn.get("url") or btn.get("web_app") or btn.get("switch_inline_query"):
                return True
            label = str(btn.get("text") or "").lower()
            if any(m.lower() in label for m in FORBIDDEN_TEXT_MARKS):
                return True
            cb = str(btn.get("callback_data") or "")
            verb = cb.split(":", 1)[0].strip().lower()
            if not verb:
                continue
            if verb in FORBIDDEN_VERBS or verb not in SAFE_VERBS:
                return True
    return False


def keyboard(lead_id, *, verbs_ready=None, has_phone: bool = False,
             has_draft: bool = False) -> "dict | None":
    """📞 و 📤 — و هیچ دکمهٔ دیگری. هیچ‌کدام ارسال نمی‌کند.

    `verbs_ready`: فهرست/مجموعهٔ فعل‌هایی که dispatcher ِ بالادست **واقعاً** مسیریابی
    می‌کند. غایب یا تهی ⇒ `None` (کارتِ بی‌دکمه). این تنها راهِ نداشتنِ دکمهٔ مرده است:
    این ماژول نمی‌تواند بداند center چه چیزی route می‌کند، پس ادعایش نمی‌کند.
    """
    lid = str(lead_id or "").strip()
    ready = {str(v).strip().lower() for v in (verbs_ready or ())} & SAFE_VERBS
    if not lid or not ready:
        return None
    row = []
    if "lcall" in ready and has_phone:
        row.append({"text": "📞 زنگ بزن", "callback_data": f"lcall:{lid}"})
    if "ldraft" in ready and has_draft:
        row.append({"text": "📤 پیش‌نویسِ پاسخ", "callback_data": f"ldraft:{lid}"})
    if not row:
        return None
    kb = {"inline_keyboard": [row]}
    if has_send_button(kb):     # کمربند و بند شلوار: هرگز نباید برسد
        return None
    return kb


# ── متنِ کارت ───────────────────────────────────────────────────────────────────
def _header(lead: dict, scored) -> str:
    src = _esc(str(lead.get("source") or "lead"))
    score = getattr(scored, "score", None)
    action = str(getattr(scored, "action", "") or "")
    emoji = {"draft": "🟢", "save": "🟡", "skip": "⚪️"}.get(action, "🎨")
    tail = f" | امتیاز {_fa(score)}" if score is not None else ""
    return f"{emoji} <b>لیدِ تازه</b> — {_ltr(src)}{tail}"


def _contact_block(c: dict) -> tuple:
    """(خطوط، missing، uri). هرگز شکافِ خالی — نبودِ تماس **صریح** اعلام می‌شود."""
    lines, missing = [], []
    name = str(c.get("name") or "").strip()
    if name:
        lines.append(f"👤 <b>{_esc(name)}</b>")
    else:
        missing.append("نام")

    uri = tel_uri(c.get("phone"))
    if uri:
        # شماره ASCII و داخلِ ایزوله — هم برای چشم، هم برای linkify ِ تلگرام.
        lines.append(f"📞 {_ltr(_esc(_pretty_phone(uri)))}")
        lines.append(f"   {_ltr(_esc(uri))}")
    else:
        missing.append("تلفن")

    email = _valid_email(c.get("email"))
    if email:
        lines.append(f"✉️ {_ltr(_esc(email))}")
    else:
        missing.append("ایمیل")
    return lines, missing, uri


def render(lead, *, scored=None, lead_id=None, first_reply=None,
           verbs_ready=None) -> dict:
    """کارتِ کاملِ لید. همیشه dict؛ هرگز استثنا؛ **هرگز ارسالِ خروجی**.

    خروجی:
      {ok, text, keyboard, delivery, edit_message_id, stream,
       tel_uri, has_contact, missing, contact}

    `delivery` همیشه `"new_message"` و `edit_message_id` همیشه `None` — ردیف ۱۲:
    ویرایشِ تلگرام هیچ notification ای نمی‌دهد، پس کارتِ ویرایش‌شده = کارتِ نادیده.
    """
    L = lead if isinstance(lead, dict) else {}
    c = contact_of(L)
    lines = [_header(L, scored), "──────────"]

    cl, missing, uri = _contact_block(c)
    lines.extend(cl)
    has_contact = bool(uri or _valid_email(c.get("email")))
    if not has_contact:
        lines.append("⚠️ <b>اطلاعات تماس ندارد</b> — نه تلفنِ قابلِ شماره‌گیری، "
                     "نه ایمیلِ معتبر. از این کارت نمی‌شود تماس گرفت؛ اول تماس را "
                     "از منبعِ لید بردار.")
    elif missing:
        lines.append("⚠️ ناقص: " + "، ".join(missing) + " ندارد.")

    scope = str(L.get("description") or "").strip()
    if scope:
        lines.append(f"📝 «{_esc(scope[:400])}»")     # به زبانِ خودِ مشتری
    suburb = str(L.get("suburb") or L.get("address") or "").strip()
    if suburb:
        lines.append(f"📍 {_esc(suburb[:120])}")

    reasons = list(getattr(scored, "reasons", None) or [])
    if reasons:
        lines.append("🧠 " + _esc("; ".join(str(r) for r in reasons))[:300])

    lid = str(lead_id or L.get("lead_id") or "").strip()
    if lid:
        lines.append(f"🆔 <code>{_ltr(_esc(lid))}</code>")

    draft_body = ""
    if isinstance(first_reply, dict):
        draft_body = str(first_reply.get("body") or "").strip()

    kb = keyboard(lid, verbs_ready=verbs_ready,
                  has_phone=bool(uri), has_draft=bool(draft_body))
    return {
        "ok": True,
        "text": "\n".join(lines),
        "keyboard": kb,
        "delivery": DELIVERY_NEW_MESSAGE,
        "edit_message_id": None,
        "stream": STREAM,
        "tel_uri": uri,
        "has_contact": has_contact,
        "missing": missing,
        "contact": c,
    }


def card_text(lead, *, scored=None, lead_id=None) -> str:
    """فقط متن — نقطهٔ ورودِ صداکنندهٔ تولیدی (`lead_scorer.ScoredLead.card`).

    دکمه نمی‌دهد چون آن مسیر جای دکمه ندارد؛ صفحه‌کلید کارِ `render()` است.
    """
    try:
        return str(render(lead, scored=scored, lead_id=lead_id).get("text") or "")
    except Exception:      # noqa: BLE001 — کارت هرگز beat را نمی‌کشد
        return ""


def draft_review_text(first_reply, *, lead_id=None) -> str:
    """چیزی که دکمهٔ 📤 نشان می‌دهد: بدنهٔ پیش‌نویسِ پاسخِ اول، **فقط برای مرور**.

    ردیف ۱۵ ِ گزارش: این پیش‌نویس امروز روی دیسک نوشته می‌شود و هیچ سطحی نشانش
    نمی‌دهد. این تابع آن سطح است — و هیچ transport ای صدا نمی‌زند.
    """
    fr = first_reply if isinstance(first_reply, dict) else {}
    body = str(fr.get("body") or "").strip()
    if not body:
        return "📤 پیش‌نویسی برای این لید وجود ندارد."
    head = ["📤 <b>پیش‌نویسِ پاسخِ اول</b> — فقط مرور؛ این کارت چیزی نمی‌فرستد."]
    subj = str(fr.get("subject") or "").strip()
    if subj:
        head.append(f"موضوع: {_ltr(_esc(subj[:160]))}")
    lid = str(lead_id or fr.get("lead_id") or "").strip()
    if lid:
        head.append(f"🆔 <code>{_ltr(_esc(lid))}</code>")
    head.append("──────────")
    head.append(_esc(body[:2500]))
    return "\n".join(head)


# ── تحویل ───────────────────────────────────────────────────────────────────────
def deliver(send_fn, payload, *, edit_fn=None) -> dict:
    """کارت را به‌صورتِ **پیامِ نو** می‌فرستد. `edit_fn` را هرگز صدا نمی‌زند.

    ردیف ۱۲: کارتِ ویرایش‌شده در تلگرام هیچ صدایی نمی‌دهد؛ مردی روی نردبان هرگز
    نمی‌فهمد لیدی آمده. پس `edit_fn` فقط پذیرفته می‌شود تا صداکننده مجبور نباشد
    امضایش را عوض کند — و عمداً بی‌استفاده می‌ماند (`edits` همیشه ۰).

    گاردِ نهایی: اگر صفحه‌کلید حتی یک دکمهٔ ارسال‌پذیر داشته باشد، **بدونِ دکمه**
    می‌رود؛ نه کارت را قربانی می‌کنیم نه ریسکِ ارسال را می‌پذیریم.
    """
    p = payload if isinstance(payload, dict) else {}
    text = str(p.get("text") or "")
    if not callable(send_fn) or not text:
        return {"sent": False, "edits": 0, "delivery": DELIVERY_NEW_MESSAGE,
                "reason": "no_channel" if not callable(send_fn) else "empty_text"}
    kb = p.get("keyboard")
    dropped = False
    if has_send_button(kb):
        kb, dropped = None, True
    try:
        ok = bool(send_fn(text, keyboard=kb, stream=p.get("stream") or STREAM))
    except Exception:  # noqa: BLE001 — کانالِ خراب هرگز beat را نمی‌کشد
        return {"sent": False, "edits": 0, "delivery": DELIVERY_NEW_MESSAGE,
                "reason": "channel_error"}
    return {"sent": ok, "edits": 0, "delivery": DELIVERY_NEW_MESSAGE,
            "dropped_unsafe_keyboard": dropped}
