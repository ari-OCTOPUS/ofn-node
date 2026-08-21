#!/usr/bin/env python3
"""Telegram loop health semantics — granular metrics and timestamps.

Distinct counters and timestamps per the 2026-08-21 milestone correction:

  poll_started_total / poll_completed_total / poll_empty_total /
  poll_updates_total / poll_timeout_total / poll_dns_stall_total /
  poll_409_total / config_read_timeout_total / config_cache_fallback_total /
  watchdog_restart_total / active_transport_workers / active_config_workers /
  process_thread_count

  last_poll_started_at / last_poll_completed_at / last_empty_poll_at /
  last_update_received_at / last_progress_at

Health is last_poll_completed_at (empty polls are healthy); last_update_received_at
alone is NEVER health — the owner may simply not have sent anything.
"""
from __future__ import annotations

import copy
import json
import os
import threading
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent

_COUNTER_KEYS = (
    "poll_started_total", "poll_completed_total", "poll_empty_total",
    "poll_updates_total", "poll_timeout_total", "poll_dns_stall_total",
    "poll_409_total", "config_read_timeout_total", "config_cache_fallback_total",
    "watchdog_restart_total",
)
_TS_KEYS = (
    "last_poll_started_at", "last_poll_completed_at", "last_empty_poll_at",
    "last_update_received_at", "last_progress_at", "last_dispatch_completed_at",
)

_MEM: dict | None = None
_MEM_PATH: str | None = None
_MEM_GEN: tuple = (0, 0)
_MEM_LOCK = threading.Lock()
_DEBUG_LOG = Path(r"f:\backup\debug-4ab476.log")


def _root() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def poll_health_path() -> Path:
    return _root() / "telegram" / "poll-health.json"


def _bounded_read(path: Path) -> dict:
    try:
        import bounded_io as _bio
        text = _bio.read_text(path)
        if text is None:
            return {}
        d = json.loads(text)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _bounded_write(path: Path, state: dict) -> None:
    try:
        import bounded_io as _bio
        tmp = path.with_suffix(".json.tmp")
        if _bio.write_text(tmp, json.dumps(state, ensure_ascii=False)):
            os.replace(tmp, path)
    except OSError:
        pass


def _dbg(location: str, message: str, data: dict, hypothesis_id: str, run_id: str = "post-fix") -> None:
    # #region agent log
    try:
        rec = {
            "sessionId": "4ab476",
            "timestamp": int(time.time() * 1000),
            "location": location,
            "message": message,
            "data": data,
            "hypothesisId": hypothesis_id,
            "runId": run_id,
        }
        with _DEBUG_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # #endregion


def reset_memory() -> None:
    """Test helper: drop in-memory HealthState (does not delete disk)."""
    global _MEM, _MEM_PATH, _MEM_GEN
    with _MEM_LOCK:
        _MEM = None
        _MEM_PATH = None
        _MEM_GEN = (0, 0)


def _file_gen(path: Path) -> tuple:
    try:
        st = path.stat()
        return (int(st.st_mtime_ns), int(st.st_size))
    except OSError:
        return (0, 0)


def _blank() -> dict:
    return {
        "counters": {},
        "last_ok_ts": 0,
        "consecutive_failures": 0,
        "last_reason": "",
    }


def _load(*, force_disk: bool = False) -> dict:
    """In-memory HealthState. Disk is read on boot, missing file, or external change."""
    global _MEM, _MEM_PATH, _MEM_GEN
    path = poll_health_path()
    key = str(path)
    gen = _file_gen(path)
    with _MEM_LOCK:
        if (
            not force_disk
            and _MEM is not None
            and _MEM_PATH == key
            and gen == _MEM_GEN
            and path.exists()
        ):
            return _MEM
        raw = _bounded_read(path)
        state = raw if isinstance(raw, dict) and raw else _blank()
        state.setdefault("counters", {})
        state.setdefault("last_ok_ts", 0)
        state.setdefault("consecutive_failures", 0)
        state.setdefault("last_reason", "")
        _MEM = state
        _MEM_PATH = key
        _MEM_GEN = gen if path.exists() else (0, 0)
        _dbg(
            "health_metrics.py:_load",
            "health state loaded",
            {"disk_read": True, "path_exists": path.exists(),
             "counters": dict(state.get("counters") or {})},
            "H1",
        )
        return _MEM


def _save(state: dict) -> None:
    global _MEM, _MEM_PATH, _MEM_GEN
    path = poll_health_path()
    with _MEM_LOCK:
        _MEM = state
        _MEM_PATH = str(path)
    _bounded_write(path, state)
    with _MEM_LOCK:
        _MEM_GEN = _file_gen(path)


def record_poll(*, ok: bool, reason: str = "", started_at: float | None = None,
                completed_at: float | None = None, updates_n: int = 0,
                empty: bool = False, timeout: bool = False,
                dns_stall: bool = False, is_409: bool = False,
                config_workers: int = 0) -> dict:
    """Record one poll round with granular counters/timestamps."""
    state = _load()
    counters = state["counters"]
    now = time.time()

    def inc(key: str, amount: int = 1) -> None:
        counters[key] = int(counters.get(key, 0)) + int(amount)

    if started_at is not None:
        state["last_poll_started_at"] = started_at
        inc("poll_started_total")
    if completed_at is not None:
        state["last_poll_completed_at"] = completed_at
        inc("poll_completed_total")
    if empty:
        state["last_empty_poll_at"] = now
        inc("poll_empty_total")
    if updates_n > 0:
        state["last_update_received_at"] = now
        inc("poll_updates_total", updates_n)
    if timeout:
        inc("poll_timeout_total")
    if dns_stall:
        inc("poll_dns_stall_total")
    if is_409:
        inc("poll_409_total")
    state["last_progress_at"] = now
    state["process_thread_count"] = threading.active_count()
    try:
        import bounded_io as _bio
        state["active_transport_workers"] = _bio.active_worker_count()
    except Exception:  # noqa: BLE001
        state["active_transport_workers"] = 0
    state["active_config_workers"] = int(config_workers)
    if ok:
        state["last_ok_ts"] = now
        state["consecutive_failures"] = 0
        state["last_reason"] = ""
    else:
        state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
        state["last_reason"] = str(reason or "unknown")[:80]
    state["last_round_ts"] = now
    _save(state)
    # #region agent log
    try:
        n = int((state.get("counters") or {}).get("poll_completed_total") or 0)
        if n <= 2 or (not ok) or n % 10 == 0:
            _dbg(
                "health_metrics.py:record_poll",
                "poll recorded (write-through, no re-read)",
                {"ok": ok, "empty": empty, "completed_total": n,
                 "did_disk_write": True, "in_memory": True},
                "H1",
            )
    except Exception:
        pass
    # #endregion
    if not ok:
        try:
            inc_path = poll_health_path().with_name("poll-health-incidents.jsonl")
            line = json.dumps({"ts": now, "reason": str(reason or "")[:80],
                               "ok": False}, ensure_ascii=False)
            with inc_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass
    return state


def record_dispatch(*, completed_at: float | None = None) -> dict:
    """Mark last_dispatch_completed_at — distinct from poll timestamps."""
    state = _load()
    now = time.time() if completed_at is None else float(completed_at)
    state["last_dispatch_completed_at"] = now
    state["last_progress_at"] = now
    _save(state)
    _dbg("health_metrics.py:record_dispatch", "dispatch completed",
         {"last_dispatch_completed_at": now}, "H5")
    return state


def classify(*, now: float | None = None, hung_after_s: float = 300.0,
             process_alive: bool = True, lease_duplicate: bool = False,
             dns_stall: bool = False, config_stall: bool = False,
             queue_blocked: bool = False, poll_in_progress: bool = False) -> dict:
    """T5 taxonomy. Does not kill processes — watchdog PS1 remains owner of restart."""
    now = time.time() if now is None else now
    if not process_alive:
        state = "PROCESS_DEAD"
    elif lease_duplicate:
        state = "DUPLICATE_CONSUMER"
    elif queue_blocked:
        state = "QUEUE_BLOCKED"
    elif dns_stall:
        state = "DNS_STALLED"
    elif config_stall:
        state = "CONFIG_STALLED"
    elif poll_in_progress:
        state = "POLL_IN_PROGRESS"
    else:
        st = snapshot()
        truth = watchdog_truth(now=now, hung_after_s=hung_after_s)
        completed = st.get("last_poll_completed_at")
        started = st.get("last_poll_started_at")
        counters = st.get("counters") or {}
        if not truth["healthy"]:
            if isinstance(started, (int, float)) and (
                    not isinstance(completed, (int, float)) or started > float(completed)
            ):
                state = "POLL_TIMED_OUT"
            else:
                state = "MAIN_LOOP_HUNG"
        elif int(counters.get("poll_empty_total") or 0) > 0 and int(
                counters.get("poll_updates_total") or 0) == 0:
            state = "HEALTHY_EMPTY_POLL"
        elif int(counters.get("poll_updates_total") or 0) == 0:
            state = "NO_UPDATES"
        else:
            state = "HEALTHY_EMPTY_POLL"
    out = {"state": state, "process_alive": bool(process_alive)}
    _dbg("health_metrics.py:classify", "watchdog taxonomy", out, "H4")
    return out


def record_config_event(kind: str, workers: int = 0) -> dict:
    """config_read_timeout_total / config_cache_fallback_total from center."""
    state = _load()
    counters = state["counters"]
    key = f"config_{kind}_total"
    if key not in _COUNTER_KEYS:
        return state
    counters[key] = int(counters.get(key, 0)) + 1
    state["active_config_workers"] = int(workers)
    _save(state)
    return state


def snapshot() -> dict:
    state = copy.deepcopy(_load())
    for key in _COUNTER_KEYS:
        state["counters"].setdefault(key, 0)
    for key in _TS_KEYS:
        state.setdefault(key, None)
    # owner-order aliases (2026-08-21 Wave A): active_workers / thread_count
    state.setdefault("active_workers", int(state.get("active_transport_workers", 0)))
    state.setdefault("thread_count", int(state.get("process_thread_count", 0)))
    return state


def watchdog_truth(now: float | None = None, hung_after_s: float = 300.0) -> dict:
    """One truth source for the external watchdog.

    HEALTH = freshness of last_poll_completed_at (empty long polls are valid
    progress — the owner simply may not have sent anything). last_update_received_at
    alone is NEVER health; a stale update timestamp with a fresh poll completion
    must not be treated as a hang (watchdog false-positive prevention, Wave A).
    """
    now = time.time() if now is None else now
    st = snapshot()
    completed = st.get("last_poll_completed_at")
    last_update = st.get("last_update_received_at")
    progress = st.get("last_progress_at")
    healthy = False
    based_on = "no-data"
    if isinstance(completed, (int, float)) and completed > 0:
        age = now - float(completed)
        healthy = age < float(hung_after_s)
        based_on = "last_poll_completed_at"
    elif isinstance(progress, (int, float)) and progress > 0:
        healthy = (now - float(progress)) < float(hung_after_s)
        based_on = "last_progress_at"
    return {
        "healthy": bool(healthy),
        "based_on": based_on,
        "last_poll_completed_age_s": round(now - float(completed), 1) if isinstance(completed, (int, float)) and completed > 0 else None,
        "last_update_received_age_s": round(now - float(last_update), 1) if isinstance(last_update, (int, float)) and last_update > 0 else None,
        "hung_after_s": float(hung_after_s),
    }
