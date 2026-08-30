"""test_heart_fuel.py — HH-fuel 2026-07-19: سوختِ زندگیِ قلب + جداسازیِ دو پول.

نامتغیرها: خونِ قلب = fuel (مصرفِ API/Ollama)، نه پولِ حساب؛ confirmed → leg_money جدا؛
flag خاموش=no-op؛ kill-switch اول؛ honest pulse = سوخت (پول/beatsِ انبوه ضربان جعل نمی‌کنند).
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("heart-fuel")

import importlib                    # noqa: E402
import heart.producers as producers  # noqa: E402
importlib.reload(producers)
import heart.fuel_meter as fm        # noqa: E402
importlib.reload(fm)


def _clear():
    for k in ("OCTOPUS_WIRE_HEART_FUEL", "OCTOPUS_HEART_HONEST_PULSE"):
        os.environ.pop(k, None)


def t_a_flag_off_is_noop():
    _clear()
    assert fm.enabled() is False
    assert fm.record("local", "m") is None
    assert not fm.STREAM_PATH.exists()


def t_b_records_local_and_paid_no_content():
    os.environ["OCTOPUS_WIRE_HEART_FUEL"] = "1"
    assert fm.record("local", "qwen2.5:latest", cost_usd=0.0, ms=700, ok=True)
    assert fm.record("primary", "fugu", cost_usd=0.02, ms=1500, ok=True)
    recs = [json.loads(l) for l in open(fm.STREAM_PATH)]
    assert len(recs) == 2
    assert recs[1]["cost_musd"] == 20000, recs[1]        # 0.02 USD = 20000 micro-USD
    assert "prompt" not in recs[0] and "text" not in recs[0]   # محتوا هرگز ثبت نمی‌شود


def t_c_count_fuel_window():
    since = dt.datetime.now() - dt.timedelta(hours=24)
    calls, musd = producers._count_fuel(since)
    assert calls >= 2 and musd >= 20000
    future = dt.datetime.now() + dt.timedelta(hours=1)
    assert producers._count_fuel(future) == (0, 0)


def t_d_fuel_is_heart_blood():
    v = producers.velocity_meter(window_hours=24.0)
    assert v["fuel_velocity_per_hr"] is not None and v["fuel_velocity_per_hr"] > 0
    assert v["real_velocity_per_hr"] == v["fuel_velocity_per_hr"]   # خونِ قلب = سوخت
    assert v["real_components"]["fuel_calls"] >= 2


def t_e_real_account_money_separated_from_heart():
    """confirmed(پولِ حساب) خونِ قلب نیست — leg_money جدا؛ سوخت=۰ → خونِ قلب=۰ نه ۵."""
    _save = (producers._count_confirmed, producers._count_effects_settled,
             producers._count_consolidation, producers._count_beats,
             producers._count_cognition, producers._count_fuel)
    producers._count_confirmed = lambda s: (5, [dt.datetime.now().timestamp()] * 5)
    producers._count_effects_settled = lambda s: 0
    producers._count_consolidation = lambda s: 0
    producers._count_beats = lambda s: 1000
    producers._count_cognition = lambda s: None
    producers._count_fuel = lambda s: (0, 0)
    try:
        v = producers.velocity_meter(window_hours=24.0)
    finally:
        (producers._count_confirmed, producers._count_effects_settled,
         producers._count_consolidation, producers._count_beats,
         producers._count_cognition, producers._count_fuel) = _save
    assert v["leg_money_count"] == 5                # پولِ حساب = KPI پا، جدا
    assert v["channels"]["leg_money"] == 5
    assert v["fuel_velocity_per_hr"] == 0.0         # سوختِ قلب صفر
    assert v["real_velocity_per_hr"] == 0.0         # خونِ قلب (سوخت) صفر — نه ۵ پول


def t_f_honest_pulse_is_fuel_not_money():
    """honest روشن: ضربان = سوخت + کفِ سقف‌دارِ beats؛ پولِ حساب و beatsِ انبوه جعل نمی‌کنند."""
    _save = (producers._count_confirmed, producers._count_effects_settled,
             producers._count_consolidation, producers._count_beats,
             producers._count_cognition, producers._count_fuel)
    producers._count_confirmed = lambda s: (5, [dt.datetime.now().timestamp()] * 5)
    producers._count_effects_settled = lambda s: 0
    producers._count_consolidation = lambda s: 0
    producers._count_beats = lambda s: 1349
    producers._count_cognition = lambda s: None
    producers._count_fuel = lambda s: (12, 0)
    try:
        os.environ.pop("OCTOPUS_HEART_HONEST_PULSE", None)
        v_off = producers.velocity_meter(window_hours=24.0)
        os.environ["OCTOPUS_HEART_HONEST_PULSE"] = "1"
        v_on = producers.velocity_meter(window_hours=24.0)
    finally:
        (producers._count_confirmed, producers._count_effects_settled,
         producers._count_consolidation, producers._count_beats,
         producers._count_cognition, producers._count_fuel) = _save
        os.environ.pop("OCTOPUS_HEART_HONEST_PULSE", None)
    # honest: total = fuel(12) + min(beats_units=134.9, cap=3)=3 → 15/24
    assert abs(v_on["velocity_per_hr"] - (12 + 3) / 24.0) < 1e-3, v_on
    assert v_on["velocity_per_hr"] < v_off["velocity_per_hr"], (v_off, v_on)  # پول در ضربانِ صادق نیست
    assert v_on["real_velocity_per_hr"] == round(12 / 24.0, 4)


def t_g_kill_switch_blocks_record():
    os.environ["OCTOPUS_WIRE_HEART_FUEL"] = "1"
    stop = fm.opslib.STOP_ORGANISM
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("stop", encoding="utf-8")
    try:
        assert fm.record("local", "m") is None   # kill-switch اول
    finally:
        try:
            stop.unlink()                         # mini-vault موقت است، unlink مجاز
        except OSError:
            pass


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_fuel: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
