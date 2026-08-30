#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spectral_definitions.py -- Single-source versioned spectral formula definitions.

Provides pure functions with version/formula IDs for:
  - Legacy sigma: min(lambda_max / (lambda_2 + eps), 10)
  - connectivity_ratio_v2: lambda_2 / (lambda_max + eps), bounded [0, 1]

All functions return None for empty, tiny, non-finite, disconnected, or
otherwise meaningless inputs -- never fake 0.0.

No side effects, no graph construction, no numpy/networkx required.
"""
from __future__ import annotations

from math import isfinite

# ---------------------------------------------------------------------------
# Formula identifiers (for telemetry attributes / documentation)
# ---------------------------------------------------------------------------

FORMULA_LEGACY_SIGMA = "legacy_sigma.v1"
"""Original heuristic: sigma = min(lambda_max / (lambda_2 + eps), 10)."""

FORMULA_CONNECTIVITY_RATIO_V2 = "connectivity_ratio_v2.v1"
"""Algebraic connectivity ratio: lambda_2 / (lambda_max + eps), bounded [0, 1]."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_pair(lambda_2: float | None, lambda_max: float | None) -> bool:
    """Return True only when both values are finite and lambda_max > 0."""
    if lambda_2 is None or lambda_max is None:
        return False
    if not (isfinite(lambda_2) and isfinite(lambda_max)):
        return False
    if lambda_max <= 0.0:
        return False
    return True


# ---------------------------------------------------------------------------
# Legacy sigma (unchanged public contract)
# ---------------------------------------------------------------------------

LEGACY_SIGMA_CAP = 10.0
"""Upper bound for legacy sigma -- preserve existing consumer expectations."""

LEGACY_EPS = 1e-6
"""Epsilon تاریخیِ ``doctor/spectral.py``؛ تغییرش خروجی live را عوض می‌کند."""


def compute_legacy_sigma(
    lambda_2: float | None,
    lambda_max: float | None,
    *,
    eps: float = LEGACY_EPS,
    cap: float = LEGACY_SIGMA_CAP,
) -> float | None:
    """Compute the legacy sigma heuristic.

    Formula (FORMULA_LEGACY_SIGMA):
        sigma = min(lambda_max / (lambda_2 + eps), cap)

    Returns None when the input pair is not valid (non-finite, None,
    lambda_max <= 0, or lambda_2 so small that sigma would be purely
    degenerate).  The caller decides what UNKNOWN means in context.
    """
    if not _valid_pair(lambda_2, lambda_max):
        return None
    # If lambda_2 is extremely close to zero the graph is effectively
    # disconnected -- sigma would blow up to cap which is meaningless.
    if abs(float(lambda_2)) < eps:
        return None
    return min(float(lambda_max) / (float(lambda_2) + eps), cap)


# ---------------------------------------------------------------------------
# connectivity_ratio_v2
# ---------------------------------------------------------------------------

CONNECTIVITY_RATIO_V2_EPS = 1e-9
"""Epsilon used in connectivity_ratio_v2 denominator."""


def compute_connectivity_ratio_v2(
    lambda_2: float | None,
    lambda_max: float | None,
    *,
    eps: float = CONNECTIVITY_RATIO_V2_EPS,
) -> float | None:
    """Compute connectivity_ratio_v2 -- a bounded algebraic connectivity ratio.

    Formula (FORMULA_CONNECTIVITY_RATIO_V2):
        ratio = clamp(lambda_2 / (lambda_max + eps), 0, 1)

    Returns None when inputs are not valid or lambda_2≈0 (disconnected/tiny graph).
    """
    if not _valid_pair(lambda_2, lambda_max):
        return None
    if abs(float(lambda_2)) < eps:
        return None
    ratio = float(lambda_2) / (float(lambda_max) + eps)
    # Clamp to [0, 1]
    if ratio < 0.0:
        ratio = 0.0
    elif ratio > 1.0:
        ratio = 1.0
    return ratio
