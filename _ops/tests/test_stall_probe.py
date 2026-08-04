#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_stall_probe.py — دیده‌بانی که باید **قبل از مرگ** حرف بزند.

۲۰۲۶-۰۸-۰۴. مرکز دو بار ~۲٫۵ ساعت هنگ کرد و علتش نامعلوم ماند، چون
`RUN-TG-CENTER.bat` پایتون را بدونِ هیچ ریدایرکتی اجرا می‌کند ⇒ stdout/stderr
هیچ‌جا نمی‌رود.

سه چیزی که اگر بشکند، این ماژول بی‌فایده است:

۱. **آستانه باید زیرِ آستانهٔ کشتن باشد.** واچ‌داگ در ۳۰۰ ثانیه می‌کُشد. اگر
   دیده‌بان دیرتر بنویسد، پروسه قبل از ثبتِ پشته مرده است و باز هیچ
   نمی‌فهمیم — یک ابزارِ تشخیصی که همیشه دیر می‌رسد.
۲. **پشتهٔ همهٔ نخ‌ها، نه فقط نخِ اصلی.** ممکن است نخِ اصلی سالم باشد و یک
   لِنِ پس‌زمینه گیر کرده باشد.
۳. **گارد نباید گرگ‌گرگ کند.** در یک اپیزودِ هنگ فقط یک پشته، وگرنه هر ۲۰
   ثانیه یک ریخت و فایل می‌ترکد.
"""
import ast
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("stall-probe")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops" / "telegram_center"))

import stall_probe as sp  # noqa: E402

WD = harness.REAL_VAULT / "_ops" / "tg-center-watchdog.ps1"
CENTER = harness.REAL_VAULT / "_ops" / "telegram_center" / "center.py"


def _write_pulse(age_s: float):
    import datetime as _dt
    import json
    p = sp.pulse_path()
    assert str(harness.REAL_VAULT).lower() not in str(p).lower(), ("‼️ زنده", str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.fromtimestamp(time.time() - age_s).isoformat(timespec="seconds")
    p.write_text(json.dumps({"ts": ts, "pid": 1, "mono": 1.0}), encoding="utf-8")
    return p


def _clear_dump():
    d = sp.dump_path()
    try:
        if d.exists():
            d.unlink()
    except OSError:
        pass
    return d


def t_a_the_threshold_is_below_the_killer():
    """⚠️ باربرترین ناوردی: واچ‌داگ در ۳۰۰ ثانیه می‌کُشد. اگر دیده‌بان دیرتر
    بنویسد، هر بار **بعد از مرگ** می‌رسد و هیچ‌وقت چیزی ثبت نمی‌شود."""
    assert WD.exists(), WD
    src = WD.read_text("utf-8", errors="replace")
    import re
    m = re.search(r"\$HUNG_AFTER_S\s*=\s*(\d+)", src)
    assert m, "آستانهٔ کشتنِ واچ‌داگ پیدا نشد — این گارد کور شده"
    killer = int(m.group(1))
    assert sp.STALL_AFTER_S < killer, (
        "دیده‌بان دیرتر از کشتن می‌نویسد ⇒ همیشه بعد از مرگ می‌رسد",
        sp.STALL_AFTER_S, killer)
    assert sp.POLL_S < (killer - sp.STALL_AFTER_S), (
        "فاصلهٔ پایش از پنجرهٔ باقی‌مانده بزرگ‌تر است ⇒ ممکن است پنجره را رد کند",
        sp.POLL_S, killer - sp.STALL_AFTER_S)


def t_b_it_reads_the_same_pulse_file_the_watchdog_reads():
    """دو ناظر با دو منبعِ حقیقت، روزی دو حکمِ متضاد می‌دهند."""
    src = WD.read_text("utf-8", errors="replace")
    assert "state\\pulse\\tg-center.json" in src or "pulse/tg-center.json" in src, src[:200]
    assert sp.pulse_path().name == "tg-center.json"
    assert sp.pulse_path().parent.name == "pulse"


def t_c_a_fresh_pulse_is_not_a_stall():
    _write_pulse(5)
    age = sp.pulse_age_s()
    assert age is not None and age < 60, age


def t_d_a_stale_pulse_is_detected():
    _write_pulse(1000)
    age = sp.pulse_age_s()
    assert age is not None and age > sp.STALL_AFTER_S, age


def t_e_an_unreadable_pulse_is_unknown_not_healthy():
    """⚠️ «نبودِ داده حکم نیست». نبضِ خراب نباید «سالم» تفسیر شود — ولی
    نباید ریختِ پشته هم بسازد، چون آن‌وقت هر خرابیِ دیسک یک هشدارِ کاذب است."""
    p = sp.pulse_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{ این JSON نیست", encoding="utf-8")
    assert sp.pulse_age_s() is None, "نبضِ خراب عددی برگرداند"
    try:
        p.unlink()
    except OSError:
        pass
    assert sp.pulse_age_s() is None, "نبضِ غایب عددی برگرداند"


def t_f_the_dump_contains_every_thread():
    """نخِ اصلی ممکن است سالم باشد و لِنِ پس‌زمینه گیر کرده باشد."""
    import threading
    d = _clear_dump()
    ready = threading.Event()
    hold = threading.Event()

    def _parked():
        ready.set()
        hold.wait(10)

    th = threading.Thread(target=_parked, name="probe-parked-thread", daemon=True)
    th.start()
    ready.wait(5)
    try:
        assert sp.write_dump("test", age=999) is True
        txt = d.read_text("utf-8", errors="replace")
    finally:
        hold.set()
    # ⚠️ `faulthandler` فقط `Thread 0x…` می‌نویسد — شناسهٔ هگز بدونِ نام. پس
    # پشتهٔ خام برای «کدام لِن گیر کرده؟» تقریباً بی‌فایده است. راهنمای نام‌ها
    # همان چیزی است که این تست کشفش کرد.
    assert "probe-parked-thread" in txt, (
        "نامِ نخ در راهنما نیست ⇒ پشته ناخوانا است و «کدام لِن؟» بی‌جواب "
        "می‌ماند", txt[:500])
    # ⚠️ `faulthandler` نخِ جاری را «Current thread 0x…» می‌نویسد (t کوچک) و
    # بقیه را «Thread 0x…». شمارشِ حساس‌به‌حروف فقط یکی می‌بیند.
    import re as _re
    assert len(_re.findall(r"(?i)\bthread 0x", txt)) >= 2, (
        "پشتهٔ چندنخی ثبت نشد ⇒ گیرکردنِ یک لِن نامرئی می‌ماند", txt[:400])
    assert f"0x{th.ident:08x}" in txt, ("شناسهٔ نخ با راهنما نمی‌خواند", txt[:400])
    assert "reason=test" in txt and "pulse_age=999" in txt, txt[:300]


def t_g_the_dump_never_leaks_a_secret_or_message_text():
    """§۱۰ — پشته کد است، نه محتوا."""
    d = _clear_dump()
    sp.write_dump("test")
    txt = d.read_text("utf-8", errors="replace")
    import re
    assert not re.search(r"\d{8,12}:AA[A-Za-z0-9_-]{20,}", txt), "توکن در پشته"
    assert "trycloudflare" not in txt, "‏URL تونل در پشته"


def t_h_a_stall_dumps_once_not_every_poll():
    """گاردی که هر ۲۰ ثانیه یک پشته بنویسد، فایل را می‌ترکاند و خاموش می‌شود."""
    d = _clear_dump()
    _write_pulse(1000)
    evt = sp.start(stall_after_s=1.0, poll_s=0.05, redump_every_s=600.0)
    assert evt is not None
    try:
        time.sleep(0.6)
    finally:
        evt.set()
    txt = d.read_text("utf-8", errors="replace") if d.exists() else ""
    assert txt.count("reason=pulse-stalled") == 1, (
        "در یک اپیزود بیش از یک پشته نوشت", txt.count("reason=pulse-stalled"))


def t_i_a_healthy_pulse_produces_no_dump():
    """قرینه، و لازم: دیده‌بانی که روی سیستمِ سالم هم بنویسد، بی‌معنی است."""
    d = _clear_dump()
    _write_pulse(1)
    evt = sp.start(stall_after_s=300.0, poll_s=0.05)
    try:
        time.sleep(0.4)
    finally:
        evt.set()
    assert not d.exists(), "روی نبضِ سالم پشته نوشت"


def t_j_the_center_actually_starts_the_probe():
    """⚠️ ماژولی که هیچ‌کس صدایش نمی‌زند یک «قابلیتِ تاریک» است."""
    src = CENTER.read_text("utf-8", errors="replace")
    fn = next((n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.FunctionDef) and n.name == "run_forever"), None)
    assert fn is not None, "run_forever پیدا نشد"
    seg = ast.get_source_segment(src, fn) or ""
    assert "stall_probe" in seg and "start()" in seg, (
        "مرکز دیده‌بان را روشن نمی‌کند ⇒ ماژول تاریک است")
    i_start = seg.find("stall_probe")
    i_loop = seg.find("while not self.stopped()")
    assert 0 <= i_start < i_loop, "دیده‌بان بعد از حلقه روشن می‌شود ⇒ هرگز"


def t_k_the_probe_thread_is_a_daemon():
    """نخِ غیرdaemon جلوی خاموش‌شدنِ تمیزِ مرکز را می‌گیرد."""
    import threading
    _write_pulse(1)
    before = {t.name for t in threading.enumerate()}
    evt = sp.start(stall_after_s=300.0, poll_s=0.05)
    try:
        time.sleep(0.2)
        th = [t for t in threading.enumerate()
              if t.name == "stall-probe" and t.name not in before]
        assert th, "نخِ دیده‌بان بالا نیامد"
        assert th[0].daemon is True, "نخ daemon نیست"
    finally:
        evt.set()


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_stall_probe: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
