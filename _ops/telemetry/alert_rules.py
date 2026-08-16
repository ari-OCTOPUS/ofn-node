#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""alert_rules.py -- Alert rules for Octopus observability failures.

Checks for conditions that indicate observability or system health problems:
  1. Retry storm: high rate of retry events in a short window
  2. Denied action: policy gate denials exceeding threshold
  3. Kill switch: any kill-switch activation (already handled, but logged here)
  4. Missing spans: trace with events but missing expected span categories
  5. Memory poisoning: quarantine count exceeding threshold
  6. Identity health regression: SOG/DARE metrics degrading

Alerts are written to _ops/state/telemetry/alerts.jsonl (append-only).
No SaaS, no network, no external notification. Alerts are file-based
and can be consumed by any downstream consumer.

Alert severity levels: INFO, WARNING, CRITICAL
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
_STATE = _OPS / "state"
_ALERTS_FILE = _STATE / "telemetry" / "alerts.jsonl"
_KILL_SWITCH = _OPS / "observatory" / "data" / "kill.switch"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _append_alert(alert: dict) -> None:
    """Append alert to alerts.jsonl. Fail-soft."""
    try:
        _ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(alert, ensure_ascii=False) + "\n"
        with open(_ALERTS_FILE, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        pass  # alerts must never crash the system


def check_retry_storm(window_minutes: int = 5,
                      threshold: int = 10) -> dict | None:
    """Check for retry storm: too many retry events in a short window.

    Reads from brain/events.py dashboard_events table.
    """
    try:
        from memory.store import DB_PATH
        if not DB_PATH.exists():
            return None
        conn = sqlite3.connect(str(DB_PATH), timeout=5, uri=True)
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()
        count = conn.execute(
            "SELECT COUNT(*) FROM dashboard_events WHERE status='retry' AND timestamp > ?",
            (cutoff,),
        ).fetchone()[0]
        conn.close()
        if count >= threshold:
            alert = {
                "schema": "alert.v1",
                "ts": _utc_iso(),
                "rule": "retry_storm",
                "severity": Severity.WARNING,
                "value": count,
                "threshold": threshold,
                "window_minutes": window_minutes,
                "message": f"{count} retry events in {window_minutes} minutes (threshold: {threshold})",
            }
            _append_alert(alert)
            return alert
    except Exception:
        pass
    return None


def check_denied_actions(window_minutes: int = 10,
                        threshold: int = 5) -> dict | None:
    """Check for high rate of denied actions (policy gate denials)."""
    try:
        from memory.store import DB_PATH
        if not DB_PATH.exists():
            return None
        conn = sqlite3.connect(str(DB_PATH), timeout=5, uri=True)
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()
        count = conn.execute(
            "SELECT COUNT(*) FROM dashboard_events WHERE status='error' AND summary LIKE '%denied%' AND timestamp > ?",
            (cutoff,),
        ).fetchone()[0]
        conn.close()
        if count >= threshold:
            alert = {
                "schema": "alert.v1",
                "ts": _utc_iso(),
                "rule": "denied_action",
                "severity": Severity.WARNING,
                "value": count,
                "threshold": threshold,
                "window_minutes": window_minutes,
                "message": f"{count} denied actions in {window_minutes} minutes (threshold: {threshold})",
            }
            _append_alert(alert)
            return alert
    except Exception:
        pass
    return None


def check_kill_switch() -> dict | None:
    """Check if kill switch is active."""
    try:
        if _KILL_SWITCH.exists():
            content = _KILL_SWITCH.read_text("utf-8", errors="replace").strip()
            alert = {
                "schema": "alert.v1",
                "ts": _utc_iso(),
                "rule": "kill_switch_active",
                "severity": Severity.CRITICAL,
                "message": f"Kill switch is active: {content[:100]}",
            }
            _append_alert(alert)
            return alert
    except OSError:
        pass
    return None


def check_missing_spans(trace_id: str,
                        expected_categories: list[str] | None = None) -> dict | None:
    """Check for missing span categories in a trace replay.

    Uses the trace_replay module to collect events and check coverage.
    """
    try:
        from trace_replay import replay_trace
        replay = replay_trace(trace_id)
        if replay.event_count == 0:
            return None
        missing = []
        expected = expected_categories or ["intent", "policy", "memory", "model", "tool", "outcome"]
        coverage_map = {
            "intent": replay.has_intent,
            "policy": replay.has_policy,
            "memory": replay.has_memory,
            "model": replay.has_model,
            "tool": replay.has_tool,
            "outcome": replay.has_outcome,
        }
        for cat in expected:
            if not coverage_map.get(cat, False):
                missing.append(cat)
        if missing:
            alert = {
                "schema": "alert.v1",
                "ts": _utc_iso(),
                "rule": "missing_spans",
                "severity": Severity.INFO,  # missing spans is informational, not necessarily an error
                "trace_id": trace_id,
                "missing_categories": missing,
                "coverage_ratio": round(replay.coverage_ratio, 3),
                "message": f"Trace {trace_id[:8]} missing span categories: {missing}",
            }
            _append_alert(alert)
            return alert
    except Exception:
        pass
    return None


def check_memory_poisoning(threshold: int = 5) -> dict | None:
    """Check for high quarantine count in memory store.

    A sudden spike in quarantined writes may indicate memory poisoning attempt.
    """
    try:
        from memory.store import DB_PATH
        if not DB_PATH.exists():
            return None
        conn = sqlite3.connect(str(DB_PATH), timeout=5, uri=True)
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE admission_state='QUARANTINED'"
            ).fetchone()[0]
        except sqlite3.OperationalError:
            # Table might not have admission_state column
            conn.close()
            return None
        conn.close()
        if count >= threshold:
            alert = {
                "schema": "alert.v1",
                "ts": _utc_iso(),
                "rule": "memory_poisoning",
                "severity": Severity.CRITICAL,
                "quarantine_count": count,
                "threshold": threshold,
                "message": f"{count} quarantined memory entries (threshold: {threshold})",
            }
            _append_alert(alert)
            return alert
    except Exception:
        pass
    return None


def check_identity_health_regression(sog_delta: float | None = None,
                                     rho_threshold: float = 0.5) -> dict | None:
    """Check for SOG/DARE metric regression.

    If SOG rho drops below threshold, identity health may be degrading.
    """
    if sog_delta is None:
        return None  # No data to check
    if sog_delta < rho_threshold:
        alert = {
            "schema": "alert.v1",
            "ts": _utc_iso(),
            "rule": "identity_health_regression",
            "severity": Severity.WARNING,
            "sog_rho": sog_delta,
            "threshold": rho_threshold,
            "message": f"SOG rho {sog_delta:.3f} below threshold {rho_threshold} — possible identity health regression",
        }
        _append_alert(alert)
        return alert
    return None


def run_all_checks(trace_id: str | None = None,
                  sog_rho: float | None = None) -> list[dict]:
    """Run all alert checks and return triggered alerts."""
    alerts: list[dict] = []
    for check_fn in [
        lambda: check_retry_storm(),
        lambda: check_denied_actions(),
        lambda: check_kill_switch(),
        lambda: check_memory_poisoning(),
        lambda: check_identity_health_regression(sog_rho) if sog_rho else None,
    ]:
        result = check_fn()
        if result:
            alerts.append(result)
    if trace_id:
        result = check_missing_spans(trace_id)
        if result:
            alerts.append(result)
    return alerts


def read_alerts(limit: int = 50) -> list[dict]:
    """Read recent alerts from the alerts.jsonl file."""
    if not _ALERTS_FILE.exists():
        return []
    try:
        lines = _ALERTS_FILE.read_text("utf-8", errors="replace").splitlines()
        alerts = []
        for line in lines[-limit:]:
            line = line.strip()
            if line:
                try:
                    alerts.append(json.loads(line))
                except ValueError:
                    continue
        return alerts
    except OSError:
        return []
