#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brief — بریفِ صبح و جمع‌بندیِ شب (منشور رأی‌های ۵ و ۱۱؛ لِین E).

    بریفِ صبح: ۳ کارِ مهمِ امروز + یک‌خطیِ هر بیزنس با لینکِ تاپیکش —
    جزئیاتِ بیزنس در گروه می‌ماند. بدونِ شلوغی.

مرزها (الگوی leg_tasks):
  · این ماژول **هیچ‌چیز نمی‌فرستد** — فقط متن می‌سازد؛ ارسال با callback ِ
    تزریقیِ beat است (send_dm_fn از مرکز).
  · ساعت تزریقی (now=)؛ cursor ِ یک‌بار-در-روز در dict ِ caller می‌مانَد
    (الگوی last_pulse ِ مرکز) — persist با caller است.
  · حقیقتِ داده از leg_tasks (store ِ هر پا) و reminders؛ هیچ I/O ِ تلگرام.
  · HTML parse-mode ِ امن، رقمِ فارسی، ایزولهٔ bidi ‏U+2066…U+2069 دورِ
    تکه‌های LTR (لینک‌ها) — قاعدهٔ UX ۹ منشور.

فلگ: OCTOPUS_TG_BRIEF (پیش‌فرض خاموش؛ گیتِ مصرف در مرکز است نه این‌جا).
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import leg_tasks  # noqa: E402

FLAG = "OCTOPUS_TG_BRIEF"

_EN2FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_ICONS = ("🚧", "⏳", "⏰", "▫")                 # ترتیبِ اهمیتِ خطوطِ کار


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _fa(n) -> str:
    return str(n).translate(_EN2FA)


def _esc(s: str) -> str:
    return (str(s or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def _iso(ltr: str) -> str:
    """ایزولهٔ bidi دورِ تکهٔ LTR — لینکِ لاتین وسطِ سطرِ فارسی نمی‌شکند."""
    return "⁦" + ltr + "⁩"


def _rem():
    try:
        import reminders
        return reminders
    except Exception:  # noqa: BLE001
        return None


def _hours() -> dict:
    rm = _rem()
    if rm is not None:
        try:
            return rm.load_config()
        except Exception:  # noqa: BLE001
            pass
    return {"brief_hour": 7.5, "wrap_hour": 21.5}


# ── لینکِ تاپیک (کانونی — جای دیگری در repo وجود ندارد) ────────────────────
def topic_link(chat_id, topic_id) -> str:
    """https://t.me/c/<chat بدونِ پیشوندِ ‎-100‎>/<topic> — سوپرگروهِ خصوصی.

    قاعدهٔ تلگرام: شناسهٔ داخلیِ سوپرگروه = chat_id منهای پیشوندِ -100؛
    اگر -100 نبود، قدرِ مطلق."""
    s = str(chat_id).strip()
    if s.startswith("-100"):
        s = s[4:]
    elif s.startswith("-"):
        s = s[1:]
    return f"https://t.me/c/{s}/{int(topic_id)}"


# ── دادهٔ مشترک ────────────────────────────────────────────────────────────
def _name(cfg: dict, leg: str) -> str:
    return str((cfg.get("display_names") or {}).get(leg) or leg)


def _gather(cfg: dict) -> dict:
    """queue ِ هر پایی که در config تاپیک دارد (= پاهای قراردادِ گروه)."""
    return {leg: leg_tasks.queue(leg) for leg in (cfg.get("topics") or {})}


def _reminders_today(rm, now: float):
    """(یادآوری‌های امروزِ هنوز-نرسانده، شمارِ کلِ باز)."""
    if rm is None:
        return [], 0
    try:
        items = rm.list_open(now=now)
    except Exception:  # noqa: BLE001
        return [], 0
    d0 = datetime.fromtimestamp(float(now))
    day_end = datetime(d0.year, d0.month, d0.day).timestamp() + 86400
    today = [r for r in items
             if float(r.get("due") or 0) <= day_end and not r.get("fired")]
    return today, len(items)


# ── بریفِ صبح ──────────────────────────────────────────────────────────────
def morning_text(*, now: float, cfg: dict, reminders_mod=None) -> str:
    """«☀️ بریف صبح» — دقیقاً قالبِ منشور (رأی ۱۱):
    ۳ کارِ مهم (BLOCKED اول، بعد WORKING، بعد یادآوری‌های امروز، بعد قدیمی‌ترین
    QUEUED) + یک‌خطیِ هر بیزنسِ ناخالی با لینکِ تاپیک + شمارِ یادآوری‌های باز."""
    now = float(now)
    rm = reminders_mod if reminders_mod is not None else _rem()
    per_leg = _gather(cfg)
    chat_id = cfg.get("chat_id")

    blocked, working, queued = [], [], []
    for leg, q in per_leg.items():
        for t in q:
            st = t.get("state")
            if st == leg_tasks.BLOCKED:
                blocked.append((leg, t))
            elif st == leg_tasks.WORKING:
                working.append((leg, t))
            elif st == leg_tasks.QUEUED:
                queued.append((leg, t))
    queued.sort(key=lambda x: float(x[1].get("created", 0) or 0))
    rem_today, open_count = _reminders_today(rm, now)

    cands = (
        [("🚧", leg, t.get("question") or t.get("text") or "")
         for leg, t in blocked] +
        [("⏳", leg, t.get("text") or "") for leg, t in working] +
        [("⏰", None, r.get("text") or "") for r in rem_today] +
        [("▫️", leg, t.get("text") or "") for leg, t in queued])

    lines = ["☀️ <b>بریف صبح</b>", ""]
    top = cands[:3]
    if top:
        lines.append("کارهای مهم امروز:")
        for icon, leg, txt in top:
            tag = f"[{_name(cfg, leg)}] " if leg else ""
            lines.append(f"{icon} {tag}{_esc(str(txt)[:70])}")
    else:
        lines.append("کارِ فوری‌ای ثبت نشده — روزِ سبک.")

    biz = []
    for leg, topic in (cfg.get("topics") or {}).items():
        q = per_leg.get(leg) or []
        last = leg_tasks.recent_done(leg, 1)
        if not q and not last:
            continue                            # پای خالی = سکوت (بدونِ شلوغی)
        nb = sum(1 for t in q if t.get("state") == leg_tasks.BLOCKED)
        nw = sum(1 for t in q if t.get("state") == leg_tasks.WORKING)
        nq = sum(1 for t in q if t.get("state") == leg_tasks.QUEUED)
        bits = []
        if nw:
            bits.append(f"{_fa(nw)} در کار")
        if nb:
            bits.append(f"{_fa(nb)} مسدود")
        if nq:
            bits.append(f"{_fa(nq)} در صف")
        res = (last[0].get("result") or "").strip() if last else ""
        tail = f" · آخرین: {_esc(res[:40])}" if res and res != "لغو شد" else ""
        link = ""
        if chat_id and topic:
            link = " " + _iso(topic_link(chat_id, topic))
        biz.append(f"· {_name(cfg, leg)}: "
                   f"{('، '.join(bits) or 'بی‌کارِ باز')}{tail}{link}")
    if biz:
        lines += ["", "بیزنس‌ها:"] + biz

    lines += ["", f"یادآوری‌های باز: {_fa(open_count)}"]
    return "\n".join(lines)


# ── جمع‌بندیِ شب ───────────────────────────────────────────────────────────
def evening_text(*, now: float, cfg: dict) -> str:
    """«🌙 جمع‌بندی شب» — چه تمام شد (۲۴ ساعت)، چه مسدود ماند، فردا اول چه."""
    now = float(now)
    day0 = now - 86400
    done_lines, blocked_lines, tomorrow = [], [], []
    for leg in (cfg.get("topics") or {}):
        dones = [t for t in leg_tasks.recent_done(leg, 5)
                 if float(t.get("updated", 0) or 0) >= day0
                 and t.get("result") != "لغو شد"]
        if dones:
            res = (dones[0].get("result") or dones[0].get("text") or "—")[:60]
            done_lines.append(
                f"✅ {_name(cfg, leg)}: {_fa(len(dones))} تمام شد · {_esc(res)}")
        for t in leg_tasks.queue(leg):
            st = t.get("state")
            if st == leg_tasks.BLOCKED:
                q = (t.get("question") or t.get("text") or "")[:60]
                blocked_lines.append(f"🚧 {_name(cfg, leg)}: {_esc(q)}")
            elif st == leg_tasks.QUEUED:
                tomorrow.append((float(t.get("created", 0) or 0), leg, t))

    lines = ["🌙 <b>جمع‌بندی شب</b>", ""]
    if done_lines:
        lines += done_lines
    else:
        lines.append("امروز کاری تمام نشد.")
    if blocked_lines:
        lines += ["", "مسدود ماند:"] + blocked_lines[:5]
    tomorrow.sort(key=lambda x: x[0])
    if tomorrow:
        lines += ["", "فردا اول این‌ها:"]
        for _c, leg, t in tomorrow[:3]:
            lines.append(f"▫️ [{_name(cfg, leg)}] "
                         f"{_esc(str(t.get('text') or '')[:70])}")
    return "\n".join(lines)


# ── ضربان (یک‌بار در روز، الگوی last_pulse) ────────────────────────────────
def beat(*, now: float, cfg: dict, send_dm_fn, state: dict) -> "str | None":
    """صبح در brief_hour و شب در wrap_hour — هر کدام یک‌بار در روز.

    قراردادِ cursor: این تابع فقط `state["last_morning_day"]` و
    `state["last_evening_day"]` (رشتهٔ YYYY-MM-DD محلی) را می‌خوانَد/می‌نویسد؛
    **persist ِ state با caller است** (مرکز آن را داخلِ همان center-config
    نگه می‌دارد، الگوی last_pulse). صبحِ جامانده تا قبلِ wrap_hour جبران
    می‌شود؛ بعد از آن دیگر صبح نمی‌فرستیم (شب کافی است).
    خروجی: متنِ فرستاده‌شده یا None."""
    now = float(now)
    hours = _hours()
    dt = datetime.fromtimestamp(now)
    h = dt.hour + dt.minute / 60.0
    day = dt.strftime("%Y-%m-%d")
    brief_h = float(hours.get("brief_hour", 7.5))
    wrap_h = float(hours.get("wrap_hour", 21.5))

    if brief_h <= h < wrap_h and state.get("last_morning_day") != day:
        txt = morning_text(now=now, cfg=cfg)
        send_dm_fn(txt)
        state["last_morning_day"] = day
        return txt
    if h >= wrap_h and state.get("last_evening_day") != day:
        txt = evening_text(now=now, cfg=cfg)
        send_dm_fn(txt)
        state["last_evening_day"] = day
        return txt
    return None
