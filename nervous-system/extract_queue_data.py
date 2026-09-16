#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_queue_data.py — enriched unified approval queue → queue-data.js

Wave 6 enrichments (B + D overlap):
  • Canonical status labels per item (mapped from legacy status strings)
  • Time-in-queue (human-readable)
  • Required owner action per item
  • Dry-run vs live flag
  • Denial reasons from approval-log.jsonl
  • Status flow diagram data
  • Log stats (transition counts, dry-run vs live ratio)

Sink: nervous-system/queue-data.js → window.QUEUE_DATA
"""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OPS_DIR = Path("F:/backup/_ops/state")
NS_DIR = Path("F:/backup/nervous-system")
APPROVAL_LOG = OPS_DIR / "approval-log.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        print(f"[extract_queue_data] read failed for {path}: {exc}")
        return {}


def _read_jsonl(path: Path, limit: int = 500) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return rows
    for ln in lines[-limit:]:
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except ValueError:
            continue
    return rows


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _time_in_queue_minutes(created_at: str) -> int | None:
    dt = _parse_iso(created_at)
    if dt is None:
        return None
    return max(0, int((datetime.now(timezone.utc) - dt).total_seconds() / 60))


def _format_duration(minutes: int | None) -> str:
    if minutes is None:
        return "—"
    if minutes < 1:
        return "تازه"
    if minutes < 60:
        return f"{minutes} دقیقه"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ساعت"
    days = hours // 24
    return f"{days} روز"


# ─── Status mapping ──────────────────────────────────────────────────────────
_CANONICAL_MAP = {
    "pending": "queued",
    "required": "queued",
    "approved": "owner_approved",
    "settled": "executed",
    "denied": "rejected",
}


def _canonical_status(old: str) -> str:
    return _CANONICAL_MAP.get(old, old) if old else "suggested"


def _required_action_label(status: str) -> str:
    labels = {
        "suggested": "بررسی و قرار دادن در صف",
        "queued": "تأیید / رد / انقضا توسط مالک",
        "owner_approved": "اجرا (تأیید شده)",
        "executed": "تکمیل‌شده — نیاز به اقدام ندارد",
        "rejected": "رد شده — نیاز به اقدام ندارد",
        "expired": "منقضی شده — نیاز به اقدام ندارد",
        "superseded": "جایگزین شده — نیاز به اقدام ندارد",
        "dry_run": "ارزیابی dry-run — نیاز به تأیید برای live",
    }
    return labels.get(status, "نامشخص")


# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> dict:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = _now_iso()

    queue_path = OPS_DIR / "unified-approval-queue.json"
    raw = _safe_read_json(queue_path)
    items = raw.get("items", [])
    counts = raw.get("counts", {})

    # Read approval log for denial reasons and stats
    log_rows = _read_jsonl(APPROVAL_LOG)
    denial_map: dict[str, list[str]] = {}
    by_new_status = Counter()
    by_verdict = Counter()
    dry_run_count = 0
    live_count = 0

    for row in log_rows:
        to_status = row.get("to_status", "")
        by_new_status[to_status] += 1
        aid = row.get("action_id", "")
        action_type = row.get("action_type", "")
        rationale = row.get("rationale", "")
        if to_status in ("rejected", "denied"):
            if aid:
                denial_map.setdefault(aid, []).append(rationale or "رد بدونِ توضیح")
        if to_status == "dry_run":
            dry_run_count += 1
        if to_status == "executed":
            live_count += 1
        if action_type == "verdict":
            verdict_val = rationale.split(":")[0] if rationale else "unknown"
            by_verdict[verdict_val] += 1

    log_stats = {
        "total_transitions": len(log_rows),
        "by_new_status": dict(by_new_status),
        "by_verdict": dict(by_verdict),
        "dry_run_count": dry_run_count,
        "live_count": live_count,
        "dry_run_ratio": round(dry_run_count / max(1, dry_run_count + live_count), 4),
    }

    # Enrich items
    pending_items = [i for i in items if i.get("status") == "pending"]
    badge_count = len(pending_items)

    first_action = None
    if pending_items:
        first = pending_items[0]
        first_action = {
            "id": first.get("id"),
            "source": first.get("source"),
            "type": first.get("type"),
            "summary": first.get("summary", "")[:80],
            "priority": first.get("priority", "medium"),
            "amount_aud": first.get("amount_aud", 0),
        }

    enriched_items: list[dict] = []
    for i in items:
        old_status = i.get("status", "pending")
        canonical = _canonical_status(old_status)
        created_at = i.get("created_at", "") or i.get("requested_at", "")
        time_minutes = _time_in_queue_minutes(created_at)
        aid = i.get("id", "")

        enriched = dict(i)
        enriched["_canonical_status"] = canonical
        enriched["_required_action"] = _required_action_label(canonical)
        enriched["_time_in_queue_minutes"] = time_minutes
        enriched["_time_in_queue_human"] = _format_duration(time_minutes)
        enriched["_dry_run"] = canonical == "dry_run"
        enriched["_deny_reasons"] = denial_map.get(aid, [])
        # HTML-facing aliases (Wave 6 UI contract)
        enriched["explicit_status_label"] = canonical
        enriched["required_action"] = enriched["_required_action"]
        enriched["time_in_queue"] = enriched["_time_in_queue_human"]
        enriched["dry_run"] = enriched["_dry_run"]
        enriched_items.append(enriched)

    by_source: dict[str, list[dict]] = {}
    for i in enriched_items:
        src = i.get("source", "unknown")
        by_source.setdefault(src, []).append({
            "id": i.get("id"),
            "type": i.get("type"),
            "status": i.get("status"),
            "summary": i.get("summary", "")[:100],
            "priority": i.get("priority", "medium"),
            "amount_aud": i.get("amount_aud", 0),
            "effect_id": i.get("effect_id"),
        })

    status_flow = [
        {"status": "suggested", "label": "پیشنهاد", "active": False},
        {"status": "queued", "label": "در صف", "active": False},
        {"status": "owner_approved", "label": "تأیید مالک", "active": False},
        {"status": "executed", "label": "اجرا", "active": False},
    ]

    queue_data = {
        "generated": generated,
        "queue": {
            "items": enriched_items,
            "counts": counts,
            "badge": badge_count,
            "first_action": first_action,
            "by_source": by_source,
            "stale": False,
            "status_flow": status_flow,
            "state_flow": {
                "states": ["suggested", "queued", "owner_approved", "executed", "rejected", "expired", "superseded", "dry_run"]
            },
            "log_stats": log_stats,
        },
        "badge": badge_count,
        "pending_count": counts.get("pending", 0),
        "high_priority": counts.get("high_priority", 0),
        "money_at_risk": counts.get("money_at_risk", 0.0),
    }

    js = "window.QUEUE_DATA = " + json.dumps(queue_data, ensure_ascii=False, default=str) + ";\n"
    out_path = NS_DIR / "queue-data.js"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(js)

    print(
        f"[extract_queue_data] refreshed: {len(js)} chars, "
        f"{badge_count} pending, {len(items)} total, {len(enriched_items)} enriched"
    )
    return queue_data


if __name__ == "__main__":
    main()
