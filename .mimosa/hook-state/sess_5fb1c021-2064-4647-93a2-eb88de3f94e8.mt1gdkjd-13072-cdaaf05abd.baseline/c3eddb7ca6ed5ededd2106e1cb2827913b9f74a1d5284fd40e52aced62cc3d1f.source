#!/usr/bin/env python3
"""checkpoint.py — Phase 5 · S-4: checkpoint سبکِ per-beat + replay.

checkpoint: snapshot سبکِ هر beat با ledger-hash (برای بازسازیِ سریع).
replay(from, to): بازسازیِ state یک leg در بیتِ دلخواهِ گذشته <۵s (از ledger، نه chrono).

این قراردادِ testable است؛ chrono.py از قبل checkpoint جدول دارد (DDL §checkpoint).
additive؛ stdlib-only. ledger/db قابل‌تزریق (تست).

DoD S-4: «بازسازیِ stateِ یک leg در بیتِ دلخواهِ گذشته <۵s» — این از genome ledger
می‌آید (reconstructable)، نه از chrono (که cache است).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "budget"))
import opslib        # noqa: E402


def checkpoint(beat: int, hlc: tuple[int, int], ledger_hash: str,
               db=None, snapshot: dict | None = None) -> bool:
    """checkpointِ سبک در chrono.db. جدولِ checkpoint موجود (DDL) استفاده می‌شود.
    beat + hlc + ledger_hash + snapshot. خروجی: ok.
    fail-soft: chrono نباشد → False (ولی ledger همچنان source of truth است)."""
    if db is None:
        return False
    try:
        metrics = {"ts": int(time.time() * 1000)}
        db.ex(
            "INSERT OR REPLACE INTO checkpoint(beat_id, logical_clock, ledger_hash, "
            "snapshot_ref, metrics) VALUES (?,?,?,?,?)",
            (int(beat), json.dumps(list(hlc)), str(ledger_hash),
             json.dumps(snapshot or {}, ensure_ascii=False), json.dumps(metrics)))
        return True
    except Exception:  # noqa: BLE001 — checkpoint fail-soft
        return False


def replay(ledger=None, event_type: str | None = None,
           from_ts: str | None = None, to_ts: str | None = None,
           actor: str | None = None) -> list[dict]:
    """بازپخشِ رویدادها از genome ledger. فیلتر بر اساسِ event_type/ts/actor.
    این source of truth است — chrono.db فقط cache. بازسازی <۵s چون ledger append-only است."""
    lg = ledger or opslib.genome_ledger()
    out = []
    for rec in lg.filter(event_type=event_type):
        # فیلترهای اختیاری
        if actor and rec.get("actor") != actor:
            continue
        ts = rec.get("ts", "")
        if from_ts and ts < from_ts:
            continue
        if to_ts and ts > to_ts:
            break
        out.append(rec)
    return out


def replay_state_at(ledger=None, leg_id: str | None = None,
                    at_ts: str | None = None) -> dict:
    """بازسازیِ state یک leg در زمانِ دلخواه. آخرین رویدادِ آن leg تا at_ts.
    خروجی: {leg_id, last_event, last_ts, events_count}. DoD: <۵s."""
    t0 = time.time()
    events = replay(ledger=ledger, to_ts=at_ts)
    if leg_id:
        events = [e for e in events if leg_id in json.dumps(e, ensure_ascii=False)]
    elapsed = time.time() - t0
    last = events[-1] if events else None
    return {"leg_id": leg_id, "last_event_type": (last or {}).get("type"),
            "last_ts": (last or {}).get("ts"), "events_count": len(events),
            "replay_seconds": round(elapsed, 3), "within_5s": elapsed < 5.0}


if __name__ == "__main__":
    # نمایشِ replay (فقط اگر ledger داشته باشیم)
    try:
        evts = replay(event_type="MONEY_ATTRIBUTION")
        print(f"replay: {len(evts)} events")
    except Exception as e:  # noqa: BLE001
        print(f"replay demo skipped: {e}")
