#!/usr/bin/env python3
"""Persistence producer (W-C). Outcome-blind by construction.

Distinct algorithm and distinct object from the strategy producer; MUST NOT
import the strategy producer (enforced statically by the verifier).
"""
from __future__ import annotations

from octopus_observation.obs_fixture import ClaimRecord

PERSISTENCE_VERSION = "persistence-producer/1"


def predict(claim: ClaimRecord) -> dict:
    """Shrinkage-toward-base-rate probability from pre-resolution context."""
    # James-Stein-flavoured shrinkage of feature_b toward the 0.5 base rate.
    p = 0.5 + 0.35 * (claim.feature_b - 0.5)
    p = min(0.95, max(0.05, p))
    return {
        "producer": PERSISTENCE_VERSION,
        "claim_id": claim.claim_id,
        "prediction": round(p, 6),
        "as_of": claim.observed_at,
    }
