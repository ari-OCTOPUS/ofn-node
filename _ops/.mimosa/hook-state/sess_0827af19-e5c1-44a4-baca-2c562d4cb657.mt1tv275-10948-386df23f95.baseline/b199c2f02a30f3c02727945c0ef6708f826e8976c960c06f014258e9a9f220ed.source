#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pain_assessment.py — immutable PainAssessment (ADR-034 B).

Diagnostic/proposal only. Never sets organism protective_skip or executes halt.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class PainAssessment:
    pain: float | None
    status: str  # OK | UNKNOWN | PARTIAL
    components: dict[str, float]
    reason_codes: tuple[str, ...]
    evidence_level: str = "SHADOW"
    trace_id: str = ""
    learned_pressure: float | None = None
    proposal: str = "none"  # none | protective_proposal | throttle_proposal
    threshold: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_pain_assessment(
    *,
    pain_level: float | None,
    contributors: dict[str, float] | None = None,
    learned_pressure: float | None = None,
    threshold: float = 0.7,
    critical_reflex: bool = False,
    high_reflex: bool = False,
    apply_learned: bool = False,
) -> PainAssessment:
    """Build assessment. Threshold only selects proposal — never executes halt."""
    trace_id = f"pain-{uuid4().hex[:12]}"
    components = dict(contributors or {})

    if pain_level is None or not isfinite(float(pain_level)):
        return PainAssessment(
            pain=None,
            status="UNKNOWN",
            components=components,
            reason_codes=("nonfinite_pain",),
            trace_id=trace_id,
            learned_pressure=learned_pressure,
            proposal="none",
            threshold=threshold,
        )

    pain = float(pain_level)
    reasons: list[str] = []
    lp = learned_pressure
    if apply_learned and lp is not None and isfinite(float(lp)) and float(lp) > 0:
        # Record fold for shadow observability only — caller must not execute.
        pain = min(1.0, pain + float(lp) * 0.5)
        components["learned_pressure_fold"] = float(lp) * 0.5
        reasons.append("learned_pressure_shadow_fold")
    elif lp is not None:
        components["learned_pressure"] = float(lp)

    pain = max(0.0, min(1.0, pain))
    proposal = "none"
    if critical_reflex:
        proposal = "throttle_proposal"
        reasons.append("critical_reflex")
    elif pain > threshold:
        proposal = "protective_proposal"
        reasons.append("pain_above_threshold")
    elif high_reflex:
        proposal = "none"
        reasons.append("high_reflex_warn")

    status = "OK"
    return PainAssessment(
        pain=pain,
        status=status,
        components=components,
        reason_codes=tuple(reasons) or ("all_clear",),
        trace_id=trace_id,
        learned_pressure=lp,
        proposal=proposal,
        threshold=threshold,
    )
