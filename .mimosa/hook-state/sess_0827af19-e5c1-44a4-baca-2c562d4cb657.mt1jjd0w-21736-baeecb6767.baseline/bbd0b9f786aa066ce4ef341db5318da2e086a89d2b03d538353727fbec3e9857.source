"""owner_debt.py — یک جملهٔ «بدهیِ مالک» برای بریفِ صبح. تابعِ خالص، **بی‌سیم**.

گامِ ۲۰ ِ UNIFICATION-DESIGN-2026-08-03 (جزءِ C15).

چرا وجود دارد:

    تنها مکانیزمِ **تشدید** در کلِ طرح. تصمیمی که نمی‌آید باید بلندتر شود، نه
    اینکه محو شود. سنجشِ زندهٔ ۲۰۲۶-۰۸-۰۳ روی همین تاشدگی: ۲۱ تصمیمِ مالک ثبت
    شده و **صفر** اثر — و هیچ سطحی این را نمی‌گفت. یک صفِ راکد که کسی صدایش
    را نمی‌شنود، با نبودنِ صف فرقی ندارد.

مرزِ عمدی — «نوشتنِ جمله مهندسی است؛ فرستادنش رأی مالک است»:

    این ماژول **هیچ صداکننده‌ای ندارد** و در روزِ اول نباید داشته باشد. وصل
    کردنش به بریف/تلگرام گامِ بعد و رأیِ مالک است. تستِ همراه هر دو را قفل
    می‌کند: صفر نوشتن، صفر صداکنندهٔ تولیدی.

ناوردی‌ها:

    ۱. **`state_dir` اجباری.** پیش‌فرضِ ضمنی یعنی خوردن به ذخیرهٔ زنده.
    ۲. **ناخوانا ⇒ UNKNOWN، هرگز «۰ کارت منتظر».** بریفی که وقتی *نمی‌بیند*
       می‌گوید «چیزی منتظر نیست» از سکوت بدتر است.
    ۳. **روی UNKNOWN هیچ کلیدِ شمارشی وجود ندارد** — نه `waiting: 0`، نه
       `waiting: None`. همان قاعدهٔ `provenance.stamp()`: ورودیِ غایب نباید به
       صفرِ بی‌صدا تبدیل شود که تا کارتِ مالک سفر کند.
    ۴. **بی‌محتوا.** فقط شمارش، سن و نامِ مرحله. نه متنِ کارت، نه شناسه.
    ۵. **صفر نوشتن، و هیچ importی از تلگرام/شبکه.**

چرا خودش خوانایی را می‌سنجد (اختلاف با C1، سنجیده‌شده):

    `pending_card_recovery._load_store()` هر استثنا را می‌بلعد و `{}` برمی‌گرداند،
    و `lifecycle_fold.fold()` خوانایی را فقط با `path.exists()` تعریف می‌کند.
    یعنی یک فایلِ **موجود ولی خراب** از C1 به‌صورتِ «۰ کارت» بیرون می‌آید. برای
    ناوردیِ ۲ کافی نیست، پس این ماژول خودش یک پروبِ خوانایی دارد. این منبعِ
    حقیقتِ دوم نیست: همان یک فایل، و هیچ شمارشی از آن استخراج نمی‌شود — فقط
    پاسخِ «اصلاً می‌شد خواندش؟».

سطحِ تشدید (`level`):

    0  چیزی برای گفتن نیست ⇒ جمله تولید نمی‌شود
    1  بدهی هست، قدیمی‌ترین کمتر از ۳ روز
    2  قدیمی‌ترین ≥ ۳ روز — **یا** دستِ‌کم یک تصمیمِ بی‌اثر
    3  قدیمی‌ترین ≥ ۷ روز

    کفِ «۲ برای بی‌اثر» عمدی است: تصمیمی که گرفته شد و اثر نکرد از تصمیمی که
    هنوز گرفته نشده بدتر است — لولهٔ اثر شکسته، نه صفِ ورودی.
    UNKNOWN اصلاً `level` ندارد: چیزی را که نمی‌بینی نمی‌توانی تشدید کنی.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import lifecycle_fold as _lf   # noqa: E402

__all__ = [
    "owner_debt", "render", "owner_debt_line",
    "DAY_S", "LOUD_S", "LOUDEST_S", "STORE_REL",
]

DAY_S = 86400.0
#: قدیمی‌ترین کارتِ منتظر از این آستانه که گذشت، لحن عوض می‌شود.
LOUD_S = 3 * DAY_S
LOUDEST_S = 7 * DAY_S

#: همان فایلی که C1 می‌خواند — فقط برای پروبِ خوانایی، نه برای شمارش.
STORE_REL = ("pulse", "pending-cards.json")

_FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

_PREFIX = {
    1: "بدهیِ مالک",
    2: "بدهیِ مالک (کهنه)",
    3: "بدهیِ مالک (بسیار کهنه)",
}

_REASON_FA = {
    "store-absent": "دفترِ کارت‌ها وجود ندارد",
    "store-unreadable": "دفترِ کارت‌ها باز نشد",
    "store-corrupt": "دفترِ کارت‌ها خوانا نبود",
    "fold-unknown": "تاشدگی شمارشی نداد",
    "fold-error": "تاشدگی شکست",
}


def _fa(number) -> str:
    """رقمِ فارسی — جمله برای مالک است. (متنِ تماماً فارسی، بی‌قاطیِ bidi.)"""
    return "".join(_FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(number))


def _store_readable(state_dir):
    """`(ok, reason_slug)` — فقط «می‌شد خواندش؟». هیچ شمارشی از اینجا درنمی‌آید."""
    path = Path(state_dir).joinpath(*STORE_REL)
    try:
        if not path.exists():
            return False, "store-absent"
        raw = path.read_text("utf-8")
    except OSError:
        return False, "store-unreadable"
    except UnicodeDecodeError:
        return False, "store-corrupt"
    try:
        data = json.loads(raw)
    except ValueError:
        return False, "store-corrupt"
    if not isinstance(data, dict):
        return False, "store-corrupt"
    return True, ""


def _count(stamped):
    """مقدارِ یک تمبر، یا None اگر UNKNOWN باشد (کلیدِ `value` را ندارد)."""
    if not isinstance(stamped, dict) or "value" not in stamped:
        return None
    if stamped.get("mode") == "UNKNOWN":
        return None
    try:
        return int(stamped["value"])
    except (TypeError, ValueError):
        return None


def _level(waiting, ineffective, oldest_age_s):
    """چقدر بلند؟ صعودی در سن — چیزی که نمی‌آید باید بلندتر شود."""
    if waiting <= 0 and ineffective <= 0:
        return 0
    level = 1
    if oldest_age_s is not None:
        if oldest_age_s >= LOUDEST_S:
            level = 3
        elif oldest_age_s >= LOUD_S:
            level = 2
    if ineffective > 0:
        level = max(level, 2)
    return level


def _unknown(reason):
    # عمداً بدونِ هیچ کلیدِ شمارشی — ناوردیِ ۳.
    return {
        "known": False,
        "reason": reason,
        "sources": list(_lf.SOURCES),
        "text": "بدهیِ مالک: نامعلوم — %s." % _REASON_FA.get(reason, reason),
    }


def owner_debt(state_dir, now=None, _fold=None):
    """بدهیِ مالک روی یک `state_dir` مشخص. صفر نوشتن، صفر حالتِ نگه‌داشته.

    `state_dir` اجباری است — پیش‌فرضِ ضمنی یعنی خوردن به ذخیرهٔ زنده.
    `_fold` فقط برای تست تزریق می‌شود؛ مسیرِ تولیدی همیشه `lifecycle_fold.fold`.
    """
    if state_dir is None:
        raise ValueError("state_dir is required; an implicit default hits the live store")

    now_s = float(now) if now is not None else time.time()

    ok, reason = _store_readable(state_dir)
    if not ok:
        return _unknown(reason)

    fold_fn = _fold if _fold is not None else _lf.fold
    try:
        folded = fold_fn(state_dir, now=now_s)
    except Exception:   # noqa: BLE001 — بریفِ صبح نباید روی یک دفترِ خراب بمیرد
        return _unknown("fold-error")

    if not isinstance(folded, dict) or not folded.get("readable"):
        return _unknown("store-unreadable")

    waiting = _count(folded.get("stalled"))
    decided = _count(folded.get("decided"))
    effected = _count(folded.get("effected"))
    if waiting is None or decided is None or effected is None:
        return _unknown("fold-unknown")

    ineffective = max(0, decided - effected)
    reconcile = _count(folded.get("reconcile_required"))

    oldest_ts = folded.get("oldest_stalled_ts")
    oldest_age = (now_s - float(oldest_ts)) if oldest_ts is not None else None
    if oldest_age is not None and oldest_age < 0:
        oldest_age = 0.0

    debt = {
        "known": True,
        "reason": "",
        "waiting": waiting,
        "decided": decided,
        "effected": effected,
        "ineffective": ineffective,
        "reconcile_required": reconcile,
        "oldest_waiting_ts": oldest_ts,
        "oldest_waiting_age_s": oldest_age,
        "oldest_waiting_days": (int(oldest_age // DAY_S) if oldest_age is not None else None),
        "level": _level(waiting, ineffective, oldest_age),
        "sources": list(_lf.SOURCES),
    }
    debt["text"] = render(debt)
    return debt


def render(debt):
    """جملهٔ کوتاه از dict — تابعِ خالص، بدونِ هیچ I/O.

    رشتهٔ تهی یعنی «چیزی برای گفتن نیست»: بریف نباید خطی بنویسد که بگوید
    هیچ‌چیز معطل نیست. سکوت وقتی درست است که واقعاً بدهی صفر باشد — نه وقتی
    که نمی‌بینیم (آن حالت UNKNOWN است و جمله دارد).
    """
    if not isinstance(debt, dict):
        return ""
    if not debt.get("known"):
        return debt.get("text") or "بدهیِ مالک: نامعلوم."

    waiting = int(debt.get("waiting") or 0)
    ineffective = int(debt.get("ineffective") or 0)
    level = int(debt.get("level") or 0)
    if level <= 0 or (waiting <= 0 and ineffective <= 0):
        return ""

    parts = []
    if waiting > 0:
        age_s = debt.get("oldest_waiting_age_s")
        if age_s is None:
            clause = "%s کارت منتظر" % _fa(waiting)
        elif age_s < DAY_S:
            clause = "%s کارت منتظر، قدیمی‌ترین کمتر از یک روز" % _fa(waiting)
        else:
            clause = "%s کارت منتظر، قدیمی‌ترین %s روز" % (
                _fa(waiting), _fa(int(age_s // DAY_S)))
        parts.append(clause)
    if ineffective > 0:
        parts.append("%s تصمیم بی‌اثر" % _fa(ineffective))

    return "%s: %s." % (_PREFIX.get(level, _PREFIX[1]), "؛ ".join(parts))


def owner_debt_line(state_dir, now=None, _fold=None):
    """`(جمله، dict)` — همان چیزی که گامِ وصل‌کردن روزی صدا خواهد زد.

    امروز عمداً صفر صداکننده دارد؛ فرستادنِ جمله رأیِ مالک است نه مهندسی.
    """
    debt = owner_debt(state_dir, now=now, _fold=_fold)
    return debt.get("text", ""), debt
