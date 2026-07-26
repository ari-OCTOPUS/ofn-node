"""test_hebbian_signals.py — تستِ متخاصم علیهِ واژگانِ سیگنالِ Hebbian.

قصد: **گول‌زدنِ خودِ تغییر**، نه تأییدش. اگر واژگانِ تازه فقط شلوغ‌تر باشد و
نه پرمعناتر، باید همین‌جا لو برود نه شش ماه بعد در یک گزارش.

پس‌زمینه (VERIFIED ۲۰۲۶-۰۷-۲۶): نسخهٔ قبلی دقیقاً دو سیگنالِ ممکن داشت، پس
`hebbian.json` بعد از ۲۲۳۵ هم‌رخدادی یک ردیف داشت. ولی «سیگنالِ بیشتر» به‌خودیِ‌خود
پیشرفت نیست — سیگنالی که **همیشه** روشن است صفر اطلاعات حمل می‌کند، و اگر یک
گروه پارتیشن باشد (همیشه دقیقاً یکی‌شان آتش کند) با هر چیزِ دیگری هم‌رخداد
می‌شود و strength را بدونِ معنا بالا می‌برد. آن دقیقاً همان بیماریِ قبلی است
با واژه‌های بیشتر.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("hebbian-signals")

import wiring as w   # noqa: E402

FLAG = "OCTOPUS_HEBBIAN_RICH"


def _rich(on):
    if on:
        os.environ[FLAG] = "1"
    else:
        os.environ.pop(FLAG, None)


CALM = {"rhythm": {"mode_color": "GREEN"}, "spectral": {"sigma": 0.3},
        "budget": {"pct": 0.2}, "sensory": {"afferent_ratio": 0.5, "error_rate": 0.01}}
STRESSED = {"rhythm": {"mode_color": "RED"}, "spectral": {"sigma": 1.5},
            "budget": {"pct": 0.95, "depleted": True},
            "sensory": {"afferent_ratio": 0.02, "error_rate": 0.9}}


# ─── حفاظتِ رفتارِ قبلی ──────────────────────────────────────────────────────
def t_flag_off_is_byte_identical_to_the_old_two_word_vocabulary():
    _rich(False)
    assert w._hebbian_signals(CALM) == ["green_mode", "stable"]
    assert w._hebbian_signals(STRESSED) == []
    assert w._hebbian_signals({}) == ["stable"]   # sigma غایب → 0 → <0.8


# ─── حملهٔ ۱: ورودیِ خراب ────────────────────────────────────────────────────
def t_malformed_input_never_raises():
    _rich(True)
    try:
        for bad in ({}, {"rhythm": None}, {"spectral": {"sigma": "خیلی"}},
                    {"budget": {"pct": None}}, {"sensory": {"error_rate": []}},
                    {"rhythm": {"mode_color": 123}}, {"spectral": "نه‌دیکشنری"}):
            out = w._hebbian_signals(bad)
            assert isinstance(out, list), f"لیست برنگرداند برای {bad!r}"
            assert all(isinstance(s, str) for s in out)
    finally:
        _rich(False)


# ─── حملهٔ ۲ (مهم‌ترین): سیگنالِ همیشه‌روشن صفر اطلاعات دارد ─────────────────
def t_no_signal_fires_in_every_single_state():
    """اگر سیگنالی در هر دو حالتِ آرام و پرتنش آتش کند، با همه‌چیز هم‌رخداد
    می‌شود و strength را بدونِ معنا بالا می‌برد — همان بیماریِ green_mode+stable
    در مقیاسِ بزرگ‌تر."""
    _rich(True)
    try:
        states = [CALM, STRESSED,
                  {"rhythm": {"mode_color": "AMBER"}, "spectral": {"sigma": 1.0},
                   "budget": {"pct": 0.6}, "sensory": {"afferent_ratio": 0.3,
                                                       "error_rate": 0.1}},
                  {}]
        sets = [set(w._hebbian_signals(s)) for s in states]
        always = set.intersection(*sets) if sets else set()
        assert not always, (
            f"سیگنال(های) همیشه‌روشن: {sorted(always)} — صفر اطلاعات حمل می‌کنند "
            "و با هر چیزِ دیگری هم‌رخداد می‌شوند")
    finally:
        _rich(False)


def t_no_partition_group_guarantees_a_signal_every_tick():
    """گروهِ پارتیشن = دقیقاً یکی‌شان همیشه آتش می‌کند (مثلِ low/mid/high).
    عضوِ چنین گروهی با هر سیگنالِ دیگری هم‌رخداد می‌شود و جفت‌های جعلی می‌سازد."""
    _rich(True)
    try:
        for group in (("sigma_low", "sigma_mid", "sigma_high"),
                      ("budget_free", "budget_mid", "budget_tight"),
                      ("errors_low", "errors_high"),
                      ("afferent_ok", "afferent_starved")):
            fired_every_time = True
            for st in (CALM, STRESSED, {}, {"spectral": {"sigma": 1.0}}):
                if not (set(w._hebbian_signals(st)) & set(group)):
                    fired_every_time = False
                    break
            assert not fired_every_time, (
                f"گروهِ {group} یک پارتیشن است — همیشه یکی آتش می‌کند، پس با هر "
                "سیگنالِ دیگری هم‌رخداد می‌شود و strength بی‌معنا بالا می‌رود")
    finally:
        _rich(False)


# ─── حملهٔ ۳: انفجارِ ترکیبی ────────────────────────────────────────────────
def t_vocabulary_does_not_explode_into_noise():
    """N سیگنال یعنی تا N(N-1)/2 جفت. اگر واژگان بزرگ شود، جدول پر از
    جفت‌های یک‌باره می‌شود و سیگنالِ واقعی در نویز گم می‌شود."""
    _rich(True)
    try:
        for st in (CALM, STRESSED):
            n = len(w._hebbian_signals(st))
            assert n <= 7, f"{n} سیگنال در یک تیک — تا {n*(n-1)//2} جفت، نویز"
    finally:
        _rich(False)


def t_signals_are_unique_within_a_tick():
    _rich(True)
    try:
        for st in (CALM, STRESSED, {}):
            s = w._hebbian_signals(st)
            assert len(s) == len(set(s)), f"سیگنالِ تکراری: {s}"
    finally:
        _rich(False)


# ─── حملهٔ ۴: آیا اصلاً تمایز می‌گذارد؟ ─────────────────────────────────────
def t_calm_and_stressed_are_actually_distinguishable():
    """اگر دو حالتِ کاملاً متفاوت سیگنالِ یکسان بدهند، واژگان کور است."""
    _rich(True)
    try:
        a, b = set(w._hebbian_signals(CALM)), set(w._hebbian_signals(STRESSED))
        assert a != b, "آرام و پرتنش یکسان دیده می‌شوند"
        assert not (a & b), f"هم‌پوشانی بینِ آرام و پرتنش: {sorted(a & b)}"
    finally:
        _rich(False)


def t_a_state_that_never_changes_produces_no_new_pairs():
    """اگر ارگانیسم بی‌حرکت باشد، واژگان نباید جفتِ تازه بسازد."""
    _rich(True)
    try:
        runs = [tuple(w._hebbian_signals(CALM)) for _ in range(5)]
        assert len(set(runs)) == 1, "همان ورودی، خروجیِ متفاوت — قطعی نیست"
    finally:
        _rich(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_hebbian_signals: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
