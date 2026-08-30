#!/usr/bin/env python3
"""approval_state_machine.py — Wave 6 · B. Approval Gate / Verdict Flow Agent

Explicit state machine for approval actions.
States: suggested → queued → owner_approved → executed
        ↓           ↓              ↓
      rejected   expired      superseded
        ↑           ↑
      dry_run (special: records intent without execution)

Rules:
  - No silent state jumps (every transition must be explicit)
  - Invalid transitions raise ValueError with clear message
  - Every transition is logged to _ops/state/approval-log.jsonl
  - Owner identity + timestamp + rationale required for verdict transitions
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPS_STATE = Path("F:/backup/_ops/state")
APPROVAL_LOG = OPS_STATE / "approval-log.jsonl"

VALID_STATUSES = frozenset({
    "suggested", "queued", "owner_approved", "executed",
    "rejected", "expired", "superseded", "dry_run",
})

# Compatibility alias for extract_queue_data.py
ActionStatus = type("ActionStatus", (), {
    "SUGGESTED": "suggested",
    "QUEUED": "queued",
    "OWNER_APPROVED": "owner_approved",
    "EXECUTED": "executed",
    "REJECTED": "rejected",
    "EXPIRED": "expired",
    "SUPERSEDED": "superseded",
    "DRY_RUN": "dry_run",
})()

# Valid transitions: from_state → {to_state, ...}
VALID_TRANSITIONS: dict[str, set[str]] = {
    "suggested": {"queued", "rejected", "expired", "dry_run"},
    "queued": {"owner_approved", "rejected", "expired", "superseded", "dry_run"},
    "owner_approved": {"executed", "superseded", "dry_run"},
    "executed": {"superseded"},  # executed can be superseded (e.g., rollback marker)
    "rejected": set(),           # terminal
    "expired": set(),            # terminal
    "superseded": set(),         # terminal
    "dry_run": {"queued", "suggested", "owner_approved"},  # can graduate from dry_run
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_state_dir() -> None:
    OPS_STATE.mkdir(parents=True, exist_ok=True)


def _append_log(entry: dict) -> None:
    _ensure_state_dir()
    try:
        with open(APPROVAL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass  # fail-soft: state machine works even if logging fails


class ApprovalStateMachine:
    """Small, explicit state machine for a single approval action."""

    def __init__(self, action_id: str, initial_status: str = "suggested"):
        if initial_status not in VALID_STATUSES:
            raise ValueError(f"Invalid initial status '{initial_status}'. Must be one of: {VALID_STATUSES}")
        self.action_id = action_id
        self.status = initial_status
        self.history: list[dict] = []
        self._log_transition(None, initial_status, "system", "init", "")

    def _log_transition(self, from_status: str | None, to_status: str,
                        actor: str, action_type: str, rationale: str) -> None:
        entry = {
            "ts": _now_iso(),
            "action_id": self.action_id,
            "from_status": from_status,
            "to_status": to_status,
            "actor": actor,
            "action_type": action_type,
            "rationale": rationale,
        }
        self.history.append(entry)
        _append_log(entry)

    def transition(self, to_status: str, *, actor: str, rationale: str = "") -> None:
        """Attempt a state transition. Raises ValueError if invalid."""
        if to_status not in VALID_STATUSES:
            raise ValueError(
                f"Action {self.action_id}: unknown target status '{to_status}'. "
                f"Valid: {VALID_STATUSES}"
            )
        if to_status == self.status:
            return  # idempotent
        allowed = VALID_TRANSITIONS.get(self.status, set())
        if to_status not in allowed:
            raise ValueError(
                f"Action {self.action_id}: INVALID transition '{self.status}' -> '{to_status}'. "
                f"Allowed from '{self.status}': {allowed or 'NONE (terminal)'}. "
                f"Rationale required for verdict transitions."
            )
        from_status = self.status
        self.status = to_status
        self._log_transition(from_status, to_status, actor, "transition", rationale)

    def verdict(self, verdict_value: str, *, owner_identity: str,
                rationale: str = "") -> None:
        """Owner verdict: approve / deny / expire / supersede."""
        if not owner_identity:
            raise ValueError("Owner identity is required for all verdicts (P3 §5).")

        verdict_map = {
            "approve": "owner_approved",
            "deny": "rejected",
            "expire": "expired",
            "supersede": "superseded",
        }
        target = verdict_map.get(verdict_value)
        if target is None:
            raise ValueError(
                f"Unknown verdict '{verdict_value}'. Use: approve, deny, expire, supersede"
            )
        self.transition(target, actor=f"owner:{owner_identity}", rationale=rationale)

    def dry_run(self, *, actor: str = "system", rationale: str = "") -> None:
        """Mark as dry-run (propose-only, no execution)."""
        self.transition("dry_run", actor=actor, rationale=rationale)

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "status": self.status,
            "history": self.history,
        }


def validate_action_object(obj: dict) -> list[str]:
    """Validate an action object against the schema. Returns list of errors."""
    errors: list[str] = []
    required = ["action_id", "type", "source", "requested_at"]
    for k in required:
        if k not in obj:
            errors.append(f"Missing required field: {k}")
    status = obj.get("status", "")
    if status not in VALID_STATUSES:
        errors.append(f"Invalid status '{status}'")
    verdict = obj.get("verdict", "")
    if verdict and verdict not in ("approve", "deny", "expire", "supersede"):
        errors.append(f"Invalid verdict '{verdict}'")
    # Owner identity required if verdict is present
    if verdict and not obj.get("owner_identity"):
        errors.append("verdict present but owner_identity missing")
    return errors


# ── Compatibility APIs for extract_queue_data.py ─────────────────────────────

def map_old_status(old_status: str) -> str:
    """Map legacy queue status to canonical Wave 6 status."""
    mapping = {
        "pending": "queued",
        "approved": "owner_approved",
        "settled": "executed",
        "denied": "rejected",
    }
    return mapping.get(old_status, old_status)


def required_action_label(status: str) -> str:
    """Human-readable required action for a given status."""
    labels = {
        "suggested": "needs review",
        "queued": "owner verdict required",
        "owner_approved": "awaiting execution",
        "executed": "complete",
        "rejected": "no action — denied",
        "expired": "no action — expired",
        "superseded": "no action — superseded",
        "dry_run": "dry-run complete — review output",
    }
    return labels.get(status, "unknown")


class ApprovalLogReader:
    """Read approval-log.jsonl for stats and denial reasons."""

    def __init__(self, path: Path | None = None):
        self._path = path or APPROVAL_LOG

    def _read(self) -> list[dict]:
        if not self._path.exists():
            return []
        rows = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
        except OSError:
            pass
        return rows

    def stats(self) -> dict:
        rows = self._read()
        by_new = {}
        by_verdict = {}
        dry_run = 0
        live = 0
        for r in rows:
            ns = r.get("to_status", "unknown")
            by_new[ns] = by_new.get(ns, 0) + 1
            v = r.get("verdict", "")
            if v:
                by_verdict[v] = by_verdict.get(v, 0) + 1
            if r.get("execution_mode") == "dry_run":
                dry_run += 1
            elif r.get("execution_mode") == "live":
                live += 1
        total = len(rows)
        return {
            "total_transitions": total,
            "by_new_status": by_new,
            "by_verdict": by_verdict,
            "dry_run_count": dry_run,
            "live_count": live,
            "dry_run_ratio": round(dry_run / total, 3) if total else 0.0,
        }

    def denial_reasons(self, action_id: str) -> list[str]:
        rows = self._read()
        reasons = []
        for r in rows:
            if r.get("action_id") == action_id and r.get("to_status") == "rejected":
                rationale = r.get("rationale", "")
                if rationale:
                    reasons.append(rationale)
        return reasons


# Patch static methods onto ApprovalStateMachine for compatibility
ApprovalStateMachine.map_old_status = staticmethod(map_old_status)  # type: ignore
ApprovalStateMachine.required_action_label = staticmethod(required_action_label)  # type: ignore


if __name__ == "__main__":
    # Quick self-test
    sm = ApprovalStateMachine("test-001")
    print("Initial:", sm.status)
    sm.dry_run(rationale="Shadow mode default")
    print("After dry_run:", sm.status)
    sm.transition("queued", actor="system", rationale="Auto-queued from suggested")
    print("After queued:", sm.status)
    sm.verdict("approve", owner_identity="owner_42", rationale="Looks safe")
    print("After approve:", sm.status)
    sm.transition("executed", actor="system", rationale="Settlement complete")
    print("After executed:", sm.status)
    print("History:", len(sm.history), "entries")
    try:
        sm.transition("rejected", actor="system", rationale="Should fail")
    except ValueError as e:
        print("Expected rejection:", str(e))
