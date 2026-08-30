"""Append-only, hash-chained event ledger. One chain per tenant.

Why a chain and not just a table with timestamps: the ledger is the answer to
"why did the system do that?", and an answer nobody can verify is worth very
little. Each event commits to its predecessor, so any edit to history —
including one made directly in `sqlite3` — breaks verification at the exact
row it touched.

What this does NOT claim: it is not tamper-*proof*. Anyone with write access
can rewrite the whole chain from a given point. It is tamper-*evident*, which
is the achievable property on a device sitting in somebody's house, and it is
enough to distinguish "the software did this" from "someone edited the file".

Isolation: chains are per tenant and never interleaved. A leg reading its own
history cannot observe that another leg exists.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..kernel.domain import TenantId
from ..kernel.errors import FailClosedError, TenantIsolationError
from ..kernel.tenancy import TenantScope
from .sqlite_base import Pool, apply_schema

GENESIS = "0" * 64

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS ledger (
        tenant     TEXT    NOT NULL,
        seq        INTEGER NOT NULL,
        ts         TEXT    NOT NULL,
        kind       TEXT    NOT NULL,
        payload    TEXT    NOT NULL,
        prev_hash  TEXT    NOT NULL,
        hash       TEXT    NOT NULL,
        PRIMARY KEY (tenant, seq)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ledger_tenant_seq ON ledger (tenant, seq DESC)",
    # A tenant may not have two events at the same position. Enforced by the
    # primary key above; stated again here because it is the anti-fork rule.
)


def canonical(payload: Mapping[str, object]) -> str:
    """Deterministic JSON. Two runs must produce byte-identical output or the
    chain is not reproducible and verification means nothing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def event_hash(prev_hash: str, tenant: str, seq: int, ts: str, kind: str,
               payload_json: str) -> str:
    """Commit to everything that identifies the event, not just its body.

    `tenant` and `seq` are inside the digest deliberately: without them a row
    could be lifted from one tenant's chain and replayed into another's at a
    different position while still verifying.
    """
    h = hashlib.sha256()
    for part in (prev_hash, tenant, str(seq), ts, kind, payload_json):
        h.update(part.encode("utf-8"))
        h.update(b"\x1f")     # unit separator: prevents field-boundary ambiguity
    return h.hexdigest()


@dataclass(frozen=True)
class Event:
    tenant: str
    seq: int
    ts: str
    kind: str
    payload: Mapping[str, object]
    prev_hash: str
    hash: str


class Ledger:
    """Append-only event log with a verifiable chain per tenant."""

    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── writing ───────────────────────────────────────────────────────────
    def append(self, scope: TenantScope, kind: str,
               payload: Mapping[str, object], ts: str) -> Event:
        """Add one event to this tenant's chain.

        The read of the head and the write of the successor happen inside a
        single IMMEDIATE transaction. Splitting them would allow two writers
        to derive the same `seq` from the same head and fork the chain — the
        classic read-then-write race, which on a three-leg node is not
        hypothetical.
        """
        if not kind:
            raise FailClosedError("event kind is required")
        tenant = scope.tenant.value
        body = canonical(payload)

        self._conn.execute("BEGIN IMMEDIATE")
        try:
            row = self._conn.execute(
                "SELECT seq, hash FROM ledger WHERE tenant = ? "
                "ORDER BY seq DESC LIMIT 1", (tenant,)).fetchone()
            seq = (row["seq"] + 1) if row else 1
            prev = row["hash"] if row else GENESIS
            digest = event_hash(prev, tenant, seq, ts, kind, body)
            self._conn.execute(
                "INSERT INTO ledger (tenant, seq, ts, kind, payload, prev_hash, hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tenant, seq, ts, kind, body, prev, digest))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

        return Event(tenant, seq, ts, kind, dict(payload), prev, digest)

    # ── reading ───────────────────────────────────────────────────────────
    def read(self, scope: TenantScope, limit: int = 100) -> Sequence[Event]:
        """Most recent events for this tenant only."""
        rows = self._conn.execute(
            "SELECT * FROM ledger WHERE tenant = ? ORDER BY seq DESC LIMIT ?",
            (scope.tenant.value, limit)).fetchall()
        return [self._row_to_event(r) for r in rows]

    def head(self, scope: TenantScope) -> Event | None:
        got = self.read(scope, limit=1)
        return got[0] if got else None

    def count(self, scope: TenantScope) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM ledger WHERE tenant = ?",
            (scope.tenant.value,)).fetchone()
        return int(row["n"])

    @staticmethod
    def _row_to_event(r: sqlite3.Row) -> Event:
        return Event(r["tenant"], r["seq"], r["ts"], r["kind"],
                     json.loads(r["payload"]), r["prev_hash"], r["hash"])

    # ── verification ──────────────────────────────────────────────────────
    def verify(self, scope: TenantScope) -> tuple[bool, str]:
        """Recompute the whole chain. Returns (ok, human-readable reason).

        Returns the *first* break rather than a count, because after the first
        break everything downstream is unverifiable anyway and reporting 400
        broken events hides which one was actually edited.
        """
        tenant = scope.tenant.value
        rows = self._conn.execute(
            "SELECT * FROM ledger WHERE tenant = ? ORDER BY seq ASC",
            (tenant,)).fetchall()
        prev = GENESIS
        expected_seq = 1
        for r in rows:
            if r["seq"] != expected_seq:
                return False, (f"sequence gap at {expected_seq}: found {r['seq']} "
                               f"— events were deleted or reordered")
            if r["prev_hash"] != prev:
                return False, f"broken link at seq {r['seq']}: prev_hash mismatch"
            digest = event_hash(prev, tenant, r["seq"], r["ts"], r["kind"],
                                r["payload"])
            if digest != r["hash"]:
                return False, (f"content edited at seq {r['seq']}: "
                               f"recomputed hash does not match stored hash")
            prev = r["hash"]
            expected_seq += 1
        return True, f"chain verified: {len(rows)} events"

    def verify_all(self, tenants: Sequence[TenantId]) -> Mapping[str, tuple[bool, str]]:
        return {t.value: self.verify(TenantScope(t)) for t in tenants}
