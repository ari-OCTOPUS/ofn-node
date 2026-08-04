#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_vitals — سه سنجه‌ای که مینی‌اپ کورشان بود.

    زمینه: راهنمای طراحِ ۰۸-۰۴ سیزده متریک شمرد. سنجشِ کد نشان داد پنج‌تای‌شان
    در `/api/state` نیستند — ولی **سه‌تا از آن پنج‌تا از قبل روی دیسک بودند**
    و فقط allowlist ِ `get_miniapp_state` دورشان می‌ریخت. این تست همان سه را
    قفل می‌کند، و مهم‌تر: قفل می‌کند که عددِ بودجه **صادق** باشد.

    ادعاهای زیرِ آزمون (هرکدام با جهشِ کُشنده روی لنگرِ یکتا سنجیده شد):
      · germline_lag_h / germline_alert / recall_reach واقعاً عبور می‌کنند.
      · مخرجِ حلقه از `cardiac.BeatBudget._cap()` می‌آید، نه از عددِ کوبیده —
        پس `/heart set cap` ِ مالک همین‌جا هم اثر می‌کند.
      · **گاردِ کهنگی**: پروندهٔ بودجه `date` دارد؛ اگر مالِ امروز نباشد،
        درصد `None` می‌شود. درسِ ۰۸-۰۴: عددِ تجمعی تازگی را پنهان می‌کند و
        حلقهٔ ۷۰٪ ِ دیروز از «حلقه نداشتن» بدتر است.
      · پروندهٔ غایب ⇒ status=unknown، نه صفرِ جعلیِ خوش‌ظاهر.
      · درصد در ۱۰۰ کلیپ می‌شود و `depleted` روی دادهٔ کهنه ادعا نمی‌شود.

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("miniapp-vitals")

import miniapp_state as ms  # noqa: E402

TODAY = time.strftime("%Y-%m-%d")
YESTERDAY = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))


def _pin(budget: "dict | None", cap: "int | None" = None,
         organism: "dict | None" = None) -> Path:
    """STATE_DIR را به یک پوشهٔ تازه پین کن و پرونده‌ها را بچین.

    ⚠️ پین روی `ms.STATE_DIR` است چون هر دو تابع همان global را در **زمانِ
    فراخوان** می‌خوانند. اگر به‌جایش فیکسچر کنارِ درختِ زنده می‌گذاشتم، تست
    پروندهٔ بودجهٔ واقعیِ ارگانیسم را می‌خواند و رقم هر روز عوض می‌شد.
    """
    d = Path(tempfile.mkdtemp(prefix="vitals-"))
    if budget is not None:
        (d / "cardiac-budget.json").write_text(json.dumps(budget), encoding="utf-8")
    if cap is not None:
        (d / "pulse").mkdir(exist_ok=True)
        (d / "pulse" / "heart-setpoint-latest.json").write_text(
            json.dumps({"daily_beat_cap": cap}), encoding="utf-8")
    if organism is not None:
        (d / "ORGANISM-STATE.json").write_text(json.dumps(organism), encoding="utf-8")
    ms.STATE_DIR = d
    return d


def t_three_metrics_reach_the_cockpit():
    """سه کلیدی که allowlist دورشان می‌ریخت، حالا در خروجی‌اند."""
    _pin({"date": TODAY, "spent": 1, "resting": 0}, cap=100, organism={
        "germline_lag_h": 0.03, "germline_alert": "ok",
        "recall_reach": {"events": 57, "reach_median": 2.0},
    })
    out = ms.get_miniapp_state()
    assert out.get("germline_lag_h") == 0.03, f"germline_lag_h نرسید: {out.get('germline_lag_h')!r}"
    assert out.get("germline_alert") == "ok", f"germline_alert نرسید: {out.get('germline_alert')!r}"
    rr = out.get("recall_reach")
    assert isinstance(rr, dict) and rr.get("events") == 57, f"recall_reach نرسید: {rr!r}"


def t_cap_comes_from_the_heart_setpoint():
    """مخرج از setpointِ قلب می‌آید — نه از عددِ کوبیده.

    اگر کسی روزی `cap` را hard-code کند، این تست می‌میرد: سقف را ۵۰۰
    می‌گذارم و خرج را ۲۵۰، پس تنها درصدِ درست ۵۰٪ است. با پیش‌فرضِ ۲۸۸
    می‌شد ۸۶.۸ و با ۲۰۰۰ می‌شد ۱۲.۵ — هر سه از هم دورند.
    """
    _pin({"date": TODAY, "spent": 250, "resting": 3}, cap=500)
    c = ms._cardiac_vitals()
    assert c["cap"] == 500, f"سقف از setpoint خوانده نشد: {c['cap']!r}"
    assert c["pct"] == 50.0, f"درصد غلط: {c['pct']!r}"


def t_stale_budget_yields_no_percentage():
    """پروندهٔ دیروز ⇒ stale و درصدِ None. رقمِ غلط از نبودِ رقم بدتر است."""
    _pin({"date": YESTERDAY, "spent": 1396, "resting": 0}, cap=2000)
    c = ms._cardiac_vitals()
    assert c["stale"] is True, "دادهٔ دیروز کهنه علامت نخورد"
    assert c["pct"] is None, f"روی دادهٔ کهنه درصد ساخت: {c['pct']!r}"
    assert c["depleted"] is False, "روی دادهٔ کهنه ادعای تخلیه کرد"


def t_fresh_budget_is_not_marked_stale():
    """قرینهٔ بالایی — وگرنه گاردی که همیشه stale بگوید هم پاس می‌شد."""
    _pin({"date": TODAY, "spent": 10, "resting": 0}, cap=100)
    c = ms._cardiac_vitals()
    assert c["stale"] is False, "دادهٔ امروز اشتباهاً کهنه شد"
    assert c["pct"] == 10.0, f"درصدِ دادهٔ تازه غلط: {c['pct']!r}"


def t_missing_file_is_unknown_not_zero():
    """پرونده نیست ⇒ unknown. صفرِ جعلی یعنی «هیچ خرجی نشده» که دروغ است."""
    _pin(None, cap=100)
    c = ms._cardiac_vitals()
    assert c["status"] == "unknown", f"غیبت را ok گزارش کرد: {c!r}"
    assert c.get("spent") is None, f"برای پروندهٔ غایب عدد ساخت: {c.get('spent')!r}"


def t_percentage_clamps_and_depletion_is_flagged():
    """خرجِ بیش از سقف ⇒ ۱۰۰٪ (نه ۱۴۰٪) و depleted=True."""
    _pin({"date": TODAY, "spent": 140, "resting": 5}, cap=100)
    c = ms._cardiac_vitals()
    assert c["pct"] == 100.0, f"درصد کلیپ نشد: {c['pct']!r}"
    assert c["depleted"] is True, "تخلیه علامت نخورد"


def t_state_carries_cardiac_block():
    """بلوکِ cardiac واقعاً به `/api/state` می‌رسد، نه فقط به تابعِ داخلی."""
    _pin({"date": TODAY, "spent": 7, "resting": 0}, cap=70, organism={"beat": 1})
    out = ms.get_miniapp_state()
    c = out.get("cardiac")
    assert isinstance(c, dict), f"cardiac در خروجی نیست: {type(c).__name__}"
    assert c.get("pct") == 10.0, f"cardiac.pct غلط: {c.get('pct')!r}"


CHECKS = [(n, f) for n, f in sorted(globals().items())
          if n.startswith("t_") and callable(f)]

if __name__ == "__main__":
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_vitals: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
