#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""notify_budget — بودجهٔ اعلانِ روزانه (منشور §۳: «≤۵ پیامِ قطع‌کننده در روز؛
سرریز → digest، با اعلامِ صادقانه»).

تا امشب این بند فقط در منشور نوشته بود و **هیچ کدی اجرایش نمی‌کرد** — یعنی
سقفِ اعلان یک ادعا بود نه یک مکانیزم. این ماژول همان بند است، نه بیشتر:

  · فقط طبقهٔ **قطع‌کننده** می‌شمارد — کارتِ مالک، هشدار، یادآوری، سؤال.
    جریانِ محیطی/ویرایشِ کارتِ زنده/خودِ digest **هرگز** بودجه نمی‌خورند؛
    طبقه را **صداکننده** می‌گوید (این ماژول متن را نمی‌خواند و حدس نمی‌زند).
  · بحرانی و ایمنی (روحِ cortisol/alert/heart، و هر چیزی که صداکننده با
    `critical=True` علامت بزند) از سقف **معاف**اند — ولی جدا شمرده می‌شوند
    (`exempt_used`) تا گزارش بتواند صادق باشد: «۵ عادی + ۳ بحرانی».
  · سرریز **دور ریخته نمی‌شود**: `defer()` آیتم را در همان بافرِ digest ِ
    `hold_policy` می‌نویسد (بافرِ دوم ساخته نمی‌شود — مسیرِ بافر همیشه از
    خودِ hold_policy پرسیده می‌شود، هرگز این‌جا بازسازی نمی‌شود).
  · `announce_line()` جملهٔ صادقانهٔ فارسی را می‌سازد؛ خودِ اعلام **نباید** از
    `allow()` رد شود (اعلامِ پرشدنِ سقف، خودش قربانیِ سقف نمی‌شود).

مرزها: صفر ارسال · صفر شبکه · ساعت تزریق‌پذیر (`now=`) · نوشتنِ اتمی
(tmp + os.replace) · state در `STATE_DIR/telegram/notify-budget.json`
(تست‌ها با harness ایزوله‌اند).

fail-safe (هم‌جهت با hold_policy): اگر ثبتِ شمارنده شکست بخورد **اجازه داده
می‌شود** و دلیل صادقانه برمی‌گردد — سکوتِ ناشی از خطای دیسک بدترین خروجی است.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve().parent

CAP = 5                                   # منشور §۳ — سقفِ پیامِ قطع‌کننده در روز
_HISTORY_DAYS = 14                        # تاریخچه برای گزارشِ هفتگی (نه بیشتر)

# جریان‌هایی که ذاتاً قطع‌کننده نیستند — هرگز بودجه نمی‌خورند.
AMBIENT_KINDS = frozenset({
    "ambient", "edit", "digest", "pulse", "health", "log", "mirror",
    "receipt", "typing", "callback", "trace",
})

# بحرانی/ایمنی — همیشه رد می‌شوند، جدا شمرده می‌شوند.
EXEMPT_KINDS = frozenset({
    "alert", "critical", "cortisol", "heart", "halt", "panic", "safety",
    "watchdog",
})

# طبقاتِ قطع‌کنندهٔ شناخته‌شده (فقط برای مستندسازی و گزارش؛ ناشناخته هم
# قطع‌کننده حساب می‌شود — پایین را ببین).
INTERRUPTING_KINDS = frozenset({
    "card", "reminder", "question", "brief", "mission", "lead", "decision",
})

AMBIENT = "ambient"
EXEMPT = "exempt"
INTERRUPTING = "interrupting"

_EN2FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(n) -> str:
    return str(n).translate(_EN2FA)


# ── مسیرها ─────────────────────────────────────────────────────────────────
def _state_dir() -> Path:
    """env-اول، بعد opslib — همان خانهٔ `hold_policy` تا دو حقیقت نسازیم."""
    env = os.environ.get("OCTOPUS_STATE_DIR", "").strip()
    if env:
        return Path(env) / "telegram"
    try:
        if str(_HERE.parent) not in sys.path:
            sys.path.insert(0, str(_HERE.parent))
        if str(_HERE.parent / "budget") not in sys.path:
            sys.path.insert(0, str(_HERE.parent / "budget"))
        import opslib
        return Path(opslib.STATE_DIR) / "telegram"
    except Exception:  # noqa: BLE001
        return _HERE.parent / "state" / "telegram"


def _path() -> Path:
    return _state_dir() / "notify-budget.json"


def _day_key(now: float) -> str:
    return datetime.fromtimestamp(float(now)).strftime("%Y-%m-%d")


# ── طبقه‌بندی ──────────────────────────────────────────────────────────────
def kind_class(kind, *, critical: bool = False) -> str:
    """`ambient` | `exempt` | `interrupting` — طبقه از صداکننده می‌آید.

    ترتیبِ حکم عمدی است:
      ۱. `critical=True` ⇒ معاف (حتی اگر نامِ طبقه محیطی باشد؛ صداکننده‌ای که
         صریحاً بحرانی می‌گوید، حرفش مقدم است).
      ۲. نامِ طبقه در EXEMPT ⇒ معاف.
      ۳. نامِ طبقه در AMBIENT ⇒ محیطی، بی‌بودجه.
      ۴. هر چیز دیگر (از جمله **ناشناخته**) ⇒ قطع‌کننده و بودجه‌خور.
         ناشناخته عمداً بودجه می‌خورد: دورزدنِ بی‌صدای سقف بدتر از یک پیامِ
         شمرده‌شدهٔ اضافه است.
    """
    k = str(kind or "").strip().lower()
    if critical:
        return EXEMPT
    if k in EXEMPT_KINDS:
        return EXEMPT
    if k in AMBIENT_KINDS:
        return AMBIENT
    return INTERRUPTING


# ── store ──────────────────────────────────────────────────────────────────
def _blank(day: str) -> dict:
    return {"day": day, "used": 0, "exempt_used": 0, "deferred": 0,
            "by_kind": {}, "announced_day": None, "history": {}}


def _load(now: "float | None" = None) -> dict:
    """store + rollover ِ روزِ محلی. (نمی‌نویسد — نوشتن کارِ عملِ mutating است؛
    الگوی question_budget.)"""
    now = float(now if now is not None else time.time())
    day = _day_key(now)
    d = _blank(day)
    try:
        raw = json.loads(_path().read_text("utf-8"))
        if isinstance(raw, dict) and raw.get("day"):
            d = raw
    except (OSError, ValueError):
        pass
    for k, v in _blank(day).items():
        d.setdefault(k, v)
    if d.get("day") != day:                       # نیمه‌شب: روزِ کهنه → تاریخچه
        hist = d.get("history") if isinstance(d.get("history"), dict) else {}
        hist[str(d.get("day"))] = {"used": int(d.get("used", 0)),
                                   "exempt": int(d.get("exempt_used", 0)),
                                   "deferred": int(d.get("deferred", 0))}
        if len(hist) > _HISTORY_DAYS:
            hist = dict(sorted(hist.items())[-_HISTORY_DAYS:])
        d["history"] = hist
        d["day"] = day
        d["used"] = 0
        d["exempt_used"] = 0
        d["deferred"] = 0
        d["by_kind"] = {}
    return d


def _save(d: dict) -> bool:
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True
    except OSError:
        return False


# ── تصمیم ──────────────────────────────────────────────────────────────────
def _verdict(d: dict, kind, cls: str, allow_: bool, reason: str) -> dict:
    return {"allow": bool(allow_), "used": int(d.get("used", 0)), "cap": CAP,
            "reason": reason, "kind": str(kind or ""), "class": cls,
            "remaining": max(0, CAP - int(d.get("used", 0))),
            "exempt_used": int(d.get("exempt_used", 0)),
            "deferred": int(d.get("deferred", 0))}


def peek(kind, now: "float | None" = None, *, critical: bool = False) -> dict:
    """همان حکمِ `allow` **بدونِ مصرفِ بودجه** — برای گزارش و پیش‌نمایش."""
    now = float(now if now is not None else time.time())
    d = _load(now)
    cls = kind_class(kind, critical=critical)
    if cls == AMBIENT:
        return _verdict(d, kind, cls, True, "ambient-never-counted")
    if cls == EXEMPT:
        return _verdict(d, kind, cls, True, "exempt")
    if int(d.get("used", 0)) >= CAP:
        return _verdict(d, kind, cls, False, "budget-exhausted")
    return _verdict(d, kind, cls, True, "within-budget")


def allow(kind, now: "float | None" = None, *, critical: bool = False) -> dict:
    """آیا این پیامِ قطع‌کننده حق دارد امروز مالک را قطع کند؟

    ⚠️ این تابع **مصرف‌کننده** است: هر `allow=True` ِ قطع‌کننده یک واحد از سقف
    را همین‌جا می‌سوزاند (نقطهٔ تصمیم = لحظهٔ تحویل، درسِ «ثبت را گیت نکن،
    تحویل را»). اگر ارسال بعدش شکست خورد، `refund()` هست.

    خروجی: ``{"allow","used","cap","reason","class","remaining",
    "exempt_used","deferred"}``. `reason` ∈ ambient-never-counted · exempt ·
    within-budget · budget-exhausted · state-write-failed.

    صداکننده موظف است روی `allow=False` آیتم را به `defer()` بدهد — نه اینکه
    دورش بیندازد (منشور: «سرریز → digest»).
    """
    now = float(now if now is not None else time.time())
    d = _load(now)
    cls = kind_class(kind, critical=critical)

    if cls == AMBIENT:                    # محیطی: نه شمرده، نه ذخیره
        return _verdict(d, kind, cls, True, "ambient-never-counted")

    if cls == EXEMPT:
        d["exempt_used"] = int(d.get("exempt_used", 0)) + 1
        _bump_kind(d, kind)
        if not _save(d):
            return _verdict(d, kind, cls, True, "state-write-failed")
        return _verdict(d, kind, cls, True, "exempt")

    if int(d.get("used", 0)) >= CAP:
        return _verdict(d, kind, cls, False, "budget-exhausted")

    d["used"] = int(d.get("used", 0)) + 1
    _bump_kind(d, kind)
    if not _save(d):
        # fail-safe: شمارنده ثبت نشد ⇒ اجازه می‌دهیم و دلیل را بلند می‌گوییم.
        # سکوتِ ناشی از خطای دیسک، بدترین خروجیِ ممکن است.
        return _verdict(d, kind, cls, True, "state-write-failed")
    return _verdict(d, kind, cls, True, "within-budget")


def _bump_kind(d: dict, kind) -> None:
    bk = d.get("by_kind") if isinstance(d.get("by_kind"), dict) else {}
    k = str(kind or "?").strip().lower()[:24] or "?"
    bk[k] = int(bk.get(k, 0)) + 1
    d["by_kind"] = bk


def refund(kind, now: "float | None" = None, *,
           critical: bool = False) -> bool:
    """واحدِ سوخته را برگردان — فقط وقتی ارسالِ بعد از `allow=True` شکست خورد.
    (اختیاری در سیم‌کشی؛ نبودش فقط یک واحدِ صادقانه هدر می‌دهد.)"""
    now = float(now if now is not None else time.time())
    d = _load(now)
    cls = kind_class(kind, critical=critical)
    if cls == AMBIENT:
        return True
    key = "exempt_used" if cls == EXEMPT else "used"
    if int(d.get(key, 0)) <= 0:
        return False
    d[key] = int(d[key]) - 1
    return _save(d)


# ── سرریز → digest ─────────────────────────────────────────────────────────
def defer(kind, text, now: "float | None" = None) -> bool:
    """سرریز را در **همان** بافرِ digest ِ hold_policy بگذار.

    خروجی **bool ِ صادق** است: `True` یعنی آیتم واقعاً در بافر نشست؛ `False`
    یعنی ننشست و صداکننده باید بلند شکست بخورد (بفرستد یا آرشیو کند) —
    آیتمِ سرریز هرگز نباید بی‌صدا گم شود.

    چرا `hold_policy._buffer_append` (تابعِ خصوصی) صدا زده می‌شود: بافرِ
    digest از قبل وجود دارد و مرکز ساعتی flushاش می‌کند. ساختنِ بافرِ دومِ
    موازی یعنی دو صفِ ناگفته و یک flush — همان اشتباهِ «دو نویسنده روی یک
    حالت». مسیرِ بافر هم این‌جا بازسازی نمی‌شود؛ همیشه از خودِ hold_policy
    پرسیده می‌شود.
    """
    now = float(now if now is not None else time.time())
    body = str(text or "").strip()
    if not body:
        return False
    try:
        hp = _hold_policy()
        if hp is None:
            return False
        ok = bool(hp._buffer_append(f"notify:{str(kind or '?')[:24]}",
                                    body, "normal", now))
    except Exception:  # noqa: BLE001 — بافر نشد ⇒ صادقانه False
        return False
    if ok:
        d = _load(now)
        d["deferred"] = int(d.get("deferred", 0)) + 1
        _save(d)                                   # شکستِ شمارش حکم را عوض نمی‌کند
    return ok


def route(kind, text, now: "float | None" = None, *,
          critical: bool = False) -> dict:
    """تصمیم **و** اجرای مقصد در یک فراخوان — نقطهٔ ورودِ توصیه‌شدهٔ سیم‌کشی.

    چرا این تابع وجود دارد: `allow()` به‌تنهایی یک تلهٔ صداکننده است — اگر
    کسی روی `allow=False` فراموش کند `defer()` را صدا بزند، پیام **بی‌صدا
    گم می‌شود**؛ دقیقاً همان شکستی که منشور ممنوعش کرده. این‌جا گم‌شدن
    ساختاراً ممکن نیست:

      route ∈ ``send`` (برو بفرست) · ``digest`` (در بافر نشست، نفرست) ·
              ``send-anyway`` (بافر ننوشت — **بفرست**؛ سکوت بدتر از سرریز است)

    `announce` می‌گوید آیا امروز باید جملهٔ صادقانهٔ سرریز هم برود (بعد از
    ارسالش `mark_announced` را صدا بزن)."""
    now = float(now if now is not None else time.time())
    d = allow(kind, now, critical=critical)
    if d["allow"]:
        return dict(d, route="send", deferred_ok=None, announce=False)
    ok = defer(kind, text, now)
    return dict(d, route=("digest" if ok else "send-anyway"),
                deferred_ok=ok, announce=announce_due(now))


def _hold_policy():
    try:
        if str(_HERE) not in sys.path:
            sys.path.insert(0, str(_HERE))
        import hold_policy
        return hold_policy
    except Exception:  # noqa: BLE001
        return None


# ── اعلامِ صادقانه ──────────────────────────────────────────────────────────
def announce_line(now: "float | None" = None) -> str:
    """جملهٔ فارسیِ منشور — در هر دو حالت **صادق**، نه فقط هنگامِ سرریز.

    ⚠️ این پیام خودش نباید از `allow()` رد شود: اعلامِ پرشدنِ سقف، قربانیِ
    سقف نمی‌شود (وگرنه سکوت، بی‌صدا و بی‌توضیح می‌ماند).
    """
    now = float(now if now is not None else time.time())
    d = _load(now)
    used = int(d.get("used", 0))
    ex = int(d.get("exempt_used", 0))
    dfr = int(d.get("deferred", 0))
    tail = f" · {_fa(ex)} موردِ بحرانی خارج از سقف" if ex else ""
    if used >= CAP:
        return (f"📵 سقفِ اعلانِ امروز پر شد ({_fa(used)} از {_fa(CAP)}){tail}. "
                f"از این‌جا به بعد هرچه بیاید در دایجست جمع می‌شود، نه دور "
                f"ریخته — تا الان {_fa(dfr)} مورد.")
    return (f"🔔 امروز {_fa(used)} از {_fa(CAP)} اعلانِ قطع‌کننده مصرف شده"
            f"{tail}" + (f" · {_fa(dfr)} مورد در دایجست." if dfr else "."))


def announce_due(now: "float | None" = None) -> bool:
    """آیا امروز باید اعلامِ سرریز برود؟ — فقط یک‌بار در روز و فقط وقتی
    واقعاً چیزی به دایجست رفته باشد (اعلامِ بی‌مصداق = نویز)."""
    now = float(now if now is not None else time.time())
    d = _load(now)
    return (int(d.get("deferred", 0)) > 0
            and str(d.get("announced_day") or "") != _day_key(now))


def mark_announced(now: "float | None" = None) -> bool:
    now = float(now if now is not None else time.time())
    d = _load(now)
    d["announced_day"] = _day_key(now)
    return _save(d)


# ── گزارش ──────────────────────────────────────────────────────────────────
def summary(now: "float | None" = None) -> dict:
    """تصویرِ امروز + جمعِ ۷ روزِ گذشته — خوراکِ بریفِ روزانه و مرورِ هفتگی."""
    now = float(now if now is not None else time.time())
    d = _load(now)
    day = _day_key(now)
    hist = d.get("history") if isinstance(d.get("history"), dict) else {}
    week_keys = [(datetime.fromtimestamp(now) - timedelta(days=i)
                  ).strftime("%Y-%m-%d") for i in range(1, 7)]
    w_used = int(d.get("used", 0))
    w_ex = int(d.get("exempt_used", 0))
    w_dfr = int(d.get("deferred", 0))
    days = 1
    for k in week_keys:
        row = hist.get(k)
        if not isinstance(row, dict):
            continue
        days += 1
        w_used += int(row.get("used", 0) or 0)
        w_ex += int(row.get("exempt", 0) or 0)
        w_dfr += int(row.get("deferred", 0) or 0)
    return {"day": day, "cap": CAP,
            "used": int(d.get("used", 0)),
            "remaining": max(0, CAP - int(d.get("used", 0))),
            "exempt_used": int(d.get("exempt_used", 0)),
            "deferred": int(d.get("deferred", 0)),
            "by_kind": dict(d.get("by_kind") or {}),
            "exhausted": int(d.get("used", 0)) >= CAP,
            "week": {"days": days, "used": w_used, "exempt": w_ex,
                     "deferred": w_dfr,
                     "avg_used": round(w_used / max(1, days), 2)},
            "line": announce_line(now)}


if __name__ == "__main__":  # pragma: no cover — گزارشِ دستی، صفر ارسال
    print(json.dumps(summary(), ensure_ascii=False, indent=2))
