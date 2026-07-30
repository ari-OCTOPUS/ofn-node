#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_governor_lapsed_deadline.py — «ددلاینِ گذشته فوریتِ ابدی نیست».

یافتهٔ ممیزیِ ۲۰۲۶-۰۷-۲۵ (عدد-به-عدد تأیید شد): سیگمویدِ DEADLINE SHIELD برای
days<0 هیچ انقضایی نداشت، پس یک ددلاینِ فراموش‌شده فشار را تا ابد روی سقف قفل می‌کرد
و ۱۰۰٪ تِرمِ urgencyِ fitness را می‌بلعید (PROJECT_F@2026-07-20 = 0.9975 در برابرِ
PAINTING = 3.9e-216).

این تست دو چیز را هم‌زمان قفل می‌کند:
  · با فلگ خاموش، رفتارِ قبلی **دقیقاً** حفظ شده (بدونِ رگرسیونِ خاموش)
  · با فلگ روشن، ددلاینِ گذشته صفر فوریت می‌دهد ولی سپرِ ددلاینِ **آینده** سالم می‌ماند

hermetic: هیچ‌جا budgets.yamlِ زنده خوانده نمی‌شود — جدولِ ارگانِ ساختگی تزریق می‌شود.
"""
from __future__ import annotations

import datetime as dt
import importlib
import math
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent / "budget"), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_GOV_LAPSED_DEADLINE_HONEST"
FAILURES: list[str] = []
CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(msg)


def _ge(flag_value: "str | None"):
    """governor_epoch را با حالتِ مشخصِ فلگ بارِ نو می‌کند."""
    if flag_value is None:
        os.environ.pop(FLAG, None)
    else:
        os.environ[FLAG] = flag_value
    import governor_epoch as ge
    return importlib.reload(ge)


def _organs(**deadlines):
    """جدولِ ارگانِ ساختگی: نام → روزهای نسبی تا ددلاین (None = بی‌ددلاین)."""
    today = dt.date.today()
    out = {}
    for name, days in deadlines.items():
        if days is None:
            out[name] = {"floor": 1, "human_priority": 1.0}
        elif isinstance(days, str):
            out[name] = {"floor": 1, "human_priority": 1.0, "deadline": days}
        else:
            out[name] = {"floor": 1, "human_priority": 1.0,
                         "deadline": (today + dt.timedelta(days=days)).isoformat()}
    return out


def _sigmoid(days):
    return 1.0 / (1.0 + math.exp((days - 7) / 2.0))


SNAP = {"today": {"usd": 0.0}, "per_organ_alltime_musd": {}, "suspect_zero_total": 0}
W = {"value": 0.30, "urgency": 0.25, "efficiency": 0.20, "human": 0.20, "waste": 0.05}


# ── T1 · فلگ خاموش = رفتارِ قبلی، بدونِ رگرسیونِ خاموش ──────────────────────
def t1_flag_off_preserves_old_behaviour():
    ge = _ge("0")
    for days in (-5, -35, -365, -1):
        prox, ref = ge._deadline_proximity(_organs(LAPSED=days))
        want = _sigmoid(days)
        ck(abs(prox - want) < 1e-9,
           f"T1: فلگ‌خاموش days={days} باید {want:.6f} بدهد، داد {prox:.6f}")
        ck("LAPSED@" in ref, f"T1: refِ ددلاینِ گذشته گم شد (days={days})")
    # عددِ مستندِ یافته: days=-5 → 0.997527
    prox, _ = ge._deadline_proximity(_organs(LAPSED=-5))
    ck(round(prox, 6) == 0.997527, f"T1: عددِ مرجعِ یافته عوض شد: {prox:.6f}")
    # و فشار → epoch را به کف می‌برد
    ck(abs(ge.epoch_length_minutes(prox) - ge.BASE_MIN_DEFAULT / 4.0) < 0.2,
       "T1: فشارِ ~۱ باید epoch را به کفِ base/4 ببرد")


# ── T2 · فلگ روشن = ددلاینِ گذشته صفر فوریت ─────────────────────────────────
def t2_flag_on_zeroes_lapsed():
    ge = _ge("1")
    for days in (-1, -5, -35, -365):
        prox, ref = ge._deadline_proximity(_organs(LAPSED=days))
        ck(prox == 0.0, f"T2: فلگ‌روشن days={days} باید صفر بدهد، داد {prox}")
        ck(ref == "", f"T2: ref باید خالی باشد وقتی همه گذشته‌اند، بود {ref!r}")
    # epoch به پایهٔ آرام برمی‌گردد
    prox, _ = ge._deadline_proximity(_organs(LAPSED=-5))
    ck(ge.epoch_length_minutes(prox) == ge.BASE_MIN_DEFAULT,
       "T2: با فوریتِ صفر، epoch باید پایهٔ ۶۰ دقیقه شود")


# ── T3 · سپرِ ددلاینِ آینده نباید بشکند ─────────────────────────────────────
def t3_future_shield_intact():
    for flag in ("0", "1"):
        ge = _ge(flag)
        for days in (0, 1, 3, 7, 14, 30):
            prox, ref = ge._deadline_proximity(_organs(SOON=days))
            want = _sigmoid(days)
            ck(abs(prox - want) < 1e-9,
               f"T3: فلگ={flag} ددلاینِ آیندهٔ days={days} عوض شد: {prox:.6f} != {want:.6f}")
            ck("SOON@" in ref, f"T3: فلگ={flag} refِ ددلاینِ آینده گم شد")
        # ددلاینِ امروز (days=0) هنوز فوریتِ بالا می‌دهد — مرزِ دقیق
        prox, _ = ge._deadline_proximity(_organs(SOON=0))
        ck(prox > 0.9, f"T3: فلگ={flag} ددلاینِ امروز باید فوریتِ بالا بدهد، داد {prox:.4f}")


# ── T4 · مخلوط: گذشته نادیده، آینده برنده ──────────────────────────────────
def t4_mixed_table():
    ge = _ge("1")
    prox, ref = ge._deadline_proximity(_organs(OLD=-30, SOON=3, NONE=None))
    ck(abs(prox - _sigmoid(3)) < 1e-9, f"T4: باید ددلاینِ ۳روزه برنده شود، داد {prox:.6f}")
    ck("SOON@" in ref, f"T4: ref باید SOON باشد، بود {ref!r}")
    ck("OLD@" not in ref, "T4: ددلاینِ گذشته برندهٔ ref شد")
    # با فلگ خاموش، گذشته می‌برد (چون سیگمویدش ~۱ است) — این همان باگِ مستند است
    ge = _ge("0")
    prox2, ref2 = ge._deadline_proximity(_organs(OLD=-30, SOON=3, NONE=None))
    ck("OLD@" in ref2, "T4: با فلگ خاموش، ددلاینِ گذشته باید برنده باشد (رفتارِ مستند)")
    ck(prox2 > prox, "T4: فشارِ فلگ‌خاموش باید بیشتر از فلگ‌روشن باشد")


# ── T5 · ددلاینِ بدشکل: نه crash، نه فوریت ─────────────────────────────────
def t5_malformed_deadline():
    for flag in ("0", "1"):
        ge = _ge(flag)
        # نکته: "20260720" این‌جا نیست — پایتون ۳.۱۱+ ISOِ فشرده را **معتبر** می‌پارسد
        # (= 2026-07-20)، پس بدشکل نیست و باید مثلِ هر ددلاینِ دیگر رفتار کند.
        for bad in ("", "فردا", "2026-13-45", "None", "2026-07", "07/20/2026", "2026-7-20x"):
            try:
                prox, _ref = ge._deadline_proximity(_organs(BAD=bad))
            except Exception as e:  # noqa: BLE001
                ck(False, f"T5: فلگ={flag} ددلاینِ {bad!r} crash کرد: {type(e).__name__}")
                continue
            ck(prox == 0.0, f"T5: فلگ={flag} ددلاینِ بدشکل {bad!r} فوریت ساخت: {prox}")


# ── T6 · _fitness_dry با _deadline_proximity هم‌داستان است ─────────────────
def t6_fitness_consistent():
    organs = _organs(LAPSED=-5, PAINTING_LIKE=None)
    ge = _ge("0")
    fit_off = ge._fitness_dry(SNAP, organs, W)
    ck(fit_off["LAPSED"] > fit_off["PAINTING_LIKE"],
       "T6: فلگ‌خاموش — ارگانِ ددلاین‌گذشته باید جلو باشد (رفتارِ مستند)")
    gap_off = fit_off["LAPSED"] - fit_off["PAINTING_LIKE"]

    ge = _ge("1")
    fit_on = ge._fitness_dry(SNAP, organs, W)
    gap_on = fit_on["LAPSED"] - fit_on["PAINTING_LIKE"]
    ck(abs(gap_on) < 1e-9,
       f"T6: با human_priorityِ یکسان، فلگ‌روشن باید شکاف را صفر کند، شد {gap_on}")
    ck(gap_off > gap_on, "T6: فلگ‌روشن باید شکاف را کم کند نه زیاد")
    # سهمِ urgency دیگر انحصاری نیست
    ck(fit_on["LAPSED"] < fit_off["LAPSED"],
       "T6: fitnessِ ارگانِ ددلاین‌گذشته باید با فلگِ روشن کم شود")
    # ارگانِ بی‌ددلاین هرگز آسیب نمی‌بیند
    ck(abs(fit_on["PAINTING_LIKE"] - fit_off["PAINTING_LIKE"]) < 1e-9,
       "T6: ارگانِ بی‌ددلاین نباید با فلگ تغییر کند")
    # human_priorityِ عمدیِ مالک محترم می‌ماند
    organs2 = _organs(LAPSED=-5, OTHER=None)
    organs2["LAPSED"]["human_priority"] = 2.0
    fit2 = ge._fitness_dry(SNAP, organs2, W)
    ck(fit2["LAPSED"] > fit2["OTHER"],
       "T6: با فلگِ روشن هم human_priority=2.0 باید برتری بدهد (تنظیمِ عمدیِ مالک)")


# ── T7 · هشدار در هر دو حالت شلیک می‌شود (مالک باید بداند) ─────────────────
def t7_alert_fires_either_way():
    import opslib
    for flag in ("0", "1"):
        ge = _ge(flag)
        seen = []
        orig = getattr(opslib, "alert_throttled", None)
        ck(orig is not None, "T7: opslib.alert_throttled وجود ندارد")
        if orig is None:
            return
        opslib.alert_throttled = lambda items, key=None, window_s=0: seen.append((items, key))
        try:
            ge._deadline_proximity(_organs(LAPSED=-5))
        finally:
            opslib.alert_throttled = orig
        ck(len(seen) == 1, f"T7: فلگ={flag} باید یک هشدار بدهد، داد {len(seen)}")
        if seen:
            txt = " ".join(seen[0][0])
            ck("LAPSED@" in txt, f"T7: فلگ={flag} نامِ ارگان در هشدار نیست")
            ck("مالک" in txt, f"T7: فلگ={flag} هشدار نمی‌گوید تصمیمِ مالک لازم است")
            ck("قفل" in txt if flag == "0" else "صفر" in txt,
               f"T7: فلگ={flag} هشدار وضعیتِ درست را نمی‌گوید")
    # ددلاینِ آینده هشدار نمی‌دهد
    ge = _ge("1")
    seen2 = []
    orig = opslib.alert_throttled
    opslib.alert_throttled = lambda items, key=None, window_s=0: seen2.append(items)
    try:
        ge._deadline_proximity(_organs(SOON=3))
    finally:
        opslib.alert_throttled = orig
    ck(len(seen2) == 0, "T7: ددلاینِ آینده نباید هشدارِ lapsed بدهد")


# ── T8 · فلگ default-off و نامش ثابت ──────────────────────────────────────
def t8_flag_default_off():
    ge = _ge(None)
    ck(ge.LAPSED_FLAG == FLAG, "T8: نامِ فلگ عوض شد")
    ck(ge._lapsed_honest() is False, "T8: فلگ بدونِ env باید خاموش باشد")
    prox, _ = ge._deadline_proximity(_organs(LAPSED=-5))
    ck(prox > 0.99, "T8: پیش‌فرض باید رفتارِ قبلی باشد (سازگاریِ عقب‌رو)")
    for on in ("1", "true", "TRUE", "yes", "on"):
        ck(_ge(on)._lapsed_honest() is True, f"T8: فلگ با {on!r} روشن نشد")
    for off in ("0", "", "no", "off", "خاموش"):
        ck(_ge(off)._lapsed_honest() is False, f"T8: فلگ با {off!r} روشن شد")
    _ge(None)


def main() -> int:
    for fn in (t1_flag_off_preserves_old_behaviour, t2_flag_on_zeroes_lapsed,
               t3_future_shield_intact, t4_mixed_table, t5_malformed_deadline,
               t6_fitness_consistent, t7_alert_fires_either_way, t8_flag_default_off):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            FAILURES.append(f"{fn.__name__}: EXCEPTION {type(e).__name__}: {e}")
    os.environ.pop(FLAG, None)
    if FAILURES:
        print(f"FAIL {len(FAILURES)}/{CHECKS} — governor lapsed deadline")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print(f"PASS {CHECKS}/{CHECKS} — ددلاینِ گذشته فوریتِ ابدی نمی‌سازد (هر دو سمتِ فلگ قفل)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
