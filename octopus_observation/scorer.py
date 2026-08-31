#!/usr/bin/env python3
"""Independent scorer (W-C).

Imports NEITHER producer (enforced statically by the verifier): predictions
arrive as plain (claim_id, prediction, outcome) tuples. Produces Brier score,
per-claim contributions, resolved sample size, unresolved exclusion count and
a normal-approximation 95% confidence interval. Makes no superiority claim.
"""
from __future__ import annotations

import math

Z95 = 1.959963984540054


def brier(contributions: list[float]) -> dict:
    """Aggregate Brier metrics for one producer's contributions."""
    n = len(contributions)
    if n == 0:
        return {"n": 0, "brier": None, "ci95": None, "method": "normal-approx"}
    mean = sum(contributions) / n
    if n > 1:
        var = sum((c - mean) ** 2 for c in contributions) / (n - 1)
        half = Z95 * math.sqrt(var / n)
    else:
        half = 0.0
    return {
        "n": n,
        "brier": round(mean, 6),
        "ci95": [round(max(0.0, mean - half), 6), round(mean + half, 6)],
        "method": "normal-approx",
    }


def score(pairs: list[tuple[str, float, int | None]]) -> dict:
    """``pairs``: (claim_id, prediction, outcome).

    Unresolved claims (outcome None) are excluded explicitly and counted.
    """
    contributions: list[float] = []
    unresolved = 0
    per_claim: dict[str, float] = {}
    for claim_id, prediction, outcome in pairs:
        if outcome is None:
            unresolved += 1
            continue
        if not 0.0 <= prediction <= 1.0:
            raise ValueError(f"prediction out of range for {claim_id}: {prediction}")
        contribution = (prediction - outcome) ** 2
        contributions.append(contribution)
        per_claim[claim_id] = round(contribution, 6)
    return {
        **brier(contributions),
        "unresolved_excluded": unresolved,
        "per_claim": per_claim,
    }
