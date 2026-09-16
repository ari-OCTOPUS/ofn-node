#!/usr/bin/env python3
"""W1b — HealthState does not re-read poll-health.json after boot.

Preserves durable write (test_tg_poll_health file-mark). Adds
last_dispatch_completed_at and classify().
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "telegram_center"))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
ENV = harness.setup("wave-w1b-health-state")
_STATE = Path(tempfile.mkdtemp(prefix="w1b-health-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_STATE / "_ops" / "state")

import health_metrics as hm  # noqa: E402

T0 = 1_785_600_000.0


def test_second_record_poll_does_not_disk_read():
    hm.reset_memory()
    reads = {"n": 0}
    real = hm._bounded_read

    def counting_read(path):
        reads["n"] += 1
        return real(path)

    with mock.patch.object(hm, "_bounded_read", counting_read):
        hm.record_poll(ok=True, started_at=T0, completed_at=T0 + 1, empty=True)
        first = reads["n"]
        hm.record_poll(ok=True, started_at=T0 + 10, completed_at=T0 + 11, empty=True)
        second_total = reads["n"]
    assert first >= 1, first
    assert second_total == first, {"first": first, "total": second_total}
    st = hm.snapshot()
    assert st["counters"]["poll_completed_total"] >= 2
    path = hm.poll_health_path()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["counters"]["poll_completed_total"] >= 2


def test_record_dispatch_sets_timestamp():
    hm.reset_memory()
    hm.record_poll(ok=True, started_at=T0, completed_at=T0 + 1, empty=True)
    st = hm.record_dispatch(completed_at=T0 + 2)
    assert st.get("last_dispatch_completed_at") == T0 + 2
    snap = hm.snapshot()
    assert "last_dispatch_completed_at" in snap
    assert snap["last_dispatch_completed_at"] == T0 + 2


def test_classify_healthy_empty_poll():
    hm.reset_memory()
    now = T0 + 40
    hm.record_poll(ok=True, started_at=T0, completed_at=T0 + 26, empty=True)
    c = hm.classify(now=now, hung_after_s=300.0, process_alive=True)
    assert c["state"] == "HEALTHY_EMPTY_POLL", c
