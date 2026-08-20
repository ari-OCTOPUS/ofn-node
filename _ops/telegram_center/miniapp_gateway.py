#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""miniapp_gateway — دیوارِ 8774 برای Mini App (PLAN-T4 §۱–۳؛ GO ِ مالک ۲۰۲۶-۰۷-۳۱).

    تونل **هرگز** مستقیم به 8773 نمی‌خورد. این gateway تنها مقصدِ تونل است:
    bind فقط 127.0.0.1:8774 · اول اعتبارسنجیِ initData، بعد حتی یک بایت داده.

مسیرها (بسته — هرچیزِ دیگر 404، هر متدِ غیرِ GET 405):
    · GET /miniapp      → شِلِ HTML از 8773 (بدونِ نیازِ initData؛ صفر داده) +
      تزریقِ اسنیپتِ JS که initData ِ تلگرام را روی هر fetch در هدر
      `X-Tg-Init-Data` می‌گذارد.
    · GET /api/miniapp  → فقط با initData ِ معتبر (HMAC طبق §۲ ِ طرح)؛ proxy
      از 8773 و **دوباره** از redaction رد می‌شود (دفاعِ دولایه).

دیوارِ §۲ (هر شکست = 403 با بدنهٔ خالی، بدونِ پیامِ اطلاعات‌دِه):
    secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token) ·
    hash روی data-check-string ِ مرتبِ الفبایی با hmac.compare_digest ·
    auth_date ≤ ۳۰۰ ثانیه · user.id == TELEGRAM_OWNER_CHAT_ID.

کلیدِ کشتار: فایلِ STOP-MINIAPP زیرِ _ops — در **هر** درخواست چک می‌شود → 503.
flag ِ OCTOPUS_TG_MINIAPP (پیش‌فرض خاموش) فقط شروعِ حلقهٔ serve را می‌گیرد.
توکن فقط از env (TG_CENTER_BOT_TOKEN) — هرگز روی دیسک/لاگ/URL نمی‌رود.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_MINIAPP_DIR = _HERE / "miniapp"
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_MINIAPP"
PORT = int(os.environ.get("OCTOPUS_MINIAPP_PORT", "8774"))
UPSTREAM_PORT = int(os.environ.get("LIVE_PORT", "8773"))
# Telegram initData is a short-lived bootstrap credential, not a session and
# not replay protection. All direct initData requests use the same strict TTL;
# a future server-side session must be issued only after this validation.
INITDATA_TTL_S = float(os.environ.get("OCTOPUS_MINIAPP_INITDATA_TTL_S", "300") or "300")
MAX_FUTURE_SKEW_S = float(os.environ.get("OCTOPUS_MINIAPP_FUTURE_SKEW_S", "30") or "30")
# Backward-compatible name for callers/tests; it now reflects the strict TTL.
AUTH_MAX_AGE_S = INITDATA_TTL_S
STOP_NAME = "STOP-MINIAPP"

# ۲۰۲۶-۰۸-۰۸: مهلتِ زمانیِ سقف برای مسیرهای غیر-خواندنی. ThreadingHTTPServer هر
# درخواست را در thread جدا می‌کند، ولی یک LLM hang همچنان یک thread را برای همیشه
# نگه می‌دارد و به‌مرور منابع را نشت می‌دهد. این سقف ضامنِ آن است که هیچ درخواستی
# بیش از این ثانیه معلق نماند — پس از آن، یک 504 (Gateway Timeout) تمیز برمی‌گردد.
# ۲۰۲۶-۰۸-۱۲: DeepSeek + self-context گاهی ۲۰–۴۰ث؛ کلاینت ۶۰ث است.
ASK_TIMEOUT_S = float(os.environ.get("OCTOPUS_MINIAPP_ASK_TIMEOUT", "45.0"))
ASK_BRAIN_TIMEOUT_S = float(os.environ.get("OCTOPUS_MINIAPP_ASK_BRAIN_TIMEOUT", "8.0"))
COLLAB_TIMEOUT_S = float(os.environ.get("OCTOPUS_MINIAPP_COLLAB_TIMEOUT", "55.0"))
ACTIONS_TIMEOUT_S = float(os.environ.get("OCTOPUS_MINIAPP_ACTIONS_TIMEOUT", "15.0"))
MIRROR_TIMEOUT_S = float(os.environ.get("OCTOPUS_MINIAPP_MIRROR_TIMEOUT", "45.0"))

# سطحِ فقط‌خواندنی (secret-scrubbed در miniapp_state، دوباره redact در همین فایل).
# **تک‌فهرست** است نه دو کپی: زیرمسیرهای /api/ops دقیقاً از همان درِ والدشان رد
# می‌شوند، پس ساختاراً نمی‌توانند بازتر باشند — سوراخِ «اندپوینتِ تازهٔ بی‌گارد»
# با قاعده بسته می‌شود نه با یادآوری.
READ_API_PATHS = {
    "/api/state", "/api/outbound", "/api/approvals", "/api/legs",
    # ۲۰۲۶-۰۸-۰۷: تبِ هفتم (اعلان‌ها/notif_inbox). همان درِ owner-auth، بدونِ استثنا.
    "/api/notifications",
    "/api/value", "/api/ui-registry", "/api/current-truth",
    "/api/ops", "/api/ops/brain", "/api/ops/leads", "/api/ops/tasks",
    # ۲۰۲۶-۰۸-۰۴: دو تابعِ یتیمِ `miniapp_state` که مسیر نداشتند و تبِ
    # متناظرشان بی‌داده مانده بود. همان درِ owner-auth، بدونِ استثنا.
    "/api/governor", "/api/obsidian",
    # ۲۰۲۶-۰۸-۰۵: نقشهٔ خودآگاهی (دسترسیِ زمانِ اجرا + اسکن‌های ایستا).
    # همان درِ owner-auth، بدونِ استثنا.
    "/api/selfmap",
    # نمایِ lifecycle (miniapp_state.get_lifecycle_state، پشتِ OCTOPUS_PF_MINIAPP).
    # برشِ ۳ این مسیر را هنگامِ بستنِ route های read جا انداخته بود: handler در
    # miniapp_state.py هست ولی هرگز dispatch نمی‌شد → 404 حتی با فلگِ روشن.
    # تاشویِ یکسانِ gate ِ owner-auth (t_no_read_route_bypasses_the_shared_gate_function).
    "/api/lifecycle",
    # ۲۰۲۶-۰۸-۰۸ — تبِ «اسکن‌ها»: شناختیِ زنده + لاگِ ایجنت
    "/api/cognitive-scan", "/api/agent-log",
    # 2026-08-12: ماتریس سقف پول (قدم ۵/۷) — read-only
    "/api/money-caps",
    # 2026-08-13 (ADR-039 C6): پنلِ فقط‌خواندنیِ epistemic — owner override
    "/api/epistemic",
    # 2026-08-13 (ADR-040 Phase 3): viewهای trace — runs + receipts
    "/api/octopus/runs", "/api/octopus/receipts",
}

# دیوارِ HMAC ِ سطحِ خواندنی: **هر** مسیرِ READ_API_PATHS همان چیزی را می‌خواهد
# که /api/miniapp می‌خواهد. VQ-OPEN-READ-API-001 (۲۰۲۶-۰۸-۰۳، برشِ ۳، آیتمِ ۱):
# پیش‌فرضِ قبلی خاموش بود — یعنی ۱۱ مسیر (شاملِ /api/approvals، /api/value)
# روی تونلِ عمومی صفر احرازِ owner داشتند، فقط با حدسِ URL ِ تونل. شِلِ
# mini-app از قبل initData را روی **هر** fetch می‌گذارد (`_INJECT`، پایین‌تر)،
# پس UI ِ واقعی هیچ اثری نمی‌بیند — فقط دسترسیِ بی‌احرازِ بیرونی بسته می‌شود.
# برای بازگشتِ صریح به رفتارِ قدیم (نبایدِ owner-decision، نه پیش‌فرض): این env
# را به "0" ست کن.
READ_GATE_FLAG = "OCTOPUS_MINIAPP_READ_OWNER_GATE"

# 2026-08-07 deep-scan follow-up: owner-auth is not a spam/replay limit.
# Keep POST /api/actions fail-closed under a short in-memory window.
def _rate_limited(hits: list, lock: threading.RLock, window_s: float,
                  max_per_window: int, now: "float | None" = None) -> bool:
    """گیتِ عمومیِ rate-limit ِ درون‌حافظه‌ای — پایهٔ مشترکِ /api/actions و
    /api/ask (۲۰۲۶-۰۸-۰۸). هر مسیرِ POST شمارندهٔ خودش را دارد چون فروکشیدنِ
    مکالمه نباید یک تأییدِ real را قفل کند و برعکس."""
    t = float(now if now is not None else time.monotonic())
    with lock:
        cutoff = t - window_s
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= max_per_window:
            return True
        hits.append(t)
        return False


_ACTION_WINDOW_S = 10.0
_ACTION_MAX_PER_WINDOW = 12
_ACTION_HITS = []
_ACTION_LOCK = threading.RLock()


def _action_rate_limited(now: "float | None" = None) -> bool:
    """Short in-memory rate-limit for POST /api/actions."""
    return _rate_limited(_ACTION_HITS, _ACTION_LOCK, _ACTION_WINDOW_S,
                         _ACTION_MAX_PER_WINDOW, now)


# ۲۰۲۶-۰۸-۰۸: چت‌باکسِ /api/ask — پنجرهٔ جداگانه از /api/actions (سؤالِ
# پیاپی نباید تأییدِ واقعی را قفل کند). خودِ ask_vault/ask_brain هم سقفِ
# روزانه/quota ِ داخلیِ خودشان را دارند؛ این‌جا فقط ضدِ سوءاستفادهٔ خامِ
# سطحِ HTTP است (thread pool ِ gateway را حفظ می‌کند).
_ASK_WINDOW_S = 30.0
_ASK_MAX_PER_WINDOW = 6
_ASK_HITS = []
_ASK_LOCK = threading.RLock()


def _ask_rate_limited(now: "float | None" = None) -> bool:
    return _rate_limited(_ASK_HITS, _ASK_LOCK, _ASK_WINDOW_S, _ASK_MAX_PER_WINDOW, now)


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def read_gate_enabled() -> bool:
    # ۲۰۲۶-۰۸-۰۷ deep-scan: env=0 برای این گارد روی تونل عمومی خطرناک بود؛
    # برای تست/اشکال‌زدایی فقط با opt-in توسعه پذیرفته می‌شود. پیش‌فرض و prod fail-closed.
    if os.environ.get(READ_GATE_FLAG, "1") != "0":
        return True
    return os.environ.get("OCTOPUS_MINIAPP_ALLOW_UNAUTH_READ_DEV", "0") != "1"


# ⚠️ کپیِ import-امنِ الگوی redaction ِ 8773 (نه import ِ متقابل از live/server —
# پروسه/مسیرِ جدا نباید به آن گره بخورد). fail-closed: لایهٔ اصلی نبود →
# الگوهای سخت؛ متنِ خام هرگز بیرون نمی‌رود. الگوها با HARD_SECRET_PATTERNS ِ
# cockpit_readmodel هم‌راستا هستند.
_FALLBACK_SECRET = (
    r"\d{8,12}:AA[A-Za-z0-9_-]{30,}",      # توکن بات تلگرام
    r"sk-[A-Za-z0-9_-]{20,}",               # کلیدهای sk-*
    r"-----BEGIN [A-Z ]*KEY",               # PEM
    r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}",  # OAuth/API bearer
)
_FALLBACK_SOFT = (
    # PII نیست که کلِ بدنه را نابود کند؛ per-match کافی است و debuggability می‌ماند.
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "‹email:حذف‌شده›"),
)
_FALLBACK_BODY = "⚠️ محتوا حذف شد — لایهٔ redaction در دسترس نبود"


def _redact(text: str) -> str:
    try:
        _c = str(_OPS / "budget")
        if _c not in sys.path:
            sys.path.insert(0, _c)
        import cockpit_readmodel as crm
        return crm.redact(text)
    except Exception:  # noqa: BLE001 — fail-closed محلی
        import re as _re
        t = str(text or "")
        for pat in _FALLBACK_SECRET:
            if _re.search(pat, t):
                return _FALLBACK_BODY
        for pat, repl in _FALLBACK_SOFT:
            t = _re.sub(pat, repl, t)
        return _re.sub(r"\b[0-9a-fA-F]{64}\b", "‹hex64:حذف‌شده›", t)


def validate_init_data(init_data: str, *, bot_token: str, owner_id,
                       now: "float | None" = None) -> "dict | None":
    """اعتبارسنجیِ initData ِ Telegram WebApp طبق PLAN-T4 §۲.

    خروجی: dict ِ user در موفقیت؛ هر شکست (به هر دلیل) = None — صداکننده 403
    با بدنهٔ خالی می‌دهد و هیچ جزئیاتی لو نمی‌رود."""
    try:
        if not init_data or not bot_token or owner_id in (None, ""):
            return None
        pairs = parse_qsl(str(init_data), keep_blank_values=True)
        keys = [key for key, _ in pairs]
        # Duplicate keys make the signed interpretation ambiguous (dict() would
        # silently keep the last value). Ambiguity is rejected fail-closed.
        if len(keys) != len(set(keys)):
            return None
        data = dict(pairs)
        got_hash = data.pop("hash", "")
        if not got_hash:
            return None
        check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret_key = hmac.new(b"WebAppData", str(bot_token).encode("utf-8"),
                              hashlib.sha256).digest()
        calc = hmac.new(secret_key, check_string.encode("utf-8"),
                        hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, str(got_hash)):
            return None
        now = float(now if now is not None else time.time())
        auth_date = float(data.get("auth_date") or 0)
        age_s = now - auth_date
        if auth_date <= 0 or age_s > INITDATA_TTL_S or age_s < -MAX_FUTURE_SKEW_S:
            return None                                   # freshness only; mutation replay needs nonce
        user = json.loads(data.get("user") or "{}")
        if int(user.get("id")) != int(owner_id):
            return None                                   # allowlist تک‌نفره
        return user
    except Exception:  # noqa: BLE001 — شک = رد
        return None


# اسنیپتِ تزریقی به شِل: initData روی هر fetch + فلگ‌های UI غیرسری (برای پیش‌فرض همکار).
# فقط booleanهای غیرسری؛ هرگز توکن/secret.
def _build_inject_js() -> str:
    """Executable JS without HTML tags; also prepended to external app.js.

    فقط config flags (wire_collab/collab_use_model) — بدون fetch wrapper.
    ۲۰۲۶-۰۸-۱۲: fetch wrapper حذف شد چون با POST /api/collab تداخل داشت و
    باعث می‌شد X-Tg-Init-Data در POST گم شود. tgHeaders خودِ app.js کافی است.
    """
    import os as _os
    collab_js = "true" if _os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1" else "false"
    model_js = "true" if _os.environ.get("OCTOPUS_COLLAB_USE_MODEL", "0") == "1" else "false"
    return (
        "(function(){window.__OCTOPUS__=window.__OCTOPUS__||{};"
        f"window.__OCTOPUS__.wire_collab={collab_js};"
        f"window.__OCTOPUS__.collab_use_model={model_js};"
        "})();"
    )


def _build_inject() -> str:
    return "<script>" + _build_inject_js() + "</script>"


_INJECT = _build_inject()  # evaluated at import/boot so restart picks flag changes


def _miniapp_static_response(path: str) -> tuple:
    """Serve the committed read-only cockpit shell/assets from disk.
    Only an explicit allowlist is served; no path traversal and no directory
    listing. The page contains no secrets and all mutating actions remain
    disabled in the frontend/backend until owner auth is explicitly wired.
    """
    p = str(path or "").split("?", 1)[0]
    if p in ("/", "/miniapp", "/miniapp/"):
        rel = "index.html"
        ctype = "text/html; charset=utf-8"
    elif p in ("/miniapp/app.js", "/app.js"):
        rel = "app.js"
        ctype = "application/javascript; charset=utf-8"
    elif p in ("/miniapp/tg_shell.js", "/tg_shell.js"):
        # پوستهٔ Mini Apps 2.0 (فاز ۳). فایلِ جدا چون در node تست می‌شود؛
        # بدونِ این مدخل، `index.html` صدایش می‌زند و ۴۰۴ می‌گیرد — یعنی
        # هیچ‌کدام از قابلیت‌های ۲۰۲۶ روی گوشی بالا نمی‌آید و هیچ خطایی هم
        # دیده نمی‌شود جز یک تگِ script ِ شکست‌خورده در کنسول.
        rel = "tg_shell.js"
        ctype = "application/javascript; charset=utf-8"
    elif p in ("/miniapp/style.css", "/style.css"):
        rel = "style.css"
        ctype = "text/css; charset=utf-8"
    else:
        return 404, b"", "text/plain; charset=utf-8"
    f = _MINIAPP_DIR / rel
    try:
        body = f.read_bytes()
    except OSError:
        return 404, b"", "text/plain; charset=utf-8"
    if rel == "index.html":
        # ── ضدِکشِ تلگرام (۲۰۲۶-۰۸-۰۴) ────────────────────────────────────
        # مالک گزارش داد «هر تغییری می‌دهی هیچی نمی‌شود» در حالی که سرور
        # اثباتاً فایلِ نو را با `Cache-Control: no-store` سرو می‌کرد.
        # وب‌ویوِ مینی‌اپِ تلگرام دارایی‌ها را بر اساسِ **URL** کش می‌کند و
        # آن هدر را همیشه رعایت نمی‌کند. تنها اهرمی که قطعی است، عوض‌کردنِ
        # خودِ URL است. پس نسخهٔ محتوا داخلِ query تزریق می‌شود:
        # فایل که عوض شد ⇒ آدرس عوض می‌شود ⇒ کش ساختاراً بی‌اثر است.
        # (اگر این را برندارم، هر بازطراحیِ آینده هم «دیده نمی‌شود».)
        body = _version_assets(body)
        # Re-build inject at serve time so flag flips apply without code reload edge cases.
        snippet = _build_inject().encode("utf-8")
        # ۲۰۲۶-۰۸-۱۱ (Integration Wave): snippet باید **پیش از** اسکریپت‌های مینی‌اپ
        # اجرا شود. پیش‌تر قبلِ `</body>` (بعد از app.js) تزریق می‌شد؛ پس وقتی
        # `renderAsk` اجرا می‌شد `window.__OCTOPUS__.wire_collab` هنوز ست نشده بود و
        # UI به‌غلط «همکار خاموش» را نشان می‌داد در حالی که COLLAB=1 روی runtime بود
        # (اثباتِ مرورگر: window.__OCTOPUS__ === {}). حالا قبل از اولین اسکریپتِ
        # مینی‌اپ می‌نشیند تا فلگ‌ها و fetch-wrapper مستقل از ترتیب/خطای اسکریپتِ
        # خارجی telegram-web-app.js آماده باشند. fallback‌ها ترتیب قبلی را حفظ می‌کنند.
        _anchor = b'<script src="/miniapp/'
        if _anchor in body:
            body = body.replace(_anchor, snippet + _anchor, 1)
        elif b"</head>" in body:
            body = body.replace(b"</head>", snippet + b"</head>", 1)
        elif b"</body>" in body:
            body = body.replace(b"</body>", snippet + b"</body>", 1)
        else:
            body = body + snippet
    elif rel == "app.js":
        # External-script fallback for webviews that suppress inline scripts.
        # This is the authoritative runtime-config bootstrap and runs before app.js body.
        body = (_build_inject_js() + "\n").encode("utf-8") + body
    return 200, body, ctype


_ASSET_NAMES = ("index.html", "app.js", "tg_shell.js", "style.css")
_ASSET_VERSION_CACHE: dict = {"key": None, "value": None}
_ASSET_VERSION_LOCK = threading.RLock()


def assets_version() -> str:
    """اثرِ انگشتِ محتوای دارایی‌ها. هر بایتِ عوض‌شده = نسخهٔ نو.

    کارایی (۲۰۲۶-۰۸-۰۸): قبلاً هر GET به `/`/`/miniapp` (یعنی هر بار که مالک
    مینی‌اپ را از تلگرام باز می‌کرد) ۴ فایل را کامل از دیسک می‌خواند و SHA-256
    می‌زد — درحالی‌که این فایل‌ها فقط وقتی deploy تازه می‌شود عوض می‌شوند.
    حالا فقط mtime (متادیتای فایل‌سیستم، نه محتوا) چک می‌شود؛ فقط وقتی عوض
    شده باشد هش دوباره محاسبه می‌شود. خروجی برای همان محتوا بایت‌به‌بایت یکی
    است — فقط مسیرِ رسیدن به آن سریع‌تر شد."""
    try:
        mtimes = tuple((_MINIAPP_DIR / n).stat().st_mtime_ns for n in _ASSET_NAMES)
    except OSError:
        mtimes = None
    # app.js response contains a dynamic non-secret bootstrap. Bind its two booleans
    # into the cache key/digest so a runtime flag flip changes the asset URL too;
    # otherwise Telegram can keep an old bootstrap under the same ?v= URL.
    config_sig = (
        os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1",
        os.environ.get("OCTOPUS_COLLAB_USE_MODEL", "0") == "1",
    )
    cache_key = (mtimes, config_sig)
    if mtimes is not None:
        with _ASSET_VERSION_LOCK:
            if _ASSET_VERSION_CACHE["key"] == cache_key:
                return _ASSET_VERSION_CACHE["value"]
    h = hashlib.sha256()
    for name in _ASSET_NAMES:
        try:
            h.update((_MINIAPP_DIR / name).read_bytes())
        except OSError:
            h.update(b"?")
    h.update(repr(config_sig).encode("ascii"))
    v = h.hexdigest()[:10]
    if mtimes is not None:
        with _ASSET_VERSION_LOCK:
            _ASSET_VERSION_CACHE["key"] = cache_key
            _ASSET_VERSION_CACHE["value"] = v
    return v


def _version_assets(body: bytes) -> bytes:
    """`/miniapp/app.js` → `/miniapp/app.js?v=<hash>` در خودِ HTML."""
    v = assets_version().encode("ascii")
    for name in (b"app.js", b"tg_shell.js", b"style.css"):
        body = body.replace(b'"/miniapp/' + name + b'"',
                            b'"/miniapp/' + name + b'?v=' + v + b'"')
    return body

def _default_fetch(path: str) -> tuple:
    """proxy ِ loopback به 8773 — فقط GET، فقط دو مسیرِ سفید. (status, body, ctype)."""
    url = f"http://127.0.0.1:{UPSTREAM_PORT}{path}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            ctype = r.headers.get("Content-Type") or "application/json; charset=utf-8"
            return int(r.status), r.read(), ctype
    except Exception:  # noqa: BLE001 — بالادستی خاموش = جوابِ صادقِ ساده
        return 502, b"", "text/plain; charset=utf-8"


def _get_header(headers, name: str) -> str:
    """جستجویِ **حساس‌نبودن به حروف** — HTTP header field name عمداً case-
    insensitive است (RFC 7230 §3.2)، ولی `_Handler._run` برای POST هدرها را
    به یک dict ِ معمولی (حساس-به-حروف) تنزل می‌دهد و مرورگر/`fetch()` نامِ
    هدر را lowercase می‌فرستد. نتیجه: `headers.get("X-Tg-Init-Data")` روی
    POST هرگز چیزی پیدا نمی‌کرد — یعنی تنها مسیرِ نوشتن (`/api/actions`)
    همیشه ۴۰۳ می‌داد صرفِ‌نظر از initData ِ واقعاً معتبر. `email.message.Message`
    (مسیرِ GET، `self.headers`) خودش از قبل case-insensitive است؛ این تابع هر
    دو شکل را یکسان می‌کند — یک نقطهٔ خواندن برای هر شکلِ نوشتن."""
    try:
        v = headers.get(name)
        if v is not None:
            return v
    except Exception:  # noqa: BLE001
        pass
    try:
        low = name.lower()
        for k in headers.keys():
            if str(k).lower() == low:
                v = headers.get(k) if hasattr(headers, "get") else headers[k]
                return v if v is not None else ""
    except Exception:  # noqa: BLE001
        pass
    return ""


def _owner_initdata_ok(headers, now: "float | None" = None) -> bool:
    """همان دیوارِ §۲ به‌شکلِ یک تابعِ مشترک — نه کپیِ دوم، نه شاخهٔ نرم‌تر."""
    token = os.environ.get("TG_CENTER_BOT_TOKEN", "")
    owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
    if not token or not owner:
        return False                                   # پیکربندیِ ناقص = بسته
    init_data = _get_header(headers, "X-Tg-Init-Data") or ""
    return validate_init_data(init_data, bot_token=token, owner_id=owner,
                              now=now) is not None


def _read_api_authorized(headers, now: "float | None" = None) -> bool:
    """گاردِ **یکسانِ** همهٔ مسیرهای READ_API_PATHS (والد و زیرمسیر، یک تابع)."""
    if not read_gate_enabled():
        return True
    return _owner_initdata_ok(headers, now=now)


DECISION_NONCE_SHADOW_FLAG = "OCTOPUS_MINIAPP_DECISION_NONCE_SHADOW"


def _shadow_consume_decision_nonce(payload: dict, *, ledger_path=None, now=None) -> dict:
    """Default-off fixture/shadow integration point for mutation envelopes.

    Live routes do not call this helper yet. A future owner-approved canary may
    wire it after security shadow verification. When enabled it fails closed on
    a missing/mismatched/replayed decision envelope.
    """
    if str(os.environ.get(DECISION_NONCE_SHADOW_FLAG, "0")).strip().lower() \
            not in {"1", "true", "yes", "on"}:
        return {"ok": False, "status_code": 403, "state": "SHADOW_FLAG_OFF"}
    envelope = payload.get("decision") if isinstance(payload, dict) else None
    if not isinstance(envelope, dict):
        return {"ok": False, "status_code": 409, "state": "NONCE_REQUIRED"}
    try:
        import miniapp_decision_ledger as _mdl  # noqa: WPS433
        path = Path(ledger_path) if ledger_path else (
            Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
            / "telegram" / "miniapp-decision-shadow.db")
        ledger = _mdl.DecisionLedger(path, clock=(lambda: float(now)) if now is not None else None)
        try:
            return ledger.consume(
                proposal_id=str(envelope.get("proposal_id") or ""),
                card_id=str(envelope.get("card_id") or ""),
                nonce=str(envelope.get("nonce") or ""),
                owner_ref=str(envelope.get("owner_id_ref") or ""),
                scope_hash=str(envelope.get("scope_hash") or ""),
            )
        finally:
            ledger.close()
    except Exception as exc:  # noqa: BLE001 — shadow security gate fails closed
        return {"ok": False, "status_code": 409,
                "state": "FAILED_SAFE", "error_code": type(exc).__name__}


def _stopped() -> bool:
    try:
        # 2026-08-12 fix: قبلاً فقط STOP_NAME (فلگِ محلیِ خودِ gateway) چک
        # می‌شد — HALT-ALL/STOP(architect) را نادیده می‌گرفت، برخلافِ قولِ
        # خودِ opslib.master_halted(): «مرزِ سختِ سراسری، هیچ‌کس حق
        # نادیده‌گرفتنش را ندارد». نتیجه: مینی‌اپ حتی زیرِ HALT-ALL جواب
        # می‌داد چون واتداگش مستقیم spawn می‌کند و از STOP-* عادی رد می‌شود.
        if opslib.master_halted():
            return True
        return (Path(opslib.OPS) / STOP_NAME).exists()
    except Exception:  # noqa: BLE001 — شک = توقف (fail-closed)
        return True


HITS_NAME = "miniapp-hits.jsonl"


def _hits_path() -> Path:
    return Path(opslib.STATE_DIR) / "telegram" / HITS_NAME


def _log_hit(path: str, status: int, authed: bool) -> None:
    """یک خط به‌ازای هر درخواستِ سرو‌شده — **تنها** راهِ اثباتِ یک تپِ راه‌دور.

    محتوا عمداً تهی از هویت است: نه توکن، نه initData، نه هیچ فیلدِ user —
    فقط مسیر، موفقیت، و یک بولیِ «از دیوارِ HMAC رد شد یا نه». fail-soft:
    خطای دیسک هرگز پاسخِ HTTP را عوض نمی‌کند (لاگ‌کردن هیچ‌وقت سرویس نیست)."""
    try:
        p = _hits_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": round(time.time(), 3),
               "path": str(path or "").split("?", 1)[0][:64],
               "ok": bool(200 <= int(status) < 400),
               "authed": bool(authed)}
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — رسید هرگز مسیرِ سرویس را نمی‌کشد
        pass


def _run_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """یک تابع را در thread جدا اجرا می‌کند و سقفِ زمانی اعمال می‌کند.

    ۲۰۲۶-۰۸-۰۸: مسیرهای ask_brain/mirror/OpsActionEngine بدونِ timeout بودند —
    اگر LLM یا DB هنگ کند، thread تا ابر باز می‌ماند و به‌مرور نشت می‌کرد. این
    wrapper ضامنِ آن است که هیچ درخواستی بیش از `timeout_s` معلق نماند.

    خروجی: (result, None) در موفقیت، یا (None, "timeout") در انقضای مهلت.

    نکتهٔ threading: thread همچنان پس از timeout زنده می‌ماند (Python به‌سختی
    threadها را kill می‌کند) ولی حداقل پاسخِ HTTP فوراً برمی‌گردد و thread معلق
    دیگر مسیرِ سرویس را قفل نمی‌کند. برای عملیاتِ LLM این عملاً یعنی connection
    مدل هم بسته می‌شود چون urllib response را می‌خواند و خارج می‌شود."""
    result_box = [None]
    error_box = [None]
    done = threading.Event()

    def _worker():
        try:
            result_box[0] = fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            error_box[0] = e
        finally:
            done.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    done.wait(timeout=timeout_s)
    if done.is_set():
        return result_box[0], error_box[0]
    return None, TimeoutError(f"exceeded {timeout_s:.0f}s")


def handle(method: str, path: str, headers, *, fetch_fn=None,
           now: "float | None" = None) -> tuple:
    """پوششِ نازکِ `_handle_core` که رسیدِ per-request می‌نویسد.

    `authed` مشتق است نه حدس: هر مسیر `/api/*` که ۲xx/3xx می‌دهد از دیوارِ HMAC
    رد شده است (هر شکست = 403). مسیرهای static (shell/app.js/css) همیشه authed=False
    هستند چون owner-auth لازم ندارند — سرو‌شدنشان معنایِ authed بودن نیست."""
    st, body, ctype = _handle_core(method, path, headers, fetch_fn=fetch_fn, now=now)
    p = str(path or "").split("?", 1)[0]
    # ۲۰۲۶-۰۸-۰۸: قبلاً فقط /api/miniapp را authed می‌شمرد — ولی همه‌ی مسیرهای
    # READ_API_PATHS و POST ها هم owner-auth لازم دارند. یک 200 روی هر /api/* =
    # رد شدن از دیوار. فقط static assets (200 بدون auth) authed نیستند.
    _is_api = p.startswith("/api/")
    _authed = _is_api and 200 <= int(st) < 400
    _log_hit(path, st, _authed)
    return st, body, ctype


def _handle_core(method: str, path: str, headers, *, fetch_fn=None,
                 now: "float | None" = None) -> tuple:
    """هستهٔ خالص/تزریق‌پذیرِ gateway → (status:int, body:bytes, ctype:str).

    تست‌ها همین را مستقیم صدا می‌زنند (بدونِ سرورِ واقعی)؛ لایهٔ HTTP فقط
    همین را wrap می‌کند. headers هر شیءِ dict-مانند با .get است."""
    fetch = fetch_fn if fetch_fn is not None else _default_fetch
    if _stopped():
        return 503, b"", "text/plain; charset=utf-8"       # کلیدِ کشتار
    method_u = str(method or "").upper()
    p = str(path or "").split("?", 1)[0]
    if method_u not in {"GET", "POST"}:
        return 405, b"", "text/plain; charset=utf-8"
    if method_u == "POST" and p not in ("/api/actions", "/api/ask", "/api/mirror", "/api/restart", "/api/collab", "/api/brain-guide", "/api/octopus/chat", "/api/board/commands", "/api/board-cp/ack"):
        return 405, b"", "text/plain; charset=utf-8"
    if p in ("/", "/miniapp", "/miniapp/", "/miniapp/app.js", "/miniapp/style.css",
             "/miniapp/tg_shell.js", "/tg_shell.js", "/app.js", "/style.css"):
        return _miniapp_static_response(p)
    if p in ("/api/board/commands", "/api/board-cp/pull", "/api/board-cp/ack"):
        try:
            from board_cp import http as _bcp_http  # noqa: WPS433
        except Exception:  # noqa: BLE001
            return 500, b'{"ok":false,"reason":"board_cp_unavailable"}', \
                "application/json; charset=utf-8"
        owner_ok = _owner_initdata_ok(headers, now=now) if p == "/api/board/commands" else False
        hit = _bcp_http.dispatch(method_u, p, headers, owner_ok=owner_ok)
        if hit is not None:
            return hit
    if p == "/api/actions":
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"status":"DENIED","reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _action_rate_limited(now):
            return 429, b'{"ok":false,"status":"DENIED","reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = b""
            try:
                raw_body = headers.get("_body") or b""
            except Exception:
                raw_body = b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            action = str(payload.get("action") or "")
            action_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
            action_id = payload.get("action_id")
            import sys as _sys
            ops_path = str(_OPS)
            if ops_path not in _sys.path:
                _sys.path.insert(0, ops_path)
            from agi2027_control.ops_actions import OpsActionEngine  # noqa: WPS433
            eng = OpsActionEngine(_OPS.parent)
            try:
                # ۲۰۲۶-۰۸-۰۸: OpsActionEngine می‌تواند به DB بنویسد که اگر قفل
                # شده باشد ممکن است هنگ کند. سقفِ زمانیِ کوتاه (۱۵s) ضامنِ آن
                # است که هیچ اقدامی thread را برای همیشه قفل نکند.
                res, a_err = _run_with_timeout(
                    eng.execute, ACTIONS_TIMEOUT_S, action, action_payload,
                    {"is_owner": True}, action_id=action_id)
                if a_err and isinstance(a_err, TimeoutError):
                    body = json.dumps({"ok": False, "status": "ERROR",
                                       "reason": "action_timeout"},
                                      ensure_ascii=False).encode("utf-8")
                    return 504, body, "application/json; charset=utf-8"
                if a_err:
                    raise a_err
                res = res or {}
                # ⚠️ باگِ «زدم و هیچ نشد» (۲۰۲۶-۰۸-۰۵): کشِ خواندن ۳ ثانیه TTL
                # دارد و UI بلافاصله بعد از اقدامِ موفق همان بخش را دوباره
                # می‌خواند ⇒ حالتِ **قبل از نوشتن** سرو می‌شد. مالک تُستِ سبز
                # می‌دید و ردیف سر‌جایش می‌ماند. `cache_clear()` از قبل وجود
                # داشت و صفر صداکننده داشت.
                # فقط APPLIED و ERROR می‌توانند حالت را عوض کرده باشند:
                # BLOCKED/DENIED هر دو قبل از هر نوشتنی return می‌کنند و
                # DUPLICATE یعنی نوشتنِ قبلی — که خودش همین‌جا کش را پاک کرد.
                # ERROR هم پاک می‌شود چون کرشِ وسطِ اجرا می‌تواند نیمه‌نوشته باشد.
                if str(res.get("status") or "").upper() in ("APPLIED", "ERROR"):
                    try:
                        import miniapp_state  # noqa: WPS433 — هم‌پوشه
                        miniapp_state.cache_clear()
                    except Exception:  # noqa: BLE001 — باطل‌سازی هرگز اقدام را نمی‌شکند
                        pass
                body = json.dumps(res, ensure_ascii=False, sort_keys=True).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            finally:
                eng.close()
        except Exception as exc:
            body = json.dumps({"ok": False, "status": "ERROR", "reason": type(exc).__name__}, ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/ask":
        # ۲۰۲۶-۰۸-۰۸: چت‌باکسِ مینی‌اپ — رأیِ مالک روی نوتِ ۲۸ («سیم‌کشیِ
        # ask_vault/ask_brain به مینی‌اپ»، بخشِ الف-۲ سابق). نردبانِ محلی-اول
        # هم‌سبکِ کلِ ارگانیسم: اول vault ِ رایگان/مستند (ask_vault)، فقط اگر
        # منبعی پیدا نشد مغزِ گران/محلیِ ask_brain (که خودش نردبانِ
        # محلی/پولیِ داخلیِ خودش را دارد). هیچ‌کدام این‌جا reimplement
        # نمی‌شوند — فقط از درِ موجودشان صدا زده می‌شوند.
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _ask_rate_limited(now):
            return 429, b'{"ok":false,"reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = b""
            try:
                raw_body = headers.get("_body") or b""
            except Exception:
                raw_body = b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            question = str(payload.get("question") or "").strip()
            if not question:
                return 400, b'{"ok":false,"reason":"empty_question"}', "application/json; charset=utf-8"
            import sys as _sys
            ops_path = str(_OPS)
            if ops_path not in _sys.path:
                _sys.path.insert(0, ops_path)
            import ask_vault  # noqa: WPS433 — هم‌پوشه
            import ask_brain  # noqa: WPS433 — هم‌پوشه
            # ۲۰۲۶-۰۸-۰۸: ask_vault معمولاً سریع است (پایگاه داده محلی) ولی
            # ask_brain می‌تواند به یک LLM محلی/پولی برسد که ممکن است هنگ کند.
            # هر دو داخلِ سقفِ زمانی اجرا می‌شوند تا هیچ مکالمه‌ای thread را
            # برای همیشه قفل نکند.
            rv, v_err = _run_with_timeout(ask_vault.query, ASK_TIMEOUT_S, question)
            if v_err and isinstance(v_err, TimeoutError):
                rv, v_err = {}, None  # vault کند → برو سراغ brain/fallback
            if v_err:
                raise v_err
            rv = rv or {}
            # sources خالی یعنی NO_ANSWER (صفر شاهد) — ok=True است ولی جوابِ
            # واقعی نیست؛ باید escalate کند، نه اینکه به‌جایِ جواب برگردد.
            if rv.get("ok") and rv.get("answer") and rv.get("sources"):
                body = json.dumps({"ok": True, "answer": rv["answer"], "source": "vault",
                                   "sources": rv.get("sources") or []},
                                  ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            # Awareness 2026-08-12: vault flag-on ولی hit خالی → صادق، نه escalate بی‌صدا
            vault_meta = {}
            if rv.get("reason") == "flag-off":
                vault_meta = {"vault_empty": False, "vault_flag": "off",
                              "vault_note": "ask_vault خاموش است → brain/collab"}
            elif not (rv.get("sources") or []):
                vault_meta = {"vault_empty": True, "vault_flag": "on",
                              "vault_note": "vault روشن است ولی منبعی برای این سؤال یافت نشد"}
            rb, b_err = _run_with_timeout(
                ask_brain.ask, ASK_BRAIN_TIMEOUT_S, question)
            if b_err and not isinstance(b_err, TimeoutError):
                raise b_err
            rb = rb or {}
            if not b_err and rb.get("ok"):
                payload_ok = {
                    "ok": True, "answer": rb.get("text") or "", "source": "brain",
                    "tier": rb.get("tier"), "model": rb.get("model"),
                }
                payload_ok.update(vault_meta)
                body = json.dumps(payload_ok, ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            # ۲۰۲۶-۰۸-۱۲: مغز هنگ/خالی → همکارِ stub تا UI روی «فکر کردن» نماند.
            try:
                from owner_console import collaborator as _collab  # noqa: WPS433
                st_dir = Path(opslib.STATE_DIR)
                creply, _cerr = _run_with_timeout(
                    _collab.handle, min(ASK_TIMEOUT_S, 10.0), question,
                    state_dir=st_dir)
                if creply and creply.get("text"):
                    payload_fb = {
                        "ok": True,
                        "answer": creply.get("text") or "",
                        "source": "collab-fallback",
                        "kind": creply.get("kind"),
                        "model_source": creply.get("model_source"),
                        "data": creply.get("data") or {},
                        "brain_reason": (
                            "brain_timeout" if isinstance(b_err, TimeoutError)
                            else (rb.get("reason") or rv.get("reason") or "no-answer")
                        ),
                    }
                    payload_fb.update(vault_meta)
                    body = json.dumps(payload_fb, ensure_ascii=False).encode("utf-8")
                    return 200, body, "application/json; charset=utf-8"
            except Exception:  # noqa: BLE001 — fallback هرگز مسیر را نمی‌کشد
                pass
            reason = (
                "brain_timeout" if isinstance(b_err, TimeoutError)
                else (rb.get("reason") or rv.get("reason") or "no-answer")
            )
            payload_fail = {"ok": False, "reason": reason}
            payload_fail.update(vault_meta)
            body = json.dumps(payload_fail, ensure_ascii=False).encode("utf-8")
            return 200, body, "application/json; charset=utf-8"
        except Exception as exc:
            body = json.dumps({"ok": False, "reason": type(exc).__name__}, ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/mirror":
        # ۲۰۲۶-۰۸-۰۸: نقطهٔ ورودِ mirror_room از مینی‌اپ (رأیِ مالک، بخشِ
        # الف-۷/mirror_room سابق). به‌جایِ deep-link به یک تاپیکِ تلگرام
        # (که به chat_id/topic_id خام نیاز داشت و mirror_room را خارج از
        # میدانپ نگه می‌داشت)، خودِ mirror_room.ask() مستقیم از این‌جا صدا
        # زده می‌شود — room="" یعنی همان تاپیکِ mirror ِ پیش‌فرض
        # (room_slug). چیزی reimplement نشده: حافظهٔ نوبت‌به‌نوبت،
        # تشخیصِ تصحیح، و نوشتنِ history همه از خودِ ماژول می‌آید.
        # پنجرهٔ rate-limit مشترک با /api/ask (هر دو یعنی «مکالمهٔ زنده»).
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _ask_rate_limited(now):
            return 429, b'{"ok":false,"reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = b""
            try:
                raw_body = headers.get("_body") or b""
            except Exception:
                raw_body = b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            question = str(payload.get("question") or "").strip()
            if not question:
                return 400, b'{"ok":false,"reason":"empty_question"}', "application/json; charset=utf-8"
            import sys as _sys
            ops_path = str(_OPS)
            if ops_path not in _sys.path:
                _sys.path.insert(0, ops_path)
            import mirror_room  # noqa: WPS433 — هم‌پوشه
            # ۲۰۲۶-۰۸-۰۸: mirror_room می‌تواند به LLM محلی/پولی برسد — سقفِ زمانی
            # همان تضمینِ ask: هیچ مکالمه‌ای thread را برای همیشه قفل نمی‌کند.
            rm, m_err = _run_with_timeout(mirror_room.ask, MIRROR_TIMEOUT_S, question)
            if m_err and isinstance(m_err, TimeoutError):
                body = json.dumps({"ok": False, "reason": "mirror_timeout"},
                                  ensure_ascii=False).encode("utf-8")
                return 504, body, "application/json; charset=utf-8"
            if m_err:
                raise m_err
            rm = rm or {}
            if rm.get("ok"):
                body = json.dumps({"ok": True, "answer": rm.get("text") or "",
                                   "source": "mirror", "tier": rm.get("tier"),
                                   "model": rm.get("model"),
                                   "recorded_correction": bool(rm.get("recorded_correction"))},
                                  ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            body = json.dumps({"ok": False, "reason": rm.get("reason") or "no-answer"},
                              ensure_ascii=False).encode("utf-8")
            return 200, body, "application/json; charset=utf-8"
        except Exception as exc:
            body = json.dumps({"ok": False, "reason": type(exc).__name__}, ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/restart":
        # ۲۰۲۶-۰۸-۰۹: دکمهٔ «ری‌استارتِ کامل» در مینی‌اپ — درِ ورودیِ دومی به
        # همان مسیرِ امنِ فرمانِ تلگرامِ `/restart` (رأیِ مالک ۰۸-۰۷: trigger
        # فقط دستی، تأیید داخلِ همان چت). این‌جا فقط request_restart را صدا
        # می‌زند و همان کارتِ approval را می‌سازد؛ **هیچ subprocessی مستقیم
        # از این‌جا launch نمی‌شود** — اجرای واقعی هنوز فقط از ap:ok در
        # center.py می‌آید (`_trigger_restart_execution`). یعنی این دکمه
        # گیتِ تأییدِ مالک را دور نمی‌زند، فقط یک راهِ کوتاه‌تر برای رسیدن به
        # همان کارت است. صفر reimplementation: منطق عیناً از
        # center.py::_restart_cmd کپی شده، نه بازنویسی.
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _ask_rate_limited(now):
            return 429, b'{"ok":false,"reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = b""
            try:
                raw_body = headers.get("_body") or b""
            except Exception:
                raw_body = b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}") if raw_body else {}
            scope = str(payload.get("scope") or "all").strip().lower()
            import sys as _sys
            ops_path = str(_OPS)
            if ops_path not in _sys.path:
                _sys.path.insert(0, ops_path)
            import restart_control as _rc  # noqa: WPS433 — هم‌پوشه
            import approval_store as _aps  # noqa: WPS433 — هم‌پوشه
            if not _rc.flag_on():
                body = json.dumps({"ok": False, "reason": "flag-off"},
                                  ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            if scope not in _rc.VALID_SCOPES:
                body = json.dumps({"ok": False, "reason": "invalid_scope"},
                                  ensure_ascii=False).encode("utf-8")
                return 400, body, "application/json; charset=utf-8"
            if _rc.is_restart_in_flight():
                body = json.dumps({"ok": False, "reason": "already_in_flight"},
                                  ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            import uuid as _uuid
            owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
            job_id = f"restart_{scope}_{int(time.time())}_{_uuid.uuid4().hex[:6]}"
            r1 = _rc.request_restart(scope, job_id=job_id, requested_by=str(owner))
            if not r1.get("ok"):
                body = json.dumps({"ok": False, "reason": r1.get("reason") or "store_failed"},
                                  ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            try:
                _aps.add_pending({"id": job_id, "type": "process_restart",
                                  "title": f"ری‌استارتِ {scope}", "risk": "high",
                                  "requires_confirmation": True,
                                  "dry_run_report": f"scope={scope}",
                                  "source": "restart_control"})
            except Exception:  # noqa: BLE001
                _rc.cancel_request()
                body = json.dumps({"ok": False, "reason": "approval_card_failed"},
                                  ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            body = json.dumps({"ok": True, "job_id": job_id, "scope": scope,
                               "reason": "confirm_in_telegram"},
                              ensure_ascii=False).encode("utf-8")
            return 200, body, "application/json; charset=utf-8"
        except Exception as exc:
            body = json.dumps({"ok": False, "reason": type(exc).__name__}, ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/collab":
        # ۲۰۲۶-۰۸-۱۱: نقطهٔ ورودِ collaborator از مینی‌اپ (WP-E3). owner-auth +
        # rate-limit + delegate به collaborator.handle(). همان پنجرهٔ rate-limitِ
        # /api/ask — مکالمه. صفر reimplement: منطق عیناً از collaborator.py
        # می‌آید. پاسخ redact می‌شود (دفاعِ دولایه). contract: owner-console.reply.v1,
        # external_effect=False, cost=0, send_attempted=False.
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _ask_rate_limited(now):
            return 429, b'{"ok":false,"reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = b""
            try:
                raw_body = headers.get("_body") or b""
            except Exception:
                raw_body = b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            text = str(payload.get("text") or "").strip()
            if not text:
                return 400, b'{"ok":false,"reason":"empty_text"}', "application/json; charset=utf-8"
            import sys as _sys
            ops_path = str(_OPS)
            if ops_path not in _sys.path:
                _sys.path.insert(0, ops_path)
            # 2026-08-11 closeout: NEVER auto-arm. Default OFF / fail-closed.
            # If unset or not "1" → feature_disabled. Do not mutate env.
            if os.environ.get("OCTOPUS_WIRE_COLLAB", "0") != "1":
                return (404,
                        b'{"ok":false,"reason":"feature_disabled","flag":"OCTOPUS_WIRE_COLLAB"}',
                        "application/json; charset=utf-8")
            from owner_console import collaborator as _collab  # noqa: WPS433
            st_dir = Path(opslib.STATE_DIR)
            # ۲۰۲۶-۰۸-۱۲: collab نیز باید زیر timeout باشد (مانند /api/ask).
            # COLLAB_USE_MODEL=1 می‌تواند model_router.ask را صدا بزند که تا ۹۰s
            # هنگ می‌کند. بدون wrapper، thread تا ابر معلق می‌ماند و پرسش هنگ می‌کند.
            reply, c_err = _run_with_timeout(
                _collab.handle, COLLAB_TIMEOUT_S, text, state_dir=st_dir)
            if c_err and isinstance(c_err, TimeoutError):
                # ۲۰۰ + schema رسمی تا UI به bad_json/504 نخورد؛ متنِ صادق.
                body = json.dumps({
                    "schema": "owner-console.reply.v1",
                    "kind": "timeout",
                    "text": ("جواب طول کشید (DeepSeek گاهی ۲۰–۴۰ثانیه). "
                             "لطفاً دوباره بپرس؛ حالت همکار را نگه دار."),
                    "keyboard": [],
                    "data": {"status": "COLLAB_TIMEOUT",
                             "timeout_s": COLLAB_TIMEOUT_S},
                    "external_effect": False,
                    "estimated_cost": 0,
                    "send_attempted": False,
                    "authorization": None,
                    "model_source": "timeout",
                }, ensure_ascii=False).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            if c_err:
                raise c_err
            # دفاعِ دولایه: redact هر پاسخی که خارج می‌رود
            reply_json = json.dumps(reply, ensure_ascii=False)
            redacted = _redact(reply_json)
            body = redacted.encode("utf-8")
            return 200, body, "application/json; charset=utf-8"
        except Exception as exc:
            body = json.dumps({"ok": False, "reason": type(exc).__name__},
                              ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/brain-guide":
        # 2026-08-12 فاز ۳: چت → cortex از مسیر موجود owner_guidance (نه IPC).
        # فقط append به state/cortex/owner-guidance.jsonl؛ cortex در cycle می‌خواند.
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _ask_rate_limited(now):
            return 429, b'{"ok":false,"reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = headers.get("_body") or b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            text = str(payload.get("text") or "").strip()
            if not text:
                return 400, b'{"ok":false,"reason":"empty_text"}', "application/json; charset=utf-8"
            import sys as _sys
            cortex_path = str(_OPS / "cortex")
            if cortex_path not in _sys.path:
                _sys.path.insert(0, cortex_path)
            import owner_guidance as _og  # noqa: WPS433
            result = _og.append(text, by="miniapp-owner")
            body = json.dumps({
                "ok": bool(result.get("ok")),
                "directive": result.get("directive"),
                "error": result.get("error"),
                "path": "state/cortex/owner-guidance.jsonl",
                "note": "cortex در cycle بعد می‌خواند؛ IPC به :8772 نیست",
                "external_effect": False,
                "may_authorize": False,
            }, ensure_ascii=False).encode("utf-8")
            return (200 if result.get("ok") else 400), body, "application/json; charset=utf-8"
        except Exception as exc:
            body = json.dumps({"ok": False, "reason": type(exc).__name__},
                              ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/octopus/chat":
        # 2026-08-13 (ADR-040 Phase 3): درگاهِ واحدِ چت — Conversation Hub.
        # flag-gated (OCTOPUS_UNIFIED_CHAT، پیش‌فرض خاموش)؛ owner-auth؛ rate-limit.
        # فقط observe+propose — execute ممنوع (Hub هرگز external_effect True نمی‌دهد).
        if os.environ.get("OCTOPUS_UNIFIED_CHAT", "0") != "1":
            return 404, b'{"ok":false,"reason":"feature_disabled","flag":"OCTOPUS_UNIFIED_CHAT"}', "application/json; charset=utf-8"
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        if _ask_rate_limited(now):
            return 429, b'{"ok":false,"reason":"rate_limited"}', "application/json; charset=utf-8"
        try:
            raw_body = headers.get("_body") or b""
            if isinstance(raw_body, str):
                raw_body = raw_body.encode("utf-8")
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            text = str(payload.get("text") or "").strip()
            if not text:
                return 400, b'{"ok":false,"reason":"empty_text"}', "application/json; charset=utf-8"
            import sys as _sys
            if str(_OPS) not in _sys.path:
                _sys.path.insert(0, str(_OPS))
            from conversation_hub import handle as _hub_handle  # noqa: WPS433
            req = {
                # 2026-08-15 (جاروی تست T7): now در ترافیکِ واقعی None است
                # (پیش‌فرضِ handle) — int(None) هر POSTِ بدونِ message_id را
                # با TypeError/500 می‌کشت. تستِ واحد now می‌داد و این را نمی‌دید.
                "message_id": str(payload.get("message_id")
                                  or ("msg-" + str(int(now if now is not None else time.time())))),
                "text": text,
                "mode": str(payload.get("mode") or "auto"),
                "requested_depth": str(payload.get("requested_depth") or "normal"),
                "idempotency_key": str(payload.get("idempotency_key") or ""),
            }
            reply = _hub_handle(req)
            body = json.dumps(reply.model_dump(mode="json"), ensure_ascii=False).encode("utf-8")
            return 200, body, "application/json; charset=utf-8"
        except Exception as exc:
            body = json.dumps({"ok": False, "reason": type(exc).__name__},
                              ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/miniapp":
        if not _owner_initdata_ok(headers, now=now):
            return 403, b"", "text/plain; charset=utf-8"
        st, body, ctype = fetch("/api/miniapp")
        if st == 200:
            # دفاعِ دولایه: 8773 خودش redact کرده؛ این لایه دوباره رد می‌کند.
            body = _redact(body.decode("utf-8", "replace")).encode("utf-8")
        return st, body, ctype
    # ── 2026-08-12: Chat Log — تاریخچهٔ سرور-ساید گفتگو + هدفِ مالک ──────────
    # GET /api/chat-log?limit=N → {ok, goal, turns[]} (owner-auth, redact دولایه)
    if p == "/api/chat-log":
        if method_u != "GET":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        limit = 10
        qs = str(path or "").split("?", 1)
        if len(qs) > 1:
            for kv in qs[1].split("&"):
                if kv.startswith("limit="):
                    try:
                        limit = min(30, max(1, int(kv[6:])))
                    except ValueError:
                        pass
        try:
            import sys as _clsys
            _own_dir = str(_OPS / "owner_console")
            if _own_dir not in _clsys.path:
                _clsys.path.insert(0, _own_dir)
            import chat_log as _clog  # noqa: WPS433
            turns = []
            for r in _clog.recent(limit=limit):
                turns.append({
                    "ts": r.get("ts"),
                    "role": r.get("role"),
                    "kind": r.get("kind"),
                    "text": _redact(str(r.get("text") or "")),
                    "run_id": r.get("run_id"),
                    "model_source": r.get("model_source"),
                })
            goal = {}
            try:
                goal = json.loads(
                    (_OPS / "state" / "owner-goal.json").read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                goal = {}
            body = json.dumps({"ok": True, "goal": goal, "turns": turns},
                              ensure_ascii=False).encode("utf-8")
            return 200, body, "application/json; charset=utf-8"
        except Exception as exc:  # noqa: BLE001
            return 500, json.dumps({"ok": False, "reason": type(exc).__name__}).encode("utf-8"), \
                "application/json; charset=utf-8"
    # ── E4: Cognitive Runtime — Run events (SSE) + Run summary ──────────────
    # GET /api/runs/{run_id} → JSON summary
    # GET /api/runs/{run_id}/events?after=N → SSE text/event-stream
    if p.startswith("/api/runs/"):
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        parts = p.split("/")
        # /api/runs/{run_id} or /api/runs/{run_id}/events
        if len(parts) >= 4 and parts[3]:
            run_id_raw = parts[3]
            # sanitize: فقط alnum و -_
            run_id = "".join(c for c in run_id_raw if c.isalnum() or c in "-_")[:64]
            if not run_id:
                return 404, b'{"ok":false,"reason":"invalid_run_id"}', "application/json; charset=utf-8"
            import sys as _rsys
            _cog_p = str(_OPS / "cognitive")
            if _cog_p not in _rsys.path:
                _rsys.path.insert(0, _cog_p)
            try:
                import event_stream as _es  # noqa: WPS433
                if len(parts) >= 5 and parts[4] == "events":
                    # SSE: events after sequence
                    after = 0
                    qs = str(path or "").split("?", 1)
                    if len(qs) > 1:
                        for kv in qs[1].split("&"):
                            if kv.startswith("after="):
                                try:
                                    after = int(kv[6:])
                                except ValueError:
                                    pass
                    events = _es.list_events(run_id, after_sequence=after - 1)
                    lines = []
                    for e in events:
                        seq = e.get("sequence", 0)
                        et = e.get("event_type", "UNKNOWN")
                        payload = json.dumps({
                            "sequence": seq,
                            "event_type": et,
                            "producer": e.get("producer"),
                            "status": e.get("status"),
                            "occurred_at": e.get("occurred_at"),
                            "intent": e.get("intent"),
                            "may_authorize": False,
                        }, ensure_ascii=False)
                        lines.append(f"id: {seq}\nevent: {et}\ndata: {payload}\n")
                    sse_body = ("\n".join(lines) + "\n").encode("utf-8") if lines else b": no events\n\n"
                    return 200, sse_body, "text/event-stream; charset=utf-8"
                else:
                    # JSON summary
                    summary = _es.run_summary(run_id)
                    return 200, json.dumps(summary, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8"
            except Exception as exc:  # noqa: BLE001
                return 500, json.dumps({"ok": False, "reason": type(exc).__name__}).encode("utf-8"), "application/json; charset=utf-8"
        return 404, b'{"ok":false,"reason":"run_not_found"}', "application/json; charset=utf-8"
    # PHASE 4 (2026-08-02): read-only /api/* cockpit helpers (secret-scrubbed, fail-closed).
    # No POST/PUT/DELETE here — read-only. Actions (/api/actions) are wired separately
    # above via OpsActionEngine (owner-gated) — stale "not wired yet" note removed 2026-08-09.
    # PHASE 5 (2026-08-03): زیرمسیرهای /api/ops/* از همین درِ واحد رد می‌شوند.
    if p.startswith("/api/") and p in READ_API_PATHS:
        if not _read_api_authorized(headers, now=now):
            return 403, b'{"status":"DENIED","reason":"owner_auth_required"}', \
                "application/json; charset=utf-8"
        try:
            import miniapp_state  # noqa: WPS433 — هم‌پوشه
        except Exception:  # noqa: BLE001
            return 500, b'{"status":"error","reason":"state_module_unavailable"}', \
                "application/json; charset=utf-8"
        st2, body2, ctype2 = miniapp_state.dispatch_api(p)
        if st2 == 200:
            body2 = _redact(body2.decode("utf-8", "replace")).encode("utf-8")
        return st2, body2, ctype2
    # PROP-D5 فاز ۱ (2026-08-03، GO ِ مالک): کارت‌های read-only ِ Project-F.
    # همان دیوارِ HMAC ِ /api/miniapp — هر شکست 403 با بدنهٔ خالی.
    # content-free مطلق: فقط aggregate/count؛ هیچ متنِ درفت از مرزِ پوشهٔ
    # پروژه عبور نمی‌کند (قاعدهٔ قفل‌شدهٔ #۷). فلگ خاموش = 404 (no-op).
    if p.startswith("/api/pf/"):
        if not _owner_initdata_ok(headers, now=now):
            return 403, b"", "text/plain; charset=utf-8"
        try:
            import pf_miniapp  # noqa: WPS433 — هم‌پوشه
        except Exception:  # noqa: BLE001
            return 500, b'{"status":"error","reason":"pf_module_unavailable"}', \
                "application/json; charset=utf-8"
        st3, body3, ctype3 = pf_miniapp.dispatch_api(p)
        if st3 == 200:
            body3 = _redact(body3.decode("utf-8", "replace")).encode("utf-8")
        return st3, body3, ctype3
    # ── 2026-08-13: Chat status banner — بنرِ پیشگیرانهٔ فقط‌خواندنی (TASK 4).
    # GET /api/chat-status → {ok, banner:{level,text,halted,...}}؛ بدونِ تماسِ پولی.
    if p == "/api/chat-status":
        if method_u != "GET":
            return 405, b"", "text/plain; charset=utf-8"
        if not _owner_initdata_ok(headers, now=now):
            return 403, b'{"ok":false,"reason":"owner_auth_required"}', "application/json; charset=utf-8"
        try:
            import sys as _sys
            _oc = str(_OPS / "owner_console")
            if _oc not in _sys.path:
                _sys.path.insert(0, _oc)
            import status_banner as _sb  # noqa: WPS433
            banner = _sb.status_banner()
        except Exception:  # noqa: BLE001 — بنر نباید جوابِ gateway را ببرد
            banner = {"level": "ok", "text": "", "halted": False}
        body = json.dumps({"ok": True, "banner": banner}, ensure_ascii=False).encode("utf-8")
        return 200, body, "application/json; charset=utf-8"
    return 404, b"{}", "application/json; charset=utf-8"


class _Srv(ThreadingHTTPServer):
    allow_reuse_address = False       # ویندوز: تک‌نمونگیِ واقعی

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _cache_control_for(path: str) -> str:
    """کارایی (۲۰۲۶-۰۸-۰۸): دارایی‌هایِ static با `?v=<hash>` (تولیدشده در
    `_version_assets`) قبلاً هم `no-store` می‌گرفتند — یعنی خودِ مکانیزمِ
    نسخه‌گذاری (که دقیقاً برایِ این ساخته شده که بشود درازمدت کش کرد، چون
    تغییرِ محتوا = تغییرِ URL) بی‌اثر بود؛ گوشیِ مالک هر بار که مینی‌اپ را
    باز می‌کرد ۲+ فایل را دوباره از تونلِ عمومی می‌کشید.

    شرطِ سخت‌گیرانه (fail-closed به no-store): فقط وقتی هم `?v=` در URL هست
    هم نامِ یکی از فایل‌هایِ static ِ شناخته‌شده — نه HTML ِ پویا، نه هیچ
    `/api/*`ای هرگز اینجا نمی‌رسد چون هیچ‌کدام `?v=` نمی‌گیرند."""
    if "?v=" in (path or "") and any(
            name in path for name in ("app.js", "tg_shell.js", "style.css")):
        return "public, max-age=31536000, immutable"
    return "no-store"


class _Handler(BaseHTTPRequestHandler):
    def _run(self, method: str):
        headers = self.headers
        if str(method or "").upper() == "POST":
            try:
                length = int(self.headers.get("Content-Length") or "0")
            except Exception:
                length = 0
            if length > 65536:
                self.send_response(413)
                self.end_headers()
                return
            raw = self.rfile.read(length) if length > 0 else b""
            headers = {k: v for k, v in self.headers.items()}
            headers["_body"] = raw
        st, body, ctype = handle(method, self.path, headers)
        self.send_response(st)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", _cache_control_for(self.path))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):    # noqa: N802
        self._run("GET")

    def do_POST(self):   # noqa: N802
        self._run("POST")

    def do_PUT(self):    # noqa: N802
        self._run("PUT")

    def do_DELETE(self):  # noqa: N802
        self._run("DELETE")

    def log_message(self, *a):
        pass              # هیچ لاگِ درخواست — URL/هدر هرگز جایی نوشته نمی‌شود


def main() -> int:
    # VQ-GATEWAY-NO-CREDS-001 (۲۰۲۶-۰۸-۰۴): این پروسه **تنها** پایی بود که
    # `env_loader` را صدا نمی‌زد. organism/center/cortex/live هر چهار می‌زنند؛
    # gateway کاملاً به env ِ ارثی تکیه داشت و واچداگش فقط `_ops/OCTOPUS.env`
    # را می‌خواند که هیچ‌کدام از سه نامِ اعتبارنامه را تعریف نمی‌کند.
    #
    # نتیجهٔ سنجیده‌شده: `TG_CENTER_BOT_TOKEN` و `TELEGRAM_OWNER_CHAT_ID` هر دو
    # غایب ⇒ `validate_init_data` سرِ **اولین** گارد `None` می‌دهد ⇒ gateway
    # صددرصدِ درخواست‌ها را ۴۰۳ می‌کرد. ناامن نبود — **مرده** بود، و از بیرون
    # دقیقاً شبیهِ «احراز درست کار می‌کند» به‌نظر می‌رسید. (۴۰۳ ِ زنده‌ای که
    # ۰۸-۰۳ به‌عنوان شاهدِ سلامتِ احراز ثبت شد، همین بود: ردِ درست به دلیلِ غلط.)
    #
    # اثباتِ بولینی، بدونِ لمسِ هیچ مقداری: قبل از `load_env` هر سه کلید False،
    # بعدش هر سه True. `load_env` خودش idempotent و fail-soft است و هرگز مقدار
    # را چاپ نمی‌کند؛ اگر `.env` نباشد no-op می‌شود و رفتار همان قبل می‌ماند.
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001 — نبودِ .env نباید دیوار را بکشد
        pass
    if not enabled():
        print(f"miniapp_gateway: {FLAG} خاموش است — هیچ پورتی باز نشد (خروجِ تمیز).")
        return 0
    if _stopped():
        print(f"miniapp_gateway: {STOP_NAME} حاضر است — شروع رد شد.")
        return 0
    try:
        srv = _Srv(("127.0.0.1", PORT), _Handler)
    except OSError:
        # VQ-PORT-COLLISION-001: پیام همیشه امیدوارانه («نمونهٔ دیگری») ولی هیچ
        # تأییدی نمی‌کند که آن نمونه واقعاً خودِ gateway است — می‌تواند هر
        # listener ِ دیگری باشد که همان پورت را گرفته (lead_boundary_http قبلاً
        # همین پیش‌فرض را داشت). آن‌وقت تونلِ عمومی بی‌صدا به سرویسِ اشتباه
        # وصل می‌ماند. حالا alert می‌کند تا سکوت نشکند — bind هرگز retry
        # نمی‌شود (idempotent-safe نیست)، فقط دیدنی می‌شود.
        try:
            opslib.alert([f"miniapp_gateway: bind روی 127.0.0.1:{PORT} شکست خورد — "
                          f"شنوندهٔ دیگری آن‌جاست. اگر خودِ gateway نیست، تونلِ "
                          f"عمومی دارد به سرویسِ اشتباه می‌رسد."])
        except Exception:  # noqa: BLE001
            pass
        print(f"miniapp_gateway: نمونهٔ دیگری روی {PORT} زنده است — خروجِ تمیز.")
        return 0
    print(f"miniapp_gateway: دیوارِ Mini App روی http://127.0.0.1:{PORT}")
    # VQ-GATEWAY-DRIFT-BLIND-001 (۲۰۲۶-۰۸-۰۳، برشِ ۳، آیتمِ ۵): برخلافِ
    # organism/center/cortex/live، gateway هرگز snapshot_boot را صدا نمی‌زد —
    # یعنی flag_drift.probe_all اصلاً نمی‌دانست این پروسه با چه فلگ‌هایی بالا
    # آمده؛ رانشِ فلگِ این limb ساختاراً نامرئی بود.
    try:
        import flag_drift
        flag_drift.snapshot_boot("miniapp-gateway")
    except Exception:  # noqa: BLE001
        pass
    try:
        opslib.heartbeat(f"miniapp-gateway=START port={PORT}")
    except Exception:  # noqa: BLE001
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            opslib.heartbeat(f"miniapp-gateway=STOP port={PORT}")
        except Exception:  # noqa: BLE001
            pass
        try:
            srv.server_close()
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
