#!/usr/bin/env python3
"""lead_email_intake.py — تولیدکنندهٔ گمشدهٔ سرِ لولهٔ لید: صندوقِ ایمیل → submit_candidate.

چرا این فایل هست (ممیزیِ ۱۱-ایجنتیِ ۲۰۲۶-۰۸-۰۱): کلِ ماشینِ لید مسلح بود — pipeline هر
تیک می‌دوید، draft مسلح، candidate-inbox مسلح — و **صفر پروپوزالِ تحویل‌شده** در تمامِ
عمرش داشت. علت نه فلگِ خاموش بود نه باگ: هر نویسندهٔ `state/legs/lead-inbox/`
انسان‌ماشه بود. هیچ producer ای وجود نداشت. این ماژول آن producer است.

قرارداد (از کد خوانده شده، نه حدس):
  · تنها درِ ورود = `lead_candidate_inbox.submit_candidate(candidate, source_id)`.
  · `source.channel` باید در `_VALID_CHANNELS` باشد؛ `request.scope_text` غیرخالی.
  · `consent_firewall` از **کانال** طبقه‌بندی می‌کند و fail-closed است: کانالِ ناشناخته
    → market_signal (سخت‌گیرترین، هرگز outreach). پس کانال را **صادقانه** انتخاب می‌کنیم:
    فقط اعلانِ واقعیِ فرمِ سایت → `website_form`؛ هر چیزِ دیگر → `other` و بگذار دیوار
    سخت‌گیر باشد. هرگز کانال را برای بازکردنِ outreach دروغ نمی‌گوییم.

سه قیدِ طراحی که از خودِ قابلیت مهم‌ترند:
  ۱. **transport تزریق‌شدنی**: `beat(fetch_fn=...)`. پیش‌فرض یک خوانندهٔ واقعیِ IMAP از env
     می‌سازد؛ تست‌ها لیستِ پیامِ ساختگی می‌دهند و **هرگز سوکتی باز نمی‌شود**. `imaplib`
     عمداً importِ تنبل داخلِ تابع است تا این ساختاراً اثبات‌پذیر باشد.
  ۲. **صندوق فقط‌خواندنی**: `select(..., readonly=True)` (یعنی EXAMINE، نه SELECT) به‌علاوهٔ
     `BODY.PEEK[]`. دو لایه تا سرور هرگز `\\Seen` نگذارد. نتیجه: نامهٔ نخواندهٔ مالک نخوانده
     می‌ماند. هزینهٔ این انتخاب: نمی‌توانیم از `\\Seen` به‌عنوانِ نشانِ «پردازش‌شده» استفاده
     کنیم، پس dedup را خودمان نگه می‌داریم (بند ۳). این معامله عمدی است: عوارضِ دیدنی روی
     صندوقِ شخصیِ مالک، چیزی است که او نخواسته.
  ۳. **idempotent با کلیدِ هش‌شده**: زخمِ ثبت‌شدهٔ این ریپو «Message-ID به‌عنوانِ نامِ فایل»
     است (`<`, `>`, `@`, `/`، طولِ نامحدود → نامِ فایلِ خراب/تصادم). پس Message-Id هرگز خام
     ذخیره/نوشته نمی‌شود؛ کلید = `sha256(message_id نرمال‌شده)[:24]` و بدونِ Message-Id
     هشِ محتوایی. همین هش هم به‌عنوانِ `source.external_id` پایین‌دست می‌رود تا idempotency
     ِ خودِ inbox لایهٔ دوم شود.

حریمِ خصوصی (مالک عمداً IMAP ِ کلِ صندوق را انتخاب کرد — دسترسیِ وسیع ≠ پردازشِ وسیع):
  · اول طبقه‌بندی. پیامِ غیرِ استعلام **هیچ ردی** نمی‌گذارد: نه فایل، نه خطِ لاگ، نه ردیفِ
    حافظه، نه کلیدِ dedup. حتی subject ش هم جایی نمی‌نشیند.
  · بدنهٔ ایمیل هرگز log نمی‌شود. آدرسِ کامل هرگز در لاگ/خطا/شمارنده نمی‌نشیند.
  · تنها خروجیِ پایدار = رکوردِ کاندید برای پیام‌هایی که **واقعاً** استعلام‌اند.
  · credential فقط از env خوانده می‌شود (`GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD`) و هرگز
    چاپ/ذخیره/برگردانده نمی‌شود — فقط PRESENT/ABSENT.

فلگ‌ها (هر دو پیش‌فرض خاموش؛ خاموش = بایت‌به‌بایتِ امروز):
  · `OCTOPUS_WIRE_LEAD_EMAIL_INTAKE=1` — خودِ ضربان.
  · `OCTOPUS_IMAP_USE_GMAIL=1` — اجازهٔ اتصالِ واقعی به صندوقِ **شخصیِ** مالک. هم‌الگوی
    `mail_credentials.OCTOPUS_SMTP_USE_GMAIL`: برداشتنِ صندوقِ شخصی باید رأیِ عمدی باشد،
    نه عارضهٔ اینکه کلیدها اتفاقاً در `.env` بودند. بدونِ آن ضربان صادقانه `not_armed`
    گزارش می‌دهد (با نامِ دقیقِ متغیر در سایدکار) — نه سکوت.

هرگز نمی‌فرستد، حذف نمی‌کند، جابه‌جا نمی‌کند، خرج نمی‌کند. stdlib-only. fail-soft مطلق.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib   # noqa: E402

FLAG = "OCTOPUS_WIRE_LEAD_EMAIL_INTAKE"
IMAP_ARM_FLAG = "OCTOPUS_IMAP_USE_GMAIL"
DOWNSTREAM_FLAG = "OCTOPUS_WIRE_LEAD_CANDIDATES"     # فلگِ خودِ submit_candidate
# مرزِ رضایت، نه یک قابلیت — عمداً فلگِ مستقل تا مسلح‌کردنِ لوله خودبه‌خود
# پهنش نکند. رأیِ مالک ۲۰۲۶-۰۸-۰۱؛ پیش‌فرض همچنان خاموش.
INBOUND_CONSENT_FLAG = "OCTOPUS_LEAD_EMAIL_INBOUND_CONSENT"

ADDR_ENV = "GMAIL_ADDRESS"
SECRET_ENV = "GMAIL_APP_PASSWORD"                     # فقط **نام** — مقدار هرگز اینجا نمی‌آید
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

SOURCE_ID = "email_intake"
MAX_PER_BEAT_DEFAULT = 25
SINCE_DAYS_DEFAULT = 3
SEEN_TTL_DAYS = 180          # کلیدِ dedup پس از این هرس می‌شود (لایهٔ دائمی در خودِ inbox است)
SCOPE_MAX = 600

_TRUTHY = {"1", "true", "yes", "on"}


def enabled() -> bool:
    """فلگ خاموش (پیش‌فرض) = no-opِ مطلق."""
    return os.environ.get(FLAG, "0") == "1"


def inbound_consent() -> bool:
    """آیا «ایمیلِ مستقیمِ مشتری» رضایتِ صریح حساب می‌شود؟ — رأیِ مالک، خاموشِ پیش‌فرض.

    این تنها فلگی در کلِ لوله است که **مرزِ رضایت** را جابه‌جا می‌کند، نه یک
    قابلیت را. پس عمداً از فلگِ اصلیِ لوله جداست: مالک می‌تواند لوله را مسلح
    کند و این را نه (لیدها ثبت شوند، پاسخِ خودکار نه).
    """
    return os.environ.get(INBOUND_CONSENT_FLAG) == "1"


def imap_armed() -> bool:
    """آیا مالک صریحاً اجازهٔ اتصالِ واقعی به صندوقِ شخصی‌اش را داده؟"""
    return str(os.environ.get(IMAP_ARM_FLAG, "")).strip().lower() in _TRUTHY


def credentials_present() -> bool:
    """فقط بولین — هرگز مقدار."""
    return bool(str(os.environ.get(ADDR_ENV, "") or "").strip()) and \
        bool(str(os.environ.get(SECRET_ENV, "") or "").strip())


# ── مسیرهای state (call-time تا OPS_DIR ِ تستی اثر کند) ─────────────────────────
def _state_dir() -> Path:
    return opslib.STATE_DIR / "legs" / "email-intake"


def _seen_path() -> Path:
    return _state_dir() / "seen.json"


# ── نرمال‌سازیِ پیام ─────────────────────────────────────────────────────────────
_TAG_RE = re.compile(r"<[^>]{1,400}>", re.S)
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_ADDR_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}")


def _strip_html(text: str) -> str:
    t = _TAG_RE.sub(" ", text or "")
    for ent, rep in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                     ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(ent, rep)
    return _WS_RE.sub(" ", t)


def _addr_of(raw: str) -> str:
    """آدرسِ خامِ داخلِ «Name <a@b>» را بیرون بکش (خالی اگر نبود)."""
    m = _ADDR_RE.search(str(raw or ""))
    return m.group(0).lower() if m else ""


def mask_address(addr: str) -> str:
    """«ab***@domain» — هیچ آدرسِ کاملی هرگز در گزارش/خطا نمی‌نشیند."""
    a = str(addr or "").strip()
    local, _, dom = a.partition("@")
    if not dom:
        return "***"
    return (local[:2] + "***@" + dom) if local else ("***@" + dom)


def normalize(msg: dict) -> dict:
    """شکلِ canonical ِ درونی. هرگز چیزی از این dict لاگ نمی‌شود."""
    m = msg if isinstance(msg, dict) else {}
    headers = {str(k).lower(): str(v) for k, v in (m.get("headers") or {}).items()
               if isinstance(m.get("headers"), dict)}
    body = str(m.get("body") or m.get("text") or "")
    if "<" in body and ">" in body:
        body = _strip_html(body)
    return {
        "message_id": str(m.get("message_id") or headers.get("message-id") or "").strip(),
        "from": str(m.get("from") or headers.get("from") or "").strip(),
        "to": str(m.get("to") or headers.get("to") or "").strip(),
        "reply_to": str(m.get("reply_to") or headers.get("reply-to") or "").strip(),
        "subject": str(m.get("subject") or headers.get("subject") or "").strip(),
        "date": str(m.get("date") or headers.get("date") or "").strip(),
        "body": body,
        "headers": headers,
    }


# ── طبقه‌بندی (محافظه‌کارانه، قطعی، بدونِ LLM، بدونِ شبکه) ─────────────────────────
# اصل: استعلامِ ازدست‌رفته = یک لید. مثبتِ کاذب = یک غریبه در لوله‌ای که می‌تواند به او
# ایمیل بزند. پس هر شکِ کوچک ⇒ رد.

_BULK_HEADERS = ("list-unsubscribe", "list-id", "list-post", "x-campaign-id",
                 "x-mailer-campaign", "feedback-id", "x-auto-response-suppress")
_AUTO_PRECEDENCE = ("bulk", "list", "junk", "auto_reply", "auto-reply")

_NOREPLY_LOCALS = ("no-reply", "noreply", "no_reply", "donotreply", "do-not-reply",
                   "mailer-daemon", "postmaster", "bounce", "bounces", "notifications",
                   "notification", "alerts", "alert", "statements", "statement",
                   "newsletter", "news", "marketing", "billing", "accounts",
                   "support", "info-noreply", "automated", "auto")

# نشانه‌های بازاریابی/خبرنامه در متن (هر کدام = رد)
_MARKETING_MARKS = ("unsubscribe", "view in browser", "view this email in",
                    "manage preferences", "email preferences", "opt out", "opt-out",
                    "% off", "shop now", "limited time offer", "terms and conditions apply",
                    "you are receiving this", "this is an automated", "do not reply to this",
                    "verification code", "one-time passcode", "otp", "password reset",
                    "your statement", "e-statement", "transaction alert", "direct debit",
                    "bsb", "account balance", "available balance")

# خانوادهٔ ۱: خدمت (باید حداقل یکی باشد)
_SERVICE_TERMS = ("paint", "painting", "painter", "repaint", "re-paint", "undercoat",
                  "primer", "render", "rendering", "plaster", "gyprock", "skirting",
                  "cornice", "feature wall", "colour consult", "color consult",
                  "نقاشی", "رنگ‌آمیزی", "رنگ آمیزی", "نقاش")

# خانوادهٔ ۲: قصد (باید حداقل یکی باشد — مستقل از خانوادهٔ ۱)
_INTENT_TERMS = ("quote", "quotation", "estimate", "how much", "price", "pricing",
                 "cost", "book", "booking", "availability", "available", "interested",
                 "enquiry", "enquiries", "inquiry", "looking for", "need a", "need some",
                 "can you", "could you", "when can", "get back to me", "give me a call",
                 "site visit", "measure up", "job", "quote request",
                 "قیمت", "استعلام", "هزینه")


def _form_senders() -> tuple:
    """آدرس/دامنهٔ اعلان‌گرِ فرمِ سایت — فقط از env، پیش‌فرض خالی.

    خالی = هیچ پیامی website_form نمی‌شود. این عمدی است: ادعای «فرمِ سایت» تنها چیزی است
    که می‌تواند outreach را باز کند، پس فقط با اعلامِ صریحِ مالک."""
    raw = str(os.environ.get("OCTOPUS_LEAD_FORM_SENDERS", "") or "")
    return tuple(x.strip().lower() for x in raw.split(",") if x.strip())


def _owner_addresses() -> tuple:
    own = _addr_of(os.environ.get(ADDR_ENV, ""))
    extra = str(os.environ.get("OCTOPUS_LEAD_OWNER_ADDRESSES", "") or "")
    out = [own] if own else []
    out += [x.strip().lower() for x in extra.split(",") if x.strip()]
    return tuple(out)


def _is_form_notifier(sender: str) -> bool:
    if not sender:
        return False
    for pat in _form_senders():
        if not pat:
            continue
        if sender == pat or (pat.startswith("@") and sender.endswith(pat)) or \
                (("@" not in pat) and sender.endswith("@" + pat)):
            return True
    return False


def classify(msg: dict) -> dict:
    """{is_inquiry, channel, reason} — `reason` یک **کُد** است، هرگز محتوای پیام.

    کانال: `website_form` فقط برای اعلانِ واقعیِ فرمِ سایت (allowlist ِ مالک)؛ هر چیزِ
    دیگر `other` تا دیوارِ رضایت سخت‌گیر بماند (→ market_signal، هرگز outreach)."""
    try:
        m = normalize(msg)
        h = m["headers"]
        sender = _addr_of(m["reply_to"]) or _addr_of(m["from"])
        from_addr = _addr_of(m["from"])
        form = _is_form_notifier(from_addr)

        # ۱) خودکار/انبوه — خبرنامه، اعلانِ بانک، رسیدِ سیستمی. (اعلان‌گرِ فرم مستثناست:
        #    خودش ماشینی است ولی allowlist ِ صریحِ مالک آن را تأیید کرده.)
        if not form:
            for hk in _BULK_HEADERS:
                if h.get(hk):
                    return {"is_inquiry": False, "channel": None, "reason": "bulk_header"}
            prec = str(h.get("precedence") or "").strip().lower()
            if prec in _AUTO_PRECEDENCE:
                return {"is_inquiry": False, "channel": None, "reason": "bulk_precedence"}
            auto = str(h.get("auto-submitted") or "").strip().lower()
            if auto and auto != "no":
                return {"is_inquiry": False, "channel": None, "reason": "auto_submitted"}
            local = from_addr.split("@")[0] if "@" in from_addr else ""
            if any(local == n or local.startswith(n + ".") or local.startswith(n + "-")
                   or local.endswith("-" + n) for n in _NOREPLY_LOCALS):
                return {"is_inquiry": False, "channel": None, "reason": "noreply_sender"}

        # ۲) نامهٔ خودِ مالک به خودش (یادداشت/ارسالی) — لید نیست.
        if from_addr and from_addr in _owner_addresses():
            return {"is_inquiry": False, "channel": None, "reason": "self_mail"}

        text = (m["subject"] + " \n " + m["body"]).lower()

        # ۳) نشانه‌های بازاریابی/بانکی در متن (حتی اگر هدرِ انبوه نداشت).
        if not form and any(mark in text for mark in _MARKETING_MARKS):
            return {"is_inquiry": False, "channel": None, "reason": "marketing_marks"}

        # ۴) دو خانوادهٔ مستقلِ نشانه — هر دو الزامی.
        if not any(t in text for t in _SERVICE_TERMS):
            return {"is_inquiry": False, "channel": None, "reason": "no_service_term"}
        if not any(t in text for t in _INTENT_TERMS):
            return {"is_inquiry": False, "channel": None, "reason": "no_intent_term"}

        # ۵) دستگیرهٔ پاسخ لازم است (وگرنه لیدِ غیرقابلِ پیگیری).
        contact_email = sender or _addr_of(m["body"])
        if not contact_email:
            return {"is_inquiry": False, "channel": None, "reason": "no_reply_handle"}

        if form:
            return {"is_inquiry": True, "channel": "website_form", "reason": "form_notifier"}
        # این «فرمِ سایت» نیست. پیش‌فرض `other` است و دیوار سخت‌گیر می‌ماند.
        #
        # ۲۰۲۶-۰۸-۰۱ — با رأیِ صریحِ مالک و **فقط** پشتِ فلگِ خاموشِ
        # `INBOUND_CONSENT_FLAG`: پیامی که تا این خط رسیده از هر شش گارد رد
        # شده (نه انبوه، نه خودکار، نه noreply، نه نامهٔ خودِ مالک، نه نشانهٔ
        # بازاریابی، و هم واژهٔ خدمت هم واژهٔ قصد هم دستگیرهٔ پاسخ). یعنی یک
        # آدمِ واقعی که **خودش** به آدرسِ کسب‌وکار نوشته و کاری می‌خواهد —
        # روشن‌ترین حالتِ رضایت. کانالِ `email_inbound` سقفِ
        # `consented_inbound` دارد و پاسخِ اول می‌تواند تولید شود.
        #
        # فلگ خاموش = دقیقاً رفتارِ دیروز (`other` → market_signal → لید ثبت
        # می‌شود، پاسخِ خودکار نه). هیچ مسیرِ دیگری این کانال را نمی‌سازد.
        if inbound_consent():
            return {"is_inquiry": True, "channel": "email_inbound",
                    "reason": "human_inquiry_consented"}
        return {"is_inquiry": True, "channel": "other", "reason": "human_inquiry"}
    except Exception:  # noqa: BLE001 — هر ابهام ⇒ رد (fail-closed به‌سمتِ سکوت)
        return {"is_inquiry": False, "channel": None, "reason": "classify_error"}


# ── dedup (کلیدِ هش‌شده — Message-Id هرگز خام ذخیره نمی‌شود) ─────────────────────
def dedup_key(msg: dict) -> str:
    """کلیدِ idempotency. زخمِ «Message-ID به‌عنوانِ نامِ فایل»: خامش نه امن است نه
    filename-safe. پس همیشه hex ِ ۲۴ نویسه‌ای — امن برای نامِ فایل، ثابت‌طول، و
    خودش هیچ PII ای فاش نمی‌کند."""
    m = normalize(msg)
    mid = m["message_id"].strip().strip("<>").lower()
    if mid:
        basis = "mid:" + mid
    else:
        basis = "body:" + "|".join((_addr_of(m["from"]), m["date"], m["subject"],
                                    m["body"][:2000]))
    return hashlib.sha256(basis.encode("utf-8", "replace")).hexdigest()[:24]


def _load_seen() -> dict:
    try:
        d = json.loads(_seen_path().read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_seen(idx: dict) -> None:
    try:
        p = _seen_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except (OSError, TypeError, ValueError):
        pass   # fail-soft: dedupِ ضعیف‌تر (لایهٔ دومِ inbox دائمی است)، نه کرش


def _prune(idx: dict) -> dict:
    """کلیدهای کهنه‌تر از TTL را بینداز — رشدِ نامحدودِ فایلِ حالت ممنوع."""
    try:
        import datetime as _dt
        cutoff = (_dt.date.today() - _dt.timedelta(days=SEEN_TTL_DAYS)).isoformat()
        return {k: v for k, v in idx.items() if str(v)[:10] >= cutoff}
    except Exception:  # noqa: BLE001
        return idx


# ── نگاشت به قراردادِ کاندید ────────────────────────────────────────────────────
_FORM_NAME_KEYS = ("name", "full name", "your name", "first name", "نام")
_FORM_MSG_KEYS = ("message", "comments", "comment", "enquiry", "inquiry",
                  "details", "description", "how can we help", "پیام")
# برچسب‌های فرم که هرگز بخشی از «خواستهٔ مشتری» نیستند — فراداده‌اند.
_FORM_META_KEYS = ("name", "full name", "your name", "first name", "email",
                   "e-mail", "phone", "mobile", "telephone", "suburb",
                   "postcode", "address", "subject", "نام", "ایمیل", "تلفن")


def _message_from_form_body(body: str) -> str:
    """فیلدِ پیامِ فرم — نه کلِ بدنه.

    بدونِ این، `scope_text` کلِ اعلانِ خام می‌شد و پاسخِ اول عیناً نقلش می‌کرد:
    «Name: Sam Jones Email: Phone: Suburb: Carlingford Message: …». دقیقاً همان
    لحنِ ماشینی که نقلِ‌قول قرار بود از آن فرار کند. همچنین لیدِ ثبت‌شده هم
    تمیزتر می‌شود، چون `scope_text` دیگر فراداده‌های فرم را حمل نمی‌کند.

    اگر فیلدِ پیام پیدا نشد → رشتهٔ خالی و caller به بدنهٔ کامل برمی‌گردد
    (هیچ اطلاعاتی از دست نمی‌رود؛ فقط زیباتر نمی‌شود).
    """
    lines = str(body or "").splitlines()
    for i, line in enumerate(lines[:60]):
        label, sep, value = line.partition(":")
        if not sep or label.strip().lower() not in _FORM_MSG_KEYS:
            continue
        parts = [value.strip()]
        for nxt in lines[i + 1:]:          # پیامِ چندخطی تا برچسبِ بعدی ادامه دارد
            lab2, sep2, _ = nxt.partition(":")
            if sep2 and lab2.strip().lower() in _FORM_META_KEYS + _FORM_MSG_KEYS:
                break
            parts.append(nxt.strip())
        out = " ".join(p for p in parts if p).strip()
        if out:
            return out
    return ""


def _name_from_form_body(body: str) -> str:
    """نامِ مشتری از **بدنهٔ** اعلانِ فرم — چون پاکت نامِ خودِ سایت را دارد.

    الگوی رایجِ همهٔ فرم‌سازها: هر فیلد یک خطِ `<برچسب>: <مقدار>`. فقط برچسب‌های
    نامِ شناخته‌شده خوانده می‌شوند؛ هر چیزِ دیگر نادیده. نبودِ نام مشکلی نیست —
    قالبِ پاسخ حالتِ بی‌نام را خودش دارد و «سلامِ بی‌نام» بی‌نهایت بهتر از
    «Hi Website» است.
    """
    for line in str(body or "").splitlines()[:40]:
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        if label.strip().lower() not in _FORM_NAME_KEYS:
            continue
        v = value.strip().strip('"').strip()
        # یک نام است، نه یک جمله؛ و هرگز چیزی که خودش آدرس باشد.
        if v and "@" not in v and len(v) <= 60 and len(v.split()) <= 4:
            return v
    return ""


# ── واقعیت‌های ملک: suburb/geo/متراژ/سطح/زمان‌بندی ───────────────────────────────
# چرا (گزارشِ ۲۰۲۶-۰۸-۰۱، دلایلِ ۸ و ۱۰ — یک زخم با دو صورت):
#   · `to_candidate` همیشه `"property": {}` می‌نوشت. پس `_to_lead_sense_file`
#     همیشه `address=None, suburb=None` می‌داد، و lat/lng هرگز وجود نداشت. آن
#     +۸ امتیازِ geo ساختاراً دست‌نیافتنی بود: repaint ِ مسکونی ۶۸ می‌گرفت در
#     برابرِ آستانهٔ ۷۰ ⇒ `save` ⇒ برای همیشه پارک، بی‌کارت و بی‌سؤال.
#   · قراردادِ کاندید هیچ فیلدی برای متراژ نداشت ⇒ `lead_quote` همیشه
#     `size_m2=0.0` ⇒ کوتِ A$0.00 ⇒ گاردِ قیمتِ خودِ سیستم ایمیل را رد می‌کرد.
#
# قیدِ صداقت (مهم‌تر از خودِ قابلیت): **عددِ حدس‌زده هرگز نباید بی‌صدا قیمتِ قطعی
# شود.** پس دو مکانیزمِ مستقل، نه یکی:
#   ۱ کلیدهای جدا: `floor_area_m2_stated` فقط وقتی مشتری **خودش** عدد داده.
#     مصرف‌کننده‌ای که فقط آن کلید را بخواند، ساختاراً نمی‌تواند به حدس برسد.
#   ۲ پرچمِ صریح: `area_is_assumption` + `area_basis` + `area_confidence` +
#     `area_*_range_m2` + `assumptions[]` با جملهٔ آمادهٔ hedge برای متنِ کوت.
# و هیچ‌جا کلیدی به نامِ `size_m2` نوشته نمی‌شود، تا هیچ مصرف‌کننده‌ای تصادفاً
# متراژِ **کف** را به‌جای متراژِ **سطحِ رنگ‌شونده** برندارد (خطای ~۳ برابری = دقیقاً
# همان‌جایی که یک نقاش روی کار ضرر می‌کند).
#
# فلگ پیش‌فرض خاموش؛ خاموش = `property: {}` و `urgency: "unknown"` — بایت‌به‌بایتِ امروز.
PROPERTY_FLAG = "OCTOPUS_LEAD_PROPERTY_EXTRACT"

EXTRACTOR_ID = "lead_email_intake.extract_property/v1"
PROPERTY_TEXT_MAX = 8000        # سقفِ متنِ اسکن‌شونده (regex روی بدنهٔ غول نرود)

# جدولِ ثابتِ NSW — بدونِ شبکه، بدونِ API key، بدونِ کلید. مختصات = مرکزِ تقریبیِ
# حومه (دقتِ ~۱km؛ برای سنجهٔ شعاعِ ۴۰km ِ scorer بیش از کافی است).
# دامنه: منطقهٔ سرویسِ واقعیِ مالک (Carlingford/Hills/Parramatta/Ryde) + همسایه‌ها.
_SUBURBS: dict = {
    # ── هستهٔ سرویس ────────────────────────────────────────────────────────
    "carlingford": ("2118", -33.7772, 151.0513),
    "epping": ("2121", -33.7726, 151.0817),
    "north epping": ("2121", -33.7597, 151.0937),
    "eastwood": ("2122", -33.7900, 151.0819),
    "marsfield": ("2122", -33.7789, 151.1027),
    "parramatta": ("2150", -33.8150, 151.0000),
    "north parramatta": ("2151", -33.7960, 151.0030),
    "harris park": ("2150", -33.8250, 151.0060),
    "castle hill": ("2154", -33.7320, 151.0050),
    "baulkham hills": ("2153", -33.7620, 150.9920),
    "bella vista": ("2153", -33.7360, 150.9440),
    "winston hills": ("2153", -33.7770, 150.9740),
    "norwest": ("2153", -33.7300, 150.9600),
    # ── همسایه‌ها (شمال‌غرب/Hills) ──────────────────────────────────────────
    "west pennant hills": ("2125", -33.7480, 151.0330),
    "pennant hills": ("2120", -33.7400, 151.0720),
    "thornleigh": ("2120", -33.7310, 151.0800),
    "cherrybrook": ("2126", -33.7230, 151.0450),
    "beecroft": ("2119", -33.7500, 151.0640),
    "normanhurst": ("2076", -33.7250, 151.0980),
    "wahroonga": ("2076", -33.7180, 151.1150),
    "hornsby": ("2077", -33.7030, 151.0990),
    "waitara": ("2077", -33.7090, 151.1030),
    "kellyville": ("2155", -33.7100, 150.9600),
    "beaumont hills": ("2155", -33.7010, 150.9330),
    "rouse hill": ("2155", -33.6870, 150.9160),
    "glenhaven": ("2156", -33.7100, 151.0000),
    "dural": ("2158", -33.6870, 151.0250),
    "kenthurst": ("2156", -33.6580, 151.0060),
    # ── همسایه‌ها (Parramatta/Ryde) ─────────────────────────────────────────
    "northmead": ("2152", -33.7860, 150.9930),
    "westmead": ("2145", -33.8030, 150.9880),
    "wentworthville": ("2145", -33.8070, 150.9720),
    "girraween": ("2145", -33.8020, 150.9490),
    "toongabbie": ("2146", -33.7880, 150.9520),
    "seven hills": ("2147", -33.7740, 150.9370),
    "kings langley": ("2147", -33.7480, 150.9330),
    "blacktown": ("2148", -33.7690, 150.9060),
    "merrylands": ("2160", -33.8360, 150.9890),
    "granville": ("2142", -33.8330, 151.0110),
    "rosehill": ("2142", -33.8236, 151.0230),
    "oatlands": ("2117", -33.7910, 151.0230),
    "dundas": ("2117", -33.7960, 151.0350),
    "dundas valley": ("2117", -33.7860, 151.0450),
    "telopea": ("2117", -33.7920, 151.0330),
    "rydalmere": ("2116", -33.8130, 151.0290),
    "ermington": ("2115", -33.8130, 151.0530),
    "west ryde": ("2114", -33.8069, 151.0900),
    "denistone": ("2114", -33.7975, 151.0766),
    "meadowbank": ("2114", -33.8181, 151.0900),
    "melrose park": ("2114", -33.8180, 151.0680),
    "ryde": ("2112", -33.8148, 151.1050),
    "north ryde": ("2113", -33.7940, 151.1290),
    "macquarie park": ("2113", -33.7770, 151.1230),
    "putney": ("2112", -33.8290, 151.1090),
    "gladesville": ("2111", -33.8330, 151.1300),
    # ── لبهٔ شعاع (هنوز داخلِ ۴۰km ولی دورتر) ───────────────────────────────
    "chatswood": ("2067", -33.7960, 151.1800),
    "turramurra": ("2074", -33.7330, 151.1290),
    "pymble": ("2073", -33.7440, 151.1430),
    "st ives": ("2075", -33.7300, 151.1620),
    # ⚠️ «Sydney/2000» عمداً در جدول **نیست**: در امضای هر ایمیلِ سیدنی‌ای هست و
    # مرکزِ شعاعِ خودِ scorer هم همان است — یعنی یک امضای معمولی می‌توانست +۸ امتیازِ
    # جغرافیاییِ کاذب بسازد. حومهٔ واقعی باید از خودِ **جمله** بیاید.
}

# کدپستی → مختصات (میانگینِ حومه‌های هم‌کد). فقط برای وقتی که کد آمده ولی نامِ
# حومه شناخته نشده. ساخته می‌شود، هاردکد نیست — پس همیشه با جدولِ بالا هم‌خوان است.
def _build_postcode_geo() -> dict:
    acc: dict = {}
    for pc, lat, lng in _SUBURBS.values():
        acc.setdefault(pc, []).append((lat, lng))
    return {pc: (round(sum(a for a, _ in v) / len(v), 4),
                 round(sum(b for _, b in v) / len(v), 4)) for pc, v in acc.items()}


_POSTCODE_GEO: dict = _build_postcode_geo()

# طولانی‌ترین نام اول: «north epping» قبل از «epping»، «castle hill» قبل از «hill».
_SUBURB_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in
                      sorted(_SUBURBS, key=len, reverse=True)) + r")\b", re.I)
# کدپستی **فقط با لنگرِ صریح**. یک ۴رقمیِ لخت هرگز کدپستی حساب نمی‌شود: «Aug 2026»
# و «budget around 2000» هر دو ۴رقمی‌اند و هر دو می‌توانستند یک +۸ ِ جغرافیاییِ کاذب
# بسازند. عددِ بی‌برچسب شاهد نیست.
_NSW_PC_RE = re.compile(r"\bn\.?\s?s\.?\s?w\.?[\s,]*(\d{4})\b", re.I)
_PC_LABEL_RE = re.compile(
    r"\b(?:post\s?code|postal\s?code|p/?code|zip)\s*[:\-]?\s*(\d{4})\b", re.I)

_STREET_TYPES = ("street", "st", "road", "rd", "avenue", "ave", "drive", "dr",
                 "place", "pl", "court", "ct", "crescent", "cres", "close", "cl",
                 "parade", "pde", "lane", "way", "terrace", "tce", "circuit",
                 "boulevard", "bvd", "grove", "highway", "hwy")
_ADDRESS_RE = re.compile(
    r"\b(\d{1,4}[a-z]?(?:\s*[/-]\s*\d{1,4}[a-z]?)?)\s+"
    r"([A-Za-z][A-Za-z'\-]{2,20}(?:\s+[A-Za-z][A-Za-z'\-]{1,20}){0,2})\s+"
    r"(" + "|".join(_STREET_TYPES) + r")\b\.?", re.I)
# «3 bed terrace» یک نشانی نیست ولی الگوی بالا آن را می‌گرفت («terrace» نوعِ خیابان
# هم هست). هر واژهٔ میانیِ این فهرست ⇒ رد.
_NOT_STREET_WORDS = frozenset((
    "bed", "beds", "bedroom", "bedrooms", "bath", "bathroom", "bathrooms",
    "room", "rooms", "coat", "coats", "car", "cars", "hour", "hours",
    "day", "days", "week", "weeks", "month", "months", "year", "years",
    "sqm", "m2", "storey", "storeys", "story", "stories", "level", "levels",
    "unit", "units", "door", "doors", "window", "windows", "wall", "walls",
) + _STREET_TYPES)

# متراژِ اعلام‌شدهٔ خودِ مشتری. `(?<![$\d.])` تا «$45 sqm» (نرخ) متراژ حساب نشود.
_M2_RE = re.compile(
    r"(?<![$\d.])(\d{1,5}(?:\.\d{1,2})?)\s*(?:m2\b|m²|sqm\b|sq\.?\s?m\b|"
    r"square\s+met(?:re|er)s?\b)", re.I)
_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
_BED_DIGIT_RE = re.compile(r"\b(\d{1,2})\s*[-\s]?\s*(?:bed(?:room)?s?|b\.?r\.?)\b", re.I)
_BED_WORD_RE = re.compile(
    r"\b(" + "|".join(_WORD_NUM) + r")[\s-]+bed(?:room)?s?\b", re.I)
_ROOM_DIGIT_RE = re.compile(r"\b(\d{1,2})\s*[-\s]?\s*rooms?\b", re.I)
_ROOM_WORD_RE = re.compile(r"\b(" + "|".join(_WORD_NUM) + r")[\s-]+rooms?\b", re.I)

def _phrase_re(words) -> "re.Pattern":
    """الگویِ «کلمهٔ کامل» — زیررشتهٔ خام فاجعه می‌سازد: `"unit" in "community"`
    و `"flat" in "flatten"` هر دو True‌اند و نوعِ ملک را بی‌صدا غلط می‌کنند."""
    return re.compile(r"\b(?:" + "|".join(re.escape(w) for w in words) + r")\b", re.I)


# نوعِ ملک — ترتیب مهم است (خاص قبل از عام؛ «granny flat» قبل از «flat»).
_PROPERTY_TYPES = tuple((name, _phrase_re(words)) for name, words in (
    ("commercial", ("office", "offices", "shop", "shops", "retail", "warehouse",
                    "factory", "commercial", "restaurant", "cafe", "showroom",
                    "tenancy", "premises")),
    ("strata", ("strata", "owners corporation", "common property", "body corporate")),
    ("granny_flat", ("granny flat", "secondary dwelling")),
    ("townhouse", ("townhouse", "townhouses", "town house", "terrace house")),
    ("duplex", ("duplex", "semi-detached", "semi detached")),
    ("villa", ("villa", "villas")),
    ("apartment", ("apartment", "apartments", "unit", "units", "flat", "flats",
                   "studio")),
    ("house", ("house", "home", "cottage", "dwelling", "bungalow", "property")),
))
_INTERIOR_RE = _phrase_re((
    "interior", "internal", "inside", "indoor", "indoors", "living room",
    "lounge", "bedroom", "bedrooms", "kitchen", "hallway", "ceiling",
    "ceilings", "skirting", "skirtings", "cornice", "cornices", "architrave"))
_EXTERIOR_RE = _phrase_re((
    "exterior", "external", "outside", "outdoor", "outdoors", "facade",
    "façade", "weatherboard", "weatherboards", "render", "rendered",
    "rendering", "eaves", "fascia", "gutter", "gutters", "fence", "fences",
    "fencing", "deck", "decking", "roof", "verandah", "veranda", "pergola",
    "balcony", "balconies", "balustrade", "garage door", "carport"))
# ترتیب عمداً asap → flexible → soon: وقتی مشتری هم «no rush» گفته و هم یک
# ماهِ هدف، محافظه‌کارانه‌ترین خوانش برنده است. ادعای فوریتِ کاذب یعنی مالک
# کارِ اشتباه را جلو می‌اندازد.
_TIMING = tuple((label, _phrase_re(words)) for label, words in (
    ("asap", ("asap", "as soon as possible", "urgent", "urgently",
              "immediately", "straight away", "right away", "this week",
              "این هفته", "فوری")),
    ("flexible", ("no rush", "no hurry", "flexible", "whenever suits",
                  "sometime", "not in a hurry", "no particular rush")),
    ("soon", ("next week", "next month", "in a few weeks", "couple of weeks",
              "within a month", "before christmas", "before we move in",
              "settlement", "moving in")),
))

# ── متراژِ کفِ تیپیک (m²) بر حسبِ تعدادِ اتاق‌خواب — (lo, hi) ─────────────────────
# مبنا: ابعادِ متعارفِ مسکنِ سیدنی (خانهٔ ۳خوابهٔ موجود ~۱۱۰–۱۷۵ m² کف؛ آپارتمانِ
# ۲خوابه ~۷۰–۱۰۰ m²). این‌ها **بازه**‌اند نه عدد؛ هرکس خواست تنظیمشان کند فقط این
# جدول را عوض می‌کند و هر رکوردِ تولیدشده `area_basis` را حمل می‌کند تا قابلِ ممیزی بماند.
_FLOOR_BY_BEDROOMS_HOUSE = {0: (40.0, 60.0), 1: (55.0, 85.0), 2: (85.0, 125.0),
                            3: (110.0, 175.0), 4: (160.0, 240.0),
                            5: (210.0, 310.0), 6: (260.0, 380.0)}
_FLOOR_BY_BEDROOMS_UNIT = {0: (35.0, 50.0), 1: (50.0, 70.0), 2: (70.0, 100.0),
                           3: (95.0, 135.0), 4: (125.0, 175.0)}
_UNIT_TYPES = ("apartment", "granny_flat", "villa")
# اتاقِ عامِ بی‌تفکیک (وقتی فقط «۵ اتاق» گفته‌اند) — بازهٔ عمداً پهن‌تر.
_FLOOR_PER_ROOM = (14.0, 25.0)
# ضریبِ سطحِ رنگ‌شونده ÷ متراژِ کف. داخلی = دیوار+سقف+قرنیز با سقفِ ~۲.۴m؛
# خارجی = دیوارِ بیرونی+زیرشیروانی+فاسیا؛ both = جمعِ دو. **همیشه** مشتق است،
# هرگز اعلام‌شدهٔ مشتری.
# 🔧 نقطهٔ کالیبراسیونِ مالک: تنها کوتِ دستیِ خودش روی دیسک
# (state/legs/lead-drafts/LEAD-REV.json) با `size_m2=200` داخلی بسته شده
# (A$5,060–9,240). اگر عادتِ قیمت‌گذاریِ او متراژِ کوچک‌تری است، **این جدول** را
# پایین بیاور — نه پرچمِ assumption را. هر رکورد `paint_area_multiplier` را حمل
# می‌کند تا این تنظیم بعداً قابلِ ممیزی باشد.
_PAINT_MULT = {"interior": (2.5, 3.4), "exterior": (0.9, 1.5), "both": (3.4, 4.9)}
# نوع‌هایی که ضریبِ مسکونی برایشان بی‌معناست ⇒ اصلاً سطحِ رنگ‌شونده تولید نکن.
_NO_PAINT_DERIVE = ("commercial", "strata")


def property_extract_on() -> bool:
    """استخراجِ واقعیت‌های ملک — پیش‌فرض خاموش؛ خاموش = `property: {}` مثلِ امروز."""
    return str(os.environ.get(PROPERTY_FLAG, "")).strip().lower() in _TRUTHY


def _find_suburb(text: str) -> tuple:
    """(نامِ حومه، کدپستی، lat، lng) — یا چهار None.

    چند اسمِ حومه در یک متن عادی است («Epping Road, Macquarie Park»، و بدتر:
    بلوکِ امضا). امتیازِ قطعی: لنگرِ زبانی («in …»، «Suburb: …») > هم‌جواری با
    کدپستیِ خودش > نامِ بلندتر، منهای جریمهٔ **موقعیت** (هرچه دیرتر در متن،
    ضعیف‌تر) — چون حومهٔ واقعی در جملهٔ مشتری است و امضا آخرِ نامه."""
    best = None
    best_score = -1.0
    span = float(max(len(text), 1))
    for m in _SUBURB_RE.finditer(text):
        name = m.group(1).lower()
        pc, lat, lng = _SUBURBS[name]
        score = float(len(name)) / 100.0          # tie-break: نامِ بلندتر برنده
        tail = text[m.end():m.end() + 14]
        if pc in tail:
            score += 3.0                          # «Carlingford NSW 2118»
        head = text[max(0, m.start() - 18):m.start()].lower()
        if any(k in head for k in ("suburb:", "suburb :", "address:", " in ",
                                   " at ", "located in", "property in")):
            score += 2.5
        # «12 Epping Road, Macquarie Park NSW 2113» — «Epping» این‌جا نامِ
        # **خیابان** است نه حومه. بدونِ این جریمه، لنگرِ « at » آن را برندهٔ
        # حومهٔ واقعی می‌کرد و لید ~۱۰km آن‌طرف‌تر مختصات می‌گرفت.
        # فقط فاصلهٔ تکیِ بی‌نقطه: «I live in Epping. Road access…» خیابان نیست.
        if tail[:1] == " " and tail[1:].split(" ")[0].lower().strip(",.") \
                in _STREET_TYPES:
            score -= 4.0
        score -= (m.start() / span)               # امضا آخرِ نامه است، نه خواسته
        if score > best_score:
            best_score, best = score, (name, pc, lat, lng)
    if best:
        return best
    # نامِ حومه نبود — فقط کدپستیِ **برچسب‌دار** («NSW 2118» یا «Postcode: 2118»).
    m = _NSW_PC_RE.search(text) or _PC_LABEL_RE.search(text)
    pc = m.group(1) if m else ""
    if pc and not ("2000" <= pc <= "2999"):
        pc = ""                                   # خارج از NSW ⇒ شاهد نیست
    if pc:
        geo = _POSTCODE_GEO.get(pc)
        return (None, pc, geo[0], geo[1]) if geo else (None, pc, None, None)
    return (None, None, None, None)


def _find_count(text: str) -> tuple:
    """(bedrooms|None, rooms|None) — رقم و حرف، هر دو."""
    beds = rooms = None
    m = _BED_DIGIT_RE.search(text) or None
    if m:
        beds = int(m.group(1))
    else:
        m = _BED_WORD_RE.search(text)
        if m:
            beds = _WORD_NUM[m.group(1).lower()]
    if beds is None and re.search(r"\bstudio\b", text, re.I):
        beds = 0
    m = _ROOM_DIGIT_RE.search(text) or _ROOM_WORD_RE.search(text)
    if m:
        raw = m.group(1)
        rooms = int(raw) if raw.isdigit() else _WORD_NUM[raw.lower()]
    if beds is not None and not (0 <= beds <= 12):
        beds = None
    if rooms is not None and not (1 <= rooms <= 40):
        rooms = None
    return beds, rooms


def _mid(lo: float, hi: float) -> float:
    return round((lo + hi) / 2.0, 1)


def _infer_area(text: str, ptype: str, surfaces: str) -> dict:
    """متراژ. **هرگز عددِ خالی نمی‌سازد**: اگر هیچ نشانه‌ای نبود، dict خالی برمی‌گردد.

    خروجی (کلیدها فقط وقتی معنا دارند حاضرند):
      · `floor_area_m2_stated` — فقط و فقط وقتی مشتری خودش عدد داده.
      · `floor_area_m2` + `floor_area_range_m2` — عددِ کاری (اعلام‌شده یا حدس).
      · `area_basis` ∈ {stated_m2, assumed_from_bedrooms, assumed_from_room_count}
      · `area_is_assumption` — True هر وقت `area_basis != "stated_m2"`.
      · `paint_area_m2` + `paint_area_range_m2` + `paint_area_is_derived=True`
        — سطحِ رنگ‌شونده؛ **همیشه** مشتق (کف × ضریب)، حتی وقتی کف اعلام‌شده بود.
      · `assumptions` — جملهٔ آمادهٔ hedge برای متنِ کوت.
    """
    out: dict = {}
    assumptions: list = []
    beds, rooms = _find_count(text)
    if beds is not None:
        out["bedrooms"] = beds
    if rooms is not None:
        out["room_count"] = rooms

    m = _M2_RE.search(text)
    floor_lo = floor_hi = floor = None
    if m:
        try:
            val = float(m.group(1))
        except ValueError:
            val = 0.0
        if 5.0 <= val <= 5000.0:                 # عددِ بی‌معنا = انگار نگفته
            floor = round(val, 1)
            floor_lo = floor_hi = floor
            out["floor_area_m2_stated"] = floor   # ← تنها کلیدی که هرگز حدس نیست
            out["area_basis"] = "stated_m2"
            out["area_is_assumption"] = False
            out["area_confidence"] = 0.9
    if floor is None and beds is not None:
        tbl = _FLOOR_BY_BEDROOMS_UNIT if ptype in _UNIT_TYPES else _FLOOR_BY_BEDROOMS_HOUSE
        rng = tbl.get(beds)
        if rng:
            floor_lo, floor_hi = rng
            floor = _mid(*rng)
            out["area_basis"] = "assumed_from_bedrooms"
            out["area_is_assumption"] = True
            out["area_confidence"] = 0.5 if ptype else 0.4
            assumptions.append({
                "field": "floor_area_m2", "value": floor,
                "range": [floor_lo, floor_hi], "basis": "assumed_from_bedrooms",
                "confidence": out["area_confidence"],
                "note": (f"Floor area was not stated. Assuming about {floor:.0f} m2 "
                         f"(typical range {floor_lo:.0f} to {floor_hi:.0f} m2) for a "
                         f"{beds}-bedroom {(ptype or 'property').replace('_', ' ')}, "
                         f"to be confirmed at the site visit."),
            })
    if floor is None and rooms is not None:
        floor_lo = round(rooms * _FLOOR_PER_ROOM[0], 1)
        floor_hi = round(rooms * _FLOOR_PER_ROOM[1], 1)
        floor = _mid(floor_lo, floor_hi)
        out["area_basis"] = "assumed_from_room_count"
        out["area_is_assumption"] = True
        out["area_confidence"] = 0.35
        assumptions.append({
            "field": "floor_area_m2", "value": floor,
            "range": [floor_lo, floor_hi], "basis": "assumed_from_room_count",
            "confidence": 0.35,
            "note": (f"Floor area was not stated. Assuming about {floor:.0f} m2 "
                     f"(range {floor_lo:.0f} to {floor_hi:.0f} m2) from "
                     f"{rooms} rooms, to be confirmed at the site visit."),
        })
    if floor is None:
        # هیچ نشانه‌ای نبود ⇒ **هیچ عددی**. تهی، نه صفر، نه پیش‌فرض.
        if assumptions:
            out["assumptions"] = assumptions
        return out

    out["floor_area_m2"] = floor
    out["floor_area_range_m2"] = [floor_lo, floor_hi]
    out["area_unit"] = "floor_m2"

    # ⚠️ برای انبار/دفتر/common-property، نسبتِ «سطحِ رنگ‌شونده ÷ کف» اصلاً پایدار
    # نیست (سقفِ ۶ متری، پلانِ باز، صفر پارتیشن). یک ضریبِ مسکونی روی ۴۰۰ m² انبار
    # عددی می‌سازد که می‌تواند چند برابر غلط باشد. پس این‌جا **عمداً هیچ عددی
    # نمی‌سازیم** و همین «نساختن» را به‌عنوان یک assumption ثبت می‌کنیم تا
    # پایین‌دست بداند باید بپرسد، نه اینکه سکوت را صفر بخواند.
    if ptype in _NO_PAINT_DERIVE:
        out["paint_area_unavailable_reason"] = "not_inferable_for_" + ptype
        assumptions.append({
            "field": "paint_area_m2", "value": None, "range": None,
            "basis": "refused_" + ptype, "confidence": 0.0,
            "note": ("Paintable surface cannot be estimated from floor area for a "
                     f"{ptype.replace('_', ' ')} site (ceiling height and layout vary "
                     "too much). It must be measured on site before any price."),
        })
        out["assumptions"] = assumptions
        return out

    mult = _PAINT_MULT.get(surfaces or "interior", _PAINT_MULT["interior"])
    p_lo = round(floor_lo * mult[0], 1)
    p_hi = round(floor_hi * mult[1], 1)
    out["paint_area_m2"] = _mid(p_lo, p_hi)
    out["paint_area_range_m2"] = [p_lo, p_hi]
    out["paint_area_is_derived"] = True           # همیشه — هرگز حرفِ خودِ مشتری
    out["paint_area_multiplier"] = list(mult)
    assumptions.append({
        "field": "paint_area_m2", "value": out["paint_area_m2"],
        "range": [p_lo, p_hi], "basis": "derived_from_floor_area",
        "confidence": round(float(out.get("area_confidence", 0.4)) * 0.9, 2),
        "note": (f"Paintable surface is estimated at about "
                 f"{out['paint_area_m2']:.0f} m2 (range {p_lo:.0f} to {p_hi:.0f} m2), "
                 f"derived from floor area for {surfaces or 'interior'} work. "
                 f"Measured on site before any firm price."),
    })
    out["assumptions"] = assumptions
    return out


def extract_property(text: str) -> dict:
    """متنِ استعلام → واقعیت‌های ملک. تابعِ **خالص**: بی‌I/O، بی‌شبکه، بی‌env.

    هیچ نشانه‌ای پیدا نشد ⇒ `{}` (تهی، نه عددِ غلط). هر خطا ⇒ `{}` (fail-soft:
    یک استعلامِ عجیب نباید خودِ لید را بکشد)."""
    try:
        raw = str(text or "")[:PROPERTY_TEXT_MAX]
        if not raw.strip():
            return {}
        low = raw.lower()
        out: dict = {}

        suburb, pc, lat, lng = _find_suburb(raw)
        if suburb:
            out["suburb"] = suburb.title()
        if pc:
            out["postcode"] = pc
        if suburb or pc:
            out["state"] = "NSW"
        if lat is not None and lng is not None:
            out["lat"] = lat
            out["lng"] = lng
            out["geo_source"] = "static_nsw_table"

        street = ""
        for m in _ADDRESS_RE.finditer(raw):
            words = [w.lower().strip(".,") for w in m.group(2).split()]
            if any(w in _NOT_STREET_WORDS for w in words):
                continue                          # «3 bed terrace» نشانی نیست
            street = " ".join(m.group(0).split()).strip(" .,")
            break
        # ⚠️ locality فقط وقتی ساخته می‌شود که واقعاً حومه/کدپستی پیدا شده باشد.
        # وگرنه «NSW» ِ تنها به‌عنوانِ نشانی می‌نشست — یعنی استعلامِ بی‌مکان یک
        # مکانِ ساختگی می‌گرفت. تهی، نه حدس.
        locality = " ".join(x for x in (out.get("suburb"), "NSW" if pc or suburb
                                        else "", pc) if x)
        if street and locality:
            out["address"] = f"{street}, {locality}"
        elif street or locality:
            out["address"] = street or locality
        if street:
            out["street_address_found"] = True

        ptype = ""
        for name, rx in _PROPERTY_TYPES:
            if rx.search(low):
                ptype = name
                break
        if ptype:
            out["property_type"] = ptype

        inside = bool(_INTERIOR_RE.search(low))
        outside = bool(_EXTERIOR_RE.search(low))
        surfaces = ("both" if inside and outside else
                    "exterior" if outside else "interior" if inside else "")
        if surfaces:
            out["surfaces"] = surfaces

        for label, rx in _TIMING:
            if rx.search(low):
                out["timing"] = label
                break

        out.update(_infer_area(low, ptype, surfaces))
        if out:
            out["extracted_by"] = EXTRACTOR_ID
        return out
    except Exception:  # noqa: BLE001 — استخراج هرگز نباید جذبِ لید را بکشد
        return {}


def _classify_hearing_optout(msg: dict) -> dict:
    """`classify` + شنیدنِ opt-out پیش از آن. fail-soft: اگر ماژولِ suppression
    نبود یا ترکید، دقیقاً `classify` ِ امروز اجرا می‌شود.

    چرا رَپِر و نه فراخوانیِ مستقیم: `classify` قراردادِ عمومیِ این ماژول است و
    ۴۹ تست رویش نشسته‌اند؛ شکلش نباید عوض شود. ترتیب هم اینجا تضمین می‌شود، نه
    در جای دیگر — یک opt-out هرگز نباید به گاردهای استعلام برسد.
    """
    try:
        import lead_suppression as _ls   # noqa: WPS433 — تنبل و اختیاری
        return _ls.classify_with_optout(msg, inner=classify)
    except Exception:  # noqa: BLE001
        return classify(msg)


def to_candidate(msg: dict, channel: str, key: str) -> dict:
    """پیامِ استعلام → کاندیدِ v1.1. `candidate_type` عمداً **اعلام نمی‌شود** تا دیوارِ
    رضایت از روی کانال تصمیم بگیرد (سقفِ کانال؛ producer هرگز خودش را ارتقا نمی‌دهد)."""
    m = normalize(msg)
    subject = m["subject"][:200]
    body = m["body"].strip()
    is_form = (channel == "website_form")
    is_inbound = (channel == "email_inbound")
    # برای اعلانِ فرم، «خواسته» = فیلدِ پیام؛ و موضوعِ اعلان («New enquiry from
    # website») حرفِ خودِ سایت است نه مشتری، پس وارد scope نمی‌شود.
    said = _message_from_form_body(body) if is_form else ""
    if said:
        scope = said[:SCOPE_MAX]
    else:
        scope = (f"{subject} — {body}" if subject and body else (subject or body))[:SCOPE_MAX]
    if is_form:
        # ⚠️ در اعلانِ فرم، پاکتِ نامه **خودِ سایت** است نه مشتری:
        # `From: Website Form <noreply@…>`. اگر ترتیبِ عادی بماند دو خرابیِ
        # مستقل رخ می‌دهد و هر دو تا لحظهٔ تماس نامرئی‌اند:
        #   ۱ ایمیلِ تماسِ لید = آدرسِ noreply ِ خودِ مالک ⇒ لیدی که گرفته شده
        #     ولی هیچ‌کس نمی‌تواند به مشتری جواب دهد.
        #   ۲ سلامِ پاسخِ اول «Hi Website» می‌شود — اولین چیزی که مشتری می‌خواند.
        # پس Reply-To (مکانیزمِ استانداردِ فرم‌ها) اول، بعد آدرسِ داخلِ بدنه،
        # و پاکت آخر.
        sender = _addr_of(m["reply_to"]) or _addr_of(body) or _addr_of(m["from"])
        name = _name_from_form_body(body)
    else:
        sender = _addr_of(m["reply_to"]) or _addr_of(m["from"]) or _addr_of(body)
        name = m["from"].split("<")[0].strip().strip('"') if "<" in m["from"] else ""
    # واقعیت‌های ملک (فلگ خاموش = `{}` و `unknown` — دقیقاً رفتارِ دیروز).
    # ⚠️ متنِ اسکن **کلِ** بدنه است نه `scope`: در اعلانِ فرم، `Suburb:`/`Postcode:`/
    # `Address:` عمداً از scope حذف شده‌اند (فرادادهٔ فرم‌اند) ولی دقیقاً همان
    # چیزی‌اند که geo از آن می‌آید.
    prop = extract_property(subject + "\n" + body) if property_extract_on() else {}
    urgency = str(prop.get("timing") or "unknown")
    return {
        "schema_version": "1.1",
        "source": {
            "channel": channel,
            "source_id": SOURCE_ID,
            "external_id": key,                    # هشِ filename-safe، نه Message-Id ِ خام
            "received_at": m["date"] or opslib.now_iso(),
        },
        # consent — دو حالتِ صریح، بقیه unknown و دیوار fail-closed می‌بندد:
        #   · فرمِ سایت: خودشان فرم را پر کردند.
        #   · ایمیلِ مستقیم: خودشان به آدرسِ کسب‌وکار نوشتند (رأیِ مالک ۰۸-۰۱،
        #     فقط وقتی `INBOUND_CONSENT_FLAG` مسلح است — `classify` کانالِ
        #     `email_inbound` را جز در آن حالت اصلاً نمی‌سازد).
        # `evidence` قابلِ ممیزی است: بعداً می‌شود پرسید «چرا فکر کردی رضایت
        # داشت؟» و جواب روی خودِ رکورد باشد، نه در ذهنِ کسی.
        "consent": {
            "basis": ("explicit" if is_form or is_inbound else "unknown"),
            "evidence": ("website_form_submission" if is_form else
                         "inbound_email_to_business_address" if is_inbound else ""),
            "compliance_reason": ("form_submission" if is_form else
                                  "customer_initiated_contact" if is_inbound else
                                  "email_unverified"),
        },
        "contact": {k: v for k, v in (
            ("name", name[:80] or None),
            ("email", sender or None),
            ("preferred_channel", "email"),
        ) if v},
        "property": prop,
        "request": {"service": "painting", "scope_text": scope, "urgency": urgency},
    }


# ── خوانندهٔ واقعیِ IMAP (فقط‌خواندنی؛ در تست هرگز اجرا نمی‌شود) ─────────────────
def imap_fetch(limit: int = MAX_PER_BEAT_DEFAULT,
               since_days: int = SINCE_DAYS_DEFAULT) -> list:
    """صندوق را **فقط‌خوانده** بخوان. هرگز حذف/انتقال؛ هرگز `\\Seen` نمی‌گذارد.

    دو لایهٔ عدمِ نشان‌گذاری: `select(readonly=True)` (=EXAMINE) و `BODY.PEEK[]`.
    بدونِ armـ صریح یا بدونِ credential → لیستِ خالی (fail-soft، بی‌صدا، بی‌اتصال).
    `imaplib` عمداً اینجا (نه top-level) import می‌شود: تست‌ها با تزریقِ fetch_fn هرگز
    به این تابع نمی‌رسند، و نبودِ `imaplib` در `sys.modules` قابلِ اثبات می‌ماند."""
    if not imap_armed() or not credentials_present():
        return []
    try:
        import datetime as _dt
        import email as _email
        import imaplib as _imaplib   # noqa: WPS433 — تنبل و عمدی
        from email.header import decode_header, make_header
    except Exception:  # noqa: BLE001
        return []

    addr = str(os.environ.get(ADDR_ENV, "")).strip()
    secret = str(os.environ.get(SECRET_ENV, "")).strip()    # فقط در همین scope؛ هرگز log
    out: list = []
    con = None
    try:
        con = _imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=30)
        con.login(addr, secret)
        con.select("INBOX", readonly=True)      # EXAMINE — سرور اجازهٔ تغییرِ flag ندارد
        since = (_dt.date.today() - _dt.timedelta(days=max(1, int(since_days)))).strftime("%d-%b-%Y")
        typ, data = con.search(None, "SINCE", since)
        if typ != "OK":
            return []
        nums = (data[0] or b"").split()
        for num in list(nums)[-max(1, int(limit)):]:
            try:
                t2, chunk = con.fetch(num, "(BODY.PEEK[])")   # PEEK = بدونِ \Seen
                if t2 != "OK" or not chunk or not isinstance(chunk[0], tuple):
                    continue
                em = _email.message_from_bytes(chunk[0][1])
                body = ""
                if em.is_multipart():
                    for part in em.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(
                                part.get_content_charset() or "utf-8", "replace")
                            break
                    if not body:
                        for part in em.walk():
                            if part.get_content_type() == "text/html":
                                body = _strip_html(part.get_payload(decode=True).decode(
                                    part.get_content_charset() or "utf-8", "replace"))
                                break
                else:
                    body = (em.get_payload(decode=True) or b"").decode(
                        em.get_content_charset() or "utf-8", "replace")

                def _hdr(nm: str) -> str:
                    try:
                        return str(make_header(decode_header(em.get(nm, "") or "")))
                    except Exception:  # noqa: BLE001
                        return str(em.get(nm, "") or "")

                out.append({
                    "message_id": em.get("Message-Id", "") or "",
                    "from": _hdr("From"), "to": _hdr("To"),
                    "reply_to": _hdr("Reply-To"), "subject": _hdr("Subject"),
                    "date": em.get("Date", "") or "", "body": body,
                    "headers": {k.lower(): v for k, v in em.items()},
                })
            except Exception:  # noqa: BLE001 — یک پیامِ خراب کلِ pollـ را نکشد
                continue
    except Exception as e:  # noqa: BLE001 — هرگز آدرس/پسورد در پیامِ خطا
        try:
            opslib.alert_throttled([f"lead_email_intake: IMAP خطا ({type(e).__name__})"],
                                   key="lead-email-intake-imap", window_s=3600.0)
        except Exception:  # noqa: BLE001
            pass
        return []
    finally:
        try:
            if con is not None:
                con.logout()
        except Exception:  # noqa: BLE001
            pass
    return out


# ── ضربان ───────────────────────────────────────────────────────────────────────
def beat(fetch_fn=None, submit_fn=None, limit: int | None = None,
         since_days: int | None = None, reply_fn=None) -> dict:
    """یک دورِ کامل: poll → طبقه‌بندی → نگاشت → submit_candidate. همیشه dict، هرگز استثنا.

    خروجی فقط **عدد و کُد** است — هیچ subject/بدنه/آدرسی. پیامِ غیرِ استعلام حتی یک
    کلیدِ dedup هم نمی‌گیرد (رد صفر).

    `reply_fn` (اختیاری، پیش‌فرض None) روی هر کاندیدِ **پذیرفته‌شده** صدا زده
    می‌شود تا پیش‌نویسِ پاسخِ اول ساخته شود. تزریق‌پذیر است تا این ماژول خالص
    بماند و هرگز به `lead_first_reply` وابسته نشود. **هرگز چیزی نمی‌فرستد** —
    ساختِ متن و ارسال دو تصمیمِ جداگانه‌اند و دومی رأیِ مالک است.

    چرا اصلاً اینجا: `lead_first_reply` بدونِ این قلاب **صفر صداکنندهٔ تولیدی**
    داشت. در همین مخزن دو بار در ۲۴ ساعت ماژولِ کاملِ بی‌صداکننده منتشر شده؛
    کدی که کسی صدایش نمی‌زند وجود ندارد، هرقدر هم تستش سبز باشد.
    """
    res = {"ok": True, "flag": FLAG, "armed": False, "fetched": 0, "inquiries": 0,
           "submitted": 0, "signals": 0, "duplicates": 0, "dropped": 0,
           "replies_drafted": 0,
           "quarantined": 0, "blocked": None, "reason": None, "injected": bool(fetch_fn),
           "ts": opslib.now_iso()}
    if not enabled():
        res.update(ok=False, reason="flag_off")
        return res

    kill = opslib.master_halted() or opslib.halted() or (
        "STOP-ORGANISM" if opslib.STOP_ORGANISM.exists() else None)
    if kill:
        res.update(ok=False, reason="halted")
        return res

    injected = fetch_fn is not None
    if not injected:
        if not imap_armed():
            res.update(reason="not_armed:" + IMAP_ARM_FLAG)
            return res
        if not credentials_present():
            res.update(reason="creds_absent:" + ADDR_ENV + "," + SECRET_ENV)
            return res
        fetch_fn = imap_fetch
    res["armed"] = True

    n_limit = int(limit if limit is not None
                  else os.environ.get("LEAD_EMAIL_MAX_PER_BEAT", MAX_PER_BEAT_DEFAULT))
    n_days = int(since_days if since_days is not None
                 else os.environ.get("LEAD_EMAIL_SINCE_DAYS", SINCE_DAYS_DEFAULT))
    # transport ِ تزریق‌شده می‌تواند بی‌آرگومان باشد (fixture) یا آرگومان‌پذیر (خوانندهٔ واقعی).
    try:
        msgs = fetch_fn(limit=n_limit, since_days=n_days)
    except TypeError:
        try:
            msgs = fetch_fn()
        except Exception:  # noqa: BLE001
            res.update(ok=False, reason="fetch_failed")
            return res
    except Exception:  # noqa: BLE001 — خطای transport هرگز محتوا echo نمی‌کند
        res.update(ok=False, reason="fetch_failed")
        return res
    msgs = list(msgs or [])[:n_limit]
    res["fetched"] = len(msgs)

    # درِ ورودِ canonical — تزریق‌پذیر تا تست بدونِ لمسِ state ِ زنده هم بتواند بسنجد.
    if submit_fn is None:
        try:
            import lead_candidate_inbox as _lci   # noqa: WPS433 — تنبل تا env ِ تست اثر کند
            submit_fn = _lci.submit_candidate
        except Exception:  # noqa: BLE001
            res.update(ok=False, reason="inbox_import_failed")
            return res

    seen = _load_seen()
    dirty = False
    held = 0
    for msg in msgs:
        # ⚠️ opt-out **قبل از** گاردهای استعلام. بدونِ این، «STOP» در گاردِ ۴
        # (`no_service_term`) و «unsubscribe» در گاردِ ۳ (`marketing_marks`)
        # می‌مرد — بی هیچ ردی. و پیامِ خروجیِ خودمان قول می‌دهد «reply STOP».
        # قول‌دادنِ لغوِ اشتراک و کر بودن نسبت به آن، دقیقاً همان چیزی است که
        # Spam Act 2003 جریمه می‌کند — و transport همین حالا مسلح است.
        # شنیدن هرگز گیت نمی‌شود؛ فقط **نوشتن** پشتِ فلگِ خودِ آن ماژول است.
        verdict = _classify_hearing_optout(msg)
        if verdict.get("opt_out"):
            res["opt_outs"] = res.get("opt_outs", 0) + 1
            continue          # ثبت شد (اگر فلگ مسلح باشد)؛ لید نیست
        if not verdict["is_inquiry"]:
            res["dropped"] += 1
            continue          # ← صفر رد: نه فایل، نه لاگ، نه کلیدِ dedup، نه شمارندهٔ محتوایی
        res["inquiries"] += 1
        key = dedup_key(msg)
        if key in seen:
            res["duplicates"] += 1
            continue
        cand = to_candidate(msg, verdict["channel"], key)
        try:
            out = submit_fn(cand, SOURCE_ID)
        except Exception:  # noqa: BLE001 — صداکننده هرگز استثنا نمی‌دهد، ولی fail-soft
            out = {"ok": False, "status": "submit_error"}
        status = str((out or {}).get("status") or "")
        if status == "accepted":
            res["submitted"] += 1
            if reply_fn is not None:
                try:
                    if (reply_fn(cand, out) or {}).get("ok"):
                        res["replies_drafted"] += 1
                except Exception:  # noqa: BLE001
                    # پیش‌نویسِ پاسخ **هرگز** نباید جذبِ لید را بکشد: لیدِ ثبت‌شدهٔ
                    # بی‌پیش‌نویس بی‌نهایت بهتر از لیدِ ازدست‌رفته است.
                    pass
        elif status == "signal_recorded":
            res["signals"] += 1
        elif status == "duplicate":
            res["duplicates"] += 1
        elif status == "quarantined":
            res["quarantined"] += 1
        elif status == "gate_off":
            held += 1
            continue          # کلید را ثبت نکن: با روشن‌شدنِ فلگ همین پیام باید برسد
        else:
            continue          # halted/ناشناخته → نگه‌دار، دوباره تلاش می‌شود
        seen[key] = opslib.now_iso()[:10]
        dirty = True

    if held:
        res["blocked"] = DOWNSTREAM_FLAG
        try:   # هشدارِ بی‌محتوا: فقط شمارش و نامِ فلگ
            opslib.alert_throttled(
                [f"lead_email_intake: {held} استعلام پشتِ فلگِ خاموشِ {DOWNSTREAM_FLAG} ماند"],
                key="lead-email-intake-downstream", window_s=3600.0)
        except Exception:  # noqa: BLE001
            pass
    if dirty:
        _save_seen(_prune(seen))
    return res


def card() -> str:
    """کارتِ «صندوق چه می‌کند» — شمار و کُد، هرگز محتوا و هرگز آدرس.

    این تنها سطحِ مالک‌روی لولهٔ ایمیل است. تا امروز تنها راهِ فهمیدنِ وضعیتش
    خواندنِ فایلِ سایدکار بود، و مالک از گوشی کار می‌کند.
    """
    import html
    import json as _json
    try:
        s = status()
    except Exception as e:  # noqa: BLE001
        return f"📥 <b>صندوقِ لید</b>\n▸ خوانده نشد: {html.escape(type(e).__name__)}"

    def _m(v):
        return "✅" if v else "🌑"

    L = ["📥 <b>صندوقِ لید (ایمیل)</b>",
         f"▸ لوله: {_m(s.get('enabled'))} <code>{html.escape(str(s.get('flag')))}</code>",
         f"▸ قفلِ صندوق: {_m(s.get('imap_armed'))} "
         f"<code>{html.escape(str(s.get('imap_arm_flag')))}</code>",
         f"▸ کلیدها: {_m(s.get('credentials_present'))} "
         f"({html.escape('، '.join(s.get('credentials_env') or []))})",
         f"▸ درِ کاندید: {_m(s.get('downstream_enabled'))}",
         f"▸ فرستندهٔ فرمِ سایت اعلام‌شده: {s.get('form_senders_configured', 0)}",
         f"▸ صندوق فقط‌خواندنی: {_m(s.get('readonly_mailbox'))} · "
         f"علامتِ خوانده: {'❌ نمی‌زند' if not s.get('marks_seen') else '⚠️ می‌زند'}"]

    # آخرین ضربان از سایدکارِ cockpit — فقط عدد، هرگز موضوع یا آدرس.
    try:
        sp = opslib.STATE_DIR / "ORGANISM-STATE.lead_email_intake"
        if sp.exists():
            d = _json.loads(sp.read_text("utf-8", errors="replace"))
            L.append("")
            L.append(f"<b>آخرین ضربان</b> — گرفته {d.get('fetched', 0)} · "
                     f"استعلام {d.get('inquiries', 0)} · ثبت {d.get('submitted', 0)} · "
                     f"لغو {d.get('opt_outs', 0)} · رد {d.get('dropped', 0)}")
            if d.get("blocked"):
                L.append(f"⚠️ پشتِ فلگِ خاموش: <code>{html.escape(str(d['blocked']))}</code>")
            if d.get("reason"):
                L.append(f"▸ دلیل: <code>{html.escape(str(d['reason']))}</code>")
    except Exception:  # noqa: BLE001 — سایدکار اختیاری است
        pass

    if not s.get("enabled"):
        L.append("")
        L.append("▸ نکنی: صندوق خوانده نمی‌شود و هیچ لیدی از ایمیل نمی‌آید.")
    else:
        L.append("")
        L.append("▸ نکنی: همین‌طور می‌ماند.")
    return "\n".join(L)


def status() -> dict:
    """گزارشِ امنِ owner-readiness — هرگز مقدارِ secret، هرگز آدرسِ کامل."""
    return {"flag": FLAG, "enabled": enabled(),
            "imap_arm_flag": IMAP_ARM_FLAG, "imap_armed": imap_armed(),
            "credentials_env": [ADDR_ENV, SECRET_ENV],
            "credentials_present": credentials_present(),
            "downstream_flag": DOWNSTREAM_FLAG,
            "downstream_enabled": os.environ.get(DOWNSTREAM_FLAG, "0") == "1",
            "form_senders_configured": len(_form_senders()),
            "property_flag": PROPERTY_FLAG,
            "property_extract_enabled": property_extract_on(),
            "property_suburbs_known": len(_SUBURBS),
            "seen_keys": len(_load_seen()),
            "readonly_mailbox": True, "marks_seen": False, "sends": False}


if __name__ == "__main__":
    # عمداً هیچ pollـی: فقط گزارشِ آمادگی (بدونِ اتصال، بدونِ secret).
    print(json.dumps(status(), ensure_ascii=False, indent=2))
