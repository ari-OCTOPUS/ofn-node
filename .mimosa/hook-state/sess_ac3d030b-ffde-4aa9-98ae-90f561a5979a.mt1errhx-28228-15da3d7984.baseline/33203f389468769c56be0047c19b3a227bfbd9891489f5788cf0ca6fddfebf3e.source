#!/usr/bin/env python3
"""wlos_bridge.py — سیگنالِ sanitizedِ WLOS برای مغز اصلی (flag-off).

دستور مالک 2026-07-20: «WLOS را بده دست مغز اصلی برای تعامل و شناخت با من.»
WLOS (کوچ کاهش وزن، `03 - Projects/WLOS - Weight Loss OS/wlos/`) یک سیستم
جدا با DB جداست و هنوز live نشده. «الحاق» امن یعنی: مغز فقط یک خلاصهٔ
whitelist شده و بدون هویت را می‌خواند که WLOS (job هفتگی‌اش) یا خود مالک در
`state/wlos/owner-summary.json` می‌گذارد. OCTOPUS هرگز در آن نمی‌نویسد و
هرگز به DB سلامت وصل نمی‌شود.

مرز حریم خصوصی (سفت): دادهٔ دستهٔ ویژهٔ سلامت هرگز وارد چت/نوت/HANDOFF/لاگ
نمی‌شود؛ این ماژول فقط فیلدهای عددی/enum کوتاه + یک نوتِ scrub شده (≤140)
برمی‌گرداند. هر چیز خارج از whitelist حذف می‌شود.

flag: OCTOPUS_WIRE_WLOS (پیش‌فرض خاموش؛ خواندن strip-safe). read-only، $0.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

_FLAG = "OCTOPUS_WIRE_WLOS"
REL_PATH = ("wlos", "owner-summary.json")

_TREND = {"down", "flat", "up", "unknown"}
# نوت: ایمیل/URL/رشته‌های عددی بلند (تلفن و…) حذف می‌شوند
_SCRUB = (
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), " "),
    (re.compile(r"https?://\S+"), " "),
    (re.compile(r"\d{5,}"), " "),
    (re.compile(r"\s+"), " "),
)


def _flag_on() -> bool:
    return os.environ.get(_FLAG, "0").strip() == "1"


def _state_dir(state_dir=None) -> Path:
    if state_dir:
        return Path(state_dir)
    env = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "state"


def _clamp_num(v, lo, hi):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return max(lo, min(hi, f))


def _scrub_note(v) -> str:
    s = str(v or "")
    for rx, rep in _SCRUB:
        s = rx.sub(rep, s)
    return s.strip()[:140]


def read_owner_signal(state_dir=None) -> dict:
    """خلاصهٔ whitelist شدهٔ WLOS یا {}. هرگز raise نمی‌کند.

    قرارداد خروجی (فقط همین کلیدها، همه اختیاری):
      week (str≤10) · weight_trend (down|flat|up|unknown) ·
      adherence_pct (0..100) · checkins_done (0..100) · energy_avg (0..10) ·
      flags (تا ۵ برچسب کوتاهِ [a-z0-9-]) · note (≤140، scrub شده)
    """
    try:
        if not _flag_on():
            return {}
        p = _state_dir(state_dir).joinpath(*REL_PATH)
        if not p.exists():
            return {}
        raw = json.loads(p.read_text("utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: dict = {}
        week = str(raw.get("week") or "").strip()[:10]
        if week:
            out["week"] = week
        trend = str(raw.get("weight_trend") or "").strip().lower()
        if trend in _TREND:
            out["weight_trend"] = trend
        for key, lo, hi in (("adherence_pct", 0, 100),
                            ("checkins_done", 0, 100),
                            ("energy_avg", 0, 10)):
            n = _clamp_num(raw.get(key), lo, hi)
            if n is not None:
                out[key] = round(n, 1)
        flags = []
        for f in (raw.get("flags") or [])[:5]:
            t = re.sub(r"[^a-z0-9\-]", "", str(f).strip().lower())[:24]
            if t:
                flags.append(t)
        if flags:
            out["flags"] = flags
        note = _scrub_note(raw.get("note"))
        if note:
            out["note"] = note
        return out
    except Exception:  # noqa: BLE001
        return {}
