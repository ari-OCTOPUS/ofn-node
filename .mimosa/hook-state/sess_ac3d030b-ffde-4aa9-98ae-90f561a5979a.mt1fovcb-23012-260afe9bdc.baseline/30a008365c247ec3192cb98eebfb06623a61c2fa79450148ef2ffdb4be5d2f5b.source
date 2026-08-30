#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_watchdog_data.py — CH-17: Watchdog alerts extractor → watchdog-data.js

منبع: _ops/state/ORGANISM-STATE.json + _ops/governor/governor-alerts.md + events.jsonl
سینک: nervous-system/watchdog-data.js → window.WATCHDOG_DATA
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPS_DIR = Path("F:/backup/_ops")
NS_DIR = Path("F:/backup/nervous-system")

# آستانه‌ها
STATE_STALE_MIN = 60       # کهنگیِ state به دقیقه
ALERT_CUTOFF_HOURS = 24    # alertهای فعال = ۲۴ ساعت اخیر
MAX_ALERTS = 50


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path, default: Any = None) -> Any:
    """خواندن JSON با fallback."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        return default or {"_error": str(exc)}


def _parse_governor_alerts(path: Path) -> list[dict]:
    """Parse governor-alerts.md → structured alerts."""
    alerts = []
    if not path.exists():
        return alerts
    try:
        text = path.read_text("utf-8", errors="replace")
    except OSError:
        return alerts

    header_pat = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+\(([^)]+)\)")
    current_ts = None
    current_source = None
    cutoff = time.time() - ALERT_CUTOFF_HOURS * 3600

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = header_pat.match(line)
        if m:
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
                current_ts = dt.replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                current_ts = None
            current_source = m.group(2).strip()
            continue
        if line.startswith("- ⚠️") or line.startswith("- ⚠"):
            msg = line.lstrip("- ⚠️").lstrip("- ⚠").strip()
            if msg:
                ts = current_ts or 0
                # فقط ۲۴ ساعت اخیر
                if ts >= cutoff:
                    alerts.append({
                        "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                        "source": current_source or "unknown",
                        "message": msg,
                        "severity": _infer_severity(msg),
                    })
    # مرتب‌سازی نزولی بر اساس زمان
    alerts.sort(key=lambda a: a["timestamp"], reverse=True)
    return alerts[:MAX_ALERTS]


def _infer_severity(msg: str) -> str:
    """تخمین severity از روی متنِ alert."""
    low = msg.lower()
    if any(k in low for k in ["failed", "error", "crash", "critical", "blocked", "throttled"]):
        return "critical"
    if any(k in low for k in ["warn", "downgraded", "missing", "stale"]):
        return "warning"
    return "info"


def _read_events_jsonl(path: Path) -> list[dict]:
    """خواندنِ watchdog-related events از events.jsonl."""
    events = []
    if not path.exists():
        return events
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    ename = ev.get("event_name", "")
                    if ename in ("watchdog.alert", "incident.opened", "system.heartbeat"):
                        events.append({
                            "timestamp": ev.get("timestamp", ""),
                            "name": ename,
                            "agent": ev.get("agent_id", ""),
                            "status": ev.get("status", ""),
                            "summary": ev.get("summary", ""),
                            "approval_state": ev.get("approval_state", "unknown"),
                        })
                except ValueError:
                    continue
    except OSError:
        pass
    # جدیدترین‌ها اول
    events.reverse()
    return events[:MAX_ALERTS]


def _compute_health_score(org_state: dict, alerts: list[dict]) -> tuple[int, str]:
    """محاسبهٔ health score (0-100) و status label."""
    score = 100
    status = "GREEN"

    # کسر برای state کهنه
    chrono = org_state.get("chrono", {})
    last_beat = chrono.get("beat", 0)
    if last_beat:
        age_min = (time.time() - last_beat) / 60
        if age_min > STATE_STALE_MIN:
            score -= 25
            status = "AMBER"

    # کسر برای alertهای critical
    crits = sum(1 for a in alerts if a.get("severity") == "critical")
    if crits > 0:
        score -= min(crits * 15, 40)
        status = "RED" if crits >= 3 else "AMBER"

    # کسر برای STOP flags
    wiring = org_state.get("wiring", {})
    if any(str(v).startswith("STOP") for v in wiring.values() if isinstance(v, str)):
        score -= 30
        status = "RED"

    score = max(0, min(100, score))
    return score, status


def main() -> None:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = _now_iso()

    # ۱) ORGANISM-STATE
    org_state = _read_json(OPS_DIR / "state" / "ORGANISM-STATE.json", {})

    # ۲) governor-alerts.md
    governor_alerts = _parse_governor_alerts(OPS_DIR / "governor" / "governor-alerts.md")

    # ۳) events.jsonl (watchdog-related)
    events = _read_events_jsonl(OPS_DIR / "state" / "events.jsonl")

    # ۴) health score
    health_score, health_status = _compute_health_score(org_state, governor_alerts)

    # ۵) summary
    chrono = org_state.get("chrono", {})
    wiring = org_state.get("wiring", {})
    wires_on = sum(1 for v in wiring.values() if v is True)
    wires_total = len(wiring)

    watchdog_data = {
        "generated": generated,
        "health": {
            "score": health_score,
            "status": health_status,  # GREEN | AMBER | RED
            "label": {
                "GREEN": "🟢 سالم",
                "AMBER": "🟡 مراقب",
                "RED": "🔴 بحرانی"
            }.get(health_status, "unknown"),
        },
        "organism": {
            "last_beat": chrono.get("beat"),
            "metabolic_age": chrono.get("metabolic_age"),
            "age_tick": chrono.get("age_tick"),
            "epoch_mode": org_state.get("epoch_mode", "unknown"),
            "wires_on": wires_on,
            "wires_total": wires_total,
        },
        "alerts": {
            "active": governor_alerts,
            "count": len(governor_alerts),
            "critical": sum(1 for a in governor_alerts if a.get("severity") == "critical"),
            "warning": sum(1 for a in governor_alerts if a.get("severity") == "warning"),
        },
        "events": events,
        "meta": {
            "source": "_ops/state + _ops/governor/governor-alerts.md",
            "schema_version": "watchdog.v1",
            "stale_threshold_min": STATE_STALE_MIN,
        },
    }

    js = "window.WATCHDOG_DATA = " + json.dumps(watchdog_data, ensure_ascii=False, default=str) + ";\n"
    out_path = NS_DIR / "watchdog-data.js"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)
    print("watchdog-data.js refreshed", len(js), "chars", "→", out_path)


if __name__ == "__main__":
    main()
