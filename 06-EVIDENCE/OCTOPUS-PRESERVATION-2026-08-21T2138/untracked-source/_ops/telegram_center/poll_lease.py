#!/usr/bin/env python3
"""Atomic Telegram polling lease keyed by token digest.

Guards against duplicate pollers on the same token: the second consumer fails
BEFORE calling Telegram. A Telegram 409 opens a circuit (DUPLICATE_CONSUMER)
with cooldown, so a rogue poller cannot trigger a retry storm.

Only a one-way token digest is persisted — never the token itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_LOCK = threading.RLock()
_LEASE_S = 120.0          # valid lease window; refreshed each poll round
_FAIL_THRESHOLD = 3       # consecutive 409s -> circuit OPEN
_COOLDOWN_S = 60.0        # circuit cooldown with jitter


def _token_digest(token: str) -> str:
    return hashlib.sha256(("poll-lease:" + str(token or "")).encode("utf-8")).hexdigest()


def _root() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def _db() -> Path:
    return _root() / "telegram" / "poll-lease.sqlite3"


def _boot_id(pid: int) -> str:
    """Per-process boot identity: pid + process start timestamp."""
    try:
        import psutil
        p = psutil.Process(pid)
        return f"{pid}:{int(p.create_time())}"
    except Exception:  # noqa: BLE001
        return f"{pid}:{int(time.time() // 3600)}"


def _conn() -> sqlite3.Connection:
    path = _db()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), check_same_thread=False,
                          isolation_level=None, timeout=10.0)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS lease("
                "token_digest TEXT PRIMARY KEY, owner_pid INTEGER NOT NULL, "
                "owner_boot_id TEXT NOT NULL, acquired_at REAL NOT NULL, "
                "heartbeat_at REAL NOT NULL, lease_until REAL NOT NULL, "
                "state TEXT NOT NULL DEFAULT 'ACTIVE', "
                "fail_count INTEGER NOT NULL DEFAULT 0, "
                "cooldown_until REAL NOT NULL DEFAULT 0)")
    return con


def assert_poll_lease(token: str) -> dict:
    """Acquire/refresh the poll lease for this process.

    Second consumer (different pid/boot) with a still-valid lease -> denied
    BEFORE any Telegram call. Circuit OPEN -> denied until cooldown passes.
    """
    if not token:
        return {"ok": False, "reason": "no-token"}
    digest = _token_digest(token)
    pid = os.getpid()
    boot = _boot_id(pid)
    now = time.time()
    con = _conn()
    with _LOCK:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT owner_pid,owner_boot_id,lease_until,state,"
                          "cooldown_until,fail_count FROM lease WHERE token_digest=?",
                          (digest,)).fetchone()
        if row is not None:
            owner_pid, owner_boot, lease_until, state, cooldown_until, fail_count = row
            if state == "OPEN" and now < float(cooldown_until):
                con.execute("ROLLBACK")
                return {"ok": False, "reason": "circuit-open",
                        "cooldown_s": round(float(cooldown_until) - now, 1)}
            if state in ("ACTIVE", "OPEN") and (owner_pid, owner_boot) != (pid, boot) \
                    and now < float(lease_until):
                con.execute("ROLLBACK")
                return {"ok": False, "reason": "duplicate-consumer",
                        "owner_pid": owner_pid}
        try:
            con.execute(
                "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
                "heartbeat_at,lease_until,state,fail_count,cooldown_until) "
                "VALUES(?,?,?,?,?,?,?,0,0) "
                "ON CONFLICT(token_digest) DO UPDATE SET "
                "owner_pid=excluded.owner_pid, owner_boot_id=excluded.owner_boot_id, "
                "heartbeat_at=excluded.heartbeat_at, lease_until=excluded.lease_until, "
                "state='ACTIVE', fail_count=0, cooldown_until=0",
                (digest, pid, boot, now, now, now + _LEASE_S, "ACTIVE"))
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:  # noqa: BLE001
                pass
            raise
        finally:
            con.close()
    return {"ok": True, "owner_pid": pid, "lease_until": now + _LEASE_S}


def mark_duplicate_consumer(token: str) -> dict:
    """A Telegram 409 was seen: open the circuit with cooldown."""
    digest = _token_digest(token)
    now = time.time()
    con = _conn()
    with _LOCK:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT fail_count FROM lease WHERE token_digest=?",
                          (digest,)).fetchone()
        fails = int(row[0]) + 1 if row else 1
        state = "OPEN" if fails >= _FAIL_THRESHOLD else "ACTIVE"
        import random as _r
        cooldown = _COOLDOWN_S * (1 + _r.random()) if state == "OPEN" else 0.0
        try:
            con.execute(
                "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
                "heartbeat_at,lease_until,state,fail_count,cooldown_until) "
                "VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(token_digest) DO UPDATE SET "
                "state=excluded.state, fail_count=excluded.fail_count, "
                "cooldown_until=excluded.cooldown_until",
                (digest, os.getpid(), _boot_id(os.getpid()), now, now,
                 now + _LEASE_S, state, fails, now + cooldown))
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:  # noqa: BLE001
                pass
            raise
        finally:
            con.close()
    return {"ok": True, "state": state, "fail_count": fails, "cooldown_s": cooldown}


def lease_snapshot(token: str) -> dict | None:
    digest = _token_digest(token)
    try:
        con = _conn()
        row = con.execute("SELECT owner_pid,owner_boot_id,acquired_at,heartbeat_at,"
                          "lease_until,state,fail_count,cooldown_until "
                          "FROM lease WHERE token_digest=?", (digest,)).fetchone()
        con.close()
        if row is None:
            return None
        return {"owner_pid": row[0], "owner_boot_id": row[1], "acquired_at": row[2],
                "heartbeat_at": row[3], "lease_until": row[4], "state": row[5],
                "fail_count": row[6], "cooldown_until": row[7]}
    except Exception:  # noqa: BLE001
        return None
