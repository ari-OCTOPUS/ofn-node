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
  · **سکوتِ تطبیقی** (رأی ۸ ِ کامل، ۲۰۲۶-۰۷-۳۱): پنجره دیگر ثابت نیست —
    `learn()` از دادهٔ موجود (مهرِ fired/done ِ همین store + ردیف‌های DM ِ
    `tg-send-log.jsonl`) می‌سنجد مالک در هر ساعت **چقدر سریع** و **چند بار**
    عمل می‌کند. بخشِ «§ سکوتِ تطبیقی» پایین را ببین.
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
def _state_root() -> Path:
    """ریشهٔ state (env-اول) — `reminders/` و `tg-send-log.jsonl` هر دو زیرِ
    همین‌اند؛ یک منبع، نه دو حقیقت."""
    env = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if env:
        return Path(env)
    try:
        import sys as _s
        for p in (str(_HERE.parent), str(_HERE.parent / "budget")):
            if p not in _s.path:
                _s.path.insert(0, p)
        import opslib
        return Path(opslib.STATE_DIR)
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state"


def _dir() -> Path:
    return _state_root() / "reminders"


def _send_log_path() -> Path:
    return _state_root() / "tg-send-log.jsonl"


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


def mark_fired(rid: str, *, now: float | None = None) -> "dict | None":
    """شلیک‌شده + مهرِ زمانِ ``fired_ts`` (بازبینی ۰۷-۳۱، BLOCKER 3):
    سنجهٔ هفتگیِ weekly_review فقط fired ِ مهر‌دارِ داخلِ پنجره را می‌شمارد —
    fired ِ بی‌تاریخ قابلِ‌شمارش در «این هفته» نیست. ساعت تزریق‌پذیر."""
    d = _load()
    it = _find(d, rid)
    if it is None:
        return None
    it["fired"] = True
    it["fired_ts"] = float(now if now is not None else time.time())
    return dict(it) if _save(d) else None


def done(rid: str, *, now: "float | None" = None) -> "dict | None":
    """✅ مالک — با مهرِ زمان `done_ts` (۲۰۲۶-۰۷-۳۱).

    چرا مهر لازم شد: سکوتِ تطبیقی «چقدر سریع عمل می‌کند» را از
    `done_ts - fired_ts` می‌سنجد. تا امروز فقط `done: True` ذخیره می‌شد، پس
    تأخیرِ عمل **قابلِ سنجش نبود** و هر یادگیری‌ای روی آن، حدس بود.
    آیتم‌های قدیمیِ بی‌مهر از نمونه‌گیری کنار گذاشته می‌شوند — «غیرقابلِ سنجش»
    شاهدِ کندی نیست. صداکنندهٔ فعلی (`center._handle_reminder_callback`)
    موقعیتی صدا می‌زند: `now` کلیدواژه‌ای و اختیاری ماند تا امضا نشکند."""
    d = _load()
    it = _find(d, rid)
    if it is None:
        return None
    it["done"] = True
    it["done_ts"] = float(now if now is not None else time.time())
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


# ══ § سکوتِ تطبیقی (رأی ۶ «تدریجی شخصی‌سازی» + رأی ۸ «بعد خودتنظیم») ══════
#
# قاعده‌های سختِ این یادگیرنده — همه از سرِ محافظه‌کاری، نه دقتِ آماری:
#   ۱. بدونِ ≥MIN_SAMPLES نمونهٔ **سنجیده‌شده** هیچ حرکتی نمی‌کند.
#   ۲. دربارهٔ ساعتی که کمتر از MIN_HOUR_SAMPLES فایر دیده، **حکم نمی‌دهد** —
#      ساعتِ ناشناخته وضعِ فعلی‌اش را نگه می‌دارد (نه بیدار، نه ساکت).
#   ۳. پنجرهٔ سکوت هرگز کوتاه‌تر از QUIET_FLOOR_H و بلندتر از QUIET_MAX_H
#      نمی‌شود؛ نامعتبر ⇒ **حرکت نمی‌کند** (نه اینکه به‌زور clamp کند).
#   ۴. کلیدِ دستیِ مالک (`quiet_manual`) **همیشه و برای همیشه** برنده است.
#   ۵. دادهٔ کم ⇒ همان پنجرهٔ فعلی + confidence ِ پایین + `why` ِ صادق.
#      صفر جعل: وقتی نمی‌داند، می‌گوید نمی‌داند.
#
# منابعِ داده (هر دو از قبل وجود دارند — چیزِ تازه‌ای جمع نمی‌شود):
#   · همین store: `fired_ts` (لحظهٔ قطعِ مالک) و `done_ts` (لحظهٔ عملِ مالک).
#   · `tg-send-log.jsonl` ردیف‌های `surface="dm"` — «چند بار در آن ساعت واقعاً
#     به مالک رسیده‌ایم». این‌ها **هرگز** به‌تنهایی «بیداری» را ثابت نمی‌کنند
#     (لاگ فقط ارسالِ ما را می‌بیند، نه واکنشِ او) — فقط اطمینان را بالا
#     می‌برند. عدمِ تقارن عمدی است.

MIN_SAMPLES = 20            # کلِ فایرهای سنجیدنی برای هر حرکت
MIN_HOUR_SAMPLES = 3        # حداقلِ فایر در یک ساعت تا دربارهٔ آن ساعت حکم بدهیم
FAST_ACT_S = 1800.0         # «سریع عمل کرد» = زیرِ نیم‌ساعت
AWAKE_RATE = 0.5            # ≥نصفِ فایرهای آن ساعت سریع جواب گرفتند ⇒ بیدار
QUIET_FLOOR_H = 5           # سکوت هرگز کوتاه‌تر از این
QUIET_MAX_H = 12            # و هرگز بلندتر از این (روزِ کر ممنوع)
CONFIDENCE_BAR = 0.6        # زیرِ این، فقط گزارش — نوشتنی در کار نیست
SEND_LOG_WINDOW_S = 30 * 86400.0

MANUAL_KEY = "quiet_manual"          # رأیِ دستیِ مالک — همیشه برنده
ADAPT_FLAG = "OCTOPUS_TG_QUIET_ADAPT"   # پیش‌فرض **روشن**؛ "0" خاموشش می‌کند


def adapt_enabled() -> bool:
    return str(os.environ.get(ADAPT_FLAG, "1")).strip() != "0"


def quiet_hours(cfg: dict) -> set:
    """مجموعهٔ ساعت‌های ساکت — دقیقاً هم‌معنیِ `_in_quiet` روی سرِ ساعت."""
    try:
        a = int(float(cfg.get("quiet_from", 23))) % 24
        b = int(float(cfg.get("quiet_to", 7))) % 24
    except (TypeError, ValueError):
        a, b = 23, 7
    if a == b:
        return set()
    if a < b:
        return set(range(a, b))
    return set(range(a, 24)) | set(range(0, b))


def _longest_run(hours: set) -> "tuple | None":
    """بلندترین بازهٔ پیوستهٔ **دایره‌ای** — (شروع، طول)."""
    if not hours or len(hours) >= 24:
        return None
    best = None
    for start in sorted(hours):
        if (start - 1) % 24 in hours:
            continue                                   # فقط از سرِ یک بازه
        ln, h = 0, start
        while (h % 24) in hours and ln < 24:
            ln += 1
            h += 1
        if best is None or ln > best[1]:
            best = (start, ln)
    return best


def _act_samples() -> tuple:
    """(n_by_hour, fast_by_hour, total) از مهرهای همین store.

    فقط آیتم‌های **سنجیدنی**: باید `fired_ts` داشته باشند؛ آیتمِ done ِ
    بی‌`done_ts` (میراثِ قبل از ۰۷-۳۱) کنار گذاشته می‌شود — نه سریع، نه کند."""
    n = [0] * 24
    fast = [0] * 24
    total = 0
    for it in _load().get("items", []):
        f = it.get("fired_ts")
        if not f:
            continue
        try:
            f = float(f)
        except (TypeError, ValueError):
            continue
        dts = it.get("done_ts")
        if it.get("done") and not dts:
            continue                                   # غیرقابلِ سنجش
        h = datetime.fromtimestamp(f).hour
        n[h] += 1
        total += 1
        if dts:
            try:
                lat = float(dts) - f
            except (TypeError, ValueError):
                lat = -1.0
            if 0 <= lat <= FAST_ACT_S:
                fast[h] += 1
    return n, fast, total


def _dm_by_hour(now: float) -> tuple:
    """(شمارشِ ساعتی، کلِ ردیف‌ها) از ردیف‌های DM ِ tg-send-log.

    «رو به مالک» یعنی صریحاً `surface == "dm"` و `state == "sent"` و `ok`.
    ردیفِ بی‌`surface` (میراث) شمرده نمی‌شود — حدس‌زدنِ مقصد از روی نبودِ
    فیلد، همان جعلی است که این ماژول از آن پرهیز می‌کند."""
    by = [0] * 24
    total = 0
    cutoff = float(now) - SEND_LOG_WINDOW_S
    try:
        raw = _send_log_path().read_text("utf-8", errors="replace")
    except OSError:
        return by, 0
    for ln in raw.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        if str(d.get("surface") or "") != "dm":
            continue
        if str(d.get("state") or "sent") != "sent" or not d.get("ok", True):
            continue
        try:
            ts = float(d.get("ts") or 0)
        except (TypeError, ValueError):
            continue
        if ts < cutoff:
            continue
        by[datetime.fromtimestamp(ts).hour] += 1
        total += 1
    return by, total


def learn(now: "float | None" = None) -> dict:
    """پنجرهٔ سکوتِ پیشنهادی از رفتارِ واقعیِ مالک — **بدونِ هیچ نوشتنی**.

    خروجی: ``{"quiet_from","quiet_to","confidence","samples","why", …}``
    و کلیدهای کمکی: `current` (پنجرهٔ امروز)، `changed`، `judged_hours`،
    `dm_rows`، `manual`، `floor`.

    دادهٔ نازک ⇒ همان پنجرهٔ فعلی با confidence ِ پایین و `why` ِ صادق."""
    now = float(now if now is not None else time.time())
    cfg = load_config()
    cur_a = int(float(cfg.get("quiet_from", 23))) % 24
    cur_b = int(float(cfg.get("quiet_to", 7))) % 24
    n, fast, samples = _act_samples()
    dm, dm_rows = _dm_by_hour(now)
    judged = [h for h in range(24) if n[h] >= MIN_HOUR_SAMPLES]

    volume = min(1.0, samples / float(2 * MIN_SAMPLES)) if MIN_SAMPLES else 0.0
    coverage = min(1.0, len(judged) / 8.0)
    # tg-send-log فقط **تأیید** می‌کند: بدونِ آن سقفِ اطمینان ۰٫۷۵ است.
    reach = 0.75 + 0.25 * min(1.0, dm_rows / float(MIN_SAMPLES))
    conf = round(volume * coverage * reach, 2)

    base = {"quiet_from": cur_a, "quiet_to": cur_b, "confidence": conf,
            "samples": samples, "current": [cur_a, cur_b], "changed": False,
            "judged_hours": len(judged), "dm_rows": dm_rows,
            "manual": bool(cfg.get(MANUAL_KEY)), "floor": QUIET_FLOOR_H,
            "bar": CONFIDENCE_BAR}

    if cfg.get(MANUAL_KEY):
        # رأیِ دستیِ مالک: نه فقط این‌بار — **همیشه**. اطمینان صفر اعلام
        # می‌شود تا هیچ مسیرِ دیگری آن را «قابلِ اعمال» نبیند.
        return dict(base, confidence=0.0,
                    why=f"پنجره دستی قفل شده ({MANUAL_KEY}) — یادگیری خاموش")

    if samples < MIN_SAMPLES:
        return dict(base, why=(f"دادهٔ کم: {_fa(samples)} نمونهٔ سنجیده از "
                               f"{_fa(MIN_SAMPLES)} لازم — پنجره دست نمی‌خورد"))

    cur = quiet_hours(cfg)
    awake = {h for h in judged if n[h] and fast[h] / n[h] >= AWAKE_RATE}
    asleep = {h for h in judged if h not in awake}
    new = (cur - awake) | asleep

    run = _longest_run(new)
    if run is None:
        return dict(base, why="پیشنهادِ بی‌معنی (خالی یا کلِ شبانه‌روز) — رد شد")
    start, length = run
    if length < QUIET_FLOOR_H:
        return dict(base, why=(f"پنجرهٔ پیشنهادی {_fa(length)} ساعت است، کفِ "
                               f"{_fa(QUIET_FLOOR_H)} ساعت را نمی‌شکنیم"))
    if length > QUIET_MAX_H:
        return dict(base, why=(f"پنجرهٔ پیشنهادی {_fa(length)} ساعت است، از "
                               f"سقفِ {_fa(QUIET_MAX_H)} ساعت بیشتر — رد شد"))

    new_a, new_b = start % 24, (start + length) % 24
    changed = (new_a, new_b) != (cur_a, cur_b)
    if not changed:
        return dict(base, why=(f"داده پنجرهٔ فعلی را تأیید می‌کند "
                               f"({_fa(samples)} نمونه)"))
    why = (f"از {_fa(samples)} نمونه در {_fa(len(judged))} ساعتِ حکم‌دار: "
           f"بیدار {_fa(sorted(awake))} · ساکت {_fa(sorted(asleep))}"
           + (f" · {_fa(dm_rows)} ردیفِ DM تأییدش می‌کند" if dm_rows else
              " · بدونِ ردیفِ DM، اطمینان سقفِ ۰٫۷۵ دارد"))
    return dict(base, quiet_from=new_a, quiet_to=new_b, changed=True, why=why)


def adapt_quiet(now: "float | None" = None) -> dict:
    """`learn()` + نوشتنِ پنجره در config — **فقط** اگر اطمینان از میله رد شود.

    خروجیِ learn به‌علاوهٔ `applied`. کلیدهای دیگرِ config (brief_hour،
    wrap_hour، رأیِ دستی) دست‌نخورده می‌مانند — این‌جا فقط پنجره و سه کلیدِ
    شفافیت (`quiet_learned_*`) نوشته می‌شوند تا مالک بتواند بپرسد «چرا؟»."""
    now = float(now if now is not None else time.time())
    v = learn(now)
    patch = {"quiet_learned_day": datetime.fromtimestamp(now).strftime("%Y-%m-%d"),
             "quiet_learned_conf": v.get("confidence"),
             "quiet_learned_why": str(v.get("why") or "")[:300]}
    if v.get("manual"):
        return dict(v, applied=False)          # قفلِ دستی: حتی مهرِ روز هم نه
    if v.get("changed") and float(v.get("confidence") or 0) >= CONFIDENCE_BAR:
        patch["quiet_from"] = int(v["quiet_from"])
        patch["quiet_to"] = int(v["quiet_to"])
        _write_config(patch)
        return dict(v, applied=True)
    _write_config(patch)                       # فقط شفافیت، نه تغییرِ رفتار
    return dict(v, applied=False)


def _write_config(patch: dict) -> bool:
    """merge ِ محافظه‌کار: فایلِ موجود برنده بر پیش‌فرض، patch برنده بر همه.
    (بازنویسیِ کامل ممنوع — کلیدِ دستیِ مالک نباید قربانیِ یادگیری شود.)"""
    raw = {}
    try:
        d = json.loads(_cfg_file().read_text("utf-8"))
        if isinstance(d, dict):
            raw = d
    except (OSError, ValueError):
        raw = {}
    merged = dict(DEFAULT_CONFIG)
    merged.update(raw)
    merged.update(patch or {})
    try:
        p = _cfg_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(merged, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


def _maybe_adapt(now: float) -> None:
    """روزی یک‌بار یادگیری را بدوان — **خودسیم‌کشی**، چون center.py قفل است.

    چرا داخلِ beat: قابلیتی که صداکننده ندارد، «اعلام‌شده ولی مرده» است — و
    درسِ ثبت‌شدهٔ همین vault می‌گوید سیمِ نبسته یعنی قابلیت وجود ندارد. مرکز
    از قبل beat را هر ضربان صدا می‌زند، پس یک گیتِ روزانه کافی است.
    نشانگرِ روز حتی وقتی یادگیری **حرکت نکرد** هم نوشته می‌شود تا هر ضربان
    دوباره فایل‌ها را نخواند (طوفانِ I/O). خطا هرگز beat را نمی‌کشد."""
    if not adapt_enabled():
        return
    try:
        today = datetime.fromtimestamp(float(now)).strftime("%Y-%m-%d")
        if str(load_config().get("quiet_learned_day") or "") == today:
            return
        adapt_quiet(now)
    except Exception:  # noqa: BLE001 — یادگیری هرگز یادآوری را نمی‌خوابانَد
        pass


def beat(*, now: float, send_dm_fn, send_leg_fn) -> int:
    """موعدرسیده‌های شلیک‌نشده را برسان — سوار بر beat ِ موجودِ مرکز.

    dm ⇒ send_dm_fn(text, reminder_id) — مرکز کیبوردِ ✅ را از
    reminder_keyboard می‌سازد؛ leg ⇒ send_leg_fn(leg, text).
    پنجرهٔ سکوت: فقط بحرانی/فوری؛ بقیه می‌مانند و سرِ ۰۷:۰۰ می‌رسند.
    ارسالِ ناموفق (استثنا) ⇒ fired نمی‌شود؛ ضربانِ بعد دوباره می‌کوشد."""
    _maybe_adapt(now)
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
        # مهرِ زمان با همان clock ِ تزریقیِ beat (پاریتی با mark_fired) —
        # سنجهٔ «یادآوری‌های fired ِ هفته» از همین fired_ts می‌خواند.
        it["fired_ts"] = float(now)
        fired += 1
        changed = True
    if changed:
        _save(d)
    return fired
