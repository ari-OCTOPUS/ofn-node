#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""weekly_review — مرورِ هفتگیِ شنبه صبح (رأی ۱۲ + سنجه‌های §۹ منشور).

«شنبه صبح — هر بیزنس: چه شد/چه ماند/چه بعد + خلاصهٔ پول + گزارشِ کارهای
خودکارِ هفته؛ مالک فقط مرور و تصمیم.»

اصلِ حاکم: **عددِ ساختگی ممنوع.** هر بخشی که داده‌اش روی دیسک نیست صادقانه
«داده‌ای نیست» می‌گوید — توان/اعتماد/پولِ جعلی هرگز (درسِ رسیدِ leg_tasks).

منابعِ داده (همه read-only و fail-soft):
  · leg_tasks (recent_done/queue/blockers) — چه شد/چه ماند/چه بعد
  · funnel.db (رویدادهای هفتهٔ لید: تحویل‌شده، paid)
  · ORGANISM-STATE.json → business_legs (نبضِ ziman/mining/…)
  · budget/telemetry.snapshot(write=False) — جمعِ ماهِ Accounting به AUD
  · tg_send_log.stats — گزارشِ خودکارها
  · state/reminders (اگر لِینِ E ساخته باشد) — یادآوری‌های fired
  · state/telegram/approvals/*.json — نرخِ تأییدِ کارت‌ها به تفکیکِ نوع؛
    نوعِ >۹۰٪ تأیید ⇒ «گیت شل است» ⇒ پیشنهادِ تنزلِ طبقه (§۹)
  · question_budget — سؤال‌های مصرف‌شده از ۳۰

زمان: شنبهٔ میلادی (weekday()==5)، ساعتِ محلیِ سیدنی (ساعتِ ماشین)، بعد از
۰۸:۰۰، یک بار در هفته (cursor ِ هفتهٔ ISO در state dict — ذخیرهٔ state با
صداکننده است). این ماژول **هیچ‌چیز نمی‌فرستد** — ارسال با `send_dm_fn` ِ
تزریقیِ لِینِ wiring، پشتِ فلگ `OCTOPUS_TG_WEEKLY_REVIEW` (پیش‌فرض خاموش).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent

FLAG = "OCTOPUS_TG_WEEKLY_REVIEW"
CURSOR_KEY = "last_weekly_review"
WEEK_S = 7 * 86400.0
NO_DATA = "داده‌ای نیست"
DEMOTE_THRESHOLD = 90.0            # §۹: بالای ۹۰٪ تأیید = گیت شل است
DEMOTE_MIN_N = 3                   # با کمتر از ۳ کارت درصد معنی ندارد

BUSINESS_LEGS = ("lead", "ziman", "mining", "crypto", "accounting")
DISPLAY = {"lead": "🎨 نقاشی", "ziman": "🖼 زیمان", "mining": "⛏ ماینینگ",
           "crypto": "📈 کریپتو", "accounting": "🧾 حسابداری"}

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(n) -> str:
    return str(n).translate(_FA)


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _state_dir() -> Path:
    base = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if base:
        return Path(base)
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        import opslib
        return Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state"


def _week_key(now: float) -> str:
    y, w, _ = datetime.fromtimestamp(float(now)).isocalendar()
    return f"{y}-W{int(w):02d}"


# ── due-logic ──────────────────────────────────────────────────────────────
def is_due(*, now: float, state: dict) -> bool:
    """شنبه (میلادی، weekday==5) بعد از ۰۸:۰۰ به وقتِ محلی، یک بار در هفته."""
    dt = datetime.fromtimestamp(float(now))
    if dt.weekday() != 5 or dt.hour < 8:
        return False
    return (state or {}).get(CURSOR_KEY) != _week_key(now)


# ── منابعِ داده (همه fail-soft: خطا/غیاب ⇒ None) ───────────────────────────
def _leg_tasks():
    try:
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import leg_tasks as lt
        return lt
    except Exception:  # noqa: BLE001
        return None


def _funnel_week_counts(now: float) -> "dict | None":
    """شمارِ رویدادهای قیف در پنجرهٔ ۷ روز، به تفکیکِ event_type. فقط‌خواندنی."""
    db = _state_dir() / "outcomes" / "funnel.db"
    if not db.exists():
        return None
    since = datetime.fromtimestamp(float(now) - WEEK_S,
                                   timezone.utc).isoformat()
    try:
        con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
        try:
            rows = con.execute(
                "SELECT event_type, COUNT(*) FROM funnel_events "
                "WHERE occurred_at >= ? GROUP BY event_type",
                (since,)).fetchall()
        finally:
            con.close()
        return {str(k): int(v) for k, v in rows}
    except sqlite3.Error:
        return None


def _business_legs_state() -> dict:
    """ORGANISM-STATE → business_legs — هر دو شکلِ دولایه/تخت (الگوی render)."""
    try:
        org = json.loads((_state_dir() / "ORGANISM-STATE.json")
                         .read_text("utf-8"))
    except (OSError, ValueError):
        return {}
    bl = org.get("business_legs")
    if (isinstance(bl, dict) and isinstance(bl.get("business_legs"), dict)
            and "mining" not in bl):
        bl = bl["business_legs"]
    out = {}
    if isinstance(bl, dict):
        for k, v in bl.items():
            if isinstance(v, dict):
                out[str(v.get("leg") or k)] = v
    elif isinstance(bl, list):
        for v in bl:
            if isinstance(v, dict) and v.get("leg"):
                out[str(v["leg"])] = v
    return out


def _month_aud() -> "float | None":
    """جمعِ ماهِ Accounting به AUD از تلمتری (write=False — صفر اثر)."""
    try:
        budget = str(_HERE.parent / "budget")
        if budget not in sys.path:
            sys.path.insert(0, budget)
        import telemetry
        snap = telemetry.snapshot(write=False)
        return float(snap["month"]["aud"])
    except Exception:  # noqa: BLE001
        return None


def _send_log_week() -> "dict | None":
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        import tg_send_log
        s = tg_send_log.stats(window_h=168.0)
        return s if s.get("sends") else None
    except Exception:  # noqa: BLE001
        return None


def _reminders_fired_week(now: float) -> "int | None":
    """یادآوری‌های fired ِ هفته — store ِ لِینِ E اگر موجود بود؛ نبود ⇒ None."""
    rdir = _state_dir() / "reminders"
    if not rdir.is_dir():
        return None
    since = float(now) - WEEK_S
    fired = 0
    try:
        for p in list(rdir.glob("*.json")) + list(rdir.glob("*.jsonl")):
            try:
                raw = p.read_text("utf-8")
            except OSError:
                continue
            rows = []
            if p.suffix == ".jsonl":
                for line in raw.splitlines():
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        continue
            else:
                try:
                    d = json.loads(raw)
                    rows = d if isinstance(d, list) else [d]
                except ValueError:
                    continue
            for r in rows:
                if not isinstance(r, dict):
                    continue
                ts = r.get("fired_ts") or r.get("fired") or 0
                try:
                    if (str(r.get("status") or "") == "fired"
                            or float(ts or 0) >= since):
                        fired += 1
                except (TypeError, ValueError):
                    continue
    except OSError:
        return None
    return fired


_POSITIVE = frozenset({"ok", "approve", "approved", "yes", "good"})
_NEGATIVE = frozenset({"no", "deny", "denied", "reject", "rejected", "bad"})


def _approval_rates(now: float) -> dict:
    """نرخِ تأیید به تفکیکِ نوع از state/telegram/approvals (پنجرهٔ ۷ روز).
    خروجی: {type: {"ok": n, "total": n, "rate": float}} — فقط رأی‌های صریح."""
    adir = _state_dir() / "telegram" / "approvals"
    if not adir.is_dir():
        return {}
    since = datetime.fromtimestamp(float(now) - WEEK_S)
    out: dict = {}
    for p in adir.glob("*.json"):
        try:
            d = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict):
            continue
        v = str(d.get("verdict") or "").strip().lower()
        if v not in _POSITIVE and v not in _NEGATIVE:
            continue
        try:
            ts = datetime.fromisoformat(str(d.get("ts") or ""))
        except ValueError:
            continue
        if ts.tzinfo is not None:            # مقایسهٔ naive-local ِ یکدست
            ts = ts.astimezone().replace(tzinfo=None)
        if ts < since:
            continue
        kind = str(d.get("type") or d.get("kind") or d.get("source")
                   or "unknown")
        row = out.setdefault(kind, {"ok": 0, "total": 0})
        row["total"] += 1
        if v in _POSITIVE:
            row["ok"] += 1
    for row in out.values():
        row["rate"] = round(100.0 * row["ok"] / row["total"], 1) \
            if row["total"] else 0.0
    return out


# ── ساختِ متن ──────────────────────────────────────────────────────────────
def _leg_section(leg: str, *, now: float, funnel: "dict | None",
                 org_legs: dict) -> list:
    """بخشِ یک پا: چه شد / چه ماند / چه بعد / پول — صادقانه، بی‌عددسازی."""
    lt = _leg_tasks()
    lines = [f"{DISPLAY.get(leg, leg)}"]
    week0 = float(now) - WEEK_S
    done = queued = blocked = []
    if lt is not None:
        try:
            done = [t for t in lt.recent_done(leg, 50)
                    if float(t.get("updated") or 0) >= week0
                    and t.get("result") != "لغو شد"]
            open_rows = lt.queue(leg)
            queued = [t for t in open_rows if t.get("state") == lt.QUEUED]
            blocked = [t for t in open_rows if t.get("state") == lt.BLOCKED]
        except Exception:  # noqa: BLE001
            done = queued = blocked = []

    shod = []
    if done:
        shod.append(f"{_fa(len(done))} کار تمام شد")
    if leg == "lead" and funnel:
        n = sum(funnel.values())
        if n:
            shod.append(f"{_fa(n)} رویدادِ قیف این هفته")
    org = org_legs.get(leg) if isinstance(org_legs, dict) else None
    note = str((org or {}).get("note") or (org or {}).get("signal")
               or "").strip()
    if not shod and note:
        shod.append(note[:80])

    if not (shod or queued or blocked):
        if leg == "ziman":
            lines.append("· کم‌صدا — رخدادِ مهمی ثبت نشده")
        else:
            lines.append("· هنوز فعالیتی ثبت نشده")
        lines.append(f"· پول: {NO_DATA}")
        return lines

    lines.append("· چه شد: " + (" · ".join(shod) if shod else "—"))
    mand = []
    if queued:
        mand.append(f"{_fa(len(queued))} در صف")
    if blocked:
        q = (blocked[0].get("question") or "—")[:80]
        mand.append(f"مانع: {q}")
    lines.append("· چه ماند: " + (" · ".join(mand) if mand else "—"))
    lines.append("· چه بعد: " + (queued[0]["text"][:80] if queued else "—"))

    money = None
    if leg == "lead" and funnel:
        paid = int(funnel.get("invoice.paid", 0))
        if paid:
            money = f"{_fa(paid)} فاکتورِ paid این هفته"
    lines.append(f"· پول: {money or NO_DATA}")
    return lines


def review_text(*, now: float, cfg: "dict | None" = None) -> str:
    """متنِ کاملِ مرورِ هفتگی — خالص (هیچ ارسالی)، همهٔ منابع fail-soft."""
    now = float(now)
    dt = datetime.fromtimestamp(now)
    funnel = _funnel_week_counts(now)
    org_legs = _business_legs_state()

    lines = [f"📅 <b>مرور هفتگی</b> — شنبه {_fa(dt.strftime('%Y-%m-%d'))}", ""]
    for leg in BUSINESS_LEGS:
        lines += _leg_section(leg, now=now, funnel=funnel, org_legs=org_legs)
        lines.append("")

    aud = _month_aud()
    lines.append("💰 جمع Accounting (ماه): "
                 + (f"AU${_fa(round(aud, 2))}" if aud is not None else NO_DATA))

    slog = _send_log_week()
    lines.append("🤖 خودکارهای هفته: "
                 + (f"{_fa(slog['sends'])} ارسال" if slog else NO_DATA))

    lines += ["", "📏 <b>سنجه‌ها (§۹)</b>"]
    fired = _reminders_fired_week(now)
    lines.append("· یادآوری‌های fired: "
                 + (_fa(fired) if fired is not None else NO_DATA))
    delivered = None
    if funnel:
        delivered = int(funnel.get("proposal.routed", 0))
    lines.append("· لیدهای تحویل‌شده: "
                 + (_fa(delivered) if delivered else (NO_DATA if not funnel
                                                     else _fa(0))))
    try:
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import question_budget as qb
        lines.append(f"· سؤال از بودجهٔ {_fa(qb.WEEK_CAP)}: "
                     f"{_fa(qb.used(now))} مصرف · {_fa(qb.remaining(now))} مانده")
    except Exception:  # noqa: BLE001
        lines.append(f"· سؤال از بودجهٔ ۳۰: {NO_DATA}")

    rates = _approval_rates(now)
    if rates:
        lines.append("· نرخ تأیید کارت‌ها:")
        for kind in sorted(rates):
            r = rates[kind]
            lines.append(f"  – {kind}: ٪{_fa(r['rate'])} "
                         f"({_fa(r['ok'])} از {_fa(r['total'])})")
        for kind in sorted(rates):
            r = rates[kind]
            if r["total"] >= DEMOTE_MIN_N and r["rate"] > DEMOTE_THRESHOLD:
                lines.append(f"پیشنهاد: این نوع را یک طبقه پایین بیاور "
                             f"(T پایین‌تر) — «{kind}» ٪{_fa(r['rate'])} "
                             f"تأیید شده؛ گیت شل است.")
    else:
        lines.append(f"· نرخ تأیید کارت‌ها: {NO_DATA}")

    return "\n".join(lines)


# ── قراردادِ beat (لِینِ wiring صدا می‌زند) ────────────────────────────────
def beat(*, now: "float | None" = None, cfg: "dict | None" = None,
         send_dm_fn=None, state: "dict | None" = None) -> bool:
    """در beat ِ مرکز، پشتِ فلگ `OCTOPUS_TG_WEEKLY_REVIEW`.

    `send_dm_fn(text) -> truthy` روی موفقیت (شناسهٔ پیام). cursor ِ هفته فقط
    بعد از ارسالِ موفق جلو می‌رود (الگوی mark_urgent_flushed) — ذخیرهٔ خودِ
    `state` با صداکننده است. خروجی True = مرور فرستاده شد."""
    if not enabled():
        return False
    now = float(now if now is not None else time.time())
    if not isinstance(state, dict) or not callable(send_dm_fn):
        return False
    if not is_due(now=now, state=state):
        return False
    text = review_text(now=now, cfg=cfg or {})
    try:
        ok = send_dm_fn(text)
    except Exception:  # noqa: BLE001
        return False
    if not ok:
        return False
    state[CURSOR_KEY] = _week_key(now)
    return True
