#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence_parser.py — Evidence-Grounded Parser Pipeline (EQUIP G3 Perception).

Bridges ObservationEnvelope to existing observation_v1.parse_body().
All parsed output is UNTRUSTED DATA. Content is NEVER instruction.

Pipeline:
  1. Validate envelope
  2. MIME-based routing
  3. Parse (delegating to observation_v1 for known formats)
  4. Mark output as untrusted
  5. Attach extraction confidence
  6. Build citation reference

$0 | stdlib-only | no network | no LLM | no external writes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from envelope import ObservationEnvelope, PARSER_VERSION, TrustLevel  # noqa: E402
from observation_v1 import parse_body, PARSE_DRIFT, SCHEMA  # noqa: E402


# Confidence levels for parser outcomes
_CONFIDENCE_STRUCTURED_PARSE = 0.8    # successful structured parse
_CONFIDENCE_DRIFT = 0.0              # parse drift = no confidence
_CONFIDENCE_UNSUPPORTED_TYPE = 0.0   # unknown content type
_CONFIDENCE_JSON_DECODE_ERROR = 0.0  # malformed JSON


def parse_envelope(envelope: ObservationEnvelope) -> dict[str, Any]:
    """Parse an observation envelope through the evidence pipeline.

    Returns:
        ok: bool - True if parsing produced useful output
        events: list of parsed events (untrusted data)
        confidence: float [0,1] extraction confidence
        trust_level: str - always 'untrusted' for parsed output
        parser_version: str
        observation_id: str
        evidence_id: str
        reason: str - human-readable outcome
        content_is_instruction: bool - ALWAYS False (invariant)
        citation_ref: str - evidence ID for citation chain
    """
    # Validate envelope
    errors = envelope.validate()
    if errors:
        return _result(False, [], _CONFIDENCE_DRIFT, "envelope-validation-failed",
                       envelope.observation_id, envelope.compute_evidence_id())

    # Route by content type
    ct = envelope.content_type.lower()

    if ct in ("application/json", "application/geo+json"):
        return _parse_json(envelope)

    if ct in ("text/plain", "text/html", "text/csv", "text/xml",
              "application/xml", "application/sdmx+xml"):
        # These require specialized parsers beyond observation_v1.
        # For now, they are not auto-parsed (future extension point).
        return _result(False, [], _CONFIDENCE_UNSUPPORTED_TYPE,
                       "unsupported-content-type-for-auto-parse",
                       envelope.observation_id, envelope.compute_evidence_id())

    return _result(False, [], _CONFIDENCE_UNSUPPORTED_TYPE,
                   "unknown-content-type",
                   envelope.observation_id, envelope.compute_evidence_id())


def _parse_json(envelope: ObservationEnvelope) -> dict[str, Any]:
    """Parse JSON body through observation_v1.parse_body().

    The body hash from the envelope is used as a raw_reference,
    not the actual body content (we don't store it here).
    observation_v1.parse_body requires the actual bytes, so we
    note that the caller must provide the body to re-parse.
    """
    # observation_v1 needs actual body bytes. The envelope only stores the hash.
    # This is by design: the envelope is metadata; the body is in raw storage.
    # For the pipeline, we return a marker that re-parsing is needed with body.
    return {
        "ok": True,
        "events": [],
        "confidence": _CONFIDENCE_STRUCTURED_PARSE,
        "trust_level": "untrusted",
        "parser_version": PARSER_VERSION,
        "observation_id": envelope.observation_id,
        "evidence_id": envelope.compute_evidence_id(),
        "reason": "json-structured-ready-for-observation_v1",
        "content_is_instruction": False,
        "citation_ref": envelope.compute_evidence_id(),
        "requires_body": True,
        "source": envelope.source,
        "fetched_at": envelope.fetched_at,
    }


def parse_with_body(
    source: str,
    fetched_at: str,
    body: bytes,
    content_type: str | None = None,
) -> dict[str, Any]:
    """Full parse pipeline: create envelope + parse body.

    Convenience function combining create_envelope + parse_body.
    All output is untrusted data.

    Returns:
        ok: bool
        events: list
        confidence: float
        trust_level: str
        parser_version: str
        evidence_id: str
        content_is_instruction: bool - ALWAYS False
        citation_ref: str
        reason: str
    """
    from envelope import create_envelope

    # Create envelope
    env_result = create_envelope(
        source=source,
        fetched_at=fetched_at,
        body=body,
        content_type=content_type or "application/json",
    )
    if not env_result["ok"]:
        return _result(False, [], 0.0, f"envelope-failed: {env_result['reason']}",
                       "", "")

    envelope = env_result["envelope"]
    evidence_id = envelope.compute_evidence_id()

    # Route to observation_v1 for JSON
    ct = (content_type or "").lower()
    if ct in ("application/json", "application/geo+json") or \
       (not ct and _looks_like_json(body)):
        parse_result = parse_body(url=source, fetched_at=fetched_at, body=body)
        if parse_result.get("ok"):
            return {
                "ok": True,
                "events": parse_result.get("events", []),
                "confidence": _CONFIDENCE_STRUCTURED_PARSE,
                "trust_level": "untrusted",
                "parser_version": PARSER_VERSION,
                "observation_id": envelope.observation_id,
                "evidence_id": evidence_id,
                "content_is_instruction": False,
                "citation_ref": evidence_id,
                "reason": "structured-parse-ok",
                "may_gate": False,
                "may_trigger_tool": False,
                "feeds_organism_decision": False,
                "schema": SCHEMA,
            }
        else:
            return _result(False, [], _CONFIDENCE_DRIFT,
                           f"parse-drift: {parse_result.get('reason', 'unknown')}",
                           envelope.observation_id, evidence_id)

    return _result(False, [], _CONFIDENCE_UNSUPPORTED_TYPE,
                   "unsupported-content-type",
                   envelope.observation_id, evidence_id)


def _looks_like_json(body: bytes) -> bool:
    """Heuristic: check if body starts with JSON marker."""
    stripped = body.lstrip()
    return len(stripped) > 0 and stripped[0:1] in (b"{", b"[")


def _result(
    ok: bool, events: list, confidence: float, reason: str,
    observation_id: str, evidence_id: str,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "events": events,
        "confidence": confidence,
        "trust_level": "untrusted",      # ALL parsed output is untrusted
        "parser_version": PARSER_VERSION,
        "observation_id": observation_id,
        "evidence_id": evidence_id,
        "content_is_instruction": False,   # INVARIANT: always False
        "citation_ref": evidence_id,
        "reason": reason,
        "may_gate": False,
        "may_trigger_tool": False,
        "feeds_organism_decision": False,
    }


if __name__ == "__main__":
    import sys

    # Test with USGS data
    body_usgs = json.dumps({
        "features": [{
            "properties": {"mag": 4.5, "place": "Test Earthquake", "time": 1234567890}
        }]
    }).encode()

    result = parse_with_body(
        source="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
        fetched_at="2026-08-16T12:00:00Z",
        body=body_usgs,
        content_type="application/geo+json",
    )
    assert result["ok"], result["reason"]
    assert result["confidence"] == 0.8
    assert result["trust_level"] == "untrusted"
    assert result["content_is_instruction"] is False
    assert result["events"][0]["kind"] == "earthquake"
    assert len(result["evidence_id"]) == 64
    print(f"  USGS parse: {result['events'][0]}")

    # Test with HN data
    body_hn = json.dumps([{"id": 42, "title": "Hello HN"}]).encode()
    result2 = parse_with_body(
        source="https://hacker-news.firebaseio.com/v0/topstories.json",
        fetched_at="2026-08-16T12:00:00Z",
        body=body_hn,
    )
    assert result2["ok"], result2["reason"]
    assert result2["events"][0]["kind"] == "hn-item"
    print(f"  HN parse: {result2['events'][0]}")

    # Test with unknown shape (drift)
    result3 = parse_with_body(
        source="https://example.com/api",
        fetched_at="2026-08-16T12:00:00Z",
        body=b"not json at all",
    )
    assert not result3["ok"]
    assert result3["confidence"] == 0.0
    print(f"  Drift: {result3['reason']}")

    # Test with HTML (unsupported for auto-parse)
    result4 = parse_with_body(
        source="https://example.com/page",
        fetched_at="2026-08-16T12:00:00Z",
        body=b"<html><body>hello</body></html>",
        content_type="text/html",
    )
    assert not result4["ok"]
    assert "unsupported" in result4["reason"]
    print(f"  HTML: {result4['reason']}")

    print("OK evidence_parser smoke test")
    sys.exit(0)
