"""claim.v1 <-> ClaimRecord adapter (S2b lane A, F3/F11).

ClaimRecord (obs_fixture.py, owner decision Q5=A) is canonical; claim.v1 is a
serialization/transport shape reached only through this module (S6-D02).

Rules this adapter owns:
- feature_a / feature_b are required keyword arguments. The adapter never
  invents them — no default 0.5, no random fill. A caller without features
  gets ObservationContractError("claim-missing-features") (F3).
- timestamps cross the boundary in exactly one canonical form,
  %Y-%m-%dT%H:%M:%SZ: parse via parse_utc, re-emit via _canonical (F11), so
  the string comparison in ClaimRecord._validate is chronology-safe.
- both directions run the destination side's own validation; FixtureError
  from the ClaimRecord side is re-raised as ObservationContractError so both
  paths reject with the same error class.

Forbidden here by contract: importing scorer, producer_strategy,
producer_persistence or fixture_run. Lane C pins this statically.
"""
from __future__ import annotations

from .claim_record import SCHEMA, ClaimV1
from .observation_record import ObservationContractError, parse_utc
from .obs_fixture import ClaimRecord, FixtureError, _validate


def _canonical(value: str, *, field_name: str) -> str:
    dt = parse_utc(value, field_name=field_name)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def claim_v1_to_record(claim: ClaimV1, *,
                       feature_a: float | None = None,
                       feature_b: float | None = None) -> ClaimRecord:
    """Serialize a ClaimV1 row into the canonical ClaimRecord."""
    if feature_a is None or feature_b is None:
        raise ObservationContractError("claim-missing-features")
    claim.validate()
    record = ClaimRecord(
        claim_id=claim.claim_id,
        observed_at=_canonical(claim.observed_at, field_name="observed_at"),
        resolved_at=(None if claim.resolved_at is None else
                     _canonical(claim.resolved_at, field_name="resolved_at")),
        outcome=(None if claim.outcome is None else int(claim.outcome)),
        feature_a=float(feature_a),
        feature_b=float(feature_b),
    )
    try:
        _validate([record])
    except FixtureError as exc:
        raise ObservationContractError(str(exc)) from exc
    return record


def record_to_claim_v1(record: ClaimRecord, *,
                       predicted_p: float | None = None) -> ClaimV1:
    """Re-emit a canonical ClaimRecord as a claim.v1 serialization row."""
    try:
        _validate([record])
    except FixtureError as exc:
        raise ObservationContractError(str(exc)) from exc
    claim = ClaimV1(
        schema=SCHEMA,
        claim_id=record.claim_id,
        observed_at=_canonical(record.observed_at, field_name="observed_at"),
        resolved_at=(None if record.resolved_at is None else
                     _canonical(record.resolved_at, field_name="resolved_at")),
        predicted_p=predicted_p,
        outcome=(None if record.outcome is None else int(record.outcome)),
    )
    claim.validate()
    return claim
