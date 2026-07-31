#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reminders — موتورِ یادآوریِ زبانِ طبیعی (منشور رأی‌های ۵–۸؛ لِین E).

    «فکر کن من حافظه ندارم — باید همه‌چیز را یادم بیندازد.»

مرزها (الگوی leg_tasks):
  · این ماژول **هیچ‌چیز نمی‌فرستد** — شلیک با callback ِ تزریقی
    (send_dm_fn / send_leg_fn) است که مرکز هنگامِ سیم‌کشی می‌دهد.
  · ساعت تزریقی است (now=) — هیچ time.time() در مسیرِ تصمیم.
  · state در `OCTOPUS_STATE_DIR/reminders/` (env-اول، بعد opslib.STATE_DIR)
    — harness ِ تست‌ها خودکار ایزوله‌اش می‌کند.
  · سکوتِ شب (رأی ۸ — شروعِ محافظه‌کار ۲۳–۷): در پنجره فقط بحرانی/فوری
    شلیک می‌شود؛ بقیه **دور ریخته نمی‌شوند** — می‌مانند و سرِ پایانِ پنجره
    (۰۷:۰۰) با اولین ضربان می‌رسند.
  · parser فقط stdlib و کاملاً قطعی است؛ نفهمید ⇒ (None, متنِ دست‌نخورده).

فلگ: OCTOPUS_TG_REMINDERS (پیش‌فرض خاموش؛ گیتِ مصرف در مرکز است نه این‌جا).
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent

FLAG = "OCTOPUS_TG_REMINDERS"

_CAP = 500                                    # سقفِ آیتم‌های نگه‌داشته
_FA2EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_EN2FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# نشانِ بحرانی — تنها چیزی که از پنجرهٔ سکوت رد می‌شود (رأی ۸).
_CRITICAL = re.compile(r"بحرانی|فوری")

DEFAULT_CONFIG = {"quiet_from": 23, "quiet_to": 7,
                  "brief_hour": 7.5, "wrap_hour": 21.5}


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def is_critical(text: str) -> bool:
    return bool(_CRITICAL.search(str(text or "")))


def _fa(n) -> str:
    return str(n).translate(_EN2FA)


def _esc(s: str) -> str:
    return (str(s or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


# ── مسیرها ─────────────────────────────────────────────────────────────────
def _dir() -> Path:
    env = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if env:
        return Path(env) / "reminders"
    try:
        import sys as _s
        for p in (str(_HERE.parent), str(_HERE.parent / "budget")):
            if p not in _s.path:
                _s.path.insert(0, p)
        import opslib
        return Path(opslib.STATE_DIR) / "reminders"
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state" / "reminders"


def _file() -> Path:
    return _dir() / "reminders.json"


def _cfg_file() -> Path:
    return _dir() / "config.json"


def _load() -> dict:
    try:
        d = json.loads(_file().read_text("utf-8"))
        if isinstance(d, dict) and isinstance(d.get("items"), list):
            return d
    except (OSError, ValueError):
        pass
    return {"seq": 0, "items": []}


def _save(d: dict) -> bool:
    try:
        p = _file()
        p.parent.mkdir(parents=True, exist_ok=True)
        d["items"] = d.get("items", [])[-_CAP:]
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


def load_config() -> dict:
    """تنظیمِ سکوت/بریف — نبود ⇒ پیش‌فرضِ محافظه‌کار نوشته می‌شود تا مالک
    بتواند دستی ویرایش کند (خودتنظیمیِ تطبیقی، فازِ بعد)."""
    cfg = dict(DEFAULT_CONFIG)
    p = _cfg_file()
    try:
        d = json.loads(p.read_text("utf-8"))
        if isinstance(d, dict):
            cfg.update(d)
            return cfg
    except (OSError, ValueError):
        pass
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
    except OSError:
        pass
    return cfg


# ── parser ِ زمانِ فارسی (خالص، قطعی، stdlib) ─────────────────────────────
_WD_BASE = {"شنبه": 5, "یکشنبه": 6, "دوشنبه": 0, "سهشنبه": 1,
            "چهارشنبه": 2, "پنجشنبه": 3, "جمعه": 4}       # کلیدِ نرمال‌شده

_WD_FORMS = ["شنبه", "یکشنبه", "یک‌شنبه", "یک شنبه", "دوشنبه", "دو‌شنبه",
             "سه‌شنبه", "سهشنبه", "سه شنبه", "چهارشنبه", "چهار‌شنبه",
             "چهار شنبه", "پنجشنبه", "پنج‌شنبه", "پنج شنبه", "جمعه"]

_B = r"(?<![\w‌])"                       # مرزِ واژه که ZWNJ را هم می‌شناسد
_E = r"(?![\w‌])"

_REL = re.compile(r"(\d+)\s*(دقیقه|ساعت|روز)\s*(دیگه|دیگر|بعد)" + _E)
_DAY = re.compile(_B + r"(پس[\s‌]?فردا|فردا|امروز)" + _E)
_WD = re.compile(_B + "(" + "|".join(
    sorted(_WD_FORMS, key=len, reverse=True)) + ")" + _E)
_TIME = re.compile(r"ساعت\s*(\d{1,2})(?::(\d{2}))?"
                   r"(?:\s*(صبح|ظهر|بعد\s*از\s*ظهر|بعدازظهر|عصر|شب))?")
_BARE = re.compile(_B + r"(صبح|شب)" + _E)


def _adjust(h: int, marker) -> int:
    """ابهامِ ۱۲ساعته با نشانهٔ فارسی حل می‌شود؛ بی‌نشانه = همان ۲۴ساعته."""
    if not marker:
        return h
    m = re.sub(r"[\s‌]", "", marker)
    if m == "صبح":
        return 0 if h == 12 else h
    if m == "ظهر":
        return h + 12 if 1 <= h <= 4 else h
    if m in ("عصر", "بعدازظهر"):
        return h + 12 if h < 12 else h
    if m == "شب":
        if h == 12:
            return 0
        return h + 12 if h < 12 else h
    return h


def _clean(original: str, spans: list) -> str:
    out, prev = [], 0
    for a, b in sorted(spans):
        out.append(original[prev:a])
        prev = b
    out.append(original[prev:])
    return re.sub(r"\s+", " ", "".join(out)).strip(" ‌،:—-")


def parse_when(text: str, *, now: float):
    """(due_ts | None, cleaned_text) — فهمِ زمانِ فارسیِ مالک، بدونِ حدس.

    می‌فهمد: امروز/فردا/پس‌فردا · نامِ روزِ هفته (وقوعِ بعدی؛ همان روز ⇒ هفتهٔ
    بعد) · «ساعت N[:MM]» ‏۲۴ساعته با ابهام‌زدای صبح/ظهر/عصر/شب · «N دقیقه/ساعت/
    روز دیگه» · «صبح»=۰۸:۰۰ و «شب»=۲۱:۰۰ ِ تنها · رقمِ فارسی. ساعتِ بدونِ روز
    که گذشته باشد ⇒ فردا. هیچ‌کدام ⇒ (None, متن)."""
    original = str(text or "")
    src = original.translate(_FA2EN)           # طول ثابت می‌ماند ⇒ span معتبر
    base = datetime.fromtimestamp(float(now))
    spans: list = []

    m = _REL.search(src)
    if m:
        n = int(m.group(1))
        unit = {"دقیقه": 60, "ساعت": 3600, "روز": 86400}[m.group(2)]
        spans.append(m.span())
        return float(now) + n * unit, _clean(original, spans)

    day_off = None
    m = _DAY.search(src)
    if m:
        w = re.sub(r"[\s‌]", "", m.group(1))
        day_off = {"امروز": 0, "فردا": 1, "پسفردا": 2}[w]
        spans.append(m.span())
    else:
        m = _WD.search(src)
        if m:
            wd = _WD_BASE[re.sub(r"[\s‌]", "", m.group(1))]
            day_off = (wd - base.weekday()) % 7 or 7
            spans.append(m.span())

    hh = mm = None
    m = _TIME.search(src)
    if m:
        h, mnt = int(m.group(1)), int(m.group(2) or 0)
        if h <= 23 and mnt <= 59:
            hh, mm = _adjust(h, m.group(3)), mnt
            spans.append(m.span())
    if hh is None:
        m = _BARE.search(src)
        if m:
            hh, mm = (8, 0) if m.group(1) == "صبح" else (21, 0)
            spans.append(m.span())

    if day_off is None and hh is None:
        return None, original
    if hh is None:
        hh, mm = 8, 0                           # روزِ بی‌ساعت = صبح
    target = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if day_off is not None:
        target += timedelta(days=day_off)
    elif target.timestamp() <= float(now):
        target += timedelta(days=1)             # ساعتِ گذشته ⇒ فردا
    return target.timestamp(), _clean(original, spans)


# ── چرخهٔ عمرِ یادآوری ─────────────────────────────────────────────────────
def add(text: str, *, due_ts, scope: str = "dm", leg=None,
        now: float | None = None) -> "dict | None":
    if due_ts is None:
        return None
    now = float(now if now is not None else time.time())
    body = str(text or "").strip()[:300]
    if not body:
        return None
    d = _load()
    d["seq"] = int(d.get("seq", 0)) + 1
    it = {"id": f"RM-{d['seq']}", "text": body, "due": float(due_ts),
          "scope": scope if scope in ("dm", "leg") else "dm",
          "leg": (str(leg) if leg else None),
          "created": now, "done": False, "fired": False}
    d["items"].append(it)
    return dict(it) if _save(d) else None


def _find(d: dict, rid: str) -> "dict | None":
    for it in d.get("items", []):
        if it.get("id") == rid:
            return it
    return None


def list_open(now: float | None = None) -> list:
    return [dict(it) for it in _load().get("items", []) if not it.get("done")]


def mark_fired(rid: str) -> "dict | None":
    d = _load()
    it = _find(d, rid)
    if it is None:
        return None
    it["fired"] = True
    return dict(it) if _save(d) else None


def done(rid: str) -> "dict | None":
    d = _load()
    it = _find(d, rid)
    if it is None:
        return None
    it["done"] = True
    return dict(it) if _save(d) else None


def snooze(rid: str, plus_s: float, now: float | None = None) -> "dict | None":
    """«بعداً» — از الان (یا از موعد اگر هنوز نیامده) جلوتر می‌رود و دوباره
    قابلِ شلیک می‌شود. دبل-تاپ بی‌ضرر: فقط جلوتر می‌بَرد."""
    now = float(now if now is not None else time.time())
    d = _load()
    it = _find(d, rid)
    if it is None or it.get("done"):
        return None
    it["due"] = max(float(it.get("due") or 0), now) + float(plus_s)
    it["fired"] = False
    return dict(it) if _save(d) else None


# ── رندر (متن، نه ارسال) ───────────────────────────────────────────────────
def fire_text(it: dict) -> str:
    return f"⏰ یادآوری: {_esc(it.get('text') or '')}"


def reminder_keyboard(rid: str) -> list:
    """دکمه‌های DM — dispatch با مرکز است (rm:done / rm:snz)."""
    return [[{"text": "✅ انجام شد", "callback_data": f"rm:done:{rid}"[:64]},
             {"text": "⏰ نیم ساعت بعد", "callback_data": f"rm:snz:{rid}"[:64]}]]


# ── ضربان ──────────────────────────────────────────────────────────────────
def _in_quiet(now: float, cfg: dict) -> bool:
    dt = datetime.fromtimestamp(float(now))
    h = dt.hour + dt.minute / 60.0
    a = float(cfg.get("quiet_from", 23))
    b = float(cfg.get("quiet_to", 7))
    if a == b:
        return False
    if a < b:
        return a <= h < b
    return h >= a or h < b


def beat(*, now: float, send_dm_fn, send_leg_fn) -> int:
    """موعدرسیده‌های شلیک‌نشده را برسان — سوار بر beat ِ موجودِ مرکز.

    dm ⇒ send_dm_fn(text, reminder_id) — مرکز کیبوردِ ✅ را از
    reminder_keyboard می‌سازد؛ leg ⇒ send_leg_fn(leg, text).
    پنجرهٔ سکوت: فقط بحرانی/فوری؛ بقیه می‌مانند و سرِ ۰۷:۰۰ می‌رسند.
    ارسالِ ناموفق (استثنا) ⇒ fired نمی‌شود؛ ضربانِ بعد دوباره می‌کوشد."""
    cfg = load_config()
    quiet = _in_quiet(now, cfg)
    d = _load()
    fired, changed = 0, False
    for it in d.get("items", []):
        if it.get("done") or it.get("fired"):
            continue
        if float(it.get("due") or 0) > float(now):
            continue
        if quiet and not is_critical(it.get("text")):
            continue                            # معوق، نه حذف
        try:
            if it.get("scope") == "leg" and it.get("leg"):
                send_leg_fn(it["leg"], fire_text(it))
            else:
                send_dm_fn(fire_text(it), it["id"])
        except Exception:  # noqa: BLE001
            continue
        it["fired"] = True
        fired += 1
        changed = True
    if changed:
        _save(d)
    return fired
