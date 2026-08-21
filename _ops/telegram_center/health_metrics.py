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
    "last_update_received_at", "last_progress_at",
)


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


def _load() -> dict:
    state = _bounded_read(poll_health_path())
    state.setdefault("counters", {})
    return state


def _save(state: dict) -> None:
    _bounded_write(poll_health_path(), state)


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
    return state


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
    state = _load()
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
