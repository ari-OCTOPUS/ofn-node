#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_send_log_stats — خطِ نبضِ ضدِاسپم (لِینِ رصد، ۲۰۲۶-۰۷-۳۱).

چرا این فایل وجود دارد: `tg_send_log.stats()` از ۲۶ جولای درصدِ تکرار را
محاسبه می‌کرد و **هیچ‌کس نمی‌خواندش** — تنها صداکننده‌اش مرورِ هفتگی بود، آن
هم فقط فیلدِ `sends`. سنجه‌ای که خوانده نمی‌شود با سنجهٔ نبود فرق ندارد.
`pulse_line()` همان عدد را به یک خط در پالسِ ساعتیِ لنگر تبدیل می‌کند.

قیدهای زیرِ آزمون:
  · صفر side-effect — خواندنِ نبض هیچ فایلی نمی‌سازد و هیچ ردیفی اضافه نمی‌کند.
  · fail-soft — لاگِ خراب/ناخوانا ⇒ None، نه استثنا (پالس نباید بمیرد).
  · پنجره واقعاً پنجره است — ردیفِ کهنه شمرده نمی‌شود (ساعتِ تزریقی).
  · فلگِ ثبت خاموش ⇒ None، نه عددِ زیرشمارش‌شده که به‌جای واقعیت جا بزند.
  · هرگز متنِ پیام در خروجی نیست — فقط شمار و نامِ جریان.
"""
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness                       # noqa: E402

ENV = harness.setup("tg-send-log-stats")

import opslib                        # noqa: E402
import tg_send_log as tsl            # noqa: E402


def _on(v=True):
    if v:
        os.environ[tsl.FLAG] = "1"
    else:
        os.environ.pop(tsl.FLAG, None)


def _clear():
    p = tsl._path()
    try:
        if p.exists():
            p.unlink()
    except OSError:
        pass


def _write(rows):
    """ردیف‌ها را مستقیم می‌نویسیم — نه از راهِ record()، چون record ساعتِ
    تزریقی ندارد و تستِ پنجره باید ts را خودش تعیین کند."""
    p = tsl._path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _row(ts, chat=-100, topic=7, sha="a" * 16, stream="heart"):
    return {"ts": ts, "chat": chat, "topic": topic, "stream": stream,
            "sha": sha, "chars": 10, "ok": True, "state": "sent"}


NOW = 1_700_000_000.0
H = 3600.0


# ── سکوتِ صادق ──────────────────────────────────────────────────────────────
def t_no_log_at_all_says_nothing():
    _on()
    _clear()
    assert tsl.pulse_line(24.0, now=NOW) is None


def t_below_the_floor_says_nothing():
    """۲ ارسال در ۲۴ ساعت یافته نیست — یک خطِ پالس نمی‌ارزد."""
    _on()
    _write([_row(NOW - 60, sha="a" * 16), _row(NOW - 120, sha="b" * 16)])
    assert tsl.pulse_line(24.0, now=NOW) is None


def t_flag_off_returns_none_instead_of_an_undercount():
    """ثبت خاموش ⇒ هر عددی زیرشمارش است؛ سکوت صادق‌تر از عددِ ناقص است."""
    _write([_row(NOW - 60 * i, sha=f"{i:016d}") for i in range(6)])
    _on(False)
    try:
        assert tsl.pulse_line(24.0, now=NOW) is None
    finally:
        _on()


# ── محتوای خط ──────────────────────────────────────────────────────────────
def t_the_line_reports_sends_unique_and_duplicate_percent():
    _on()
    # ۶ ارسال، ۳ تای آن‌ها دقیقاً یک محتوا به یک مقصد ⇒ ۲ تکراری از ۶ = ۳۳٪
    rows = [_row(NOW - 60, sha="dup"), _row(NOW - 120, sha="dup"),
            _row(NOW - 180, sha="dup"), _row(NOW - 240, sha="x1"),
            _row(NOW - 300, sha="x2"), _row(NOW - 360, sha="x3")]
    _write(rows)
    line = tsl.pulse_line(24.0, now=NOW)
    assert line, "با ۶ ارسال خط باید ساخته شود"
    assert isinstance(line, str) and "\n" not in line, line
    s = tsl.stats(24.0, now=NOW)
    assert s["sends"] == 6 and s["unique"] == 4 and s["duplicates"] == 2, s
    assert tsl._fa(6) in line and tsl._fa(4) in line, line
    assert "تکراری" in line and tsl._fa(33) in line, line


def t_digits_are_persian_and_the_latin_stream_is_bidi_isolated():
    """درسِ کارتِ فارسی: رقمِ لاتین وسطِ جملهٔ RTL جابه‌جا رندر می‌شود."""
    _on()
    _write([_row(NOW - 60 * i, sha=f"{i:016d}", stream="heart")
            for i in range(5)])
    line = tsl.pulse_line(24.0, now=NOW)
    assert line and not any(ch.isdigit() and ch.isascii() for ch in line), line
    assert "⁦heart⁩" in line, line


def t_the_top_stream_is_the_loudest_one_and_ties_are_deterministic():
    _on()
    rows = ([_row(NOW - 60 * i, sha=f"a{i:015d}", stream="needs")
             for i in range(4)]
            + [_row(NOW - 60 * (10 + i), sha=f"b{i:015d}", stream="heart")
               for i in range(2)])
    _write(rows)
    line = tsl.pulse_line(24.0, now=NOW)
    assert "⁦needs⁩" in line and "⁦heart⁩" not in line, line
    # مساوی: نامِ الفبایی برنده — خروجی نباید به ترتیبِ dict وابسته باشد
    assert tsl._top_stream({"zeta": 3, "alpha": 3}) == "alpha"


def t_a_streamless_flood_is_named_not_hidden():
    """اگر بیشترِ ترافیک بی‌جریان است، همان خودش یافته است."""
    _on()
    _write([_row(NOW - 60 * i, sha=f"{i:016d}", stream=None) for i in range(5)])
    line = tsl.pulse_line(24.0, now=NOW)
    assert "بی‌جریان" in line, line
    assert "None" not in line, line
    # متنِ فارسی نباید در ایزولهٔ LTR بپیچد — جهت را برعکس می‌کند
    assert "⁦بی‌جریان⁩" not in line, line


# ── پنجره واقعاً پنجره است ──────────────────────────────────────────────────
def t_rows_older_than_the_window_are_not_counted():
    _on()
    fresh = [_row(NOW - 60 * i, sha=f"f{i:015d}") for i in range(4)]
    stale = [_row(NOW - 30 * H - 60 * i, sha=f"s{i:015d}") for i in range(50)]
    _write(fresh + stale)
    s = tsl.stats(24.0, now=NOW)
    assert s["sends"] == 4, s
    line = tsl.pulse_line(24.0, now=NOW)
    assert tsl._fa(4) in line and tsl._fa(54) not in line, line


def t_the_injected_clock_is_the_only_clock():
    """درسِ «ساعتِ نیمه‌تزریقی» — هیچ شاخه‌ای مخفیانه time.time() نمی‌خواند."""
    _on()
    _write([_row(NOW - 60 * i, sha=f"{i:016d}") for i in range(5)])
    # با ساعتِ واقعی (۲۰۲۶) این ردیف‌ها (۲۰۲۳) خیلی کهنه‌اند ⇒ هیچ
    assert tsl.pulse_line(24.0) is None
    assert tsl.pulse_line(24.0, now=NOW) is not None


def t_a_fractional_window_is_labelled_honestly():
    _on()
    _write([_row(NOW - 60 * i, sha=f"{i:016d}") for i in range(5)])
    line = tsl.pulse_line(0.5, now=NOW)
    assert line and "۰٫۵" in line, line


# ── مقاومت ─────────────────────────────────────────────────────────────────
def t_a_corrupt_log_never_raises_and_never_lies():
    _on()
    p = tsl._path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{این JSON نیست\n\n{\"ts\": \"نه-عدد\"}\n", encoding="utf-8")
    assert tsl.pulse_line(24.0, now=NOW) is None
    assert tsl.stats(24.0, now=NOW)["sends"] == 0


def t_pulse_line_has_zero_side_effects():
    """نبض فقط می‌خواند: نه ردیفی اضافه می‌کند، نه فایلِ prune را لمس می‌کند."""
    _on()
    rows = [_row(NOW - 60 * i, sha=f"{i:016d}") for i in range(5)]
    _write(rows)
    p = tsl._path()
    before = p.read_bytes()
    prune_before = (tsl._PRUNE_STATE.read_bytes()
                    if tsl._PRUNE_STATE.exists() else None)
    listing = sorted(x.name for x in p.parent.iterdir())
    tsl.pulse_line(24.0, now=NOW)
    assert p.read_bytes() == before, "خطِ نبض لاگ را تغییر داد"
    after_prune = (tsl._PRUNE_STATE.read_bytes()
                   if tsl._PRUNE_STATE.exists() else None)
    assert after_prune == prune_before, "خطِ نبض فایلِ prune را لمس کرد"
    assert sorted(x.name for x in p.parent.iterdir()) == listing, "فایلِ تازه ساخت"


def t_the_line_never_leaks_message_content():
    """لاگ فقط hash دارد؛ خطِ نبض هم نباید چیزی جز شمار و جریان بگوید."""
    _on()
    secret_sha = "d" * 16
    _write([_row(NOW - 60 * i, sha=secret_sha) for i in range(5)])
    line = tsl.pulse_line(24.0, now=NOW)
    assert secret_sha not in line, line
    assert "chars" not in line and "sha" not in line, line


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT).lower()
    assert not str(tsl._path()).lower().startswith(live), tsl._path()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    _on(False)
    print(f"\n{'✅' if not failed else '❌'} test_tg_send_log_stats: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
