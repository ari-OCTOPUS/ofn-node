"""Append-only, hash-chained ledger events (INV-5).

The ledger is the genome: the single source of truth. History is never
mutated; every event carries the hash of its predecessor so tampering or
truncation is detectable by `verify_chain`.
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .errors import LedgerIntegrityError

GENESIS_HASH = "0" * 64


class EventKind(enum.Enum):
    PROPOSAL = "proposal"
    VERDICT = "verdict"
    GRANT = "grant"
    SPEND = "spend"
    REVENUE = "revenue"
    SPAWN = "spawn"
    LIFECYCLE = "lifecycle"
    INCIDENT = "incident"
    KILL = "kill"
    RESUME = "resume"    # kill released by a human — the switch is reversible (INV-3)
    EPOCH = "epoch"      # epoch advanced; ledgered so the soma rebuilds it from the genome


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Deterministic serialization — the hashed representation of a payload."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class LedgerEvent:
    seq: int
    ts: str
    kind: EventKind
    payload: Mapping[str, Any]
    prev_hash: str
    hash: str


def compute_hash(seq: int, ts: str, kind: EventKind, payload: Mapping[str, Any], prev_hash: str) -> str:
    body = f"{seq}|{ts}|{kind.value}|{canonical_json(payload)}|{prev_hash}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def next_event(
    prev: LedgerEvent | None,
    ts: str,
    kind: EventKind,
    payload: Mapping[str, Any],
) -> LedgerEvent:
    """Build the successor event. Pure: the caller supplies the timestamp."""
    seq = 0 if prev is None else prev.seq + 1
    prev_hash = GENESIS_HASH if prev is None else prev.hash
    digest = compute_hash(seq, ts, kind, payload, prev_hash)
    return LedgerEvent(seq=seq, ts=ts, kind=kind, payload=payload, prev_hash=prev_hash, hash=digest)


def verify_chain(events: Iterable[LedgerEvent]) -> None:
    """Raise LedgerIntegrityError on the first broken link, gap, or forged hash."""
    prev: LedgerEvent | None = None
    for event in events:
        expected_seq = 0 if prev is None else prev.seq + 1
        if event.seq != expected_seq:
            raise LedgerIntegrityError(f"seq gap at {event.seq}, expected {expected_seq}")
        expected_prev = GENESIS_HASH if prev is None else prev.hash
        if event.prev_hash != expected_prev:
            raise LedgerIntegrityError(f"prev_hash mismatch at seq {event.seq}")
        recomputed = compute_hash(event.seq, event.ts, event.kind, event.payload, event.prev_hash)
        if recomputed != event.hash:
            raise LedgerIntegrityError(f"hash forged at seq {event.seq}")
        prev = event
