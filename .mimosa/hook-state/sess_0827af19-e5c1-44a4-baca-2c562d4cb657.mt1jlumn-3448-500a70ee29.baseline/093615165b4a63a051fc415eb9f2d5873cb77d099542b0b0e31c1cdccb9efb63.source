#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_traffic.py — گزارشی که خودش گمراه نکند.

فاز ۱ (۲۰۲۶-۰۸-۰۴). این ابزار برای جلوگیری از خطایی ساخته شد که **ایجنت
مرتکب شد**: روی کلِ لاگ شمرد، «۲۱۶ پیامِ یکسان» دید، و نزدیک بود آن را یک
باگِ زنده گزارش کند. توزیعِ ساعتی نشان داد رگبار مالِ ۰۸-۰۲ بوده و از ۰۸-۰۳
خودش رفع شده — در ۲۴ ساعتِ اخیر نرخِ تکرار ۴٪ بود.

    عددِ تجمعی می‌گوید «چقدر»؛ فقط توزیعِ زمانی می‌گوید «هنوز؟»

ولی یک گاردِ ضدِ-هشدار خودش یک خطرِ قرینه دارد: اگر رگبارِ **واقعاً زنده** را
هم «کهنه» بنامد، دقیقاً همان حادثه‌ای را پنهان می‌کند که باید نشان دهد. پس
این فایل هر دو جهت را می‌سنجد — درسِ ثبت‌شدهٔ «هر باریک‌کردن، هر دو جهت را
دوباره».
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("tg-traffic")
sys.path.insert(0, str(harness.REAL_VAULT / "_ops"))

import tg_traffic as tt  # noqa: E402

NOW = 1_800_000_000.0
H = 3600.0
DM, GROUP = 555, -100555


def _row(ts, *, stream="center", chat=DM, sha="a", state="sent", topic=None):
    return {"ts": ts, "stream": stream, "chat": chat, "topic": topic,
            "sha": sha, "state": state, "ok": True}


def t_a_new_edit_held_are_counted_apart():
    """سه سرنوشتِ متفاوت نباید یک عدد شوند — درسِ «ثبت را گیت نکن، تحویل را»."""
    rows = ([_row(NOW - 100, sha=str(i)) for i in range(5)]
            + [_row(NOW - 100, stream="edit") for _ in range(7)]
            + [_row(NOW - 100, state="held", sha="h") for _ in range(3)]
            + [_row(NOW - 100, state="blocked", sha="b")])
    d = tt.analyse(rows, hours=24, now=NOW)
    assert d["new_sent"] == 5, d
    assert d["edits"] == 7, d
    assert d["held"] == 3 and d["blocked"] == 1, d


def t_b_the_window_actually_excludes_older_rows():
    rows = [_row(NOW - 2 * H, sha="in"), _row(NOW - 30 * H, sha="out")]
    d = tt.analyse(rows, hours=24, now=NOW)
    assert d["new_sent"] == 1, ("پنجره ردیفِ کهنه را داخل آورد", d)


def t_c_dm_and_group_are_split_by_chat_sign():
    """شناسهٔ مثبت = کاربر (DM)، منفی = گروه. این تفکیک باربر است: «۷۶ پیام»
    وقتی معنی دارد که بدانیم چندتایش به خودِ مالک رفته."""
    rows = [_row(NOW - 60, chat=DM, sha="1"), _row(NOW - 60, chat=DM, sha="2"),
            _row(NOW - 60, chat=GROUP, sha="3")]
    d = tt.analyse(rows, hours=24, now=NOW)
    assert d["to_dm"] == 2 and d["to_group"] == 1, d


def t_d_duplicates_need_the_same_stream_chat_and_content():
    rows = [_row(NOW - 60, sha="same"), _row(NOW - 61, sha="same"),
            _row(NOW - 62, sha="same"),
            _row(NOW - 63, sha="same", chat=GROUP),   # مقصدِ دیگر ⇒ تکراری نیست
            _row(NOW - 64, sha="same", stream="other")]  # جریانِ دیگر ⇒ نه
    d = tt.analyse(rows, hours=24, now=NOW)
    assert d["duplicates"] == 2, ("۳ ردیفِ یکسان یعنی ۲ تکرار", d)


# ── قلبِ فایل: گارد باید در **هر دو** جهت درست باشد ─────────────────────────
def t_e_a_historical_burst_is_named_as_historical():
    """رگباری که تمام شده نباید «باگِ زنده» به‌نظر برسد."""
    rows = ([_row(NOW - 40 * H + i, sha="storm") for i in range(60)]
            + [_row(NOW - 60, sha="normal")])
    d = tt.analyse(rows, hours=24, now=NOW)
    assert d["stale_bursts"], ("رگبارِ کهنه شناسایی نشد", d)
    s = d["stale_bursts"][0]
    assert s["total"] == 60 and s["in_window"] == 0, s
    txt = tt.report(d)
    assert "کهنه" in txt and "گذشته است" in txt, txt


def t_f_a_live_burst_is_never_excused_as_historical():
    """⚠️ خطرِ قرینه، و مهم‌تر از خودِ گارد: اگر رگبارِ **زنده** «کهنه» نامیده
    شود، این ابزار همان حادثه‌ای را پنهان می‌کند که برای نشان‌دادنش ساخته شد.
    گاردی که در جهتِ اشتباه بلندتر از لازم باشد، بدتر از نبودنش است."""
    rows = [_row(NOW - 3 * H + i, sha="storm") for i in range(60)]
    d = tt.analyse(rows, hours=24, now=NOW)
    assert not d["stale_bursts"], (
        "رگبارِ زنده «کهنه» اعلام شد ⇒ حادثهٔ واقعی پنهان می‌شود", d["stale_bursts"])
    assert d["duplicates"] == 59, d
    assert "کهنه" not in tt.report(d)


def t_g_a_burst_that_is_dying_but_not_dead_is_not_excused():
    """حالتِ مرزی: رگبار کم شده ولی هنوز نفس می‌کشد. تا وقتی سهمِ پنجره از
    آستانه بالاتر است، «کهنه» نیست."""
    rows = ([_row(NOW - 40 * H + i, sha="storm") for i in range(60)]
            + [_row(NOW - 2 * H + i, sha="storm") for i in range(30)])
    d = tt.analyse(rows, hours=24, now=NOW)
    assert not d["stale_bursts"], ("رگبارِ در حالِ ادامه بخشوده شد", d)


def t_h_tiny_clusters_are_not_worth_a_warning():
    """گاردی که برای ۳ پیام هشدار بدهد، خاموش می‌شود."""
    rows = ([_row(NOW - 40 * H + i, sha="tiny") for i in range(3)]
            + [_row(NOW - 60, sha="x")])
    d = tt.analyse(rows, hours=24, now=NOW)
    assert not d["stale_bursts"], d


def t_i_an_empty_log_reports_nothing_rather_than_exploding():
    d = tt.analyse([], hours=24, now=NOW)
    assert d["new_sent"] == 0 and d["duplicate_pct"] == 0.0, d
    assert isinstance(tt.report(d), str)


def t_j_a_corrupt_row_drops_only_itself():
    """یک بایتِ خراب نباید کلِ لایهٔ اندازه‌گیری را خاموش کند — همان درسی که
    یک بار `stats()` را با یک `ts` ِ غیرعددی کشت."""
    rows = [_row(NOW - 60, sha="ok"), {"ts": "نه‌عدد", "stream": "center"},
            {"stream": "center"}]
    d = tt.analyse(rows, hours=24, now=NOW)
    assert d["new_sent"] == 1, d


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
    print(f"\ntest_tg_traffic: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
