"""
sitecustomize.py — مسلح‌کردنِ `live_state_guard` **قبل از** اولین خطِ هر تست.

چرا این‌طور و نه ویرایشِ فایلِ تست‌ها: از ۵۴۰ فایلِ تست، ۴۴۷ تا `harness` را import
می‌کنند و ~۹۳ تا نمی‌کنند. ویرایشِ ۹۳ فایل «بستنِ شکاف» است؛ این «بستنِ قاعده» است —
مفسر این فایل را در بوت می‌خواند، پس هر پروسهٔ تستی که با این پوشه روی `PYTHONPATH`
اجرا شود مسلح بالا می‌آید، حتی تستی که فردا نوشته شود.

فعال فقط با `OCTOPUS_TEST_LIVE_STATE_GUARD` ِ ناتهی — هیچ پروسهٔ تولیدی این را ست
نمی‌کند، پس ارگانیسمِ زنده هرگز این مسیر را نمی‌بیند.

اگر مسلح‌شدن شکست بخورد **ساکت نمی‌ماند**: هم روی stderr داد می‌زند، هم فایلِ
echo را نمی‌سازد — و runner نبودِ echo را «گارد مسلح نشد» گزارش می‌کند، نه «تمیز».
(غیابِ خطا سبز نیست.)
"""
import os
import sys

_MODE = (os.environ.get("OCTOPUS_TEST_LIVE_STATE_GUARD") or "").strip()

if _MODE:
    try:
        _here = os.path.dirname(os.path.abspath(__file__))
        _tests = os.path.dirname(_here)
        if _tests not in sys.path:
            sys.path.insert(0, _tests)
        import live_state_guard

        _roots = live_state_guard.arm()
        if (os.environ.get("OCTOPUS_TEST_NET_GUARD") or "").strip():
            live_state_guard.arm_network()
        _echo = os.environ.get("OCTOPUS_TEST_ISOLATION_ECHO")
        if _echo:
            # رسیدِ سمتِ خواننده: runner این را می‌خواند تا بداند گارد **واقعاً** بالا آمد.
            with open(_echo, "w", encoding="utf-8") as _f:
                _f.write("armed\t%s\t%s\n" % (live_state_guard._mode, "|".join(_roots)))
    except Exception as _e:  # noqa: BLE001
        sys.stderr.write(
            "LIVE-STATE-GUARD: مسلح نشد (%s: %s) — این اجرا معتبر نیست\n"
            % (type(_e).__name__, _e)
        )
