"""test_provenance — عددِ تمبرخورده باید بتواند دروغ نگوید.

گامِ ۱ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C10). سه سنجهٔ پذیرشِ سند به‌علاوهٔ
دو ردِ ساختاریِ اجباری اینجا قفل می‌شوند:

  الف) ts را ۱۰ دقیقه عقب ببر  ⇒ HELD، نه یک عددِ به‌ظاهر سالم
  ب)  ۲۸۸ نمونهٔ یکسان        ⇒ dof=1، mode=CONSTANT
  ج)  منبعِ غایب               ⇒ UNKNOWN و **بدونِ کلیدِ value**، پس استخراجِ
                                 مقدار استثنا بدهد نه صفر

  رد ۱) mtime هرگز observed_ts نیست  (۱۴ از ۲۰ فایلِ pulse گیت‌tracked اند و
        mtime شان آرتیفکتِ merge است — تا ۶.۶ ساعت جلوتر از ts درونی)
  رد ۲) observed_ts باید از **داخلِ خودِ مقدار** بیاید، نه از ts سطحِ بالای سند
        (merge_prev در organism.py::_write_state آن یکی را حتی وقتی این کلید
        به‌روز نشده جلو می‌برد)

ساعت در همهٔ تست‌ها تزریق می‌شود؛ هیچ assert ی به ساعتِ دیوار وابسته نیست.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness   # noqa: E402
ENV = harness.setup("provenance")

_OPS = harness.SELF_OPS
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import provenance as P   # noqa: E402

NOW = 1_785_700_000.0   # ساعتِ ثابتِ تزریقی برای همهٔ سنجه‌ها


def t_module_is_pure_no_io():
    """C10 قول داده هیچ مسیری نمی‌خواند و هیچ‌چیز نمی‌نویسد."""
    src = (_OPS / "provenance.py").read_text("utf-8")
    for forbidden in ("open(", "Path(", "os.environ", "json.load", "json.dump"):
        assert forbidden not in src, f"provenance.py باید خالص بماند، ولی {forbidden} دارد"


def t_a_held_when_vessel_did_not_refresh():
    """(الف) ts ِ ۱۰ دقیقه عقب روی ظرفی با ریتمِ ۲۸۵s ⇒ HELD."""
    cadence = 285.0
    s = P.stamp(60.0, "heart-shadow-latest.json", NOW - 600, cadence, now=NOW)
    assert s["mode"] == P.Mode.HELD, f"باید HELD باشد، شد {s['mode']}"
    assert not P.is_trustworthy(s), "HELD نباید قابلِ تصمیم شمرده شود"
    # مقدار هنوز هست — HELD یعنی «کهنه»، نه «غایب»
    assert P.value_of(s) == 60.0


def t_a_live_when_fresh():
    """جفتِ لازمِ (الف): همان ظرف وقتی تازه است LIVE می‌شود، وگرنه گارد کور است."""
    s = P.stamp(60.0, "heart-shadow-latest.json", NOW - 30, 285.0,
                history=[59.0, 60.0, 61.0], now=NOW)
    assert s["mode"] == P.Mode.LIVE, f"باید LIVE باشد، شد {s['mode']}"
    assert P.is_trustworthy(s)


def t_b_constant_on_288_identical_samples():
    """(ب) ۲۸۸ نمونهٔ یکسان ⇒ dof=1 و CONSTANT — دقیقاً تلهٔ control_law=60.0."""
    cadence = 285.0
    hist = [60.0] * 288
    s = P.stamp(60.0, "heart-params-shadow.jsonl", NOW - 10, cadence,
                history=hist, now=NOW)
    assert s["dof"] == 1, f"dof باید ۱ باشد، شد {s['dof']}"
    assert s["mode"] == P.Mode.CONSTANT, f"باید CONSTANT باشد، شد {s['mode']}"
    assert not P.is_trustworthy(s), "یک ثابت نباید رأیِ زنده شمرده شود"


def t_b_moving_series_is_not_constant():
    """جفتِ لازمِ (ب): سریِ متحرک با همان طولِ پنجره نباید CONSTANT شود."""
    hist = [60.0 + (i % 7) * 0.1 for i in range(288)]
    s = P.stamp(hist[-1], "rhythm", NOW - 10, 285.0, history=hist, now=NOW)
    assert s["dof"] > 1, "سریِ متحرک باید dof>1 بدهد"
    assert s["mode"] == P.Mode.LIVE


def t_b_constant_needs_a_long_enough_window():
    """dof=1 روی پنجرهٔ کوتاه CONSTANT نیست — دو نمونه هنوز شاهدِ ثابت‌بودن نیست."""
    s = P.stamp(60.0, "x", NOW - 10, 285.0, history=[60.0, 60.0], now=NOW)
    assert s["dof"] == 1
    assert s["mode"] == P.Mode.LIVE, "پنجرهٔ کوتاه نباید CONSTANT اعلام شود"


def t_c_unknown_has_no_value_key():
    """(ج) منبعِ غایب ⇒ UNKNOWN، و **هیچ کلیدِ value** — تا صفرِ بی‌صدا نسازد."""
    s = P.stamp(None, "", None, 285.0, now=NOW)
    assert s["mode"] == P.Mode.UNKNOWN
    assert "value" not in s, "UNKNOWN نباید کلیدِ value داشته باشد"
    try:
        P.value_of(s)
    except KeyError:
        pass
    else:
        raise AssertionError("value_of روی UNKNOWN باید استثنا بدهد، نه مقدار")


def t_c_unknown_never_becomes_zero():
    """پیامدِ (ج): هیچ مسیری نباید UNKNOWN را به عددِ قابلِ‌محاسبه تبدیل کند."""
    s = P.stamp(None, "missing-vessel.json", None, 60.0, now=NOW)
    assert s["mode"] == P.Mode.UNKNOWN
    try:
        float(P.value_of(s))
    except KeyError:
        pass
    else:
        raise AssertionError("UNKNOWN نباید به float تبدیل شود")


def t_reject_1_mtime_is_never_observed_ts():
    """ردِ ساختاریِ ۱: mtime تازگی را اثبات نمی‌کند."""
    s = P.stamp(60.0, "heart-setpoint-latest.json", P.Mtime(NOW - 5), 285.0, now=NOW)
    assert s["mode"] == P.Mode.UNKNOWN, "mtime باید رد شود حتی وقتی تازه به‌نظر می‌رسد"
    assert s["reason"] == "mtime-only", f"دلیل باید mtime-only باشد، شد {s.get('reason')}"
    assert "value" not in s


def t_reject_1_plain_ts_still_accepted():
    """جفتِ لازمِ رد ۱: همان عدد بدونِ پوششِ Mtime پذیرفته می‌شود."""
    s = P.stamp(60.0, "heart-setpoint-latest.json", NOW - 5, 285.0, now=NOW)
    assert s["mode"] != P.Mode.UNKNOWN, "ts ِ عادی نباید رد شود"


def t_reject_2_observed_ts_comes_from_inside_the_value():
    """ردِ ساختاریِ ۲: ts را از داخلِ خودِ مقدار بگیر، نه از سندِ دربرگیرنده."""
    envelope = {"ts": "2026-08-03T05:43:51", "arbiter": {"effective_period_s": 56.98}}
    inner = P.observed_in(envelope["arbiter"])
    assert inner is None, "مقدارِ بدونِ ts خودش نباید از پوشش ts قرض بگیرد"
    withts = P.observed_in({"ts": "2026-08-03T05:40:07", "period_s": 60.0})
    assert withts is not None and withts > 0


def t_iso_and_epoch_both_parse():
    """هر دو شکل در این ارگانیسم زنده‌اند و باید یکسان رفتار کنند."""
    iso = P.parse_ts("2026-08-03T05:40:07")
    epoch = P.parse_ts(1_785_697_207.0)
    assert iso is not None and epoch is not None
    assert P.parse_ts("not-a-time") is None
    assert P.parse_ts(None) is None


def t_round_trip_through_the_real_writer():
    """🔴 گاردِ باگی که یک‌بار زد و یک‌بار برگشت: منطقهٔ زمانیِ نویسنده در برابر خواننده.

    نسخهٔ اولِ `parse_ts` ‏ISO ِ بدونِ منطقه را UTC فرض می‌کرد، ولی نویسندهٔ
    canonicalِ هر ظرف `opslib.now_iso()` است که **محلیِ بدونِ منطقه** می‌دهد.
    نتیجه روی دادهٔ زنده: `age_s = -35,879` — و چون `age > 2×cadence` با عددِ
    منفی هرگز درست نمی‌شود، `HELD` هیچ‌وقت شلیک نمی‌کرد.

    هیچ فیکسچری این را نمی‌گرفت. فقط round-trip از **مسیرِ نویسندهٔ تولیدی**
    می‌گیردش — درسِ «خواننده و نویسنده را با هم بسنج».
    """
    import time as _t
    sys.path.insert(0, str(_OPS / "budget"))
    import opslib   # noqa: PLC0415

    written = opslib.now_iso()          # همان چیزی که هر ظرفِ زنده می‌نویسد
    parsed = P.parse_ts(written)
    assert parsed is not None, f"خروجیِ نویسندهٔ واقعی پارس نشد: {written!r}"
    age = _t.time() - parsed
    assert age >= -2.0, (
        f"age منفی شد ({age:.0f}s) — خواننده منطقهٔ نویسنده را اشتباه می‌فهمد. "
        f"نویسنده داد {written!r}")
    assert age < 120.0, f"age بی‌دلیل بزرگ است: {age:.0f}s"


def t_a_stale_vessel_written_by_the_real_writer_is_held():
    """پیامدِ همان باگ: با ساعتِ درست، ظرفِ کهنه باید واقعاً HELD شود."""
    import datetime as _dt
    import time as _t
    old = (_dt.datetime.now() - _dt.timedelta(minutes=30)).isoformat(timespec="seconds")
    s = P.stamp(60.0, "heart-shadow-latest.json", old, 285.0, now=_t.time())
    assert s["age_s"] > 0, f"age هنوز منفی است: {s['age_s']}"
    assert s["mode"] == P.Mode.HELD, f"ظرفِ ۳۰دقیقه‌ای HELD نشد: {s['mode']}"


def t_timezone_aware_strings_keep_their_offset():
    """رشتهٔ دارای منطقه نباید دوباره تفسیر شود."""
    utc = P.parse_ts("2026-08-03T00:00:00Z")
    plus10 = P.parse_ts("2026-08-03T10:00:00+10:00")
    assert utc is not None and plus10 is not None
    assert abs(utc - plus10) < 1.0, f"هر دو باید یک لحظه باشند: {utc} vs {plus10}"


def t_clock_is_fully_injected():
    """درسِ «ساعتِ نیمه‌تزریقی»: با now ِ تزریقی هیچ شاخه‌ای ساعتِ دیوار نخواند."""
    src = (_OPS / "provenance.py").read_text("utf-8")
    body = src.split("def stamp(", 1)[1]
    assert "time.time()" in body, "stamp باید پیش‌فرضِ ساعت داشته باشد"
    assert body.count("time.time()") == 1, "فقط یک نقطهٔ خواندنِ ساعت مجاز است"
    a = P.stamp(1.0, "s", NOW - 10, 5.0, now=NOW)
    b = P.stamp(1.0, "s", NOW - 10, 5.0, now=NOW)
    assert a["age_s"] == b["age_s"] == 10.0, "با now ِ یکسان نتیجه باید قطعی باشد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_provenance: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
