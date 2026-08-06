"""Durable outbox: the only door out of the node.

Everything that reaches the world queues here first, and nothing leaves
without an approved decision. That is the structural reason a leg cannot act
on its own — not a rule it is asked to follow, but the absence of any other
exit.

The hard problem this solves is the one that shows up after a power cut: an
item was sent, the acknowledgement was never written, the box rebooted, and
now the queue wants to send it again. A customer receiving the same quote
twice is a real cost, so:

  * `idempotency_key` is UNIQUE. Enqueueing the same logical action twice is
    a no-op, not a duplicate.
  * Sending is a two-phase move — `claim()` marks in-flight with an attempt
    count, `mark_sent()` finalises. A crash between them leaves the item
    visibly in-flight rather than silently pending.
  * Recovery is explicit: `recover_stale()` decides what to do with items
    that were in-flight when the lights went out. It defaults to *not*
    resending, because a missed message is recoverable by a human and a
    duplicate one is not.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from ..kernel.domain import RiskTier
from ..kernel.errors import FailClosedError
from ..kernel.tenancy import TenantScope
from .sqlite_base import Pool, apply_schema

PENDING = "pending"
IN_FLIGHT = "in_flight"
SENT = "sent"
HELD = "held"        # was in flight during a crash; needs a human to decide
FAILED = "failed"

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS outbox (
        idem_key    TEXT PRIMARY KEY,
        tenant      TEXT    NOT NULL,
        kind        TEXT    NOT NULL,
        payload     TEXT    NOT NULL,
        tier        TEXT    NOT NULL,
        status      TEXT    NOT NULL,
        attempts    INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT    NOT NULL,
        updated_at  TEXT    NOT NULL,
        note        TEXT    NOT NULL DEFAULT ''
    )
    """,
    "CREATE INDEX IF NOT EXISTS outbox_queue ON outbox (tenant, status, created_at)",
)


@dataclass(frozen=True)
class OutboxItem:
    idem_key: str
    tenant: str
    kind: str
    payload: Mapping[str, object]
    tier: RiskTier
    status: str
    attempts: int
    created_at: str
    updated_at: str
    note: str


class Outbox:
    """Tenant-scoped, idempotent, crash-safe."""

    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA)

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        """This thread's connection. See `Pool` for why it is per-thread."""
        return self._pool.conn

    # ── enqueue ───────────────────────────────────────────────────────────
    def enqueue(self, scope: TenantScope, idem_key: str, kind: str,
                payload: Mapping[str, object], tier: RiskTier,
                now_iso: str) -> bool:
        """Queue an item. Returns False if this key was already queued.

        Idempotency is enforced by the primary key rather than a read-then-
        insert check, so two callers racing on the same key cannot both win.
        """
        if not idem_key:
            raise FailClosedError("idempotency key is required")
        scoped = f"{scope.tenant.value}:{idem_key}"
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "INSERT INTO outbox (idem_key, tenant, kind, payload, tier,"
                " status, attempts, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (scoped, scope.tenant.value, kind,
                 json.dumps(payload, ensure_ascii=False, sort_keys=True),
                 tier.value, PENDING, now_iso, now_iso))
            self._conn.execute("COMMIT")
            return True
        except Exception as exc:
            self._conn.execute("ROLLBACK")
            if "UNIQUE" in str(exc) or "PRIMARY KEY" in str(exc):
                return False
            raise

    # ── send lifecycle ────────────────────────────────────────────────────
    def pending(self, scope: TenantScope, limit: int = 50) -> Sequence[OutboxItem]:
        rows = self._conn.execute(
            "SELECT * FROM outbox WHERE tenant = ? AND status = ?"
            " ORDER BY created_at ASC LIMIT ?",
            (scope.tenant.value, PENDING, limit)).fetchall()
        return [self._to_item(r) for r in rows]

    def claim(self, scope: TenantScope, idem_key: str, now_iso: str) -> bool:
        """Move pending -> in_flight and bump the attempt count.

        The status guard in the WHERE clause is what makes this safe against
        two senders: exactly one UPDATE matches, the other gets rowcount 0.
        """
        scoped = f"{scope.tenant.value}:{idem_key}"
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE outbox SET status = ?, attempts = attempts + 1,"
                " updated_at = ? WHERE idem_key = ? AND tenant = ? AND status = ?",
                (IN_FLIGHT, now_iso, scoped, scope.tenant.value, PENDING))
            self._conn.execute("COMMIT")
            return cur.rowcount == 1
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def mark_sent(self, scope: TenantScope, idem_key: str, now_iso: str) -> None:
        self._set_status(scope, idem_key, SENT, now_iso)

    def mark_failed(self, scope: TenantScope, idem_key: str, now_iso: str,
                    note: str = "") -> None:
        self._set_status(scope, idem_key, FAILED, now_iso, note)

    def _set_status(self, scope: TenantScope, idem_key: str, status: str,
                    now_iso: str, note: str = "") -> None:
        scoped = f"{scope.tenant.value}:{idem_key}"
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "UPDATE outbox SET status = ?, updated_at = ?, note = ?"
                " WHERE idem_key = ? AND tenant = ?",
                (status, now_iso, note, scoped, scope.tenant.value))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ── crash recovery ────────────────────────────────────────────────────
    def recover_stale(self, now_iso: str, *, resend: bool = False) -> int:
        """Deal with items that were in flight when the process died.

        Default is to HOLD, not resend. We cannot know whether the send
        completed before the crash — the acknowledgement is exactly what we
        lost. Holding turns an unknowable into a decision a human makes with
        context; resending turns it into a duplicate the customer sees.

        `resend=True` exists for transports that are genuinely idempotent on
        the receiving side, and should be enabled per-transport, never globally.
        """
        target = PENDING if resend else HELD
        note = ("re-queued after restart" if resend else
                "was in flight during shutdown — send status unknown, "
                "needs human decision")
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE outbox SET status = ?, updated_at = ?, note = ?"
                " WHERE status = ?", (target, now_iso, note, IN_FLIGHT))
            self._conn.execute("COMMIT")
            return cur.rowcount
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def held(self, scope: TenantScope, limit: int = 50) -> Sequence[OutboxItem]:
        """Held decisions, oldest first and bounded like the pending queue.

        The owner surface used to read every held row.  A caller cannot choose
        this limit, but an incident can still produce enough rows to turn one
        dashboard refresh into an unbounded database read.  The count remains
        available separately; this method is only the bounded item projection.
        """
        rows = self._conn.execute(
            "SELECT * FROM outbox WHERE tenant = ? AND status = ?"
            " ORDER BY created_at ASC LIMIT ?",
            (scope.tenant.value, HELD, max(0, int(limit)))).fetchall()
        return [self._to_item(r) for r in rows]

    def actionable_counts(self, scope: TenantScope) -> Mapping[str, object]:
        """Exact counts for the human-decision queue, without reading payloads.

        `pending()` and `held()` are deliberately bounded lists.  Deriving the
        summary from those lists would quietly under-count a large incident, so
        the aggregate is a separate SQL count over the complete queue.
        """
        rows = self._conn.execute(
            "SELECT status, tier, COUNT(*) AS n FROM outbox "
            "WHERE tenant = ? AND status IN (?, ?) GROUP BY status, tier",
            (scope.tenant.value, PENDING, HELD),
        ).fetchall()
        by_state = {PENDING: 0, HELD: 0}
        by_tier = {tier.value: 0 for tier in RiskTier}
        for row in rows:
            n = int(row["n"])
            by_state[row["status"]] = by_state.get(row["status"], 0) + n
            by_tier[row["tier"]] = by_tier.get(row["tier"], 0) + n
        return {"by_state": by_state, "by_tier": by_tier}

    def get(self, scope: TenantScope, idem_key: str) -> OutboxItem | None:
        row = self._conn.execute(
            "SELECT * FROM outbox WHERE idem_key = ? AND tenant = ?",
            (f"{scope.tenant.value}:{idem_key}", scope.tenant.value)).fetchone()
        return self._to_item(row) if row else None

    def counts(self, scope: TenantScope) -> Mapping[str, int]:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM outbox WHERE tenant = ?"
            " GROUP BY status", (scope.tenant.value,)).fetchall()
        return {r["status"]: int(r["n"]) for r in rows}

    @staticmethod
    def _to_item(row) -> OutboxItem:
        return OutboxItem(
            idem_key=row["idem_key"], tenant=row["tenant"], kind=row["kind"],
            payload=json.loads(row["payload"]), tier=RiskTier(row["tier"]),
            status=row["status"], attempts=row["attempts"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            note=row["note"],
        )
