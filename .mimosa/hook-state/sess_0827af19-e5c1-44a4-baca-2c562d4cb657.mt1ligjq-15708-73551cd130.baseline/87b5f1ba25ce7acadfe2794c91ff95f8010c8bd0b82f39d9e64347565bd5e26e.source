#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ratio_model.py — C13 (مگا‌دستور #۱۷): مدل کمی starvation با margin صریح.

Pure function · بدون I/O · property-testable.
counterfactual 0.50 باید BORDERLINE باشد نه HEALTHY — epsilon صریح."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EPSILON = 0.05  # حاشیهٔ صریح — برابر با threshold یعنی BORDERLINE نه HEALTHY
DEFAULT_THRESHOLD = 0.5


@dataclass(frozen=True)
class SourceState:
    name: str
    rate: float              # events per minute
    reader_ok: bool          # آیا reader این منبع را می‌خواند؟
    freshness: float = 1.0   # 0..1 (1=فرش، 0=کاملاً کهنه)
    quality: float = 1.0     # 0..1 (1=CLEAN، 0=SECRET_SUSPECTED)
    weight: float = 1.0      # وزن نسبی منبع


@dataclass
class RatioBreakdown:
    total_ratio: float
    source_contributions: dict[str, float]
    missing_penalty: float
    stale_penalty: float
    reader_failure_penalty: float
    quality_penalty: float
    threshold: float
    margin: float            # total_ratio - threshold
    verdict: str             # HEALTHY | BORDERLINE | STARVED


def afferent_ratio(source_states: list[SourceState],
                   threshold: float = DEFAULT_THRESHOLD,
                   epsilon: float = EPSILON) -> RatioBreakdown:
    """محاسبهٔ ratio با تفکیک penaltyها. Pure — بدون side effect."""
    if not source_states:
        return RatioBreakdown(
            total_ratio=0.0, source_contributions={}, missing_penalty=1.0,
            stale_penalty=0.0, reader_failure_penalty=0.0, quality_penalty=0.0,
            threshold=threshold, margin=-threshold, verdict="STARVED")

    contributions: dict[str, float] = {}
    missing_pen = stale_pen = reader_pen = quality_pen = 0.0
    # وزن فقط بین منابع خوانده‌شده نرمال شود — غیرخوانده‌ها رقیق نمی‌کنند
    readable = [s for s in source_states if s.reader_ok]
    total_weight = sum(s.weight for s in readable) if readable else 1.0

    for s in source_states:
        base = s.rate * s.weight / max(total_weight, 1e-12)
        if not s.reader_ok:
            reader_pen += base
            contributions[s.name] = 0.0
            continue
        stale_factor = 1.0 - s.freshness
        stale_pen += base * stale_factor
        quality_factor = 1.0 - s.quality
        quality_pen += base * quality_factor
        contributions[s.name] = base * s.freshness * s.quality

    # saturation: ratio ∈ [0, 1] — منابع بیشتر نرخ فزاینده می‌دهند
    total_signal = sum(contributions.values())
    total_ratio = total_signal / (total_signal + _saturation_constant(source_states))

    # missing penalty: منابعی که اصلاً داده ندارند (rate=0)
    zero_sources = sum(1 for s in source_states if s.rate == 0)
    missing_pen = zero_sources / len(source_states) if source_states else 0.0

    margin = total_ratio - threshold
    if total_ratio >= threshold + epsilon:
        verdict = "HEALTHY"
    elif abs(total_ratio - threshold) <= epsilon:
        verdict = "BORDERLINE"
    else:
        verdict = "STARVED"

    return RatioBreakdown(
        total_ratio=round(total_ratio, 4),
        source_contributions={k: round(v, 4) for k, v in contributions.items()},
        missing_penalty=round(missing_pen, 4),
        stale_penalty=round(stale_pen, 4),
        reader_failure_penalty=round(reader_pen, 4),
        quality_penalty=round(quality_pen, 4),
        threshold=threshold,
        margin=round(margin, 4),
        verdict=verdict)


def _saturation_constant(sources: list[SourceState]) -> float:
    """نقطهٔ اشباع: بیشتر منابع فعال → اشباع کمتر → ratio بالاتر.
    10/active: با ۲ منبع فعال، scenario counterfactual (signal=5) → ratio≈0.50=BORDERLINE."""
    active = sum(1 for s in sources if s.reader_ok and s.rate > 0)
    return max(1.0, 10.0 / max(active, 1))
