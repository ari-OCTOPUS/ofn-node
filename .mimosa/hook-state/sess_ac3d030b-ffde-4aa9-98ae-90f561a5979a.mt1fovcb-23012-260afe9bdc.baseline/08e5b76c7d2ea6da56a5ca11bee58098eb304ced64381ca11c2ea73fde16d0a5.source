"""reconcile_card.py — یک کارتِ تجمیعی برای بدهیِ `RECONCILE_REQUIRED`.

گامِ ۱۵ ِ UNIFICATION-DESIGN-2026-08-03 (نیمهٔ ساختِ C4).

## چرا این ماژول هیچ‌چیز نمی‌نویسد و هیچ‌چیز نمی‌فرستد

سنجشِ ۰۸-۰۳: ۲۱ ردیفِ `rfc_decision` در وضعیتِ `RECONCILE_REQUIRED` با
`receipt_id=''` و `operation_key=NULL` نشسته‌اند. نامِ آن وضعیت لفظاً یعنی «یک
انسان باید reconcile کند» — و هشت روز به هیچ انسانی نگفته.

سند شرطِ فعال‌سازی را غیرقابلِ چشم‌پوشی اعلام کرده و دلیلش دقیق است:

    زیرسیستمی که مسیرِ اثرِ زنده‌اش ۰ از ۲۱ است، حق ندارد با نوشتنِ کارتی
    دربارهٔ شکستِ خودش، خودش را bootstrap کند.

پس این ماژول فقط **محتوای کارت را می‌سازد**. ساختن امن است؛ نوشتن و فرستادن
رأیِ مالک است. تا وقتی دستِ‌کم یک کارت روی ذخیرهٔ **زنده** به `APPLIED` با
`receipt_id` ناتهی نرسیده باشد، اتوماسیونِ C4 حق شلیک ندارد.

## ناوردی‌ها

  ۱. **صفر نوشتن، صفر شبکه.** خروجی یک dict است، نه یک اثر.
  ۲. **دقیقاً یک کارت** برای N ردیف — نه N کارت. سیلِ ۲۱ کارتی خودش یک نقص است.
  ۳. **content-free** (قاعدهٔ #۷): شمار، سن، و شناسه‌ها. هیچ متنی از خلاصهٔ کارت‌ها،
     هیچ نامی، هیچ توکنی.
  ۴. **ذخیرهٔ ناخوانا ⇒ UNKNOWN، نه «۰ بدهی».** بریفی که وقتی نمی‌بیند بگوید
     «چیزی منتظر نیست»، از سکوت بدتر است.
  ۵. **`state_dir` اجباری است** — پیش‌فرضِ ضمنی یعنی خوردن به ذخیرهٔ زنده.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import provenance as _prov   # noqa: E402

__all__ = ["build_aggregate_card", "RECONCILE_STATE", "CARD_ID"]

RECONCILE_STATE = "RECONCILE_REQUIRED"

#: شناسهٔ ثابت — تجمیع باید idempotent باشد. دو بار ساختن، دو کارت نمی‌سازد.
CARD_ID = "RFC-RECONCILE-BACKLOG"

#: حداکثر شناسه‌ای که در کارت فهرست می‌شود؛ بقیه شمرده می‌شوند. کارتِ تلگرامی
#: سقفِ طول دارد و یک کارتِ بریده بدتر از یک کارتِ خلاصه است (حادثهٔ ۰۸-۰۱).
MAX_IDS = 8


def build_aggregate_card(state_dir, now=None, min_age_s=0.0, _pcr=None):
    """محتوای یک کارتِ تجمیعی. **هیچ نوشتن، هیچ ارسال.**

    برمی‌گرداند:
        None                      اگر بدهی‌ای نیست (صفرِ صادقانه)
        {"unknown": True, ...}    اگر ذخیره ناخوانا/غایب است
        {...card kwargs...}       آمادهٔ پاس‌دادن به `prepare_rfc_card` — که کارِ
                                  مالک است، نه کارِ این ماژول
    """
    if state_dir is None:
        raise ValueError("state_dir is required; an implicit default hits the live store")

    pcr = _pcr
    if pcr is None:
        import pending_card_recovery as pcr   # noqa: PLC0415

    db = pcr._rfc_db_path(state_dir)
    if not Path(db).exists():
        return {"unknown": True, "reason": "rfc-verdicts.db غایب",
                "source": str(db), "count": None}

    try:
        verdicts = pcr.load_rfc_verdicts(state_dir)
    except Exception as exc:   # noqa: BLE001
        return {"unknown": True, "reason": f"ناخوانا:{type(exc).__name__}",
                "source": str(db), "count": None}

    if not isinstance(verdicts, dict):
        return {"unknown": True, "reason": "شکلِ نامنتظره", "source": str(db),
                "count": None}

    stuck = []
    for rid, row in verdicts.items():
        if not isinstance(row, dict):
            continue
        if str(row.get("state") or "").upper() != RECONCILE_STATE:
            continue
        if str(row.get("receipt_id") or ""):
            continue          # رسید دارد ⇒ بدهی نیست
        stuck.append(rid)

    if not stuck:
        return None           # صفرِ صادقانه: بدهی‌ای نیست

    stuck.sort()
    shown = stuck[:MAX_IDS]
    more = len(stuck) - len(shown)

    oldest_ts, oldest_id = None, None
    for rid in stuck:
        ts = _prov.parse_ts((verdicts.get(rid) or {}).get("updated_ts"))
        if ts is not None and (oldest_ts is None or ts < oldest_ts):
            oldest_ts, oldest_id = ts, rid

    age_days = None
    if oldest_ts is not None:
        ref = float(now) if now is not None else _now()
        age_days = max(0.0, (ref - oldest_ts) / 86400.0)
        if min_age_s and (ref - oldest_ts) < float(min_age_s):
            return None       # هنوز به آستانه نرسیده

    ids_txt = "، ".join(shown) + (f" و {more} تای دیگر" if more else "")
    age_txt = f"، قدیمی‌ترین ~{age_days:.0f} روز" if age_days is not None else ""
    summary = (f"{len(stuck)} تصمیمِ ثبت‌شده هرگز اثر نکرد (RECONCILE_REQUIRED با "
               f"رسیدِ تهی){age_txt}. این‌ها رأیِ داده‌شدهٔ خودت‌اند که در پلهٔ "
               f"آخر ماندند — نه کارتِ تازه. شناسه‌ها: {ids_txt}")

    return {
        "rfc_id": CARD_ID,
        "summary": summary,
        "count": len(stuck),
        "rfc_ids": shown,
        "more": more,
        "oldest_ts": oldest_ts,
        "oldest_rfc_id": oldest_id,
        "oldest_age_days": age_days,
        "source": str(db),
        "unknown": False,
    }


def _now():
    import time
    return time.time()
