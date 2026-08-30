#!/usr/bin/env python3
"""self_improve_gauges — پنج vital ماشینِ خودبهبودی (فقط gauge، نه رفتار).

خودیادگیریِ بدون متریک = ادعا. این ماژول عدد می‌خواند، چیزی را عوض نمی‌کند.
منبع‌ها همه روی دیسک‌اند؛ خواننده تا 2026-08-16 پراکنده بود.

vitals:
  1. goal_loop_close_7d  — چند حکم PASS در ۷ روز / کل احکام همان پنجره
  2. memory_in_decision  — اگر M1 windowed روی دیسک باشد همان؛ وگرنه None صادق
  3. internal_goals_moved_7d — چند goal_key متمایز این هفته PASS گرفت
  4. consolidation_24h   — چند سیکل consolidation.json در ۲۴ساعت
  5. pending_queue       — شمار pending فرضیه اگر sqlite در دسترس باشد، وگرنه None
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_STATE = Path(os.environ.get("OCTOPUS_STATE_DIR") or os.environ.get("OPS_DIR") or _OPS) 
if _STATE.name != "state":
    _STATE = Path(os.environ.get("OCTOPUS_STATE_DIR") or (_OPS / "state"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts) -> datetime | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    s = str(ts).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _verdicts() -> list:
    p = _STATE / "test_cycle" / "verdicts.jsonl"
    out = []
    try:
        if not p.exists():
            return out
        for line in p.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict) and d.get("schema") == "cycle_verdict.v1":
                out.append(d)
    except OSError:
        return []
    return out


def goal_loop_close_7d(now: datetime | None = None) -> dict:
    now = now or _now()
    cut = now - timedelta(days=7)
    rows = []
    for d in _verdicts():
        ts = _parse_ts(d.get("ts"))
        if ts is None or ts < cut:
            continue
        rows.append(d)
    n = len(rows)
    n_pass = sum(1 for d in rows if str(d.get("verdict") or "") == "PASS")
    return {
        "n": n, "n_pass": n_pass,
        "rate_pct": round(100.0 * n_pass / n, 1) if n else None,
    }


def internal_goals_moved_7d(now: datetime | None = None) -> dict:
    now = now or _now()
    cut = now - timedelta(days=7)
    keys = set()
    for d in _verdicts():
        ts = _parse_ts(d.get("ts"))
        if ts is None or ts < cut:
            continue
        if str(d.get("verdict") or "") == "PASS" and d.get("goal_key"):
            keys.add(str(d["goal_key"]))
    return {"n_keys_passed": len(keys), "keys": sorted(keys)[:8]}


def consolidation_24h(now: datetime | None = None) -> dict:
    now = now or _now()
    cut = now.timestamp() - 86400
    p = _OPS / "neural" / "consolidation.json"
    n = 0
    last_cycle = None
    try:
        raw = json.loads(p.read_text("utf-8"))
        rows = raw if isinstance(raw, list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            ts = row.get("timestamp")
            try:
                tsf = float(ts)
            except (TypeError, ValueError):
                continue
            if tsf >= cut:
                n += 1
                last_cycle = row.get("cycle")
    except (OSError, ValueError):
        return {"n": None, "last_cycle": None, "reason": "unreadable"}
    return {"n": n, "last_cycle": last_cycle}


def memory_in_decision() -> dict:
    """M1 اگر روی دیسک باشد؛ اختراع نمی‌کنیم."""
    p = _STATE / "thesis" / "measurements.jsonl"
    last = None
    try:
        if p.exists():
            for line in p.read_text("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if isinstance(d, dict) and (
                        d.get("metric") == "M1" or d.get("id") == "M1"
                        or "windowed" in str(d.get("name") or "").lower()):
                    last = d
    except OSError:
        last = None
    if not last:
        return {"value": None, "source": None}
    val = last.get("value")
    if val is None:
        val = last.get("windowed") or last.get("rate")
    return {"value": val, "source": "thesis/measurements.jsonl"}


def pending_queue() -> dict:
    """صف فرضیه — sqlite mode=ro. TCB را لمس نمی‌کنیم؛ فقط SELECT شمار."""
    db = Path(os.environ.get("FOURD_DB") or "")
    if not db:
        root = Path(os.environ.get("ORG_ROOT") or _OPS.parent)
        cand = root / "4d_system" / "state" / "memory.db"
        if not cand.exists():
            cand = root / "4d_system" / "memory" / "memory.db"
        db = cand
    if not db.exists():
        return {"n_pending": None, "median_age_h": None, "reason": "db-absent"}
    try:
        uri = db.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=2)
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM hypotheses WHERE status = 'pending'"
            ).fetchone()[0]
            ages = conn.execute(
                "SELECT created_at FROM hypotheses WHERE status = 'pending'"
            ).fetchall()
        finally:
            conn.close()
    except sqlite3.Error as e:
        return {"n_pending": None, "median_age_h": None,
                "reason": type(e).__name__}
    median = None
    now = time.time()
    vals = []
    for (c,) in ages or []:
        try:
            vals.append(now - float(c))
        except (TypeError, ValueError):
            continue
    if vals:
        vals.sort()
        median = round(vals[len(vals) // 2] / 3600.0, 2)
    return {"n_pending": int(n), "median_age_h": median}


def snapshot(*, now: datetime | None = None) -> dict:
    now = now or _now()
    g1 = goal_loop_close_7d(now)
    g3 = internal_goals_moved_7d(now)
    return {
        "schema": "self-improve-gauges.v1",
        "ts": now.isoformat(),
        "goal_loop_close_7d": g1,
        "memory_in_decision": memory_in_decision(),
        "internal_goals_moved_7d": g3,
        "consolidation_24h": consolidation_24h(now),
        "pending_queue": pending_queue(),
        "honest": {
            "goal_loop_closed": bool(g1.get("n_pass")),
            "any_internal_goal_moved": bool(g3.get("n_keys_passed")),
        },
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
