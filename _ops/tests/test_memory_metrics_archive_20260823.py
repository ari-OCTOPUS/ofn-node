#!/usr/bin/env python3
"""Regression: memory KPI must include events moved by housekeeping."""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

FOURD = Path(__file__).resolve().parents[2] / "4d_system"
sys.path.insert(0, str(FOURD))

from brain import events  # noqa: E402
from brain import memory_read_patch as mrp  # noqa: E402


SCHEMA = """
CREATE TABLE {table} (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    trace_id TEXT,
    agent_id TEXT,
    event_name TEXT,
    status TEXT
)
"""


def _insert(conn, table, row):
    conn.execute(
        f"INSERT INTO {table} "
        "(id,timestamp,trace_id,agent_id,event_name,status) VALUES (?,?,?,?,?,?)",
        row,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "events.db"
        conn = sqlite3.connect(db)
        conn.execute(SCHEMA.format(table="events_archive"))
        conn.execute(SCHEMA.format(table="dashboard_events"))

        _insert(conn, "events_archive",
                (1, "2026-07-01T00:00:00", "old-miss", "creative",
                 "task.completed", "ok"))
        _insert(conn, "events_archive",
                (2, "2026-07-01T00:01:00", "old-hit", "memory:hypotheses",
                 "memory.read", "ok"))
        _insert(conn, "events_archive",
                (3, "2026-07-01T00:01:01", "old-hit", "creative",
                 "task.completed", "ok"))
        _insert(conn, "events_archive",
                (4, "2026-07-01T00:02:00", "old-rb", "memory:readback",
                 "memory.readback", "error"))

        _insert(conn, "dashboard_events",
                (11, "2026-08-01T00:00:00", "new-hit", "memory:experiments",
                 "memory.read", "ok"))
        _insert(conn, "dashboard_events",
                (12, "2026-08-01T00:00:01", "new-hit", "introspect",
                 "task.completed", "ok"))
        _insert(conn, "dashboard_events",
                (13, "2026-08-01T00:00:02", "new-rb", "memory:readback",
                 "memory.readback", "ok"))
        conn.commit()
        conn.close()

        original = events._db_path
        events._db_path = lambda: db
        try:
            full = mrp.telemetry_metrics(after_id=0)
            assert full["decision_jobs"] == 3, full
            assert full["decision_jobs_with_read"] == 2, full
            assert abs(full["memory_read_before_decision_ratio"] - (2 / 3)) < 1e-12, full
            assert full["readback_total"] == 2 and full["readback_ok"] == 1, full
            assert abs(full["memory_readback_success_ratio"] - 0.5) < 1e-12, full

            recent = mrp.telemetry_metrics(after_id=10)
            assert recent["decision_jobs"] == 1, recent
            assert recent["decision_jobs_with_read"] == 1, recent
            assert recent["memory_read_before_decision_ratio"] == 1.0, recent
            assert recent["readback_total"] == 1 and recent["readback_ok"] == 1, recent
        finally:
            events._db_path = original

    print("PASS memory metrics include archive and preserve after_id")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
