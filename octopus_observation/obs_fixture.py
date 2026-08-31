#!/usr/bin/env python3
"""Versioned claim fixture for the fixture-only observatory pipeline (W-C).

Design contract (owner decision Q5=A, 2026-08-30):
- deterministic: identical inputs produce byte-identical fixtures (seeded RNG,
  fixed epoch, no wall clock);
- producers may consume any field EXCEPT ``outcome`` (outcome-blindness is
  verified by the verifier's outcome-flip probe);
- unresolved claims carry ``resolved_at=None`` / ``outcome=None`` and are
  excluded from scoring explicitly, never silently;
- missing-data policy: a claim without ``observed_at`` is rejected at build
  time (fail closed);
- duplicate claim IDs are rejected at build time;
- tamper detection: ``provenance_hash`` is the SHA-256 of the canonical JSON
  of all claims (predictions excluded).
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone

FIXTURE_VERSION = "obs-fixture/1"
EPOCH = datetime(2026, 8, 30, 0, 0, 0, tzinfo=timezone.utc)


class FixtureError(ValueError):
    """Malformed or tampered fixture input."""


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    observed_at: str          # ISO-8601 UTC; mandatory
    resolved_at: str | None   # ISO-8601 UTC or None (unresolved)
    outcome: int | None       # 0/1 after resolution; None while unresolved
    feature_a: float          # pre-resolution context only
    feature_b: float
    fixture_version: str = FIXTURE_VERSION


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_claims_json(claims: list[ClaimRecord]) -> str:
    return json.dumps([asdict(c) for c in claims], sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)


def provenance_hash(claims: list[ClaimRecord]) -> str:
    return hashlib.sha256(canonical_claims_json(claims).encode("utf-8")).hexdigest()


def build_fixture(n: int = 40, seed: int = 20260830,
                  unresolved: int = 5, version: str = FIXTURE_VERSION
                  ) -> list[ClaimRecord]:
    """Deterministic claim fixture. ``unresolved`` claims stay unresolved."""
    if n < 1:
        raise FixtureError("n must be >= 1")
    if not 0 <= unresolved <= n:
        raise FixtureError("unresolved must be within [0, n]")
    rng = random.Random(seed)
    claims: list[ClaimRecord] = []
    for i in range(n):
        observed = EPOCH + timedelta(hours=i)
        fa = round(rng.random(), 6)
        fb = round(rng.random(), 6)
        if i >= n - unresolved:
            resolved_at, outcome = None, None
        else:
            resolved_at = _iso(observed + timedelta(hours=1 + rng.randrange(1, 24)))
            # Outcome is drawn from the seeded stream only; producers never see it.
            outcome = int(rng.random() < 0.25 + 0.5 * fa)
        claims.append(ClaimRecord(
            claim_id=f"claim-{i:04d}",
            observed_at=_iso(observed),
            resolved_at=resolved_at,
            outcome=outcome,
            feature_a=fa,
            feature_b=fb,
            fixture_version=version,
        ))
    _validate(claims)
    return claims


def _validate(claims: list[ClaimRecord]) -> None:
    seen: set[str] = set()
    for c in claims:
        if not c.claim_id:
            raise FixtureError("empty claim_id")
        if c.claim_id in seen:
            raise FixtureError(f"duplicate claim_id: {c.claim_id}")
        seen.add(c.claim_id)
        if not c.observed_at:
            raise FixtureError(f"missing observed_at for {c.claim_id}")
        if (c.resolved_at is None) != (c.outcome is None):
            raise FixtureError(
                f"unresolved policy violation for {c.claim_id}: "
                "resolved_at and outcome must be both set or both None")
        if c.outcome is not None and c.outcome not in (0, 1):
            raise FixtureError(f"outcome not binary for {c.claim_id}")
        if c.resolved_at is not None and c.resolved_at <= c.observed_at:
            raise FixtureError(
                f"future-data violation for {c.claim_id}: "
                "resolved_at must be after observed_at")


def load_claims(payload: list[dict], expected_provenance: str | None = None
                ) -> list[ClaimRecord]:
    """Rehydrate + validate claims; optional provenance (tamper) check."""
    claims = [ClaimRecord(**d) for d in payload]
    _validate(claims)
    if expected_provenance is not None:
        actual = provenance_hash(claims)
        if actual != expected_provenance:
            raise FixtureError(
                f"fixture tampered: provenance hash mismatch "
                f"(expected {expected_provenance[:12]}..., got {actual[:12]}...)")
    return claims
