#!/usr/bin/env python3
"""Wave D — single poller lease (owner order 2026-08-21).

Proves:
- second consumer (different pid/boot) is denied BEFORE any getUpdates call
- a 409 opens the lease circuit (no retry storm)
- circuit-open denies until the cooldown passes
- an expired lease is taken over by a new owner
- poll_updates with a foreign active lease returns [] (fail-soft, no network)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("wave-d-poller-lease")
_STATE = Path(tempfile.mkdtemp(prefix="wave-d-lease-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

import poll_lease as pl  # noqa: E402

TOKEN = "123456789:AA" + "s" * 32


def _foreign_acquire(token: str = TOKEN) -> dict:
    """Acquire the lease from a SEPARATE process (different pid -> consumer 2)."""
    tc_dir = repr(str(_OPS / "telegram_center"))
    ops_dir = repr(str(_OPS))
    code = (
        "import sys, os\n"
        f"sys.path.insert(0, {tc_dir})\n"
        f"sys.path.insert(0, {ops_dir})\n"
        "import poll_lease as pl\n"
        "import json\n"
        "r = pl.assert_poll_lease(" + json.dumps(token) + ")\n"
        "print(json.dumps(r))\n"
    )
    env = dict(os.environ)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, timeout=60, env=env)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_first_consumer_acquires():
    r = pl.assert_poll_lease(TOKEN)
    assert r["ok"] is True
    snap = pl.lease_snapshot(TOKEN)
    assert snap is not None
    assert snap["owner_pid"] == os.getpid()
    assert snap["state"] == "ACTIVE"
    assert snap["lease_until"] > time.time()


def test_second_consumer_denied_before_getupdates():
    token = TOKEN + "-race"              # fresh token: parent is NOT the holder
    # consumer 1 = separate process (lease holder)
    r = _foreign_acquire(token)
    assert r["ok"] is True, r
    # parent is the SECOND consumer: denied at the lease gate
    lease = pl.assert_poll_lease(token)
    assert lease["ok"] is False, "second consumer must be denied"
    assert lease["reason"] == "duplicate-consumer"
    # poll_updates returns [] WITHOUT touching the network (get would explode)
    import tg_api  # noqa: WPS433
    def _boom(*_a, **_k):
        raise AssertionError("network must not be called for a denied lease")
    client = tg_api.TgClient(token, owner_chat_id=1, get_fn=_boom)
    ups = client.poll_updates(offset=0, timeout_s=1)
    assert ups == []
    import health_metrics as _hm  # noqa: WPS433
    st = _hm.snapshot()
    assert "lease" in str(st.get("last_reason") or "")


def test_expired_lease_taken_over():
    # force an expired lease owned by a foreign pid
    digest = pl._token_digest(TOKEN + "-expired")
    con = pl._conn()
    con.execute("BEGIN IMMEDIATE")
    con.execute(
        "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,acquired_at,"
        "heartbeat_at,lease_until,state,fail_count,cooldown_until) "
        "VALUES(?,?,?,?,?,?,?,0,0)",
        (digest, 999999, "999999:1", 1.0, 1.0, time.time() - 10.0, "ACTIVE"))
    con.execute("COMMIT")
    con.close()
    r = pl.assert_poll_lease(TOKEN + "-expired")
    assert r["ok"] is True, "expired lease must be taken over"
    snap = pl.lease_snapshot(TOKEN + "-expired")
    assert snap["owner_pid"] == os.getpid()


def test_409_opens_circuit_and_denies_until_cooldown():
    token = TOKEN + "-409"
    pl.assert_poll_lease(token)
    for _ in range(3):
        pl.mark_duplicate_consumer(token)
    snap = pl.lease_snapshot(token)
    assert snap["state"] == "OPEN"
    r = pl.assert_poll_lease(token)
    assert r["ok"] is False and r["reason"] == "circuit-open"
    # after cooldown passes, polling is allowed again
    con = pl._conn()
    con.execute("UPDATE lease SET cooldown_until=? WHERE token_digest=?",
                (time.time() - 1.0, pl._token_digest(token)))
    con.close()
    r = pl.assert_poll_lease(token)
    assert r["ok"] is True


def test_409_fail_count_resets_only_after_successful_poll():
    token = TOKEN + "-count"
    acquired = pl.assert_poll_lease(token)
    pl.mark_duplicate_consumer(token)
    assert pl.lease_snapshot(token)["fail_count"] == 1
    # Cooldown expiry permits another request, but does not erase conflict
    # history. Only a valid completed poll for the same fence resets it.
    con = pl._conn()
    con.execute("UPDATE lease SET cooldown_until=? WHERE token_digest=?",
                (time.time() - 1.0, pl._token_digest(token)))
    con.close()
    refreshed = pl.assert_poll_lease(token)
    assert refreshed["ok"] is True
    assert pl.lease_snapshot(token)["fail_count"] == 1
    assert pl.mark_poll_success(
        token, generation=acquired["generation"])["ok"] is True
    assert pl.lease_snapshot(token)["fail_count"] == 0


def main() -> int:
    failed = []
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
