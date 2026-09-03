"""F1 contract freeze — the lock is the law (Round 19, PR #162).

If anyone edits contracts/runtime_truth_v1.py without updating FROZEN.lock,
this test goes red — that is the whole point of 'قرارداد قبل از قابلیت'."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.runtime_truth_v1 import (  # noqa: E402
    F1_STATUSES, GOV_STATUSES, NODE_IDS, ContractViolation,
    RuntimeTruthRow, validate_rows,
)

CONTRACT = ROOT / "contracts" / "runtime_truth_v1.py"
LOCK = ROOT / "contracts" / "FROZEN.lock"
GITATTRIBUTES = ROOT / "contracts" / ".gitattributes"

# windows-latest job 100656285087 @6b0353280b6aca63bcc7e64a6dd63b830470d630
# (2026-09-03T12:56:27Z) hashed the working-tree file as bad38e24… after
# autocrlf rewrote LF→CRLF. That is a checkout artefact, not a source
# change. The LF blob is the contract. Pin: contracts/.gitattributes.
_CONTRACT_CRLF_SHA256 = (
    "bad38e2496e138d07dccee0135de1a6cf0098f6f1477d99dfce89e1901717b4b"
)


def _canonical_bytes(data: bytes) -> bytes:
    """LF identity. CRLF checkout is not a contract edit."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _canonical_sha256(data: bytes) -> str:
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


def _lock_digest() -> str:
    return LOCK.read_text(encoding="utf-8").split()[0]


def _row(**over) -> RuntimeTruthRow:
    base = dict(
        id="F1-138-T01", claim="test claim", node_id="138",
        read_method="echo ok", output_excerpt="ok",
        evidence_path="receipts/x.jsonl", sha256_or_commit="abc123",
        timestamp_utc="2026-09-03T00:00:00Z",
        f1_status="LIVE", gov_status="OPEN",
        writer="w", readers=("pulse",),
    )
    base.update(over)
    return RuntimeTruthRow(**base)


def test_frozen_lock_matches_contract() -> None:
    # Preferred pin: .gitattributes eol=lf.
    # Second witness: LF-canonical hash, so a runner that still
    # converts checkout bytes cannot fake a source-hash miss.
    # Pattern: tests/test_doctor_lane_contract_map.py.
    want = _canonical_sha256(CONTRACT.read_bytes())
    got = _lock_digest()
    assert got == want, "contract edited without updating FROZEN.lock"


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


def test_row_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _row().id = "changed"


def test_status_vocabularies_exact() -> None:
    assert F1_STATUSES == ("LIVE", "PRESENT_UNWIRED", "STALE", "NOT_FOUND",
                           "UNKNOWN")
    assert GOV_STATUSES == ("OPEN", "BLOCKED", "PARKED", "OWNER_DECISION",
                            "BROKEN")
    assert NODE_IDS == ("138", "180", "182", "laptop")


def test_rule_no_receipt_never_live() -> None:
    with pytest.raises(ContractViolation):
        _row(sha256_or_commit="", f1_status="LIVE")
    # بدون رسید اما UNKNOWN — مجاز
    assert _row(sha256_or_commit="", f1_status="UNKNOWN").f1_status == "UNKNOWN"


def test_rule_empty_readers_present_unwired() -> None:
    with pytest.raises(ContractViolation):
        _row(readers=(), f1_status="LIVE")
    ok = _row(readers=(), f1_status="PRESENT_UNWIRED")
    assert ok.as_dict()["readers"] == []


def test_bad_enum_or_node_rejected() -> None:
    with pytest.raises(ContractViolation):
        _row(f1_status="GREEN")
    with pytest.raises(ContractViolation):
        _row(gov_status="MAYBE")
    with pytest.raises(ContractViolation):
        _row(node_id="190")


def test_excerpt_cap_enforced() -> None:
    with pytest.raises(ContractViolation):
        _row(output_excerpt="x" * 501)


def test_duplicate_ids_rejected() -> None:
    a, b = _row(), _row(gov_status="BLOCKED")
    with pytest.raises(ContractViolation):
        validate_rows([a, b])
