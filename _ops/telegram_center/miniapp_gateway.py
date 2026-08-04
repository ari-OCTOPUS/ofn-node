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
AUTH_MAX_AGE_S = 300.0
STOP_NAME = "STOP-MINIAPP"

# سطحِ فقط‌خواندنی (secret-scrubbed در miniapp_state، دوباره redact در همین فایل).
# **تک‌فهرست** است نه دو کپی: زیرمسیرهای /api/ops دقیقاً از همان درِ والدشان رد
# می‌شوند، پس ساختاراً نمی‌توانند بازتر باشند — سوراخِ «اندپوینتِ تازهٔ بی‌گارد»
# با قاعده بسته می‌شود نه با یادآوری.
READ_API_PATHS = {
    "/api/state", "/api/outbound", "/api/approvals", "/api/legs",
    "/api/value", "/api/ui-registry", "/api/current-truth",
    "/api/ops", "/api/ops/brain", "/api/ops/leads", "/api/ops/tasks",
    # نمایِ lifecycle (miniapp_state.get_lifecycle_state، پشتِ OCTOPUS_PF_MINIAPP).
    # برشِ ۳ این مسیر را هنگامِ بستنِ route های read جا انداخته بود: handler در
    # miniapp_state.py هست ولی هرگز dispatch نمی‌شد → 404 حتی با فلگِ روشن.
    # تاشویِ یکسانِ gate ِ owner-auth (t_no_read_route_bypasses_the_shared_gate_function).
    "/api/lifecycle",
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


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def read_gate_enabled() -> bool:
    return os.environ.get(READ_GATE_FLAG, "1") == "1"


# ⚠️ کپیِ import-امنِ الگوی redaction ِ 8773 (نه import ِ متقابل از live/server —
# پروسه/مسیرِ جدا نباید به آن گره بخورد). fail-closed: لایهٔ اصلی نبود →
# الگوهای سخت؛ متنِ خام هرگز بیرون نمی‌رود. الگوها با HARD_SECRET_PATTERNS ِ
# cockpit_readmodel هم‌راستا هستند.
_FALLBACK_SECRET = (
    r"\d{8,12}:AA[A-Za-z0-9_-]{30,}",      # توکن بات تلگرام
    r"sk-[A-Za-z0-9_-]{20,}",               # کلیدهای sk-*
    r"-----BEGIN [A-Z ]*KEY",               # PEM
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
        return _re.sub(r"\b[0-9a-fA-F]{64}\b", "‹hex64:حذف‌شده›", t)


def validate_init_data(init_data: str, *, bot_token: str, owner_id,
                       now: "float | None" = None) -> "dict | None":
    """اعتبارسنجیِ initData ِ Telegram WebApp طبق PLAN-T4 §۲.

    خروجی: dict ِ user در موفقیت؛ هر شکست (به هر دلیل) = None — صداکننده 403
    با بدنهٔ خالی می‌دهد و هیچ جزئیاتی لو نمی‌رود."""
    try:
        if not init_data or not bot_token or owner_id in (None, ""):
            return None
        data = dict(parse_qsl(str(init_data), keep_blank_values=True))
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
        age = now - auth_date
        if auth_date <= 0 or age > AUTH_MAX_AGE_S or age < -60.0:
            return None                                   # ضدِ replay
        user = json.loads(data.get("user") or "{}")
        if int(user.get("id")) != int(owner_id):
            return None                                   # allowlist تک‌نفره
        return user
    except Exception:  # noqa: BLE001 — شک = رد
        return None


# اسنیپتِ تزریقی به شِل: initData را روی هر fetch در هدر می‌گذارد. شِل خودش
# صفر داده دارد؛ داده فقط بعد از دیوارِ HMAC می‌آید.
_INJECT = ("<script>(function(){var g=function(){try{return (window.Telegram&&"
           "window.Telegram.WebApp&&window.Telegram.WebApp.initData)||''}catch(e)"
           "{return ''}};var f=window.fetch.bind(window);window.fetch=function(u,o)"
           "{o=o||{};var h=new Headers(o.headers||{});var d=g();"
           "if(d){h.set('X-Tg-Init-Data',d)}o.headers=h;return f(u,o)};})();"
           "</script>")


def _miniapp_static_response(path: str) -> tuple:
    """Serve the committed read-only cockpit shell/assets from disk.
    Only an explicit allowlist is served; no path traversal and no directory
    listing. The page contains no secrets and all mutating actions remain
    disabled in the frontend/backend until owner auth is explicitly wired.
    """
    p = str(path or "").split("?", 1)[0]
    if p in ("/miniapp", "/miniapp/"):
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
        snippet = _INJECT.encode("utf-8")
        if b"</body>" in body:
            body = body.replace(b"</body>", snippet + b"</body>", 1)
        else:
            body = body + snippet
    return 200, body, ctype

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


def _stopped() -> bool:
    try:
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


def handle(method: str, path: str, headers, *, fetch_fn=None,
           now: "float | None" = None) -> tuple:
    """پوششِ نازکِ `_handle_core` که رسیدِ per-request می‌نویسد.

    `authed` مشتق است نه حدس: تنها مسیری که پشتِ دیوارِ HMAC است
    `/api/miniapp` است، و تنها وقتی وضعیتِ ۲xx/3xx می‌دهد که
    `validate_init_data` پاس شده باشد (هر شکست = 403 با بدنهٔ خالی)."""
    st, body, ctype = _handle_core(method, path, headers, fetch_fn=fetch_fn, now=now)
    p = str(path or "").split("?", 1)[0]
    _log_hit(path, st, p == "/api/miniapp" and 200 <= int(st) < 400)
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
    if method_u == "POST" and p != "/api/actions":
        return 405, b"", "text/plain; charset=utf-8"
    if p in ("/miniapp", "/miniapp/", "/miniapp/app.js", "/miniapp/style.css",
             "/miniapp/tg_shell.js", "/tg_shell.js", "/app.js", "/style.css"):
        return _miniapp_static_response(p)
    if p == "/api/actions":
        if method_u != "POST":
            return 405, b"", "text/plain; charset=utf-8"
        token = os.environ.get("TG_CENTER_BOT_TOKEN", "")
        owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
        init_data = _get_header(headers, "X-Tg-Init-Data") or ""
        if not token or not owner or validate_init_data(init_data, bot_token=token, owner_id=owner, now=now) is None:
            return 403, b'{"ok":false,"status":"DENIED","reason":"owner_auth_required"}', "application/json; charset=utf-8"
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
                res = eng.execute(action, action_payload, {"is_owner": True}, action_id=action_id)
                body = json.dumps(res, ensure_ascii=False, sort_keys=True).encode("utf-8")
                return 200, body, "application/json; charset=utf-8"
            finally:
                eng.close()
        except Exception as exc:
            body = json.dumps({"ok": False, "status": "ERROR", "reason": type(exc).__name__}, ensure_ascii=False).encode("utf-8")
            return 500, body, "application/json; charset=utf-8"
    if p == "/api/miniapp":
        token = os.environ.get("TG_CENTER_BOT_TOKEN", "")
        owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
        init_data = _get_header(headers, "X-Tg-Init-Data") or ""
        if not token or not owner:
            return 403, b"", "text/plain; charset=utf-8"   # پیکربندیِ ناقص = بسته
        if validate_init_data(init_data, bot_token=token, owner_id=owner,
                              now=now) is None:
            return 403, b"", "text/plain; charset=utf-8"
        st, body, ctype = fetch("/api/miniapp")
        if st == 200:
            # دفاعِ دولایه: 8773 خودش redact کرده؛ این لایه دوباره رد می‌کند.
            body = _redact(body.decode("utf-8", "replace")).encode("utf-8")
        return st, body, ctype
    # PHASE 4 (2026-08-02): read-only /api/* cockpit helpers (secret-scrubbed, fail-closed).
    # No POST/PUT/DELETE here — read-only. Actions are Phase 7 (owner-gated, not wired yet).
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
        token = os.environ.get("TG_CENTER_BOT_TOKEN", "")
        owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
        init_data = _get_header(headers, "X-Tg-Init-Data") or ""
        if not token or not owner:
            return 403, b"", "text/plain; charset=utf-8"   # پیکربندیِ ناقص = بسته
        if validate_init_data(init_data, bot_token=token, owner_id=owner,
                              now=now) is None:
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
    return 404, b"{}", "application/json; charset=utf-8"


class _Srv(ThreadingHTTPServer):
    allow_reuse_address = False       # ویندوز: تک‌نمونگیِ واقعی

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


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
        self.send_header("Cache-Control", "no-store")
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
