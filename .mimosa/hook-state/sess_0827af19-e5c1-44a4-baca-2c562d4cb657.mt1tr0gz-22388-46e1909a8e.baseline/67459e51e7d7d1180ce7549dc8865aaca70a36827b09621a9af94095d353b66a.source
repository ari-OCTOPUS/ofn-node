"""
Governance — Kill switch + Spend cap (INV-3)
Non-removable. Every agent action MUST call check_and_enforce() first.

Kill switch: presence of KILL_SWITCH_FILE halts all external actions.
Spend cap: per-action AUD cap + per-day AUD cap, tracked via cost_events table.
"""
import json
import uuid
from datetime import datetime, date
from pathlib import Path

from .config import config
from .database import get_connection


# ── Exceptions ────────────────────────────────────────────────────────────────

class KillSwitchActivated(Exception):
    """Raised when the kill switch is active. No external action may proceed."""
    pass


class SpendCapExceeded(Exception):
    """Raised when an action would exceed a spend cap."""
    pass


# ── Kill switch ───────────────────────────────────────────────────────────────

def is_kill_switch_active() -> bool:
    return Path(config.KILL_SWITCH_FILE).exists()


def activate_kill_switch(operator_chat_id: int, reason: str) -> None:
    """
    Activate the kill switch. Logs to audit BEFORE writing file.
    Once active, check_and_enforce() raises KillSwitchActivated everywhere.
    """
    from . import audit  # late import to avoid circular
    audit.append("KILL_SWITCH_ACTIVATED", "system", {
        "operator_chat_id": operator_chat_id,
        "reason": reason,
    })
    ks = Path(config.KILL_SWITCH_FILE)
    ks.parent.mkdir(parents=True, exist_ok=True)
    ks.write_text(json.dumps({
        "activated_at": datetime.utcnow().isoformat(),
        "reason": reason,
        "operator_chat_id": operator_chat_id,
    }))


def deactivate_kill_switch(operator_chat_id: int) -> None:
    """Deactivate the kill switch. Logs to audit."""
    from . import audit
    audit.append("KILL_SWITCH_DEACTIVATED", "system", {
        "operator_chat_id": operator_chat_id,
    })
    ks = Path(config.KILL_SWITCH_FILE)
    if ks.exists():
        ks.unlink()


def get_kill_switch_info() -> dict | None:
    """Return kill switch metadata if active, else None."""
    ks = Path(config.KILL_SWITCH_FILE)
    if not ks.exists():
        return None
    try:
        return json.loads(ks.read_text())
    except Exception:
        return {"status": "active", "info": "unreadable"}


# ── Spend cap ─────────────────────────────────────────────────────────────────

def log_cost(event_type: str, agent_id: str, model: str,
             cost_usd: float, tokens_in: int = 0, tokens_out: int = 0) -> str:
    """
    Record a cost event. Returns the cost_event ID.
    cost_aud = cost_usd * FX_AUD_USD (from CONFIG).
    """
    cost_aud = config.usd_to_aud(cost_usd)
    event_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO cost_events
               (id, event_type, agent_id, model, cost_usd, cost_aud,
                tokens_in, tokens_out, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, event_type, agent_id, model, cost_usd, cost_aud,
             tokens_in, tokens_out, timestamp)
        )
        conn.commit()
    finally:
        conn.close()

    return event_id


def _utc_today() -> date:
    """
    Single source of truth for the governance 'day'.
    cost_events timestamps are written with datetime.utcnow(); the daily-cap
    query MUST use the same clock. Using local date.today() here silently
    zeroed the daily spend for the hours where Sydney local date is ahead of
    UTC (midnight-~10:00 AEST) -- an INV-3 cap bypass. Fixed 2026-07-02.
    """
    return datetime.utcnow().date()


def _day_range(d: date):
    """[start, end) ISO bounds for one UTC day -- lexicographic on ISO-8601,
    so the query is sargable (uses idx_cost_events_ts) instead of the old
    date(timestamp)=? which forced a full-table scan on every
    check_and_enforce call."""
    from datetime import timedelta
    start = d.isoformat()
    end = (d + timedelta(days=1)).isoformat()
    return start, end


def get_daily_spend_aud(for_date: date = None) -> float:
    """Return total AUD spent today (UTC day, or for_date)."""
    start, end = _day_range(for_date or _utc_today())
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_aud), 0) as total FROM cost_events "
            "WHERE timestamp >= ? AND timestamp < ?",
            (start, end)
        ).fetchone()
        return float(row["total"]) if row else 0.0
    finally:
        conn.close()


def get_spend_status() -> dict:
    """Full spend status dashboard (for /spend Telegram command)."""
    today_aud = get_daily_spend_aud()
    conn = get_connection()
    try:
        _start, _end = _day_range(_utc_today())
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) as usd, COUNT(*) as n "
            "FROM cost_events WHERE timestamp >= ? AND timestamp < ?",
            (_start, _end)
        ).fetchone()
    finally:
        conn.close()

    return {
        "date": _utc_today().isoformat(),
        "daily_total_aud": round(today_aud, 4),
        "daily_total_usd": round(float(row["usd"]) if row else 0.0, 4),
        "daily_cap_aud": config.SPEND_CAP_PER_DAY_AUD,
        "per_action_cap_aud": config.SPEND_CAP_PER_ACTION_AUD,
        "remaining_aud": round(config.SPEND_CAP_PER_DAY_AUD - today_aud, 4),
        "events_today": int(row["n"]) if row else 0,
        "kill_switch_active": is_kill_switch_active(),
    }


# ── Main enforcement gate ─────────────────────────────────────────────────────

def check_and_enforce(estimated_cost_aud: float, agent_id: str) -> None:
    """
    MUST be called before every external action (LLM call, search, sync, publish).
    Raises KillSwitchActivated or SpendCapExceeded if limits are breached.

    Args:
        estimated_cost_aud: estimated AUD cost of the action about to run
        agent_id:           ID of the calling agent (for logging)
    """
    # 1. Kill switch check — highest priority
    if is_kill_switch_active():
        raise KillSwitchActivated(
            f"Kill switch active. Agent '{agent_id}' blocked. "
            f"Deactivate via Telegram /kill_off."
        )

    # 2. Per-action cap
    if estimated_cost_aud > config.SPEND_CAP_PER_ACTION_AUD:
        raise SpendCapExceeded(
            f"Per-action cap exceeded: AUD ${estimated_cost_aud:.4f} > "
            f"cap AUD ${config.SPEND_CAP_PER_ACTION_AUD:.2f}. "
            f"Raise SPEND_CAP_PER_ACTION_AUD in .env if intentional."
        )

    # 3. Daily cap (including the current action)
    today_aud = get_daily_spend_aud()
    if today_aud + estimated_cost_aud > config.SPEND_CAP_PER_DAY_AUD:
        raise SpendCapExceeded(
            f"Daily cap would be exceeded: "
            f"spent AUD ${today_aud:.2f} + action AUD ${estimated_cost_aud:.4f} "
            f"> daily cap AUD ${config.SPEND_CAP_PER_DAY_AUD:.2f}."
        )
