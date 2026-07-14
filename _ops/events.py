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
    # پیشنهاد #۱۳ — رکوردِ Incident (additive؛ خواننده‌های فعلی نمی‌شکنند)
    "incident.opened", "incident.contained",
})
APPROVAL_STATES = frozenset({"unknown", "none", "required", "approved", "denied"})

# پیشنهاد #۱۱ — نسخهٔ اسکیمای envelope (v1 = پیش از غنی‌سازی؛ v2 = با فیلدهای اختیاری + control_plane)
SCHEMA_VERSION = "event.v2"
# containment (parity با registry_scan.scrub) — هیچ رشتهٔ ممنوع در incident echo نمی‌شود
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")
# ریسک‌هایی که incidentشان به‌طور پیش‌فرض «منتظرِ مالک» علامت می‌خورد (نه اکشنِ خودکار)
_HIGH_RISK = frozenset({"R4", "R5", "R4-pending", "critical", "high"})


def _iso(ts: float) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def emit(event_name: str, agent_id: str, *, status: str = "ok",
         summary: str = "", next_action: str = "", duration_ms: int = 0,
         trace_id: str = "", approval_state: str = "unknown",
         schema_version: str = SCHEMA_VERSION, correlation_id: str = "",
         idempotency_key: str = "", enrich: bool = False,
         incident: "dict | None" = None) -> dict:
    """یک رویدادِ ساختاریافته ثبت کن. هرگز crash نمی‌کند (fail-soft). خروجی = رویداد.

    #۱۱ (backward-compatible، همه اختیاری): schema_version/correlation_id/idempotency_key
    برای همبستگی و idempotency؛ enrich=True یک بلوکِ read-onlyِ `control_plane` از
    registry (owner/risk_tier/…) به رویداد می‌چسباند (fail-soft، بدونِ I/O اگر registry نبود).
    #۱۳: incident=dict یک زیرشاخهٔ scrub-شدهٔ `incident` اضافه می‌کند.
    خواننده‌های فعلی هیچ‌کدام را لازم ندارند (فقط .get) — صفر شکست."""
    ts = time.time()
    # رفعِ E2 (2026-07-13): نامِ رویدادِ خارج از taxonomy دیگر به task.completed (سبز) coerce
    # نمی‌شود — به task.failed (قرمز) می‌رود تا drift ِ تولیدکننده «موفق» جلوه نکند؛ نامِ اصلی
    # در summary ثبت می‌شود (fail-loud). خواننده‌ها بی‌تغییر (فقط .get).
    _known = event_name in EVENT_NAMES
    _summary = str(summary or "")
    if not _known:
        _summary = f"[drift:unknown-event={str(event_name)[:32]}] " + _summary
    ev = {
        "timestamp": _iso(ts), "ts": ts,
        "trace_id": str(trace_id or "")[:40],
        "agent_id": str(agent_id or "system")[:40],
        "event_name": event_name if _known else "task.failed",
        "status": str(status or "ok")[:20],
        "summary": _summary[:200],
        "duration_ms": int(duration_ms or 0),
        "next_action": str(next_action or "")[:120],
        "approval_state": approval_state if approval_state in APPROVAL_STATES else "unknown",
        # #۱۱ — فیلدهای اختیاریِ envelope (پیش‌فرضِ صریح، هرگز null)
        "schema_version": str(schema_version or SCHEMA_VERSION)[:20],
        "correlation_id": str(correlation_id or "")[:64],
        "idempotency_key": str(idempotency_key or "")[:64],
    }
    if enrich:
        cp = _cp_lookup(ev["agent_id"])          # #۱۱ — زمینهٔ control-plane از registry (fail-soft)
        if cp:
            ev["control_plane"] = cp
    if incident is not None:
        ev["incident"] = _scrub_incident(incident)   # #۱۳ — رکوردِ scrub-شده (containment)
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
    # att فقط وقتی 🔴/🟡 می‌کند که رویدادِ محرک تازه باشد (~۳۰min) — رفعِ sticky-red
    att_recent = bool(att) and float(att.get("ts", 0) or 0) >= time.time() - 30 * 60
    is_blocked = bool(s5["failed"] or s5["blocked"]
                      or (att_recent and att.get("event_name") == "task.blocked"))
    is_waiting = bool(pending_count or s5["waiting"]
                      or (att_recent and att.get("approval_state") == "required"))
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


# ── #۱۱ control-plane enrichment (کش‌دار بر mtime، fail-soft، content-free) ────
_CP_CACHE: dict = {"mtime": 0.0, "by_slug": {}}


def _cp_path() -> Path:
    return opslib.STATE_DIR / "registry" / "registry-latest.json"


def _cp_load() -> dict:
    """snapshotِ registry → {slug: زمینهٔ control-plane}. کش بر mtime؛ هر خطا fail-soft."""
    p = _cp_path()
    try:
        mt = p.stat().st_mtime
    except OSError:
        return _CP_CACHE["by_slug"]
    if mt == _CP_CACHE["mtime"]:
        return _CP_CACHE["by_slug"]
    try:
        snap = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        return _CP_CACHE["by_slug"]
    by_slug: dict = {}
    for e in snap.get("entities", []):
        lid = str(e.get("logical_id", ""))
        cp = {"logical_id": lid, "entity_type": e.get("entity_type", "unknown"),
              "owner": e.get("owner", "unknown"), "risk_tier": e.get("risk_tier", "unknown"),
              "risk_declared": e.get("risk_declared", ""),
              "conformance": e.get("conformance_score", 0)}
        slug = lid.rsplit(":", 1)[-1] if ":" in lid else lid
        if slug:
            by_slug.setdefault(slug, cp)
        dslug = str(e.get("display_name", "")).strip().lower().replace(" ", "-")
        if dslug:
            by_slug.setdefault(dslug, cp)
    _CP_CACHE["mtime"], _CP_CACHE["by_slug"] = mt, by_slug
    return by_slug


def _cp_lookup(agent_id: str) -> dict:
    """زمینهٔ control-plane برای یک agent_id (نگاشتِ slug به موجودیتِ registry). fail-soft."""
    by_slug = _cp_load()
    if not by_slug:
        return {}
    slug = str(agent_id or "").strip().lower().replace(" ", "-")
    return dict(by_slug.get(slug, {}))


# ── #۱۳ Incident record (additive؛ telemetry/propose، هرگز اکشنِ خودکار) ────────
def _scrub_str(s: str, cap: int = 200) -> str:
    """هر رشتهٔ حاوی echo ِ ممنوع → کاملاً redact (parity با registry_scan.scrub)."""
    v = str(s or "")[:cap]
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


def _scrub_incident(d: dict) -> dict:
    """رکوردِ Incident → فیلدهای کوتاهِ content-free + scrub containment (parity با registry)."""
    return {k: _scrub_str(d.get(k, ""), 160)
            for k in ("what", "where", "risk", "path", "policy",
                      "outcome", "evidence", "replay_ref")}


def open_incident(source: str, *, what: str, where: str = "", risk: str = "unknown",
                  path: str = "", policy: str = "", evidence: str = "",
                  replay_ref: str = "", trace_id: str = "", next_action: str = "",
                  summary: str = "") -> dict:
    """incident باز کن (رویدادِ incident.opened + رکوردِ ساختاریافته). content-free.
    ریسکِ بالا → approval_state=required (منتظرِ مالک)، نه هیچ اکشنِ خودکار."""
    inc = {"what": what, "where": where, "risk": risk, "path": path,
           "policy": policy, "outcome": "open", "evidence": evidence, "replay_ref": replay_ref}
    appr = "required" if str(risk).strip() in _HIGH_RISK else "unknown"
    return emit("incident.opened", source, status="alert",
                summary=_scrub_str(summary or what),
                next_action=_scrub_str(next_action or "بررسیِ مالک", 120),
                trace_id=trace_id, approval_state=appr, enrich=True, incident=inc)


def contain_incident(source: str, *, trace_id: str = "", outcome: str = "contained",
                     note: str = "", summary: str = "") -> dict:
    """یک incident را بسته/مهارشده علامت بزن (incident.contained)."""
    return emit("incident.contained", source, status="ok",
                summary=_scrub_str(summary or f"incident {outcome}"), trace_id=trace_id,
                enrich=True, incident={"outcome": outcome, "policy": note})


def recent_incidents(n: int = 10) -> list[dict]:
    """جدیدترین incidentها برای داشبورد (باز/مهار)، جدید→قدیم."""
    inc = [e for e in _all() if str(e.get("event_name", "")).startswith("incident.")]
    return inc[-n:][::-1]


if __name__ == "__main__":
    print(json.dumps(dashboard_state(), ensure_ascii=False, indent=2))
