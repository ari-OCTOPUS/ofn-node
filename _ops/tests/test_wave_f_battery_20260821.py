#!/usr/bin/env python3
"""Wave F — owner-order test battery (2026-08-21).

Runs the NEW scenarios not already covered by waves A-E and reports the full
16-scenario coverage matrix:

 1. 100 DNS stalls            -> NEW here (transport pool, high threshold)
 2. 100 config read stalls    -> NEW here (ConfigManager stalling reader)
 3. 100 config write stalls   -> NEW here (ConfigManager stalling writer)
 4. concurrent poller race    -> Wave D test_poller_lease_20260821
 5. 409 simulation            -> Wave D + Wave C
 6. crash before attempt      -> NEW here (durable queue survives, sends once)
 7. crash after attempt       -> Wave E (UNCERTAIN_SEND_OUTCOME, no resend)
 8. restart at retry_after-1  -> Wave E
 9. restart at retry_after    -> Wave E
10. duplicate message key     -> Wave E
11. malformed config          -> Wave B
12. stale snapshot            -> Wave B
13. empty long poll           -> Wave A
14. no updates 30 minutes     -> Wave A
15. watchdog false-positive   -> Wave A (watchdog_truth)
16. worker/thread leak        -> NEW here (bounded pools return to zero)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("wave-f-battery")
_STATE = Path(tempfile.mkdtemp(prefix="wave-f-battery-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

import bounded_io  # noqa: E402
import config_manager as cm  # noqa: E402
import rate_limit_queue as rlq  # noqa: E402
from sender_bridge import SenderBridge  # noqa: E402
from transport_pool import TransportPool  # noqa: E402

T0 = 1_785_500_000.0
CLOCK = {"now": T0}


def _clock() -> float:
    return CLOCK["now"]


# ── 1. one hundred DNS stalls ───────────────────────────────────────────────
def test_100_dns_stalls_fail_soft_no_leak():
    pool = TransportPool(fail_threshold=10_000, cooldown_s=3600.0,
                         deadline_margin=0.05)  # small margin for the battery
    calls = {"n": 0}

    def stall(url, timeout_s, data, headers):
        calls["n"] += 1
        time.sleep(0.2)               # outlasts the deadline (0.05 + 0.02)
        return b"never"

    t0 = time.time()
    results = [pool.call("bot-dns", "u", 0.02, fn=stall) for _ in range(100)]
    elapsed = time.time() - t0
    assert calls["n"] == 100, "all 100 stalls must actually reach the transport"
    assert all(r is None for r in results), "every stall returns None (fail-soft)"
    assert elapsed < 30.0, f"100 stalls must complete within bounds ({elapsed:.1f}s)"
    assert pool.stats()["active"] == 0, "no worker left behind"
    assert bounded_io.active_worker_count() == 0


# ── 2. one hundred config read stalls ───────────────────────────────────────
def test_100_config_read_stalls_serve_lkg():
    p = _STATE / "telegram" / "stall-read.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"k": "lkg"}), "utf-8")
    mgr = cm.ConfigManager(p)
    mgr.boot()
    # touch the file so the next reload crosses the generation check, then the
    # bounded reader stalls on every changed generation
    p.write_text(json.dumps({"k": "lkg", "v": 2}), "utf-8")
    mgr._reader = lambda path: None   # every read stalls
    t0 = time.time()
    for _ in range(100):
        p.write_text(json.dumps({"k": "lkg", "v": 2, "t": _}), "utf-8")  # new gen each time
        snap = mgr.reload()
        assert snap == {"k": "lkg"}, "stalled reads serve last-known-good"
        assert mgr.stale is True
    assert time.time() - t0 < 30.0, "100 stalled reads must be fast (no block)"


# ── 3. one hundred config write stalls ──────────────────────────────────────
def test_100_config_write_stalls_fail_soft():
    p = _STATE / "telegram" / "stall-write.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"n": 0}), "utf-8")
    mgr = cm.ConfigManager(p, writer=lambda path, text: False)  # always stalls
    mgr.boot()
    t0 = time.time()
    for _ in range(100):
        ok = mgr.commit({"n": 99})
        assert ok is False, "stalled write must fail soft"
        assert mgr.get() == {"n": 0}, "snapshot unchanged on failed write"
    assert time.time() - t0 < 10.0


# ── 4. concurrent poller race (declared: Wave D) ────────────────────────────
def test_concurrent_poller_race_coverage():
    """Coverage marker — real assertions live in test_poller_lease_20260821
    (second consumer in a separate process denied before any getUpdates)."""
    import poll_lease as pl  # noqa: WPS433
    r = pl.assert_poll_lease("wavef-race-token")
    assert r["ok"] is True


# ── 5. 409 simulation (declared: Wave C/D) ──────────────────────────────────
def test_409_simulation_coverage():
    import poll_lease as pl  # noqa: WPS433
    tok = "wavef-409"
    pl.assert_poll_lease(tok)
    for _ in range(3):
        pl.mark_duplicate_consumer(tok)
    snap = pl.lease_snapshot(tok)
    assert snap["state"] == "OPEN"


# ── 6. crash before attempt ─────────────────────────────────────────────────
def test_crash_before_attempt_sends_once_after_restart():
    q1 = rlq.RateLimitQueue(str(_STATE / "crash-before.sqlite3"),
                            clock=_clock, jitter=lambda: 0.0)
    q1.enqueue(message_key="m1", chat_hash="c1", payload_hash="p1")
    # crash: process dies BEFORE mark_delivery_attempt — item stays QUEUED
    q2 = rlq.RateLimitQueue(str(_STATE / "crash-before.sqlite3"),
                            clock=_clock, jitter=lambda: 0.0)   # restart
    sends = []
    out = SenderBridge(q2, lambda it: sends.append(it) or {"ok": True, "message_id": 1}).run_once()
    assert len(sends) == 1, "queued item survives a pre-attempt crash"
    assert out["sent"] == 1
    assert q2.get("m1")["state"] == "CONFIRMED"


# ── 7-10. crash after attempt / restart boundaries / duplicate key ──────────
def test_crash_after_attempt_coverage():
    # declared: Wave E test_wave_e_c3c4_20260821
    pass


def test_restart_boundaries_coverage():
    pass


def test_duplicate_key_coverage():
    pass


# ── 11-12. malformed config / stale snapshot (declared: Wave B) ─────────────
def test_malformed_and_stale_coverage():
    p = _STATE / "telegram" / "malformed.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"good": True}), "utf-8")
    mgr = cm.ConfigManager(p)
    mgr.boot()
    p.write_text("{broken", "utf-8")
    assert mgr.reload().get("good") is True
    assert mgr.stale is True


# ── 13-15. empty long poll / 30-min silence / watchdog truth (Wave A) ───────
def test_health_semantics_coverage():
    import health_metrics as hm  # noqa: WPS433
    for i in range(180):
        t = T0 + i * 10.0
        hm.record_poll(ok=True, started_at=t, completed_at=t + 1.0, empty=True)
    truth = hm.watchdog_truth(now=T0 + 30 * 60.0 + 2.0, hung_after_s=300.0)
    assert truth["healthy"] is True


# ── 16. worker/thread leak detection ────────────────────────────────────────
def test_worker_thread_leak_detection():
    base_threads = threading.active_count()
    pool = TransportPool(fail_threshold=10_000)
    def stall(url, timeout_s, data, headers):
        time.sleep(0.05)
        return b"never"
    for _ in range(30):
        pool.call("bot-leak", "u", 0.02, fn=stall)
    time.sleep(0.2)                       # let workers finish/exit
    assert pool.stats()["active"] == 0
    growth = threading.active_count() - base_threads
    assert growth <= 2, f"thread leak: growth={growth}"
    assert bounded_io.active_worker_count() == 0


COVERAGE_MATRIX = [
    ("100 DNS stalls", "test_100_dns_stalls_fail_soft_no_leak"),
    ("100 config read stalls", "test_100_config_read_stalls_serve_lkg"),
    ("100 config write stalls", "test_100_config_write_stalls_fail_soft"),
    ("concurrent poller race", "test_poller_lease_20260821.py"),
    ("409 simulation", "test_poller_lease_20260821.py + test_transport_pool_20260821.py"),
    ("crash before attempt", "test_crash_before_attempt_sends_once_after_restart"),
    ("crash after attempt", "test_wave_e_c3c4_20260821.py"),
    ("restart at retry_after-1", "test_wave_e_c3c4_20260821.py"),
    ("restart at retry_after", "test_wave_e_c3c4_20260821.py"),
    ("duplicate message key", "test_wave_e_c3c4_20260821.py"),
    ("malformed config", "test_config_manager_20260821.py"),
    ("stale snapshot", "test_config_manager_20260821.py"),
    ("empty long poll", "test_health_truth_20260821.py"),
    ("no updates 30 minutes", "test_health_truth_20260821.py"),
    ("watchdog false-positive prevention", "test_health_truth_20260821.py"),
    ("worker/thread leak detection", "test_worker_thread_leak_detection"),
]


def main() -> int:
    failed = []
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and not k.endswith("_coverage")]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    print(f"coverage matrix: {len(COVERAGE_MATRIX)}/16 scenarios (matrix below)")
    for name, where in COVERAGE_MATRIX:
        print(f"  - {name}: {where}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
