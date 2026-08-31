"""Versioned claim.v1 record: observed_at and resolved_at only.

Fixture successor piece 1. Does not recover evidence.db.
Does not set official n. Does not score Brier.
JSON only — does not load YAML (R-05 stays out of this path).

Owner rulings S2b (2026-09-01), see docs/octopus-surgery/DECISIONS.md S6-D02/03:
- outcome is int in {0,1}. bool is accepted on input and normalized;
  bool is re-emitted only via to_legacy_dict() when a caller asks for
  legacy JSON (Q3).
- time is strict: resolved_at <= observed_at is a future-data violation
  on this path too, matching ClaimRecord._validate (Q2).
- predicted_p is DEPRECATED as a claim-row field (S6-D03): it is validated
  here — on unresolved rows as well, before the resolved/unresolved branch
  (F9) — until piece 3 moves it to a separate prediction record.
- schema must be present; a missing schema is rejected, never defaulted (F10).
"""
from __future__ import annotations

import json
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
    outcome: int | None

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ObservationContractError(f"claim-schema-invalid:{self.schema}")
        if not str(self.claim_id or "").strip():
            raise ObservationContractError("claim-id-blank")
        # F9: predicted_p is validated BEFORE the resolved/unresolved branch,
        # so an invalid value on an unresolved row cannot slip through.
        if self.predicted_p is not None:
            if not isinstance(self.predicted_p, (int, float)) or isinstance(self.predicted_p, bool):
                raise ObservationContractError("predicted-p-not-number")
            if not 0.0 <= float(self.predicted_p) <= 1.0:
                raise ObservationContractError("predicted-p-out-of-range")
        observed = parse_utc(self.observed_at, field_name="observed_at")
        if self.resolved_at is None:
            if self.outcome is not None:
                raise ObservationContractError("unresolved-cannot-have-outcome")
            return
        resolved = parse_utc(self.resolved_at, field_name="resolved_at")
        # Q2 strict: equal timestamps are future-data on both paths.
        if resolved <= observed:
            raise ObservationContractError("future-data-violation")
        if self.outcome is None:
            raise ObservationContractError("resolved-missing-outcome")
        if self.outcome not in (0, 1):
            raise ObservationContractError("outcome-not-binary")

    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def to_dict(self) -> dict[str, Any]:
        """Canonical dict: outcome is int in {0,1} (Q3)."""
        return {
            "schema": self.schema,
            "claim_id": self.claim_id,
            "observed_at": self.observed_at,
            "resolved_at": self.resolved_at,
            "predicted_p": self.predicted_p,
            "outcome": self.outcome,
        }

    def to_legacy_dict(self) -> dict[str, Any]:
        """Legacy JSON shape: outcome re-emitted as bool, only on request."""
        out = self.to_dict()
        if out["outcome"] is not None:
            out["outcome"] = bool(out["outcome"])
        return out


def claim_from_mapping(data: Mapping[str, Any]) -> ClaimV1:
    if not isinstance(data, Mapping):
        raise ObservationContractError("claim-not-object")
    # F10: a missing schema is never silently defaulted.
    if "schema" not in data:
        raise ObservationContractError("claim-schema-missing")
    raw_outcome = data.get("outcome")
    if raw_outcome is None:
        outcome = None
    elif isinstance(raw_outcome, bool):          # Q3: bool accepted...
        outcome = int(raw_outcome)
    elif isinstance(raw_outcome, int) and raw_outcome in (0, 1):
        outcome = raw_outcome
    else:                                        # ...anything else rejected (F2)
        raise ObservationContractError("outcome-not-binary")
    record = ClaimV1(
        schema=str(data["schema"]),
        claim_id=str(data.get("claim_id", "")),
        observed_at=str(data.get("observed_at", "")),
        resolved_at=None if data.get("resolved_at") in (None, "") else str(data.get("resolved_at")),
        predicted_p=data.get("predicted_p"),
        outcome=outcome,
    )
    record.validate()
    return record


def claim_to_legacy_json(claim: ClaimV1) -> str:
    """Legacy wire form: sorted keys, bool outcome. Opt-in only (Q3)."""
    return json.dumps(claim.to_legacy_dict(), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
