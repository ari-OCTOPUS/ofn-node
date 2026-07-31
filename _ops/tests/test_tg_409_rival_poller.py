#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_409_rival_poller.py — رگرسیونِ تشخیصِ pollerِ رقیب (Wave 1.4).

قانونی که این تست محافظت می‌کند (یافتهٔ boundary-12):

  تا ۲۰۲۶-۰۷-۳۱ `tg_api.poll_updates` روی هر پاسخِ غیر-ok بی‌صدا [] برمی‌گرداند.
  اگر یک پروسهٔ دوم روی همان توکن getUpdates بزد، تلگرام ۴۰۹ Conflict می‌دهد،
  و باتِ مرکز ساکت می‌شد — تنها نشانه، یک «غیبت» بود (هیچ لاگ، هیچ رسید، هیچ
  هشدار). approval_channel.poll_once این را قبلاً داشت (جلسه ۴۶) ولی روی باتِ
  مرکز اجرا نمی‌شد.

  حالا poll_updates الگوی ۴۰۹ را دارد: هشدارِ throttled (۱/ساعت) وقتی
  error_code == 409. این تست با یک get-fn تزریق‌شده که ۴۰۹ برمی‌گرداند ثابت
  می‌کند که هشدار صادر می‌شود و [] برمی‌گردد (نه استثنا).
"""
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness  # noqa: E402


def _make_client(get_fn, alert_sink=None):
    """یک TgClient با get_fn و post_fn تزریقی، و alert_sink برای گرفتنِ هشدار."""
    import tg_api
    if alert_sink is not None:
        tg_api._alert_soft = lambda msg: alert_sink.append(msg)
    c = tg_api.TgClient(token="fake:token", owner_chat_id=123, center_chat_id=-100,
                        get_fn=get_fn)
    return c, tg_api


def t_poll_returns_empty_on_409():
    """۴۰۹ نباید استثنا پرتاب کند — باید [] برگرداند (fail-soft)."""
    def fake_get(url, timeout):
        return {"ok": False, "error_code": 409,
                "description": "Conflict: terminated by other getUpdates request"}
    c, _ = _make_client(fake_get)
    result = c.poll_updates()
    assert result == [], f"409 should return [], got {result!r}"


def t_poll_alerts_on_409():
    """۴۰۹ باید یک هشدارِ throttled صادر کند (نه سکوت)."""
    sink = []
    def fake_get(url, timeout):
        return {"ok": False, "error_code": 409, "description": "Conflict"}
    c, _ = _make_client(fake_get, alert_sink=sink)
    c.poll_updates()
    assert sink, "no alert emitted on 409 — رقیب‌poller ساکت می‌ماند"
    assert "409" in sink[0] or "Conflict" in sink[0], (
        f"alert does not mention 409/Conflict: {sink[0]!r}")


def t_409_alert_is_throttled_to_once_per_hour():
    """دو ۴۰۹ پیاپی نباید دو هشدار بزنند — throttle ۱/ساعت."""
    sink = []
    def fake_get(url, timeout):
        return {"ok": False, "error_code": 409, "description": "Conflict"}
    c, _ = _make_client(fake_get, alert_sink=sink)
    c.poll_updates()   # first → alert
    c.poll_updates()   # second → throttled, no alert
    assert len(sink) == 1, (
        f"409 alert not throttled: {len(sink)} alerts for 2 polls (expected 1)")


def t_non_409_error_still_silent():
    """خطای غیرِ ۴۰۹ (مثلاً ۵۰۰) همچنان بی‌صدا [] است — فقط ۴۰۹ هشدار دارد."""
    sink = []
    def fake_get(url, timeout):
        return {"ok": False, "error_code": 500, "description": "Internal"}
    c, _ = _make_client(fake_get, alert_sink=sink)
    result = c.poll_updates()
    assert result == []
    assert not sink, f"non-409 error should not alert: {sink!r}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_409_rival_poller: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
