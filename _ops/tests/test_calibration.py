#!/usr/bin/env python3
"""تست Doctor calibration (feedback + attention) + wiring ($0 آفلاین).

Feedback: verdict_history + should_skip_bottleneck (ضدِ تکرارِ نویز).
Attention: attention_gate (pending زیاد → فقط critical).
Wiring: flags پیش‌فرض خاموز؛ enrich_state_with_germline همیشه روشن.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("calibration")
_REAL = (harness.REAL_VAULT / r"_ops")
for _p in (str(_REAL / "doctor"), str(_REAL)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from calibration import (record_verdict, get_verdict_history, should_skip_bottleneck,  # noqa: E402
                         attention_gate, count_pending_rfc, effective_mine,
                         PENDING_SOFT_CAP, PENDING_HARD_CAP, REJECT_FORGET_N)
import wiring as W  # noqa: E402
from doctor import Doctor  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════════
# FEEDBACK LOOP
# ════════════════════════════════════════════════════════════════════════════════

def t_record_verdict_no_db_returns_false():
    """بدونِ db → False (fail-soft)."""
    assert record_verdict(None, "RFC-1", "rejected") is False


def t_attention_gate_allows_low_pending():
    """pending کم → اجازه."""
    allow, _ = attention_gate(None, 0, "high")
    assert allow is True


def t_attention_gate_blocks_when_hard_cap():
    """pending ≥ hard-cap و severity≠critical → block."""
    allow, reason = attention_gate(None, PENDING_HARD_CAP, "high")
    assert allow is False
    assert "hard-cap" in reason


def t_attention_gate_critical_passes_hard_cap():
    """critical همیشه می‌گذرد حتی در hard-cap."""
    allow, _ = attention_gate(None, PENDING_HARD_CAP + 1, "critical")
    assert allow is True


def t_attention_gate_soft_cap_blocks_low():
    """pending ≥ soft-cap و severity=medium → block."""
    allow, reason = attention_gate(None, PENDING_SOFT_CAP, "medium")
    assert allow is False
    assert "soft-cap" in reason


def t_skip_bottleneck_no_db_never_skips():
    """بدونِ db → هیچ‌وقت skip نمی‌کند (fail-open، نه fail-closed برای production)."""
    skip, _ = should_skip_bottleneck(None, "error-rate-high")
    assert skip is False


def t_count_pending_rfc():
    """شمارشِ RFCهای pending در doctor registry."""
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    # ابتدا صفر
    assert count_pending_rfc(doc) == 0


def t_effective_mine_uses_mine_when_no_calibration():
    """effective_mine بدونِ db → همان mine (fail-soft)."""
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    # mine با trace غنی
    result = effective_mine(doc, trace={"errors_24h": 3}, db=None)
    assert result is not None   # پیدا کرد


# ════════════════════════════════════════════════════════════════════════════════
# WIRING
# ════════════════════════════════════════════════════════════════════════════════

def t_flag_default_off():
    """flags پیش‌فرض خاموز (paper-mode، no regression)."""
    # مطمئن شو env ست نیست
    for k in ("OCTOPUS_WIRE_DOCTOR", "OCTOPUS_WIRE_UNIFIED", "OCTOPUS_WIRE_LEAD"):
        os.environ.pop(k, None)
    assert W.flag("OCTOPUS_WIRE_DOCTOR") is False
    assert W.flag("OCTOPUS_WIRE_UNIFIED") is False


def t_flag_on_when_set():
    """flag=1 → True."""
    os.environ["OCTOPUS_WIRE_DOCTOR"] = "1"
    assert W.flag("OCTOPUS_WIRE_DOCTOR") is True
    os.environ.pop("OCTOPUS_WIRE_DOCTOR")


def test_enrich_state_germline_always_on():
    """W-1: enrich_state_with_germline همیشه کار می‌کند (read-only، ریسک صفر)."""
    state = {}
    result = W.enrich_state_with_germline(state)
    # باید germline_lag_h یا germline_alert داشته باشد (یا fallback)
    assert "germline_lag_h" in result or "germline_alert" in result


def t_make_doctor_none_without_flag():
    """بدونِ flag → make_doctor None."""
    os.environ.pop("OCTOPUS_WIRE_DOCTOR", None)
    assert W.make_doctor() is None


def t_make_doctor_with_flag():
    """با flag → Doctor ساخته می‌شود."""
    os.environ["OCTOPUS_WIRE_DOCTOR"] = "1"
    doc = W.make_doctor(state_dir=str(ENV["ops"] / "state"))
    assert doc is not None
    os.environ.pop("OCTOPUS_WIRE_DOCTOR")


def t_make_telegram_none_without_token():
    """بدونِ TELEGRAM_BOT_TOKEN → None (no-op امن)."""
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    assert W.make_telegram_channel() is None


def t_make_unified_none_without_flag():
    """بدونِ flag → None."""
    os.environ.pop("OCTOPUS_WIRE_UNIFIED", None)
    assert W.make_unified_bus() is None


def t_make_lead_leg_none_without_flag():
    """بدونِ flag → None."""
    os.environ.pop("OCTOPUS_WIRE_LEAD", None)
    assert W.make_lead_leg() is None


def t_doctor_beat_none_without_doctor():
    """بدونِ doctor → None."""
    assert W.doctor_beat(None, 1) is None


def t_doctor_beat_skips_wrong_beat():
    """doctor_beat فقط هر N beat. beat=1 با every_n=1440 → skip."""
    os.environ["CHRONO_DOCTOR_EVERY_N_BEATS"] = "1440"
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    # beat=1 ≠ multiple of 1440 → None
    assert W.doctor_beat(doc, 1) is None
    os.environ.pop("CHRONO_DOCTOR_EVERY_N_BEATS", None)


def t_wire_summary():
    """wire_summary وضعیت flags را برمی‌گرداند."""
    os.environ.pop("OCTOPUS_WIRE_DOCTOR", None)
    s = W.wire_summary()
    assert "wire_doctor" in s and s["wire_doctor"] is False
    assert "doctor_every_n" in s


# ════════════════════════════════════════════════════════════════════════════════
# CHAMBER → run_cycle integration
# ════════════════════════════════════════════════════════════════════════════════

def t_run_cycle_uses_chamber():
    """run_cycle با use_chamber=True از Chamber می‌گذرد."""
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3},
                           use_calibration=False, use_chamber=True)
    assert result is not None
    assert "rfc_id" in result


def t_run_cycle_calibration_suppresses():
    """run_cycle با calibration: attention-budget می‌تواند suppress کند."""
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    # trace با severity پایین → اگر pending زیاد باشد، suppressed
    # (بدونِ db، attention_gate fail-open → allow)
    result = doc.run_cycle(beat=1, trace={"errors_24h": 1},
                           use_calibration=True, use_chamber=False)
    # یا RFC داده یا suppressed — ولی crash نکند
    assert result is None or "rfc_id" in result or "suppressed" in result


def t_run_cycle_backward_compatible():
    """run_cycle با use_calibration=False, use_chamber=False = همان قدیمی."""
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3},
                           use_calibration=False, use_chamber=False)
    assert result is not None and "rfc_id" in result


def t_chamber_report_survives_sandbox():
    """فیکس 2026-07-10: run_sandbox دیگر sandbox_result از-پیش-گذاشته را clobber نمی‌کند —
    گزارش chamber (که run_cycle قبل از sandbox می‌گذارد) باید تا کارت تأیید زنده بماند."""
    doc = Doctor(state_dir=str(ENV["ops"] / "state"),
                 knowledge_dir=str(ENV["ops"] / "ki"))
    result = doc.run_cycle(beat=1, trace={"errors_24h": 3},
                           use_calibration=False, use_chamber=True)
    assert result is not None and "rfc_id" in result
    rfc = doc._rfcs.get(result["rfc_id"])
    assert rfc is not None
    assert isinstance(rfc.sandbox_result, dict)
    assert "chamber" in rfc.sandbox_result, \
        f"گزارش chamber بعد از sandbox باید بماند؛ keys={list(rfc.sandbox_result.keys())}"
    # کلیدهای خودِ sandbox هم باید باشند (merge، نه فقط حفظِ قدیمی)
    assert "critic" in rfc.sandbox_result


if __name__ == "__main__":
    failed = harness.run([
        # Feedback
        ("[FB] record_verdict بدونِ db → False", t_record_verdict_no_db_returns_false),
        ("[AT] pending کم → اجازه", t_attention_gate_allows_low_pending),
        ("[AT] hard-cap + high → block", t_attention_gate_blocks_when_hard_cap),
        ("[AT] critical از hard-cap می‌گذرد", t_attention_gate_critical_passes_hard_cap),
        ("[AT] soft-cap + medium → block", t_attention_gate_soft_cap_blocks_low),
        ("[FB] skip_bottleneck بدونِ db → no-skip", t_skip_bottleneck_no_db_never_skips),
        ("[FB] count_pending_rfc", t_count_pending_rfc),
        ("[FB] effective_mine بدونِ db = mine", t_effective_mine_uses_mine_when_no_calibration),
        ("[CH] گزارش chamber از sandbox زنده می‌ماند", t_chamber_report_survives_sandbox),
        # Wiring
        ("[W] flags پیش‌فرض خاموز", t_flag_default_off),
        ("[W] flag=1 → True", t_flag_on_when_set),
        ("[W-1] enrich germline همیشه روشن", test_enrich_state_germline_always_on),
        ("[W] make_doctor بدونِ flag → None", t_make_doctor_none_without_flag),
        ("[W] make_doctor با flag → Doctor", t_make_doctor_with_flag),
        ("[W] make_telegram بدونِ توکن → None", t_make_telegram_none_without_token),
        ("[W] make_unified بدونِ flag → None", t_make_unified_none_without_flag),
        ("[W] make_lead بدونِ flag → None", t_make_lead_leg_none_without_flag),
        ("[W] doctor_beat بدونِ doctor → None", t_doctor_beat_none_without_doctor),
        ("[W] doctor_beat wrong beat → skip", t_doctor_beat_skips_wrong_beat),
        ("[W] wire_summary", t_wire_summary),
        # Chamber integration
        ("[C→rc] run_cycle با Chamber", t_run_cycle_uses_chamber),
        ("[C→rc] run_cycle calibration suppress", t_run_cycle_calibration_suppresses),
        ("[C→rc] run_cycle backward-compatible", t_run_cycle_backward_compatible),
    ])
    sys.exit(1 if failed else 0)
