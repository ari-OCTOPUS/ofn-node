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
  · budget/telemetry.snapshot(write=False) — خرجِ LLM ِ خودِ اختاپوس (AUD/ماه)
  · «10 - Telegram processing/Raw» (ORG_ROOT) — سطرهای هزینهٔ capture ِ مالک
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

# 2026-08-03: `studio_pf` افزوده شد — تا امروز سکوتِ این پا حتی در گزارشِ هفتگی هم
# دیده نمی‌شد (رأیِ مالک: «هرکاری می‌کنن اختاپوس یادش بمونه»). نامِ نمایشی عمداً
# خنثی است: بیرون از پوشهٔ پروژه فقط کدِ «Project-F» (قاعدهٔ قفل‌شدهٔ #۷).
# گاردِ parity در `_ops/tests/test_leg_registry_parity.py` تضمین می‌کند این فهرست
# از `wiring._BUSINESS_LEGS_SPEC` عقب نماند (`knowledge` تا امروز جا افتاده بود).
BUSINESS_LEGS = ("lead", "ziman", "mining", "crypto", "accounting",
                 "knowledge", "studio_pf")
DISPLAY = {"lead": "🎨 نقاشی", "ziman": "🖼 زیمان", "mining": "⛏ ماینینگ",
           "crypto": "📈 کریپتو", "accounting": "🧾 حسابداری",
           "knowledge": "📚 دانش", "studio_pf": "🅿️ Project-F"}

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
    """یادآوری‌های شلیک‌شدهٔ هفته — از شکلِ **واقعیِ** store ِ لِینِ E.

    بازبینیِ ۰۷-۳۱ (BLOCKER 3): reminders.json یک dict است —
    ``{"seq": int, "items": [...]}`` — و نسخهٔ قبلی آن را ``rows=[d]`` می‌کرد،
    یعنی کلِ store یک «ردیف» شمرده می‌شد و شمار همیشه ۰ بود. حالا items
    خوانده می‌شود و فقط آیتم‌هایی می‌شمارند که ``fired_ts`` ِ داخلِ پنجرهٔ
    هفته دارند — fired ِ بی‌مهرِ زمان ادعای «این هفته» نیست (عددِ ساختگی
    ممنوع). نبودِ دایرکتوری ⇒ None (غیابِ صادقانه)."""
    rdir = _state_dir() / "reminders"
    if not rdir.is_dir():
        return None
    since = float(now) - WEEK_S
    fired = 0
    try:
        for p in rdir.glob("*.json"):
            try:
                d = json.loads(p.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            items = d.get("items") if isinstance(d, dict) else d
            if not isinstance(items, list):
                continue                 # config.json و هر شکلِ دیگر — نه store
            for r in items:
                if not isinstance(r, dict):
                    continue
                try:
                    ts = float(r.get("fired_ts") or 0)
                except (TypeError, ValueError):
                    continue
                if since < ts <= float(now):
                    fired += 1
    except OSError:
        return None
    return fired


# ── کیفیتِ یادآوری (§۹): شلیک ≠ مفید ───────────────────────────────────────
# «یادآوری‌های به‌موقع/مفید» ِ منشور با یک شمارندهٔ fired سنجیده نمی‌شود؛
# یادآوری‌ای که مالک همان لحظه «بعداً» زد، شلیک شد ولی کار نکرد.
#
# ⚠️ محدودیتِ صادقانهٔ شکلِ داده (reminders.py مالِ لِینِ E است و این‌جا عوض
# نمی‌شود): store نه `done_ts` دارد نه شمارندهٔ snooze. پس تنها چیزی که از
# روی *وضعِ فعلی* قابلِ استنتاج است این است:
#   · fired   = آیتمی که `fired_ts` ِ آن داخلِ پنجرهٔ هفته است
#   · done    = همان‌ها که الان `done=True`اند
#   · snoozed = همان‌ها که `done` نیستند ولی `fired` دوباره False شده —
#               امضای منحصربه‌فردِ `reminders.snooze` (fired را صفر می‌کند و
#               `fired_ts` را دست نمی‌زند)
#   · open    = بقیه (شلیک شد، نه انجام، نه به تعویق)
# دو تعویقِ پشت‌سرهم یک بار شمرده می‌شود و «انجام‌شده بعد از تعویق» در ستونِ
# done می‌نشیند. همین محدودیت در متن هم اعلام می‌شود («وضعِ فعلی») تا عدد
# بیش از آن‌چه هست ادعا نکند.
def _reminder_quality(now: float) -> "dict | None":
    rdir = _state_dir() / "reminders"
    if not rdir.is_dir():
        return None
    since = float(now) - WEEK_S
    q = {"fired": 0, "done": 0, "snoozed": 0, "open": 0}
    try:
        for p in rdir.glob("*.json"):
            try:
                d = json.loads(p.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            items = d.get("items") if isinstance(d, dict) else d
            if not isinstance(items, list):
                continue                 # config.json و هر شکلِ دیگر — نه store
            for r in items:
                if not isinstance(r, dict):
                    continue
                try:
                    ts = float(r.get("fired_ts") or 0)
                except (TypeError, ValueError):
                    continue
                if not (since < ts <= float(now)):
                    continue
                q["fired"] += 1
                if r.get("done"):
                    q["done"] += 1
                elif not r.get("fired"):
                    q["snoozed"] += 1
                else:
                    q["open"] += 1
    except OSError:
        return None
    return q


# ── ساعتِ آزادشدهٔ مالک (§۹) — تخمین، با فرمولِ نمایان ─────────────────────
# رأیِ ساختاری: «ساعتِ آزادشده» ذاتاً اندازه‌گیری‌شدنی نیست (هیچ‌کس کرنومتر
# نزده). پس یا تخمینِ **برچسب‌دارِ فرمول‌نما** می‌دهیم یا هیچ — عددِ لختِ
# بی‌فرمول همان «عددِ ساختگی» ِ ممنوعِ این ماژول است.
MIN_PER_TASK = 10        # کارِ موتور که مالک هیچ ورودی‌ای نداد
MIN_PER_REMINDER = 2     # یادآوری‌ای که مالک «انجام شد» زد
MIN_PER_CAPTURE = 3      # ثبتِ خودکارِ یک نوت در vault
# نشانِ دخالتِ مالک — عینِ رشته‌ای که `leg_tasks.resolve_blocked` می‌نویسد.
# تغییرِ آن‌جا باید این‌جا را هم عوض کند (تستِ round-trip قفلش می‌کند).
_OWNER_INPUT_MARK = "➕ اطلاعات مالک:"


def _engine_tasks_week(now: float) -> "int | None":
    """کارهای تمام‌شدهٔ هفته که **هیچ ورودیِ مالک** نداشتند. هیچ فایلِ کاری
    وجود نداشت ⇒ None (نه صفر — «نبود» با «صفر» یکی نیست)."""
    lt = _leg_tasks()
    if lt is None:
        return None
    week0 = float(now) - WEEK_S
    seen_any = False
    n = 0
    for leg in BUSINESS_LEGS:
        try:
            if not lt._path(leg).exists():
                continue
            seen_any = True
            rows = lt.recent_done(leg, 200)
        except Exception:  # noqa: BLE001
            continue
        for t in rows:
            try:
                upd = float(t.get("updated") or 0)
            except (TypeError, ValueError):
                continue
            if upd < week0 or upd > float(now):
                continue
            if t.get("result") == "لغو شد":
                continue
            if _OWNER_INPUT_MARK in str(t.get("text") or ""):
                continue                 # مالک وسطِ کار اطلاعات داد ⇒ آزاد نشد
            n += 1
    return n if seen_any else None


# نامِ فایلِ capture طبق §۵ منشورِ vault: `YYYY-MM-DD HHmm <slug>.md` —
# دقیقاً همان چیزی که `capture.file_to_vault` می‌سازد (خواننده به نویسنده pin).
_CAPTURE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2}) \d{4} ")


def _captures_filed_week(vault_root, now: float) -> "int | None":
    """نوت‌های خودکارِ بایگانی‌شدهٔ هفته در «10 - Telegram processing/Raw»."""
    try:
        root_s = str(vault_root or os.environ.get("ORG_ROOT", "") or "").strip()
        if not root_s:
            return None
        raw = Path(root_s) / "10 - Telegram processing" / "Raw"
        if not raw.is_dir():
            return None
        since = float(now) - WEEK_S
        n = 0
        for p in raw.rglob("*.md"):
            m = _CAPTURE_NAME.match(p.name)
            if not m:
                continue
            try:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d").timestamp()
            except ValueError:
                continue
            if since <= ts <= float(now):
                n += 1
        return n
    except OSError:
        return None


def hours_freed(now: float, *, quality: "dict | None" = None) -> "dict | None":
    """تخمینِ ساعتِ آزادشده + اجزای فرمول. هیچ جزئی داده نداشت ⇒ None."""
    tasks = _engine_tasks_week(now)
    caps = _captures_filed_week(None, now)
    q = quality if quality is not None else _reminder_quality(now)
    done = q.get("done") if isinstance(q, dict) else None
    parts = [tasks, done, caps]
    if all(v is None for v in parts):
        return None                      # هیچ منبعی روی دیسک نیست
    t, d, c = (int(v or 0) for v in parts)
    minutes = t * MIN_PER_TASK + d * MIN_PER_REMINDER + c * MIN_PER_CAPTURE
    if minutes <= 0:
        return None                      # صفرِ خالی خط نمی‌گیرد
    return {"tasks": t, "reminders_done": d, "captures": c,
            "minutes": minutes, "hours": round(minutes / 60.0, 1)}


# ── هزینه‌های ثبت‌شدهٔ مالک (BLOCKER 2 — خواننده و نویسنده با هم) ─────────
# نویسنده: capture.route (شاخهٔ expense) دقیقاً این سطر را append می‌کند:
#   ``- YYYY-MM-DD هزینه: <خلاصه>``
# این regex عمداً به همان قرارداد pin است — تغییرِ فرمتِ capture باید هر دو
# را با هم عوض کند (تستِ round-trip همین را قفل می‌کند).
_EXPENSE_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) هزینه: (.+)$")


def _owner_expenses_week(vault_root, now: float) -> "list | None":
    """سطرهای هزینهٔ هفتهٔ مرور از نوت‌های «10 - Telegram processing/Raw».

    فقط‌خواندنی و fail-soft: ریشه از پارامتر یا env ORG_ROOT (harness-safe)؛
    نبودِ ریشه/پوشه یا هر خطا ⇒ None (غیابِ صادقانه، هرگز crash/عددسازی).
    خروجی: [(date_str, متن)] مرتب به تاریخ."""
    try:
        root_s = str(vault_root or os.environ.get("ORG_ROOT", "") or "").strip()
        if not root_s:
            return None
        raw = Path(root_s) / "10 - Telegram processing" / "Raw"
        if not raw.is_dir():
            return None
        since = float(now) - WEEK_S
        out = []
        for p in raw.rglob("*.md"):
            try:
                body = p.read_text("utf-8", errors="ignore")
            except OSError:
                continue
            for line in body.splitlines():
                m = _EXPENSE_LINE.match(line)
                if not m:
                    continue
                try:
                    ts = datetime.strptime(m.group(1), "%Y-%m-%d").timestamp()
                except ValueError:
                    continue
                if since <= ts <= float(now):
                    out.append((m.group(1), m.group(2).strip()))
        out.sort()
        return out
    except Exception:  # noqa: BLE001 — بخشِ هزینه هرگز مرور را نمی‌کشد
        return None


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
    # (بازبینی ۰۷-۳۱، BLOCKER 2c) برچسبِ صادق: این عدد از budget/telemetry
    # می‌آید — هزینهٔ LLM ِ خودِ ارگانیسم است، نه پولِ مالک/بیزنس.
    lines.append("💰 خرجِ خودِ اختاپوس (LLM) این ماه: "
                 + (f"AU${_fa(round(aud, 2))}" if aud is not None else NO_DATA))

    # (بازبینی ۰۷-۳۱، BLOCKER 2a) هزینه‌های ثبت‌شدهٔ خودِ مالک — از سطرهایی
    # که capture در نوت‌های Raw نوشته؛ نبودِ داده = غیابِ صادقانه.
    lines.append("🧾 هزینه‌های ثبت‌شدهٔ هفته:")
    exps = _owner_expenses_week(None, now)
    if exps:
        lines.append(f"· {_fa(len(exps))} هزینه ثبت شده")
        for day, what in exps[:5]:
            lines.append(f"  – {_fa(day)} · {what[:60]}")
    else:
        lines.append("· هیچ هزینه‌ای ثبت نشده")

    slog = _send_log_week()
    lines.append("🤖 خودکارهای هفته: "
                 + (f"{_fa(slog['sends'])} ارسال" if slog else NO_DATA))

    lines += ["", "📏 <b>سنجه‌ها (§۹)</b>"]
    # کیفیتِ یادآوری، نه فقط شمارِ شلیک (§۹ «به‌موقع/مفید»). شکلِ store اجازهٔ
    # بیش از این نمی‌دهد و متن همین را اعلام می‌کند («وضعِ فعلی»).
    qual = _reminder_quality(now)
    if qual is None:
        lines.append(f"· یادآوری‌ها: {NO_DATA}")
    elif not qual["fired"]:
        lines.append("· یادآوری‌ها: این هفته هیچ یادآوری‌ای شلیک نشد")
    else:
        lines.append(f"· یادآوری‌ها: {_fa(qual['fired'])} شلیک · "
                     f"{_fa(qual['done'])} انجام‌شده · "
                     f"{_fa(qual['snoozed'])} بعداً · "
                     f"{_fa(qual['open'])} بی‌پاسخ (وضعِ فعلی)")

    # ساعتِ آزادشده — **تخمین**، و فرمولش همیشه کنارش. داده نبود ⇒ عدد نه.
    hf = hours_freed(now, quality=qual)
    if hf is None:
        lines.append(f"· ساعتِ آزادشدهٔ تو: {NO_DATA}")
    else:
        lines.append(f"· ساعتِ آزادشدهٔ تو (تخمین): ~{_fa(hf['hours'])} ساعت")
        lines.append(f"  فرمول: ({_fa(hf['tasks'])} کارِ بی‌دخالتِ تو × "
                     f"{_fa(MIN_PER_TASK)}د) + ({_fa(hf['reminders_done'])} "
                     f"یادآوریِ انجام‌شده × {_fa(MIN_PER_REMINDER)}د) + "
                     f"({_fa(hf['captures'])} ثبتِ خودکار × "
                     f"{_fa(MIN_PER_CAPTURE)}د) = {_fa(hf['minutes'])} دقیقه")

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
