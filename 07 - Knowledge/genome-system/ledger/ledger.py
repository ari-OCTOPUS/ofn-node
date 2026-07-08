"""Append-only, tamper-evident event ledger (JSONL + SHA-256 hash chain).

The ledger is the ONLY shared memory in the system. Every observation, metric,
proposal, approval and applied change is written here as exactly one JSON object
per line. Records are never mutated or deleted in place. Each record stores the
hash of the previous record, so any silent edit to history breaks the chain and
is detected by `verify()`.

Concurrency: multiple agents (a live watcher, a scheduled run, a backup) may
append at the same time. `append()` takes a best-effort cross-process lock and
re-reads the true tail hash from disk before writing, so concurrent appends
chain correctly instead of forking. The lock NEVER hangs -- on a filesystem that
forbids the lock it degrades to unlocked, and chain-correctness then rests on the
disk re-read. Readers tolerate a torn last line (from a crash mid-write).

v0.4.5 (LANGAR arrow, Octopus P-Chrono-4, 2026-07-08): every record now carries
`age_tick` + `is_human` (DataSchemas.sql `langar_ledger` shape -- EXTENDS this
chain, no rival table). TINV-3 (ratified): `age_tick` advances by exactly +1
ONLY on a human append (`is_human=1`) and NEVER decreases; both fields are part
of the hashed body, so rewriting age history breaks the chain (= logical death).
Legacy records without these fields still verify (keys are conditionally hashed).

v0.4.6 (heart-driven arrow, owner re-ratify 2026-07-08): `age_tick` now advances on
a human append OR a heartbeat append (`beat=1`, emitted by the pacemaker every
CHRONO_AGE_PER_N_BEATS beats) -- the machine ages itself. Each new record carries an
`age_rule="heart"` tag; verify() applies the heart rule to tagged records and the
original TINV-3 rule to legacy (untagged) records, so pre-v0.4.6 history stays valid.

Dependency-free (Python 3.9+ standard library only).
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

EVENT_TYPES = {
    "OBSERVE", "INDEX", "METRIC", "PROPOSAL", "APPROVAL", "APPLY",
    "GENOME_CHANGE", "HEARTBEAT", "NOTE",
    # v0.4.4 (verdict V2 + آری 2026-07-07: append-only): money ground-truth events —
    # written ONLY by the reconcile job, never by agents (anti reward-hacking wall).
    "MONEY_ATTRIBUTION",
}

GENESIS = "0" * 64

# v0.4.6 (heart-driven arrow -- owner re-ratify 2026-07-08): regime tag stamped on
# every NEW record. Records WITHOUT this tag are legacy and keep the ratified TINV-3
# rule in verify() (only a human append moves the arrow), so history stays valid.
AGE_RULE_CURRENT = "heart"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


_THREAD_LOCKS: dict[str, threading.Lock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


def _thread_lock_for(lockpath: str) -> threading.Lock:
    with _THREAD_LOCKS_GUARD:
        lk = _THREAD_LOCKS.get(lockpath)
        if lk is None:
            lk = _THREAD_LOCKS[lockpath] = threading.Lock()
        return lk


class _AppendLock:
    """Two-layer append lock.

    Layer 1 (exact): a per-path threading.Lock shared by every Ledger instance
    in this process -- threads NEVER race each other, regardless of filesystem.
    (The live watcher + indexer run as threads of one process; the old
    file-lock-only design let a thread time out after 3s of fsync contention,
    proceed unlocked, and fork the chain -- the flaky review_test failure.)

    Layer 2 (best-effort): an O_EXCL sidecar for cross-PROCESS writers
    (scheduled run + backup). Never hangs: after `timeout` it proceeds
    unlocked; it self-heals a stale lock from a crashed process. Cross-process
    contention is rare and appends are short, so the long timeout is cheap
    insurance rather than a hot path."""

    def __init__(self, path: Path, timeout: float = 10.0, stale: float = 20.0) -> None:
        self.lockpath = str(path) + ".lock"
        self.timeout = timeout
        self.stale = stale
        self.fd: int | None = None
        self.tlock = _thread_lock_for(self.lockpath)

    def __enter__(self) -> "_AppendLock":
        self.tlock.acquire()
        start = time.monotonic()
        while time.monotonic() - start < self.timeout:
            try:
                self.fd = os.open(self.lockpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:  # break a stale lock from a dead process
                    if time.time() - os.path.getmtime(self.lockpath) > self.stale:
                        os.unlink(self.lockpath)
                        continue
                except OSError:
                    pass
                time.sleep(0.02)
            except OSError:
                return self  # locking unsupported here -> proceed unlocked
        return self          # timed out -> proceed unlocked (best-effort)

    def __exit__(self, *exc: Any) -> None:
        try:
            if self.fd is not None:
                try:
                    os.close(self.fd)
                except OSError:
                    pass
                try:
                    os.unlink(self.lockpath)
                except OSError:
                    pass
                self.fd = None
        finally:
            self.tlock.release()


@dataclass
class Ledger:
    path: Path
    _last_hash: str = field(default=GENESIS, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._last_hash_from_disk()

    def _last_hash_from_disk(self) -> str:
        return self._tail_from_disk()[0]

    def _tail_from_disk(self) -> tuple[str, int]:
        """(last_hash, last_age_tick) in one pass. Legacy records without
        `age_tick` leave the age unchanged (age starts at 0 -- TINV-3)."""
        if not self.path.exists():
            return GENESIS, 0
        last, age = GENESIS, 0
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue  # tolerate a torn line
                    last = rec.get("hash", last)
                    if isinstance(rec.get("age_tick"), int):
                        age = max(age, rec["age_tick"])  # arrow never decreases
        except OSError:
            return GENESIS, 0
        return last, age

    def last_hash(self) -> str:
        """Cheap in-memory chain head (for per-beat light checkpoints -- F14:
        no full re-scan on the hot path; cross-process truth is re-read under
        the append lock)."""
        return self._last_hash

    def last_age_tick(self) -> int:
        """Current value of the mortal arrow (disk truth)."""
        return self._tail_from_disk()[1]

    def append(self, event_type: str, payload: dict[str, Any] | None = None,
               actor: str = "system", *, is_human: bool = False,
               beat: bool = False, **meta: Any) -> dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise ValueError(
                f"unknown event_type {event_type!r}; allowed: {sorted(EVENT_TYPES)}")
        with _AppendLock(self.path):
            prev, prev_age = self._tail_from_disk()     # true tail, under lock
            # v0.4.6: the mortal arrow is heart-driven -- it advances +1 on a human
            # append OR a heartbeat append (`beat=1`); every other append carries the
            # age but does not move it. (Owner re-ratified TINV-3 on 2026-07-08.)
            advances = is_human or beat
            age = prev_age + 1 if advances else prev_age
            body = {
                "id": uuid.uuid4().hex, "ts": _utcnow(), "type": event_type,
                "actor": actor, "payload": payload or {}, "meta": meta, "prev": prev,
                "age_tick": age, "is_human": 1 if is_human else 0,
                "age_rule": AGE_RULE_CURRENT, "beat": 1 if beat else 0,
            }
            digest = hashlib.sha256(_canonical(body)).hexdigest()
            record = {**body, "hash": digest}
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            self._last_hash = digest
        return record

    def iter_events(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue  # tolerate a torn/corrupt line rather than crash readers

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

    def verify(self) -> tuple[bool, str]:
        prev = GENESIS
        prev_age = 0
        for i, rec in enumerate(self.iter_events(), 1):
            body = {k: rec[k] for k in
                    ("id", "ts", "type", "actor", "payload", "meta", "prev",
                     "age_tick", "is_human", "age_rule", "beat")
                    if k in rec}
            recomputed = hashlib.sha256(_canonical(body)).hexdigest()
            if rec.get("prev") != prev:
                return False, f"chain break at record {i}: prev mismatch"
            if rec.get("hash") != recomputed:
                return False, f"tamper detected at record {i}: hash mismatch"
            # The mortal arrow never decreases. Which appends may move it depends on
            # the record's regime tag: legacy records (no `age_rule`) keep ratified
            # TINV-3 (only a human append); v0.4.6 `age_rule="heart"` records advance
            # on a human OR heartbeat (`beat=1`) append -- owner re-ratify 2026-07-08.
            if "age_tick" in rec:
                age = rec["age_tick"]
                if not isinstance(age, int) or age < prev_age:
                    return False, f"age reversal at record {i}: {age} < {prev_age}"
                if rec.get("age_rule") == "heart":
                    advances = rec.get("is_human") == 1 or rec.get("beat") == 1
                    if advances:
                        if age != prev_age + 1:
                            return False, (f"age-advancing append at record {i} must "
                                           f"advance age by exactly 1 ({prev_age} -> {age})")
                    elif age != prev_age:
                        return False, (f"non-advancing append at record {i} moved the "
                                       f"arrow ({prev_age} -> {age}) — heart-rule")
                elif rec.get("is_human") == 1:
                    if age != prev_age + 1:
                        return False, (f"human append at record {i} must advance "
                                       f"age by exactly 1 ({prev_age} -> {age})")
                elif age != prev_age:
                    return False, (f"non-human append at record {i} moved the "
                                   f"arrow ({prev_age} -> {age}) — TINV-3")
                prev_age = age
            prev = rec["hash"]
        return True, "ok"


if __name__ == "__main__":
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
