#!/usr/bin/env python3
"""تست HH-P11 (لِینِ ۳ — MEGAPROMPT ۲۰۲۶-۰۸-۰۵) — آمادگیِ سیم‌کشیِ زندهٔ داورِ نبض.

این فایل مکملِ test_pulse_arbiter.py است، نه جایگزینش: آنجا فقط «امروز بسته است»
را می‌سنجد (بخشِ ی). اینجا **سه‌گانهٔ دقیقِ شرط** را یکی‌یکی و ترکیبی می‌سنجد —
چون تسکِ لِینِ ۳ صریحاً می‌خواهد قبل از هر فلیپِ زنده اثبات شود که:

  (الف) غیابِ فایلِ ACTIVATION-PULSE-ARBITER.flag به‌تنهایی کافی است تا wire_open()
        بسته بماند — حتی وقتی هر دو envِ OCTOPUS_WIRE_PULSE_ARBITER/OCTOPUS_WIRE_BIO
        روشن‌اند. گیت واقعاً AND سه‌طرفه است، نه یک flag تنها.
  (ب) با هر سه شرط حاضر (دو env + فایل)، wire_open() باز می‌شود.
  (ج) effective_period_if_open مسیرِ authority را واقعاً اعمال می‌کند: بسته → default_s
      دست‌نخورده؛ باز بدون baseline معتبر → همچنان بسته؛ باز با baseline معتبر →
      control_lawِ shadow فقط مشاهده می‌شود و candidateِ دو رأی معتبر با anchor ثابت
      non-acceleration اعمال می‌شود. این یک اثر رفتاری است، نه فقط تغییرِ رشتهٔ JSON.

⚠️ همهٔ این تست‌ها داخلِ ops_dir موقتِ harness (تمپ‌فایلِ ویندوز) کار می‌کنند و هیچ
فایلِ فعال‌سازیِ واقعی یا envِ زندهٔ this-process-only را در `F:\\backup` نمی‌سازند/
نمی‌نویسند. `pa.ACT_ARBITER`/`opslib.OPS` هر دو از همان تمپ resolve می‌شوند چون
harness.setup() پیش از importِ opslib/pulse_arbiter مقدارِ OPS_DIR را ست می‌کند
(نگاه کن harness.py — الگوی همهٔ تست‌های این پوشه).
"""
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("pulse-arbiter-wire-readiness")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
from heart import pulse_arbiter as pa  # noqa: E402

# دومین envِ لازم (OCTOPUS_WIRE_BIO) داخلِ pulse_arbiter.wire_open() فقط به‌صورتِ
# رشتهٔ لفظی خوانده می‌شود — بدونِ ثابتِ ماژول‌سطحیِ جدا (فقط pa.FLAG_ENV صادراتی
# است، برای OCTOPUS_WIRE_PULSE_ARBITER). عمداً همان رشته را اینجا هم لفظی می‌نویسیم
# (نه حدس؛ از خودِ pulse_arbiter.py:458 خوانده شد) تا اگر روزی ثابتی برایش ساخته
# شد، این فایل به‌جای import شکسته، فقط دیگر «تنها منبعِ رشته» نباشد.
_FLAG_BIO = "OCTOPUS_WIRE_BIO"


def _reset():
    """هر سه شرط را به حالتِ «بسته» برگردان — قبل و بعدِ هر تست (idempotent)."""
    os.environ.pop(pa.FLAG_ENV, None)
    os.environ.pop(_FLAG_BIO, None)
    if pa.ACT_ARBITER.exists():
        pa.ACT_ARBITER.unlink()


def _arm_all():
    """هر سه شرط را «باز» کن — فقط داخلِ envِ همین پروسهٔ تست و فایلِ داخلِ
    ops_dir موقتِ harness؛ هرگز چیزی در درختِ زنده."""
    os.environ[pa.FLAG_ENV] = "1"
    os.environ[_FLAG_BIO] = "1"
    pa.ACT_ARBITER.parent.mkdir(parents=True, exist_ok=True)
    pa.ACT_ARBITER.write_text("owner-created (test-only, temp ops_dir)\n", "utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# (الف) غیابِ فایلِ فعال‌سازی → همیشه بسته، حتی با هر دو envِ روشن
# ════════════════════════════════════════════════════════════════════════════════
def t_flag_absent_blocks_even_with_both_env_on():
    """قلبِ ادعای CRITICAL SAFETY: تنها چیزِ غایب امروز همین فایل است — پس این
    تست دقیقاً همان مسیر را می‌سنجد که امشب واقعاً بسته نگهش داشته."""
    _reset()
    try:
        os.environ[pa.FLAG_ENV] = "1"
        os.environ[_FLAG_BIO] = "1"
        assert not pa.ACT_ARBITER.exists(), "پیش‌شرطِ تست: فایل نباید از قبل باشد"
        ok, reasons = pa.wire_open()
        assert ok is False, (ok, reasons)
        assert any("live-gate" in r for r in reasons), reasons
    finally:
        _reset()


def t_each_missing_condition_individually_blocks():
    """ماتریسِ کاملِ ۷ ترکیبِ ناقص (از ۸ حالتِ ممکن، بدونِ حالتِ کاملِ «هر سه روشن»):
    گیت واقعاً AND سه‌طرفه است — غیابِ دقیقاً یکی از سه شرط هم برای بسته‌ماندن کافی است."""
    combos = [
        (False, False, False), (True, False, False), (False, True, False),
        (False, False, True), (True, True, False), (True, False, True),
        (False, True, True),
    ]
    try:
        for env_arb, env_bio, has_flag in combos:
            _reset()
            if env_arb:
                os.environ[pa.FLAG_ENV] = "1"
            if env_bio:
                os.environ[_FLAG_BIO] = "1"
            if has_flag:
                pa.ACT_ARBITER.parent.mkdir(parents=True, exist_ok=True)
                pa.ACT_ARBITER.write_text("x", "utf-8")
            ok, reasons = pa.wire_open()
            assert ok is False, f"combo={(env_arb, env_bio, has_flag)} باید بسته بماند: {reasons}"
    finally:
        _reset()


# ════════════════════════════════════════════════════════════════════════════════
# (ب) هر سه شرط حاضر → باز
# ════════════════════════════════════════════════════════════════════════════════
def t_all_three_conditions_open_the_wire():
    _reset()
    try:
        _arm_all()
        ok, reasons = pa.wire_open()
        assert ok is True, reasons
        assert reasons == [], reasons
    finally:
        _reset()


# ════════════════════════════════════════════════════════════════════════════════
# (ج) effective_period_if_open: بسته=default؛ باز=authority guard + anchor ثابت
# ════════════════════════════════════════════════════════════════════════════════
def _fixture_views():
    """سه قلبِ متحرک و متمایز (cardiac=40s با mass>1 تا LIVE باشد نه CONSTANT،
    control_law=45s با `ts` تازه تا LIVE باشد نه UNKNOWN، rhythm=50s که همیشه LIVE
    است) — تا اجماع مقداری قابلِ پیش‌بینی و **دور از default_s** بدهد. اگر فلیپ
    فقط رشتهٔ wire_open را عوض می‌کرد، این عدد هرگز از default حرکت نمی‌کرد."""
    return dict(
        cardiac_snapshot={"enabled": True,
                          "bio_rhythm": {"period_s": 40.0, "pace": "balanced", "mass": 5.0},
                          "budget": {}, "baroreflex_factor": None},
        heart_shadow={"period_s": 45.0, "telemetry": {"gates": {}}, "ts": opslib.now_iso()},
        rhythm_state={"mode_color": "GREEN", "T_beat": 50.0, "hrv": 4.0,
                     "mode_focus": "STEADY"},
    )


def t_effective_period_differs_open_vs_closed():
    """G4: بازشدنِ outer wire بدون baseline، authority نمی‌سازد؛ با baseline معتبر
    candidateِ دو قلب محاسبه می‌شود ولی حذفِ رأی shadow حقِ تسریع ندارد."""
    views = _fixture_views()
    default_s = 777.0

    expected_candidate = pa.arbitrate(pa.gather_views(**views))["effective_period_s"]
    assert expected_candidate < 60.0, expected_candidate

    _reset()
    try:
        period_closed, snap_closed = pa.effective_period_if_open(default_s, **views)
        assert snap_closed["wire_open"] is False, snap_closed
        assert period_closed == default_s, period_closed

        _arm_all()
        period_no_base, snap_no_base = pa.effective_period_if_open(default_s, **views)
        assert period_no_base == default_s
        assert snap_no_base["wire_open"] is False
        assert snap_no_base["authority_status"] == "NO_VALID_BASELINE"

        previous = {
            "schema": pa.SCHEMA, "effective_period_s": 98.11,
            "wire_open": True, "written": True,
        }
        original = pa.read_latest
        pa.read_latest = lambda: previous
        try:
            period_open, snap_open = pa.effective_period_if_open(default_s, **views)
        finally:
            pa.read_latest = original
        assert snap_open["wire_open"] is True, snap_open
        assert snap_open["n_present"] == 2, snap_open
        control = next(v for v in snap_open["votes"] if v["heart"] == "control_law")
        assert control["present"] is False and control["eligible_for_live"] is False
        assert control["authority"] == "SHADOW_ONLY"
        assert math.isclose(snap_open["candidate_period_s"], expected_candidate, rel_tol=1e-9)
        assert math.isclose(period_open, 98.11, rel_tol=1e-9), snap_open
        assert snap_open["driver"] == "authority-hold"
        assert snap_open["authority_hold_applied"] is True
    finally:
        _reset()


def t_half_open_still_returns_default():
    """کنترلِ منفی: فایل حاضر ولی فقط یکی از دو envِ لازم روشن → هنوز default
    برمی‌گردد (نه عددِ نصفه‌بسته). گیت باینری است، درجه‌بندی‌شده نیست."""
    views = _fixture_views()
    _reset()
    try:
        pa.ACT_ARBITER.parent.mkdir(parents=True, exist_ok=True)
        pa.ACT_ARBITER.write_text("x", "utf-8")
        os.environ[pa.FLAG_ENV] = "1"      # فقط یکی از دو env روشن
        period, snap = pa.effective_period_if_open(999.0, **views)
        assert snap["wire_open"] is False, snap
        assert period == 999.0, period
    finally:
        _reset()


if __name__ == "__main__":
    failed = harness.run([
        ("[الف] غیابِ فایل → بسته حتی با هر دو env", t_flag_absent_blocks_even_with_both_env_on),
        ("[الف] ماتریسِ کاملِ AND سه‌شرطی", t_each_missing_condition_individually_blocks),
        ("[ب] هر سه شرط → باز", t_all_three_conditions_open_the_wire),
        ("[ج] period متفاوت: باز≠بسته، باز=اجماعِ واقعی", t_effective_period_differs_open_vs_closed),
        ("[ج] نیم‌باز هم بسته می‌ماند (باینری)", t_half_open_still_returns_default),
    ])
    sys.exit(1 if failed else 0)
