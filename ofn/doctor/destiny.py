#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""destiny — no proposal may exist without a destiny (owner directive LB).

Every proposal ends in EXACTLY ONE of four outcomes:
  PR_CREATED | QUEUED_WITH_REASON | REJECTED_WITH_REASON | ESCALATED_TO_OWNER

There is no PENDING state in the data model, and the append-only journal plus
fail-closed recovery guarantee a crash cannot strand a proposal mid-flight:
any STARTED record without DONE is recovered as ESCALATED_TO_OWNER
("interrupted_mid_flight") — an over-escalation is always safe, a silent
limbo never is.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path

from .receipts import canonical_json, sha256_text

__all__ = [
    "OUTCOMES", "FORBIDDEN_TARGETS", "SENSITIVE_MARKERS", "LANE_OWNED_PREFIXES",
    "Proposal", "Decision", "DestinyEngine", "InvalidProposalError",
]

OUTCOMES = ("PR_CREATED", "QUEUED_WITH_REASON", "REJECTED_WITH_REASON",
            "ESCALATED_TO_OWNER")

# contract.forbidden + patch_boundary + AGENTS.md §4/§5 surfaces. A proposal
# whose target matches may never become PR_CREATED.
FORBIDDEN_TARGETS = (
    ".github/workflows/", "CODEOWNERS", ".git/config", "branch-protection",
    "_ops/state/", ".env", "flags.cmd", "octopus-flags",
    "kill", "stop-organism", "secrets.env", "secret_rotation",
    "owner-key", "WAR24-LOCK",
)
SENSITIVE_MARKERS = (
    "workflow", "protection", "owner", "gate", "secret", "key", "policy",
    "budget", "constitution", "verifier", "ledger", "kill",
)
# Reversible machine PRs are confined to this lane's owned paths (SCOPE.md).
LANE_OWNED_PREFIXES = (
    "ofn/doctor/", "tests/test_doctor_lane_", "09-LANES/LB/",
)


class InvalidProposalError(ValueError):
    pass


@dataclass
class Proposal:
    id: str
    title: str
    target_path: str
    action: str                 # create | append | archive | code_change | ...
    reversible: bool
    evidence_refs: list[str] = field(default_factory=list)
    payload_path: str = ""      # prepared artifact (for QUEUED appends)

    def validate(self) -> None:
        if not self.id or not self.title.strip() or not self.target_path.strip():
            raise InvalidProposalError("id, title and target_path are required")
        if not self.evidence_refs:
            raise InvalidProposalError("a proposal without evidence is opinion, not a proposal")


@dataclass
class Decision:
    proposal_id: str
    outcome: str
    reason: str
    rule_trace: list[str] = field(default_factory=list)


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DestinyEngine:
    def __init__(self, journal_path: Path | str):
        self.journal_path = Path(journal_path)
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.journal_path.exists():
            self.journal_path.touch()
        self.recover()

    # --------------------------------------------------------------- journal
    def _journal(self, record: dict) -> None:
        record = {"ts": _utcnow(), **record}
        record["line_sha256"] = sha256_text(canonical_json(record))
        with open(self.journal_path, "a", encoding="utf-8") as fh:
            fh.write(canonical_json(record) + "\n")

    def _load(self) -> list[dict]:
        rows = []
        for raw in self.journal_path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                rows.append(json.loads(raw))
        return rows

    # ---------------------------------------------------------------- decide
    def decide(self, prop: Proposal) -> Decision:
        prop.validate()
        target = prop.target_path.replace("\\", "/").lower()
        trace: list[str] = []

        hit = next((f for f in FORBIDDEN_TARGETS if f.lower() in target), None)
        if hit:
            trace.append(f"forbidden_target:{hit}")
            return Decision(prop.id, "ESCALATED_TO_OWNER",
                            "target is a forbidden surface (contract.forbidden / "
                            "patch_boundary); incident recorded, no auto-retry", trace)
        if not prop.reversible:
            trace.append("irreversible")
            return Decision(prop.id, "ESCALATED_TO_OWNER",
                            "irreversible actions are never machine-decided", trace)
        if any(m in target for m in SENSITIVE_MARKERS):
            marker = next(m for m in SENSITIVE_MARKERS if m in target)
            trace.append(f"sensitive_marker:{marker}")
            return Decision(prop.id, "ESCALATED_TO_OWNER",
                            f"target carries sensitive marker '{marker}'; owner rules", trace)
        if target.startswith(LANE_OWNED_PREFIXES) and prop.action in ("create", "code_change"):
            trace.append("lane_owned_reversible_code")
            return Decision(prop.id, "PR_CREATED",
                            "reversible change inside lane-owned paths; PR is machine-"
                            "created, MERGE stays human", trace)
        # everything else = an append/artifact into shared or external surfaces
        trace.append("payload_instead_of_direct_write")
        return Decision(prop.id, "QUEUED_WITH_REASON",
                        "shared/external surface: prepared payload + proposed append "
                        f"location ({prop.payload_path or 'artifact under 09-LANES/LB/runs/'})",
                        trace)

    # ---------------------------------------------------------------- assign
    def assign(self, prop: Proposal, executor=None) -> Decision:
        """Journal STARTED → act → journal DONE. An invalid proposal is still a
        proposal: it gets REJECTED_WITH_REASON, never an unjournaled exception.
        A crash between STARTED and DONE is recovered on next engine load as
        ESCALATED_TO_OWNER (fail-closed)."""
        self._journal({"proposal_id": prop.id, "phase": "STARTED",
                       "target_path": prop.target_path, "action": prop.action})
        try:
            prop.validate()
        except InvalidProposalError as e:
            decision = Decision(prop.id, "REJECTED_WITH_REASON",
                                f"invalid proposal: {e}", ["validation_failed"])
            self._journal({"proposal_id": prop.id, "phase": "DONE",
                           "outcome": decision.outcome, "reason": decision.reason})
            return decision
        decision = self.decide(prop)
        self._journal({"proposal_id": prop.id, "phase": "STARTED",
                       "outcome_plan": decision.outcome,
                       "rule_trace": decision.rule_trace})
        error = ""
        if executor is not None and decision.outcome == "PR_CREATED":
            try:
                result = executor(prop)
                decision.reason += f" — executor: {result}"
            except Exception as e:                     # noqa: BLE001
                error = f"{type(e).__name__}: {e}"
                decision = Decision(prop.id, "ESCALATED_TO_OWNER",
                                    f"PR executor failed ({error}); escalated, not retried",
                                    decision.rule_trace + ["executor_failed"])
        self._journal({"proposal_id": prop.id, "phase": "DONE",
                       "outcome": decision.outcome, "reason": decision.reason})
        return decision

    # --------------------------------------------------------------- recover
    def recover(self) -> list[dict]:
        """Assign a fail-closed destiny to any proposal stuck mid-flight."""
        recovered = []
        state: dict[str, dict] = {}
        for row in self._load():
            pid = row.get("proposal_id")
            if row.get("phase") == "STARTED":
                state[pid] = row
            elif row.get("phase") == "DONE":
                state.pop(pid, None)
        for pid, row in state.items():
            self._journal({"proposal_id": pid, "phase": "DONE",
                           "outcome": "ESCALATED_TO_OWNER",
                           "reason": "interrupted_mid_flight: recovered fail-closed"})
            recovered.append({"proposal_id": pid, "outcome": "ESCALATED_TO_OWNER",
                              "original_plan": row.get("outcome_plan")})
        return recovered

    # ---------------------------------------------------------------- audit
    def outcomes(self) -> dict[str, str]:
        """proposal_id → final outcome (last DONE wins; no PENDING representable)."""
        out: dict[str, str] = {}
        for row in self._load():
            if row.get("phase") == "DONE":
                out[row["proposal_id"]] = row["outcome"]
        return out

    def orphan_count(self) -> int:
        started, done = set(), set()
        for row in self._load():
            if row.get("phase") == "STARTED":
                started.add(row["proposal_id"])
            elif row.get("phase") == "DONE":
                done.add(row["proposal_id"])
        return len(started - done)
