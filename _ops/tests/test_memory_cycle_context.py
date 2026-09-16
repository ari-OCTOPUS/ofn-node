#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W8 — MemoryContext cycle-1 write changes cycle-2 decision.

Isolated FakeStore only. Does not open production memory.db, send logs, or Telegram.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "memory"))

from cycle_context import (  # noqa: E402
    build_context, decide_from_context, retrieve_owner_decisions,
    retrieve_similar_failures,
)

T0 = datetime(2026, 8, 21, 8, 0, tzinfo=timezone.utc)


class FakeStore:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def all_records(self):
        return list(self.rows)


def _exp(rid, outcome, minute, text="dns stall poller", goal="g-dns"):
    ts = (T0 + timedelta(minutes=minute)).isoformat()
    return {
        "id": rid, "kind": "experiment", "outcome": outcome, "text": text,
        "goal_id": goal, "occurred_at": ts, "recorded_at": ts,
    }


def test_cycle2_decision_changes_after_cycle1_failure():
    store = FakeStore([])
    t1 = T0 + timedelta(minutes=5)
    ctx1 = build_context(store, goal_id="g-dns", decision_time=t1, needle="dns")
    d1 = decide_from_context(ctx1)
    assert d1["action"] == "explore", d1
    assert d1["context_id"] == ctx1.context_id
    store.rows.append(_exp("exp-1", "failed", 6))
    t2 = T0 + timedelta(minutes=15)
    ctx2 = build_context(store, goal_id="g-dns", decision_time=t2, needle="dns")
    d2 = decide_from_context(ctx2)
    assert d2["action"] == "hold_and_revise", d2
    assert d2["reason"] == "prior_failure"
    assert d2["context_id"] == ctx2.context_id
    assert d2["context_id"] != d1["context_id"]
    assert "exp-1" in d2["used_failure_ids"]
    assert "exp-1" in d2["used_memory_ids"]


def test_retrieve_helpers_are_real_call_sites():
    store = FakeStore([
        _exp("exp-f", "failed", 1),
        {
            "id": "od-1", "kind": "owner_decision", "text": "hold dns work",
            "occurred_at": (T0 + timedelta(minutes=1)).isoformat(),
            "recorded_at": (T0 + timedelta(minutes=1)).isoformat(),
        },
    ])
    dt = T0 + timedelta(minutes=10)
    fails = retrieve_similar_failures(store, "dns", dt)
    decs = retrieve_owner_decisions(store, dt)
    assert [r["id"] for r in fails] == ["exp-f"]
    assert [r["id"] for r in decs] == ["od-1"]


def test_future_failure_does_not_leak_into_decision():
    store = FakeStore([_exp("exp-future", "failed", 90)])
    ctx = build_context(store, goal_id="g-dns",
                        decision_time=T0 + timedelta(minutes=5), needle="dns")
    d = decide_from_context(ctx)
    assert d["action"] == "explore", d
    assert d["used_failure_ids"] == []
