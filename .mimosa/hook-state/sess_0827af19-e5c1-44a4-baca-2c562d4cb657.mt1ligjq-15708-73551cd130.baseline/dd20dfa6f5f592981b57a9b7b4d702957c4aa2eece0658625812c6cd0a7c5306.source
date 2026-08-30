# -*- coding: utf-8 -*-
"""هستهٔ ریاضیِ وتر — فاصلهٔ اقلیدسیِ وزن‌دارِ نرمال‌شده. Pure و deterministic.

d(x, x*) = sqrt( Σ_i w_i (x_i - x*_i)^2 / Σ_i w_i )
چون همهٔ ابعاد در [0,1]اند، d هم در [0,1] است و بینِ missionها قابلِ‌مقایسه.
"""
from __future__ import annotations

import math

from .schemas import StateVector, clamp01


def weighted_distance(vec: StateVector) -> float:
    """فاصلهٔ کل. بردارِ نامعتبر → ValueError (نه حدسِ بی‌صدا)."""
    errs = vec.validate()
    if errs:
        raise ValueError("invalid StateVector: " + "; ".join(errs))
    wsum = sum(float(vec.weights[d]) for d in vec.dimensions)
    if wsum <= 0:
        raise ValueError("all-zero weights — distance undefined")
    acc = 0.0
    for d in vec.dimensions:
        gap = clamp01(vec.values[d]) - clamp01(vec.targets[d])
        acc += float(vec.weights[d]) * gap * gap
    return math.sqrt(acc / wsum)


def component_gaps(vec: StateVector) -> dict:
    """سهمِ هر بُعد: {dim: {gap, weighted}} — برای «کجا می‌لنگد» در کارت/گزارش."""
    errs = vec.validate()
    if errs:
        raise ValueError("invalid StateVector: " + "; ".join(errs))
    out = {}
    for d in vec.dimensions:
        gap = clamp01(vec.values[d]) - clamp01(vec.targets[d])
        out[d] = {"gap": round(gap, 4),
                  "weighted": round(float(vec.weights[d]) * gap * gap, 4)}
    return out


def top_gaps(vec: StateVector, n: int = 3) -> list:
    """nتا بُعدِ پرشکاف — مرتب بر اساسِ سهمِ وزن‌دار."""
    gaps = component_gaps(vec)
    return sorted(gaps.items(), key=lambda kv: kv[1]["weighted"], reverse=True)[:n]
