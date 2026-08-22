#!/usr/bin/env python3
"""Durable typed-poll retry schedule and restart-safe backoff."""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("poll-schedule")
_OPS = Path(__file__).resolve().parent.parent
for _path in (str(_OPS), str(_OPS / "telegram_center")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import poll_schedule as schedule  # noqa: E402

TOKEN = "123456789:AA" + "Q" * 32
_SEQ = 0


def _token(label: str) -> str:
    global _SEQ
    _SEQ += 1
    return f"{TOKEN}-{label}-{_SEQ}"


def t_a_empty_token_is_stopped():
    assert schedule.check("") == {
        "ok": False, "allowed": False, "kind": "STOPPED",
        "reason": "no-token",
    }


def t_b_server_retry_after_is_preserved_in_full():
    token = _token("429")
    stored = schedule.record_failure(
        token, kind="RATE_LIMITED", reason="rate-limited",
        retry_after_s=75.0, now=100.0)
    assert stored["ok"] is True
    assert stored["retry_after_s"] == 75.0
    blocked = schedule.check(token, now=174.0)
    assert blocked["allowed"] is False
    assert 0.9 <= blocked["retry_after_s"] <= 1.1
    assert schedule.check(token, now=175.0)["allowed"] is True


def t_c_failure_streak_survives_expiry_and_doubles_delay():
    token = _token("backoff")
    first = schedule.record_failure(
        token, kind="TIMEOUT", reason="timeout", now=10.0)
    assert first["failure_streak"] == 1
    assert first["retry_after_s"] == 1.0
    assert schedule.check(token, now=11.0)["allowed"] is True
    second = schedule.record_failure(
        token, kind="TIMEOUT", reason="timeout", now=11.0)
    assert second["failure_streak"] == 2
    assert second["retry_after_s"] == 2.0


def t_d_schedule_persists_across_module_consumers():
    token = _token("restart")
    schedule.record_failure(
        token, kind="DNS_ERROR", reason="dns", retry_after_s=30, now=50.0)
    snap = schedule.snapshot(token)
    assert snap["kind"] == "DNS_ERROR"
    assert snap["not_before"] == 80.0
    assert schedule.check(token, now=60.0)["reason"] == "dns"


def t_e_success_is_the_only_reset():
    token = _token("success")
    schedule.record_failure(token, kind="HTTP_5XX", now=20.0)
    assert schedule.snapshot(token) is not None
    assert schedule.record_success(token)["ok"] is True
    assert schedule.snapshot(token) is None
    assert schedule.check(token, now=20.0)["allowed"] is True


def t_f_tokens_are_isolated_and_one_way():
    first = _token("one")
    second = _token("two")
    schedule.record_failure(first, kind="RATE_LIMITED", retry_after_s=60)
    assert schedule.check(first)["allowed"] is False
    assert schedule.check(second)["allowed"] is True
    assert first.encode("utf-8") not in schedule._db().read_bytes()
    assert schedule._token_digest(first) != first


def t_g_clock_regression_fails_closed():
    token = _token("clock")
    schedule.record_failure(token, kind="TIMEOUT", now=100.0)
    con = schedule._conn()
    con.execute(
        "UPDATE schedule SET updated_at=? WHERE token_digest=?",
        (200.0, schedule._token_digest(token)),
    )
    con.close()
    denied = schedule.check(token, now=100.0)
    assert denied["allowed"] is False
    assert denied["reason"] == "schedule-clock-regression"


def t_h_storage_error_fails_closed():
    real = schedule._conn
    schedule._conn = lambda: (_ for _ in ()).throw(
        sqlite3.OperationalError("locked"))
    try:
        result = schedule.check(_token("db"))
    finally:
        schedule._conn = real
    assert result["allowed"] is False
    assert result["reason"] == "schedule-error"
    assert result["error_class"] == "OperationalError"


def t_i_http_4xx_and_webhook_use_bounded_max_delay():
    for kind in ("HTTP_4XX", "WEBHOOK_PRESENT"):
        token = _token(kind)
        stored = schedule.record_failure(token, kind=kind, now=0.0)
        assert stored["retry_after_s"] == schedule._MAX_DELAY_S


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_poll_schedule: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
