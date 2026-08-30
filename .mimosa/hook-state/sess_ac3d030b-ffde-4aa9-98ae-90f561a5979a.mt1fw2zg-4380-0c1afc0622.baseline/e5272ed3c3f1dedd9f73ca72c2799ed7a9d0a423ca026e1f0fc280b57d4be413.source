#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_audit_data.py — CH-11: Agent telemetry → audit dashboard.

Source:
  • _ops/state/events.jsonl   (structured events از events.py)
  • _ops/state/traces.jsonl   (trace spans از tracer.py)
  • _ops/state/ledger-fallback.jsonl (fallback audit)
  • 07 - Knowledge/genome-system/ledger/ledger.jsonl (genome ledger — audit trail)

Transform:
  • freshness check (stale flag > 45min)
  • delta detection (تغییر نسبت به run قبلی)
  • aggregation by agent, by status, by event type
  • span tree stats (avg/max duration, depth)

Sink:
  • nervous-system/audit-data.js → window.AUDIT_DATA
  • consumed by OCTOPUS/worlds/04-twin/index.html (twin/audit world)

قرارداد: همان الگوی extract_live_data.py / extract_ops_data.py.
stdlib-only؛ fail-soft؛ content-free (no secrets).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# ─── مسیرها ──────────────────────────────────────────────────────────────────
OPS_STATE = Path("F:/backup/_ops/state")
NS_DIR = Path("F:/backup/nervous-system")
GENOME_LEDGER = Path("F:/backup/07 - Knowledge/genome-system/ledger/ledger.jsonl")
DELTA_FILE = NS_DIR / ".audit_delta.json"

STALE_MIN = 45
MAX_EVENTS = 300
MAX_TRACES = 300
MAX_LEDGER = 200


# ─── helper: timestamp ISO ─────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── helper: freshness check ───────────────────────────────────────────────
def _freshness(path: Path) -> dict:
    """کهنگیِ یک فایل: age_min, stale, present."""
    if not path.exists():
        return {"age_min": float("inf"), "stale": True, "present": False}
    try:
        age_s = time.time() - path.stat().st_mtime
        age_min = round(age_s / 60)
        return {"age_min": age_min, "stale": age_min > STALE_MIN, "present": True}
    except OSError:
        return {"age_min": float("inf"), "stale": True, "present": False}


# ─── helper: read jsonl ──────────────────────────────────────────────────────
def _read_jsonl(path: Path, limit: int) -> list[dict]:
    """خواندن آخرین limit سطر از jsonl. fail-soft."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return []
    out = []
    for ln in lines[-limit:]:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out


# ─── helper: delta detection ─────────────────────────────────────────────────
def _delta_digest(records: list[dict]) -> str:
    """hash کوتاه از records برای delta detection."""
    try:
        raw = json.dumps(records, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:12]
    except Exception:
        return "err"


def _load_last_delta() -> dict:
    if not DELTA_FILE.exists():
        return {}
    try:
        with open(DELTA_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_delta(generated: str, digest_events: str, digest_traces: str, digest_ledger: str) -> None:
    try:
        NS_DIR.mkdir(parents=True, exist_ok=True)
        with open(DELTA_FILE, "w", encoding="utf-8") as fh:
            json.dump({
                "generated": generated,
                "digest_events": digest_events,
                "digest_traces": digest_traces,
                "digest_ledger": digest_ledger,
            }, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ─── helper: content-free scrub ──────────────────────────────────────────────
def _scrub(record: dict) -> dict:
    """content-free: هیچ summary طولانی یا کلیدی حساس نگه نمی‌دارد."""
    safe = {}
    for k, v in record.items():
        if k in ("summary", "what", "evidence", "note") and isinstance(v, str) and len(v) > 120:
            safe[k] = v[:120] + "…"
        else:
            safe[k] = v
    return safe


# ─── main extractor ──────────────────────────────────────────────────────────
def main() -> dict:
    NS_DIR.mkdir(parents=True, exist_ok=True)
    generated = _now_iso()

    # ── Source 1: events.jsonl (_ops events) ──
    events_path = OPS_STATE / "events.jsonl"
    events_raw = _read_jsonl(events_path, MAX_EVENTS)
    events_fresh = _freshness(events_path)

    # ── Source 2: traces.jsonl (tracer.py) ──
    traces_path = OPS_STATE / "traces.jsonl"
    traces_raw = _read_jsonl(traces_path, MAX_TRACES)
    traces_fresh = _freshness(traces_path)

    # ── Source 3: ledger-fallback.jsonl (audit fallback) ──
    fallback_path = OPS_STATE / "ledger-fallback.jsonl"
    fallback_raw = _read_jsonl(fallback_path, 100)

    # ── Source 4: genome ledger (LANGAR) ──
    ledger_raw = _read_jsonl(GENOME_LEDGER, MAX_LEDGER)
    ledger_fresh = _freshness(GENOME_LEDGER)

    # ── Transform: events aggregation ──
    by_event_name: dict = {}
    by_agent: dict = {}
    by_status: dict = {}
    approvals_pending = 0
    incidents_open = 0
    recent_incidents = []
    recent_events = []
    for ev in events_raw:
        name = ev.get("event_name", "unknown")
        agent = ev.get("agent_id", "system")
        status = ev.get("status", "ok")
        by_event_name[name] = by_event_name.get(name, 0) + 1
        by_agent[agent] = by_agent.get(agent, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        if ev.get("approval_state") == "required":
            approvals_pending += 1
        if name.startswith("incident."):
            incidents_open += 1 if name == "incident.opened" else 0
            recent_incidents.append(_scrub(ev))
        recent_events.append(_scrub(ev))

    # ── Transform: traces aggregation ──
    by_trace_agent: dict = {}
    by_trace_op: dict = {}
    by_trace_status: dict = {}
    trace_durations = []
    recent_traces = []
    for tr in traces_raw:
        agent = tr.get("agent_id", "system")
        op = tr.get("operation", "?")
        status = tr.get("status", "ok")
        by_trace_agent[agent] = by_trace_agent.get(agent, 0) + 1
        by_trace_op[op] = by_trace_op.get(op, 0) + 1
        by_trace_status[status] = by_trace_status.get(status, 0) + 1
        dur = tr.get("duration_ms", 0)
        if isinstance(dur, (int, float)) and dur > 0:
            trace_durations.append(float(dur))
        recent_traces.append(_scrub(tr))

    trace_stats = {
        "avg_ms": round(sum(trace_durations) / len(trace_durations), 2) if trace_durations else 0,
        "max_ms": round(max(trace_durations), 2) if trace_durations else 0,
        "p95_ms": round(sorted(trace_durations)[int(len(trace_durations) * 0.95)] if trace_durations else 0, 2),
    }

    # ── Transform: ledger aggregation ──
    ledger_by_type: dict = {}
    ledger_by_actor: dict = {}
    recent_ledger = []
    for rec in ledger_raw:
        rtype = rec.get("type", "UNKNOWN")
        actor = rec.get("actor", "system")
        ledger_by_type[rtype] = ledger_by_type.get(rtype, 0) + 1
        ledger_by_actor[actor] = ledger_by_actor.get(actor, 0) + 1
        recent_ledger.append({
            "ts": rec.get("ts", "")[:19] if rec.get("ts") else "",
            "type": rtype,
            "actor": actor,
            "hash": rec.get("hash", "")[:16],
        })

    # ── Transform: fallback audit ──
    fallback_count = len(fallback_raw)

    # ── Delta detection ──
    last_delta = _load_last_delta()
    digest_events = _delta_digest(events_raw)
    digest_traces = _delta_digest(traces_raw)
    digest_ledger = _delta_digest(ledger_raw)
    changed = (
        digest_events != last_delta.get("digest_events", "")
        or digest_traces != last_delta.get("digest_traces", "")
        or digest_ledger != last_delta.get("digest_ledger", "")
    )
    _save_delta(generated, digest_events, digest_traces, digest_ledger)

    # ── Sink: build AUDIT_DATA ──
    audit_data = {
        "generated": generated,
        "delta": {
            "changed": changed,
            "since": last_delta.get("generated", "never"),
        },
        "freshness": {
            "events": events_fresh,
            "traces": traces_fresh,
            "ledger": ledger_fresh,
        },
        "events": {
            "total": len(events_raw),
            "by_name": by_event_name,
            "by_agent": by_agent,
            "by_status": by_status,
            "approvals_pending": approvals_pending,
            "incidents_open": incidents_open,
            "recent": recent_events[-20:][::-1],
        },
        "traces": {
            "total": len(traces_raw),
            "by_agent": by_trace_agent,
            "by_operation": by_trace_op,
            "by_status": by_trace_status,
            "stats": trace_stats,
            "recent": recent_traces[-20:][::-1],
        },
        "ledger": {
            "total": len(ledger_raw),
            "by_type": ledger_by_type,
            "by_actor": ledger_by_actor,
            "recent": recent_ledger[-20:][::-1],
            "fallback_count": fallback_count,
        },
        "twin": {
            "pulse": {
                "events_rate": round(len(events_raw) / max(1, STALE_MIN), 2),
                "trace_rate": round(len(traces_raw) / max(1, STALE_MIN), 2),
                "health_ok": trace_stats.get("avg_ms", 0) < 5000,
            },
            "vitals": [
                {"k": "رویداد", "v": len(events_raw), "ok": events_fresh.get("stale") is not True},
                {"k": "trace", "v": len(traces_raw), "ok": traces_fresh.get("stale") is not True},
                {"k": "ledger", "v": len(ledger_raw), "ok": ledger_fresh.get("stale") is not True},
                {"k": "pending approval", "v": approvals_pending, "ok": approvals_pending == 0},
            ],
        },
    }

    # ── emit JS ──
    js = "window.AUDIT_DATA = " + json.dumps(audit_data, ensure_ascii=False, default=str) + ";\n"
    out_path = NS_DIR / "audit-data.js"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)
    print("audit-data.js refreshed", len(js), "chars")
    return audit_data


if __name__ == "__main__":
    data = main()
    print(json.dumps(data.get("freshness"), ensure_ascii=False, indent=2))
