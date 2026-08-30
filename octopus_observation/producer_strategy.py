#!/usr/bin/env python3
"""Strategy producer (W-C). Outcome-blind by construction.

May import the fixture data model but MUST NOT import the persistence
producer (enforced statically by the verifier). Reads only pre-resolution
fields: claim_id, observed_at, feature_a, feature_b, fixture_version.
"""
from __future__ import annotations

import hashlib

from octopus_observation.obs_fixture import ClaimRecord

STRATEGY_VERSION = "strategy-producer/1"


def predict(claim: ClaimRecord) -> dict:
    """Deterministic probability from pre-resolution context only."""
    key = hashlib.sha256(
        f"{STRATEGY_VERSION}|{claim.claim_id}|{claim.feature_a:.6f}".encode()
    ).hexdigest()
    spread = (int(key[:8], 16) % 1000) / 1000.0        # [0,1)
    p = 0.25 + 0.5 * claim.feature_a + 0.05 * (spread - 0.5)
    p = min(0.97, max(0.03, p))
    return {
        "producer": STRATEGY_VERSION,
        "claim_id": claim.claim_id,
        "prediction": round(p, 6),
        "as_of": claim.observed_at,
    }
