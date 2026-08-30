#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_telegram_control.py — CH-15: Telegram Control → Admin Actions

منبع:
  • _ops/state/channel-status.json        → وضعیتِ کانال‌های ارتباطی
  • _ops/state/telegram_offset.json       → آخرین offsetِ poll
  • _ops/state/pulse/telegram-poll.json   → تپشِ poll
  • _ops/state/telegram/approvals/*.json  → فایل‌های تأییدِ پراکنده
  • _ops/state/telegram/approvals/approvals.jsonl → لاگِ verdictها
  • _ops/state/unified-approval-queue.json → صفِ تأییدِ یکپارچه
  • _ops/budget/budget-state.json         → دروازهٔ بودجه (halted)

سینک:
  nervous-system/telegram-data.js → window.TELEGRAM_DATA

الگو: stdlib-only، fail-soft، Persian labels for UI.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPS_DIR = Path("F:/backup/_ops")
NS_DIR = Path("F:/backup/nervous-system")

MAX_RECENT = 20


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default if default is not None else {}


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return rows


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(ts[:26], fmt) if len(ts) > 26 else datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def _ts_age_hours(ts: str | None) -> float | None:
    dt = _parse_ts(ts)
    if not dt:
        return None
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - dt
        return diff.total_seconds() / 3600.0
    except Exception:
        return None


def _health_color(score: int) -> str:
    if score >= 80:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


def main() -> None:
    os.makedirs(NS_DIR, exist_ok=True)
    generated = _now_iso()

    # ── 1) channel-status.json ──────────────────────────────────────────────
    channel_status = _read_json(OPS_DIR / "state" / "channel-status.json", {})
    tg_channel = channel_status.get("channels", {}).get("telegram", {})
    dashboard_channel = channel_status.get("channels", {}).get("dashboard", {})

    tg_live = tg_channel.get("live", False)
    tg_mode = tg_channel.get("mode", "unknown")
    tg_required_env = tg_channel.get("required_env", [])

    # ── 2) offset + poll pulse ──────────────────────────────────────────────
    offset_data = _read_json(OPS_DIR / "state" / "telegram_offset.json", {})
    poll_pulse = _read_json(OPS_DIR / "state" / "pulse" / "telegram-poll.json", {})

    last_offset = offset_data.get("offset")
    offset_saved_at = offset_data.get("saved_at")
    offset_age_h = _ts_age_hours(offset_saved_at)

    poll_ts = poll_pulse.get("ts")
    poll_age_h = _ts_age_hours(poll_ts)
    poll_batch = poll_pulse.get("batch", 0)

    # ── 3) approvals.jsonl (canonical log) ──────────────────────────────────
    approvals_log = _read_jsonl(OPS_DIR / "state" / "telegram" / "approvals" / "approvals.jsonl")

    verdict_counts = Counter(a.get("verdict", "unknown") for a in approvals_log)
    total_approvals = len(approvals_log)

    recent_approvals = []
    for a in reversed(approvals_log[-MAX_RECENT:]):
        recent_approvals.append({
            "id": a.get("id", "?"),
            "verdict": a.get("verdict", "?"),
            "ts": a.get("ts"),
            "source": a.get("source", "?"),
        })

    # distinct action_ids approved
    approved_ids = {a["id"] for a in approvals_log if a.get("verdict") == "ok"}
    denied_ids = {a["id"] for a in approvals_log if a.get("verdict") == "no"}

    # ── 4) unified approval queue ───────────────────────────────────────────
    queue = _read_json(OPS_DIR / "state" / "unified-approval-queue.json", {})
    queue_counts = queue.get("counts", {})
    queue_items = queue.get("items", [])

    pending_items = []
    for item in queue_items:
        if item.get("status") in ("pending", "required"):
            pending_items.append({
                "id": item.get("action_id", item.get("id", "?")),
                "amount": item.get("amount_aud", item.get("amount", 0)),
                "priority": item.get("priority", "normal"),
                "status": item.get("status", "?"),
                "ts": item.get("ts") or item.get("requested_at"),
            })

    # ── 5) budget gate (halted?) ────────────────────────────────────────────
    budget_state = _read_json(OPS_DIR / "budget" / "budget-state.json", {})
    budget_halted = budget_state.get("halted", False)
    spent_today_usd = budget_state.get("spent_today_usd", 0.0)
    spent_month_aud = budget_state.get("spent_month_aud", 0.0)

    # ── 6) compute health score ─────────────────────────────────────────────
    # factors: live (40%), offset fresh (20%), queue drained (20%), budget open (20%)
    score = 0
    score += 40 if tg_live else 10  # partial if stub mode
    score += 20 if (offset_age_h is not None and offset_age_h < 2) else (
        10 if (offset_age_h is not None and offset_age_h < 24) else 0
    )
    score += 20 if queue_counts.get("pending", 0) == 0 else (
        10 if queue_counts.get("pending", 0) < 3 else 0
    )
    score += 20 if not budget_halted else 0

    health_label = "سالم" if score >= 80 else ("هشدار" if score >= 50 else "بحرانی")

    # ── 7) build payload ────────────────────────────────────────────────────
    telegram_data = {
        "generated": generated,
        "channel": {
            "name": "telegram",
            "live": tg_live,
            "mode": tg_mode,
            "required_env": tg_required_env,
            "dashboard_live": dashboard_channel.get("live", False),
        },
        "poll": {
            "last_offset": last_offset,
            "offset_saved_at": offset_saved_at,
            "offset_age_hours": round(offset_age_h, 2) if offset_age_h is not None else None,
            "poll_ts": poll_ts,
            "poll_age_hours": round(poll_age_h, 2) if poll_age_h is not None else None,
            "poll_batch": poll_batch,
        },
        "approvals": {
            "total": total_approvals,
            "by_verdict": dict(verdict_counts),
            "approved_unique": len(approved_ids),
            "denied_unique": len(denied_ids),
            "recent": recent_approvals,
        },
        "queue": {
            "pending_count": queue_counts.get("pending", 0),
            "approved_count": queue_counts.get("approved", 0),
            "rejected_count": queue_counts.get("rejected", 0),
            "high_priority_count": queue_counts.get("high_priority", 0),
            "money_at_risk": queue_counts.get("money_at_risk", 0.0),
            "pending_items": pending_items[:10],
        },
        "budget_gate": {
            "halted": budget_halted,
            "spent_today_usd": spent_today_usd,
            "spent_month_aud": spent_month_aud,
        },
        "health": {
            "score": score,
            "label": health_label,
            "emoji": _health_color(score),
        },
        "admin_actions": {
            "needs_attention": bool(pending_items or budget_halted),
            "action_count": len(pending_items) + (1 if budget_halted else 0),
            "summary": _build_summary(tg_live, budget_halted, pending_items, total_approvals),
        },
    }

    js_path = NS_DIR / "telegram-data.js"
    js = "window.TELEGRAM_DATA = " + json.dumps(telegram_data, ensure_ascii=False, default=str) + ";\n"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)

    print("telegram-data.js refreshed", len(js), "chars")


def _build_summary(tg_live: bool, budget_halted: bool, pending_items: list, total_approvals: int) -> str:
    parts: list[str] = []
    if not tg_live:
        parts.append("کانال تلگرام غیرفعال (stub)")
    if budget_halted:
        parts.append("دروازهٔ بودجه بسته است")
    if pending_items:
        parts.append(f"{len(pending_items)} اقدام در انتظار تأیید")
    if total_approvals == 0 and tg_live:
        parts.append("هنوز تأییدی ثبت نشده")
    if not parts:
        parts.append("وضعیت عادی — نیازمند اقدام خاصی نیست")
    return " · ".join(parts)


if __name__ == "__main__":
    main()
