#!/usr/bin/env python3
"""execution_board.py — «تختهٔ اجرا» (Execution Board) کنترل-پلین (فقط‌خواندنی).

مدلِ دادهٔ doctrineِ کنترل-پلین: هر کارِ ارگانیسم در یک «خطِ» (lane) دیده می‌شود تا
مالک در یک نگاه بفهمد چه در صف است، چه در حالِ اجراست، چه گیر کرده، چه منتظرِ اوست،
چه تمام شده و چه قرنطینه (شکست‌خورده) شده. این ماژول هیچ چیزی را حرکت نمی‌دهد؛ فقط
از **stateِ موجود** خطوط را استنتاج می‌کند (عینِ idiomِ stress.py / innervation.py:
داشبورد صداشان می‌زند، خودشان هرگز نمی‌نویسند).

منبعِ خطوط (فقط خواندن، fail-soft):
  • لاگِ رویداد (`state/events.jsonl`) →
        task.started (بی‌پایانِ بعدی) → running
        task.completed               → done
        task.failed                  → quarantined
        task.blocked                 → blocked
        approval.required / approval_state=="required" → awaiting_user
  • نقشه/حالتِ پمپِ کار (`state/pulse/work-plan.json` + `work-state.json`) →
        templateهای سررسیده ولی هنوز اجرا نشده → queued

ناوردی‌ها: $0 · stdlib + opslib · read-only (هیچ نوشتنِ دیسک، هیچ mutation، هیچ اثرِ
import-time) · fail-soft (فایلِ نبود → خطِ خالی، هرگز crashِ صداکننده) · containment
(هیچ رشتهٔ هویتِ Project-F هرگز echo نمی‌شود — scrub با _BANNED_ECHO، parity با
registry_scan.scrub / events._scrub_str). کران‌دار: حداکثر CAP آیتم در هر خط.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

CAP = 12                # سقفِ آیتم در هر خط (کران‌دار، ضدِ طوفانِ رویداد)
MAX_SCAN = 500          # چند خطِ آخرِ events.jsonl خوانده شود (هم‌ارز events.MAX_KEEP)

# containment (parity با registry_scan.scrub) — هیچ رشتهٔ ممنوع بیرون نمی‌رود
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا")

# رویدادهایی که یک taskِ startedِ باز را «بسته» می‌کنند (هم‌ارز events.now_line)
_TERMINAL = frozenset({"task.completed", "task.failed", "task.blocked"})

LANES = ("queued", "running", "blocked", "awaiting_user", "done", "quarantined")


# ─── ابزارِ خواندن fail-soft ─────────────────────────────────────────────────────
def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else {}
    except (OSError, ValueError):
        return {}


def _read_events() -> list[dict]:
    """آخرین MAX_SCAN رویداد از state/events.jsonl (قدیمی→جدید). fail-soft → []."""
    p = opslib.STATE_DIR / "events.jsonl"
    try:
        if not p.exists():
            return []
        out: list[dict] = []
        for ln in p.read_text("utf-8").splitlines()[-MAX_SCAN:]:
            try:
                rec = json.loads(ln)
            except ValueError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
        return out
    except OSError:
        return []


def _scrub(s: object) -> str:
    """رشتهٔ حاویِ echo ِ ممنوع → کاملاً redact (parity با registry_scan.scrub)."""
    v = str(s if s is not None else "")
    low = v.lower()
    if any(b in low or b in v for b in _BANNED_ECHO):
        return "(redacted:containment)"
    return v


# ─── نگاشتِ رویداد → خط ───────────────────────────────────────────────────────────
def _lane_for(ev: dict) -> str | None:
    """خطِ یک رویدادِ پایانی (منحصربه‌فرد). task.started اینجا None است (خطِ running
    از رهگیریِ open جدا استنتاج می‌شود). approval غالب است بر blocked (منتظرِ مالک)."""
    name = ev.get("event_name")
    if name == "approval.required" or ev.get("approval_state") == "required":
        return "awaiting_user"
    if name == "task.blocked":
        return "blocked"
    if name == "task.failed":
        return "quarantined"
    if name == "task.completed":
        return "done"
    return None


def _item(ev: dict) -> dict:
    """آیتمِ خط: content-free، scrub-شده، کوتاه (خوراکِ UI)."""
    return {
        "agent": _scrub(str(ev.get("agent_id", ""))[:40]),
        "summary": _scrub(str(ev.get("summary", ""))[:120]),
        "status": _scrub(str(ev.get("status", ""))[:20]),
        "t": str(ev.get("timestamp", ""))[-8:],       # HH:MM:SS
        "trace": _scrub(str(ev.get("trace_id", ""))[:40]),
        "next": _scrub(str(ev.get("next_action", ""))[:80]),
        "event": str(ev.get("event_name", ""))[:24],
    }


def _queued() -> list[dict]:
    """templateهای پمپِ کار که سررسیده‌اند ولی هنوز اجرا نشده‌اند = صفِ کار. fail-soft."""
    import time
    pulse = opslib.STATE_DIR / "pulse"
    plan = _read_json(pulse / "work-plan.json")
    state = _read_json(pulse / "work-state.json")
    last_run = state.get("last_run") or {}
    if not isinstance(last_run, dict):
        last_run = {}
    now = time.time()
    out: list[dict] = []
    for tpl in (plan.get("templates") or []):
        if not isinstance(tpl, dict):
            continue
        kind = tpl.get("kind")
        if not kind:
            continue
        try:
            every = float(tpl.get("every_s", 86400) or 86400)
            lr = float(last_run.get(kind, 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if now - lr >= every:                     # سررسید شده → در صف
            out.append({
                "kind": _scrub(str(kind)[:40]),
                "goal": _scrub(str(tpl.get("goal", ""))[:120]),
                "paid": bool(tpl.get("paid", False)),
                "every_s": int(every),
            })
    return out


# ─── API ─────────────────────────────────────────────────────────────────────────
def board() -> dict:
    """تختهٔ اجرا: شش خط + شمارش. خالص، read-only، fail-soft (نبودِ فایل → خطِ خالی)."""
    lanes: dict[str, list] = {k: [] for k in LANES}

    # ۱) رویدادها → running / blocked / awaiting_user / done / quarantined
    try:
        evs = _read_events()
        # running = task.startedِ هنوز باز (بدونِ رویدادِ پایانیِ بعدی روی همان trace)
        open_tasks: dict = {}
        for ev in evs:                            # قدیمی→جدید
            name = ev.get("event_name")
            key = ev.get("trace_id") or ev.get("agent_id") or ev.get("summary") or id(ev)
            if name == "task.started":
                open_tasks[key] = ev
            elif name in _TERMINAL:
                open_tasks.pop(key, None)
        for ev in list(open_tasks.values())[::-1][:CAP]:   # جدید→قدیم
            lanes["running"].append(_item(ev))
        # خطوطِ پایانی، جدید→قدیم، کران‌دار. dedup بر اساسِ agent_id تا چند
        # شکستِ پشت‌سرِهمِ یک عضو (مثلاً lead-naghshi ۳ بار failed) کلِ خطِ
        # blocked را پر نکند — فقط آخرین وضعیتِ هر agent دیده می‌شود.
        _seen_agents: set[str] = set()
        for ev in reversed(evs):
            lane = _lane_for(ev)
            if lane in ("blocked", "awaiting_user", "done", "quarantined") \
                    and len(lanes[lane]) < CAP:
                _ag = str(ev.get("agent_id", ""))
                if _ag and _ag in _seen_agents:
                    continue   # همین agent قبلاً در همین خط ثبت شد
                if _ag:
                    _seen_agents.add(_ag)
                lanes[lane].append(_item(ev))
    except Exception as e:  # noqa: BLE001 — مشاهده هرگز صداکننده را نمی‌کشد
        try:
            opslib.alert([f"execution_board events lane failed: {e}"])
        except Exception:  # noqa: BLE001
            pass

    # ۲) صفِ کار از نقشه/حالتِ پمپ
    try:
        lanes["queued"] = _queued()[:CAP]
    except Exception as e:  # noqa: BLE001
        try:
            opslib.alert([f"execution_board queued lane failed: {e}"])
        except Exception:  # noqa: BLE001
            pass

    counts = {k: len(lanes[k]) for k in LANES}
    counts["total"] = sum(counts.values())
    return {"ts": opslib.now_iso(), "schema": "execution-board.v1", **lanes, "counts": counts}


if __name__ == "__main__":
    print(json.dumps(board(), ensure_ascii=False, indent=2))