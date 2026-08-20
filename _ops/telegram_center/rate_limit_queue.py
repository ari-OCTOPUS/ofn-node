#!/usr/bin/env python3
"""Durable Telegram rate-limit queue for fixture/shadow verification.

This module has no network capability and is not wired into the live sender.
It stores hashes/metadata only and provides the scheduler invariants needed for
an owner-approved future sender integration.
"""
from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path

_LOCK = threading.RLock()
_TERMINAL = {"CONFIRMED", "DLQ"}


def deterministic_key(*parts: object) -> str:
    blob = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class RateLimitQueue:
    def __init__(self, path: Path | str, *, clock=None, jitter=None,
                 max_depth: int = 1000, max_age_s: float = 86400.0):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock or time.time
        self._jitter = jitter or (lambda: 0.0)
        self.max_depth = max(1, int(max_depth))
        self.max_age_s = max(1.0, float(max_age_s))
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False,
                                     isolation_level=None, timeout=10.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.executescript(
            "CREATE TABLE IF NOT EXISTS queue("
            "seq INTEGER PRIMARY KEY AUTOINCREMENT, message_key TEXT UNIQUE NOT NULL, "
            "chat_hash TEXT NOT NULL, payload_hash TEXT NOT NULL, priority INTEGER NOT NULL, "
            "state TEXT NOT NULL, business_attempts INTEGER NOT NULL, "
            "delivery_attempts INTEGER NOT NULL, created_at REAL NOT NULL, "
            "retry_not_before REAL NOT NULL, message_id INTEGER, last_error TEXT);"
            "CREATE INDEX IF NOT EXISTS idx_queue_due ON queue(state,retry_not_before,priority,seq);"
            "CREATE TABLE IF NOT EXISTS digests("
            "group_key TEXT PRIMARY KEY, count INTEGER NOT NULL, first_seen REAL NOT NULL, "
            "last_seen REAL NOT NULL, state TEXT NOT NULL DEFAULT 'OPEN');"
            "CREATE TABLE IF NOT EXISTS rate_events("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, chat_hash TEXT NOT NULL, "
            "is_group INTEGER NOT NULL, ts REAL NOT NULL);"
            "CREATE INDEX IF NOT EXISTS idx_rate_ts ON rate_events(ts);"
            "CREATE INDEX IF NOT EXISTS idx_rate_chat ON rate_events(chat_hash,ts);")

    def set_clock(self, clock) -> None:
        self._clock = clock

    def admit(self, *, chat_hash: str, is_group: bool = False) -> dict:
        """Apply local conservative policy before a sender takes an item.

        Policy, not a Telegram guarantee: 1/s per chat, 20/min per group,
        30/s global. A rejection records no rate event and provides the next
        local retry time.
        """
        now = float(self._clock())
        with _LOCK:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute("DELETE FROM rate_events WHERE ts<?", (now - 60.0,))
            global_count = self._conn.execute(
                "SELECT COUNT(*) FROM rate_events WHERE ts>?", (now - 1.0,)).fetchone()[0]
            chat_last = self._conn.execute(
                "SELECT MAX(ts) FROM rate_events WHERE chat_hash=?", (str(chat_hash),)).fetchone()[0]
            group_count = 0
            if is_group:
                group_count = self._conn.execute(
                    "SELECT COUNT(*) FROM rate_events WHERE chat_hash=? AND is_group=1 AND ts>?",
                    (str(chat_hash), now - 60.0)).fetchone()[0]
            reasons = []
            retry_at = now
            if global_count >= 30:
                reasons.append("GLOBAL_30_PER_SECOND")
                first = self._conn.execute(
                    "SELECT MIN(ts) FROM rate_events WHERE ts>?", (now - 1.0,)).fetchone()[0]
                retry_at = max(retry_at, float(first or now) + 1.0)
            if chat_last is not None and now - float(chat_last) < 1.0:
                reasons.append("CHAT_1_PER_SECOND")
                retry_at = max(retry_at, float(chat_last) + 1.0)
            if is_group and group_count >= 20:
                reasons.append("GROUP_20_PER_MINUTE")
                first = self._conn.execute(
                    "SELECT MIN(ts) FROM rate_events WHERE chat_hash=? AND is_group=1 AND ts>?",
                    (str(chat_hash), now - 60.0)).fetchone()[0]
                retry_at = max(retry_at, float(first or now) + 60.0)
            if reasons:
                self._conn.execute("COMMIT")
                return {"allowed": False, "reasons": reasons,
                        "retry_not_before": retry_at}
            self._conn.execute(
                "INSERT INTO rate_events(chat_hash,is_group,ts) VALUES(?,?,?)",
                (str(chat_hash), 1 if is_group else 0, now))
            self._conn.execute("COMMIT")
        return {"allowed": True, "reasons": [], "retry_not_before": now}

    def enqueue(self, *, message_key: str | None = None, chat_hash: str,
                payload_hash: str, priority: int = 0,
                business_attempts: int = 0) -> dict:
        key = str(message_key or deterministic_key(chat_hash, payload_hash))
        now = float(self._clock())
        with _LOCK:
            self._conn.execute("BEGIN IMMEDIATE")
            current = self._conn.execute(
                "SELECT state FROM queue WHERE message_key=?", (key,)).fetchone()
            if current is not None:
                self._conn.execute("COMMIT")
                return {"message_key": key, "duplicate": True,
                        "state": current[0]}
            depth = self._conn.execute(
                "SELECT COUNT(*) FROM queue WHERE state NOT IN ('CONFIRMED','DLQ')").fetchone()[0]
            if depth >= self.max_depth:
                self._conn.execute("COMMIT")
                return {"message_key": key, "duplicate": False,
                        "state": "REJECTED_QUEUE_FULL"}
            self._conn.execute(
                "INSERT INTO queue(message_key,chat_hash,payload_hash,priority,state,"
                "business_attempts,delivery_attempts,created_at,retry_not_before) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (key, str(chat_hash), str(payload_hash), int(priority), "QUEUED",
                 int(business_attempts), 0, now, now))
            self._conn.execute("COMMIT")
        return {"message_key": key, "duplicate": False, "state": "QUEUED"}

    def due(self, *, limit: int = 100) -> list[dict]:
        now = float(self._clock())
        lim = min(100, max(1, int(limit)))
        with _LOCK:
            # Expired queued items are retained as DLQ, never silently deleted.
            cutoff = now - self.max_age_s
            self._conn.execute(
                "UPDATE queue SET state='DLQ',last_error='QUEUE_AGE_EXCEEDED' "
                "WHERE state IN ('QUEUED','DEFERRED') AND created_at<?", (cutoff,))
            rows = self._conn.execute(
                "SELECT message_key,chat_hash,payload_hash,priority,state,"
                "business_attempts,delivery_attempts,created_at,retry_not_before,message_id "
                "FROM queue WHERE state IN ('QUEUED','DEFERRED') AND retry_not_before<=? "
                "ORDER BY priority DESC,seq ASC LIMIT ?", (now, lim)).fetchall()
        names = ("message_key", "chat_hash", "payload_hash", "priority", "state",
                 "business_attempts", "delivery_attempts", "created_at",
                 "retry_not_before", "message_id")
        return [dict(zip(names, row)) for row in rows]

    def defer(self, message_key: str, *, retry_after: float) -> bool:
        ra = max(0.0, float(retry_after))
        retry_not_before = float(self._clock()) + ra + max(0.0, float(self._jitter()))
        with _LOCK:
            updated = self._conn.execute(
                "UPDATE queue SET state='DEFERRED',retry_not_before=?,last_error='RATE_LIMIT' "
                "WHERE message_key=? AND state NOT IN ('CONFIRMED','DLQ')",
                (retry_not_before, message_key)).rowcount
        return updated == 1

    def mark_delivery_attempt(self, message_key: str) -> bool:
        with _LOCK:
            updated = self._conn.execute(
                "UPDATE queue SET delivery_attempts=delivery_attempts+1,state='SENDING' "
                "WHERE message_key=? AND state IN ('QUEUED','DEFERRED')",
                (message_key,)).rowcount
        return updated == 1

    def reconcile_sending(self, message_key: str) -> bool:
        """Crash after transport attempt is quarantined, never auto-resent."""
        with _LOCK:
            updated = self._conn.execute(
                "UPDATE queue SET state='DLQ',last_error='UNCERTAIN_SEND_OUTCOME' "
                "WHERE message_key=? AND state='SENDING'", (message_key,)).rowcount
        return updated == 1

    def confirm(self, message_key: str, *, message_id: int) -> bool:
        with _LOCK:
            updated = self._conn.execute(
                "UPDATE queue SET state='CONFIRMED',message_id=?,last_error=NULL "
                "WHERE message_key=? AND state!='DLQ'", (int(message_id), message_key)).rowcount
        return updated == 1

    def dead_letter(self, message_key: str, *, reason: str) -> bool:
        with _LOCK:
            updated = self._conn.execute(
                "UPDATE queue SET state='DLQ',last_error=? WHERE message_key=? "
                "AND state!='CONFIRMED'", (str(reason)[:120], message_key)).rowcount
        return updated == 1

    def get(self, message_key: str) -> dict | None:
        row = self._conn.execute(
            "SELECT message_key,chat_hash,payload_hash,priority,state,business_attempts,"
            "delivery_attempts,created_at,retry_not_before,message_id,last_error "
            "FROM queue WHERE message_key=?", (message_key,)).fetchone()
        if row is None:
            return None
        names = ("message_key", "chat_hash", "payload_hash", "priority", "state",
                 "business_attempts", "delivery_attempts", "created_at",
                 "retry_not_before", "message_id", "last_error")
        return dict(zip(names, row))

    def enqueue_finding(self, *, group_key: str, finding_key: str,
                        now: float | None = None) -> dict:
        observed = float(now if now is not None else self._clock())
        with _LOCK:
            self._conn.execute(
                "INSERT INTO digests(group_key,count,first_seen,last_seen,state) VALUES(?,1,?,?,'OPEN') "
                "ON CONFLICT(group_key) DO UPDATE SET count=count+1,last_seen=excluded.last_seen",
                (str(group_key), observed, observed))
            row = self._conn.execute(
                "SELECT count,first_seen,last_seen FROM digests WHERE group_key=?",
                (str(group_key),)).fetchone()
        return {"group_key": group_key, "finding_key": finding_key,
                "count": row[0], "first_seen": row[1], "last_seen": row[2]}

    def pending_digests(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT group_key,count,first_seen,last_seen,state FROM digests "
            "WHERE state='OPEN' ORDER BY first_seen").fetchall()
        return [{"group_key": row[0], "count": row[1], "first_seen": row[2],
                 "last_seen": row[3], "state": row[4]} for row in rows]

    def close(self) -> None:
        self._conn.close()
