#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mission_contract — the shared "envelope" every Octopus cross-component record conforms to.

WHAT THIS IS (and is NOT):
  * A tiny, stdlib-only HELPER: field list, id/trace generation, content hashing,
    validation, and legal status transitions.
  * NOT a new bus and NOT a new mission store. It complements the existing
    `mission.py` (Mission Genome) and `unified_bus.py` (event spine); it does not
    replace or compete with them. Callers IMPORT this to stay consistent — which
    PREVENTS the "two parallel worlds" drift the connectivity audit found.

Adoption plan (wired by the lead, serial lane): mission.py, approval_store.py, and the
GLM worker modules (lead_leg, doctor.advance_rfcs, approval sha) all build/validate their
cross-component records through here.

Contract: OCTOPUS-OS strategy §4. Stdlib only. Inert until imported.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any, Dict, List, Optional

# ── canonical vocabulary ─────────────────────────────────────────────
RISK = ("low", "medium", "high", "critical")
STATUS = ("queued", "running", "blocked", "needs_approval", "done", "failed")
TERMINAL = ("done", "failed")

# legal status transitions (fail-closed: anything not listed is illegal)
LEGAL_TRANSITIONS: Dict[str, tuple] = {
    "queued": ("running", "blocked", "needs_approval", "failed"),
    "running": ("done", "failed", "blocked", "needs_approval"),
    "blocked": ("queued", "running", "failed"),
    "needs_approval": ("running", "failed", "blocked"),
    "done": (),
    "failed": (),
}

# the required envelope fields (OCTOPUS-OS §4)
REQUIRED_FIELDS = (
    "mission_id", "source", "target_leg", "owner", "action",
    "risk", "status", "trace_id", "content_sha256",
)


# ── generators ───────────────────────────────────────────────────────
def new_mission_id(prefix: str = "MIS") -> str:
    """MIS-YYYYMMDD-<6 hex>. Sortable-ish, collision-resistant enough for owner scale."""
    day = time.strftime("%Y%m%d", time.gmtime())
    return f"{prefix}-{day}-{uuid.uuid4().hex[:6]}"


def new_trace_id() -> str:
    return uuid.uuid4().hex


def content_sha256(action: str, target_leg: str, payload: Optional[Any] = None) -> str:
    """Deterministic hash over the canonical (action, target, payload).
    Binds an approval to the EXACT scope it approved (anti-TOCTOU)."""
    blob = json.dumps(
        {"action": action, "target_leg": target_leg, "payload": payload if payload is not None else {}},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def requires_approval(risk: str) -> bool:
    """Risk-proportional authorization: medium/high/critical require an owner verdict."""
    return risk in ("medium", "high", "critical")


# ── builders / validators ────────────────────────────────────────────
def make_envelope(
    *, source: str, target_leg: str, owner: str, action: str, risk: str,
    intent: str = "", payload: Optional[Any] = None,
    input_refs: Optional[List[str]] = None, output_refs: Optional[List[str]] = None,
    next_owner: str = "octopus_core", mission_id: Optional[str] = None,
    trace_id: Optional[str] = None, status: str = "queued",
    tenant_id: str = "personal", project_id: str = "octopus-core",
    task_id: str = "", scope: str = "project", schema_version: int = 2,
    policy_version: str = "octopus-policy.v1",
) -> Dict[str, Any]:
    """Build a conformant mission record. Computes id, trace, sha, and requires_approval."""
    if risk not in RISK:
        raise ValueError(f"risk must be one of {RISK}, got {risk!r}")
    if status not in STATUS:
        raise ValueError(f"status must be one of {STATUS}, got {status!r}")
    return {
        "mission_id": mission_id or new_mission_id(),
        "source": source,
        "intent": intent,
        "target_leg": target_leg,
        "owner": owner,
        "action": action,
        "risk": risk,
        "status": status,
        "requires_approval": requires_approval(risk),
        "input_refs": list(input_refs or []),
        "output_refs": list(output_refs or []),
        "next_owner": next_owner,
        "trace_id": trace_id or new_trace_id(),
        "content_sha256": content_sha256(action, target_leg, payload),
        "tenant_id": str(tenant_id or "personal"),
        "project_id": str(project_id or "octopus-core"),
        "task_id": str(task_id or ""),
        "scope": str(scope or "project"),
        "schema_version": int(schema_version),
        "policy_version": str(policy_version or "octopus-policy.v1"),
        "created_ts": time.time(),
    }


# ── واژگانِ آشتیِ دو دنیا (VQ-MISSION-RECONCILE-001 قدمِ ۱، ۰۷-۳۱) ──────────
# Mission Genome (telegram_center/mission.py) ۱۲ وضعیت دارد و این قرارداد ۶ تا.
# این نگاشتِ خالص هر وضعِ Genome را به واژگانِ canonical می‌برد تا خواننده‌های
# cross-world (snapshot/کارت‌ها) یک زبان ببینند. ناشناخته = blocked (fail-up).
GENOME_STATE_MAP = {
    "created": "queued", "planned": "queued",
    "patched": "running", "tested": "running", "reviewed": "running",
    "awaiting_owner": "needs_approval",
    "approved": "running", "applied": "running", "monitored": "running",
    "done": "done", "reverted": "failed", "rejected": "failed",
}


def genome_to_canonical(state: str) -> str:
    return GENOME_STATE_MAP.get(str(state or ""), "blocked")


def can_transition(old: str, new: str) -> bool:
    return new in LEGAL_TRANSITIONS.get(old, ())


def is_terminal(status: str) -> bool:
    return status in TERMINAL


def validate(record: Dict[str, Any]) -> List[str]:
    """Return a list of human-readable problems ([] == valid). Never raises."""
    errs: List[str] = []
    if not isinstance(record, dict):
        return ["record is not a dict"]
    for f in REQUIRED_FIELDS:
        if f not in record or record[f] in (None, ""):
            errs.append(f"missing required field: {f}")
    if record.get("risk") not in RISK:
        errs.append(f"invalid risk: {record.get('risk')!r}")
    if record.get("status") not in STATUS:
        errs.append(f"invalid status: {record.get('status')!r}")
    # consistency: medium/high/critical must be gated
    r = record.get("risk")
    if r in ("medium", "high", "critical") and record.get("requires_approval") is not True:
        errs.append("medium/high/critical risk must have requires_approval=True")
    for f in ("tenant_id", "project_id", "scope"):
        if f in record and not str(record.get(f) or "").strip():
            errs.append(f"{f} must be non-empty when present")
    sha = record.get("content_sha256")
    if isinstance(sha, str) and len(sha) != 64:
        errs.append("content_sha256 must be 64 hex chars")
    return errs


if __name__ == "__main__":  # tiny smoke when run directly
    m = make_envelope(source="telegram_owner", target_leg="lead", owner="leg_lead_owner",
                      action="register_lead", risk="low", intent="نقاشیِ مشتری X")
    assert validate(m) == [], validate(m)
    print("smoke ok:", m["mission_id"], m["content_sha256"][:12])
