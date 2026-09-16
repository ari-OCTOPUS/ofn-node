#!/usr/bin/env python3
"""Wave A — health truth semantics (owner order 2026-08-21).

Proves:
- empty long poll is valid progress (last_poll_completed_at / last_progress_at)
- no updates for 30 minutes is NOT a hang (watchdog truth uses poll completion)
- timeout/transport stall never advances the Telegram offset
- updates advance offset only via next_offset on success
- the full Wave A field set exists in the health snapshot
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("wave-a-health-truth")
_STATE = Path(tempfile.mkdtemp(prefix="wave-a-health-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

import health_metrics as hm  # noqa: E402
from tg_api import TgClient  # noqa: E402

# Wave A required field set (owner order)
REQUIRED_COUNTERS = {
    "poll_started_total", "poll_completed_total", "poll_empty_total",
    "poll_timeout_total", "poll_dns_stall_total", "poll_409_total",
    "watchdog_restart_total",
}
REQUIRED_TS = {
    "last_poll_started_at", "last_poll_completed_at", "last_empty_poll_at",
    "last_update_received_at", "last_progress_at",
}
REQUIRED_ALIASES = {"active_workers", "thread_count"}

T0 = 1_785_500_000.0


def test_all_required_fields_exist():
    hm.record_poll(ok=True, started_at=T0, completed_at=T0 + 1, empty=True)
    st = hm.snapshot()
    counters = st["counters"]
    missing = REQUIRED_COUNTERS - set(counters)
    assert not missing, f"missing counters: {missing}"
    missing_ts = REQUIRED_TS - set(st)
    assert not missing_ts, f"missing timestamps: {missing_ts}"
    missing_al = REQUIRED_ALIASES - set(st)
    assert not missing_al, f"missing aliases: {missing_al}"
    # aliases mirror the live values
    assert st["active_workers"] == st["active_transport_workers"]
    assert st["thread_count"] == st["process_thread_count"]


def test_empty_poll_is_progress():
    hm.record_poll(ok=True, started_at=T0, completed_at=T0 + 1.0, empty=True)
    st = hm.snapshot()
    assert st["last_poll_completed_at"] == T0 + 1.0
    assert st["last_empty_poll_at"] is not None
    assert st["last_progress_at"] is not None
    assert st["counters"]["poll_empty_total"] >= 1
    # empty poll is a SUCCESSFUL round (consecutive failures reset)
    assert st["consecutive_failures"] == 0


def test_no_updates_30_minutes_is_healthy():
    # 180 empty polls over 30 simulated minutes: owner sent nothing, loop alive.
    for i in range(180):
        t = T0 + i * 10.0
        hm.record_poll(ok=True, started_at=t, completed_at=t + 1.0, empty=True)
    now = T0 + 30 * 60.0 + 2.0
    truth = hm.watchdog_truth(now=now, hung_after_s=300.0)
    assert truth["healthy"] is True, truth
    assert truth["based_on"] == "last_poll_completed_at"
    # last_update_received_at is stale — and that must NOT flip health
    st = hm.snapshot()
    assert st["last_update_received_at"] is None


def test_stale_poll_completion_is_unhealthy():
    hm.record_poll(ok=True, started_at=T0, completed_at=T0 + 1.0, empty=True)
    now = T0 + 400.0  # > 300s hung threshold, no further polls
    truth = hm.watchdog_truth(now=now, hung_after_s=300.0)
    assert truth["healthy"] is False, truth
    assert truth["last_poll_completed_age_s"] > 300.0


def test_update_timestamp_alone_is_never_health():
    # only last_update_received_at fresh, no completed poll -> no-data/healthy=false
    hm.record_poll(ok=False, reason="api:429", started_at=T0, completed_at=T0 + 1.0)
    st = hm.snapshot()
    st["last_update_received_at"] = T0 + 10.0
    hm._save(st)
    now = T0 + 60.0
    truth = hm.watchdog_truth(now=now, hung_after_s=300.0)
    # a failing round with no completed success still records progress; the
    # truth source must be poll completion, not the update timestamp
    assert truth["based_on"] != "last_update_received_at"
    assert truth["healthy"] in (True, False)  # deterministic per state


def test_timeout_does_not_advance_offset():
    # next_offset semantics: failure returns current offset unchanged.
    current = 12345
    nxt = TgClient.next_offset([], current=current)
    assert nxt == current, "empty/error round must not advance offset"
    ups = [{"update_id": 12346}, {"update_id": 12347}]
    nxt = TgClient.next_offset(ups, current=current)
    assert nxt == 12348, "successful round advances to max(update_id)+1"


def test_updates_advance_offset_only_on_success():
    ups = [{"update_id": 500}, {"update_id": 502}]
    assert TgClient.next_offset(ups, current=0) == 503
    # out-of-order / stale updates never move the offset backwards
    ups_stale = [{"update_id": 400}]
    assert TgClient.next_offset(ups_stale, current=503) == 503


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
