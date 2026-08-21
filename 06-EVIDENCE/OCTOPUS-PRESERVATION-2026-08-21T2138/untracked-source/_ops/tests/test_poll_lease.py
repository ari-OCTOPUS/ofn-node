#!/usr/bin/env python3
"""Atomic polling lease — single consumer + 409 circuit."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("poll-lease")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import poll_lease as pl  # noqa: E402

TOKEN = "123456789:AA" + "L" * 32


def t_a_first_consumer_acquires():
    out = pl.assert_poll_lease(TOKEN)
    assert out["ok"] and out["owner_pid"] == os.getpid()
    snap = pl.lease_snapshot(TOKEN)
    assert snap and snap["state"] == "ACTIVE" and snap["owner_pid"] == os.getpid()


def t_b_second_pid_consumer_is_denied_before_telegram():
    import types
    pl2 = types.ModuleType("pl2")
    for k, v in vars(pl).items():
        setattr(pl2, k, v)
    import time as _t
    # simulate another process: patch _boot_id and os.getpid at module level
    pl._boot_id = lambda pid: "999999:1"
    try:
        out = pl.assert_poll_lease(TOKEN)
        assert not out["ok"] and out["reason"] == "duplicate-consumer", out
    finally:
        pl._boot_id = pl.__dict__["_boot_id"]


def t_c_409_opens_circuit_and_blocks_until_cooldown():
    for _ in range(3):
        pl.mark_duplicate_consumer(TOKEN)
    snap = pl.lease_snapshot(TOKEN)
    assert snap and snap["state"] == "OPEN" and snap["fail_count"] == 3
    out = pl.assert_poll_lease(TOKEN)
    assert not out["ok"] and out["reason"] == "circuit-open", out


def t_d_token_digest_is_one_way_and_no_raw_token_persisted():
    import sqlite3
    db = Path(ENV["ops"]) / "state" / "telegram" / "poll-lease.sqlite3"
    raw = db.read_bytes()
    assert TOKEN.encode() not in raw, "raw token must never be persisted"
    assert pl._token_digest(TOKEN) != TOKEN


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_poll_lease: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
