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

import hashlib
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
# Operations-launch states (O1/O2): approval is decoupled from send. An
# approved item waits for a HUMAN to complete it manually; nothing claims
# it until a real sender exists (which it does not yet).
APPROVED_MANUAL = "approved_manual"
REJECTED = "rejected"
COMPLETED = "manual_completed"

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS outbox (
        tenant      TEXT    NOT NULL,
        idem_key    TEXT    NOT NULL,
        kind        TEXT    NOT NULL,
        payload     TEXT    NOT NULL,
        tier        TEXT    NOT NULL,
        status      TEXT    NOT NULL,
        attempts    INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT    NOT NULL,
        updated_at  TEXT    NOT NULL,
        note        TEXT    NOT NULL DEFAULT '',
        delivery_mode     TEXT    NOT NULL DEFAULT 'manual',
        approved_at       TEXT    NOT NULL DEFAULT '',
        approved_by       TEXT    NOT NULL DEFAULT '',
        completed_at      TEXT    NOT NULL DEFAULT '',
        completed_by      TEXT    NOT NULL DEFAULT '',
        completion_channel TEXT   NOT NULL DEFAULT '',
        packet_sha256     TEXT    NOT NULL DEFAULT '',
        external_ref_digest TEXT  NOT NULL DEFAULT '',
        PRIMARY KEY (tenant, idem_key)
    )
    """,
    "CREATE INDEX IF NOT EXISTS outbox_queue ON outbox (tenant, status, created_at)",
)

# Migration: add the manual-completion columns to files created before the
# operations-launch schema change. Idempotent: checks each column. The
# approved index is created HERE, after the columns exist — putting it in
# SCHEMA would make apply_schema run it before the migration on old files.

def _migrate_composite_pk(conn) -> None:
    """Rebuild legacy single-PK outbox files onto the composite key.

    Raw-key contract: every legacy row is copied 1:1. The tenant column
    already carries the tenant; the idem_key column already carries the
    key. No prefix stripping, no normalization, no collision detection.
    The composite PK (tenant, idem_key) provides uniqueness. A lossless
    verification (count + fingerprint) runs before the legacy table is
    dropped - if anything was lost in transit, boot fails with the exact
    counts and the legacy table preserved for manual recovery.
    """
    pk = [r["name"] for r in conn.execute("PRAGMA table_info(outbox)")
          if r["pk"] > 0]
    if pk and pk[0] == "idem_key" and len(pk) == 1:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(outbox)")]
        info = {r["name"]: r["type"] or "TEXT"
                for r in conn.execute("PRAGMA table_info(outbox)")}
        others = [c for c in cols if c not in ("tenant", "idem_key")]
        sel = ", ".join(["tenant", "idem_key"] + others)
        old_rows = conn.execute(
            f"SELECT {sel} FROM outbox").fetchall()
        # fingerprint before rebuild
        canon = json.dumps([dict(r) for r in old_rows],
                           sort_keys=True, ensure_ascii=False)
        before_fp = hashlib.sha256(canon.encode()).hexdigest()
        before_n = len(old_rows)
        conn.execute("ALTER TABLE outbox RENAME TO outbox_legacy")
        conn.execute(
            "CREATE TABLE outbox ("
            " tenant TEXT NOT NULL, idem_key TEXT NOT NULL"
            + "".join(f", {c} {info[c]}" for c in others)
            + ", PRIMARY KEY (tenant, idem_key))")
        for row in old_rows:
            d = dict(row)
            placeholders = ", ".join("?" for _ in d)
            conn.execute(
                f"INSERT INTO outbox ({', '.join(d)}) VALUES ({placeholders})",
                tuple(d.values()))
        new_rows = conn.execute("SELECT * FROM outbox").fetchall()
        new_canon = json.dumps([dict(r) for r in new_rows],
                               sort_keys=True, ensure_ascii=False)
        after_fp = hashlib.sha256(new_canon.encode()).hexdigest()
        after_n = len(new_rows)
        if after_n != before_n or after_fp != before_fp:
            conn.execute("DROP TABLE outbox")
            conn.execute("ALTER TABLE outbox_legacy RENAME TO outbox")
            raise FailClosedError(
                f"lossless-migration-check-failed: "
                f"before={before_n}, after={after_n}, "
                f"fp_before={before_fp[:12]}, fp_after={after_fp[:12]} - "
                "legacy table preserved; no DROP performed")
        conn.execute("DROP TABLE outbox_legacy")


def _migrate_manual_columns(conn) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(outbox)")}
    for col, ddl in (
        ("delivery_mode", "TEXT NOT NULL DEFAULT 'manual'"),
        ("approved_at", "TEXT NOT NULL DEFAULT ''"),
        ("approved_by", "TEXT NOT NULL DEFAULT ''"),
        ("completed_at", "TEXT NOT NULL DEFAULT ''"),
        ("completed_by", "TEXT NOT NULL DEFAULT ''"),
        ("completion_channel", "TEXT NOT NULL DEFAULT ''"),
        ("packet_sha256", "TEXT NOT NULL DEFAULT ''"),
        ("external_ref_digest", "TEXT NOT NULL DEFAULT ''"),
    ):
        if col not in cols:
            conn.execute(f"ALTER TABLE outbox ADD COLUMN {col} {ddl}")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS outbox_approved "
        "  ON outbox (tenant, status, approved_at)")


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
    delivery_mode: str = "manual"
    approved_at: str = ""
    approved_by: str = ""
    completed_at: str = ""
    completed_by: str = ""
    completion_channel: str = ""
    packet_sha256: str = ""
    external_ref_digest: str = ""


class Outbox:
    """Tenant-scoped, idempotent, crash-safe."""

    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA,
                     (_migrate_composite_pk, _migrate_manual_columns))

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
        # raw key: tenant lives in its own column; string composition created
        # the a:b:c collision class (tenant a + key b:c == tenant a:b + key c)
        scoped = idem_key
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
        # raw key: tenant lives in its own column; string composition created
        # the a:b:c collision class (tenant a + key b:c == tenant a:b + key c)
        scoped = idem_key
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
        """Finalise a send. Only valid from IN_FLIGHT — the two-phase move."""
        self._set_status(scope, idem_key, SENT, now_iso,
                         from_status=(IN_FLIGHT,))

    # ── manual lifecycle (operations launch O1/O2) ────────────────────────
    def approve_manual(self, scope: TenantScope, idem_key: str, now_iso: str,
                       approved_by: str = "") -> bool:
        """Approve for MANUAL delivery: pending → approved_manual.

        Deliberately NOT claim(): no sender exists, so in_flight would be a
        lie. The item waits in approved_manual until a human completes it.
        """
        # raw key: tenant lives in its own column; string composition created
        # the a:b:c collision class (tenant a + key b:c == tenant a:b + key c)
        scoped = idem_key
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE outbox SET status = ?, approved_at = ?,"
                " approved_by = ?, delivery_mode = 'manual',"
                " updated_at = ? WHERE idem_key = ? AND tenant = ?"
                " AND status = ?",
                (APPROVED_MANUAL, now_iso, approved_by[:80], now_iso,
                 scoped, scope.tenant.value, PENDING))
            self._conn.execute("COMMIT")
            return cur.rowcount == 1
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def reject(self, scope: TenantScope, idem_key: str, now_iso: str,
               note: str = "") -> bool:
        """Reject: any non-terminal state → rejected (fail-closed).

        Valid from pending or approved_manual (held/failed stay as they are;
        sent/completed are terminal and immutable).
        """
        # raw key: tenant lives in its own column; string composition created
        # the a:b:c collision class (tenant a + key b:c == tenant a:b + key c)
        scoped = idem_key
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE outbox SET status = ?, note = ?, updated_at = ?"
                " WHERE idem_key = ? AND tenant = ? AND status IN (?, ?)",
                (REJECTED, note, now_iso, scoped, scope.tenant.value,
                 PENDING, APPROVED_MANUAL))
            self._conn.execute("COMMIT")
            return cur.rowcount == 1
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def complete_manual(self, scope: TenantScope, idem_key: str, now_iso: str,
                        *, completed_by: str = "", channel: str = "",
                        packet_sha256: str = "",
                        external_ref_digest: str = "") -> bool:
        """Complete a manually delivered item: approved_manual → completed.

        Idempotent: a second completion of the same item is a no-op (returns
        False), never a duplicate effect.
        """
        # raw key: tenant lives in its own column; string composition created
        # the a:b:c collision class (tenant a + key b:c == tenant a:b + key c)
        scoped = idem_key
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self._conn.execute(
                "UPDATE outbox SET status = ?, completed_at = ?,"
                " completed_by = ?, completion_channel = ?,"
                " packet_sha256 = ?, external_ref_digest = ?,"
                " updated_at = ? WHERE idem_key = ? AND tenant = ?"
                " AND status = ?",
                (COMPLETED, now_iso, completed_by[:80], channel[:40],
                 packet_sha256[:64], external_ref_digest[:64], now_iso,
                 scoped, scope.tenant.value, APPROVED_MANUAL))
            self._conn.execute("COMMIT")
            return cur.rowcount == 1
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def approved_manual(self, scope: TenantScope,
                        limit: int = 50) -> Sequence[OutboxItem]:
        """Items approved and waiting for a human to complete them."""
        rows = self._conn.execute(
            "SELECT * FROM outbox WHERE tenant = ? AND status = ?"
            " ORDER BY approved_at ASC LIMIT ?",
            (scope.tenant.value, APPROVED_MANUAL, limit)).fetchall()
        return [self._to_item(r) for r in rows]

    def mark_failed(self, scope: TenantScope, idem_key: str, now_iso: str,
                    note: str = "") -> None:
        """Mark an item as failed. Valid from pending, held, or in_flight.

        Pending → failed is the owner-reject path (no claim needed).
        Held → failed is a manual decision on a crash-recovered item.
        In_flight → failed is a send that errored after claiming.
        """
        self._set_status(scope, idem_key, FAILED, now_iso, note,
                         from_status=(PENDING, HELD, IN_FLIGHT))

    def _set_status(self, scope: TenantScope, idem_key: str, status: str,
                    now_iso: str, note: str = "",
                    from_status: tuple[str, ...] | None = None) -> None:
        """Update status with an optional precondition on current state.

        `from_status` restricts which rows may be updated. If None, any row
        matching idem_key+tenant is updated (legacy behaviour, kept for
        recover_stale). When set, the UPDATE includes AND status IN (...)
        so a state transition that violates the two-phase contract silently
        affects zero rows rather than corrupting the queue.
        """
        # raw key: tenant lives in its own column; string composition created
        # the a:b:c collision class (tenant a + key b:c == tenant a:b + key c)
        scoped = idem_key
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            if from_status is not None:
                placeholders = ",".join("?" for _ in from_status)
                self._conn.execute(
                    f"UPDATE outbox SET status = ?, updated_at = ?, note = ?"
                    f" WHERE idem_key = ? AND tenant = ? AND status IN ({placeholders})",
                    (status, now_iso, note, scoped, scope.tenant.value,
                     *from_status))
            else:
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
            (idem_key, scope.tenant.value)).fetchone()
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
            delivery_mode=row["delivery_mode"],
            approved_at=row["approved_at"],
            approved_by=row["approved_by"],
            completed_at=row["completed_at"],
            completed_by=row["completed_by"],
            completion_channel=row["completion_channel"],
            packet_sha256=row["packet_sha256"],
            external_ref_digest=row["external_ref_digest"],
        )
