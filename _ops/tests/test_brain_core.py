#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_brain_core.py — C7.1: ریشهٔ ترکیبِ ضربانِ سایه با **parityِ واقعیِ زمان‌محور**.

این نسخه false-parity (B11..B13) را می‌کشد:
  * ParityTracker در build_shadow_scheduler ساخته و در **مسیرِ tick** compare می‌شود (B11).
  * PARITY-GREEN فقط با soakِ پیوستهٔ ≥۲۴h — نه با شمارشِ نمونه (B12).
  * وضعیتِ BrainCore در organism_state_block/ORGANISM-STATE ظاهر می‌شود (B13).
  * صفر ACT؛ missing از mismatch جدا؛ HALT فقط فازهای امن؛ cortex/doctor دوباره اجرا نمی‌شوند.
$0 آفلاین؛ صفر شبکه؛ virtual clock؛ state در sandbox.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("brain-core")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import brain_core as bc  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))
_H = 3600.0


def _on():
    os.environ["OCTOPUS_ONE_HEARTBEAT"] = "1"


def _off():
    os.environ.pop("OCTOPUS_ONE_HEARTBEAT", None)


def _fresh_sd(tag):
    sd = _STATE / f"pt-{tag}"
    (sd / "pulse").mkdir(parents=True, exist_ok=True)
    p = bc._parity_path(sd)
    if p.exists():
        p.unlink()
    return sd


# ── ۱+۲: composition adapterهای واقعی، صفر ACT ──────────────────────────────────
def t_composition_real_adapters_no_act():
    _on()
    sch = bc.build_shadow_scheduler(state_dir=_fresh_sd("comp"), clock=lambda: 1000.0,
                                    halted_fn=lambda: None)
    assert sch is not None
    phases = bc.registered_organ_phases(sch)
    assert set(phases) == {"SENSE", "RECORD", "THINK", "HEAL"}, phases
    assert "ACT" not in phases, "صفر ACT در سایه"
    names = {o.name for o in sch._organs}
    assert names == {"health", "spine-observe", "cortex-advisory", "doctor-advisory"}, names
    assert getattr(sch, "parity", None) is not None, "ParityTracker باید سیم‌کشی شود (B11)"


# ── ۳: فلگ خاموش → None ─────────────────────────────────────────────────────────
def t_flag_off_no_scheduler():
    _off()
    assert bc.build_shadow_scheduler(state_dir=_STATE) is None


# ── ۴ (B11): compare در **مسیرِ tick** صدا زده می‌شود (نه dead-code) ─────────────
def t_parity_compare_called_in_tick():
    _on()
    sd = _fresh_sd("tick")
    sch = bc.build_shadow_scheduler(state_dir=sd, clock=lambda: 1000.0, halted_fn=lambda: None)
    before = sch.parity.counters["compared"]
    r = sch.tick()
    after = sch.parity.counters["compared"]
    assert r["beat"] == 1 and not r["degraded"]
    # SENSE(health) + RECORD(spine-observe) هر دو comparable → compare در tick اجرا شد
    assert after - before >= 2, f"compare باید در مسیرِ tick صدا شود (B11): {before}->{after}"
    assert not any(o.phase == "ACT" for o in sch._organs), "صفر ACT"


# ── ۵: طبقه‌بندیِ parity — missing از mismatch جدا ─────────────────────────────────
def t_parity_classification():
    _on()
    pt = bc.ParityTracker(state_dir=_fresh_sd("cls"), clock=lambda: 1000.0)
    assert pt.compare("x", {"a": 1}, {"a": 1}) == "matched"
    assert pt.compare("x", {"a": 1}, {"a": 2}, critical=True) == "mismatched"
    assert pt.compare("x", None, {"a": 1}) == "missing_old"
    assert pt.compare("x", {"a": 1}, None) == "missing_new"
    c = pt.counters
    assert c["compared"] == 4 and c["matched"] == 1 and c["mismatched"] == 1
    assert c["missing_old"] == 1 and c["missing_new"] == 1 and c["critical_mismatched"] == 1
    # mismatchِ ثبت‌شده فقط طبقهٔ ساختاری (بدونِ PII/محتوای خام)
    assert all(set(m.keys()) <= {"organ", "class"} for m in pt.mismatches), pt.mismatches


# ── ۶ (B12): زیرِ ۲۴ساعت هرگز green — حتی با انبوهِ matched ───────────────────────
def t_under_24h_never_green():
    _on()
    pt = bc.ParityTracker(state_dir=_fresh_sd("u24"), clock=lambda: 0.0)
    for _ in range(150):                       # ۱۵۰ matched ولی همه در لحظهٔ صفر → elapsed=0
        pt.compare("health", 1, 1, now=0.0)
    assert pt.counters["matched"] == 150
    assert pt.status(now=0.0) == "SHADOW-LIVE", "شمارشِ نمونه بدونِ زمان نباید green کند (B12)"
    # حتی ۱۲ ساعت هم کافی نیست
    assert pt.status(now=12 * _H) == "SHADOW-LIVE"


# ── ۷ (B12): ۲۴ساعتِ پیوسته + نمونهٔ کافی + صفر mismatch → green ─────────────────
def t_24h_continuous_green():
    _on()
    pt = bc.ParityTracker(state_dir=_fresh_sd("g24"), clock=lambda: 0.0)
    # ۱۰۰ نمونه با فاصلهٔ ۹۰۰s (< gapِ مجاز) → span ≈ 89100s > 86400
    t = 0.0
    for _ in range(100):
        pt.compare("health", 1, 1, now=t)
        t += 900.0
    last = t - 900.0
    assert pt.continuous_elapsed_s(now=last) >= 24 * _H
    assert pt.status(now=last) == "PARITY-GREEN", f"۲۴h پیوسته + نمونه → green: {pt.soak_report(last)}"


# ── ۸ (B12): critical mismatch → هرگز green ──────────────────────────────────────
def t_critical_mismatch_blocks_green():
    _on()
    pt = bc.ParityTracker(state_dir=_fresh_sd("crit"), clock=lambda: 0.0)
    t = 0.0
    for _ in range(100):
        pt.compare("health", 1, 1, now=t); t += 900.0
    pt.compare("health", 1, 2, critical=True, now=t)   # یک critical mismatch
    assert pt.counters["critical_mismatched"] == 1
    assert pt.status(now=t) == "SHADOW-LIVE", "critical mismatch باید green را ببندد"


# ── ۹ (B12): gapِ بزرگ پیوستگی را می‌شکند → started_at ری‌ست → not green ─────────
def t_restart_gap_breaks_continuity():
    _on()
    pt = bc.ParityTracker(state_dir=_fresh_sd("gap"), clock=lambda: 0.0)
    t = 0.0
    for _ in range(100):
        pt.compare("health", 1, 1, now=t); t += 900.0
    # درست پیش از green بودیم؛ حالا یک gapِ بزرگ (> 1h) → پیوستگی می‌شکند
    big = t + 2 * _H
    pt.compare("health", 1, 1, now=big)
    assert len(pt.restart_gaps) == 1, "gapِ بزرگ باید ثبت شود"
    assert pt.continuous_elapsed_s(now=big) < 24 * _H, "started_at باید ری‌ست شود"
    assert pt.status(now=big) == "SHADOW-LIVE", "gapِ خارج از سیاست → not green"


# ── ۱۰ (B13): وضعیتِ BrainCore در organism_state_block ───────────────────────────
def t_state_block_exposed():
    _on()
    sd = _fresh_sd("state")
    sch = bc.build_shadow_scheduler(state_dir=sd, clock=lambda: 1000.0, halted_fn=lambda: None)
    sch.tick()
    block = bc.organism_state_block(state_dir=sd, sched=sch)
    assert block["flag_on"] is True and block["mode"] in ("SHADOW-LIVE", "PARITY-GREEN"), block
    assert "parity" in block and "counters" in block["parity"], block
    assert block["parity"]["soak_min_hours"] == 24.0, block
    _off()
    off_block = bc.organism_state_block(state_dir=sd)
    assert off_block["mode"] == "HARNESS", off_block


# ── ۱۱: HALT → فقط فازهای امن؛ cortex/doctor دوباره اجرا نمی‌شوند ─────────────────
def t_halt_safe_phases_only():
    _on()
    sch = bc.build_shadow_scheduler(state_dir=_fresh_sd("halt"), clock=lambda: 1000.0,
                                    halted_fn=lambda: "STOP-METABOLIC")
    r = sch.tick()
    assert r["halted"] == "STOP-METABOLIC"
    ran = set(r["phase_order"])
    assert "cortex-advisory" not in ran, "THINK زیرِ HALT اجرا نمی‌شود (فقط SENSE/RECORD/HEAL)"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱+۲] composition واقعی + parity سیم‌کشی، صفر ACT", t_composition_real_adapters_no_act),
        ("[۳] فلگ خاموش → None", t_flag_off_no_scheduler),
        ("[۴/B11] compare در مسیرِ tick", t_parity_compare_called_in_tick),
        ("[۵] طبقه‌بندی parity (missing≠mismatch)", t_parity_classification),
        ("[۶/B12] زیرِ ۲۴h هرگز green (حتی انبوه match)", t_under_24h_never_green),
        ("[۷/B12] ۲۴h پیوسته + نمونه → green", t_24h_continuous_green),
        ("[۸/B12] critical mismatch → not green", t_critical_mismatch_blocks_green),
        ("[۹/B12] gap پیوستگی را می‌شکند → not green", t_restart_gap_breaks_continuity),
        ("[۱۰/B13] وضعیت BrainCore در state block", t_state_block_exposed),
        ("[۱۱] HALT فقط فازهای امن", t_halt_safe_phases_only),
    ])
    sys.exit(1 if failed else 0)
