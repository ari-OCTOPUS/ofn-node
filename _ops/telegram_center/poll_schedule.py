#!/usr/bin/env python3
"""Durable retry schedule for typed Telegram polling outcomes."""
from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_LOCK = threading.RLock()
_SQLITE_TIMEOUT_S = 1.0
_CLOCK_SKEW_S = 5.0
_BASE_DELAY_S = 1.0
_MAX_DELAY_S = 60.0


def _token_digest(token: str) -> str:
    return hashlib.sha256(("poll-schedule:" + str(token or "")).encode("utf-8")).hexdigest()


def _root() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def _db() -> Path:
    return _root() / "telegram" / "poll-schedule.sqlite3"


def _conn() -> sqlite3.Connection:
    path = _db()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        str(path), isolation_level=None, timeout=_SQLITE_TIMEOUT_S,
        check_same_thread=False,
    )
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schedule("
            "token_digest TEXT PRIMARY KEY, kind TEXT NOT NULL, "
            "reason TEXT NOT NULL, failure_streak INTEGER NOT NULL, "
            "not_before REAL NOT NULL, updated_at REAL NOT NULL)"
        )
        return connection
    except Exception:
        connection.close()
        raise


def _error(exc: BaseException) -> dict:
    return {
        "ok": False,
        "allowed": False,
        "kind": "LEASE_DENIED",
        "reason": "schedule-error",
        "retry_after_s": _BASE_DELAY_S,
        "error_class": type(exc).__name__,
    }


def check(token: str, *, now: float | None = None) -> dict:
    """Return whether a network poll may start, failing closed on ambiguity."""
    if not token:
        return {"ok": False, "allowed": False, "kind": "STOPPED", "reason": "no-token"}
    observed = time.time() if now is None else float(now)
    connection: sqlite3.Connection | None = None
    try:
        connection = _conn()
        with _LOCK:
            row = connection.execute(
                "SELECT kind,reason,failure_streak,not_before,updated_at "
                "FROM schedule WHERE token_digest=?",
                (_token_digest(token),),
            ).fetchone()
            if row is None:
                return {"ok": True, "allowed": True}
            kind, reason, streak, not_before, updated_at = row
            if observed + _CLOCK_SKEW_S < float(updated_at):
                return {
                    "ok": False,
                    "allowed": False,
                    "kind": "LEASE_DENIED",
                    "reason": "schedule-clock-regression",
                    "retry_after_s": _BASE_DELAY_S,
                }
            remaining = float(not_before) - observed
            if remaining <= 0:
                return {
                    "ok": True,
                    "allowed": True,
                    "failure_streak": int(streak),
                    "last_kind": str(kind),
                }
            return {
                "ok": True,
                "allowed": False,
                "kind": str(kind),
                "reason": str(reason),
                "failure_streak": int(streak),
                "retry_after_s": remaining,
                "not_before": float(not_before),
            }
    except (OSError, sqlite3.Error, ValueError) as exc:
        return _error(exc)
    finally:
        if connection is not None:
            connection.close()


def _local_delay(kind: str, streak: int) -> float:
    if kind in {"HTTP_4XX", "WEBHOOK_PRESENT"}:
        return _MAX_DELAY_S
    exponent = min(20, max(0, int(streak) - 1))
    return min(_MAX_DELAY_S, _BASE_DELAY_S * (2 ** exponent))


def record_failure(token: str, *, kind: str, reason: str = "",
                   retry_after_s: float | None = None,
                   now: float | None = None) -> dict:
    """Persist the full server prohibition or an exponential local delay."""
    if not token:
        return {"ok": False, "reason": "no-token"}
    observed = time.time() if now is None else float(now)
    connection: sqlite3.Connection | None = None
    try:
        connection = _conn()
        digest = _token_digest(token)
        with _LOCK:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT failure_streak,not_before,updated_at FROM schedule "
                "WHERE token_digest=?",
                (digest,),
            ).fetchone()
            streak = int(row[0]) + 1 if row else 1
            if row is not None and observed + _CLOCK_SKEW_S < float(row[2]):
                connection.execute("ROLLBACK")
                return {"ok": False, "reason": "schedule-clock-regression"}
            server_delay = max(0.0, float(retry_after_s or 0.0))
            delay = max(server_delay, _local_delay(str(kind), streak))
            prior_not_before = float(row[1]) if row else 0.0
            not_before = max(prior_not_before, observed + delay)
            connection.execute(
                "INSERT INTO schedule(token_digest,kind,reason,failure_streak,"
                "not_before,updated_at) VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(token_digest) DO UPDATE SET "
                "kind=excluded.kind,reason=excluded.reason,"
                "failure_streak=excluded.failure_streak,"
                "not_before=excluded.not_before,updated_at=excluded.updated_at",
                (
                    digest, str(kind), str(reason or kind)[:120], streak,
                    not_before, observed,
                ),
            )
            connection.execute("COMMIT")
        return {
            "ok": True,
            "kind": str(kind),
            "failure_streak": streak,
            "retry_after_s": max(0.0, not_before - observed),
            "not_before": not_before,
        }
    except (OSError, sqlite3.Error, ValueError) as exc:
        try:
            if connection is not None:
                connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        return _error(exc)
    finally:
        if connection is not None:
            connection.close()


def record_success(token: str) -> dict:
    """Clear retry state only after a valid completed poll."""
    if not token:
        return {"ok": False, "reason": "no-token"}
    connection: sqlite3.Connection | None = None
    try:
        connection = _conn()
        with _LOCK:
            connection.execute(
                "DELETE FROM schedule WHERE token_digest=?",
                (_token_digest(token),),
            )
        return {"ok": True}
    except (OSError, sqlite3.Error, ValueError) as exc:
        return _error(exc)
    finally:
        if connection is not None:
            connection.close()


def snapshot(token: str) -> dict | None:
    if not token:
        return None
    connection: sqlite3.Connection | None = None
    try:
        connection = _conn()
        row = connection.execute(
            "SELECT kind,reason,failure_streak,not_before,updated_at "
            "FROM schedule WHERE token_digest=?",
            (_token_digest(token),),
        ).fetchone()
        if row is None:
            return None
        return dict(zip(
            ("kind", "reason", "failure_streak", "not_before", "updated_at"),
            row,
        ))
    except (OSError, sqlite3.Error, ValueError):
        return None
    finally:
        if connection is not None:
            connection.close()
