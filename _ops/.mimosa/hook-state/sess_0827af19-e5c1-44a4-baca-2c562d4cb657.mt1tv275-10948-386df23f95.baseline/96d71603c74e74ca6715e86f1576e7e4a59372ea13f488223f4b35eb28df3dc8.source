# -*- coding: utf-8 -*-
"""T45 (دستور #۷ §۶): تست‌های پیشنهاد memory_read_loop — تصمیم-زمان،
شمارندهٔ reads، read-back چرخه N→N+1، و نفی نشت آینده."""
from datetime import datetime, timedelta, timezone

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))

from memory_read_loop import MemoryReadLoop  # noqa: E402

T0 = datetime(2026, 8, 20, 10, 0, tzinfo=timezone.utc)


def _row(rid, kind, occ_min, rec_min, **extra):
    row = {"id": rid, "kind": kind,
           "occurred_at": (T0 + timedelta(minutes=occ_min)).isoformat(),
           "recorded_at": (T0 + timedelta(minutes=rec_min)).isoformat()}
    row.update(extra)
    return row


class FakeStore:
    def __init__(self, rows):
        self.rows = rows

    def all_records(self):
        return list(self.rows)


def test_reads_respect_decision_time():
    store = FakeStore([
        _row("e1", "experiment", 0, 1, text="alpha"),
        _row("e2", "experiment", 5, 20, text="alpha late"),   # دیررس
        _row("e3", "experiment", 60, 1, text="alpha future"),  # رخداد آینده
    ])
    loop = MemoryReadLoop(store)
    res = loop.query_experiments(T0 + timedelta(minutes=10))
    assert res.ids == ["e1"]                    # e2 هنوز ثبت نشده؛ e3 آینده است
    res_late = loop.query_experiments(T0 + timedelta(minutes=30))
    assert res_late.ids == ["e1", "e2"]


def test_pending_hypotheses_and_search():
    store = FakeStore([
        _row("h1", "hypothesis", 0, 1, text="spine bitemporal", resolved=False),
        _row("h2", "hypothesis", 0, 1, text="other", resolved=True),
        _row("h3", "hypothesis", 0, 2, text="spine shadow", resolved=False),
    ])
    loop = MemoryReadLoop(store)
    assert loop.get_pending_hypotheses(T0 + timedelta(minutes=5)).ids == ["h1", "h3"]
    assert loop.search_vault("SPINE", T0 + timedelta(minutes=5)).ids == ["h1", "h3"]


def test_memory_reads_per_cycle_counter_and_telemetry():
    loop = MemoryReadLoop(FakeStore([_row("e1", "experiment", 0, 1)]))
    loop.query_experiments(T0 + timedelta(minutes=5))
    loop.get_pending_hypotheses(T0 + timedelta(minutes=5))
    tel = loop.telemetry()
    assert tel["memory_reads_per_cycle"] == 2
    assert tel["executable"] is False
    assert "agent_id" in tel and "session_id" in tel   # قرارداد رسید دستور #۶ §۴


def test_readback_write_cycle_n_read_cycle_n1():
    store = FakeStore([])
    loop = MemoryReadLoop(store)
    rid = loop.record_written(_row("w1", "experiment", 0, 1))
    # چرخهٔ N+1: رکورد حالا وارد store شده
    store.rows.append(_row("w1", "experiment", 0, 1))
    assert loop.readback(rid, T0 + timedelta(minutes=5)) is True
    assert loop.telemetry()["readback"]["w1"] == "read_ok"


def test_future_record_never_leaks_any_path():
    store = FakeStore([_row("f1", "experiment", 120, 1, text="future alpha")])
    loop = MemoryReadLoop(store)
    for dt in (T0, T0 + timedelta(minutes=30), T0 + timedelta(minutes=60)):
        assert loop.query_experiments(dt).ids == []
        assert loop.search_vault("future", dt).ids == []
        assert loop.get_pending_hypotheses(dt).ids == []
