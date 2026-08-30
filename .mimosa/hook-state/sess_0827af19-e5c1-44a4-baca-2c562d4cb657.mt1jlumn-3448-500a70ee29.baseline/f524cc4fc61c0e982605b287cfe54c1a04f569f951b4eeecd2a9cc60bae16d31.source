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


# ── T49 (دستور #۸ §۴): اتصال زنده به spine — فقط خواندن ─────────────────────
class SpineReadStore:
    """آداپتور فقط-خواندنی از رویدادهای spine به ReadStore.

    نگاشت اولیه (صادقانه و مستند): proposal-issued→experiment ·
    hebb.observation→hypothesis(pending) · متن جست‌وجو = event_type+subject.
    مسیر ارتقا: آداپتور vault_bridge/retrieval_router در فعال‌سازی بعدی."""

    def __init__(self, rows: list[dict]):
        self.rows = rows

    def all_records(self) -> list[dict]:
        out = []
        for r in self.rows:
            et = str(r.get("event_type") or "")
            kind = ("experiment" if et == "proposal-issued"
                    else "hypothesis" if et == "hebb.observation" else et)
            out.append({"id": r.get("event_id"), "kind": kind,
                        "occurred_at": r.get("occurred_at"),
                        "recorded_at": r.get("recorded_at"),
                        "resolved": False,
                        "text": f"{et} {r.get('subject') or ''}"})
        return out


_PULSE_DIR = None


def tick_from_spine(beat: int | None = None, *, spine_rows=None) -> dict:
    """یک تیکِ خواندنِ حافظهٔ زنده از spine + انتشار تلمتری.

    فقط خواندن؛ خطا ⇒ MEMORY_READ_DEGRADED (هرگز حلقهٔ organism را نمی‌کشد)؛
    read-back: جدیدترین رویدادِ تیک قبل باید این تیک قابل‌خواندن باشد (N→N+1)."""
    global _PULSE_DIR
    from pathlib import Path
    if _PULSE_DIR is None:
        _PULSE_DIR = Path(__file__).resolve().parent / "state" / "pulse"
    out: dict = {"schema": "memory-read-tick/1", "beat": beat, "executable": False}
    try:
        if spine_rows is None:
            import sys as _sys
            _sp = str(Path(__file__).resolve().parent / "spine")
            if _sp not in _sys.path:
                _sys.path.insert(0, _sp)
            import event_spine as _es
            _spine = _es.EventSpine()
            try:
                spine_rows = _spine.events()
            finally:
                _spine.close()   # EventSpine context-manager نیست — close صریح
        now_dt = datetime.now(timezone.utc)
        loop = MemoryReadLoop(SpineReadStore(spine_rows),
                              agent_id="organism", session_id=f"beat-{beat}")
        loop.query_experiments(now_dt)
        loop.get_pending_hypotheses(now_dt)
        loop.search_vault("spine", now_dt)
        state_path = _PULSE_DIR / "memory-read-last.json"
        prev = {}
        try:
            import json as _json
            prev = _json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            prev = {}
        last_id = prev.get("last_id")
        newest = spine_rows[-1].get("event_id") if spine_rows else None
        if not last_id:
            rb = "first_cycle"
        else:
            match = next((r for r in spine_rows if r.get("event_id") == last_id), None)
            rb = "read_ok" if (match and MemoryReadLoop._eligible(match, now_dt)) else "read_miss"
        out.update({"status": "OK", "memory_reads_per_cycle": loop.reads_this_cycle,
                    "readback": rb, "last_id_seen": last_id, "newest_id": newest,
                    "n_rows": len(spine_rows)})
        try:
            import json as _json
            _PULSE_DIR.mkdir(parents=True, exist_ok=True)
            state_path.write_text(_json.dumps({"last_id": newest, "beat": beat,
                                               "ts": now_dt.isoformat(timespec="seconds")},
                                              ensure_ascii=False), encoding="utf-8")
            (_PULSE_DIR / "memory-read-latest.json").write_text(
                _json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:  # noqa: BLE001 — تلمتری هرگز تیک را نمی‌کشد
            pass
    except Exception as e:  # noqa: BLE001 — قرارداد T49: DEGRADED نه crash
        out.update({"status": "MEMORY_READ_DEGRADED", "error": type(e).__name__})
        try:
            import json as _json
            _PULSE_DIR.mkdir(parents=True, exist_ok=True)
            (_PULSE_DIR / "memory-read-latest.json").write_text(
                _json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return out
