"""Durable marketing inbox: where inbound webhook payloads land before processing.

Design mirrors the outbox pattern: SQLite via Pool, idempotent inserts, crash-
safe states, and tenant-scoped queries. The inbox is the only place inbound
vendor data is stored — nothing from a webhook touches the ledger, the facts,
or the outbox without passing through here first.

States:
  pending   — arrived, not yet processed
  processed — successfully normalised and stored
  failed    — processing error (kept for debugging, not retried automatically)

The inbox is NOT a queue to be drained. Items are processed in-order by the
connector loop, but the inbox itself is an append-only log with status updates.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Mapping, Sequence

from .sqlite_base import Pool, apply_schema

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS marketing_inbox (
        inbox_id        TEXT PRIMARY KEY,
        tenant          TEXT    NOT NULL,
        connector_id    TEXT    NOT NULL,
        vendor          TEXT    NOT NULL,
        event_type      TEXT    NOT NULL DEFAULT '',
        vendor_event_id TEXT    NOT NULL DEFAULT '',
        correlation_id  TEXT    NOT NULL DEFAULT '',
        body_sha256     TEXT    NOT NULL DEFAULT '',
        body_size       INTEGER NOT NULL DEFAULT 0,
        status          TEXT    NOT NULL DEFAULT 'pending',
        attempts        INTEGER NOT NULL DEFAULT 0,
        error_note      TEXT    NOT NULL DEFAULT '',
        received_at     TEXT    NOT NULL,
        processed_at    TEXT    NOT NULL DEFAULT '',
        claimed_at      TEXT    NOT NULL DEFAULT '',
        UNIQUE(tenant, vendor_event_id, connector_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS inbox_pending "
    "  ON marketing_inbox (tenant, status, received_at)",
)

# Migration: rename raw_body → body_sha256 + body_size for files created
# before this schema change. Runs on every boot and must be idempotent.
def _migrate_raw_body_to_hash(conn) -> None:
    cols = {r[1]: r[2] for r in conn.execute("PRAGMA table_info(marketing_inbox)")}
    if "raw_body" in cols and "body_sha256" not in cols:
        # Old schema: rename raw_body, add hash + size columns.
        # We cannot recover the original bytes after this rename, so old
        # payloads get an empty hash and their size is lost. New payloads
        # arrive with a real hash from the start.
        conn.execute("ALTER TABLE marketing_inbox RENAME COLUMN raw_body TO _raw_body_deprecated")
        conn.execute("ALTER TABLE marketing_inbox ADD COLUMN body_sha256 TEXT NOT NULL DEFAULT ''")
        conn.execute("ALTER TABLE marketing_inbox ADD COLUMN body_size INTEGER NOT NULL DEFAULT 0")


def _migrate_claimed_at(conn) -> None:
    """Add claimed_at for the claim/recover state machine."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(marketing_inbox)")}
    if "claimed_at" not in cols:
        conn.execute("ALTER TABLE marketing_inbox ADD COLUMN claimed_at TEXT NOT NULL DEFAULT ''")

PENDING = "pending"
PROCESSING = "processing"
PROCESSED = "processed"
FAILED = "failed"
HELD = "held"


@dataclass(frozen=True)
class InboxItem:
    inbox_id: str
    tenant: str
    connector_id: str
    vendor: str
    event_type: str
    vendor_event_id: str
    correlation_id: str
    body_sha256: str
    body_size: int
    status: str
    attempts: int
    error_note: str
    received_at: str
    processed_at: str
    claimed_at: str = ""


class MarketingInbox:
    """Durable store for inbound webhook payloads.

    Raw payloads are never stored — only their SHA-256 hash and byte size.
    The hash is enough to detect duplicates and correlate, the size is enough
    for the owner's panel, and neither leaks PII. The original bytes were
    never needed for processing: the connector normalises them before any
    fact write, and the inbox is a durable receipt, not a data lake.
    """

    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA,
                     (_migrate_raw_body_to_hash, _migrate_claimed_at))

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        return self._pool.conn

    def store(self, tenant: str, connector_id: str, vendor: str,
              vendor_event_id: str, correlation_id: str,
              body: bytes, inbox_id: str, now_iso: str,
              event_type: str = "") -> bool:
        """Insert a webhook payload. Returns False on duplicate.

        Raises on real database errors (disk full, corruption, etc.) rather
        than silently returning False — a caller that sees False may safely
        treat it as a duplicate, and a caller that sees an exception knows
        the inbox itself is in trouble.
        """
        import hashlib
        body_sha = hashlib.sha256(body).hexdigest()
        body_sz = len(body)
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO marketing_inbox "
                "(inbox_id, tenant, connector_id, vendor, event_type, "
                " vendor_event_id, correlation_id, body_sha256, body_size, "
                " status, received_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (inbox_id, tenant, connector_id, vendor, event_type,
                 vendor_event_id, correlation_id, body_sha, body_sz,
                 PENDING, now_iso))
            return self._conn.execute("SELECT changes()").fetchone()[0] > 0
        except sqlite3.IntegrityError:
            return False

    def pending(self, tenant: str, limit: int = 50) -> Sequence[InboxItem]:
        """Fetch pending items for a tenant, oldest first."""
        rows = self._conn.execute(
            "SELECT * FROM marketing_inbox WHERE tenant = ? AND status = ? "
            "ORDER BY received_at ASC LIMIT ?",
            (tenant, PENDING, limit)).fetchall()
        return [InboxItem(**dict(r)) for r in rows]

    def mark_processed(self, inbox_id: str, tenant: str,
                       now_iso: str) -> bool:
        """Finalise a processed item. Only valid from PROCESSING.

        Returns True if a row was actually updated, False if the item was
        not in PROCESSING state (e.g. already processed or never claimed).
        """
        cur = self._conn.execute(
            "UPDATE marketing_inbox SET status = ?, processed_at = ?, "
            "attempts = attempts + 1 "
            "WHERE inbox_id = ? AND tenant = ? AND status = ?",
            (PROCESSED, now_iso, inbox_id, tenant, PROCESSING))
        return cur.rowcount == 1

    def mark_failed(self, inbox_id: str, tenant: str,
                    now_iso: str, note: str = "") -> bool:
        """Mark an item as failed. Valid from PROCESSING (or PENDING for
        direct rejection paths that never claimed).

        Returns True if a row was actually updated, False otherwise.
        """
        cur = self._conn.execute(
            "UPDATE marketing_inbox SET status = ?, error_note = ?, "
            "attempts = attempts + 1, processed_at = ? "
            "WHERE inbox_id = ? AND tenant = ? AND status IN (?, ?)",
            (FAILED, note, now_iso, inbox_id, tenant, PROCESSING, PENDING))
        return cur.rowcount == 1

    def claim_next(self, tenant: str | None = None,
                   now_iso: str | None = None) -> InboxItem | None:
        """Atomically claim one pending item: pending → processing.

        BEGIN IMMEDIATE + SELECT + UPDATE in one transaction makes the claim
        race-free: two concurrent processors can never both claim the same
        row, because the second sees status='processing' and claims nothing.

        Returns the claimed item, or None when nothing is pending.
        """
        import time as _t
        if now_iso is None:
            now_iso = _t.strftime("%Y-%m-%dT%H:%M:%S", _t.gmtime())
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            if tenant is None:
                row = self._conn.execute(
                    "SELECT * FROM marketing_inbox WHERE status = ? "
                    "ORDER BY received_at ASC LIMIT 1", (PENDING,)).fetchone()
            else:
                row = self._conn.execute(
                    "SELECT * FROM marketing_inbox WHERE tenant = ? "
                    "AND status = ? ORDER BY received_at ASC LIMIT 1",
                    (tenant, PENDING)).fetchone()
            if row is None:
                self._conn.execute("COMMIT")
                return None
            item = InboxItem(**dict(row))
            self._conn.execute(
                "UPDATE marketing_inbox SET status = ?, claimed_at = ?, "
                "attempts = attempts + 1 "
                "WHERE inbox_id = ? AND status = ?",
                (PROCESSING, now_iso, item.inbox_id, PENDING))
            self._conn.execute("COMMIT")
            return item
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def recover_stale(self, timeout_s: int = 300,
                      now_iso: str | None = None) -> int:
        """Items stuck in PROCESSING longer than timeout_s become HELD.

        A crash between claim and mark leaves a row in PROCESSING forever.
        This turns such rows into HELD — visible, human-decidable — rather
        than pretending they are being processed. Age is measured from
        claimed_at, so a freshly claimed item is never touched.
        """
        import time as _t
        if now_iso is None:
            now_iso = _t.strftime("%Y-%m-%dT%H:%M:%S", _t.gmtime())
        # Cutoff computed from the same clock as claimed_at (the injected
        # now_iso), so tests and production agree on what "stale" means.
        # `calendar.timegm` treats the parsed time as UTC — the format this
        # node writes everywhere — regardless of the host's timezone.
        try:
            import calendar
            now_epoch = calendar.timegm(
                _t.strptime(now_iso, "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            now_epoch = _t.time()
        cutoff = _t.strftime(
            "%Y-%m-%dT%H:%M:%S", _t.gmtime(now_epoch - timeout_s))
        cur = self._conn.execute(
            "UPDATE marketing_inbox SET status = ?, error_note = 'stale claim', "
            "processed_at = ? "
            "WHERE status = ? AND claimed_at != '' AND claimed_at < ?",
            (HELD, now_iso, PROCESSING, cutoff))
        return cur.rowcount

    def counts(self, tenant: str) -> Mapping[str, int]:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) FROM marketing_inbox "
            "WHERE tenant = ? GROUP BY status", (tenant,)).fetchall()
        return {dict(r)["status"]: dict(r)["COUNT(*)"] for r in rows}

    def counts_all(self) -> Mapping[str, Mapping[str, int]]:
        """Per-tenant counts, keyed by tenant name."""
        rows = self._conn.execute(
            "SELECT tenant, status, COUNT(*) FROM marketing_inbox "
            "GROUP BY tenant, status").fetchall()
        out: dict[str, dict[str, int]] = {}
        for r in rows:
            d = dict(r)
            out.setdefault(d["tenant"], {})[d["status"]] = d["COUNT(*)"]
        return out

    def recent(self, tenant: str, limit: int = 20) -> Sequence[InboxItem]:
        """Most recent items across all statuses, for the owner's view."""
        rows = self._conn.execute(
            "SELECT * FROM marketing_inbox WHERE tenant = ? "
            "ORDER BY received_at DESC LIMIT ?",
            (tenant, limit)).fetchall()
        return [InboxItem(**dict(r)) for r in rows]

    def depth(self, tenant: str) -> int:
        """Count of pending items — the backlog."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM marketing_inbox "
            "WHERE tenant = ? AND status = ?", (tenant, PENDING)).fetchone()
        return dict(row)["COUNT(*)"]
