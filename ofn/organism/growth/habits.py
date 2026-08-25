from __future__ import annotations

import json
import time
from typing import Any

from ofn.organism.persistence.db import DB_LOCK
from ofn.organism.runtime.public_status import meta_value


MIN_HEARTBEAT_S = 120
MAX_HEARTBEAT_S = 300
DEFAULT_HEARTBEAT_S = 180
GROWTH_COOLDOWN_S = 3600


def set_meta(con, key: str, value: str) -> None:
    with DB_LOCK:
        con.execute(
            "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (key, value),
        )


def heartbeat_interval_s(con, fallback: float = DEFAULT_HEARTBEAT_S) -> float:
    raw = meta_value(con, "heartbeat_interval_s")
    try:
        value = float(raw) if raw is not None else float(fallback)
    except (TypeError, ValueError):
        value = float(fallback)
    return max(MIN_HEARTBEAT_S, min(MAX_HEARTBEAT_S, value))


def growth_view(con) -> dict[str, Any]:
    return {
        "heartbeat_interval_s": heartbeat_interval_s(con),
        "last_habit": meta_value(con, "last_growth_habit"),
        "parent_rhythm_lock": meta_value(con, "parent_rhythm_lock") == "1",
        "allowlist": ["heartbeat_interval_s"],
        "forbidden": [
            "external_api",
            "telegram",
            "actuators",
            "autonomy_state",
            "allowlist_ips",
        ],
    }


def _mem_available_kb(measured: dict[str, Any]) -> int | None:
    for item in measured.get("signals") or []:
        if item.get("name") == "MemAvailable_kB" and item.get("value") is not None:
            return int(item["value"])
    return None


def maybe_adapt_heartbeat(
    con,
    health_state: str,
    measured: dict[str, Any],
) -> dict[str, Any] | None:
    now = time.time()
    last_raw = meta_value(con, "last_growth_at")
    try:
        last_at = float(last_raw) if last_raw else 0.0
    except (TypeError, ValueError):
        last_at = 0.0
    if now - last_at < GROWTH_COOLDOWN_S:
        return None

    consecutive_raw = meta_value(con, "consecutive_observing", "0") or "0"
    try:
        consecutive = int(consecutive_raw)
    except ValueError:
        consecutive = 0
    if health_state in {"OBSERVING", "STABLE"}:
        consecutive += 1
    else:
        consecutive = 0
    set_meta(con, "consecutive_observing", str(consecutive))

    current = heartbeat_interval_s(con)
    mem = _mem_available_kb(measured)
    candidate = current
    reason = None
    if health_state in {"DEGRADED", "SAFE_HALT"} or (mem is not None and mem < 800 * 1024):
        if current > MIN_HEARTBEAT_S:
            candidate = max(MIN_HEARTBEAT_S, current - 30)
            reason = "body_stress_faster_watch"
    elif (
        health_state in {"OBSERVING", "STABLE"}
        and consecutive >= 3
        and mem is not None
        and mem > 2 * 1024 * 1024
        and current < MAX_HEARTBEAT_S
    ):
        candidate = min(MAX_HEARTBEAT_S, current + 30)
        reason = "stable_body_slower_rhythm"

    locked = meta_value(con, "parent_rhythm_lock") == "1"
    if locked and reason == "stable_body_slower_rhythm":
        return None

    if candidate == current or reason is None:
        return None

    evidence = {
        "reason": reason,
        "health_state": health_state,
        "mem_available_kB": mem,
        "consecutive_observing": consecutive,
    }
    return apply_heartbeat_habit(con, candidate, reason, evidence)


def apply_heartbeat_habit(
    con,
    candidate: float,
    reason: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    current = heartbeat_interval_s(con)
    candidate = max(MIN_HEARTBEAT_S, min(MAX_HEARTBEAT_S, float(candidate)))
    if candidate == current:
        return None
    now = time.time()
    prefix = "G-PARENT" if str(reason).startswith("parent_") else "G-HB"
    habit_id = f"{prefix}-{int(current)}-{int(candidate)}-{int(now)}"
    payload = dict(evidence or {})
    payload["reason"] = reason
    with DB_LOCK:
        con.execute(
            """
            INSERT INTO growth_habits(
                habit_id, status, parameter, baseline_json, candidate_json,
                evidence_json, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                habit_id,
                "applied",
                "heartbeat_interval_s",
                json.dumps({"heartbeat_interval_s": current}, sort_keys=True),
                json.dumps({"heartbeat_interval_s": candidate}, sort_keys=True),
                json.dumps(payload, sort_keys=True),
                now,
                now,
            ),
        )
    set_meta(con, "heartbeat_interval_s", str(int(candidate)))
    set_meta(con, "last_growth_habit", habit_id)
    set_meta(con, "last_growth_at", str(now))
    return {
        "habit_id": habit_id,
        "parameter": "heartbeat_interval_s",
        "from": current,
        "to": candidate,
        "reason": reason,
        "status": "applied",
    }
