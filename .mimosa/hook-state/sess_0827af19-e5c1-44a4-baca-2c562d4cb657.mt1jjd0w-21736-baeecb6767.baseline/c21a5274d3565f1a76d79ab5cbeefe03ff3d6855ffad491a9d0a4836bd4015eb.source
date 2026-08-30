#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_alert_rules_testable.py -- Tests for refactored alert_rules (MEDIUM-002 fix).

Tests check_retry_storm() and check_denied_actions() with an injectable
test database, proving that the MEDIUM-002 gap (zero test coverage due to
hardcoded DB dependency) is now closed.

$0 | stdlib-only | sqlite3 temp DB | no network
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "telemetry")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import alert_rules

passed = 0
failed = 0


def ok(name: str):
    global passed
    passed += 1
    print(f"  [PASS] {name}")


def fail(name: str, reason: str):
    global failed
    failed += 1
    print(f"  [FAIL] {name}: {reason}")


def run(fn):
    try:
        fn()
    except AssertionError as e:
        fail(fn.__name__, str(e))
    except Exception as e:
        fail(fn.__name__, f"{type(e).__name__}: {e}")


def _make_test_db() -> Path:
    """Create a temporary SQLite DB with dashboard_events table."""
    db_path = Path(tempfile.mktemp(suffix=".db", prefix="alert_test_"))
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE dashboard_events ("
        "id INTEGER PRIMARY KEY, "
        "status TEXT, "
        "summary TEXT, "
        "timestamp TEXT)"
    )
    conn.commit()
    conn.close()
    return db_path


def _insert_events(db_path: Path, events: list[tuple]):
    """Insert events into test DB.
    events: list of (status, summary, timestamp)
    """
    conn = sqlite3.connect(str(db_path))
    from datetime import datetime, timezone, timedelta
    for status, summary, minutes_ago in events:
        ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
              ).isoformat()
        conn.execute(
            "INSERT INTO dashboard_events (status, summary, timestamp) VALUES (?, ?, ?)",
            (status, summary, ts))
    conn.commit()
    conn.close()


def t_medium002_01_no_events_no_alert():
    """No retry events => no alert."""
    db = _make_test_db()
    try:
        result = alert_rules.check_retry_storm(db_path=db)
        assert result is None, f"Expected no alert, got {result}"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_01_no_events_no_alert")


def t_medium002_02_below_threshold_no_alert():
    """Retry count below threshold => no alert."""
    db = _make_test_db()
    try:
        _insert_events(db, [("retry", "retry error", i) for i in range(5)])
        result = alert_rules.check_retry_storm(threshold=10, db_path=db)
        assert result is None, f"Expected no alert, got {result}"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_02_below_threshold_no_alert")


def t_medium002_03_above_threshold_alert_fires():
    """Retry count at/above threshold => alert fires."""
    db = _make_test_db()
    try:
        # Insert 12 events within 1 minute (all within 5-min default window)
        _insert_events(db, [("retry", "retry error", i * 0.05) for i in range(12)])
        result = alert_rules.check_retry_storm(threshold=10, db_path=db)
        assert result is not None, "Expected alert to fire"
        assert result["rule"] == "retry_storm"
        assert result["severity"] == alert_rules.Severity.WARNING
        assert result["value"] >= 10
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_03_above_threshold_alert_fires")


def t_medium002_04_stale_events_out_of_window():
    """Old events outside the window don't trigger alert."""
    db = _make_test_db()
    try:
        # Insert 15 events but all 10 minutes ago (window default = 5min)
        _insert_events(db, [("retry", "retry error", 10 + i) for i in range(15)])
        result = alert_rules.check_retry_storm(threshold=10, db_path=db)
        assert result is None, f"Old events should not trigger: {result}"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_04_stale_events_out_of_window")


def t_medium002_05_denied_actions_below_threshold():
    """Denied actions below threshold => no alert."""
    db = _make_test_db()
    try:
        _insert_events(db, [("error", "access denied", i) for i in range(3)])
        result = alert_rules.check_denied_actions(threshold=5, db_path=db)
        assert result is None, f"Expected no alert, got {result}"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_05_denied_actions_below_threshold")


def t_medium002_06_denied_actions_above_threshold():
    """Denied actions at/above threshold => alert fires."""
    db = _make_test_db()
    try:
        _insert_events(db, [("error", "access denied for user X", i * 0.1)
                            for i in range(7)])
        result = alert_rules.check_denied_actions(threshold=5, db_path=db)
        assert result is not None, "Expected alert to fire"
        assert result["rule"] == "denied_action"
        assert result["value"] >= 5
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_06_denied_actions_above_threshold")


def t_medium002_07_non_denied_errors_not_counted():
    """Error events without 'denied' in summary are not counted."""
    db = _make_test_db()
    try:
        _insert_events(db, [("error", "timeout", i) for i in range(10)])
        result = alert_rules.check_denied_actions(threshold=5, db_path=db)
        assert result is None, "Non-denied errors should not trigger"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_07_non_denied_errors_not_counted")


def t_medium002_08_custom_window():
    """Custom window parameter works correctly."""
    db = _make_test_db()
    try:
        # 8 events at 3 minutes ago, with 2-minute window should not trigger
        _insert_events(db, [("retry", "retry", 3 + i * 0.1) for i in range(8)])
        result = alert_rules.check_retry_storm(
            threshold=5, window_minutes=2, db_path=db)
        assert result is None, f"Events outside 2-min window: {result}"

        # With 5-minute window, should trigger
        result2 = alert_rules.check_retry_storm(
            threshold=5, window_minutes=5, db_path=db)
        assert result2 is not None, "Events within 5-min window should trigger"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_08_custom_window")


def t_medium002_09_missing_db_path_no_crash():
    """Non-existent DB path returns None (no crash)."""
    result = alert_rules.check_retry_storm(
        db_path=Path("/nonexistent/path/alert.db"))
    assert result is None
    ok("medium002_09_missing_db_path_no_crash")


def t_medium002_10_alert_schema_fields():
    """Alert dict has all expected fields."""
    db = _make_test_db()
    try:
        # Insert 15 events within 1 minute
        _insert_events(db, [("retry", "retry", i * 0.05) for i in range(15)])
        result = alert_rules.check_retry_storm(threshold=10, db_path=db)
        assert result is not None
        for field in ("schema", "ts", "rule", "severity", "value",
                      "threshold", "window_minutes", "message"):
            assert field in result, f"Missing field: {field}"
        assert result["schema"] == "alert.v1"
    finally:
        db.unlink(missing_ok=True)
    ok("medium002_10_alert_schema_fields")


if __name__ == "__main__":
    checks = sorted([(n, f) for n, f in globals().items()
                    if n.startswith("t_") and callable(f)],
                   key=lambda x: x[0])

    print(f"test_alert_rules_testable (MEDIUM-002) -- {len(checks)} checks")
    print("=" * 60)

    for name, fn in checks:
        run(fn)

    total = passed + failed
    print("=" * 60)
    if failed:
        print(f"FAIL {passed}/{total} ({failed} failures)")
        sys.exit(1)
    else:
        print(f"PASS {passed}/{total} (0 failures)")
        sys.exit(0)
