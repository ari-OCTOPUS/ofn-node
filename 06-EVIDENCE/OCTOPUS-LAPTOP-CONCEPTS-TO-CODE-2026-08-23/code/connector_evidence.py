"""Connector Evidence Record rules (ADR-LAPTOP-AGENT-DECISIONS-2026-08-22).

Extends organism evidence plane with connector-facing fields required for
Similarweb/estimate and CONNECTOR-GAP discipline.

Prefer this module for connector outputs. Existing modules:
- _ops/shadow_homeostasis/evidence_store.py (lab observation JSONL)
- _ops/epistemics/schemas.py EvidenceLink (claim links; no estimate/valid_for)
- _ops/evidence_plane/* (capability registry / events)

Rule: missing evidence_id OR invalid source_type -> unverified=True.
Estimates require confidence + valid_for.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable
import hashlib
import re

SCHEMA = "octopus-connector-evidence.v1"
VALID_SOURCE_TYPES = frozenset({
    "runtime",
    "connector_result",
    "owner_statement",
    "file_line",
    "command_output",
    "test_artifact",
    "derived",
    "manifest",
    "owner-brief",
    "unknown",
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def is_valid_source_type(source_type: Any) -> bool:
    if not isinstance(source_type, str):
        return False
    st = source_type.strip()
    return bool(st) and st in VALID_SOURCE_TYPES


def is_valid_evidence_id(evidence_id: Any) -> bool:
    if not isinstance(evidence_id, str):
        return False
    eid = evidence_id.strip()
    if not eid:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_.:/-]{8,200}", eid))


def compute_evidence_id(*parts: str) -> str:
    raw = "||".join(str(p) for p in parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_record(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize a connector/evidence datum and apply unverified rule."""
    data = dict(raw or {})
    evidence_id = data.get("evidence_id")
    source_type = data.get("source_type")

    missing_id = not is_valid_evidence_id(evidence_id)
    invalid_st = not is_valid_source_type(source_type)
    unverified = bool(missing_id or invalid_st)

    estimate = data.get("estimate")
    is_estimate = bool(data.get("is_estimate")) or estimate is not None or data.get("label") == "estimate"

    confidence = data.get("confidence")
    valid_for = data.get("valid_for")

    out = {
        "schema": SCHEMA,
        "evidence_id": evidence_id if not missing_id else None,
        "source_type": source_type if not invalid_st else None,
        "captured_at": data.get("captured_at") or _now_iso(),
        "label": data.get("label"),
        "estimate": estimate,
        "is_estimate": is_estimate,
        "confidence": confidence,
        "valid_for": valid_for,
        "value": data.get("value"),
        "scope": data.get("scope"),
        "source_ref": data.get("source_ref"),
        "unverified": unverified,
        "unverified_reasons": [],
    }
    if missing_id:
        out["unverified_reasons"].append("missing_or_invalid_evidence_id")
    if invalid_st:
        out["unverified_reasons"].append("missing_or_invalid_source_type")
    if is_estimate:
        if confidence is None:
            out["unverified"] = True
            out["unverified_reasons"].append("estimate_missing_confidence")
        if not valid_for:
            out["unverified"] = True
            out["unverified_reasons"].append("estimate_missing_valid_for")
    return out


def validate_batch(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_record(r) for r in records]
    return {
        "schema": SCHEMA + ".batch",
        "count": len(normalized),
        "unverified_count": sum(1 for r in normalized if r["unverified"]),
        "records": normalized,
    }
