#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_read_loop.py — PROPOSAL (T45، دستور مالک #۷ §۶).

حکم تاریخ گیت: نسخهٔ حلقهٔ زنده (_ops/) هرگز وجود نداشته — UNLOCATED؛
این ماژول بازنویسی از صفر است و تا دستور جداگانهٔ مالک به organism.py
سیم نمی‌شود (executable=false، فقط-خواندنی).

قرارداد:
  - سه نقطهٔ خواندن: query_experiments · get_pending_hypotheses · search_vault
  - هر خواندن از query با decision_time می‌گذرد: occurred_at <= dt و
    recorded_at <= dt وگرنه رکورد در نمی‌آید (FUTURE_DATA حذف، نه اصلاح).
  - شمارندهٔ memory_reads_per_cycle در تلمتری منتشر می‌شود؛ صفر ماندن =
    MEMORY_STILL_WRITE_ONLY.
  - read-back: نوشتن در چرخهٔ N باید در چرخهٔ N+1 قابل بازیابی باشد.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol


def _parse(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class ReadStore(Protocol):
    """آداپتور فقط-خواندنی. پیاده‌سازی زنده به vault_bridge/retrieval_router
    وصل می‌شود (در زمان فعال‌سازی، با تصمیم مالک)."""

    def all_records(self) -> list[dict]: ...


@dataclass
class ReadResult:
    kind: str
    decision_time: datetime
    ids: list[str]
    rows: list[dict] = field(default_factory=list)


@dataclass
class MemoryReadLoop:
    store: ReadStore
    agent_id: str = "unknown"
    session_id: str = "unknown"

    def __post_init__(self) -> None:
        self.reads_this_cycle = 0
        self.readback_log: dict[str, str] = {}

    # ── فیلتر تصمیم-زمان (قانون WAVE0) ─────────────────────────────
    @staticmethod
    def _eligible(row: dict, decision_time: datetime) -> bool:
        occ = row.get("occurred_at")
        rec = row.get("recorded_at")
        if not occ or not rec:
            return False  # INELIGIBLE_TEMPORAL_METADATA — هرگز تزریق ساعت
        try:
            return _parse(occ) <= decision_time and _parse(rec) <= decision_time
        except ValueError:
            return False

    def _query(self, kind: str, decision_time: datetime,
               predicate: Callable[[dict], bool]) -> ReadResult:
        rows = [r for r in self.store.all_records()
                if predicate(r) and self._eligible(r, decision_time)]
        self.reads_this_cycle += 1
        return ReadResult(kind=kind, decision_time=decision_time,
                          ids=sorted(str(r.get("id") or r.get("memory_id") or "")
                                     for r in rows), rows=rows)

    # ── سه نقطهٔ خواندن مصوب ───────────────────────────────────────
    def query_experiments(self, decision_time: datetime | str) -> ReadResult:
        return self._query("query_experiments", _parse(decision_time),
                           lambda r: r.get("kind") == "experiment")

    def get_pending_hypotheses(self, decision_time: datetime | str) -> ReadResult:
        return self._query("get_pending_hypotheses", _parse(decision_time),
                           lambda r: r.get("kind") == "hypothesis"
                           and not r.get("resolved"))

    def search_vault(self, needle: str, decision_time: datetime | str) -> ReadResult:
        n = needle.lower()

        def _match(r: dict) -> bool:
            text = str(r.get("text") or r.get("payload") or "")
            return n in text.lower()
        return self._query("search_vault", _parse(decision_time), _match)

    # ── read-back چرخه N → N+1 ─────────────────────────────────────
    def record_written(self, row: dict) -> str:
        rid = str(row.get("id") or row.get("memory_id"))
        self.readback_log[rid] = "written"
        return rid

    def readback(self, rid: str, decision_time: datetime | str) -> bool:
        self.reads_this_cycle += 1
        found = any(str(r.get("id") or r.get("memory_id")) == rid
                    and self._eligible(r, _parse(decision_time))
                    for r in self.store.all_records())
        self.readback_log[rid] = "read_ok" if found else "read_miss"
        return found

    # ── تلمتری ─────────────────────────────────────────────────────
    def telemetry(self) -> dict:
        return {"agent_id": self.agent_id, "session_id": self.session_id,
                "memory_reads_per_cycle": self.reads_this_cycle,
                "readback": dict(self.readback_log),
                "executable": False}
