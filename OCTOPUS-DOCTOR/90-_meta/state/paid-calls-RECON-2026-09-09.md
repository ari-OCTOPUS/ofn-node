# RECON — paid-calls.jsonl (OP-2 · MP-OPERATORS-01 · 2026-09-09)

قرارداد: هیچ ردیفی از لجر بازنویسی/حذف نشده. این یادداشت آشتیِ additive است.

## نویسنده (پیدا‌شده)
`OCTOPUS-DOCTOR/doctor/fugu.py` — `Quota.charge()` + `Fugu._receipt()`.
جست‌وجوهای قبلی (_ops / F:\ofn-node / ~/ofn روی 138) این مسیر را ندیده بودند
چون خودِ `OCTOPUS-DOCTOR/` grep نشده بود. اجرای روزانه ~07:01–07:03 local
(تسک زمان‌بندیِ دکتر؛ امروز 2026-09-09T07:07:59 هم دیدم).

## ردیف‌های تاریخیِ خلاف‌واقع
| ts (local) | cost_usd | spent_usd_today ثبت‌شده | درست |
|---|---|---|---|
| 2026-09-06T07:01:56 | 0.065455 | 0.0 | 0.065455 |
| 2026-09-07T07:01:28 | 0.108665 | 0.0 | 0.108665 |

کم‌شمارِ جمعی: **0.174120 USD** — هر دو روز only-call-of-day بودند
(quota_used=1) پس کم‌شماریِ سقفِ آن روزها هم دقیقاً به همین مقدار بود.
علت: `_save` ساکت OSError می‌بلعید (قفل گذرای فایل) و `_receipt` از دیسکِ
stale می‌خواند. وصله: `charge()` مقدارِ بعد از کسر را برمی‌گرداند؛ رسید از
مقدارِ صریح می‌سازد؛ دو شکستِ نوشتن ⇒ `fugu-quota-savefail.jsonl`.

## ردیفِ null (خلاف‌واقع **نیست**)
`2026-07-29T16:56:19 · model=fugu · cost_usd=null` — به‌موجب طراحی:
`PRICING["fugu"] = {in: None, out: None}  # [UNKNOWN]` و `charge(None)` به
`unpriced_calls` می‌رود، نه به spent_usd. «ادعای صفر ممنوع» رعایت شده.

## شواهد
- تست واحد (پس از وصله): `OCTOPUS-DOCTOR/doctor/tests/test_fugu_quota_honesty.py` — 5/5 سبز
- همان تست روی کدِ pre-patch (tmp): TypeError — `charge` مقدار برنمی‌گرداند
- رگرسیون: `doctor/tests/test_doctor.py` — 163 سبز / 5 قرمز = baselineِ
  pre-existing (همهٔ قرمزها vault-content، هیچ‌کدام fugu-related)
- بازتولید زندهٔ نبودِ باگ امروز: ردیف 2026-09-09T07:07:59 درست
  (cost=spent=0.20457؛ وصله پیش از اجرای امروز اعمال نشده بود — این ردیف
  کدِ قدیمی را نشان می‌دهد که در شرایطِ عادی درست کار می‌کند؛ باگ گذرا بود)

rollback: `git checkout -- OCTOPUS-DOCTOR/doctor/fugu.py` (تست مستقل باقی می‌ماند)
