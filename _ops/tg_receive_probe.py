#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tg_receive_probe.py — «تلگرام پیامی را نگه داشته که ما هرگز نگرفتیم؟»

مسئله‌ای که این ابزار برای آن ساخته شد (صبحِ ۲۰۲۶-۰۸-۰۱ — دو ساعت از دست رفت)
──────────────────────────────────────────────────────────────────────────────
وقتی بات از **دریافت** می‌افتد، تنها نشانه‌اش «غیاب» است. ارسال سالم می‌ماند،
دکمه‌ها هنوز رندر می‌شوند، لاگِ ارسال هنوز پر است — پس از بیرون یک باتِ کر و یک
صبحِ ساکت **دقیقاً یک شکل** دارند. تنها راهِ تفکیک این است که از خودِ تلگرام
بپرسیم چیزی برای ما معطل مانده یا نه.

فایلِ سلامتِ poll (از ۰۸-۰۱ در `tg_api._record_poll`) نیمِ **اول** را جواب
می‌دهد: «دورِ getUpdates ِ *ما* موفق بود؟». نیمِ دوم را جواب نمی‌دهد:

    · اگر پروسهٔ ما اصلاً بالا نباشد، آن فایل فقط کهنه می‌شود و چیزی نمی‌گوید.
    · اگر یک pollerِ **رقیب** (webhook یا دستگاهِ دیگر) آپدیت‌ها را ببلعد،
      دورهای ما می‌توانند «موفق و خالی» باشند در حالی که پیامِ مالک رفته است.

`getWebhookInfo` دقیقاً همان نیمِ دوم است: read-only، و برخلافِ `getUpdates`
**هیچ آپدیتی مصرف نمی‌کند**. این ابزار دو نما را کنارِ هم می‌گذارد تا قابلِ
مقایسه شوند — نه یکی به‌جای دیگری.

قواعدِ سختِ این ابزار (هر کدام تستِ خودش را دارد)
─────────────────────────────────────────────────
⛔️ **هرگز getUpdates نمی‌زند.** تنها یک pollerِ مشروع وجود دارد؛ یک getUpdates ِ
   کنجکاوانه از این‌جا، «سلام» مالک را از دهانِ آن پولر می‌دزدد و برای همیشه
   ناپدید می‌کند. متدها allowlist ِ ساختاری دارند (`_build_url`).
⛔️ **توکن فقط از `os.environ`.** نه `.env` خوانده می‌شود، نه هیچ فایلِ secret،
   نه هیچ fallback ِ «شاید جای دیگری باشد». نبودِ متغیر ⇒ همان را صریح بگو و
   برو. (رأیِ مالک، سوالِ ۶ ِ AGENT_QUESTIONS، ۰۸-۰۱.)
⛔️ **توکن هرگز چاپ/لاگ/ذخیره نمی‌شود** — حتی mask‌شده. و چون تلگرام می‌تواند
   خودش توکن را در `url` ِ webhook به ما پس بدهد (الگوی رایجِ webhook همان
   `/bot<token>/…` است)، یک scrub ِ نهایی روی کلِ خروجی هست، نه فقط اعتماد به
   این‌که «ما که چاپش نمی‌کنیم».
⛔️ **صفر نوشتن، صفر ارسال.** هیچ فایلی از state ِ ارگانیسم لمس نمی‌شود مگر
   خواندنِ poll-health. اجرا در هر لحظه‌ای بی‌خطر است.

«نمی‌دانم» هرگز «سالم» گزارش نمی‌شود: نبودِ توکن، شبکهٔ خراب، یا فایلِ غایبِ
سلامت ⇒ خروجیِ ۲ (نامعلوم)، نه ۰.

اجرا (فقط مالک):
    python -X utf8 _ops/tg_receive_probe.py
    python -X utf8 _ops/tg_receive_probe.py --json
    python -X utf8 _ops/tg_receive_probe.py --timeout 15

کدِ خروج: 0 پاک · 1 نشانهٔ بد · 2 نامعلوم
   ۲ یعنی یا هیچ باتی پروب نشد، یا باتی که توکن داشت جوابِ روشنی نداد. یک باتِ
   سالم، «نمی‌دانم» ِ باتِ دیگر را نمی‌پوشاند.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

SCHEMA = "tg-receive-probe.v1"
TELEGRAM_API_BASE = "https://api.telegram.org"   # تنها میزبانِ مجاز

# ── allowlist ِ ساختاری: فقط دو متدِ خواندنی. getUpdates عمداً این‌جا نیست و
#    هرگز نباید اضافه شود — مصرف‌کنندهٔ مشروعش یکی است و بس. ─────────────────
ALLOWED_METHODS = frozenset({"getMe", "getWebhookInfo"})

# باتِ زنده‌ای که «دریافت» برایشان معنا دارد (BOTS-REGISTRY.md، ردیفِ ۱ و ۲).
# ساختار: (نامِ متغیرِ محیطی، نامِ بات، نقش)
BOTS = (
    ("TELEGRAM_BOT_TOKEN", "باتِ یکپارچهٔ اختاپوس", "پولرِ تأیید/دکمه‌ها"),
    ("TG_CENTER_BOT_TOKEN", "باتِ مرکزِ تلگرام", "مرکزِ فرمانِ گروه"),
)

DEFAULT_TIMEOUT_S = 8.0
PENDING_BACKLOG_RED = 3      # این تعداد پیامِ معطل = دیگر «نوسان» نیست
STALE_ROUND_S = 120.0        # ~۵ دورِ longpoll: نویسنده ساکت شده ⇒ پولر نمی‌دود
DEAF_AFTER_S = 300.0         # آینهٔ tg_api.POLL_DEAF_AFTER_S (اگر import شد، از خودش)
FAILURES_RED = 2             # یک لرزشِ تکی الگو نیست؛ دومی هست
_MIN_SECRET_LEN = 8          # کوتاه‌تر از این را scrub نکن (خطرِ خرابیِ متن)
_REDACTED = "▮REDACTED▮"

# حکم‌ها: کلیدِ ASCII برای JSON، رندرِ فارسی در _VERDICT_FA
BAD_VERDICTS = frozenset({"auth_failed", "webhook_hijack", "deaf", "backlog", "tg_error"})
UNKNOWN_VERDICTS = frozenset({"no_token", "unreachable"})

_VERDICT_FA = {
    "ok": "✅ سالم — تلگرام چیزی معطل ندارد",
    "no_token": "⬜ نامعلوم — متغیرِ محیطی ست نیست",
    "unreachable": "⬜ نامعلوم — تلگرام جواب نداد",
    "auth_failed": "⛔ توکن احراز نشد (باطل/اشتباه؟)",
    "webhook_hijack": "⛔ webhook ست است — getUpdates ِ ما هرگز چیزی نمی‌گیرد",
    "deaf": "🔴 کر — تلگرام پیام نگه داشته و پولرِ ما سالم نیست",
    "backlog": "🟠 صف — تلگرام پیام نگه داشته",
    "tg_error": "🟠 تلگرام یک خطا ثبت کرده",
}

_HEALTH_FA = {
    "ok": "✅ دورِ موفقِ تازه",
    "failing": "🔴 دورها شکست می‌خورند",
    "silent": "🔴 نویسنده ساکت است — پولر احتمالاً اصلاً نمی‌دود",
    "unknown": "⬜ نامعلوم",
    "not_covered": "⬜ پوشش ندارد — این فایل را پولرِ این بات نمی‌نویسد",
}


# ─── لولهٔ HTTP (فقط خواندنی) ────────────────────────────────────────────────
def _build_url(token: str, method: str, params: dict | None = None) -> str:
    """URL ِ Bot API. متدِ خارج از allowlist ⇒ ValueError — نه fail-soft.

    این تنها گاردی است که «getUpdates زده نشود» را **ساختاری** می‌کند: هیچ
    مسیرِ کدی نمی‌تواند تصادفاً یا با یک آرگومانِ اشتباه به آن برسد. عمداً
    استثنا پرتاب می‌کند (نه return ِ خالی) تا خطا بلند و دیده‌شدنی باشد.
    URL هرگز نباید لاگ شود — توکن داخلش است."""
    if method not in ALLOWED_METHODS:
        raise ValueError(f"probe: متدِ غیرمجاز {method!r} — این ابزار فقط خواندنی است")
    q = urllib.parse.urlencode(params or {})
    return f"{TELEGRAM_API_BASE}/bot{token}/{method}" + (f"?{q}" if q else "")


def _url_json_get(url: str, timeout_s: float) -> dict:
    """getter ِ پیش‌فرض. تنها میزبانِ مجاز api.telegram.org. URL هرگز لاگ نمی‌شود."""
    if not url.startswith(TELEGRAM_API_BASE + "/"):
        raise ValueError("blocked host (only api.telegram.org)")
    req = urllib.request.Request(url, headers={"User-Agent": "octopus-receive-probe/0.1"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — only TELEGRAM_API_BASE
        return json.loads(resp.read().decode("utf-8"))


def _api(token: str, method: str, get_fn, timeout_s: float) -> dict:
    """یک تماسِ خواندنی. هر خطا ⇒ {"_transport_error": "<ClassName>"} — هرگز
    متنِ خطا برنمی‌گردد چون متنِ خطای urllib می‌تواند URL (و پس توکن) داشته باشد.

    ⚠️ `_build_url` عمداً **بیرونِ** try است. تخطیِ allowlist باید بلند بشکند،
    ولی خطای سمتِ ترابری باید «نامعلوم» شود نه crash — و قبلاً یک
    `except ValueError: raise` هر دو را یکی می‌شمرد. چون `json.JSONDecodeError`
    و `UnicodeDecodeError` هر دو زیرشاخهٔ ValueError اند، یک پاسخِ غیرِJSON
    (پورتالِ اسیرِ وای‌فای، ۵۰۲ ِ HTML ِ یک پراکسی، بایتِ خراب) کلِ ابزار را با
    traceback می‌کشت — دقیقاً در همان لحظه‌ای که ابزار برای آن ساخته شده."""
    url = _build_url(token, method)
    try:
        data = get_fn(url, timeout_s)
    except Exception as e:  # noqa: BLE001
        return {"_transport_error": type(e).__name__}
    return data if isinstance(data, dict) else {"_transport_error": "BadPayload"}


# ─── توکن: فقط os.environ، بدونِ هیچ جست‌وجوی دیگری ──────────────────────────
def _token_from_env(env_var: str, environ=None) -> str:
    """توکن از متغیرِ محیطی — و بس.

    عمداً **هیچ** fallback ِ فایلی ندارد: نه `.env`، نه flags.cmd، نه هیچ
    مسیرِ secret. اگر ست نباشد رشتهٔ خالی برمی‌گردد و صداکننده صریح گزارش
    می‌دهد. (این تابع نباید هرگز چیزی باز کند — تستِ حسابرسیِ فایل همین را
    قفل می‌کند.)"""
    env = os.environ if environ is None else environ
    v = env.get(env_var, "")
    return v.strip() if isinstance(v, str) else ""


def _live_tokens(environ=None) -> list[str]:
    """رشته‌هایی که هرگز نباید در خروجی دیده شوند — برای scrub ِ نهایی.

    شاملِ خودِ توکن، شکلِ URL-encoded ِ آن (توکن `:` دارد ⇒ `%3A`)، و نیمهٔ
    محرمانه‌اش به‌تنهایی (`<id>:<secret>`؛ نیمهٔ دوم است که راز است). بلندترین
    اول، تا جایگزینی زیرمجموعه‌ای متن را تکه‌تکه نکند."""
    env = os.environ if environ is None else environ
    out: list[str] = []
    for env_var, _, _ in BOTS:
        tok = _token_from_env(env_var, env)
        if len(tok) < _MIN_SECRET_LEN:
            continue
        out.append(tok)
        out.append(urllib.parse.quote(tok, safe=""))
        half = tok.split(":", 1)[-1]
        if len(half) >= _MIN_SECRET_LEN:
            out.append(half)
    return sorted(set(out), key=len, reverse=True)


def scrub_secrets(text: str, environ=None) -> tuple[str, int]:
    """آخرین سد. (متنِ پاک، تعدادِ نشتیِ گرفته‌شده) برمی‌گرداند.

    چرا لازم است با وجودِ این‌که «ما که چاپش نمی‌کنیم»: `getWebhookInfo` مقدارِ
    `url` را همان‌طور که ست شده پس می‌دهد، و الگوی متعارفِ webhook ِ تلگرام
    خودِ توکن را داخلِ مسیر می‌گذارد (`https://host/bot<token>/hook`). یعنی
    راهی وجود دارد که توکن از **سمتِ تلگرام** واردِ گزارش شود."""
    hits = 0
    for secret in _live_tokens(environ):
        if secret and secret in text:
            hits += text.count(secret)
            text = text.replace(secret, _REDACTED)
    return text, hits


# ─── نمای محلی: فایلِ سلامتِ poll (فقط خواندن) ───────────────────────────────
def _tg_api():
    """import ِ تنبلِ tg_api — تا مسیرِ فایل و آستانه از **خودِ نویسنده** بیاید،
    نه از یک کپیِ که فردا drift می‌کند. هر شکست ⇒ None (fail-soft)."""
    try:
        from telegram_center import tg_api  # noqa: PLC0415
        return tg_api
    except Exception:  # noqa: BLE001
        return None


def local_poll_health(path=None, now: float | None = None) -> dict:
    """نمای محلی: پولرِ خودمان چه می‌گوید؟ فقط خواندن — صفر نوشتن.

    سه چیزِ متفاوت تفکیک می‌شود، چون قاطی‌کردنشان همان اشتباهِ اول است:
      · `unknown`  فایل نیست/خراب است ⇒ نمی‌دانیم (هرگز «سالم»)
      · `silent`   فایل هست ولی **کسی تازه ننوشته** ⇒ پولر نمی‌دود
      · `failing`  می‌دود ولی دورهایش شکست می‌خورند

    ترتیب عمدی است: یک پروسه که درست بعد از یک دورِ موفق مرده، فایلی با
    `last_ok_ts` ِ کاملاً سالم جا می‌گذارد. اگر فقط `last_ok_ts` را نگاه کنیم،
    یک بات مرده «✅ سالم» گزارش می‌شود — همان سبزِ ناشی از غیاب."""
    api = _tg_api()
    deaf_after = float(getattr(api, "POLL_DEAF_AFTER_S", DEAF_AFTER_S) or DEAF_AFTER_S)
    src = "explicit"
    if path is None:
        if api is None:
            return {"source": "unavailable", "status": "unknown", "file_present": False,
                    "deaf_after_s": deaf_after,
                    "note": "tg_api قابلِ import نبود — مسیرِ فایل نامعلوم"}
        path = api._poll_health_path()
        src = "tg_api"

    from pathlib import Path as _P
    p = _P(path)
    out = {"source": src, "path_name": p.name, "deaf_after_s": deaf_after,
           "file_present": False, "status": "unknown", "last_ok_age_s": None,
           "last_round_age_s": None, "consecutive_failures": None, "last_reason": ""}
    try:
        state = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return out
    if not isinstance(state, dict):
        return out
    out["file_present"] = True
    ts_now = float(now if now is not None else time.time())
    last_ok = float(state.get("last_ok_ts") or 0.0)
    last_round = float(state.get("last_round_ts") or 0.0)
    fails = int(state.get("consecutive_failures") or 0)
    out["consecutive_failures"] = fails
    out["last_reason"] = str(state.get("last_reason") or "")[:80]
    out["last_ok_age_s"] = max(0.0, ts_now - last_ok) if last_ok > 0 else None
    out["last_round_age_s"] = max(0.0, ts_now - last_round) if last_round > 0 else None

    if out["last_round_age_s"] is not None and out["last_round_age_s"] > STALE_ROUND_S:
        out["status"] = "silent"
    elif fails >= FAILURES_RED:
        out["status"] = "failing"
    elif out["last_ok_age_s"] is None:
        out["status"] = "unknown"        # بوتی که هرگز موفق نشده = نمی‌دانیم
    elif out["last_ok_age_s"] > deaf_after:
        out["status"] = "failing"
    else:
        out["status"] = "ok"
    return out


def health_owner_env(environ=None) -> str:
    """کدام بات فایلِ poll-health را می‌نویسد؟

    آینهٔ دقیقِ منطقِ `tg_api.TgClient.__init__`: اگر `TG_CENTER_BOT_TOKEN` ست
    باشد نویسنده اوست، وگرنه fallback به `TELEGRAM_BOT_TOKEN`. بدونِ این،
    نمای محلی به بات**ی** چسبانده می‌شد که هرگز آن را ننوشته — یعنی گزارشی که
    مؤدبانه دروغ می‌گوید."""
    if _token_from_env("TG_CENTER_BOT_TOKEN", environ):
        return "TG_CENTER_BOT_TOKEN"
    return "TELEGRAM_BOT_TOKEN"


# ─── پروبِ یک بات ────────────────────────────────────────────────────────────
def _clean(raw, environ, out: dict, cap: int = 200) -> str:
    """هر رشته‌ای که از **سمتِ تلگرام** می‌آید از این‌جا رد می‌شود.

    `description` و `last_error_message` را تلگرام می‌نویسد، نه ما — و هر دو
    می‌توانند URL ِ درخواست/webhook را داخل خود داشته باشند. یعنی رشتهٔ ورودیِ
    غیرِقابلِ‌اعتماد؛ در سرچشمه scrub می‌شود تا ساختارِ گزارش هرگز آلوده نشود.

    ⚠️ ترتیب حیاتی است: **اول scrub، بعد بریدن.** عکسش (که اول نوشته شده بود)
    یک نشتیِ بی‌صدا داشت — توکنی که روی مرزِ `cap` می‌افتاد نصف می‌شد، دیگر با
    هیچ‌کدام از الگوهای `_live_tokens` برابر نبود، و ۱۷ کاراکترِ اولِ نیمهٔ
    محرمانه با `secret_redactions == 0` چاپ می‌شد؛ یعنی گزارش می‌گفت «نشتی
    نبود» در حالی که تکهٔ راز روی صفحه بود."""
    v, n = scrub_secrets(str(raw or ""), environ)
    out["secret_redactions"] = int(out.get("secret_redactions") or 0) + n
    return v[:cap]


def probe_bot(env_var: str, name: str = "", role: str = "", get_fn=None,
              timeout_s: float = DEFAULT_TIMEOUT_S, environ=None) -> dict:
    """یک بات: احراز هویت + صفِ معطلِ سمتِ تلگرام. صفر ارسال، صفر getUpdates.

    خروجی هرگز توکن ندارد — حتی mask‌شده. `webhook_url` هم برنگردانده می‌شود
    (فقط host)، چون مسیرش می‌تواند خودِ توکن باشد."""
    out = {"env_var": env_var, "name": name, "role": role,
           "token_present": False, "auth": "skipped", "username": "",
           "pending_update_count": None, "webhook_url_set": None,
           "webhook_host": "", "last_error_message": "", "last_error_age_s": None,
           "transport_error": "", "secret_redactions": 0}
    token = _token_from_env(env_var, environ)
    if not token:
        return out
    out["token_present"] = True
    get_fn = get_fn or _url_json_get

    me = _api(token, "getMe", get_fn, timeout_s)
    if me.get("_transport_error"):
        out["auth"] = "unreachable"
        out["transport_error"] = str(me["_transport_error"])
        return out
    if not me.get("ok"):
        out["auth"] = "failed"
        out["transport_error"] = _clean(me.get("description"), environ, out, 120)
        return out
    out["auth"] = "ok"
    out["username"] = _clean((me.get("result") or {}).get("username"), environ, out, 64)

    info = _api(token, "getWebhookInfo", get_fn, timeout_s)
    if info.get("_transport_error"):
        out["transport_error"] = str(info["_transport_error"])
        return out
    if not info.get("ok"):
        out["transport_error"] = _clean(info.get("description"), environ, out, 120)
        return out
    res = info.get("result") or {}
    try:
        out["pending_update_count"] = int(res.get("pending_update_count") or 0)
    except (TypeError, ValueError):
        out["pending_update_count"] = None
    hook = str(res.get("url") or "")
    out["webhook_url_set"] = bool(hook)
    if hook:
        try:
            netloc = urllib.parse.urlsplit(hook).netloc
        except ValueError:
            netloc = "?"
        # «فقط host برمی‌گردانیم» به‌تنهایی کافی نیست: netloc می‌تواند userinfo
        # داشته باشد (`https://user:<token>@host/hook` یک webhook ِ کاملاً مجاز
        # است)، و آن‌وقت توکن از راهِ host واردِ ساختارِ گزارش می‌شود بدونِ آن‌که
        # هیچ شمارنده‌ای بالا برود. پس این هم از سرچشمه رد می‌شود.
        out["webhook_host"] = _clean(netloc, environ, out, 120)
    # scrub در **سرچشمه**، نه فقط موقعِ چاپ: متنِ خطای تلگرام می‌تواند URL ِ
    # webhook (و پس توکن) داشته باشد، و آن‌وقت خودِ ساختارِ گزارش آلوده است —
    # هر مصرف‌کنندهٔ بعدی (JSON، لاگ، کارتِ تلگرام) بی‌گناه پخشش می‌کند.
    out["last_error_message"] = _clean(res.get("last_error_message"), environ, out)
    try:
        led = float(res.get("last_error_date") or 0)
        if led > 0:
            out["last_error_age_s"] = max(0.0, time.time() - led)
    except (TypeError, ValueError):
        pass
    return out


def verdict(bot: dict, health: dict) -> str:
    """حکمِ یک بات از ترکیبِ **دو** نما. ترتیب از قطعی‌ترین به مبهم‌ترین."""
    if not bot.get("token_present"):
        return "no_token"
    if bot.get("auth") == "unreachable":
        return "unreachable"
    if bot.get("auth") != "ok":
        return "auth_failed"
    if bot.get("webhook_url_set"):
        return "webhook_hijack"
    pending = bot.get("pending_update_count")
    if pending is None:
        return "unreachable"
    if pending >= 1 and health.get("status") in ("failing", "silent"):
        return "deaf"
    if pending >= PENDING_BACKLOG_RED:
        return "backlog"
    if bot.get("last_error_message"):
        return "tg_error"
    return "ok"


def build_report(get_fn=None, environ=None, timeout_s: float = DEFAULT_TIMEOUT_S,
                 now: float | None = None, health=None) -> dict:
    """گزارشِ کامل. صفر نوشتن، صفر ارسال، صفر getUpdates."""
    ts = float(now if now is not None else time.time())
    local = local_poll_health(now=ts) if health is None else dict(health)
    owner_env = health_owner_env(environ)
    bots = []
    for env_var, name, role in BOTS:
        b = probe_bot(env_var, name, role, get_fn=get_fn, timeout_s=timeout_s,
                      environ=environ)
        # نمای محلی فقط به باتی چسبانده می‌شود که واقعاً نویسنده‌اش است.
        b["local"] = dict(local) if env_var == owner_env else {
            "status": "not_covered", "source": "n/a",
            "note": f"نویسندهٔ poll-health باتِ {owner_env} است"}
        b["verdict"] = verdict(b, b["local"])
        bots.append(b)

    # دو متغیرِ محیطی که به **یک** بات اشاره کنند = جنگِ ۴۰۹: هر دو پولر
    # getUpdates می‌زنند و هرکدام آپدیتِ دیگری را می‌بلعد. این دقیقاً یکی از
    # شکل‌های «نمی‌شنویم» است، و از راهِ username بدونِ هیچ نشتی دیده می‌شود.
    seen: dict[str, list[str]] = {}
    for b in bots:
        if b.get("username"):
            seen.setdefault(b["username"], []).append(b["env_var"])
    shared = sorted(u for u, evs in seen.items() if len(evs) > 1)

    return {"schema": SCHEMA, "ts": ts,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)),
            "health_owner_env": owner_env, "local_poll_health": local,
            "bots": bots, "shared_bot_usernames": shared,
            "secret_leaks_redacted": sum(int(b.get("secret_redactions") or 0)
                                         for b in bots)}


def exit_code(report: dict) -> int:
    """0 پاک · 1 نشانهٔ بد · 2 نامعلوم. «نمی‌دانم» هرگز ۰ نمی‌شود."""
    bots = report.get("bots") or []
    verdicts = [b.get("verdict") for b in bots]
    if report.get("shared_bot_usernames"):
        return 1
    if any(v in BAD_VERDICTS for v in verdicts):
        return 1
    # باتی که توکن **دارد** ولی پروبش شکست خورده، یک «نمی‌دانم» ِ واقعی است و
    # سبزیِ باتِ دیگر نباید بپوشاندش: کدِ خروج تنها کانالِ ماشین‌خوانِ ماست و
    # ۰ یعنی «پرسیدم و پاک بود». نبودِ توکن فرق دارد — چیزی برای پرسیدن نبوده،
    # و مالک ممکن است عمداً فقط یک بات را ست کرده باشد.
    if any(b.get("token_present") and b.get("verdict") in UNKNOWN_VERDICTS
           for b in bots):
        return 2
    if not any(v == "ok" for v in verdicts):
        return 2
    return 0


# ─── رندرِ فارسی ─────────────────────────────────────────────────────────────
def _fmt_age(sec) -> str:
    if sec is None:
        return "—"
    s = int(sec)
    if s < 90:
        return f"{s} ثانیه"
    if s < 5400:
        return f"{s // 60} دقیقه"
    return f"{s // 3600} ساعت و {(s % 3600) // 60} دقیقه"


def _render_health(h: dict) -> list[str]:
    st = h.get("status", "unknown")
    lines = [f"   نمای محلی (poll-health): {_HEALTH_FA.get(st, st)}"]
    if h.get("note"):
        lines.append(f"      · {h['note']}")
    if st in ("ok", "failing", "silent"):
        lines.append(f"      · آخرین دورِ موفق: {_fmt_age(h.get('last_ok_age_s'))} پیش")
        lines.append(f"      · آخرین دورِ ثبت‌شده: {_fmt_age(h.get('last_round_age_s'))} پیش")
        lines.append(f"      · شکستِ پیاپی: {h.get('consecutive_failures')}"
                     + (f" ({h['last_reason']})" if h.get("last_reason") else ""))
    return lines


def render(report: dict, environ=None) -> str:
    out = [f"🎧 پروبِ دریافتِ تلگرام — {report.get('generated_at', '')}",
           "   فقط getMe + getWebhookInfo · صفر getUpdates · صفر ارسال · صفر نوشتن",
           ""]
    for b in report.get("bots") or []:
        out.append(f"━━ {b.get('name') or b['env_var']} — {b.get('role', '')}")
        out.append(f"   متغیرِ محیطی: {b['env_var']}")
        if not b.get("token_present"):
            out.append("   توکن در env: ❌ ست نیست")
            out.append("      · این ابزار عمداً جای دیگری دنبالش نمی‌گردد "
                       "(نه .env، نه هیچ فایلِ secret).")
            out.append(f"      · برای پروب: {b['env_var']} را در همین شل ست کن.")
            out.append(f"   حکم: {_VERDICT_FA.get(b['verdict'], b['verdict'])}")
            out.append("")
            continue
        out.append("   توکن در env: ✅")
        auth = b.get("auth")
        if auth == "ok":
            out.append(f"   احراز هویت: ✅ @{b.get('username') or '?'}")
        elif auth == "unreachable":
            out.append(f"   احراز هویت: ⬜ تلگرام جواب نداد ({b.get('transport_error')})")
        else:
            out.append(f"   احراز هویت: ⛔ رد شد ({b.get('transport_error') or '—'})")
        if b.get("pending_update_count") is not None:
            out.append(f"   معطل نزدِ تلگرام (pending_update_count): "
                       f"{b['pending_update_count']}")
        if b.get("webhook_url_set") is not None:
            out.append("   webhook: " + (f"⛔ ست است روی {b.get('webhook_host') or '?'}"
                                          if b["webhook_url_set"] else "✅ ست نیست"))
        if b.get("last_error_message"):
            # تلگرام گاهی متنِ خطا می‌دهد ولی تاریخ نه ⇒ «(— پیش)» ِ بی‌معنی
            # چاپ نشود؛ نبودِ تاریخ را با سکوت نشان بده، نه با خط تیره.
            age = b.get("last_error_age_s")
            out.append(f"   آخرین خطای ثبت‌شدهٔ تلگرام: {b['last_error_message']}"
                       + (f"  ({_fmt_age(age)} پیش)" if age is not None else ""))
        out.extend(_render_health(b.get("local") or {}))
        out.append(f"   حکم: {_VERDICT_FA.get(b['verdict'], b['verdict'])}")
        out.append("")

    if report.get("shared_bot_usernames"):
        out.append("⛔ دو متغیرِ محیطی به یک بات اشاره می‌کنند: "
                   + "، ".join("@" + u for u in report["shared_bot_usernames"]))
        out.append("   دو پولر روی یک بات = ۴۰۹ و بلعیدنِ آپدیتِ همدیگر.")
        out.append("")

    out.append("راهنمای خواندن:")
    out.append("   pending>0 + نمای محلیِ قرمز ⇒ تلگرام دارد نگه می‌دارد و ما نمی‌گیریم.")
    out.append("   pending=0 + نمای محلیِ سبز  ⇒ واقعاً کسی پیام نداده.")
    out.append("   «نامعلوم» یعنی نامعلوم — سالم نیست.")
    text, leaks = scrub_secrets("\n".join(out), environ)
    total = int(report.get("secret_leaks_redacted") or 0) + leaks
    if total:
        text += (f"\n\n⚠️ {total} رخدادِ توکن پیدا و redact شد "
                 "(احتمالاً از url ِ webhook که خودِ تلگرام پس داده). "
                 "webhook را بدونِ توکن در مسیر بساز.")
    return text


def render_json(report: dict, environ=None) -> str:
    """JSON ِ scrub‌شده. هشدارِ نشتی **داخلِ** سند می‌رود، نه چسبیده به دمش —
    وگرنه خروجی دیگر JSON ِ معتبر نیست و هر مصرف‌کننده‌ای می‌شکند."""
    text, leaks = scrub_secrets(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), environ)
    if leaks:
        rep = dict(report)
        rep["secret_leaks_redacted"] = int(rep.get("secret_leaks_redacted") or 0) + leaks
        text, _ = scrub_secrets(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str), environ)
    return text


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    timeout = DEFAULT_TIMEOUT_S
    if "--timeout" in argv:
        try:
            timeout = float(argv[argv.index("--timeout") + 1])
        except (IndexError, ValueError):
            print("--timeout یک عدد می‌خواهد", file=sys.stderr)
            return 2
    missing = [ev for ev, _, _ in BOTS if not _token_from_env(ev)]
    if len(missing) == len(BOTS):
        print("هیچ توکنی در محیط نیست: " + "، ".join(missing))
        print("این ابزار فقط os.environ را می‌خواند و عمداً دنبالِ .env نمی‌گردد.")
        print("«نمی‌دانم» ≠ «سالم» — خروجی ۲.")
        return 2
    report = build_report(timeout_s=timeout)
    print(render_json(report) if "--json" in argv else render(report))
    return exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
