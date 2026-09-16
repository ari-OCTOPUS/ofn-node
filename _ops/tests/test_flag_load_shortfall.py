#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_flag_load_shortfall.py — پیکربندیِ نصفه باید سرِ boot داد بزند.

آنچه این گارد از تکرارش جلوگیری می‌کند (۲۰۲۶-۰۸-۰۱ ۰۹:۰۶):

  یک ویرایشِ متنی `OCTOPUS-flags.cmd` را از CRLF به LF برد. cmd.exe چنین فایلی
  را تقریباً **یک‌درمیان** اجرا می‌کند، پس مرکز در ۰۹:۰۷ با ۵۹ از ۱۵۶ فلگ بالا
  آمد. `OCTOPUS_TG_CAPTURE` بینِ گم‌شده‌ها بود؛ مالک ویس فرستاد و سیزده دقیقه
  هیچ اتفاقی نیفتاد، در حالی که سه پروسهٔ دیگر با پیکربندیِ کاملِ قبلی‌شان
  سالم کار می‌کردند.

  هیچ لایه‌ای نفهمید: فایل در پایتون تمیز پارس می‌شود (`splitlines()` به CRLF
  کاری ندارد)، پروسه بالا آمد، استثنایی نبود، و هر فلگی که بار شده بود درست
  بود. تنها نشانه یک **عدد** بود — و همان دو عدد از قبل، یک خط با فاصله، در
  همان فایلِ snapshot نوشته می‌شدند و کسی مقایسه‌شان نمی‌کرد.

قواعدِ قفل‌شده:
  · وضعِ سالم ساکت است (هشدارِ گرگ‌گرگ گارد را بی‌ارزش می‌کند).
  · سناریوی دقیقِ امروز — یک‌درمیان — هشدار می‌دهد.
  · فایلِ کوچک (تست/جعبه‌شنی) هشدار نمی‌دهد.
  · متغیرهای غیرِردیابی‌شده (کلیدهای `.env` و امثالش) در حساب نمی‌آیند.
  · هشدار هرگز boot را نمی‌کشد — پیکربندیِ ناقص بد است، پروسه‌ای که بالا
    نیامد بدتر.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness  # noqa: E402
ENV = harness.setup("flag-load-shortfall")

import flag_drift as fd  # noqa: E402


def _file_flags(n=156):
    return {("OCTOPUS_WIRE_F%03d" % i): "1" for i in range(n)}


def t_a_a_healthy_boot_is_silent():
    ff = _file_flags()
    sf = fd.load_shortfall(ff, dict(ff))
    assert sf["missing_count"] == 0 and not sf["alarm"], sf


def t_b_todays_every_other_line_collapse_fires():
    """سناریوی واقعیِ ۰۹:۰۷ — cmd.exe یک‌درمیان خواند."""
    ff = _file_flags()
    env = {k: v for i, (k, v) in enumerate(sorted(ff.items())) if i % 2 == 0}
    sf = fd.load_shortfall(ff, env)
    assert sf["alarm"], sf
    assert sf["missing_count"] == 78, sf
    assert 0.49 < sf["ratio"] < 0.51, sf
    assert sf["missing_sample"], "نمونهٔ گم‌شده‌ها خالی است — گزارش بی‌فایده می‌شود"


def t_c_a_total_wipeout_fires_too():
    """صفر فلگ از یک فایلِ پر = بدترین حالت، نه حالتِ خاصی که از قلم بیفتد."""
    sf = fd.load_shortfall(_file_flags(), {})
    assert sf["alarm"] and sf["ratio"] == 1.0, sf


def t_d_a_tiny_file_never_cries_wolf():
    sf = fd.load_shortfall({"OCTOPUS_A": "1", "OCTOPUS_B": "1"}, {})
    assert not sf["alarm"], sf


def t_e_one_missing_flag_out_of_many_is_below_the_bar():
    """یک فلگِ جاافتاده نوسان است نه فروپاشی؛ آستانه باید تحملش کند."""
    ff = _file_flags(100)
    env = dict(ff)
    env.pop(sorted(ff)[0])
    sf = fd.load_shortfall(ff, env)
    assert sf["missing_count"] == 1 and not sf["alarm"], sf


def t_f_untracked_env_keys_are_not_counted():
    """کلیدهای `.env` و متغیرهای سیستمی نباید عددِ env را باد کنند."""
    ff = _file_flags(30)
    env = dict(ff)
    env.update({"PATH": "x", "GMAIL_ADDRESS": "y", "RANDOM_THING": "z"})
    sf = fd.load_shortfall(ff, env)
    assert sf["file_count"] == 30 and not sf["alarm"], sf


def t_g_snapshot_records_the_shortfall_and_alerts_once():
    """snapshot باید هم عدد را ثبت کند هم داد بزند — ثبتِ بی‌صدا همان باگ است."""
    flags_file = Path(ENV["ORG_ROOT"]) / "OCTOPUS-flags.cmd"
    lines = ["set OCTOPUS_WIRE_F%03d=1\r\n" % i for i in range(40)]
    flags_file.write_text("".join(lines), encoding="utf-8", newline="")
    out = Path(ENV["ORG_ROOT"]) / "flags-loaded-test.json"

    said = []
    orig = fd._alert_shortfall
    fd._alert_shortfall = lambda sf, src: said.append(sf)
    try:
        env = {("OCTOPUS_WIRE_F%03d" % i): "1" for i in range(0, 40, 2)}
        doc = fd.snapshot(flags_file, out, env=env)
    finally:
        fd._alert_shortfall = orig

    assert "load_shortfall" in doc, "عدد اصلاً ثبت نشد"
    assert doc["load_shortfall"]["alarm"], doc["load_shortfall"]
    assert len(said) == 1, f"هشدار نرفت یا تکراری رفت: {len(said)}"
    on_disk = json.loads(out.read_text("utf-8"))
    assert on_disk["load_shortfall"]["missing_count"] == 20, on_disk["load_shortfall"]


def t_h_a_healthy_snapshot_stays_quiet():
    flags_file = Path(ENV["ORG_ROOT"]) / "OCTOPUS-flags-ok.cmd"
    flags_file.write_text(
        "".join("set OCTOPUS_WIRE_G%03d=1\r\n" % i for i in range(40)),
        encoding="utf-8", newline="")
    out = Path(ENV["ORG_ROOT"]) / "flags-loaded-ok.json"
    said = []
    orig = fd._alert_shortfall
    fd._alert_shortfall = lambda sf, src: said.append(sf)
    try:
        env = {("OCTOPUS_WIRE_G%03d" % i): "1" for i in range(40)}
        doc = fd.snapshot(flags_file, out, env=env)
    finally:
        fd._alert_shortfall = orig
    assert not doc["load_shortfall"]["alarm"], doc["load_shortfall"]
    assert not said, f"بوتِ سالم هشدار داد: {said}"


def t_i_a_broken_alerter_never_kills_boot():
    """پیکربندیِ ناقص بد است؛ پروسه‌ای که به‌خاطرِ هشدار بالا نیامد بدتر."""
    flags_file = Path(ENV["ORG_ROOT"]) / "OCTOPUS-flags-boom.cmd"
    flags_file.write_text(
        "".join("set OCTOPUS_WIRE_H%03d=1\r\n" % i for i in range(40)),
        encoding="utf-8", newline="")
    out = Path(ENV["ORG_ROOT"]) / "flags-loaded-boom.json"
    orig = fd._alert_shortfall

    def boom(sf, src):
        raise RuntimeError("alerting is down")

    fd._alert_shortfall = boom
    try:
        doc = fd.snapshot(flags_file, out, env={})
    except RuntimeError:
        raise AssertionError("هشدارِ خراب boot را کشت")
    finally:
        fd._alert_shortfall = orig
    # boot زنده ماند؛ و کلید همچنان هست تا خواننده «خبر ندارم» را از
    # «سالم بود» تشخیص بدهد.
    assert "load_shortfall" in doc, "کلیدِ گزارش بعد از خطا ناپدید شد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_flag_load_shortfall: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
