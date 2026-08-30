"""test_heart_cognition.py — HH-artery 2026-07-19: effectِ شناختیِ بیرونی-تأییدشده.

به‌روزِ 2026-07-19 (جداسازیِ دو پول): cognition حالا کانالِ **value** را تغذیه می‌کند
(نه خونِ قلب — خونِ قلب = fuel). خودسنجی همچنان رد؛ flag خاموش=no-op؛ flag-off بایت‌به‌بایت.
ترتیبِ چک‌ها با پیشوندِ حرفی pin شده (state مشترکِ mini-vault؛ env قبل از import).
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
ENV = harness.setup("heart-cognition")

import importlib                       # noqa: E402
import heart.producers as producers    # noqa: E402
importlib.reload(producers)
import heart.cognition_effect as ce    # noqa: E402
importlib.reload(ce)


def _clear_flags():
    for k in ("OCTOPUS_WIRE_COGNITION_EFFECT", "OCTOPUS_HEART_HONEST_PULSE"):
        os.environ.pop(k, None)


def t_a_flag_off_is_noop():
    """flag خاموش → record هیچ نمی‌نویسد و None برمی‌گرداند (بایت‌به‌بایت)."""
    _clear_flags()
    assert ce.enabled() is False
    assert ce.record("x", "id1", validator="owner") is None
    assert not ce.STREAM_PATH.exists()


def t_b_self_validator_rejected():
    """خودسنجی (llm/self/خالی/model) ساختاراً رد — هیچ خونِ قلابی."""
    os.environ["OCTOPUS_WIRE_COGNITION_EFFECT"] = "1"
    assert ce.record("x", "id2", validator="llm") is None
    assert ce.record("x", "id3", validator="self") is None
    assert ce.record("x", "id4", validator="") is None
    assert ce.record("x", "id5", validator="model") is None
    n = sum(1 for _ in open(ce.STREAM_PATH)) if ce.STREAM_PATH.exists() else 0
    assert n == 0, f"خودسنجی نباید نوشته شود: {n}"


def t_c_owner_effect_recorded():
    """تأییدِ بیرونی (owner) → رکورد در استریم نوشته می‌شود."""
    os.environ["OCTOPUS_WIRE_COGNITION_EFFECT"] = "1"
    r = ce.record("owner-approval", "job-1", validator="owner", weight_class="review")
    assert r and r["validator"] == "owner" and r["leg"] == "owner-approval"
    recs = [json.loads(l) for l in open(ce.STREAM_PATH)]
    assert any(x["artifact_id"] == "job-1" for x in recs)


def t_d_count_cognition_in_window():
    """producers._count_cognition رکوردِ تازه را در پنجره می‌شمارد؛ پنجرهٔ آینده → صفر."""
    since = dt.datetime.now() - dt.timedelta(hours=24)
    assert producers._count_cognition(since) >= 1
    future = dt.datetime.now() + dt.timedelta(hours=1)
    assert producers._count_cognition(future) == 0


def t_e_cognition_feeds_value_channel_not_heart_blood():
    """cognitionِ واقعی → کانالِ value (خروجی)، نه خونِ قلب. بدونِ سوخت، real(=fuel)=None."""
    _clear_flags()
    os.environ["OCTOPUS_WIRE_COGNITION_EFFECT"] = "1"
    v = producers.velocity_meter(window_hours=24.0)
    for key in ("fuel_velocity_per_hr", "value_velocity_per_hr", "leg_money_count",
                "metronome_share", "honest_pulse", "channels"):
        assert key in v, f"فیلدِ کانال غایب: {key}"
    assert v["components"].get("cognition") is not None and v["components"]["cognition"] >= 1
    assert v["value_velocity_per_hr"] is not None and v["value_velocity_per_hr"] > 0  # value
    assert v["real_velocity_per_hr"] is None            # خونِ قلب = سوخت؛ سوختی ثبت نشده


def t_f_honest_pulse_caps_metronome():
    """honest روشن: ضربان = سوخت + کفِ سقف‌دارِ beats؛ beatsِ انبوه throughput جعل نمی‌کند."""
    _save = (producers._count_confirmed, producers._count_effects_settled,
             producers._count_consolidation, producers._count_beats,
             producers._count_cognition, producers._count_fuel)
    producers._count_confirmed = lambda s: (0, [])
    producers._count_effects_settled = lambda s: 0
    producers._count_consolidation = lambda s: 0
    producers._count_beats = lambda s: 1349
    producers._count_cognition = lambda s: 0
    producers._count_fuel = lambda s: (0, 0)
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
    assert v_off["velocity_per_hr"] > 1.0, v_off                      # beats غالب (~5.6/hr)
    assert v_on["velocity_per_hr"] < v_off["velocity_per_hr"], (v_off, v_on)   # سقف خورد
    assert v_off["metronome_share"] is not None and v_off["metronome_share"] > 0.9, v_off


def t_g_flag_off_byte_identical_shape():
    """استریم‌های نو غایب + honest خاموش → velocity_per_hr برابرِ فرمولِ کلاسیک (رگرسیون)."""
    _save = (producers._count_confirmed, producers._count_effects_settled,
             producers._count_consolidation, producers._count_beats,
             producers._count_cognition, producers._count_fuel)
    producers._count_confirmed = lambda s: (2, [dt.datetime.now().timestamp()] * 2)
    producers._count_effects_settled = lambda s: 1
    producers._count_consolidation = lambda s: None
    producers._count_beats = lambda s: None
    producers._count_cognition = lambda s: None
    producers._count_fuel = lambda s: (None, 0)
    try:
        _clear_flags()
        v = producers.velocity_meter(window_hours=24.0)
    finally:
        (producers._count_confirmed, producers._count_effects_settled,
         producers._count_consolidation, producers._count_beats,
         producers._count_cognition, producers._count_fuel) = _save
    assert v["components"]["cognition"] is None
    assert "cognition" not in v["sources_available"]
    assert abs(v["velocity_per_hr"] - (2 * 3.0 + 1) / 24.0) < 1e-3, v
    assert v["sample_size"] == 3


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_cognition: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
