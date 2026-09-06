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

try:
    import pytest
except ModuleNotFoundError:  # CI installs pytest; this host may not.
    class _Raises:
        def __init__(self, exc: type[BaseException]) -> None:
            self.exc = exc

        def __enter__(self) -> "_Raises":
            return self

        def __exit__(self, typ, val, tb):
            if typ is None:
                raise AssertionError(f"DID NOT RAISE {self.exc}")
            return issubclass(typ, self.exc)

    class _PytestShim:
        raises = staticmethod(lambda exc: _Raises(exc))

    pytest = _PytestShim()  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ofn.agents.brain_schema import (  # noqa: E402
    BrainEvent, BrainProposal, SchemaViolation,
    EVENT_TYPES, BUSINESS_IDS, ACTION_TYPES,
)

CONTRACT = ROOT / "ofn" / "agents" / "brain_schema.py"
LOCK = ROOT / "ofn" / "agents" / "brain_schema.lock"
GITATTRIBUTES = ROOT / "ofn" / "agents" / ".gitattributes"

# windows-latest job 100896706436 @547991646c70fca80f617ab01d599ff067ad07fe
# (2026-09-04T03:11:10Z) hashed the working-tree file as 7e99cb35… after
# autocrlf rewrote LF→CRLF. That is a checkout artefact, not a source
# change. The LF blob is the contract. Pin: ofn/agents/.gitattributes.
_CONTRACT_CRLF_SHA256 = (
    "7e99cb35f8970a5069521f36f72855948b56f2a8d9182326edd2db61d4d9c901"
)


def _canonical_bytes(data: bytes) -> bytes:
    """LF identity. CRLF checkout is not a contract edit."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _canonical_sha256(data: bytes) -> str:
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


def _lock_digest() -> str:
    return LOCK.read_text(encoding="utf-8").split()[0]


def test_frozen_lock_matches() -> None:
    # Preferred pin: .gitattributes eol=lf.
    # Second witness: LF-canonical hash, so a runner that still
    # converts checkout bytes cannot fake a source-hash miss.
    # Pattern: tests/test_runtime_truth_contract_frozen.py.
    want = _canonical_sha256(CONTRACT.read_bytes())
    got = _lock_digest()
    assert got == want, "brain_schema.py edited without updating lock"


def test_windows_crlf_checkout_is_a_known_hash_not_the_source() -> None:
    """Second witness: the windows-latest failure hash is LF→CRLF, not a new source."""
    lf = _canonical_bytes(CONTRACT.read_bytes())
    crlf = lf.replace(b"\n", b"\r\n")
    assert hashlib.sha256(crlf).hexdigest() == _CONTRACT_CRLF_SHA256
    assert _CONTRACT_CRLF_SHA256 != _lock_digest()
    assert _canonical_sha256(crlf) == _lock_digest()


def test_hashed_contract_checkout_is_pinned_lf() -> None:
    assert GITATTRIBUTES.is_file()
    text = GITATTRIBUTES.read_text(encoding="utf-8")
    assert "eol=lf" in text
    assert "*.py" in text
    assert "*.lock" in text


def test_content_edit_breaks_lock() -> None:
    mutated = _canonical_bytes(CONTRACT.read_bytes()) + b"\n# mutated\n"
    assert _canonical_sha256(mutated) != _lock_digest()


def test_lone_cr_normalizes_to_same_lock() -> None:
    lf = _canonical_bytes(CONTRACT.read_bytes())
    classic_mac = lf.replace(b"\n", b"\r")
    assert _canonical_sha256(classic_mac) == _lock_digest()
    assert hashlib.sha256(classic_mac).hexdigest() != _lock_digest()


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
