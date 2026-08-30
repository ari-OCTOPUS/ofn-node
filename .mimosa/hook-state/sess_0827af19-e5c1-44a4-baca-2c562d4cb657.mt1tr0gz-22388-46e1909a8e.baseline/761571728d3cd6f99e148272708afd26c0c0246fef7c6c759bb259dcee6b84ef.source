#!/usr/bin/env python3
"""b3_bridge.py — B3: Box output → Doctor.submit_for_approval (propose-only).

DOCTOR-BOX-OF-AGENTS-SPEC Part 8·B3: «خروجیِ جعبه → doctor.submit_for_approval
(propose-only). تست: صفر production-touch؛ هیچ merge بدونِ human-append.»

این bridge فقط خروجیِ Box را به فرمتِ RFCِ Doctor تبدیل می‌کند و submit می‌زند.
هیچ دسترسیِ مستقیم به production — فقط از Doctor's propose-only path.

هیچ import از *_gate/chrono/money. $0 آفلاین.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BoxInsight:
    """یک insight از Box که به RFC تبدیل می‌شود."""
    bottleneck: str
    fix: str
    expected_lift: str
    confidence: float = 0.5
    measured_lift_score: float = 0.0
    tournament_elo: float = 1000.0
    source: str = "box"


def box_insight_to_rfc_payload(insight: BoxInsight) -> dict:
    """تبدیلِ BoxInsight → payload برای Doctor.propose_rfc.
    propose-only: فقط داده، نه اثر."""
    return {
        "bottleneck": insight.bottleneck,
        "evidence": {"key": "box-insight", "severity": "high" if insight.confidence > 0.6 else "medium",
                     "source": "box-of-agents",
                     "confidence": insight.confidence,
                     "measured_lift": insight.measured_lift_score,
                     "tournament_elo": insight.tournament_elo},
        "fix": insight.fix,
        "expected_lift": insight.expected_lift,
    }


def submit_box_insight(doctor: Any, insight: BoxInsight) -> dict:
    """Box insight → Doctor.propose_rfc → submit_for_approval.
    خروجی: {submitted, rfc_id, status}. هیچ merge — فقط propose.
    اگر doctor نباشد → {submitted: False}."""
    if doctor is None:
        return {"submitted": False, "reason": "no doctor instance"}
    payload = box_insight_to_rfc_payload(insight)
    # ساختِ RFC از طریقِ Doctor's normal path
    bottleneck_dict = {"bottleneck": payload["bottleneck"],
                       "evidence": payload["evidence"]}
    try:
        rfc = doctor.propose_rfc(bottleneck_dict, fix=payload["fix"],
                                 expected_lift=payload["expected_lift"],
                                 rollback="revert flag")
        # sandbox + critic (propose-only)
        doctor.run_sandbox(rfc)
        # submit (human-append gate)
        submitted = doctor.submit_for_approval(rfc)
        return {"submitted": submitted, "rfc_id": rfc.rfc_id,
                "status": rfc.status, "propose_only": True}
    except Exception as e:  # noqa: BLE001 — fail-closed
        return {"submitted": False, "error": str(e)[:200]}


def box_to_doctor_pipeline(box_metrics: dict, doctor: Any) -> list[dict]:
    """Pipeline: از metricsِ Box، insights استخراج کن → submit.
    فعلاً stub: اگر Box یک bottleneck شناسایی کرد → submit.
    خروجی: list of submit results."""
    results = []
    # اگر Box یک bottleneck دارد (از G_t یا flagged)
    bottlenecks = box_metrics.get("bottlenecks") or []
    for bn in bottlenecks:
        insight = BoxInsight(
            bottleneck=bn.get("description", "box-detected"),
            fix=bn.get("suggested_fix", "review needed"),
            expected_lift=bn.get("expected_lift", "improvement"),
            confidence=bn.get("confidence", 0.5))
        results.append(submit_box_insight(doctor, insight))
    return results
