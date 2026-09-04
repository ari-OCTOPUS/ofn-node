"""Brain schema freeze — GAP-066 close (Round 35).

The brain needs structured input, not raw events. This contract freezes
the shape: BrainEvent (what goes in) and BrainProposal (what comes out),
with may_authorize structurally forbidden (the brain never authorizes).

Frozen via the same pattern as runtime_truth_v1: edit without updating
FROZEN.lock = red test."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ofn.agents.brain_schema import (  # noqa: E402
    BrainEvent, BrainProposal, SchemaViolation,
    EVENT_TYPES, BUSINESS_IDS, ACTION_TYPES,
)

CONTRACT = ROOT / "ofn" / "agents" / "brain_schema.py"
LOCK = ROOT / "ofn" / "agents" / "brain_schema.lock"


def test_frozen_lock_matches() -> None:
    want = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    got = LOCK.read_text(encoding="utf-8").split()[0]
    assert got == want, "brain_schema.py edited without updating lock"


def test_event_vocabularies() -> None:
    assert "payment.verified" in EVENT_TYPES
    assert "order.received" in EVENT_TYPES
    assert "painting" in BUSINESS_IDS
    assert "ziman" in BUSINESS_IDS
    assert "studio" in BUSINESS_IDS


def test_action_vocabularies() -> None:
    assert "rank" in ACTION_TYPES
    assert "propose" in ACTION_TYPES
    assert "hold" in ACTION_TYPES
    assert "escalate" in ACTION_TYPES


def test_may_authorize_always_false() -> None:
    with pytest.raises(SchemaViolation):
        BrainProposal(
            business_id="ziman", action="propose", summary="t",
            confidence=0.5, may_authorize=True)


def test_invalid_business_rejected() -> None:
    with pytest.raises(SchemaViolation):
        BrainEvent(event_type="payment.verified", business_id="mars",
                   lead_id="l", occurred_at="2026-09-04T00:00:00Z")


def test_invalid_event_type_rejected() -> None:
    with pytest.raises(SchemaViolation):
        BrainEvent(event_type="explosion", business_id="ziman",
                   lead_id="l", occurred_at="2026-09-04T00:00:00Z")


def test_invalid_confidence_rejected() -> None:
    with pytest.raises(SchemaViolation):
        BrainProposal(business_id="ziman", action="rank",
                      summary="t", confidence=1.5)


def test_confidence_zero_valid() -> None:
    p = BrainProposal(business_id="ziman", action="hold",
                      summary="uncertain", confidence=0.0)
    assert p.confidence == 0.0
