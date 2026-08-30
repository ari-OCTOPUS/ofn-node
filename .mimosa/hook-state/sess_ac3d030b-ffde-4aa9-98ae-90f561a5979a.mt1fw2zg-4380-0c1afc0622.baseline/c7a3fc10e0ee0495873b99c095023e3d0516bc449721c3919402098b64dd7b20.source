#!/usr/bin/env python3
"""test_hebbian_real_signals.py — سیم‌کشیِ محافظه‌کارِ ۲۰۲۶-۰۸-۰۶: sigma_high و
budget_depleted در `_hebbian_signals` را از منابعِ **واقعیِ** موجود تغذیه می‌کند
(نه از payloadِ organism.py/brain_worker.py که هر دو ساختاراً مرده‌اند — مستندِ
`wiring.SIGNAL_DORMANT`).

پس‌زمینه (تأییدشده روی کد):
  · organism.py:632-634 همیشه `sigma_is_replication_ratio: True` هاردکد می‌کند؛
    brain_worker.py:187 اصلاً آن کلید را نمی‌دهد. هر دو یعنی `sigma_high`
    ساختاراً هرگز از مسیرِ payload آتش نمی‌کند.
  · organism.py:618 هرگز `budget.depleted` نمی‌دهد (فقط `pct`). تنها تولیدکنندهٔ
    واقعیِ این مفهوم `cardiac.py::status_snapshot()` است.

این تست دو مسیرِ **جانبی** و پشتِ فلگِ نو را می‌سنجد — عمداً payloadِ organism.py/
brain_worker.py را دست‌نخورده می‌گذارند (هیچ تغییری در آن دو فایل):
  OCTOPUS_WIRE_HEBBIAN_SPECTRAL → doctor/spectral.py::estimate_sigma روی traceِ واقعی
  OCTOPUS_WIRE_HEBBIAN_CARDIAC  → cardiac.py::status_snapshot (خودش پشتِ OCTOPUS_WIRE_BIO)

اثباتِ لازم: (الف) فلگ‌های نو خاموش (پیش‌فرض) → رفتار بایت‌به‌بایت قبلی، حتی با
دادهٔ واقعیِ بالادست. (ب) فلگ‌ها روشن → سیگنال واقعاً آتش می‌کند و تا
`hebbian.observe()` می‌رسد و جدولِ تداعی را از baselineِ فقط-errors_high متفاوت
می‌کند.
$0 آفلاین، stdlib-only.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("hebbian-real-signals")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "neural"), str(_OPS / "doctor")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib   # noqa: E402
import wiring   # noqa: E402


SPECTRAL_FLAG = "OCTOPUS_WIRE_HEBBIAN_SPECTRAL"
CARDIAC_FLAG = "OCTOPUS_WIRE_HEBBIAN_CARDIAC"


def _clear_flags():
    for f in (SPECTRAL_FLAG, CARDIAC_FLAG, "OCTOPUS_WIRE_BIO", "OCTOPUS_HEBBIAN_RICH",
              "OCTOPUS_HEBBIAN_EVENTCLOCK", "OCTOPUS_WIRE_NEURAL"):
        os.environ.pop(f, None)


# ── payloadِ literalِ organism.py — دست‌نخورده در همهٔ تست‌ها (byte-identical) ──
def _payload(error_rate=0.99):
    return {
        "rhythm": {"mode_color": "GREEN"},
        "budget": {"pct": 0.0},
        "spectral": {"sigma": 0.0, "sigma_is_replication_ratio": True,
                     "sigma_source": "replication-latest.json"},
        "sensory": {"afferent_ratio": 1.0, "error_rate": error_rate},
    }


def _seed_fragile_trace():
    """ORGANISM-STATE.json + telemetry-latest.json واقعی — گرافِ ستارهٔ ۳-گرهی
    (۱ خطا روی ORGAN_A، ۳ ارگان از تله‌متری) → σ محاسبه‌شده ≈ 3.0 (≥ ۱.۲)."""
    org = {"conflicts": [{"organ": "ORGAN_A", "msg": "boom"}]}
    (opslib.STATE_DIR / "ORGANISM-STATE.json").write_text(
        json.dumps(org, ensure_ascii=False), "utf-8")
    tel = {"per_organ_alltime_musd": {"ORGAN_A": 10, "ORGAN_B": 5, "ORGAN_C": 3}}
    (opslib.STATE_DIR / "telemetry-latest.json").write_text(
        json.dumps(tel, ensure_ascii=False), "utf-8")


def _clear_trace():
    for name in ("ORGANISM-STATE.json", "telemetry-latest.json"):
        p = opslib.STATE_DIR / name
        if p.exists():
            p.unlink()


def _deplete_cardiac_budget():
    """budget.depleted=True واقعی — از مسیرِ عمومیِ BeatBudget.spend (نه نوشتنِ
    دستیِ فایل). CARDIAC_DAILY_BEAT_CAP باید **قبل از اولین importِ cardiac**
    ست شود (ثابتِ ماژول‌سطح)."""
    os.environ["CARDIAC_DAILY_BEAT_CAP"] = "1"
    os.environ["OCTOPUS_WIRE_BIO"] = "1"
    import cardiac
    cardiac._budget = cardiac.BeatBudget(daily_cap=1)
    cardiac._budget.spend("active")   # spent=1 >= cap=1 → depleted


def _stack():
    os.environ["OCTOPUS_WIRE_NEURAL"] = "1"
    s = wiring.make_neural_stack()
    os.environ.pop("OCTOPUS_WIRE_NEURAL")
    return s


# ════════════════════════════════════════════════════════════════════════════════
# (۱) _real_spectral_sigma — واحد
# ════════════════════════════════════════════════════════════════════════════════

def t_spectral_flag_off_is_none_even_with_fragile_trace():
    _clear_flags()
    _seed_fragile_trace()
    try:
        assert wiring._real_spectral_sigma() is None, \
            "فلگ خاموش باید بی‌قیدوشرط None بدهد (no regression)"
    finally:
        _clear_trace()


def t_spectral_flag_on_no_trace_is_none():
    """فلگ روشن ولی گرافِ خطا خالی/دژنره است → None (نه σ=1.00ِ ساختگی)."""
    _clear_flags()
    _clear_trace()
    os.environ[SPECTRAL_FLAG] = "1"
    try:
        got = wiring._real_spectral_sigma()
    finally:
        os.environ.pop(SPECTRAL_FLAG, None)
    assert got is None, f"گرافِ خالی باید None بدهد، شد {got}"


def t_spectral_flag_on_fragile_trace_gives_high_sigma():
    """فلگ روشن + traceِ واقعیِ شکننده → σ محاسبه‌شده ≥ ۱.۲ (آستانهٔ sigma_high)."""
    _clear_flags()
    _seed_fragile_trace()
    os.environ[SPECTRAL_FLAG] = "1"
    try:
        got = wiring._real_spectral_sigma()
    finally:
        os.environ.pop(SPECTRAL_FLAG, None)
        _clear_trace()
    assert got is not None, "با traceِ واقعیِ شکننده نباید None باشد"
    assert got >= 1.2, f"σ محاسبه‌شده زیرِ آستانه است: {got}"


# ════════════════════════════════════════════════════════════════════════════════
# (۲) _real_budget_depleted — واحد
# ════════════════════════════════════════════════════════════════════════════════

def t_cardiac_flag_off_is_none_even_when_depleted():
    _clear_flags()
    _deplete_cardiac_budget()
    try:
        assert wiring._real_budget_depleted() is None, \
            "فلگ خاموش باید بی‌قیدوشرط None بدهد (no regression)"
    finally:
        _clear_flags()


def t_cardiac_flag_on_but_bio_off_is_none():
    """فلگِ نو روشن ولی OCTOPUS_WIRE_BIO (پیش‌شرطِ خودِ cardiac) خاموش → None."""
    _clear_flags()
    os.environ[CARDIAC_FLAG] = "1"
    try:
        got = wiring._real_budget_depleted()
    finally:
        os.environ.pop(CARDIAC_FLAG, None)
    assert got is None, f"بدونِ OCTOPUS_WIRE_BIO باید None باشد، شد {got}"


def t_cardiac_flag_on_and_depleted_is_true():
    _clear_flags()
    _deplete_cardiac_budget()
    os.environ[CARDIAC_FLAG] = "1"
    try:
        got = wiring._real_budget_depleted()
    finally:
        os.environ.pop(CARDIAC_FLAG, None)
        _clear_flags()
    assert got is True, f"با بودجهٔ واقعاً depleted باید True باشد، شد {got}"


def t_cardiac_flag_on_and_not_depleted_is_false():
    _clear_flags()
    os.environ["OCTOPUS_WIRE_BIO"] = "1"
    os.environ[CARDIAC_FLAG] = "1"
    import cardiac
    cardiac._budget = cardiac.BeatBudget(daily_cap=1000)   # سقفِ بلندبالا → depleted نیست
    try:
        got = wiring._real_budget_depleted()
    finally:
        os.environ.pop(CARDIAC_FLAG, None)
        os.environ.pop("OCTOPUS_WIRE_BIO", None)
    assert got is False, f"با بودجهٔ سالم باید False باشد، شد {got}"


# ════════════════════════════════════════════════════════════════════════════════
# (۳) _hebbian_signals — سرِ خط
# ════════════════════════════════════════════════════════════════════════════════

def t_hebbian_signals_flags_off_matches_baseline():
    """فلگ‌های نو خاموش (پیش‌فرض) → فقط errors_high، حتی با دادهٔ واقعیِ بالادست."""
    _clear_flags()
    os.environ["OCTOPUS_HEBBIAN_RICH"] = "1"
    _seed_fragile_trace()
    _deplete_cardiac_budget()
    try:
        sig = wiring._hebbian_signals(_payload())
    finally:
        os.environ.pop("OCTOPUS_HEBBIAN_RICH", None)
        _clear_trace()
        _clear_flags()
    assert sig == ["errors_high"], f"با فلگ‌های نو خاموش انتظارِ فقط errors_high بود: {sig}"


def t_hebbian_signals_flags_on_adds_real_signals():
    """فلگ‌های نو روشن + دادهٔ واقعی → sigma_high و budget_depleted هم آتش می‌کنند."""
    _clear_flags()
    os.environ["OCTOPUS_HEBBIAN_RICH"] = "1"
    _seed_fragile_trace()
    _deplete_cardiac_budget()
    os.environ[SPECTRAL_FLAG] = "1"
    os.environ[CARDIAC_FLAG] = "1"
    try:
        sig = wiring._hebbian_signals(_payload())
    finally:
        os.environ.pop("OCTOPUS_HEBBIAN_RICH", None)
        os.environ.pop(SPECTRAL_FLAG, None)
        os.environ.pop(CARDIAC_FLAG, None)
        _clear_trace()
        _clear_flags()
    assert set(sig) == {"errors_high", "sigma_high", "budget_depleted"}, \
        f"با فلگ‌های نو روشن انتظارِ هر سه سیگنال بود: {sig}"


# ════════════════════════════════════════════════════════════════════════════════
# (۴) neural_beat — اثباتِ اثر: جریانِ واقعی تا hebbian.observe()
# ════════════════════════════════════════════════════════════════════════════════

def t_real_signals_reach_hebbian_observe_and_diverge_from_baseline():
    """اثباتِ **اثر**: با فلگ‌های نو روشن، جفت‌های تداعیِ حاویِ sigma_high/
    budget_depleted واقعاً در جدولِ hebbian ثبت می‌شوند — چیزی که baselineِ
    فقط-errors_high (تک‌سیگنال، بدونِ جفت) هرگز تولید نمی‌کند."""
    _clear_flags()

    # baseline: فلگ‌های نو خاموش — حتی با دادهٔ واقعیِ بالادست
    stack_off = _stack()
    if stack_off is None:
        return
    _seed_fragile_trace()
    _deplete_cardiac_budget()
    os.environ["OCTOPUS_HEBBIAN_RICH"] = "1"
    try:
        wiring.neural_beat(stack_off, 100, _payload())
    finally:
        os.environ.pop("OCTOPUS_HEBBIAN_RICH", None)
        _clear_trace()
        _clear_flags()
    pairs_off = {tuple(sorted(a.signals)) for a in stack_off["hebbian"].associations}
    assert pairs_off == set(), \
        f"baselineِ تک‌سیگنال نباید جفتی ثبت کند (observe نیاز به ≥۲ سیگنالِ هم‌زمان دارد): {pairs_off}"

    # armed: فلگ‌های نو روشن + همان دادهٔ واقعی
    stack_on = _stack()
    _seed_fragile_trace()
    _deplete_cardiac_budget()
    os.environ["OCTOPUS_HEBBIAN_RICH"] = "1"
    os.environ[SPECTRAL_FLAG] = "1"
    os.environ[CARDIAC_FLAG] = "1"
    try:
        wiring.neural_beat(stack_on, 100, _payload())
    finally:
        os.environ.pop("OCTOPUS_HEBBIAN_RICH", None)
        os.environ.pop(SPECTRAL_FLAG, None)
        os.environ.pop(CARDIAC_FLAG, None)
        _clear_trace()
        _clear_flags()
    pairs_on = {tuple(sorted(a.signals)) for a in stack_on["hebbian"].associations}
    assert pairs_on != set(), "با فلگ‌های نو روشن باید جفت‌هایی ثبت شوند"
    assert any("sigma_high" in p for p in pairs_on), \
        f"sigma_high باید در یکی از جفت‌ها باشد: {pairs_on}"
    assert any("budget_depleted" in p for p in pairs_on), \
        f"budget_depleted باید در یکی از جفت‌ها باشد: {pairs_on}"
    assert pairs_on != pairs_off, "جدولِ تداعی با دادهٔ واقعی باید از baseline متفاوت باشد"


if __name__ == "__main__":
    failed = harness.run([
        ("spectral: فلگ خاموش → None حتی با traceِ واقعی", t_spectral_flag_off_is_none_even_with_fragile_trace),
        ("spectral: فلگ روشن + گرافِ خالی → None", t_spectral_flag_on_no_trace_is_none),
        ("spectral: فلگ روشن + traceِ واقعی → σ≥۱.۲", t_spectral_flag_on_fragile_trace_gives_high_sigma),
        ("cardiac: فلگ خاموش → None حتی وقتی depleted", t_cardiac_flag_off_is_none_even_when_depleted),
        ("cardiac: فلگ روشن ولی BIO خاموش → None", t_cardiac_flag_on_but_bio_off_is_none),
        ("cardiac: فلگ روشن + واقعاً depleted → True", t_cardiac_flag_on_and_depleted_is_true),
        ("cardiac: فلگ روشن + سالم → False", t_cardiac_flag_on_and_not_depleted_is_false),
        ("hebbian_signals: فلگ‌های نو خاموش = baseline", t_hebbian_signals_flags_off_matches_baseline),
        ("hebbian_signals: فلگ‌های نو روشن → سه سیگنال", t_hebbian_signals_flags_on_adds_real_signals),
        ("اثباتِ اثر: neural_beat تا hebbian.observe می‌رسد", t_real_signals_reach_hebbian_observe_and_diverge_from_baseline),
    ])
    print(f"\n{'OK' if not failed else 'FAIL'} test_hebbian_real_signals: "
          f"{10 - failed}/10 passed, {failed} failed")
    sys.exit(1 if failed else 0)
