#!/usr/bin/env python3
"""event_bridge.py — پلِ push از رویدادهای ارگانیسم به تلگرام (فاز A).

تلگرام pull-based است (center.py:1486 poll + center.py:394 beat که فقط status/digest
ویرایش می‌کند). این ماژول، درِ push اضافه می‌کند: سه منبعِ بحرانی را در هر beat
می‌خواند و پیام‌های انسانی به مالک می‌فرستد.

سه منبع:
  1) governor-alerts.md (Tier 0: alert→push) — opslib.alert() همه‌چیز اینجا می‌نویسد.
  2) events.jsonl فیلتر incident.opened/incident.contained/task.failed.
  3) ORGANISM-STATE.json protective_mode — edge-triggered (تغییر وضعیت).

گیت: OCTOPUS_WIRE_EVENT_BRIDGE (پیش‌فرض خاموش = no-op).
امنیت: dedup با cursor (byte offset، restart-safe)؛ rate-limit سخت (نهایتاً ۱۰/ساعت)؛
  _scrub برای redact (همان parity با center.py:120)؛ fail-soft (هرگز beat را نمی‌کشد).
صدا زدن: از Center.beat() صدا زده می‌شود (مرجع: 01-INTEGRATION-CHECKLIST.md).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
sys_path_add = [str(_OPS), str(_OPS / "budget")]
for _p in sys_path_add:
    import sys
    if _p not in sys.path:
        sys.path.insert(0, _p)
import opslib  # noqa: E402

FLAG = "OCTOPUS_WIRE_EVENT_BRIDGE"
ALERTS_MD = opslib.OPS / "governor" / "governor-alerts.md"
EVENTS = opslib.STATE_DIR / "events.jsonl"
STATE = opslib.STATE_DIR / "ORGANISM-STATE.json"
# source 4 (هماهنگ با c6_state_machine.py:56 از Opus مافوق): دفترِ گذارِ تولدِ نسلی.
C6_JOURNAL = opslib.STATE_DIR / "c6" / "state-machine.jsonl"
CURSOR = opslib.STATE_DIR / "telegram" / "event-bridge-cursor.json"
MAX_PUSH_PER_HOUR = 10

# واژگانِ بحرانی — فقط این alertها push می‌شوند تا spam نشود (نه همهٔ alertها).
_CRITICAL_KW = (
    "crit", "protective", "throttle", "circuit", "fail", "incident",
    "halt", "stop-metabolic", "freeze", "quarantine", "unstable",
    "lead-naghshi", "selfheal", "deny", "denied", "broken",
)
# واژگانِ ممنوعِ echo (parity با center.py _BANNED_ECHO) — اگر در متن بود، redact.
_BANNED = ("api_key", "token", "password", "secret", "bot_token")


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _scrub(s: object) -> str:
    v = str(s if s is not None else "")
    low = v.lower()
    if any(b in low for b in _BANNED):
        return "(redacted:secret-detected)"
    return v


def _load_cursor() -> dict:
    try:
        if CURSOR.exists():
            d = json.loads(CURSOR.read_text("utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        pass
    return {}


def _save_cursor(c: dict) -> None:
    try:
        CURSOR.parent.mkdir(parents=True, exist_ok=True)
        tmp = CURSOR.with_suffix(".tmp")
        tmp.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, CURSOR)
    except Exception:  # noqa: BLE001
        pass


def _read_past(path: Path, pos: int) -> "tuple[list[str], int]":
    """خواندنِ بایت‌های پس از pos. خروجی: (lines, new_pos). file نبود → ([], 0)."""
    if not path.exists():
        return [], 0
    try:
        size = path.stat().st_size
        if size < pos:        # فایل truncate/churn شده → از صفر
            pos = 0
        if pos >= size:
            return [], size
        with path.open("rb") as f:
            f.seek(pos)
            chunk = f.read(size - pos).decode("utf-8", errors="replace")
        return chunk.splitlines(), size
    except Exception:  # noqa: BLE001
        return [], pos


def _rate_ok(cur: dict, now: float) -> bool:
    """rate-limit سخت: نهایتاً MAX_PUSH_PER_HOUR در هر پنجرهٔ ۳۶۰۰s."""
    window = cur.get("window_start", 0.0)
    count = cur.get("push_count", 0)
    if now - window >= 3600.0:
        cur["window_start"] = now
        cur["push_count"] = 0
        return True
    if count >= MAX_PUSH_PER_HOUR:
        return False
    return True


def _is_critical(line: str) -> bool:
    low = line.lower()
    return any(k in low for k in _CRITICAL_KW)


def _protective_state() -> "str | None":
    """خواندنِ protective_mode از ORGANISM-STATE.json. نبود → None."""
    try:
        if STATE.exists():
            d = json.loads(STATE.read_text("utf-8"))
            pm = d.get("protective_mode")
            pr = d.get("protective_reason", "")
            if pm:
                return str(pr or "active")
    except Exception:  # noqa: BLE001
        pass
    return None


def _human_alert(line: str) -> str:
    """یک خطِ alert را به پیامِ کوتاهِ انسانی تبدیل کن."""
    line = line.strip()
    if not line:
        return ""
    # خطوطِ alert با "## ts (metabolism)" شروع و سپس "- ⚠️ ..." می‌آیند.
    if line.startswith("- "):
        return "⚠️ " + line[2:].lstrip("⚠️").strip()[:280]
    if line.startswith("## "):
        return ""   # header تنها، skip
    return "⚠️ " + line[:280]


def _human_event(evt: dict) -> str:
    name = evt.get("event_name", "task")
    summ = str(evt.get("summary", ""))[:280]
    icon = {"incident.opened": "🔴", "incident.contained": "🟢",
            "task.failed": "❌"}.get(name, "⚠️")
    return f"{icon} {name}: {summ}"


def beat(center=None) -> dict:
    """یک تیکِ push. از Center.beat() صدا زده می‌شود. خروجی = {pushed, skipped, reason}.

    center: شیء Center (دارای متد push_alert). اگر None → فقط لاگ، بدون ارسال واقعی
    (برای تست). push_alert(center, text) امضاست.
    """
    out = {"pushed": 0, "skipped": 0}
    if not flag_on():
        out["reason"] = "flag-off"
        return out
    cur = _load_cursor()
    now = time.time()

    def _push(text: str) -> bool:
        if not text:
            return False
        if not _rate_ok(cur, now):
            out["skipped"] += 1
            return False
        ok = False
        try:
            if center is not None and hasattr(center, "push_alert"):
                ok = bool(center.push_alert(_scrub(text)))
        except Exception:  # noqa: BLE001 — fail-soft: push هرگز beat را نمی‌کشد
            ok = False
        if ok:
            out["pushed"] += 1
            cur["push_count"] = cur.get("push_count", 0) + 1
        else:
            out["skipped"] += 1
        return ok

    # ۱) governor-alerts.md — خطوطِ جدیدِ بحرانی
    lines, new_pos = _read_past(ALERTS_MD, cur.get("alerts_pos", 0))
    cur["alerts_pos"] = new_pos
    for ln in lines:
        if _is_critical(ln):
            _push(_human_alert(ln))

    # ۲) events.jsonl — incident.* / task.failed جدید
    elines, epos = _read_past(EVENTS, cur.get("events_pos", 0))
    cur["events_pos"] = epos
    for ln in elines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            evt = json.loads(ln)
        except ValueError:
            continue
        if evt.get("event_name") in ("incident.opened", "incident.contained", "task.failed"):
            _push(_human_event(evt))

    # ۳) protective-halt — edge-triggered (فقط تغییرِ وضعیت)
    prot = _protective_state()
    last_prot = cur.get("last_prot")
    if prot and prot != last_prot:
        _push(f"🛑 protective-halt فعال: {prot[:200]}")
        cur["last_prot"] = prot
    elif not prot and last_prot:
        _push("🟢 protective-halt برخشت — ارگانیسم به حالت عادی")
        cur["last_prot"] = None

    # ۴) c6 state-machine journal (تولدِ نسلی — هماهنگ با c6_state_machine.py:56 از Opus).
    # فقط گذارهای مهم را push کن: ADMITTED، TRANSPLANTED (تولد)، QUARANTINED، DENIED،
    # REJECTED. ردیف‌های تکراری با cursor dedup می‌شوند (byte offset).
    if C6_JOURNAL.exists():
        clines, cpos = _read_past(C6_JOURNAL, cur.get("c6_pos", 0))
        cur["c6_pos"] = cpos
        for ln in clines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                t = json.loads(ln)
            except ValueError:
                continue
            to_st = str(t.get("to", ""))
            if to_st in ("ADMITTED", "TRANSPLANTED", "QUARANTINED", "DENIED", "REJECTED"):
                rid = str(t.get("repro_id", "?"))[:24]
                _push(_human_c6(to_st, rid, t.get("from")))

    _save_cursor(cur)
    return out


def _human_c6(to_state: str, rid: str, from_state) -> str:
    """گذارِ c6 را به پیامِ انسانی تبدیل کن. تولدِ نسلی = TRANSPLANTED (tapِ مالک)."""
    icon = {"TRANSPLANTED": "🌱", "ADMITTED": "✅", "QUARANTINED": "🟡",
            "DENIED": "🚫", "REJECTED": "❌"}.get(to_state, "🔄")
    label = {"TRANSPLANTED": "تولدِ نسلی (کدِ نو پذیرفته شد)",
             "ADMITTED": "یافتهٔ خودبهبودی پذیرفته شد",
             "QUARANTINED": "آزمایش قرنطینه شد",
             "DENIED": "مالک رد کرد",
             "REJECTED": "رد شد"}.get(to_state, to_state)
    frm = f" (از {from_state})" if from_state else ""
    return f"{icon} تولید مثل-C6: {label}{frm} · {rid}"
