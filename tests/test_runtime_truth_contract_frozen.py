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
    want = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    got = LOCK.read_text(encoding="utf-8").split()[0]
    assert got == want, "contract edited without updating FROZEN.lock"


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
