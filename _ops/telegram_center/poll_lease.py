#!/usr/bin/env python3
"""Fail-closed Telegram polling lease keyed by a one-way token digest.

The lease is checked before every ``getUpdates`` request.  A different live
process is refused before network I/O, an expired owner can be replaced with a
new fencing generation, and the first Telegram 409 opens a persistent cooldown.
Only hashes and process identity metadata are stored; the bot token is not.
"""
from __future__ import annotations

import functools
import hashlib
import os
import platform
import random
import sqlite3
import subprocess
import threading
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
_LOCK = threading.RLock()
_LEASE_S = 90.0
_SQLITE_TIMEOUT_S = 1.0
_CLOCK_SKEW_S = 5.0
_BASE_COOLDOWN_S = 5.0
_MAX_COOLDOWN_S = 300.0
_FAIL_THRESHOLD = 1
_COOLDOWN_S = _BASE_COOLDOWN_S
_PROCESS_STARTED_NS = time.time_ns()


def _token_digest(token: str) -> str:
    return hashlib.sha256(("poll-lease:" + str(token or "")).encode("utf-8")).hexdigest()


def _root() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def _db() -> Path:
    return _root() / "telegram" / "poll-lease.sqlite3"


def _boot_id(pid: int) -> str:
    """Stable identity for one process incarnation, including PID reuse."""
    try:
        import psutil
        return f"{pid}:{int(psutil.Process(pid).create_time() * 1_000_000_000)}"
    except Exception:  # noqa: BLE001
        if int(pid) == os.getpid():
            return f"{pid}:{_PROCESS_STARTED_NS}"
        return f"{pid}:unknown"


@functools.lru_cache(maxsize=1)
def _host_boot_digest() -> str:
    try:
        import psutil
        boot = int(psutil.boot_time() * 1_000_000_000)
    except Exception:  # noqa: BLE001
        boot = 0
    raw = f"{platform.node()}:{boot}".encode("utf-8", "replace")
    return hashlib.sha256(raw).hexdigest()


@functools.lru_cache(maxsize=1)
def _code_head() -> str:
    value = str(os.environ.get("OCTOPUS_CODE_HEAD", "") or "").strip()
    if len(value) == 40 and all(ch in "0123456789abcdefABCDEF" for ch in value):
        return value.lower()
    try:
        return subprocess.check_output(
            ["git", "-C", str(_OPS.parent), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL, timeout=2.0,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        try:
            return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:40]
        except OSError:
            return "unknown"


def _identity() -> tuple[int, str, str, str, str]:
    pid = os.getpid()
    boot = _boot_id(pid)
    host_boot = _host_boot_digest()
    code_head = _code_head()
    owner_raw = f"{host_boot}:{boot}:{code_head}".encode("utf-8", "replace")
    owner_instance = hashlib.sha256(owner_raw).hexdigest()[:32]
    return pid, boot, owner_instance, host_boot, code_head


def _ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        "CREATE TABLE IF NOT EXISTS lease("
        "token_digest TEXT PRIMARY KEY, owner_pid INTEGER NOT NULL, "
        "owner_boot_id TEXT NOT NULL, acquired_at REAL NOT NULL, "
        "heartbeat_at REAL NOT NULL, lease_until REAL NOT NULL, "
        "state TEXT NOT NULL DEFAULT 'ACTIVE', "
        "fail_count INTEGER NOT NULL DEFAULT 0, "
        "cooldown_until REAL NOT NULL DEFAULT 0, "
        "generation INTEGER NOT NULL DEFAULT 1, "
        "owner_instance TEXT NOT NULL DEFAULT '', "
        "host_boot_digest TEXT NOT NULL DEFAULT '', "
        "code_head TEXT NOT NULL DEFAULT '', "
        "request_deadline REAL NOT NULL DEFAULT 0, "
        "last_reason TEXT NOT NULL DEFAULT '')"
    )
    columns = {row[1] for row in con.execute("PRAGMA table_info(lease)")}
    additions = {
        "generation": "INTEGER NOT NULL DEFAULT 1",
        "owner_instance": "TEXT NOT NULL DEFAULT ''",
        "host_boot_digest": "TEXT NOT NULL DEFAULT ''",
        "code_head": "TEXT NOT NULL DEFAULT ''",
        "request_deadline": "REAL NOT NULL DEFAULT 0",
        "last_reason": "TEXT NOT NULL DEFAULT ''",
    }
    for name, declaration in additions.items():
        if name in columns:
            continue
        try:
            con.execute(f"ALTER TABLE lease ADD COLUMN {name} {declaration}")
        except sqlite3.OperationalError as exc:
            refreshed = {row[1] for row in con.execute("PRAGMA table_info(lease)")}
            if name not in refreshed:
                raise exc


def _conn() -> sqlite3.Connection:
    path = _db()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(
        str(path), check_same_thread=False, isolation_level=None,
        timeout=_SQLITE_TIMEOUT_S,
    )
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        with _LOCK:
            _ensure_schema(con)
        return con
    except Exception:
        con.close()
        raise


def _rollback(con: sqlite3.Connection | None) -> None:
    if con is None:
        return
    try:
        con.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _lease_error(exc: BaseException) -> dict:
    return {"ok": False, "reason": "lease-error", "error_class": type(exc).__name__}


def _select(con: sqlite3.Connection, digest: str):
    return con.execute(
        "SELECT owner_pid,owner_boot_id,lease_until,state,cooldown_until,"
        "fail_count,generation,owner_instance,host_boot_digest,code_head,"
        "request_deadline,heartbeat_at,acquired_at,last_reason "
        "FROM lease WHERE token_digest=?",
        (digest,),
    ).fetchone()


def assert_poll_lease(token: str, *, request_deadline: float | None = None) -> dict:
    """Acquire or refresh this process's lease, failing closed on ambiguity.

    A foreign unexpired owner, active cooldown, clock regression, or storage
    failure returns ``ok=False``.  No exception from the lease store authorizes
    network I/O.  ``generation`` is a fencing token and increments on takeover.
    """
    if not token:
        return {"ok": False, "reason": "no-token"}
    digest = _token_digest(token)
    pid, boot, owner_instance, host_boot, code_head = _identity()
    now = time.time()
    deadline = max(now, float(request_deadline or 0.0))
    con: sqlite3.Connection | None = None
    try:
        con = _conn()
        with _LOCK:
            con.execute("BEGIN IMMEDIATE")
            row = _select(con, digest)
            generation = 1
            acquired_at = now
            fail_count = 0
            last_reason = ""
            if row is not None:
                (owner_pid, owner_boot, lease_until, state, cooldown_until,
                 fail_count, generation, stored_instance, stored_host_boot,
                 stored_head, stored_deadline, heartbeat_at, acquired_at,
                 last_reason) = row
                if now + _CLOCK_SKEW_S < float(heartbeat_at):
                    _rollback(con)
                    return {"ok": False, "reason": "clock-regression"}
                if state == "OPEN" and now < float(cooldown_until):
                    _rollback(con)
                    return {
                        "ok": False,
                        "reason": "circuit-open",
                        "cooldown_s": round(float(cooldown_until) - now, 3),
                        "generation": int(generation),
                    }
                same_process = (
                    int(owner_pid) == pid
                    and str(owner_boot) == boot
                    and (not stored_instance or str(stored_instance) == owner_instance)
                    and (not stored_host_boot or str(stored_host_boot) == host_boot)
                )
                protected_until = max(float(lease_until), float(stored_deadline or 0.0))
                if same_process and float(stored_deadline or 0.0) > now:
                    _rollback(con)
                    return {
                        "ok": False,
                        "reason": "request-in-flight",
                        "owner_pid": pid,
                        "generation": int(generation),
                    }
                if not same_process and now < protected_until:
                    _rollback(con)
                    return {
                        "ok": False,
                        "reason": "duplicate-consumer",
                        "owner_pid": int(owner_pid),
                        "generation": int(generation),
                    }
                if not same_process:
                    generation = int(generation) + 1
                    acquired_at = now
                    fail_count = 0
                    last_reason = "takeover-after-expiry"
            lease_until = now + _LEASE_S
            con.execute(
                "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
                "heartbeat_at,lease_until,state,fail_count,cooldown_until,generation,"
                "owner_instance,host_boot_digest,code_head,request_deadline,last_reason) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(token_digest) DO UPDATE SET "
                "owner_pid=excluded.owner_pid,owner_boot_id=excluded.owner_boot_id,"
                "acquired_at=excluded.acquired_at,heartbeat_at=excluded.heartbeat_at,"
                "lease_until=excluded.lease_until,state='ACTIVE',"
                "cooldown_until=0,generation=excluded.generation,"
                "owner_instance=excluded.owner_instance,"
                "host_boot_digest=excluded.host_boot_digest,code_head=excluded.code_head,"
                "request_deadline=excluded.request_deadline,last_reason=excluded.last_reason",
                (
                    digest, pid, boot, float(acquired_at), now, lease_until,
                    "ACTIVE", int(fail_count), 0.0, int(generation),
                    owner_instance, host_boot, code_head, deadline,
                    str(last_reason or "")[:80],
                ),
            )
            con.execute("COMMIT")
        return {
            "ok": True,
            "owner_pid": pid,
            "owner_boot_id": boot,
            "owner_instance": owner_instance,
            "generation": int(generation),
            "lease_until": lease_until,
            "request_deadline": deadline,
        }
    except (OSError, sqlite3.Error, ValueError) as exc:
        _rollback(con)
        return _lease_error(exc)
    finally:
        if con is not None:
            con.close()


def _cooldown_delay(fail_count: int) -> float:
    exponent = min(20, max(0, int(fail_count) - 1))
    ceiling = min(_MAX_COOLDOWN_S, _BASE_COOLDOWN_S * (2 ** exponent))
    return (ceiling / 2.0) + (random.random() * ceiling / 2.0)


def mark_duplicate_consumer(token: str) -> dict:
    """Persist the first 409 as an immediately open duplicate-consumer circuit."""
    if not token:
        return {"ok": False, "reason": "no-token"}
    digest = _token_digest(token)
    pid, boot, owner_instance, host_boot, code_head = _identity()
    now = time.time()
    con: sqlite3.Connection | None = None
    try:
        con = _conn()
        with _LOCK:
            con.execute("BEGIN IMMEDIATE")
            row = _select(con, digest)
            if row is None:
                generation = 1
                fail_count = 1
                acquired_at = now
                owner_pid = pid
                owner_boot = boot
                stored_instance = owner_instance
                stored_host_boot = host_boot
                stored_head = code_head
                lease_until = now + _LEASE_S
                request_deadline = now
            else:
                (owner_pid, owner_boot, lease_until, _state, _cooldown_until,
                 old_fail_count, generation, stored_instance, stored_host_boot,
                 stored_head, request_deadline, heartbeat_at, acquired_at,
                 _last_reason) = row
                if now + _CLOCK_SKEW_S < float(heartbeat_at):
                    _rollback(con)
                    return {"ok": False, "reason": "clock-regression"}
                fail_count = int(old_fail_count) + 1
                lease_until = max(float(lease_until), now + _LEASE_S)
                stored_instance = stored_instance or owner_instance
                stored_host_boot = stored_host_boot or host_boot
                stored_head = stored_head or code_head
            cooldown = _cooldown_delay(fail_count)
            cooldown_until = now + cooldown
            con.execute(
                "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
                "heartbeat_at,lease_until,state,fail_count,cooldown_until,generation,"
                "owner_instance,host_boot_digest,code_head,request_deadline,last_reason) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(token_digest) DO UPDATE SET "
                "heartbeat_at=excluded.heartbeat_at,lease_until=excluded.lease_until,"
                "state='OPEN',fail_count=excluded.fail_count,"
                "cooldown_until=excluded.cooldown_until,last_reason=excluded.last_reason",
                (
                    digest, int(owner_pid), str(owner_boot), float(acquired_at),
                    now, float(lease_until), "OPEN", int(fail_count),
                    cooldown_until, int(generation), str(stored_instance),
                    str(stored_host_boot), str(stored_head),
                    float(request_deadline or 0.0), "DUPLICATE_CONSUMER",
                ),
            )
            con.execute("COMMIT")
        return {
            "ok": True,
            "state": "OPEN",
            "fail_count": int(fail_count),
            "generation": int(generation),
            "cooldown_s": cooldown,
        }
    except (OSError, sqlite3.Error, ValueError) as exc:
        _rollback(con)
        return _lease_error(exc)
    finally:
        if con is not None:
            con.close()


def finish_poll_request(token: str, *, generation: int | None = None,
                        reason: str = "poll-failed") -> dict:
    """Clear the in-flight deadline without resetting conflict history.

    This is used after a request has definitely returned with an error.  It is
    fenced by the same owner identity and generation as successful completion.
    """
    if not token:
        return {"ok": False, "reason": "no-token"}
    digest = _token_digest(token)
    pid, boot, owner_instance, host_boot, _code = _identity()
    now = time.time()
    con: sqlite3.Connection | None = None
    try:
        con = _conn()
        with _LOCK:
            con.execute("BEGIN IMMEDIATE")
            row = _select(con, digest)
            if row is None:
                _rollback(con)
                return {"ok": False, "reason": "lease-missing"}
            (owner_pid, owner_boot, lease_until, _state, _cooldown_until,
             _fail_count, current_generation, stored_instance, stored_host_boot,
             _stored_head, _request_deadline, _heartbeat_at, _acquired_at,
             _last_reason) = row
            identity_ok = (
                int(owner_pid) == pid
                and str(owner_boot) == boot
                and (not stored_instance or str(stored_instance) == owner_instance)
                and (not stored_host_boot or str(stored_host_boot) == host_boot)
            )
            generation_ok = generation is None or int(generation) == int(current_generation)
            if not identity_ok or not generation_ok:
                _rollback(con)
                return {
                    "ok": False,
                    "reason": "stale-generation",
                    "generation": int(current_generation),
                }
            con.execute(
                "UPDATE lease SET heartbeat_at=?,lease_until=?,request_deadline=0,"
                "last_reason=CASE WHEN state='OPEN' THEN last_reason ELSE ? END "
                "WHERE token_digest=? AND generation=?",
                (
                    now, max(float(lease_until), now + _LEASE_S),
                    str(reason or "poll-failed")[:80], digest,
                    int(current_generation),
                ),
            )
            con.execute("COMMIT")
        return {"ok": True, "generation": int(current_generation)}
    except (OSError, sqlite3.Error, ValueError) as exc:
        _rollback(con)
        return _lease_error(exc)
    finally:
        if con is not None:
            con.close()


def mark_poll_success(token: str, *, generation: int | None = None) -> dict:
    """Confirm the same fenced owner completed a valid poll and reset failures."""
    if not token:
        return {"ok": False, "reason": "no-token"}
    digest = _token_digest(token)
    pid, boot, owner_instance, host_boot, _code = _identity()
    now = time.time()
    con: sqlite3.Connection | None = None
    try:
        con = _conn()
        with _LOCK:
            con.execute("BEGIN IMMEDIATE")
            row = _select(con, digest)
            if row is None:
                _rollback(con)
                return {"ok": False, "reason": "lease-missing"}
            (owner_pid, owner_boot, lease_until, state, cooldown_until,
             _fail_count, current_generation, stored_instance, stored_host_boot,
             _stored_head, _request_deadline, _heartbeat_at, _acquired_at,
             _last_reason) = row
            identity_ok = (
                int(owner_pid) == pid
                and str(owner_boot) == boot
                and (not stored_instance or str(stored_instance) == owner_instance)
                and (not stored_host_boot or str(stored_host_boot) == host_boot)
            )
            generation_ok = generation is None or int(generation) == int(current_generation)
            if not identity_ok or not generation_ok:
                _rollback(con)
                return {"ok": False, "reason": "stale-generation", "generation": int(current_generation)}
            if state == "OPEN" and now < float(cooldown_until):
                _rollback(con)
                return {"ok": False, "reason": "circuit-open", "generation": int(current_generation)}
            con.execute(
                "UPDATE lease SET heartbeat_at=?,lease_until=?,state='ACTIVE',"
                "fail_count=0,cooldown_until=0,request_deadline=0,last_reason='' "
                "WHERE token_digest=? AND generation=?",
                (now, max(float(lease_until), now + _LEASE_S), digest, int(current_generation)),
            )
            con.execute("COMMIT")
        return {"ok": True, "generation": int(current_generation)}
    except (OSError, sqlite3.Error, ValueError) as exc:
        _rollback(con)
        return _lease_error(exc)
    finally:
        if con is not None:
            con.close()


def release_poll_lease(token: str, *, generation: int | None = None) -> dict:
    """Release only this exact process generation; a foreign owner is untouched."""
    if not token:
        return {"ok": False, "reason": "no-token"}
    digest = _token_digest(token)
    pid, boot, owner_instance, host_boot, _code = _identity()
    now = time.time()
    con: sqlite3.Connection | None = None
    try:
        con = _conn()
        with _LOCK:
            con.execute("BEGIN IMMEDIATE")
            row = _select(con, digest)
            if row is None:
                _rollback(con)
                return {"ok": True, "state": "ABSENT"}
            owner_pid, owner_boot, _until, _state, _cooldown, _fails, current_generation, stored_instance, stored_host_boot, *_rest = row
            identity_ok = (
                int(owner_pid) == pid and str(owner_boot) == boot
                and (not stored_instance or str(stored_instance) == owner_instance)
                and (not stored_host_boot or str(stored_host_boot) == host_boot)
            )
            generation_ok = generation is None or int(generation) == int(current_generation)
            if not identity_ok or not generation_ok:
                _rollback(con)
                return {"ok": False, "reason": "not-owner", "generation": int(current_generation)}
            con.execute(
                "UPDATE lease SET state='RELEASED',heartbeat_at=?,lease_until=?,"
                "request_deadline=0,last_reason='released' WHERE token_digest=?",
                (now, now, digest),
            )
            con.execute("COMMIT")
        return {"ok": True, "state": "RELEASED", "generation": int(current_generation)}
    except (OSError, sqlite3.Error, ValueError) as exc:
        _rollback(con)
        return _lease_error(exc)
    finally:
        if con is not None:
            con.close()


def lease_snapshot(token: str) -> dict | None:
    if not token:
        return None
    con: sqlite3.Connection | None = None
    try:
        con = _conn()
        row = _select(con, _token_digest(token))
        if row is None:
            return None
        names = (
            "owner_pid", "owner_boot_id", "lease_until", "state",
            "cooldown_until", "fail_count", "generation", "owner_instance",
            "host_boot_digest", "code_head", "request_deadline",
            "heartbeat_at", "acquired_at", "last_reason",
        )
        return dict(zip(names, row))
    except (OSError, sqlite3.Error, ValueError):
        return None
    finally:
        if con is not None:
            con.close()
