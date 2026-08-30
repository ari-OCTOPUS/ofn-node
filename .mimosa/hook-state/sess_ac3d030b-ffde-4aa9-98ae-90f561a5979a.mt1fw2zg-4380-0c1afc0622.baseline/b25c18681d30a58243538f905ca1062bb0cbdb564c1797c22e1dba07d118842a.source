#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_poll_health.py — گوشِ مرده باید دیده شود، نه حدس زده.

مسئله‌ای که این تست قفل می‌کند (صبحِ ۲۰۲۶-۰۸-۰۱، منتظرِ «سلام» مالک):

  مسیرِ **دریافت** تنها بخشی از تلگرام بود که هیچ ردی از خودش نمی‌گذاشت.
  ارسال رسید دارد؛ ۴۰۹ (پولرِ رقیب) از ۰۷-۳۱ هشدار دارد؛ ولی هر خطای دیگری —
  `URLError`، DNS، تایم‌اوت — بی‌صدا `[]` برمی‌گرداند. از بیرون این دقیقاً
  شبیهِ «کسی پیام نداده» است. آن صبح دو ساعت نمی‌شد این دو حالت را از هم جدا
  کرد، و لاگِ هشدارها نشان داد ساعت ۰۶:۴۴ یک `URLError` واقعاً خورده بود.

قواعدی که این‌جا گارد می‌شوند:
  · دورِ **موفقِ خالی** هم ثبت می‌شود. اگر فقط دورهایی که آپدیت آورده‌اند ثبت
    شوند، «گوشِ سالمِ ساکت» و «گوشِ مرده» دوباره یک شکل می‌شوند — یعنی همان
    باگ با یک فایلِ جدید.
  · شکست، `last_ok_ts` را پاک نمی‌کند (وگرنه «چقدر است که کریم؟» بی‌معنا).
  · ندانستن هرگز «سالم» گزارش نمی‌شود: بدونِ فایل ⇒ `None`، نه صفر.
  · یک لرزشِ تکیِ شبکه هشدار نمی‌دهد؛ هشدارِ گرگ‌گرگ بدتر از سکوت است.
"""
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import harness  # noqa: E402

ENV = harness.setup("tg-poll-health")     # قبل از هر importی که state می‌نویسد

import tg_api  # noqa: E402


def _client(get_fn, alert_sink=None):
    if alert_sink is not None:
        tg_api._alert_soft = lambda msg: alert_sink.append(msg)
    return tg_api.TgClient(token="fake:token", owner_chat_id=123,
                           center_chat_id=-100, get_fn=get_fn)


def _reset():
    p = tg_api._poll_health_path()
    if p.exists():
        p.unlink()
    return p


def _state():
    return json.loads(tg_api._poll_health_path().read_text("utf-8"))


def t_a_quiet_healthy_round_still_leaves_a_mark():
    """هیچ آپدیتی نیامد ولی تماس موفق بود ⇒ باید ثبت شود.

    این قلبِ ماجراست: اگر فقط دورهای پرآپدیت ثبت شوند، سکوتِ سالم و کوریِ
    کامل دوباره از هم قابلِ تشخیص نیستند."""
    _reset()
    c = _client(lambda url, timeout: {"ok": True, "result": []})
    assert c.poll_updates() == []
    st = _state()
    assert st["last_ok_ts"] > 0, st
    assert st["consecutive_failures"] == 0, st


def t_b_a_failed_round_counts_and_keeps_the_last_success():
    _reset()
    c = _client(lambda url, timeout: {"ok": True, "result": []})
    c.poll_updates()
    ok_ts = _state()["last_ok_ts"]

    def boom(url, timeout):
        raise OSError("network down")

    c2 = _client(boom)
    assert c2.poll_updates() == []
    st = _state()
    assert st["consecutive_failures"] == 1, st
    assert st["last_ok_ts"] == ok_ts, "شکست نباید آخرین موفقیت را پاک کند"
    assert "OSError" in str(st.get("last_reason")), st


def t_c_not_knowing_is_never_reported_as_healthy():
    _reset()
    assert tg_api.poll_deaf_for_s() is None, "بدونِ فایل باید None بدهد، نه ۰"


def t_c2_a_boot_that_never_succeeded_is_unknown_not_healthy():
    """فایل هست ولی هیچ موفقیتی داخلش نیست ⇒ باز هم «نمی‌دانم».

    سناریوی واقعی: مرکز بالا می‌آید و همان اولین تماسش شکست می‌خورد. فایل
    ساخته می‌شود با `last_ok_ts = 0`. اگر این حالت به‌جای None عددِ صفر بدهد،
    گزارش می‌شود «صفر ثانیه است که کر است» — یعنی سالم‌ترین حالتِ ممکن، دقیقاً
    وقتی که هرگز نشنیده. (جهشِ ۰۸-۰۱ همین‌جا زنده مانده بود: تستِ قبلی فقط
    حالتِ **نبودِ فایل** را می‌دید و به این خط نمی‌رسید.)"""
    p = _reset()

    def boom(url, timeout):
        raise OSError("down since boot")

    c = _client(boom)
    c.poll_updates()
    assert p.exists(), "دورِ ناموفق هم باید فایل بسازد"
    assert _state()["last_ok_ts"] == 0, _state()
    assert tg_api.poll_deaf_for_s() is None, "بوتِ بی‌موفقیت = نمی‌دانم، نه سالم"


def t_e2_the_first_failure_after_a_gap_waits_for_a_second_opinion():
    """یک شکستِ تنها — حتی با فاصلهٔ طولانی از آخرین موفقیت — هشدار نمی‌دهد.

    سناریوی واقعی: پروسه بعد از چند دقیقه خواب/ری‌استارت بالا می‌آید، فایل
    `last_ok_ts` ِ کهنه دارد و شمارنده صفر است. اولین تماس ممکن است سرِ همان
    لحظهٔ بالاآمدنِ شبکه بخورد؛ فریادزدن روی آن یعنی هشدارِ گرگ‌گرگ. دومین
    شکستِ پیاپی است که «الگو» می‌سازد."""
    p = _reset()
    sink = []
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"last_ok_ts": time.time() - (tg_api.POLL_DEAF_AFTER_S + 300),
                             "consecutive_failures": 0, "last_reason": ""}), "utf-8")

    def boom(url, timeout):
        raise OSError("first miss")

    c = _client(boom, alert_sink=sink)
    c.poll_updates()
    assert not sink, f"اولین شکست نباید فریاد بزند: {sink!r}"
    c.poll_updates()
    assert len(sink) == 1, f"دومین شکستِ پیاپی باید فریاد بزند: {sink!r}"


def t_d_deaf_duration_is_measured_from_the_last_success():
    _reset()
    c = _client(lambda url, timeout: {"ok": True, "result": []})
    c.poll_updates()
    gap = tg_api.poll_deaf_for_s(now=time.time() + 600)
    assert gap is not None and 590 < gap < 610, gap


def t_e_a_single_blip_does_not_cry_wolf():
    _reset()
    sink = []
    c = _client(lambda url, timeout: {"ok": True, "result": []}, alert_sink=sink)
    c.poll_updates()

    def boom(url, timeout):
        raise OSError("blip")

    c2 = _client(boom, alert_sink=sink)
    c2.poll_updates()
    assert not sink, f"یک لرزشِ تکی نباید هشدار بدهد: {sink!r}"


def t_f_a_truly_deaf_ear_shouts_once_per_hour():
    """دو شکستِ پیاپی + گذشتِ پنجره ⇒ هشدار؛ و دفعهٔ بعد throttle."""
    p = _reset()
    sink = []
    old = time.time() - (tg_api.POLL_DEAF_AFTER_S + 120)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"last_ok_ts": old, "consecutive_failures": 5,
                             "last_reason": "URLError"}), "utf-8")

    def boom(url, timeout):
        raise OSError("still down")

    c = _client(boom, alert_sink=sink)
    c.poll_updates()
    assert len(sink) == 1, f"گوشِ مرده باید فریاد بزند: {sink!r}"
    assert "نمی‌شنود" in sink[0] or "getUpdates" in sink[0], sink[0]
    c.poll_updates()
    assert len(sink) == 1, f"هشدار throttle نشد: {sink!r}"


def t_g_a_bad_api_payload_is_a_failed_round_too():
    """پاسخِ غیر-ok (۵۰۰/۴۲۹/۴۰۹) هم یک دورِ ناموفق است — نه «چیزی نیامد»."""
    _reset()
    c = _client(lambda url, timeout: {"ok": False, "error_code": 500,
                                      "description": "Internal"})
    assert c.poll_updates() == []
    st = _state()
    assert st["consecutive_failures"] == 1, st
    assert "500" in str(st.get("last_reason")), st


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_poll_health: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
