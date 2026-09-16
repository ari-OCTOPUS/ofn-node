#!/usr/bin/env python3
"""Fail-closed polling lease: ownership, fencing, cooldown, and storage errors."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("poll-lease")
_OPS = Path(__file__).resolve().parent.parent
for _path in (str(_OPS), str(_OPS / "telegram_center")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import poll_lease as pl  # noqa: E402

TOKEN = "123456789:AA" + "L" * 32
_SEQ = 0


def _token(label: str) -> str:
    global _SEQ
    _SEQ += 1
    return f"{TOKEN}-{label}-{_SEQ}"


def _foreign_acquire(token: str) -> dict:
    code = (
        "import json,sys;"
        f"sys.path.insert(0,{str(_OPS / 'telegram_center')!r});"
        "import poll_lease;"
        f"print(json.dumps(poll_lease.assert_poll_lease({token!r})))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True,
        timeout=30, env=dict(os.environ),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def t_a_empty_token_fails_closed_without_db():
    assert pl.assert_poll_lease("") == {"ok": False, "reason": "no-token"}


def t_b_first_consumer_acquires_generation_one():
    token = _token("first")
    result = pl.assert_poll_lease(token, request_deadline=time.time() + 30)
    assert result["ok"] is True and result["generation"] == 1
    snap = pl.lease_snapshot(token)
    assert snap["owner_pid"] == os.getpid()
    assert snap["state"] == "ACTIVE"
    assert snap["request_deadline"] > time.time()
    assert len(snap["owner_instance"]) == 32
    assert len(snap["host_boot_digest"]) == 64


def t_c_same_process_cannot_overlap_requests():
    token = _token("same-process")
    acquired = pl.assert_poll_lease(
        token, request_deadline=time.time() + 30.0)
    assert acquired["ok"] is True
    denied = pl.assert_poll_lease(token)
    assert denied["ok"] is False
    assert denied["reason"] == "request-in-flight"
    assert denied["generation"] == acquired["generation"]
    assert pl.mark_poll_success(
        token, generation=acquired["generation"])["ok"] is True
    assert pl.assert_poll_lease(token)["ok"] is True


def t_d_n_way_process_race_has_one_winner():
    token = _token("race")
    tc = str(_OPS / "telegram_center")
    code = (
        "import json,sys,time;"
        f"sys.path.insert(0,{tc!r});"
        "import poll_lease;"
        f"r=poll_lease.assert_poll_lease({token!r});"
        "print(json.dumps(r),flush=True);"
        "time.sleep(0.5)"
    )
    children = [subprocess.Popen(
        [sys.executable, "-c", code], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env=dict(os.environ),
    ) for _ in range(8)]
    results = []
    for child in children:
        stdout, stderr = child.communicate(timeout=30)
        assert child.returncode == 0, stderr
        results.append(json.loads(stdout.strip().splitlines()[-1]))
    assert sum(bool(row.get("ok")) for row in results) == 1, results
    assert sum(row.get("reason") == "duplicate-consumer" for row in results) == 7


def t_e_live_foreign_owner_is_denied_before_network():
    token = _token("foreign")
    assert _foreign_acquire(token)["ok"] is True
    denied = pl.assert_poll_lease(token)
    assert denied["ok"] is False and denied["reason"] == "duplicate-consumer"


def t_e_pid_reuse_boot_mismatch_is_denied():
    token = _token("pid-reuse")
    digest = pl._token_digest(token)
    con = pl._conn()
    now = time.time()
    con.execute(
        "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
        "heartbeat_at,lease_until,state,fail_count,cooldown_until,generation,"
        "owner_instance,host_boot_digest,code_head,request_deadline,last_reason) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (digest, os.getpid(), "same-pid:old-boot", now, now, now + 60,
         "ACTIVE", 0, 0, 4, "old", pl._host_boot_digest(), "old-head",
         now + 60, "fixture"),
    )
    con.close()
    denied = pl.assert_poll_lease(token)
    assert denied["ok"] is False and denied["reason"] == "duplicate-consumer"
    assert denied["generation"] == 4


def t_f_expired_takeover_increments_generation():
    token = _token("takeover")
    digest = pl._token_digest(token)
    con = pl._conn()
    now = time.time()
    con.execute(
        "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
        "heartbeat_at,lease_until,state,fail_count,cooldown_until,generation,"
        "owner_instance,host_boot_digest,code_head,request_deadline,last_reason) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (digest, 999999, "999999:old", now - 100, now - 100, now - 10,
         "ACTIVE", 0, 0, 7, "foreign", "foreign-host", "old-head", 0,
         "fixture"),
    )
    con.close()
    result = pl.assert_poll_lease(token)
    assert result["ok"] is True and result["generation"] == 8


def t_g_first_409_opens_circuit_immediately():
    token = _token("409")
    acquired = pl.assert_poll_lease(token)
    opened = pl.mark_duplicate_consumer(token)
    assert opened["ok"] is True and opened["state"] == "OPEN"
    assert opened["fail_count"] == 1
    denied = pl.assert_poll_lease(token)
    assert denied["ok"] is False and denied["reason"] == "circuit-open"
    assert denied["generation"] == acquired["generation"]


def t_h_failed_request_clears_inflight_but_not_failure_history():
    token = _token("failed-finish")
    acquired = pl.assert_poll_lease(
        token, request_deadline=time.time() + 30.0)
    assert acquired["ok"] is True
    finished = pl.finish_poll_request(
        token, generation=acquired["generation"], reason="api:500")
    assert finished["ok"] is True
    snap = pl.lease_snapshot(token)
    assert snap["request_deadline"] == 0
    assert snap["last_reason"] == "api:500"
    assert pl.assert_poll_lease(token)["ok"] is True


def t_i_only_success_resets_conflict_streak():
    token = _token("reset")
    acquired = pl.assert_poll_lease(token)
    pl.mark_duplicate_consumer(token)
    con = pl._conn()
    con.execute(
        "UPDATE lease SET cooldown_until=? WHERE token_digest=?",
        (time.time() - 1, pl._token_digest(token)),
    )
    con.close()
    refreshed = pl.assert_poll_lease(token)
    assert refreshed["ok"] is True
    assert pl.lease_snapshot(token)["fail_count"] == 1
    success = pl.mark_poll_success(token, generation=acquired["generation"])
    assert success["ok"] is True
    assert pl.lease_snapshot(token)["fail_count"] == 0


def t_j_stale_generation_cannot_confirm_or_release():
    token = _token("fence")
    acquired = pl.assert_poll_lease(token)
    stale = acquired["generation"] + 1
    assert pl.mark_poll_success(token, generation=stale)["reason"] == "stale-generation"
    assert pl.release_poll_lease(token, generation=stale)["reason"] == "not-owner"
    assert pl.release_poll_lease(token, generation=acquired["generation"])["ok"] is True


def t_k_storage_error_fails_closed():
    real = pl._conn
    pl._conn = lambda: (_ for _ in ()).throw(sqlite3.OperationalError("locked"))
    try:
        result = pl.assert_poll_lease(_token("db-error"))
    finally:
        pl._conn = real
    assert result["ok"] is False and result["reason"] == "lease-error"
    assert result["error_class"] == "OperationalError"


def t_l_clock_regression_fails_closed():
    token = _token("clock")
    acquired = pl.assert_poll_lease(token)
    con = pl._conn()
    con.execute(
        "UPDATE lease SET heartbeat_at=? WHERE token_digest=?",
        (time.time() + 60, pl._token_digest(token)),
    )
    con.close()
    denied = pl.assert_poll_lease(token)
    assert denied["ok"] is False and denied["reason"] == "clock-regression"
    assert acquired["generation"] == 1


def t_m_raw_token_is_never_persisted():
    token = _token("secret")
    assert pl.assert_poll_lease(token)["ok"] is True
    raw = pl._db().read_bytes()
    assert token.encode("utf-8") not in raw
    assert pl._token_digest(token) != token


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_poll_lease: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
