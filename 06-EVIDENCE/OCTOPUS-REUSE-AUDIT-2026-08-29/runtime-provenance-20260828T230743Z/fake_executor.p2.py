"""The gate between an owner's approval and a provider call — faked honestly.

The real executor will stand between an `OwnerDecision` and some external
provider. Before it exists, this module pins its behaviour with a fake:
every rule the real one must enforce is enforced here, against a provider
that only records calls. Nothing leaves the process; every rule is still
real.

The gate, in order, each rule fail-closed:

  policy unavailable      DENY `policy-unavailable`. No policy, no judgement.
  witness unavailable     DENY `witness-unavailable`. No receipt, no proof.
  invalid decision        DENY `decision-invalid` (owner_decision.validate).
  mutated payload         DENY `payload-mutated` — sha256(exact_payload)
                          must equal the decision's own payload_sha.
  unbound approval        DENY `approval-unbound` — the approval names a
                          different decision than the one being executed.
  wrong user              DENY `approver-not-owner` — the approver is not on
                          the owner allowlist.
  payload mismatch        DENY `payload-mismatch` — the approval was given
                          for different bytes than the decision now carries.
  expired                 DENY `decision-expired` — past expires_at.
  superseded              DENY `approval-superseded`.
  duplicate approval      DENY `duplicate-approval` — this approval already
                          produced an EXECUTED receipt.
  duplicate key           DENY `duplicate-idempotency-key` — this
                          idempotency key already executed, whatever the
                          approval.

Only then is the provider called. A provider timeout is not a DENY: an
attempt was made, so the outcome is genuinely unknown and the receipt says
FAILED, which is terminal — the log records what happened, never what
should be retried.

Every outcome appends one receipt to `state_dir/execution_receipts.jsonl`,
append-only, with a terminal status (EXECUTED / DENIED / FAILED). There is
no PENDING, on purpose: a receipt that could change later is not a receipt,
and the duplicate rules read this same file — a second execution of one
approval must find the first one there.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from .owner_decision import OwnerDecision, validate

RECEIPT_SCHEMA = "execution_receipt.v1"
RECEIPTS_FILENAME = "execution_receipts.jsonl"

STATUS_EXECUTED = "EXECUTED"
STATUS_DENIED = "DENIED"
STATUS_FAILED = "FAILED"
TERMINAL_STATUSES = (STATUS_EXECUTED, STATUS_DENIED, STATUS_FAILED)

# Who may approve, for the fake. The real executor reads this from
# config.owner_user_ids; a constant keeps the fake hermetic.
OWNER_USER_IDS = frozenset({"owner"})


class ProviderTimeout(Exception):
    """The provider did not answer. The outcome is unknown, not denied."""


class FakeProvider:
    """Records every call it would have made. Sends nothing, ever."""

    def __init__(self, *, timeout: bool = False) -> None:
        self.timeout = timeout
        self.calls: list[str] = []

    def send(self, payload: str) -> dict:
        self.calls.append(payload)
        if self.timeout:
            raise ProviderTimeout("provider timed out")
        return {"status": "sent",
                "payload_sha256": hashlib.sha256(
                    payload.encode("utf-8")).hexdigest()}


@dataclass(frozen=True)
class Approval:
    """The owner's yes, as the executor needs to see it.

    `superseded` models the owner changing their mind after approving: the
    approval still exists, still hashes correctly, and must still be
    refused — which is why it is a field rather than a deleted row.
    """
    approval_id: str
    decision_id: str
    approver_user_id: str
    payload_sha: str
    idempotency_key: str
    granted_at: str = ""
    superseded: bool = False


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _receipts_path(state_dir: str | None) -> Path | None:
    if state_dir is None:
        return None
    path = Path(state_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / RECEIPTS_FILENAME


def _load_receipts(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    out: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                out.append(record)
    return out


def _append_receipt(path: Path | None, receipt: dict) -> None:
    if path is None:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def execute_with_approval(decision: OwnerDecision, approval: Approval,
                          provider: FakeProvider,
                          policy_available: bool = True,
                          witness_available: bool = True, *,
                          state_dir: str | None = None,
                          now_utc: str = "") -> dict:
    """Run the gate, call the provider at most once, return the receipt.

    `now_utc` freezes the clock for tests; without it the wall clock is
    read once. `state_dir` is where receipts live and where the duplicate
    rules read history from — without it the gate still runs, but two calls
    in one process cannot see each other's history, so pass it whenever
    replay protection matters (it always does outside a single assertion).
    """
    now = now_utc or _now_iso()
    path = _receipts_path(state_dir)
    prior = _load_receipts(path)

    rule = ""
    if not policy_available:
        rule = "policy-unavailable"
    elif not witness_available:
        rule = "witness-unavailable"
    elif validate(decision):
        rule = "decision-invalid"
    elif _sha256_text(decision.exact_payload) != decision.payload_sha:
        rule = "payload-mutated"
    elif approval.decision_id != decision.decision_id:
        rule = "approval-unbound"
    elif approval.approver_user_id not in OWNER_USER_IDS:
        rule = "approver-not-owner"
    elif approval.payload_sha != decision.payload_sha:
        rule = "payload-mismatch"
    # `now >= decision.expires_at` is safe as a string compare because
    # validate() has already rejected any expires_at that is not exactly
    # YYYY-MM-DDTHH:MM:SSZ — a shape whose byte order is its time order.
    elif now >= decision.expires_at:
        rule = "decision-expired"
    elif approval.superseded:
        rule = "approval-superseded"
    elif any(r.get("status") == STATUS_EXECUTED
             and r.get("approval_id") == approval.approval_id for r in prior):
        rule = "duplicate-approval"
    elif any(r.get("status") == STATUS_EXECUTED
             and r.get("idempotency_key") == decision.idempotency_key
             for r in prior):
        rule = "duplicate-idempotency-key"

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "decision_id": decision.decision_id,
        "idempotency_key": decision.idempotency_key,
        "approval_id": approval.approval_id,
        "approver_user_id": approval.approver_user_id,
        "recorded_at": now,
        "provider_called": False,
    }

    if rule:
        receipt["status"] = STATUS_DENIED
        receipt["rule"] = rule
    else:
        receipt["provider_called"] = True
        try:
            result = provider.send(decision.exact_payload)
        except ProviderTimeout:
            receipt["status"] = STATUS_FAILED
            receipt["rule"] = "provider-timeout"
        else:
            receipt["status"] = STATUS_EXECUTED
            receipt["rule"] = "executed"
            receipt["provider_result"] = result

    _append_receipt(path, receipt)
    return receipt
