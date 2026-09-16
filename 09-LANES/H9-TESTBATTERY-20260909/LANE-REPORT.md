# LANE-REPORT — H9-TESTBATTERY-20260909

```
GOV_VERSION=V8
LADDER=L2
MISSION: OCTOPUS-H9-TESTBATTERY-01
MODE: LOCAL_TESTING / MEASURE_ONLY / NO_NEW_OUTBOUND / NO_LIVE_DAEMON_TOUCH
```

## چه شد (done)
باتری تستِ ۷گانهٔ مکانیزم OQD-H9 (resume-از-آرشیو در `_ops/three_role.py`) اجرا شد — هر تست با
رأیِ صریح و معیارِ قفل‌شدهٔ داخلِ هارنس (`h9tb.py`) پیش از اندازه‌گیری:

| تست | رأی |
|---|---|
| T1 خرابیِ حافظه (سطح-واحد در tmp) | **FAIL** — fail-closed فقط برای OSError؛ JSON خراب/salience رشته‌ای/سطر غیر-dict/UTF-8 بد = کرشِ uncaught |
| T2 یکپارچگی سکه (۱۵۰۰ کلید) | **PASS** — قطعیت ۱۰۰٪، تعادل سراسری و per-mission در باند ۴۰–۶۰ (χ² p=0.148) |
| T3 کیفیت بذر (داورِ قفل‌شده، ۲۰×۴) | **FAIL** — نوتِ هم‌دامنه: shelf/store/checkout = 0.00، liveness = 0.85 (خطِ پایهٔ H9-v2) |
| T4 حساسیت مغز (هارنس director_pick، ۳ جفت) | **PASS** — ۲/۳ flip؛ pick_valid ۳/۳؛ اثرِ لنگر: هر ۳ pickِ بذردار → store_order_check |
| T5 رسایی + انباشت (۳ چرخهٔ واقعی + تحلیل‌گر یک‌بار) | **PASS** — h9 کامل ۳/۳، سکه بازمحاسبه ۳/۳، وضعیت: T=6/R=1 PENDING_CONTINUE |
| T6 رگرسیون (تست‌ها + دوپامین + spine) | **FAIL** — اما هر دو شکست پیش‌موجود و بی‌ربط به H9 (test_freeze: kwarg drift؛ test_event_spine: API drift)؛ چک‌های H9-مرتبط همه سبز |
| T7 کارایی (۶ در برابر ۶ رسید) | **PASS** — نسبتِ مدت 1.20 (<2.0)؛ archive_seed روی انبار واقعی 3.8ms |

گزارش کامل فارسی: `REPORT-H9-TESTBATTERY.md` · نمودار: `chart_coin_balance_seed_quality.png`.

## چه مانده (remaining)
- رأیِ H9 خودش: accrues تا 2026-09-22 یا n≥30/arm (تغییرناپذیر؛ این باتری دستش نزد).
- H9-v2 (هاردنینگ fail-closed + رتبه‌بندِ هم‌دامنه + نسخه‌بندی/washout): فقط پیشنهاد در REPORT —
  اجرا فقط با GO مالک بعد از رأی H9.
- بدهیِ تستیِ قدیمی (بی‌ربط به H9): استابِ test_freeze_semantics و مهاجرتِ test_event_spine به API فعلی.

## چه شکست (failed)
- T1 و T3 و T6 خودِ مکانیزم/وضعیت را FAIL دادند — نگه داشته شد، تست سبز نشد (قانونِ باتری).
- یک باگِ هارنسِ داخلی (case فایلِ نبود T1) وسطِ کار درست شد — نتیجهٔ T1 پس از اصلاح از نو تولید شد.
- راه‌اندازِ دو تستِ T6 اول اشتباه بود (pytest روی اسکریپت‌های harness-style → rc=5)؛ با اجرای
  مستقیمِ اسکریپت اصلاح شد — مستند در `T6_regression.json` (runner per-file).
- معیارِ اولیهٔ دوپامین (delta==3) به آرتیفکتِ مرزِ پنجرهٔ ۲۴ساعته خورد (۳ رسیدِ ۰۹-۰۷ حینِ تست
  از پنجره افتادند)؛ تحلیلِ مستقیمِ پنجره جایگزین و مستند شد — سؤالِ اصلی («اجرای جدید شمرده می‌شود؟») = بله.

## شواهد (evidence paths)
- `F:\backup\09-LANES\H9-TESTBATTERY-20260909\` — h9tb.py، T1..T7 JSON، نمودار، REPORT، همین گزارش
- رسیدهای واقعیِ T5 (۳ سطرِ جدید): `F:\backup\09-LANES\MP-CAPABILITY-GAP-01-20260907\evidence\three-role-receipts.jsonl`
- وضعیتِ تحلیل‌گر (یک‌بار اجرا): `F:\backup\09-LANES\QD-BRIDGE-REALTESTS-20260908\h9\h9_status.json`
- پیش‌ثبتِ دست‌نخورده (sha256_16 = 4938d82e740ef6ce، بازچک شد): `...\QD-BRIDGE-REALTESTS-20260908\h9\study_h9.json`

## مرزها و ایمنی
- دیمنِ زنده، فلگ‌ها، gates.json، آستانه‌های H9، پیش‌ثبت: دست‌نخورده. صفر تغییرِ کد در `_ops`
  (فقط این پوشهٔ جدید + ۳ سطرِ رسیدِ واقعی + خروجیِ تحلیل‌گر).
- خرابی‌های T1 فقط روی کپی‌های tmp سطح-واحد؛ صفر سطرِ ساختگی در رسیدهای واقعی (قانون طلایی).
- هیچ مجوزِ production/خودمختاری از این باتری بیرون نمی‌آید (V8/L2). تراکنشِ پولی: صفر (مغزِ محلی $0).

## Rollback
`git revert <کامیتِ H9-TESTBATTERY>` — تک‌کامیت. (۳ سطرِ رسیدِ T5 دادهٔ واقعیِ آزمون‌اند؛
حذفِ آن‌ها تصمیمِ مالک است، چون زنجیرهٔ رسید سطر از دست نمی‌دهد.)
