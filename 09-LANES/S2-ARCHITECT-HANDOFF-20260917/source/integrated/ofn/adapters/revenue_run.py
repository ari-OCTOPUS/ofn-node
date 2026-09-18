"""RevenueRun v1: read-only receipt-chain validation, never authorization.

Uses the existing execution receipt canonicalization. Digests bind bytes;
they do not authenticate a provider, owner release, or independent witness.
No function here writes a ledger, dispatches, or marks VERIFIED_CASH.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from ofn.adapters.receipt import stamp_receipt, verify_receipt
from ofn.kernel.errors import FailClosedError

SCHEMA = "revenue_run.v1"
LEGS = frozenset({"ziman", "painting", "studio"})
STAGES = (
    "lead_captured", "enriched", "qualified", "offer_drafted",
    "owner_released", "dispatched", "replied", "quote_or_order", "settled_cash",
)
GENESIS = "0" * 64
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_FIELDS = frozenset({
    "schema", "run_id", "leg", "stage", "prev_receipt_sha", "policy_sha",
    "evidence_sha", "producer_id", "recorded_at_epoch_s", "mode",
    "witness_id", "witness_receipt_sha", "receipt_sha256",
})


def _require_sha(value: object, field: str, *, genesis: bool = False) -> None:
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise FailClosedError(f"invalid {field}")
    if value == GENESIS and not genesis:
        raise FailClosedError(f"placeholder {field}")


def _require_id(value: object, field: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise FailClosedError(f"invalid opaque {field}")


def _validate_record(record: object) -> dict:
    if not isinstance(record, dict) or set(record) != _FIELDS:
        raise FailClosedError("RevenueRun fields missing or unknown")
    if record["schema"] != SCHEMA:
        raise FailClosedError("unsupported RevenueRun schema")
    for field in ("run_id", "producer_id"):
        _require_id(record[field], field)
    if (not isinstance(record["leg"], str) or record["leg"] not in LEGS
            or not isinstance(record["stage"], str) or record["stage"] not in STAGES):
        raise FailClosedError("unknown RevenueRun leg or stage")
    if record["mode"] not in ("dry_run", "live_observation"):
        raise FailClosedError("invalid RevenueRun mode")
    for field in ("policy_sha", "evidence_sha", "receipt_sha256"):
        _require_sha(record[field], field)
    _require_sha(record["prev_receipt_sha"], "prev_receipt_sha", genesis=True)
    epoch = record["recorded_at_epoch_s"]
    if type(epoch) is not int or epoch < 0:
        raise FailClosedError("invalid recorded_at_epoch_s")
    if record["stage"] == "settled_cash":
        if record["mode"] != "live_observation":
            raise FailClosedError("dry-run cannot claim settled_cash")
        _require_id(record["witness_id"], "witness_id")
        _require_sha(record["witness_receipt_sha"], "witness_receipt_sha")
        if record["witness_id"] == record["producer_id"]:
            raise FailClosedError("settlement witness must differ from producer")
        if record["witness_receipt_sha"] == record["evidence_sha"]:
            raise FailClosedError("witness must reference a separate receipt")
    elif record["witness_id"] is not None or record["witness_receipt_sha"] is not None:
        raise FailClosedError("v1 settlement witness fields only apply at settlement")
    verify_receipt(record)
    return record


def replay(records: Iterable[dict], *, expected_policy_sha: str) -> dict:
    """Validate one run against the caller's independently supplied policy hash.

    An ordered prefix is useful evidence, not a completed run. Even a full
    chain is only structurally valid: referenced source receipts and witness
    identity must be verified outside this byte-integrity contract.
    """
    _require_sha(expected_policy_sha, "expected_policy_sha")
    previous = GENESIS
    identity = None
    last_epoch = -1
    count = 0
    used_evidence = set()
    for raw in records:
        record = _validate_record(raw)
        if count >= len(STAGES) or record["stage"] != STAGES[count]:
            raise FailClosedError("RevenueRun stage skipped, repeated, or reordered")
        current_identity = (record["run_id"], record["leg"], record["mode"])
        if identity is None:
            identity = current_identity
        if current_identity != identity:
            raise FailClosedError("RevenueRun identity changed")
        if record["policy_sha"] != expected_policy_sha:
            raise FailClosedError("RevenueRun policy does not match pinned policy")
        if record["prev_receipt_sha"] != previous:
            raise FailClosedError("RevenueRun predecessor mismatch")
        if record["recorded_at_epoch_s"] < last_epoch:
            raise FailClosedError("RevenueRun timestamp moved backwards")
        if record["evidence_sha"] in used_evidence:
            raise FailClosedError("RevenueRun source evidence reused across stages")
        used_evidence.add(record["evidence_sha"])
        previous = record["receipt_sha256"]
        last_epoch = record["recorded_at_epoch_s"]
        count += 1
    if identity is None:
        raise FailClosedError("RevenueRun requires at least one receipt")
    return {
        "schema": SCHEMA, "status": "STRUCTURE_VALID", "run_id": identity[0],
        "leg": identity[1], "mode": identity[2], "receipt_count": count,
        "last_stage": STAGES[count - 1], "head_receipt_sha": previous,
        "chain_complete": count == len(STAGES), "cash_verified": False,
        "external_evidence_status": "UNVERIFIED", "may_authorize": False,
    }


def make_receipt(*, run_id: str, leg: str, stage: str, prev_receipt_sha: str,
                 policy_sha: str, evidence_sha: str, producer_id: str,
                 recorded_at_epoch_s: int, mode: str = "dry_run",
                 witness_id: str | None = None,
                 witness_receipt_sha: str | None = None) -> dict:
    """Bind a stage observation; replay must still validate its predecessors."""
    record = stamp_receipt({
        "schema": SCHEMA, "run_id": run_id, "leg": leg, "stage": stage,
        "prev_receipt_sha": prev_receipt_sha, "policy_sha": policy_sha,
        "evidence_sha": evidence_sha, "producer_id": producer_id,
        "recorded_at_epoch_s": recorded_at_epoch_s, "mode": mode,
        "witness_id": witness_id, "witness_receipt_sha": witness_receipt_sha,
    })
    return _validate_record(record)
