"""Versioned claim.v1 record: observed_at and resolved_at only.

Fixture successor piece 1. Does not recover evidence.db.
Does not set official n. Does not score Brier.
JSON only — does not load YAML (R-05 stays out of this path).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .observation_record import ObservationContractError, parse_utc

SCHEMA = "claim.v1"


@dataclass(frozen=True)
class ClaimV1:
    schema: str
    claim_id: str
    observed_at: str
    resolved_at: str | None
    predicted_p: float | None
    outcome: bool | None

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ObservationContractError(f"claim-schema-invalid:{self.schema}")
        if not str(self.claim_id or "").strip():
            raise ObservationContractError("claim-id-blank")
        observed = parse_utc(self.observed_at, field_name="observed_at")
        if self.resolved_at is None:
            if self.outcome is not None:
                raise ObservationContractError("unresolved-cannot-have-outcome")
            return
        resolved = parse_utc(self.resolved_at, field_name="resolved_at")
        if resolved < observed:
            raise ObservationContractError("resolved-before-observed")
        if self.outcome is None:
            raise ObservationContractError("resolved-missing-outcome")
        if self.predicted_p is not None:
            if not isinstance(self.predicted_p, (int, float)) or isinstance(self.predicted_p, bool):
                raise ObservationContractError("predicted-p-not-number")
            if not 0.0 <= float(self.predicted_p) <= 1.0:
                raise ObservationContractError("predicted-p-out-of-range")

    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "claim_id": self.claim_id,
            "observed_at": self.observed_at,
            "resolved_at": self.resolved_at,
            "predicted_p": self.predicted_p,
            "outcome": self.outcome,
        }


def claim_from_mapping(data: Mapping[str, Any]) -> ClaimV1:
    if not isinstance(data, Mapping):
        raise ObservationContractError("claim-not-object")
    outcome = data.get("outcome")
    if outcome is not None and not isinstance(outcome, bool):
        raise ObservationContractError("outcome-not-bool")
    record = ClaimV1(
        schema=str(data.get("schema", SCHEMA)),
        claim_id=str(data.get("claim_id", "")),
        observed_at=str(data.get("observed_at", "")),
        resolved_at=None if data.get("resolved_at") in (None, "") else str(data.get("resolved_at")),
        predicted_p=data.get("predicted_p"),
        outcome=outcome,
    )
    record.validate()
    return record
