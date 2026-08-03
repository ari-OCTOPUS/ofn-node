"""SQLite stores (stdlib sqlite3). Phase 2 adds a Postgres twin behind the same ports.

Concurrency notes (the two real bug classes from the v0.1 review live here):

- Optimistic lock: budget writes go through a single UPDATE guarded by
  `WHERE version = ?`; rowcount 0 means someone else won the race and the
  caller gets ConcurrencyConflictError. Never read-modify-write in two steps.
- TOCTOU: the ledger append computes seq/prev_hash and inserts inside one
  IMMEDIATE transaction, and the events table has UNIQUE(seq) so even a bug
  upstream cannot silently fork history.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Mapping, Sequence

from ...kernel.domain import BudgetState, Money
from ...kernel.errors import ConcurrencyConflictError, LedgerIntegrityError
from ...kernel.events import GENESIS_HASH, EventKind, LedgerEvent, compute_hash

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger_events (
    seq        INTEGER NOT NULL UNIQUE,
    ts         TEXT    NOT NULL,
    kind       TEXT    NOT NULL,
    payload    TEXT    NOT NULL,
    prev_hash  TEXT    NOT NULL,
    hash       TEXT    NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS budget_state (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    cap_cents  INTEGER NOT NULL,
    committed  INTEGER NOT NULL,
    currency   TEXT    NOT NULL,
    version    INTEGER NOT NULL
);
"""


def _connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class SqliteLedgerStore:
    def __init__(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = _connect(path)
        self._lock = threading.Lock()
        with self._conn:
            self._conn.executescript(_SCHEMA)

    def append(self, ts: str, kind: EventKind, payload: Mapping[str, object]) -> LedgerEvent:
        body = dict(payload)
        with self._lock, self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            row = self._conn.execute(
                "SELECT seq, hash FROM ledger_events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            seq = 0 if row is None else row[0] + 1
            prev_hash = GENESIS_HASH if row is None else row[1]
            digest = compute_hash(seq, ts, kind, body, prev_hash)
            self._conn.execute(
                "INSERT INTO ledger_events (seq, ts, kind, payload, prev_hash, hash) VALUES (?, ?, ?, ?, ?, ?)",
                (seq, ts, kind.value, json.dumps(body, sort_keys=True, ensure_ascii=False), prev_hash, digest),
            )
        return LedgerEvent(seq=seq, ts=ts, kind=kind, payload=body, prev_hash=prev_hash, hash=digest)

    def read_all(self) -> Sequence[LedgerEvent]:
        # The lock also serializes reads: a sqlite3 connection resets pending
        # cursors on commit/rollback, so unsynchronized cross-thread reads can
        # observe truncated results.
        with self._lock:
            rows = self._conn.execute(
                "SELECT seq, ts, kind, payload, prev_hash, hash FROM ledger_events ORDER BY seq"
            ).fetchall()
        return tuple(
            LedgerEvent(
                seq=r[0], ts=r[1], kind=EventKind(r[2]), payload=json.loads(r[3]),
                prev_hash=r[4], hash=r[5],
            )
            for r in rows
        )

    def head(self) -> LedgerEvent | None:
        events = self.read_all()
        return events[-1] if events else None

    def close(self) -> None:
        self._conn.close()


class SqliteBudgetStore:
    def __init__(self, path: str | Path, initial: BudgetState) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = _connect(path)
        self._lock = threading.Lock()
        with self._conn:
            self._conn.executescript(_SCHEMA)
            row = self._conn.execute("SELECT id FROM budget_state WHERE id = 1").fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO budget_state (id, cap_cents, committed, currency, version) VALUES (1, ?, ?, ?, ?)",
                    (initial.cap.cents, initial.committed.cents, initial.cap.currency, initial.version),
                )

    def get(self) -> BudgetState:
        with self._lock:
            row = self._conn.execute(
                "SELECT cap_cents, committed, currency, version FROM budget_state WHERE id = 1"
            ).fetchone()
        if row is None:
            raise LedgerIntegrityError("budget_state row missing")
        return BudgetState(
            cap=Money(row[0], row[2]),
            committed=Money(row[1], row[2]),
            version=row[3],
        )

    def compare_and_swap(self, expected_version: int, new_state: BudgetState) -> None:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "UPDATE budget_state SET cap_cents = ?, committed = ?, currency = ?, version = ? "
                "WHERE id = 1 AND version = ?",
                (
                    new_state.cap.cents,
                    new_state.committed.cents,
                    new_state.cap.currency,
                    new_state.version,
                    expected_version,
                ),
            )
            if cursor.rowcount != 1:
                raise ConcurrencyConflictError(
                    f"stale version {expected_version}; re-read and retry"
                )

    def close(self) -> None:
        self._conn.close()
