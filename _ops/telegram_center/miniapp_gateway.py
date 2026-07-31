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
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_TG_MINIAPP"
PORT = int(os.environ.get("OCTOPUS_MINIAPP_PORT", "8774"))
UPSTREAM_PORT = int(os.environ.get("LIVE_PORT", "8773"))
AUTH_MAX_AGE_S = 300.0
STOP_NAME = "STOP-MINIAPP"


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


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


def _default_fetch(path: str) -> tuple:
    """proxy ِ loopback به 8773 — فقط GET، فقط دو مسیرِ سفید. (status, body, ctype)."""
    url = f"http://127.0.0.1:{UPSTREAM_PORT}{path}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            ctype = r.headers.get("Content-Type") or "application/json; charset=utf-8"
            return int(r.status), r.read(), ctype
    except Exception:  # noqa: BLE001 — بالادستی خاموش = جوابِ صادقِ ساده
        return 502, b"", "text/plain; charset=utf-8"


def _stopped() -> bool:
    try:
        return (Path(opslib.OPS) / STOP_NAME).exists()
    except Exception:  # noqa: BLE001 — شک = توقف (fail-closed)
        return True


def handle(method: str, path: str, headers, *, fetch_fn=None,
           now: "float | None" = None) -> tuple:
    """هستهٔ خالص/تزریق‌پذیرِ gateway → (status:int, body:bytes, ctype:str).

    تست‌ها همین را مستقیم صدا می‌زنند (بدونِ سرورِ واقعی)؛ لایهٔ HTTP فقط
    همین را wrap می‌کند. headers هر شیءِ dict-مانند با .get است."""
    fetch = fetch_fn if fetch_fn is not None else _default_fetch
    if _stopped():
        return 503, b"", "text/plain; charset=utf-8"       # کلیدِ کشتار
    if str(method or "").upper() != "GET":
        return 405, b"", "text/plain; charset=utf-8"       # فقط‌خواندنی — صفر POST
    p = str(path or "").split("?", 1)[0]
    if p in ("/miniapp", "/miniapp/"):
        st, body, ctype = fetch("/miniapp")
        if st == 200:
            snippet = _INJECT.encode("utf-8")
            if b"</body>" in body:
                body = body.replace(b"</body>", snippet + b"</body>", 1)
            else:
                body = body + snippet
        return st, body, ctype
    if p == "/api/miniapp":
        token = os.environ.get("TG_CENTER_BOT_TOKEN", "")
        owner = os.environ.get("TELEGRAM_OWNER_CHAT_ID", "")
        init_data = ""
        try:
            init_data = headers.get("X-Tg-Init-Data") or ""
        except Exception:  # noqa: BLE001
            init_data = ""
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
    return 404, b"{}", "application/json; charset=utf-8"


class _Srv(ThreadingHTTPServer):
    allow_reuse_address = False       # ویندوز: تک‌نمونگیِ واقعی

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _Handler(BaseHTTPRequestHandler):
    def _run(self, method: str):
        st, body, ctype = handle(method, self.path, self.headers)
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
    if not enabled():
        print(f"miniapp_gateway: {FLAG} خاموش است — هیچ پورتی باز نشد (خروجِ تمیز).")
        return 0
    if _stopped():
        print(f"miniapp_gateway: {STOP_NAME} حاضر است — شروع رد شد.")
        return 0
    try:
        srv = _Srv(("127.0.0.1", PORT), _Handler)
    except OSError:
        print(f"miniapp_gateway: نمونهٔ دیگری روی {PORT} زنده است — خروجِ تمیز.")
        return 0
    print(f"miniapp_gateway: دیوارِ Mini App روی http://127.0.0.1:{PORT}")
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
