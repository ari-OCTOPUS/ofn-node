#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_audit_trail.py — CH-15-D: Audit Trail Extractor

Reads _ops/state/action-audit.jsonl and emits audit-trail-data.js
for the admin-telegram audit panel.

HTML contract:
  AT.stats.total          → total action count
  AT.stats.success_rate   → float 0..1
  AT.stats.mode_ratio     → {dry_run, live}
  AT.stats.rollback_coverage → {reversible, irreversible, requires_manual, unknown}
  AT.recent               → last 10 actions with ts, actor, action_type, rollback_class, execution_mode, result
  AT.rollback_legend      → human-readable descriptions
  AT.freshness.stale      → bool (>45min old)

Safety: $0 offline, stdlib-only, read-only.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG = Path("F:/backup/_ops/state/action-audit.jsonl")
NS_DIR = Path("F:/backup/nervous-system")

ROLLBACK_LEGEND = {
    "reversible": "قابلِ بازگشت: refresh, toggle, copy",
    "irreversible": "برگشت‌ناپذیر: approve spending, execute, delete",
    "requires_manual": "نیاز به دستی: mining start, wallet transfer",
    "unknown": "ناشناخته: action جدید/تست‌نشده",
}


def _read_audit_log(max_lines: int = 5000) -> list[dict[str, Any]]:
    if not AUDIT_LOG.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with open(AUDIT_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return rows
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
        if len(rows) >= max_lines:
            break
    return list(reversed(rows))


def main() -> int:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows = _read_audit_log()
    total = len(rows)

    # Compute staleness
    stale = True
    if rows:
        try:
            last_ts = rows[-1].get("timestamp", "")
            if last_ts:
                dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                age_min = (datetime.now(timezone.utc) - dt).total_seconds() / 60
                stale = age_min > 45
        except Exception:
            pass

    if total == 0:
        payload = {
            "generated": generated,
            "stats": {
                "total_actions": 0,
                "success_rate": None,
                "dry_run_ratio": 0.0,
                "live_ratio": 0.0,
                "by_rollback": {"reversible": 0, "irreversible": 0, "requires_manual": 0, "unknown": 0},
            },
            "rollback_classification": ROLLBACK_LEGEND,
            "recent_actions": [],
            "freshness": {"stale": stale, "generated": generated},
            "note": "No audit records yet — audit_logger.py is ready",
        }
    else:
        successes = sum(1 for r in rows if r.get("result") == "success")
        success_rate = round(successes / total, 4)

        rollback_counts = {"reversible": 0, "irreversible": 0, "requires_manual": 0, "unknown": 0}
        for r in rows:
            rc = r.get("rollback_class", "unknown")
            rollback_counts[rc] = rollback_counts.get(rc, 0) + 1

        mode_counts = {"dry_run": 0, "shadow": 0, "live": 0}
        for r in rows:
            m = r.get("execution_mode", "unknown")
            mode_counts[m] = mode_counts.get(m, 0) + 1

        dry_run_total = mode_counts.get("dry_run", 0) + mode_counts.get("shadow", 0)
        live_total = mode_counts.get("live", 0)
        total_modes = dry_run_total + live_total
        dry_run_ratio = round(dry_run_total / max(1, total_modes), 4)
        live_ratio = round(live_total / max(1, total_modes), 4)

        # Recent 10 for display
        recent_raw = rows[-10:]
        recent_actions = []
        for r in recent_raw:
            recent_actions.append({
                "timestamp": str(r.get("timestamp", "")[:19]),
                "actor": r.get("actor", "?"),
                "action_type": r.get("action_type", "?"),
                "rollback_class": r.get("rollback_class", "unknown"),
                "execution_mode": r.get("execution_mode", "?"),
                "result": r.get("result", "?"),
            })

        payload = {
            "generated": generated,
            "stats": {
                "total_actions": total,
                "success_rate": success_rate,
                "dry_run_ratio": dry_run_ratio,
                "live_ratio": live_ratio,
                "by_rollback": rollback_counts,
            },
            "rollback_classification": ROLLBACK_LEGEND,
            "recent_actions": recent_actions,
            "freshness": {"stale": stale, "generated": generated},
        }

    out_path = NS_DIR / "audit-trail-data.js"
    js = "window.AUDIT_TRAIL_DATA = " + json.dumps(payload, ensure_ascii=False, default=str) + ";\n"
    out_path.write_text(js, encoding="utf-8")
    print(f"audit-trail-data.js refreshed: {len(js)} chars, {total} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
