#!/usr/bin/env python3
"""audit_chain.py -- Tamper-evident audit ledger with hash-chain (EQUIP G8).

Each audit entry includes a hash of the previous entry, creating a chain
where tampering with any entry invalidates all subsequent entries.

Design:
  - Each entry: {seq, ts, event, actor, action_id, risk_tier, decision,
                 details_hash, prev_hash, entry_hash}
  - entry_hash = SHA256(seq + ts + event + ... + prev_hash)
  - Verification: walk chain forward, recompute each hash, detect any mismatch
  - Append-only: entries are never modified, only appended
  - Fail-closed: verification failure = chain tampered

$0 | stdlib-only | no network | SHA256 hash chain
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "audit-chain.v1"


def _hash_entry(seq: int, ts: str, event: str, actor: str,
                action_id: str, risk_tier: str, decision: str,
                details_hash: str, prev_hash: str) -> str:
    """Compute the hash for an audit entry."""
    payload = f"{seq}|{ts}|{event}|{actor}|{action_id}|{risk_tier}|{decision}|{details_hash}|{prev_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _hash_details(details: dict) -> str:
    """Hash the details dict to keep entry size bounded."""
    raw = json.dumps(details, sort_keys=True, separators=(",", ":"),
                     default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


GENESIS_HASH = "0" * 32  # prev_hash for the first entry


@dataclass
class AuditEntry:
    """A single audit entry in the tamper-evident chain."""
    seq: int
    ts: str
    event: str           # "action_evaluated", "approval_issued", "kill_activated", etc.
    actor: str           # agent_id or "system"
    action_id: str
    risk_tier: str       # "read_only", "reversible_write", "irreversible", "financial"
    decision: str         # "ALLOW", "DENY", "ESCALATE", "KILL"
    details_hash: str
    prev_hash: str
    entry_hash: str

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "seq": self.seq,
            "ts": self.ts,
            "event": self.event,
            "actor": self.actor,
            "action_id": self.action_id,
            "risk_tier": self.risk_tier,
            "decision": self.decision,
            "details_hash": self.details_hash,
            "prev_hash": self.prev_hash,
            "entry_hash": self.entry_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuditEntry":
        return cls(
            seq=int(d.get("seq", 0)),
            ts=str(d.get("ts", "")),
            event=str(d.get("event", "")),
            actor=str(d.get("actor", "")),
            action_id=str(d.get("action_id", "")),
            risk_tier=str(d.get("risk_tier", "")),
            decision=str(d.get("decision", "")),
            details_hash=str(d.get("details_hash", "")),
            prev_hash=str(d.get("prev_hash", "")),
            entry_hash=str(d.get("entry_hash", "")),
        )


class AuditChain:
    """In-memory tamper-evident audit ledger.

    For production, entries should be flushed to append-only JSONL file.
    The chain structure allows detection of any tampering.
    """

    def __init__(self, entries: list[AuditEntry] | None = None):
        self._entries: list[AuditEntry] = list(entries or [])
        self._details_store: dict[int, dict] = {}
        self._used_nonces: set[str] = set()

    @property
    def head(self) -> str:
        """Hash of the last entry (or genesis hash if empty)."""
        if not self._entries:
            return GENESIS_HASH
        return self._entries[-1].entry_hash

    @property
    def length(self) -> int:
        return len(self._entries)

    def append(self, event: str, actor: str, action_id: str,
               risk_tier: str, decision: str,
               details: dict | None = None) -> AuditEntry:
        """Append a new entry to the chain.

        Args:
            event: Event type (e.g., "action_evaluated")
            actor: Who triggered the event (agent_id or "system")
            action_id: Action identifier
            risk_tier: Risk tier of the action
            decision: Decision made (ALLOW/DENY/ESCALATE/KILL)
            details: Optional details dict (stored separately, only hash in chain)

        Returns:
            The newly created AuditEntry
        """
        seq = len(self._entries) + 1
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        prev = self.head
        det_hash = _hash_details(details or {})
        entry_hash = _hash_entry(seq, ts, event, actor, action_id,
                                 risk_tier, decision, det_hash, prev)
        entry = AuditEntry(
            seq=seq, ts=ts, event=event, actor=actor,
            action_id=action_id, risk_tier=risk_tier, decision=decision,
            details_hash=det_hash, prev_hash=prev, entry_hash=entry_hash,
        )
        self._entries.append(entry)
        if details:
            self._details_store[seq] = details
        return entry

    def verify(self) -> dict:
        """Verify the integrity of the entire chain.

        Returns:
            {valid: bool, entries_checked: int, first_invalid_seq: int | None, reason: str}
        """
        if not self._entries:
            return {"valid": True, "entries_checked": 0,
                    "first_invalid_seq": None, "reason": "empty_chain"}

        prev_hash = GENESIS_HASH
        for i, entry in enumerate(self._entries):
            # Check sequence ordering
            if entry.seq != i + 1:
                return {"valid": False, "entries_checked": i,
                        "first_invalid_seq": entry.seq,
                        "reason": f"sequence_gap:expected={i+1},got={entry.seq}"}

            # Check prev_hash linkage
            if entry.prev_hash != prev_hash:
                return {"valid": False, "entries_checked": i,
                        "first_invalid_seq": entry.seq,
                        "reason": f"prev_hash_mismatch:entry={entry.seq}"}

            # Recompute and verify entry hash
            expected = _hash_entry(
                entry.seq, entry.ts, entry.event, entry.actor,
                entry.action_id, entry.risk_tier, entry.decision,
                entry.details_hash, entry.prev_hash)
            if entry.entry_hash != expected:
                return {"valid": False, "entries_checked": i,
                        "first_invalid_seq": entry.seq,
                        "reason": f"entry_hash_mismatch:entry={entry.seq}"}

            prev_hash = entry.entry_hash

        return {"valid": True, "entries_checked": len(self._entries),
                "first_invalid_seq": None, "reason": "chain_intact"}

    def entries(self) -> list[AuditEntry]:
        """Return all entries in order."""
        return list(self._entries)

    def to_jsonl(self) -> str:
        """Serialize chain to JSONL for persistence."""
        lines = []
        for e in self._entries:
            lines.append(json.dumps(e.to_dict(), ensure_ascii=False))
        return "\n".join(lines) + ("\n" if lines else "")

    @classmethod
    def from_jsonl(cls, data: str) -> "AuditChain":
        """Deserialize chain from JSONL."""
        entries = []
        for line in data.strip().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(AuditEntry.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Skip malformed entries (fail-open for loading,
                    # verification will catch gaps)
                    pass
        return cls(entries)


if __name__ == "__main__":
    # Demo
    chain = AuditChain()
    chain.append("action_evaluated", "worker-1", "act-001",
                 "read_only", "ALLOW", {"tool": "list_tree"})
    chain.append("action_evaluated", "worker-1", "act-002",
                 "irreversible", "DENY", {"tool": "deploy", "reason": "no_approval"})
    chain.append("kill_activated", "system", "kill-001",
                 "financial", "KILL", {"trigger": "owner_command"})

    print("Chain length:", chain.length)
    print("Verification:", chain.verify())
    print("\nJSONL:")
    print(chain.to_jsonl())

    # Tamper test
    chain._entries[1].decision = "ALLOW"  # tamper!
    print("\nAfter tampering:", chain.verify())
