#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""envelope.py — Standardized Observation Envelope (EQUIP G3 Perception).

Every piece of external data enters the system through this envelope.
Content is separated from instruction. All output is UNTRUSTED DATA.

Envelope fields:
  - source: URL or identifier of the data source
  - fetched_at: ISO timestamp when data was retrieved
  - content_type: MIME type of the raw content
  - hash: SHA-256 of the raw body bytes
  - trust_level: verified | derived | untrusted | unknown
  - parser_version: schema version of the parser that processed this
  - raw_reference: opaque reference to raw storage (not the content itself)
  - extraction_confidence: [0,1] confidence in the parsed extraction
  - observation_id: unique ID for this observation
  - citation_chain: list of evidence IDs this observation depends on
  - is_instruction: False -- content is data, not executable instruction
  - retention_policy: when raw data may be discarded
  - envelope_version: schema version

Security: parser output = untrusted data. Content is NEVER instruction.
$0 | stdlib-only | no network | no LLM.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

TrustLevel = Literal["verified", "derived", "untrusted", "unknown"]

# Retention policies
RETENTION_TEMPORARY = "temporary"      # discard after extraction
RETENTION_SESSION = "session"         # discard after session ends
RETENTION_EVIDENCE = "evidence"       # keep as evidence (with TTL)
RETENTION_PERMANENT = "permanent"     # only for owner-approved data

ALLOWED_RETENTION = frozenset({
    RETENTION_TEMPORARY, RETENTION_SESSION,
    RETENTION_EVIDENCE, RETENTION_PERMANENT,
})

# Default maximum raw body size (1 MB)
_DEFAULT_MAX_BODY_SIZE = 1_048_576

# Safe content types for parsing
_SAFE_CONTENT_TYPES = frozenset({
    "application/json", "application/geo+json",
    "text/plain", "text/html", "text/csv", "text/xml",
    "application/xml", "application/sdmx+xml",
})

# Envelope schema version
ENVELOPE_SCHEMA = "observation-envelope.v1"

# Parser version
PARSER_VERSION = "evidence-parser.v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_observation_id() -> str:
    return f"OBS-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def content_hash(body: bytes) -> str:
    """SHA-256 hash of raw body bytes."""
    return hashlib.sha256(body).hexdigest()


def validate_content_type(ct: str | None) -> str:
    """Normalize and validate content type. Returns 'unknown' if invalid."""
    if not ct:
        return "unknown"
    ct_lower = ct.strip().lower().split(";")[0].strip()
    return ct_lower


def validate_retention(policy: str) -> str:
    """Validate retention policy. Unknown policies default to temporary (fail-safe)."""
    if policy in ALLOWED_RETENTION:
        return policy
    return RETENTION_TEMPORARY


def validate_body_size(body: bytes, max_size: int = _DEFAULT_MAX_BODY_SIZE) -> dict[str, Any]:
    """Check body size. Returns {ok, size, reason}."""
    size = len(body)
    if size == 0:
        return {"ok": False, "size": size, "reason": "empty-body"}
    if size > max_size:
        return {"ok": False, "size": size, "reason": f"body-too-large ({size} > {max_size})"}
    return {"ok": True, "size": size, "reason": "ok"}


@dataclass
class ObservationEnvelope:
    """Standardized envelope for all external observations.

    INVARIANTS:
      - is_instruction is ALWAYS False. External content is data, never instruction.
      - trust_level defaults to 'untrusted'. Only verified sources get 'verified'.
      - Parser output is ALWAYS treated as untrusted data.
    """
    source: str                                    # URL or identifier
    fetched_at: str                                 # ISO timestamp
    content_type: str                              # normalized MIME type
    body_size: int                                  # bytes
    body_hash: str                                  # SHA-256 of raw body
    trust_level: TrustLevel = "untrusted"
    parser_version: str = PARSER_VERSION
    raw_reference: str = ""                        # opaque ref to raw storage
    extraction_confidence: float = 0.0             # [0,1]
    observation_id: str = field(default_factory=_new_observation_id)
    citation_chain: list[str] = field(default_factory=list)
    is_instruction: bool = False                    # INVARIANT: always False
    retention_policy: str = RETENTION_TEMPORARY
    envelope_version: str = ENVELOPE_SCHEMA
    envelope_created_at: str = field(default_factory=_utc_now_iso)
    meta: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate envelope integrity. Returns list of errors (empty = valid)."""
        errors = []
        if not self.source.strip():
            errors.append("source-empty")
        if not self.fetched_at.strip():
            errors.append("fetched_at-empty")
        if not self.body_hash.strip():
            errors.append("body_hash-empty")
        if self.body_size < 0:
            errors.append("body_size-negative")
        if self.trust_level not in ("verified", "derived", "untrusted", "unknown"):
            errors.append(f"invalid-trust-level: {self.trust_level}")
        if self.extraction_confidence < 0.0 or self.extraction_confidence > 1.0:
            errors.append("extraction_confidence-out-of-range")
        if self.retention_policy not in ALLOWED_RETENTION:
            errors.append(f"invalid-retention-policy: {self.retention_policy}")
        if self.is_instruction:
            errors.append("INVARIANT-VIOLATION: is_instruction must be False")
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize envelope to dict."""
        return {
            "source": self.source,
            "fetched_at": self.fetched_at,
            "content_type": self.content_type,
            "body_size": self.body_size,
            "body_hash": self.body_hash,
            "trust_level": self.trust_level,
            "parser_version": self.parser_version,
            "raw_reference": self.raw_reference,
            "extraction_confidence": self.extraction_confidence,
            "observation_id": self.observation_id,
            "citation_chain": list(self.citation_chain),
            "is_instruction": self.is_instruction,
            "retention_policy": self.retention_policy,
            "envelope_version": self.envelope_version,
            "envelope_created_at": self.envelope_created_at,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObservationEnvelope:
        """Deserialize from dict."""
        return cls(
            source=str(data.get("source", "")),
            fetched_at=str(data.get("fetched_at", "")),
            content_type=str(data.get("content_type", "unknown")),
            body_size=int(data.get("body_size", 0)),
            body_hash=str(data.get("body_hash", "")),
            trust_level=str(data.get("trust_level", "untrusted")),
            parser_version=str(data.get("parser_version", PARSER_VERSION)),
            raw_reference=str(data.get("raw_reference", "")),
            extraction_confidence=float(data.get("extraction_confidence", 0.0)),
            observation_id=str(data.get("observation_id", "")),
            citation_chain=list(data.get("citation_chain", [])),
            is_instruction=bool(data.get("is_instruction", False)),
            retention_policy=str(data.get("retention_policy", RETENTION_TEMPORARY)),
            envelope_version=str(data.get("envelope_version", ENVELOPE_SCHEMA)),
            envelope_created_at=str(data.get("envelope_created_at", "")),
            meta=dict(data.get("meta", {})),
        )

    def compute_evidence_id(self) -> str:
        """Compute evidence_id = sha256(source || fetched_at || body_hash).
        Used for deduplication and citation chain."""
        evidence_input = f"{self.source}||{self.fetched_at}||{self.body_hash}"
        return hashlib.sha256(evidence_input.encode("utf-8")).hexdigest()


def create_envelope(
    source: str,
    fetched_at: str,
    body: bytes,
    content_type: str | None = None,
    trust_level: TrustLevel = "untrusted",
    raw_reference: str = "",
    retention_policy: str = RETENTION_TEMPORARY,
    max_body_size: int = _DEFAULT_MAX_BODY_SIZE,
) -> dict[str, Any]:
    """Create a validated ObservationEnvelope from raw fetch data.

    Returns:
        ok: bool - True if envelope was created successfully
        envelope: ObservationEnvelope or None
        reason: str - error reason if ok=False
    """
    # Validate body size
    size_check = validate_body_size(body, max_body_size)
    if not size_check["ok"]:
        return {"ok": False, "envelope": None, "reason": size_check["reason"]}

    # Validate content type
    ct = validate_content_type(content_type)

    # Compute hash
    bh = content_hash(body)

    # Validate retention
    rp = validate_retention(retention_policy)

    envelope = ObservationEnvelope(
        source=source,
        fetched_at=fetched_at,
        content_type=ct,
        body_size=size_check["size"],
        body_hash=bh,
        trust_level=trust_level,
        raw_reference=raw_reference,
        retention_policy=rp,
    )

    errors = envelope.validate()
    if errors:
        return {"ok": False, "envelope": None,
                "reason": f"validation-errors: {errors}"}

    return {"ok": True, "envelope": envelope, "reason": "ok"}


if __name__ == "__main__":
    import sys

    # Smoke test
    body = b'{"test": "data"}'
    result = create_envelope(
        source="https://example.com/api",
        fetched_at="2026-08-16T12:00:00Z",
        body=body,
        content_type="application/json",
    )
    assert result["ok"], result["reason"]
    env = result["envelope"]
    assert env.body_hash == content_hash(body)
    assert not env.is_instruction
    assert env.trust_level == "untrusted"
    assert env.validate() == []

    # Round-trip
    d = env.to_dict()
    env2 = ObservationEnvelope.from_dict(d)
    assert env2.body_hash == env.body_hash

    # Evidence ID computation
    eid = env.compute_evidence_id()
    assert len(eid) == 64  # SHA-256 hex

    # Empty body rejection
    r2 = create_envelope(source="http://x", fetched_at="2026-08-16T12:00:00Z", body=b"")
    assert not r2["ok"]

    # Oversized body rejection
    r3 = create_envelope(source="http://x", fetched_at="2026-08-16T12:00:00Z",
                         body=b"x" * 2_000_000, max_body_size=1_000_000)
    assert not r3["ok"]
    assert "too-large" in r3["reason"]

    # Content/Instruction invariant
    env3 = ObservationEnvelope(
        source="test", fetched_at="2026-08-16T12:00:00Z",
        content_type="text/plain", body_size=10, body_hash="abc",
        is_instruction=True,
    )
    errors = env3.validate()
    assert any("INVARIANT-VIOLATION" in e for e in errors)

    print("OK envelope smoke test")
    sys.exit(0)
