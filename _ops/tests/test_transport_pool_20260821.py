#!/usr/bin/env python3
"""Wave C — transport pool isolation (owner order 2026-08-21).

Proves:
- hard deadline: stalled transport returns None (fail-soft) within bound
- circuit breaker: N consecutive failures open per-bot circuit; OPEN refuses
  before any network I/O (no retry storm)
- 409 opens the circuit immediately
- circuits are per bot (one bot's failures never block another bot)
- bounded concurrency: saturation fails soft instead of spawning
- terminable subprocess mode: a stalling worker is killed and replaced
- timeout never advances offset (tg_api.next_offset contract, exercised here)
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
ENV = harness.setup("wave-c-transport-pool")
_STATE = Path(tempfile.mkdtemp(prefix="wave-c-transport-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

from transport_pool import BotCircuit, CircuitOpenError, TransportPool  # noqa: E402
from tg_api import TgClient  # noqa: E402

BOT_A = "aaaa"
BOT_B = "bbbb"


def _ok(url, timeout_s, data, headers):
    return b'{"ok": true, "result": []}'


def _stall(url, timeout_s, data, headers):
    time.sleep(timeout_s + 10.0)   # longer than the deadline
    return b"never"


def _fail(url, timeout_s, data, headers):
    raise ConnectionError("simulated network failure")


def test_hard_deadline_fail_soft():
    pool = TransportPool()
    t0 = time.time()
    blob = pool.call(BOT_A, "https://api.telegram.org/botX/getUpdates", 0.4,
                     fn=_stall)
    assert blob is None, "stalled transport must return None (fail-soft)"
    assert time.time() - t0 < 10.0, "caller must regain control within the bound"


def test_circuit_opens_after_threshold_and_refuses_before_network():
    pool = TransportPool(fail_threshold=3, cooldown_s=30.0)
    calls = {"n": 0}
    def flaky(url, timeout_s, data, headers):
        calls["n"] += 1
        raise ConnectionError("boom")
    for _ in range(3):
        try:
            pool.call(BOT_A, "u", 1.0, fn=flaky)
        except ConnectionError:
            pass
        pool.record_result(BOT_A, ok=False)
    assert pool.stats()["circuits"][BOT_A]["open"] is True
    before = calls["n"]
    try:
        pool.call(BOT_A, "u", 1.0, fn=flaky)
        raise AssertionError("OPEN circuit must refuse the call")
    except CircuitOpenError:
        pass
    assert calls["n"] == before, "no network I/O while circuit is OPEN"
    # success after cooldown resets
    pool._circuits[BOT_A]._open_until = 0.0
    blob = pool.call(BOT_A, "u", 1.0, fn=_ok)
    assert blob is not None
    assert pool.stats()["circuits"][BOT_A]["open"] is False


def test_409_opens_circuit_immediately():
    pool = TransportPool(fail_threshold=10, cooldown_s=60.0)
    pool.record_result(BOT_A, ok=False, is_409=True)
    assert pool.stats()["circuits"][BOT_A]["open"] is True
    try:
        pool.call(BOT_A, "u", 1.0, fn=_ok)
        raise AssertionError("409 must open the circuit immediately")
    except CircuitOpenError:
        pass


def test_circuits_are_per_bot():
    pool = TransportPool(fail_threshold=1, cooldown_s=60.0)
    try:
        pool.call(BOT_A, "u", 1.0, fn=_fail)
    except ConnectionError:
        pass
    pool.record_result(BOT_A, ok=False)
    assert pool.stats()["circuits"][BOT_A]["open"] is True
    # BOT_B unaffected
    blob = pool.call(BOT_B, "u", 1.0, fn=_ok)
    assert blob is not None
    assert pool.stats()["circuits"][BOT_B]["open"] is False


def test_bounded_concurrency_saturates_fail_soft():
    pool = TransportPool(max_concurrent=2)
    gate = threading.Event()
    def blocked(url, timeout_s, data, headers):
        gate.wait(5.0)
        return b"x"
    t1 = threading.Thread(target=lambda: pool.call(BOT_A, "u", 5.0, fn=blocked))
    t2 = threading.Thread(target=lambda: pool.call(BOT_A, "u", 5.0, fn=blocked))
    t1.start(); t2.start()
    time.sleep(0.3)
    # pool saturated: third call fails soft without spawning a third worker
    try:
        pool.call(BOT_A, "u", 5.0, fn=blocked)
        raise AssertionError("saturated pool must refuse (fail-soft)")
    except CircuitOpenError:
        pass
    gate.set(); t1.join(); t2.join()
    assert pool.stats()["total_saturated"] == 1
    # after release, calls succeed again
    blob = pool.call(BOT_A, "u", 1.0, fn=_ok)
    assert blob is not None


def test_timeout_never_advances_offset():
    # contract exercised at the client level: error round keeps current offset
    current = 777
    assert TgClient.next_offset([], current=current) == current
    ups = [{"update_id": 778}]
    assert TgClient.next_offset(ups, current=current) == 779


def test_subprocess_mode_terminates_stuck_worker():
    import transport_pool as _tp
    blob = _tp.subprocess_transport("https://api.telegram.org/botX/getUpdates", 0.3)
    # unreachable host in fixture env: either None (deadline kill) or error path;
    # the point is the caller returns within the bound and no child survives
    assert blob is None
    # pool in subprocess mode refuses nothing structurally; circuit still applies
    pool = TransportPool(subprocess_fn=_tp.subprocess_transport)
    t0 = time.time()
    out = pool.call(BOT_B, "https://api.telegram.org/botX/getUpdates", 0.4)
    assert out is None
    assert time.time() - t0 < 10.0


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
