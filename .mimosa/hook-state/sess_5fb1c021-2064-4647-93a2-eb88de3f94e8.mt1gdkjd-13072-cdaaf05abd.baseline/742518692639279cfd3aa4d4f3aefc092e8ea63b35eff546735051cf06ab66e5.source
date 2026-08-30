"""Append-only, tamper-evident event ledger (JSONL + SHA-256 hash chain).

The ledger is the ONLY shared memory in the system. Every observation,
metric, proposal, approval and applied change is written here as exactly one
JSON object per line. Records are never mutated or deleted in place -- the
file is opened in append mode only. Each record stores the hash of the
previous record, so any silent edit to history breaks the chain and is
detected by `verify()`.

Why this shape (design rationale):
  * JSONL       -> greppable, diffable, git-friendly; one corrupt line does
                   not destroy the rest of the history; no server, no schema
                   migration, survives decades (open format = future-proof).
  * hash chain  -> cheap tamper-evidence for an audit trail without a DB.
  * append + fsync -> durability on a single laptop.

Dependency-free (Python 3.9+ standard library only). This is the Phase-0
"episodic memory" + audit substrate referenced by the 5-phase master prompt.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# Canonical event types. Keep this set SMALL and STABLE: it is part of the
# contract that the Doctor, Guardian and any reader rely on. Adding a type is
# a mutable-shell change; removing/renaming one is effectively a genome change.
EVENT_TYPES = {
    "OBSERVE",        # a file changed in the vault (from the watcher)
    "INDEX",          # a note was (re)indexed (from the indexer)
    "METRIC",         # a measured health metric (from perception/guardian)
    "PROPOSAL",       # an agent proposes a change -- PROPOSE-ONLY, never applied here
    "APPROVAL",       # the human owner approved a proposal
    "APPLY",          # an approved change was applied to the mutable shell
    "GENOME_CHANGE",  # a change to the invariant core (slow 72h two-key path)
    "HEARTBEAT",      # Guardian liveness / online-ness beacon
    "NOTE",           # free-form annotation
}

GENESIS = "0" * 64


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj: dict[str, Any]) -> bytes:
    """Stable serialization for hashing (sorted keys, no whitespace jitter)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


@dataclass
class Ledger:
    """Append-only JSONL ledger with a verifiable hash chain."""

    path: Path
    _last_hash: str = field(default=GENESIS, init=False)

    # --- lifecycle -------------------------------------------------------
    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self._last_hash = self._recover_last_hash()

    def _recover_last_hash(self) -> str:
        last = GENESIS
        for rec in self.iter_events():
            last = rec.get("hash", last)
        return last

    # --- write -----------------------------------------------------------
    def append(self, event_type: str, payload: dict[str, Any] | None = None,
               actor: str = "system", **meta: Any) -> dict[str, Any]:
        """Append one event. Returns the full record (including its hash).

        `actor` should name the agent, e.g. "guardian", "creativity",
        "doctor", "watcher", "owner". Unknown event types are rejected so a
        buggy agent cannot silently pollute the shared memory.
        """
        if event_type not in EVENT_TYPES:
            raise ValueError(
                f"unknown event_type {event_type!r}; allowed: {sorted(EVENT_TYPES)}"
            )
        body = {
            "id": uuid.uuid4().hex,
            "ts": _utcnow(),
            "type": event_type,
            "actor": actor,
            "payload": payload or {},
            "meta": meta,
            "prev": self._last_hash,
        }
        digest = hashlib.sha256(_canonical(body)).hexdigest()
        record = {**body, "hash": digest}
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._last_hash = digest
        return record

    # --- read ------------------------------------------------------------
    def iter_events(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:  # pragma: no cover
                    raise ValueError(f"corrupt ledger line {i}: {exc}") from exc

    def tail(self, n: int = 20) -> list[dict[str, Any]]:
        return list(self.iter_events())[-n:]

    def filter(self, event_type: str | None = None,
               actor: str | None = None) -> list[dict[str, Any]]:
        out = []
        for rec in self.iter_events():
            if event_type and rec.get("type") != event_type:
                continue
            if actor and rec.get("actor") != actor:
                continue
            out.append(rec)
        return out

    # --- integrity -------------------------------------------------------
    def verify(self) -> tuple[bool, str]:
        """Re-walk the chain. Returns (ok, message)."""
        prev = GENESIS
        for i, rec in enumerate(self.iter_events(), 1):
            body = {k: rec[k] for k in
                    ("id", "ts", "type", "actor", "payload", "meta", "prev")
                    if k in rec}
            recomputed = hashlib.sha256(_canonical(body)).hexdigest()
            if rec.get("prev") != prev:
                return False, f"chain break at record {i}: prev mismatch"
            if rec.get("hash") != recomputed:
                return False, f"tamper detected at record {i}: hash mismatch"
            prev = rec["hash"]
        return True, "ok"


if __name__ == "__main__":  # tiny CLI: python ledger.py <path> [tail|verify]
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else "ledger.jsonl"
    cmd = sys.argv[2] if len(sys.argv) > 2 else "tail"
    lg = Ledger(p)
    if cmd == "verify":
        ok, msg = lg.verify()
        print(("OK: " if ok else "FAIL: ") + msg)
        sys.exit(0 if ok else 1)
    for r in lg.tail(int(sys.argv[3]) if len(sys.argv) > 3 else 20):
        print(f"{r['ts']}  {r['type']:<13} {r['actor']:<10} {r['payload']}")
