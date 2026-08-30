"""clock_guard — وقتی ساعتِ دیوار عقب می‌رود، انقضا بی‌معنی می‌شود.

نقطهٔ کورِ ۱۳۵
─────────────
هر جای مسیرِ تأیید که انقضا را می‌سنجد، `time.time()` می‌خواند: کارتِ تلگرام،
تگِ صحتِ کارتِ مالی، و بازسازیِ کارت بعد از restart. `time.time()` **قابلِ
تنظیم** است — با تصحیحِ NTP، با دستِ کاربر، با درستشدنِ ساعتِ سخت‌افزاری بعد از
تعویضِ باتری.

اگر ساعت به عقب بپرد، هر کارتی که منقضی شده بود **دوباره معتبر می‌شود**. یعنی
یک تأییدِ پولیِ سوخته می‌تواند زنده شود.

جالب اینکه خودِ این مخزن این اصل را می‌داند: `c6_trigger.py` صریحاً نوشته
«perf_counter_ns (monotonic، غیرقابلِ تنظیم) — نه time.time که adjustable است».
دانش بود، ولی به مسیرِ پول نرسیده بود.

چرا monotonic به‌تنهایی جواب نمی‌دهد
────────────────────────────────────
`time.monotonic()` بینِ ری‌استارت‌ها معنی ندارد و مبدأش دلخواه است، ولی انقضاها
روی دیسک ذخیره می‌شوند و باید از ری‌استارت جان به در ببرند. پس نمی‌شود صرفاً
جایگزینش کرد.

راهِ حل: **خطِ بیشینه**. بالاترین ساعتی که تا حالا دیده‌ایم روی دیسک می‌ماند.
اگر ساعتِ فعلی به‌طورِ معنادار از آن پایین‌تر باشد، ساعت پرید — و آن‌وقت
انقضا **fail-closed** می‌شود: کارت منقضی حساب می‌شود، نه معتبر.

چرا تحملِ ۱۲۰ ثانیه
───────────────────
تصحیحِ عادیِ NTP در حدِ میلی‌ثانیه تا چند ثانیه است. منطقهٔ زمانی و ساعتِ
تابستانی اصلاً روی epoch اثر ندارند. پس پرشِ بیش از دو دقیقه به عقب، رویدادِ
نادری است که ارزشِ محتاط‌بودن دارد. کمترش نویز است.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

SCHEMA = "clock-guard.v1"
BACKWARD_TOLERANCE_S = 120.0     # پرشِ کمتر از این = نویزِ عادیِ NTP
_WRITE_EVERY_S = 300.0           # خطِ بیشینه هر ۵ دقیقه به‌روز می‌شود، نه هر تماس
_last_write = [0.0]


def _path() -> Path:
    return opslib.STATE_DIR / "clock-highwater.json"


def _read_high() -> float:
    try:
        d = json.loads(_path().read_text("utf-8"))
        return float(d.get("high_water") or 0.0)
    except (OSError, ValueError, TypeError):
        return 0.0


def _write_high(v: float) -> None:
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"schema": SCHEMA, "high_water": float(v)}), "utf-8")
        tmp.replace(p)
    except OSError:
        pass


def check(now: "float | None" = None) -> dict:
    """{now, trusted, why, high_water}. هرگز استثنا نمی‌دهد.

    اثرِ جانبی: خطِ بیشینه را جلو می‌برد (حداکثر هر ۵ دقیقه یک نوشتن)."""
    t = time.time() if now is None else float(now)
    high = _read_high()
    if high <= 0:
        _write_high(t)
        _last_write[0] = t
        return {"now": t, "trusted": True, "why": "اولین مشاهده", "high_water": t}
    if t < high - BACKWARD_TOLERANCE_S:
        return {"now": t, "trusted": False,
                "why": f"ساعت {high - t:.0f} ثانیه به عقب پرید",
                "high_water": high}
    if t > high and (t - _last_write[0]) >= _WRITE_EVERY_S:
        _write_high(t)
        _last_write[0] = t
        high = t
    return {"now": t, "trusted": True, "why": "", "high_water": max(high, t)}


def is_expired(expires_at, now: "float | None" = None) -> "tuple[bool, str]":
    """آیا این مهلت گذشته؟ **fail-closed** روی هر ابهام.

    سه حالتِ «منقضی» که هر سه عمدی‌اند:
      · مهلتِ ناخوانا → منقضی. عددِ خراب مجوز نیست.
      · ساعتِ بی‌اعتماد → منقضی. اگر نمی‌دانیم ساعت چند است، نمی‌توانیم بگوییم
        هنوز وقت هست.
      · مهلت گذشته → منقضی. حالتِ عادی.
    """
    try:
        exp = float(expires_at)
    except (TypeError, ValueError):
        return True, "مهلتِ نامعتبر — fail-closed"
    # ⚠️ `float("nan")` بدونِ خطا ساخته می‌شود و **هر مقایسه‌ای با آن False است**.
    # پس بدونِ این خط، مهلتِ nan نه «گذشته» بود نه «نگذشته» — یعنی عملاً
    # **برای همیشه معتبر**. تستِ خودِ این فایل گرفتش؛ دقیقاً همان fail-openی که
    # قرار بود ببندم، یک لایه پایین‌تر.
    import math as _m
    if not _m.isfinite(exp):
        return True, "مهلتِ غیرعددی (nan/inf) — fail-closed"
    if exp <= 0:
        return True, "مهلتِ صفر — fail-closed"
    c = check(now)
    if not c["trusted"]:
        return True, f"{c['why']} — انقضا قابلِ اتکا نیست، fail-closed"
    return (c["now"] > exp), ("مهلت گذشته" if c["now"] > exp else "")


def card() -> str:
    """کارتِ سلامتِ ساعت — ساکت وقتی چیزی نیست."""
    c = check()
    if c["trusted"]:
        return ("🕐 <b>ساعت سالم است</b>\n"
                "▸ هیچ پرشی به عقب دیده نشده.\n"
                "▸ نکنی: هیچ.")
    return ("🕐 <b>ساعت به عقب پریده</b>\n"
            f"▸ {c['why']}\n"
            "▸ تا وقتی جلو نیامده، هر مهلتی <b>منقضی</b> حساب می‌شود — "
            "چون اگر ندانیم ساعت چند است، نمی‌توانیم بگوییم هنوز وقت هست.\n"
            "▸ نکنی: کارت‌ها منقضی می‌مانند و باید از منو دوباره باز شوند.")


if __name__ == "__main__":   # pragma: no cover
    c = check()
    print(json.dumps({**c, "expired_demo": is_expired(c["now"] - 10)},
                     ensure_ascii=False, indent=1))
