#!/usr/bin/env python3
"""ziman_biology.py — اتصال زیستیِ پای Ziman به قلب، اعصاب و دکتر تکاملی.

این ماژول یک adapter مشورتی است، نه effector:
  Heart -> فقط rhythm/setpoint خوانده می‌شود؛ زیمان قلب را تغییر نمی‌دهد.
  Nerves -> SignalHub یک NeuralSnapshot(advisory_only=True) می‌سازد.
  Doctor -> فقط در anomaly یک RFC پیشنهاد می‌دهد؛ sandbox/human-append حاکم است.

قوانین پذیرفته‌شده:
  * STOP / protective mode مقدم است.
  * sigma <= 1؛ sigma بالاتر anomaly بحرانی است.
  * lambda_persist منفی؛ uptime/self-preservation هدف نیست.
  * publish/send/spend/pay/deploy وجود ندارد.
  * خروجی content-free و بدون PII/secret است.

additive · stdlib-only · local · fail-closed
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (_OPS, _OPS / "budget", _OPS / "neural", _OPS / "doctor"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib  # noqa: E402
from signal_hub import SignalHub  # noqa: E402

SCHEMA = "ziman-biology.v1"
_HUB = SignalHub()


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text("utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, TypeError, ValueError):
        return {}


def heart_readmodel() -> dict:
    """نمای فقط‌خواندنی قلب. هیچ write/setpoint در این مسیر وجود ندارد."""
    shadow = _read_json(opslib.STATE_DIR / "pulse" / "heart-shadow-latest.json")
    setpoint = _read_json(opslib.STATE_DIR / "pulse" / "heart-setpoint-latest.json")
    try:
        period = float(shadow.get("period_s"))
        if not math.isfinite(period) or period <= 0:
            period = None
    except (TypeError, ValueError):
        period = None
    try:
        sigma = shadow.get("sigma_now")
        sigma = float(sigma) if sigma is not None else None
        if sigma is not None and not math.isfinite(sigma):
            sigma = None
    except (TypeError, ValueError):
        sigma = None
    return {
        "period_s": period,
        "sigma_now": sigma,
        "target_sigma": setpoint.get("target_sigma"),
        "viable_band_lo": setpoint.get("viable_band_lo"),
        "viable_band_hi": setpoint.get("viable_band_hi"),
        "authority": "rhythm_only",
        "ziman_can_write_heart": False,
    }


def health_assessment(ziman_status: dict | None, heart: dict | None = None) -> dict:
    """تشخیص خالص و fail-closed؛ unknown را healthy فرض نمی‌کند."""
    status = ziman_status if isinstance(ziman_status, dict) else {}
    heart = heart if isinstance(heart, dict) else heart_readmodel()
    anomalies: list[dict[str, Any]] = []

    sigma = heart.get("sigma_now")
    if sigma is not None and sigma > 1.0:
        anomalies.append({"code": "SIGMA_CANCER_RISK", "severity": "critical"})

    capacity = status.get("capacity_ceiling_per_week")
    capacity_class = status.get("capacity_evidence_class", "UNVERIFIED")
    if capacity in (None, 0) or capacity_class in ("UNVERIFIED", "CONFLICT", "UNKNOWN"):
        anomalies.append({"code": "CAPACITY_UNVERIFIED", "severity": "high"})

    if status.get("autonomy") != "propose-only":
        anomalies.append({"code": "AUTONOMY_DRIFT", "severity": "critical"})
    if status.get("execution_state") != "ZERO outward execution — drafts only":
        anomalies.append({"code": "EXECUTION_BOUNDARY_DRIFT", "severity": "critical"})

    critical = any(a["severity"] == "critical" for a in anomalies)
    pain = min(1.0, sum(0.7 if a["severity"] == "critical" else 0.35 for a in anomalies))
    return {
        "healthy": not anomalies,
        "critical": critical,
        "pain_level": round(pain, 2),
        "anomalies": anomalies,
        "protective_mode": critical,
    }


def doctor_trace(assessment: dict) -> dict:
    """نگاشت content-free به قرارداد Doctor.mine؛ هیچ دادهٔ مشتری عبور نمی‌کند."""
    anomalies = assessment.get("anomalies") or []
    sigma_risk = any(a.get("code") == "SIGMA_CANCER_RISK" for a in anomalies)
    return {
        "errors_24h": len(anomalies),
        "effects_pending": 0,
        "frozen": bool(assessment.get("protective_mode")),
        "sigma_effective": 1.01 if sigma_risk else 0.0,
        "ziman_codes": [a.get("code") for a in anomalies],
        "scope": "ZIMAN",
    }


def collect_neural_snapshot(beat: int, status: dict, heart: dict,
                            assessment: dict, doctor_result: dict | None = None) -> dict:
    """زیمان را به SignalHub (نخاع) وصل می‌کند؛ snapshot فقط advisory است."""
    snap = _HUB.collect(
        beat=int(beat or 0),
        rhythm={"period_s": heart.get("period_s"), "authority": "heart"},
        sensory={
            "leg_id": status.get("leg_id", "ziman-gallery"),
            "organ": "ZIMAN",
            "drafts_count": int(status.get("drafts_count") or 0),
            "inventory_known": status.get("inventory_hint") is not None,
        },
        spectral={"sigma": heart.get("sigma_now")},
        budget={"money_link": status.get("money_link")},
        doctor=doctor_result or {"status": "not_due"},
        pain_level=float(assessment.get("pain_level") or 0.0),
    )
    return snap.to_dict()


def biology_beat(ziman_leg, beat: int = 0, doctor=None,
                 doctor_every_n: int = 1440) -> dict | None:
    """ضربان ترکیبی Ziman.

    Doctor فقط وقتی anomaly هست و cadence سررسیده اجرا می‌شود. اگر doctor تزریق نشده
    باشد، فقط trace تولید می‌شود (هیچ Doctor خودسرانه ساخته نمی‌شود).
    """
    if ziman_leg is None:
        return None
    if opslib.STOP_ORGANISM.exists() or opslib.halted():
        return {"schema": SCHEMA, "halted": True, "reason": "STOP", "beat": beat}

    status = ziman_leg.status_snapshot()
    heart = heart_readmodel()
    assessment = health_assessment(status, heart)
    due = bool(assessment["anomalies"]) and (
        doctor_every_n <= 0 or beat <= 0 or beat % doctor_every_n == 0
    )
    doctor_result = None
    if due and doctor is not None:
        try:
            doctor_result = doctor.run_cycle(beat=int(beat or 0), trace=doctor_trace(assessment))
        except Exception as exc:  # noqa: BLE001 — Doctor نباید limb را بکشد
            doctor_result = {"status": "failed-soft", "error_type": type(exc).__name__}

    neural = collect_neural_snapshot(beat, status, heart, assessment, doctor_result)
    return {
        "schema": SCHEMA,
        "beat": int(beat or 0),
        "organ": "ZIMAN",
        "heart": heart,
        "nerves": {
            "connected": True,
            "advisory_only": neural.get("advisory_only") is True,
            "pain_level": neural.get("pain_level"),
        },
        "doctor": {
            "due": due,
            "connected": doctor is not None,
            "result": doctor_result,
            "auto_merge": False,
            "human_append_required": True,
        },
        "assessment": assessment,
        "propose_only": True,
        "outward_execution": False,
        "ziman_can_write_heart": False,
    }
