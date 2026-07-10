#!/usr/bin/env python3
"""events.py — ستون‌فقراتِ رویدادِ ساختاریافته برای داشبوردِ اتوماسیونِ مینیمال (جلسه ۴۶).

رأی مالک: «داشبوردِ اتوماسیونِ مینیمال و عمل‌گرا — خودش اجرا کند، فقط خلاصه بگوید،
هر ۵ دقیقه یا رخدادِ مهم آپدیت بده.» به‌جای لاگِ متنیِ آزاد، هر نقطهٔ مهم یک رویدادِ
ساختاریافته emit می‌کند → `state/events.jsonl`. داشبورد فقط state خلاصه را نشان می‌دهد.

اسکیمای هر رویداد (دقیقاً طبقِ اسپکِ مالک):
  timestamp · trace_id · agent_id · event_name · status · summary · duration_ms
  · next_action · approval_state (صریح: unknown/none/required/approved/denied — نه null)

event_name ∈ {task.started, task.completed, task.failed, task.blocked,
              handoff.created, system.heartbeat, approval.required}

$0 · stdlib-only · fail-soft · بی‌محتوا (فقط خلاصهٔ عمومی؛ هیچ secret/محتوای خصوصی).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE / "budget"))
import opslib  # noqa: E402

LOG = opslib.STATE_DIR / "events.jsonl"
MAX_KEEP = 500

EVENT_NAMES = frozenset({
    "task.started", "task.completed", "task.failed", "task.blocked",
    "handoff.created", "system.heartbeat", "approval.required",
})
APPROVAL_STATES = frozenset({"unknown", "none", "required", "approved", "denied"})


def _iso(ts: float) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def emit(event_name: str, agent_id: str, *, status: str = "ok",
         summary: str = "", next_action: str = "", duration_ms: int = 0,
         trace_id: str = "", approval_state: str = "unknown") -> dict:
    """یک رویدادِ ساختاریافته ثبت کن. هرگز crash نمی‌کند (fail-soft). خروجی = رویداد."""
    ts = time.time()
    ev = {
        "timestamp": _iso(ts), "ts": ts,
        "trace_id": str(trace_id or "")[:40],
        "agent_id": str(agent_id or "system")[:40],
        "event_name": event_name if event_name in EVENT_NAMES else "task.completed",
        "status": str(status or "ok")[:20],
        "summary": str(summary or "")[:200],
        "duration_ms": int(duration_ms or 0),
        "next_action": str(next_action or "")[:120],
        "approval_state": approval_state if approval_state in APPROVAL_STATES else "unknown",
    }
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return ev


def _all() -> list[dict]:
    try:
        if not LOG.exists():
            return []
        out = []
        for ln in LOG.read_text("utf-8").splitlines()[-MAX_KEEP:]:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out
    except OSError:
        return []


def recent(n: int = 12) -> list[dict]:
    return _all()[-n:][::-1]


def summary_window(minutes: float = 5) -> dict:
    """خلاصهٔ پنجرهٔ اخیر: شمارِ رویدادها، تمام‌شده‌ها، منتظرها، خطاها، گیرکرده‌ها."""
    cutoff = time.time() - minutes * 60
    evs = [e for e in _all() if float(e.get("ts", 0)) >= cutoff]
    c = {"events": len(evs), "completed": 0, "failed": 0, "blocked": 0,
         "waiting": 0, "started": 0}
    for e in evs:
        n = e.get("event_name", "")
        if n == "task.completed":
            c["completed"] += 1
        elif n == "task.failed":
            c["failed"] += 1
        elif n == "task.blocked":
            c["blocked"] += 1
        elif n == "task.started":
            c["started"] += 1
        if e.get("approval_state") == "required":
            c["waiting"] += 1
    return c


def now_line() -> str:
    """«الان چیکار می‌کند» — آخرین task.startedِ بدونِ completed/failedِ بعدی، وگرنه idle."""
    evs = _all()
    started = {}
    for e in evs:
        tr = e.get("trace_id") or e.get("summary")
        if e.get("event_name") == "task.started":
            started[tr] = e
        elif e.get("event_name") in ("task.completed", "task.failed", "task.blocked"):
            started.pop(tr, None)
    if started:
        last = list(started.values())[-1]
        return last.get("summary") or last.get("agent_id", "کار")
    return ""


def last_outcome() -> dict | None:
    for e in reversed(_all()):
        if e.get("event_name") in ("task.completed", "task.failed"):
            return e
    return None


def attention() -> dict | None:
    """چیزی که گیر کرده یا منتظرِ توست (blocked یا approval.required)، جدیدترین."""
    for e in reversed(_all()):
        if e.get("event_name") == "task.blocked" or e.get("approval_state") == "required":
            return e
    return None


def dashboard_state(pending_count: int = 0) -> dict:
    """کلِ state خلاصهٔ داشبورد در یک dict — خوراکِ UI (بدونِ raw log خام)."""
    s5 = summary_window(5)
    att = attention()
    lo = last_outcome()
    # 🔴 فقط برای خرابی/گیرِ واقعی؛ منتظرِ تأییدِ تو = 🟡 نه 🔴
    is_blocked = bool(s5["failed"] or s5["blocked"]
                      or (att and att.get("event_name") == "task.blocked"))
    is_waiting = bool(pending_count or s5["waiting"]
                      or (att and att.get("approval_state") == "required"))
    overall = "🔴 گیر" if is_blocked else ("🟡 منتظرِ تو" if is_waiting else "🟢 روان")
    return {
        "ts": opslib.now_iso(), "schema": "dashboard-state.v1",
        "overall": overall,
        "now": now_line() or "—",
        "last_outcome": (lo.get("summary") if lo else "—"),
        "last_status": (lo.get("status") if lo else ""),
        "attention": (att.get("summary") if att else ""),
        "attention_next": (att.get("next_action") if att else ""),
        "pending": int(pending_count),
        "summary_5m": s5,
        "log": [{"t": e.get("timestamp", "")[-8:], "name": e.get("event_name"),
                 "agent": e.get("agent_id"), "summary": e.get("summary"),
                 "status": e.get("status")} for e in recent(12)],
    }


if __name__ == "__main__":
    print(json.dumps(dashboard_state(), ensure_ascii=False, indent=2))
