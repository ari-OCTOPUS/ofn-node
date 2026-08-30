#!/usr/bin/env python3
"""test_httpauth.py — گاردِ CSRF/Origin مشترکِ سرورهای loopback (RC1، فلگ OCTOPUS_HTTP_AUTH).

قرارداد (بایت‌به‌بایت با httpauth.py — secure-by-default از 2026-07-20 Stage-1):
- enabled(): unset→True · ""→True · 1/on/yes→True · 0/false/no/off→False.
- گارد روشن (پیش‌فرض یا صریح) + Originِ خارجی → ۴۰۳ (رد؛ بردارِ «صفحهٔ وبِ مخرب»).
- گارد روشن + Originِ loopback → True.
- گارد روشن + بدونِ Origin/Referer (curl/اسکریپتِ محلی) → True (مرورگر نیست).
- گارد روشن + Refererِ loopback (Origin غایب) → True؛ Refererِ خارجی → ۴۰۳.
- گاردِ خاموشِ صریح (0/false/no/off) → guard_post همیشه True، حتی cross-origin (rollback/دیباگ).
$0 آفلاین، بدونِ شبکه/سرورِ واقعی — فقط یک handlerِ ساختگی که هدرها/۴۰۳ را ضبط می‌کند.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))        # _ops/ → httpauth.py

import harness      # noqa: E402
import httpauth     # noqa: E402

FLAG = httpauth.FLAG   # "OCTOPUS_HTTP_AUTH"


class _FakeHandler:
    """کمینه‌ترین شبیه‌سازِ BaseHTTPRequestHandler برای guard_post: headers + ضبطِ ۴۰۳."""
    def __init__(self, headers=None):
        self.headers = dict(headers or {})
        self.status = None
        self.sent_headers = []
        self.body = b""
        self.wfile = self

    def send_response(self, code):
        self.status = code

    def send_header(self, key, value):
        self.sent_headers.append((key, value))

    def end_headers(self):
        pass

    def write(self, data):
        self.body += data


def _guard(headers, flag):
    """یک فراخوانِ ایزوله: env را ست/پاک می‌کند تا نشتی بینِ تست‌ها نباشد."""
    import os
    prev = os.environ.get(FLAG)
    if flag is None:
        os.environ.pop(FLAG, None)
    else:
        os.environ[FLAG] = flag
    try:
        h = _FakeHandler(headers)
        allowed = httpauth.guard_post(h)
        return allowed, h
    finally:
        if prev is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = prev


def t_enabled_matrix_secure_by_default():
    """enabled(): unset→True, ""→True, on-words→True; فقط 0/false/no/off→False."""
    import os
    prev = os.environ.get(FLAG)
    try:
        os.environ.pop(FLAG, None)
        assert httpauth.enabled() is True, "unset باید secure-by-default = روشن باشد"
        for on in ("", "1", "on", "yes", "true", "TRUE", "anything"):
            os.environ[FLAG] = on
            assert httpauth.enabled() is True, f"{on!r} باید روشن باشد"
        for off in ("0", "false", "no", "off", "OFF", " off "):
            os.environ[FLAG] = off
            assert httpauth.enabled() is False, f"{off!r} باید خاموش باشد"
    finally:
        if prev is None:
            os.environ.pop(FLAG, None)
        else:
            os.environ[FLAG] = prev


def t_a_default_on_cross_origin_403():
    """فلگ unset (پیش‌فرضِ امن) → cross-origin رد می‌شود (۴۰۳)."""
    allowed, h = _guard({"Origin": "https://evil.example.com"}, flag=None)
    assert allowed is False and h.status == 403, "unset باید گارد را روشن کند"


def t_b_explicit_off_passes_cross_origin():
    """فقط خاموشِ صریح (0/false/no/off) گارد را می‌بندد → cross-origin عبور."""
    for off in ("0", "false", "off", "no"):
        allowed, h = _guard({"Origin": "https://evil.example.com"}, flag=off)
        assert allowed is True and h.status is None, f"{off!r} باید خاموش تلقی شود"


def t_c_flag_on_cross_origin_403():
    allowed, h = _guard({"Origin": "https://evil.example.com"}, flag="1")
    assert allowed is False
    assert h.status == 403
    assert b"cross-origin" in h.body
    assert any(k == "Content-Type" for k, _ in h.sent_headers)


def t_d_flag_on_loopback_origin_passes():
    for host in ("http://127.0.0.1:8787", "http://localhost:9000", "http://[::1]:5000"):
        allowed, h = _guard({"Origin": host}, flag="1")
        assert allowed is True, host
        assert h.status is None, host


def t_e_flag_on_no_headers_passes():
    allowed, h = _guard({}, flag="1")
    assert allowed is True
    assert h.status is None


def t_f_flag_on_referer_fallback():
    ok_allowed, ok_h = _guard({"Referer": "http://127.0.0.1:8787/panel"}, flag="1")
    assert ok_allowed is True and ok_h.status is None
    bad_allowed, bad_h = _guard({"Referer": "https://evil.example.com/x"}, flag="1")
    assert bad_allowed is False and bad_h.status == 403


def t_g_flag_on_origin_wins_over_referer():
    allowed, h = _guard({"Origin": "https://evil.example.com",
                         "Referer": "http://127.0.0.1:8787/"}, flag="1")
    assert allowed is False and h.status == 403


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_httpauth: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
