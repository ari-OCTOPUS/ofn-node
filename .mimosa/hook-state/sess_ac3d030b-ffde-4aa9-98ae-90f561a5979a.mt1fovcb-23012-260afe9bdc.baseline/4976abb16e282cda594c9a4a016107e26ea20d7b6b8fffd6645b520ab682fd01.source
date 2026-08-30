#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""health_digest.py -- Observability health/safety/memory/workflow digest.

Produces a file-based digest (no Grafana/SaaS dependency) covering:
  1. Safety: kill-switch status, halted state, FREEZE flag
  2. Memory: read ratios, readback success, quarantine count
  3. Workflow: task success/failure rates, approval pending count
  4. Telemetry: system health (which trace sources are active)

Output: JSON digest file at _ops/state/telemetry/health-digest.jsonl
Also provides a query function for retrieving latest digest.

No network, no secrets, no side effects beyond writing the digest file.
Fail-soft: if any source is unavailable, that section is empty (not error).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parent.parent
_STATE = _OPS / "state"
_DIGEST_DIR = _STATE / "telemetry"
_DIGEST_FILE = _DIGEST_DIR / "health-digest.jsonl"
_OCTOPUS_QUEUE = _OPS.parent / "_octopus"
_FREEZE_FLAG = _OPS / "budget" / "FREEZE.flag"
_STOP_METABOLIC = _OPS / "STOP-METABOLIC"
_KILL_SWITCH = _OPS / "observatory" / "data" / "kill.switch"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _check_safety() -> dict[str, Any]:
    """Check safety system status."""
    status: dict[str, Any] = {
        "kill_switch": False,
        "freeze_flag": False,
        "stop_metabolic": False,
        "halted_in_queue": False,
        "status": "green",
    }
    # Kill switch
    try:
        ks = _KILL_SWITCH
        if ks.exists():
            status["kill_switch"] = True
            status["status"] = "red"
    except OSError:
        pass

    # Freeze flag
    try:
        if _FREEZE_FLAG.exists():
            status["freeze_flag"] = True
            if status["status"] == "green":
                status["status"] = "amber"
    except OSError:
        pass

    # STOP-METABOLIC
    try:
        if _STOP_METABOLIC.exists():
            status["stop_metabolic"] = True
            status["status"] = "red"
    except OSError:
        pass

    # Check pending queue for halted items
    try:
        pending_dir = _OCTOPUS_QUEUE / "queue" / "pending"
        if pending_dir.exists():
            for f in pending_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text("utf-8"))
                    if data.get("status") == "halted":
                        status["halted_in_queue"] = True
                        if status["status"] == "green":
                            status["status"] = "amber"
                        break
                except (ValueError, OSError):
                    continue
    except OSError:
        pass

    return status


def _check_memory_health() -> dict[str, Any]:
    """Check memory system health metrics."""
    metrics: dict[str, Any] = {
        "read_before_decision_ratio": None,
        "readback_success_ratio": None,
        "phase_zero_targets": {"read_before_decision": 0.95, "readback": 0.99},
        "source": None,
    }
    try:
        from memory.store import DB_PATH
        if not DB_PATH.exists():
            return metrics
        metrics["source"] = str(DB_PATH)
        conn = sqlite3.connect(str(DB_PATH), timeout=5, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            # Count memory.read events
            read_count = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name='memory.read'"
            ).fetchone()[0]
            # Count memory.readback events
            readback_ok = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name='memory.readback' AND status='ok'"
            ).fetchone()[0]
            readback_total = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name='memory.readback'"
            ).fetchone()[0]
            # Count decision tasks
            decision_agents = ("creative", "conclude", "introspect")
            placeholders = ",".join("?" * len(decision_agents))
            decisions = conn.execute(
                f"SELECT COUNT(*) FROM dashboard_events WHERE event_name IN ('task.completed','task.failed') AND agent_id IN ({placeholders}) AND trace_id IS NOT NULL AND trace_id != ''",
                decision_agents,
            ).fetchone()[0]

            if decisions > 0:
                metrics["read_before_decision_ratio"] = round(read_count / decisions, 4)
            if readback_total > 0:
                metrics["readback_success_ratio"] = round(readback_ok / readback_total, 4)
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
    except Exception:
        pass
    return metrics


def _check_workflow_health() -> dict[str, Any]:
    """Check workflow task health metrics."""
    metrics: dict[str, Any] = {
        "total_tasks": 0,
        "completed": 0,
        "failed": 0,
        "blocked": 0,
        "pending_approval": 0,
        "success_rate": None,
    }
    try:
        from memory.store import DB_PATH
        if not DB_PATH.exists():
            return metrics
        conn = sqlite3.connect(str(DB_PATH), timeout=5, uri=True)
        try:
            metrics["total_tasks"] = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name LIKE 'task.%'"
            ).fetchone()[0]
            metrics["completed"] = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.completed'"
            ).fetchone()[0]
            metrics["failed"] = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.failed'"
            ).fetchone()[0]
            metrics["blocked"] = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.blocked'"
            ).fetchone()[0]
            metrics["pending_approval"] = conn.execute(
                "SELECT COUNT(*) FROM dashboard_events WHERE approval_state='pending'"
            ).fetchone()[0]
            task_total = metrics["completed"] + metrics["failed"]
            if task_total > 0:
                metrics["success_rate"] = round(metrics["completed"] / task_total, 4)
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
    except Exception:
        pass
    return metrics


def _check_telemetry_health() -> dict[str, Any]:
    """Check which telemetry sources are active and their basic stats."""
    from pathlib import Path

    health: dict[str, Any] = {
        "semantic_trace": {"active": False, "record_count": 0},
        "otel_traces": {"active": False, "record_count": 0},
        "cognitive_runs": {"active": False, "run_count": 0},
        "budget_telemetry": {"active": False},
    }
    # Semantic trace
    st_path = _STATE / "cortex" / "semantic-trace.jsonl"
    if st_path.exists():
        try:
            lines = st_path.read_text("utf-8", errors="replace").splitlines()
            health["semantic_trace"]["active"] = True
            health["semantic_trace"]["record_count"] = sum(
                1 for l in lines if l.strip()
            )
        except OSError:
            pass

    # OTel traces
    ot_path = _STATE / "otel" / "traces.jsonl"
    if ot_path.exists():
        try:
            lines = ot_path.read_text("utf-8", errors="replace").splitlines()
            health["otel_traces"]["active"] = True
            health["otel_traces"]["record_count"] = sum(
                1 for l in lines if l.strip()
            )
        except OSError:
            pass

    # Cognitive runs
    cog_dir = _STATE / "cognitive" / "runs"
    if cog_dir.exists():
        runs = list(cog_dir.glob("*.jsonl"))
        if runs:
            health["cognitive_runs"]["active"] = True
            health["cognitive_runs"]["run_count"] = len(runs)

    # Budget telemetry
    tel_latest = _DIGEST_DIR / "telemetry-latest.json"
    if tel_latest.exists():
        health["budget_telemetry"]["active"] = True

    return health


def produce_digest(write: bool = True) -> dict[str, Any]:
    """Produce a complete health digest.

    Args:
        write: If True, append the digest to the JSONL file.

    Returns:
        Digest dict.
    """
    digest = {
        "schema": "health-digest.v1",
        "ts": _utc_iso(),
        "safety": _check_safety(),
        "memory": _check_memory_health(),
        "workflow": _check_workflow_health(),
        "telemetry_systems": _check_telemetry_health(),
    }

    if write:
        try:
            _DIGEST_DIR.mkdir(parents=True, exist_ok=True)
            line = json.dumps(digest, ensure_ascii=False) + "\n"
            with open(_DIGEST_FILE, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass  # digest must never crash the system

    return digest


def read_latest_digest() -> dict[str, Any] | None:
    """Read the most recent digest from the JSONL file."""
    if not _DIGEST_FILE.exists():
        return None
    try:
        lines = _DIGEST_FILE.read_text("utf-8", errors="replace").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if line:
                return json.loads(line)
    except (OSError, ValueError):
        pass
    return None
