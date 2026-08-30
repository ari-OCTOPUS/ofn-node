#!/usr/bin/env python3
"""autoregulation.py — HH-P3: کوپلِ velocity → Governor → spend (additive).

نگاشتِ اقتصادی (توصیهٔ مالک): ضربان↔velocity · تورم↔Internal-CPI · ثباتِ پولی↔Governor.
CPIِ بالا = سیگنالِ ارزش نویزی است → تخصیصِ سریع‌تر فقط دنبال‌کردنِ نویز است →
Governor «سفت» می‌شود: بازبرنامه‌ریزیِ کندتر (epoch_damping≥1) + exploreِ محتاطانه‌تر
(advisory). استالِ velocity زیرِ باند → مؤلفهٔ فشارِ کران‌دار (بازبرنامه‌ریزیِ زودتر).

ناوردی: نرخِ خامِ ضربان هرگز مستقیم spend را تعیین نمی‌کند — این ماژول فقط cadence و
advisory تولید می‌کند؛ allocate_dry/pressure_state بایت‌به‌بایت دست‌نخورده‌اند و هیچ
importی از organ_gate/money_gate اینجا نیست.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

sys.path.insert(0, str(_HERE.parent))
from heart import interface as hi   # noqa: E402
from heart import producers        # noqa: E402

MAX_HEART_PRESSURE = 0.5     # ضربان هرگز نمی‌تواند Governor را تسخیر کند
MAX_EPOCH_DAMPING = 2.0      # CPI حداکثر ۲× epoch را کش می‌دهد
CPI_NEUTRAL_BELOW = 0.3      # زیرِ این، تورم «عادی» است (CVِ پواسونی)


def velocity_pressure(velocity_state: dict | None,
                      setpoint: "hi.HeartParams | None") -> dict:
    """استال زیرِ باند → مؤلفهٔ فشارِ کران‌دار [0..0.5]. داخل/بالای باند → 0."""
    if not velocity_state or velocity_state.get("velocity_per_hr") is None:
        return {"pressure": 0.0, "reason": "no-velocity-data"}
    if not velocity_state.get("authoritative"):
        return {"pressure": 0.0, "reason": "velocity-not-authoritative"}
    sp = setpoint or hi.HeartParams()
    v = float(velocity_state["velocity_per_hr"])
    lo = sp.viable_band_lo
    if lo <= 0 or v >= lo:
        return {"pressure": 0.0, "reason": "in-or-above-band", "gap": 0.0}
    gap = (lo - v) / lo                       # 0..1
    return {"pressure": round(min(MAX_HEART_PRESSURE, gap * MAX_HEART_PRESSURE), 3),
            "gap": round(gap, 3), "reason": "velocity-stall"}


def cpi_tightening(cpi_state: dict | None) -> dict:
    """تورمِ واسط → سفتی: epoch_damping∈[1..2] + پیشنهادِ کاهشِ explore (advisory)."""
    if not cpi_state or cpi_state.get("cpi_0_1") is None:
        return {"tighten": 0.0, "epoch_damping": 1.0,
                "explore_advice": None, "reason": "no-cpi-data"}
    cpi = float(cpi_state["cpi_0_1"])
    tighten = max(0.0, min(1.0, (cpi - CPI_NEUTRAL_BELOW) / (1.0 - CPI_NEUTRAL_BELOW)))
    damping = 1.0 + (MAX_EPOCH_DAMPING - 1.0) * tighten
    return {"tighten": round(tighten, 3),
            "epoch_damping": round(damping, 3),
            "explore_advice": f"explore_pct × {round(1.0 - 0.5 * tighten, 2)} (advisory)",
            "reason": "cpi-tightening" if tighten > 0 else "cpi-neutral"}


def governor_view(snap: dict | None = None) -> dict:
    """نمای ترکیبی برای run_epoch — fail-soft: هر چیزِ غایب → خنثی."""
    try:
        signals = producers.read_signals()
        setpoint = hi.read_setpoint()
        vp = velocity_pressure(signals.get("velocity"), setpoint)
        ct = cpi_tightening(signals.get("cpi"))
        return {
            "available": bool(signals),
            "heart_pressure": vp["pressure"],
            "velocity": (signals.get("velocity") or {}).get("velocity_per_hr"),
            "band": None if setpoint is None else
                    [setpoint.viable_band_lo, setpoint.viable_band_hi],
            "epoch_damping": ct["epoch_damping"],
            "cpi": (signals.get("cpi") or {}).get("cpi_0_1"),
            "tighten": ct["tighten"],
            "explore_advice": ct["explore_advice"],
            "reasons": {"velocity": vp["reason"], "cpi": ct["reason"]},
            "invariant": "raw-beat-never-sets-spend (cadence+advisory فقط)",
        }
    except Exception as e:  # noqa: BLE001 — کوپل نباید epoch را بکشد
        return {"available": False, "error": f"{type(e).__name__}: {e}",
                "heart_pressure": 0.0, "epoch_damping": 1.0}


if __name__ == "__main__":
    print(json.dumps(governor_view(), ensure_ascii=False, indent=2))
