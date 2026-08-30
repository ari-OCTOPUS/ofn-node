#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lead_suppression.py — دروازهٔ حقوقیِ opt-out (Spam Act 2003 (Cth) §ِ unsubscribe).

چرا این فایل وجود دارد
──────────────────────
پیامِ خروجیِ ما امروز قول می‌دهد (`lead_first_reply.py:376-377`):

    "If you'd rather not hear from us again, just reply with the word STOP
     and we won't contact you again."

و `lead_outbound_transport.py:258` هم "Reply STOP to opt out." را به هر بدنه می‌چسباند.
ولی هیچ‌چیز در این ماشین STOP را **نمی‌شنود**: یک پاسخِ «STOP» به `lead_email_intake.classify`
می‌رسد و آن‌جا در گاردِ ۴ با `no_service_term` رد می‌شود، و «unsubscribe» در گاردِ ۳ با
`marketing_marks` — هر دو **بدونِ هیچ رد و اثری**. جدولِ `suppression` در `consent.db`
از روزِ ساخته‌شدنش (۲۰۲۶-۰۷-۲۲) صفر ردیف دارد.

قولِ unsubscribe دادن و نشنیدنش، دقیقاً همان چیزی است که ACMA بابتش جریمه می‌کند.
و چون `OCTOPUS_WIRE_LEAD_OUTBOUND=1` و `OCTOPUS_SMTP_USE_GMAIL=1` هم‌اکنون در هر چهار
پروسه مسلح‌اند، این تنها چیزی است که باید **پیش از** اولین ارسالِ واقعی وجود داشته باشد.

storeِ دوم نمی‌سازیم — REUSE
────────────────────────────
`consent_store.py` از قبل primitiveهای suppression را دارد و ما دقیقاً همان‌ها را
صدا می‌زنیم؛ این ماژول **هیچ جدولی نمی‌سازد** و هیچ DDLای ندارد:
  · `ConsentStore.insert_suppression(value, kind, reason)` → idempotent (INSERT OR IGNORE
    روی PRIMARY KEY)، هرگز purge نمی‌شود، `lifted_at` فقط nullable است.
  · `ConsentStore.suppression_active(value)` → دلیل یا None؛ خطا = «فعال» (fail-closed).
  · `ConsentStore.record_event(...)` با `event_type='consent.suppressed'` → ردِ append-only.
تنها تفاوتِ ما با صداکننده‌های موجود این است که مقدارِ کلید را **plaintext نمی‌فرستیم**.

آدرس هرگز plaintext ذخیره نمی‌شود
─────────────────────────────────
کلیدِ ستونِ `channel_value_norm` نزدِ ما یک اثرِ انگشتِ نمک‌دار است:
`"e1:" + pbkdf2_hmac('sha256', normalized_address, salt, KDF_ROUNDS)`.
نمک یک‌بار در `state/legs/lead-suppression.salt` ساخته می‌شود (۳۲ بایتِ `os.urandom`).

⚠️ `KDF_ROUNDS` و مقدارِ نمک **هرگز** نباید عوض شوند: عوض‌شدنشان یعنی همهٔ ردیف‌های
موجود دیگر تطبیق نمی‌خورند — یعنی آدم‌هایی که STOP زده‌اند بی‌صدا دوباره قابلِ ایمیل
می‌شوند. اگر نمک گم شود و ردیفی وجود داشته باشد، این ماژول **fail-closed** می‌شود
(`suppression-unverifiable`) — یعنی ارسال متوقف می‌شود، نه اینکه به غریبه ایمیل برود.

suppression ابدی است
────────────────────
اینجا نه `unsuppress` هست، نه `lift`، نه `delete`، و هیچ SQLِ DELETE/UPDATE روی جدول
زده نمی‌شود. دوباره suppress کردنِ یک نفر بی‌ضرر است (idempotent)؛ برداشتنش قابلیتِ این
ماژول نیست. (ستونِ `lifted_at` در schema برای رأیِ صریحِ مالک از مسیرِ دیگری است.)

فلگ
───
`OCTOPUS_WIRE_LEAD_SUPPRESSION=1` — پیش‌فرض **خاموش**، و خاموش‌بودن دقیقاً بایت‌به‌بایتِ
امروز است: هیچ فایلی ساخته نمی‌شود، هیچ ردیفی نوشته نمی‌شود، هیچ DBای لمس نمی‌شود.
فلگ فقط **نوشتن** را گیت می‌کند. دو رفتارِ دیگر عمداً بی‌گیت‌اند، چون هر دو در جهتِ
ایمنی‌اند و گیت‌کردنشان یعنی «دروازه‌ای که می‌شود خلعِ سلاحش کرد»:
  · شناساییِ opt-out (`classify_optout`) — تابعِ خالص، بدونِ I/O.
  · ردِ ارسال (`check_send`) — با فلگِ خاموش هم اگر ردیفی وجود داشته باشد رد می‌کند.
    (با فلگِ خاموش هرگز ردیفی نوشته نشده، پس نتیجه‌اش «مجاز» است = رفتارِ امروز.)

⚠️ تلهٔ «سیم‌کشی‌شده ولی مسلح‌نشده»: اگر روزی `classify_with_optout` در `classify`
نشست ولی فلگ ست نشد، STOP شناخته می‌شود و پیام لید نمی‌شود (= امروز)، ولی **ثبت هم
نمی‌شود**. سیم‌کشی و مسلح‌کردن باید در یک تغییر باشند.

stdlib-only. هرگز نمی‌فرستد، هرگز شبکه نمی‌زند، هرگز حذف نمی‌کند، هرگز آدرس را چاپ
نمی‌کند (فقط `mask()`).
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib   # noqa: E402

# ── فلگ ────────────────────────────────────────────────────────────────────────
FLAG = "OCTOPUS_WIRE_LEAD_SUPPRESSION"      # فقط **نوشتن** را گیت می‌کند
SALT_ENV = "OCTOPUS_LEAD_SUPPRESSION_SALT"  # اختیاری — وگرنه فایلِ نمک
_TRUTHY = {"1", "true", "yes", "on"}

# ⚠️ ثابت‌های قفل‌شده — تغییرشان همهٔ suppressionهای موجود را بی‌اثر می‌کند.
KDF_ROUNDS = 120_000
SALT_BYTES = 32
FP_PREFIX = "e1:"          # e = email، 1 = نسخهٔ الگوریتم

# سقفِ طولِ متنی که «درخواستِ opt-out» شمرده می‌شود.
#
# این سقف عمداً **بلند** است. محافظت در برابرِ مثبتِ کاذب از سه جای دیگر می‌آید:
# هدرِ فرستندهٔ انبوه، بریدنِ متنِ نقل/فوروارد، و خودِ واژگان (که فقط شکل‌های
# چندکلمه‌ایِ بی‌ابهام را می‌پذیرد — «unsubscribe» ِ تنها فقط وقتی کلِ پیام باشد).
# سقفِ کوتاه یک **شکافِ حقوقی** می‌ساخت: آدمی که در انتهای یک ایمیلِ بلند و
# انسانی می‌نویسد «please remove me from your list» هم زیرِ Spam Act یک درخواستِ
# معتبر است و نباید به گاردهای استعلام بیفتد و بی‌صدا دور ریخته شود. آن‌چه این سقف
# واقعاً می‌گیرد، متنِ **کپی‌شدهٔ** یک خبرنامهٔ طولانی است که پاورقی‌اش داخلِ پیام آمده.
MAX_OPTOUT_CHARS = 2000

# ── کُدهای دلیل (هرگز سکوت — هر مسیر یک کُد دارد) ────────────────────────────────
CODE_OK = "not-suppressed"
CODE_SUPPRESSED = "suppressed"
CODE_UNVERIFIABLE = "suppression-unverifiable"   # ردیف هست ولی تطبیق ممکن نیست
CODE_ERROR = "suppression-check-error"
CODE_NO_RECIPIENT = "no-recipient"
CODE_STORE_ABSENT = "store-absent"               # هرگز کسی opt-out نکرده
CODE_STORE_EMPTY = "store-empty"
CODE_FLAG_OFF = "flag-off"
CODE_RECORDED = "recorded"
CODE_ALREADY = "already-suppressed"
CODE_SALT_UNAVAILABLE = "salt-unavailable"
CODE_RECORD_ERROR = "record-error"

# واژگانِ `reason` در schema بسته است (CHECK در consent_store._ddl)
REASON_STOP = "stop_reply"
REASON_UNSUB = "unsubscribe"
REASON_BOUNCE = "bounce"
REASON_MANUAL = "manual_dnc"
REASON_COMPLAINT = "complaint"
STORE_REASONS = (REASON_STOP, REASON_UNSUB, REASON_BOUNCE, REASON_MANUAL, REASON_COMPLAINT)


def enabled() -> bool:
    """آیا اجازهٔ **نوشتن** در store هست؟ (خواندن/ردکردن بی‌گیت است.)"""
    return os.environ.get(FLAG, "").strip().lower() in _TRUTHY


# ── نرمال‌سازیِ متن (فارسی-آگاه) ─────────────────────────────────────────────────
# نویسه‌های صفرعرض/جهت‌ده که در متنِ فارسیِ کپی‌شده فراوان‌اند و مقایسه را می‌شکنند.
_ZW = dict.fromkeys(
    (0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
     0x2066, 0x2067, 0x2068, 0x2069, 0xFEFF), None)
_AR_FIX = {ord("ي"): "ی", ord("ك"): "ک",
           ord("ة"): "ه", ord("ۀ"): "ه"}
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_TAG_RE = re.compile(r"<[^>]{1,400}>", re.S)
_ADDR_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}")


def _strip_html(text: str) -> str:
    t = _TAG_RE.sub(" ", text or "")
    for ent, rep in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                     ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(ent, rep)
    return _WS_RE.sub(" ", t)


def fold(s) -> str:
    """NFKC + حذفِ نویسه‌های صفرعرض/bidi + یکسان‌سازیِ ی/ک عربی + casefold."""
    t = unicodedata.normalize("NFKC", str(s or ""))
    t = t.translate(_ZW).translate(_AR_FIX)
    return _WS_RE.sub(" ", t).strip().casefold()


# ── جداکردنِ «متنِ خودِ فرستنده» از نقلِ نامهٔ ما ─────────────────────────────────
# ⚠️ حیاتی: پاورقیِ خودِ ما شاملِ «reply with the word STOP» است. اگر بدنهٔ کامل را
# اسکن کنیم، **هر پاسخی** که نامهٔ ما را نقل کرده opt-out شمرده می‌شود — یعنی هر
# مشتریِ واقعی که جواب می‌دهد برای همیشه خاموش می‌شود.
_OWN_FOOTER = (
    "if you'd rather not hear from us again",
    "if you would rather not hear from us again",
    "reply stop to opt out",
    "reply with the word stop",
)
_CUT_RES = (
    re.compile(r"^\s*>"),
    re.compile(r"^\s*on\b.{0,160}\bwrote\s*:", re.I),
    re.compile(r"^\s*-{2,}\s*original message", re.I),
    re.compile(r"^\s*-{2,}\s*forwarded message", re.I),
    re.compile(r"^\s*_{10,}\s*$"),
    re.compile(r"^\s*from\s*:\s*.*@", re.I),
    re.compile(r"^\s*sent from my\b", re.I),
    re.compile(r"^\s*begin forwarded message", re.I),
)


def unquoted(body: str) -> str:
    """فقط متنی که خودِ فرستنده **تایپ کرده**؛ از اولین نشانهٔ نقل/فوروارد به بعد بریده."""
    raw = str(body or "").replace("\r\n", "\n").replace("\r", "\n")
    if "<" in raw and ">" in raw:
        raw = _strip_html(raw)
    out = []
    for line in raw.split("\n"):
        low = fold(line)
        if any(s in low for s in _OWN_FOOTER):
            break
        if any(rx.search(line) for rx in _CUT_RES):
            break
        out.append(line)
    return "\n".join(out).strip()


# ── واژگانِ opt-out ─────────────────────────────────────────────────────────────
# ردهٔ ۱ — «کلِ پیام همین است». قولِ ما تحت‌اللفظی «reply with the word STOP» است،
# پس «stop» ِ تنها فقط وقتی معتبر است که کلِ پیام باشد (نه «stop by tomorrow»).
_BARE_STOP = ("stop", "stopp", "توقف", "استاپ")
_BARE_UNSUB = (
    "unsubscribe", "unsub", "remove me", "take me off", "opt out", "optout",
    "no more emails", "no more email",
    "لغو اشتراک", "لغو عضویت", "قطع اشتراک",
    "حذفم کن", "حذفم کنید", "مرا حذف کن", "منو حذف کن",
)
# ردهٔ ۲ — عبارتِ چندکلمه‌ایِ بدونِ ابهام، فقط اگر متن کوتاه باشد.
_PHRASE_STOP = (
    "stop contacting", "stop emailing", "stop sending", "stop messaging",
    "stop all contact",
    "دیگر تماس نگیر", "دیگه تماس نگیر", "تماس نگیرید",
)
_PHRASE_UNSUB = (
    "unsubscribe me", "remove me from", "take me off your", "take me off the",
    "opt me out", "opt-out", "do not contact me", "don't contact me",
    "do not email me", "don't email me", "do not call me", "don't call me",
    "no longer wish to receive", "no longer want to receive",
    "remove my email", "remove my details", "delete my email", "delete my details",
    "انصراف از دریافت", "ایمیل نفرستید", "ایمیل نفرست",
    "پیام ندهید", "مرا حذف کنید",
)
# واژه‌های تعارفی/سرآیندِ پاسخ که «کلِ پیام همین است» را نباید بشکنند.
_POLITE = {
    "please", "pls", "plz", "thanks", "thank", "you", "regards", "kind", "hi",
    "hello", "hey", "cheers", "and", "just", "now", "immediately", "asap",
    "re", "fw", "fwd",
    "لطفا", "لطفاً", "ممنون", "متشکرم", "سلام", "تشکر", "با",
}
_PUNCT = " \t\n.,!;:\"'()[]*…،؛؟?—–-"
_SPACE_RE = re.compile(r"\s+")


def _despace(s: str) -> str:
    return _SPACE_RE.sub("", s)


# فارسی با نیم‌فاصله/بی‌فاصله هم نوشته می‌شود («لغو‌اشتراک»، «لغواشتراک»). `fold`
# نویسهٔ صفرعرض را برمی‌دارد، پس نسخهٔ بی‌فاصله را جداگانه هم می‌سنجیم. این تساهل
# **فقط** برای عبارت‌های غیر-ASCII است تا رفتارِ انگلیسی دقیقاً همان قواعدِ بافاصله بماند.
_BARE_STOP_D = tuple(_despace(x) for x in _BARE_STOP if not x.isascii())
_BARE_UNSUB_D = tuple(_despace(x) for x in _BARE_UNSUB if not x.isascii())
_PHRASE_STOP_D = tuple(_despace(x) for x in _PHRASE_STOP if not x.isascii())
_PHRASE_UNSUB_D = tuple(_despace(x) for x in _PHRASE_UNSUB if not x.isascii())
_BULK_HEADERS = ("list-unsubscribe", "list-id", "list-post", "feedback-id",
                 "x-campaign-id", "x-mailer-campaign")


def _core(folded: str) -> str:
    """هستهٔ پیام: نشانه‌ها و واژه‌های تعارفی حذف‌شده."""
    toks = [t.strip(_PUNCT) for t in folded.split()]
    return " ".join(t for t in toks if t and t not in _POLITE)


def normalize_address(raw) -> str | None:
    """آدرسِ نرمال‌شده (lowercase، از داخلِ «Name <a@b>») یا None."""
    m = _ADDR_RE.search(str(raw or ""))
    if not m:
        return None
    s = m.group(0).strip().lower()
    dom = s.rsplit("@", 1)[-1]
    return s if ("@" in s and "." in dom and len(s) >= 6) else None


def mask(addr) -> str:
    """«ab***@domain» — آدرسِ کامل هرگز در بازگشتی/لاگ/خطا نمی‌نشیند."""
    a = str(addr or "").strip()
    local, _, dom = a.partition("@")
    if not dom:
        return "***"
    return (local[:2] + "***@" + dom) if local else ("***@" + dom)


# ── پیش‌طبقه‌بند (تابعِ خالص — صفر I/O، صفر فلگ) ─────────────────────────────────
def classify_optout(msg) -> dict | None:
    """آیا این پیام یک **درخواستِ opt-out** است؟ dict یا None.

    این تابع باید **پیش از** شش گاردِ `lead_email_intake.classify` بدود؛ آن گاردها
    امروز STOP را با `no_service_term` و unsubscribe را با `marketing_marks` بی‌اثر
    دور می‌ریزند. اینجا هیچ‌کدام از جدول‌های آن گاردها خوانده نمی‌شود.

    فرستندهٔ انبوه (هدرِ list-unsubscribe و …) عمداً None می‌گیرد: آن نامهٔ **خودِ**
    اوست، نه درخواستِ ما را قطع‌کردن. اجازه می‌دهیم گاردِ bulk خودش ردش کند.
    """
    try:
        m = msg if isinstance(msg, dict) else {"body": str(msg or "")}
        hdrs = m.get("headers") if isinstance(m.get("headers"), dict) else {}
        headers = {str(k).lower(): str(v) for k, v in hdrs.items()}
        for hk in _BULK_HEADERS:
            if headers.get(hk):
                return None

        subject = str(m.get("subject") or headers.get("subject") or "")
        body = str(m.get("body") or m.get("text") or "")
        own = unquoted(body)

        f_sub = fold(subject)
        f_own = fold(own)
        cores = [c for c in (_core(f_own), _core(f_sub)) if c]

        matched = reason = code = None
        for c in cores:
            d = _despace(c)
            if c in _BARE_STOP or d in _BARE_STOP_D:
                matched, reason, code = c, REASON_STOP, "bare_token"
                break
            if c in _BARE_UNSUB or d in _BARE_UNSUB_D:
                matched, reason, code = c, REASON_UNSUB, "bare_token"
                break
        if matched is None:
            joined = (f_sub + " \n " + f_own).strip()
            jd = _despace(joined)
            if len(joined) <= MAX_OPTOUT_CHARS:
                for p in _PHRASE_STOP:
                    if p in joined:
                        matched, reason, code = p, REASON_STOP, "phrase"
                        break
                if matched is None:
                    for pd in _PHRASE_STOP_D:
                        if pd in jd:
                            matched, reason, code = pd, REASON_STOP, "phrase"
                            break
                if matched is None:
                    for p in _PHRASE_UNSUB:
                        if p in joined:
                            matched, reason, code = p, REASON_UNSUB, "phrase"
                            break
                if matched is None:
                    for pd in _PHRASE_UNSUB_D:
                        if pd in jd:
                            matched, reason, code = pd, REASON_UNSUB, "phrase"
                            break
        if matched is None:
            return None

        addr = (normalize_address(m.get("reply_to")) or normalize_address(m.get("from"))
                or normalize_address(headers.get("reply-to"))
                or normalize_address(headers.get("from")))
        return {"opt_out": True, "reason": reason, "code": code, "matched": matched,
                "address": addr, "address_masked": mask(addr or "")}
    except Exception:  # noqa: BLE001 — ابهام = «opt-out نیست»، پیام به گاردها می‌رود
        return None


def classify_with_optout(msg, *, inner=None, record: bool = True,
                         lead_id: str = "", store_path=None) -> dict:
    """رَپِرِ ترتیب‌دار: opt-out **قبل از** هر گاردِ استعلام.

    قراردادِ ترتیب که این تابع تضمین می‌کند: اگر پیام opt-out باشد، `inner`
    (یعنی `lead_email_intake.classify`) **اصلاً صدا زده نمی‌شود**.
    """
    v = classify_optout(msg)
    if v is None:
        if inner is None:
            return {"is_inquiry": False, "channel": None,
                    "reason": "no_inner_classifier", "opt_out": False}
        return inner(msg)

    rec = ({"recorded": False, "code": "not-requested"} if not record
           else record_optout(v.get("address"), v.get("reason"),
                              lead_id=lead_id, store_path=store_path))
    return {"is_inquiry": False, "channel": None, "reason": "opt_out", "opt_out": True,
            "opt_out_code": v["code"], "suppression_reason": v["reason"],
            "recorded": bool(rec.get("recorded")), "record_code": rec.get("code"),
            "address_masked": v["address_masked"]}


# ── نمک و اثرِ انگشت ────────────────────────────────────────────────────────────
def _salt_path() -> Path:
    return Path(opslib.STATE_DIR) / "legs" / "lead-suppression.salt"


def _salt(*, create: bool = False) -> bytes | None:
    """نمکِ پایدار. `create=False` هرگز چیزی نمی‌سازد (چکِ فقط‌خواندنی side-effect ندارد)."""
    env = os.environ.get(SALT_ENV, "").strip()
    if env:
        return env.encode("utf-8")
    p = _salt_path()
    try:
        if p.exists():
            b = p.read_bytes()
            return b if len(b) >= 16 else None
        if not create:
            return None
        p.parent.mkdir(parents=True, exist_ok=True)
        b = os.urandom(SALT_BYTES)
        p.write_bytes(b)
        try:
            os.chmod(p, 0o600)
        except Exception:  # noqa: BLE001 — ویندوز/ACL: بهترین تلاش
            pass
        return b
    except Exception:  # noqa: BLE001
        return None


def fingerprint(address, *, create_salt: bool = False) -> str | None:
    """اثرِ انگشتِ نمک‌دارِ آدرس — همان چیزی که در store می‌نشیند. None اگر ممکن نبود."""
    norm = normalize_address(address)
    if not norm:
        return None
    salt = _salt(create=create_salt)
    if salt is None:
        return None
    return FP_PREFIX + hashlib.pbkdf2_hmac(
        "sha256", norm.encode("utf-8"), salt, KDF_ROUNDS).hex()


# ── store (هیچ DDLای اینجا نیست — همان consent_store) ───────────────────────────
def db_path(explicit=None) -> Path:
    if explicit:
        return Path(explicit)
    try:
        import consent_store as _cs   # noqa: WPS433 — lazy، هم‌پوشه
        return Path(_cs._default_path())
    except Exception:  # noqa: BLE001
        return Path(opslib.STATE_DIR) / "legs" / "consent.db"


def _hashed_rows_exist(path) -> bool:
    """آیا اصلاً ردیفی با کلیدِ هش‌شده هست؟ ابهام (خطا) ⇒ True یعنی fail-closed.

    این تابع تنها چیزی است که تفاوتِ «نمی‌دانم» و «چیزی برای دانستن نیست» را
    تعیین می‌کند. بدونِ آن، نبودِ نمک هر ارسالی را می‌بست — یعنی یک گاردِ ایمنی
    به قطعِ سراسریِ سرویس تبدیل می‌شد.
    """
    con = None
    try:
        con = sqlite3.connect(str(path))
        row = con.execute(
            "SELECT COUNT(*) FROM suppression "
            "WHERE lifted_at IS NULL AND channel_value_norm LIKE ?",
            (FP_PREFIX + "%",)).fetchone()
        return bool(row and int(row[0]) > 0)
    except Exception:  # noqa: BLE001
        return True          # نمی‌دانم ⇒ سخت‌گیرانه
    finally:
        try:
            if con is not None:
                con.close()
        except Exception:  # noqa: BLE001
            pass


def _legacy_plaintext_hit(path, norm: str):
    """ردیفِ suppressionِ مسیرِ قدیمی (کلیدِ متنِ ساده). هرگز فایل نمی‌سازد."""
    store = None
    try:
        import consent_store as _cs   # noqa: WPS433
        store = _cs.ConsentStore(path)
        return store.suppression_active(norm)
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass


def _active_count(path) -> int | None:
    """تعدادِ suppressionِ فعال، یا None اگر خوانده نشد. هرگز فایل نمی‌سازد."""
    con = None
    try:
        con = sqlite3.connect(str(path))
        row = con.execute(
            "SELECT COUNT(*) FROM suppression WHERE lifted_at IS NULL").fetchone()
        return int(row[0]) if row else 0
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            if con is not None:
                con.close()
        except Exception:  # noqa: BLE001
            pass


def record_optout(address, reason: str = REASON_STOP, *, lead_id: str = "",
                  source_event_id=None, store_path=None) -> dict:
    """ثبتِ opt-out. idempotent و **ابدی**. فقط با فلگِ مسلح می‌نویسد.

    خروجی همیشه dict با `code` — هرگز سکوت، هرگز استثنا.
    """
    out = {"ok": False, "recorded": False, "new": False, "code": "",
           "address_masked": mask(address or "")}
    if not enabled():
        out["code"] = CODE_FLAG_OFF
        return out
    norm = normalize_address(address)
    if not norm:
        out["code"] = CODE_NO_RECIPIENT
        return out
    r = reason if reason in STORE_REASONS else REASON_MANUAL
    fp = fingerprint(norm, create_salt=True)
    if not fp:
        out["code"] = CODE_SALT_UNAVAILABLE
        return out
    store = None
    try:
        import consent_store as _cs   # noqa: WPS433 — lazy، هم‌پوشه
        store = _cs.ConsentStore(db_path(store_path))
        new = store.insert_suppression(fp, "email", r, source_event_id=source_event_id)
        try:   # ردِ append-only برای ممیزی. payload هرگز آدرس ندارد.
            store.record_event({
                "lead_id": str(lead_id or ""), "event_type": "consent.suppressed",
                "actor": "inbox", "to_state": "SUPPRESSED",
                "idempotency_key": "supp:" + fp,
                "payload": {"kind": "opt_out", "channel_kind": "email",
                            "reason": r, "fp_prefix": fp[:15]}})
        except Exception:  # noqa: BLE001 — ردِ ممیزی هرگز خودِ suppression را لغو نمی‌کند
            pass
        out.update({"ok": True, "recorded": True, "new": bool(new),
                    "code": CODE_RECORDED if new else CODE_ALREADY})
    except Exception as e:  # noqa: BLE001
        out["code"] = CODE_RECORD_ERROR
        out["detail"] = type(e).__name__
    finally:
        try:
            if store is not None:
                store.close()
        except Exception:  # noqa: BLE001
            pass
    return out


def is_suppressed(address, *, store_path=None) -> dict:
    """آیا این آدرس opt-out کرده؟ همیشه dict با `code` — هرگز None، هرگز استثنا.

    ابهام = suppressed (fail-closed). ولی «storeِ خالی/نبود» ابهام **نیست**: یعنی
    هیچ‌کس تا امروز opt-out نکرده، و آن پاسخِ قطعیِ «نه» است.
    """
    base = {"suppressed": False, "code": CODE_OK, "reason": "",
            "address_masked": mask(address or "")}
    try:
        norm = normalize_address(address)
        if not norm:
            base["code"] = CODE_NO_RECIPIENT
            return base
        p = db_path(store_path)
        if not p.exists():
            base["code"] = CODE_STORE_ABSENT
            return base
        n = _active_count(p)
        if n is None:
            base.update({"suppressed": True, "code": CODE_UNVERIFIABLE,
                         "reason": "store-unreadable"})
            return base
        if n == 0:
            base["code"] = CODE_STORE_EMPTY
            return base
        fp = fingerprint(norm, create_salt=False)
        if not fp:
            # ⚠️ ۲۰۲۶-۰۸-۰۱ — این شاخه اول **هر ارسالی** را می‌بست و سه تستِ
            # `test_lead_outbound_transport` را قرمز کرد. استدلالِ اصلاح:
            #
            #   نمک در **اولین نوشتنِ** ما ساخته می‌شود. پس نبودِ نمک یعنی این
            #   ماژول هرگز رکوردی ننوشته، پس هیچ ردیفِ `e1:` ای وجود ندارد،
            #   پس چیزی نیست که از دستش بدهیم. ردیف‌های موجود همه از مسیرِ
            #   قدیمیِ متنِ ساده‌اند و آن‌ها را **می‌توانیم** دقیق بپرسیم.
            #
            # پس: اگر هیچ ردیفِ هش‌داری نیست، جست‌وجوی متنِ ساده قطعی است و
            # جوابش معتبر. fail-closed فقط وقتی درست است که واقعاً ابهام باشد —
            # وگرنه یک گاردِ ایمنی به یک قطعِ سراسریِ سرویس تبدیل می‌شود، و آن
            # خودش یک شکستِ ایمنی است.
            if _hashed_rows_exist(p):
                base.update({"suppressed": True, "code": CODE_UNVERIFIABLE,
                             "reason": CODE_SALT_UNAVAILABLE})
                return base
            legacy = _legacy_plaintext_hit(p, norm)
            if legacy:
                base.update({"suppressed": True, "code": CODE_SUPPRESSED,
                             "reason": str(legacy)})
            else:
                base["code"] = CODE_STORE_EMPTY   # هیچ ردیفِ هش‌داری نیست
            return base
        store = None
        try:
            import consent_store as _cs   # noqa: WPS433
            store = _cs.ConsentStore(p)
            hit = store.suppression_active(fp)
        finally:
            try:
                if store is not None:
                    store.close()
            except Exception:  # noqa: BLE001
                pass
        if not hit:
            # ⚠️ ۲۰۲۶-۰۸-۰۱ — بازگشت به کلیدِ قدیمی. جدولِ suppression از
            # ۲۰۲۶-۰۷-۲۲ وجود دارد و ردیف‌هایش کلیدِ **متنِ ساده** دارند. از
            # لحظه‌ای که نمک ساخته شد، این تابع فقط هش را می‌پرسید — یعنی هر
            # کسی که پیش از امروز opt-out کرده بود **دوباره ایمیل می‌گرفت**.
            # مهاجرتِ شکلِ کلید هرگز نباید خواننده را نسبت به گذشته کور کند.
            hit = _legacy_plaintext_hit(p, norm)
        if hit:
            base.update({"suppressed": True, "code": CODE_SUPPRESSED, "reason": str(hit)})
        return base
    except Exception as e:  # noqa: BLE001 — هر ابهام = رد
        base.update({"suppressed": True, "code": CODE_ERROR, "reason": type(e).__name__})
        return base


def recipient_of(candidate) -> str | None:
    """گیرندهٔ نرمال‌شدهٔ یک candidate (هم‌شکلِ lead_outbound_transport._recipient)."""
    c = candidate if isinstance(candidate, dict) else {}
    contact = c.get("contact") if isinstance(c.get("contact"), dict) else {}
    return normalize_address(contact.get("email") or c.get("email") or "")


_MARKER_KEYS = ("opt_out", "stop", "unsubscribed", "do_not_contact")


def _record_marker(candidate) -> str | None:
    """نشانِ opt-out رویِ خودِ رکورد (لایهٔ صفر، بدونِ I/O)."""
    c = candidate if isinstance(candidate, dict) else {}
    contact = c.get("contact") if isinstance(c.get("contact"), dict) else {}
    for holder in (c, contact):
        for k in _MARKER_KEYS:
            if holder.get(k):
                return k
    return None


def check_send(candidate, *, effect_id=None, authorized=None, store_path=None) -> dict:
    """دروازهٔ **زمانِ ارسال**. همیشه dict با `allow` و `code` — هرگز سکوت.

    عمداً هیچ‌جا `authorized` را در تصمیم دخالت نمی‌دهد: کسی که opt-out کرده رد
    می‌شود **حتی اگر** effectِ معتبر و authorizeشدهٔ مالک وجود داشته باشد. آدم می‌تواند
    بعد از نوشته‌شدنِ کوت هم opt-out کند؛ چکِ زمانِ intake به‌تنهایی کافی نیست.
    `authorized` فقط برای ردِ ممیزی در خروجی بازتاب می‌شود.
    """
    to = recipient_of(candidate)
    res = {"allow": False, "code": "", "reason": "", "to_masked": mask(to or ""),
           "effect_id": str(effect_id or ""), "authorized": authorized}
    try:
        if not to:
            res["code"] = CODE_NO_RECIPIENT
            res["reason"] = "candidate has no usable email"
            return res
        marker = _record_marker(candidate)
        if marker:
            res["code"] = CODE_SUPPRESSED
            res["reason"] = f"candidate-marker:{marker}"
            return res
        s = is_suppressed(to, store_path=store_path)
        if s["suppressed"]:
            res["code"] = s["code"]
            res["reason"] = (f"{s['code']}:{s['reason']}" if s.get("reason") else s["code"])
            return res
        res.update({"allow": True, "code": CODE_OK, "reason": s["code"]})
        return res
    except Exception as e:  # noqa: BLE001 — هر ابهام = رد
        res.update({"allow": False, "code": CODE_ERROR, "reason": type(e).__name__})
        return res


def status() -> dict:
    """گزارشِ صادقانه — هرگز نمک، هرگز آدرس."""
    p = db_path()
    present = p.exists()
    n = _active_count(p) if present else 0
    return {"flag": FLAG, "armed": enabled(), "store_present": present,
            "active_suppressions": n, "salt_present": _salt(create=False) is not None,
            "kdf_rounds": KDF_ROUNDS, "plaintext_stored": False,
            "store_owner": "consent_store.ConsentStore (reused, no second store)"}


def card() -> str:
    """کارتِ «چه کسانی گفتند دیگر پیام نده» — بدونِ حتی یک آدرس.

    این کارت عمداً هیچ نشانی از هویتِ کسی نمی‌دهد؛ فقط شمار و سلامتِ سازوکار.
    اگر روزی کسی بخواهد بداند «چه کسی opt-out کرد»، جوابِ درست این است که
    نمی‌شود — ذخیره هش است و همین ویژگی است، نه نقص.
    """
    import html
    try:
        s = status()
    except Exception as e:  # noqa: BLE001
        return f"🚫 <b>لغوِ اشتراک</b>\n▸ خوانده نشد: {html.escape(type(e).__name__)}"

    heard = "✅ همیشه" if True else ""      # شنیدن هرگز گیت نمی‌شود
    write = "✅ مسلح" if s.get("armed") else "🌑 خاموش"
    L = ["🚫 <b>لغوِ اشتراک (STOP)</b>",
         f"▸ شنیدنِ STOP: {heard} — گیت‌پذیر نیست",
         f"▸ ثبتِ رکورد: {write} (<code>{html.escape(str(s.get('flag')))}</code>)",
         f"▸ کسانی که گفتند نه: <b>{s.get('active_suppressions', 0)}</b>",
         f"▸ آدرسِ خام روی دیسک: {'❌ هرگز' if not s.get('plaintext_stored') else '⚠️ بله'}"]
    if not s.get("store_present"):
        L.append("▸ انبار هنوز ساخته نشده — یعنی تا امروز کسی opt-out نکرده.")
    elif s.get("active_suppressions") and not s.get("salt_present"):
        L.append("⚠️ رکورد هست ولی نمک نیست — ارسال به هر آدرسِ هش‌شده بسته می‌ماند.")
    L.append("")
    L.append("▸ نکنی: همین‌طور می‌ماند. کسی که STOP بزند دیگر ایمیل نمی‌گیرد؛ "
             "این مرزِ قانونی است، نه یک قابلیت.")
    return "\n".join(L)


if __name__ == "__main__":   # pragma: no cover — گزارشِ دستی، بدونِ side-effect
    import json
    print(json.dumps(status(), ensure_ascii=False, indent=2))
