#!/usr/bin/env python3
"""httpauth.py — گاردِ CSRF/Origin مشترکِ سرورهای loopback اختاپوس (RC1).

مدلِ تهدید (سه یافتهٔ High امنیتی ۰۷-۱۶): یک صفحهٔ وبِ مخرب در مرورگرِ خودِ مالک که
بی‌صدا به 127.0.0.1 POST می‌کند (CSRF) → اجرای کد از فایلِ فلگ / دور زدنِ STOP /
پاک‌شدنِ گاردها. مرورگر روی هر POSTِ cross-origin هدرِ Origin (یا دستِ‌کم Referer)
می‌فرستد که جاوااسکریپتِ صفحه نمی‌تواند override کند — پس بررسیِ loopback بودنِ مبدأ،
این بردار را می‌بندد بی‌آنکه صفحات نیاز به بازنویسی/توکن داشته باشند.

انضباط: پشتِ فلگِ OCTOPUS_HTTP_AUTH. خاموش (پیش‌فرض) = رفتارِ امروز بایت‌به‌بایت.
روشن = فقط مبدأِ loopback؛ شک/خطا = رد (fail-closed). bind روی loopback تغییر نمی‌کند.
stdlib-only · هیچ secret نمی‌سازد/echo نمی‌کند.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

FLAG = "OCTOPUS_HTTP_AUTH"
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def enabled() -> bool:
    """آیا گاردِ HTTP روشن است؟ (پیش‌فرض خاموش = رفتارِ محافظه‌کارِ قبلی)."""
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _host_ok(url: str) -> bool:
    try:
        return urlparse(url).hostname in _LOOPBACK
    except Exception:  # noqa: BLE001
        return False


def origin_ok(handler) -> bool:
    """آیا این درخواستِ تغییردهنده از مبدأِ loopback (خودِ مالک) است؟
    - Origin موجود → باید loopback باشد (صفحهٔ خارجی = رد).
    - Origin غایب ولی Referer موجود → Referer باید loopback باشد.
    - هر دو غایب → مرورگر نیست (curl/اسکریپتِ محلیِ خودِ مالک) → مجاز؛ این بردارِ CSRFِ
      «صفحهٔ وبِ مخرب» نیست (مرورگر روی POST همیشه Origin/Referer می‌گذارد)."""
    try:
        origin = handler.headers.get("Origin")
        if origin:
            return _host_ok(origin)
        referer = handler.headers.get("Referer")
        if referer:
            return _host_ok(referer)
        return True
    except Exception:  # noqa: BLE001 — شک = رد وقتی فلگ روشن است (fail-closed)
        return False


def guard_post(handler) -> bool:
    """درِ واحد برای do_POST. True = ادامه بده؛ False = ۴۰۳ فرستاده شد، برگرد.

    فلگ خاموش → همیشه True (رفتارِ امروز، بایت‌به‌بایت). فلگ روشن → فقط مبدأِ loopback."""
    if not enabled():
        return True
    if origin_ok(handler):
        return True
    try:
        body = b'{"ok":false,"reason":"cross-origin POST rejected (OCTOPUS_HTTP_AUTH)"}'
        handler.send_response(403)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
    except Exception:  # noqa: BLE001 — نتوانستیم ۴۰۳ بفرستیم؛ باز هم درخواست را اجرا نکن
        pass
    return False
