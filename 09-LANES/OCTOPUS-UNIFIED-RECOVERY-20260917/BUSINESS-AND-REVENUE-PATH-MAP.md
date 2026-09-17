# BUSINESS-AND-REVENUE-PATH-MAP — OCTOPUS 2026-09-17
# lane: OCTOPUS-UNIFIED-RECOVERY-20260917 · شواهد: امروز (API/ssh/tree) + قراردادهای قفل‌شدهٔ والت

## ۱. سه پای درآمد
| پای | موتور/سطح | وضعیت اثبات‌شده |
|---|---|---|
| painting | `packs/lead.yaml` + `web/lead.html` (tracked روی main + زنده روی 138، mtime Sep-2) | فعال؛ فانل ارسال ایمیل لید |
| ziman | ziman-gift.com.au (Shopify، وصل+TLS) | فعال؛ قیمت ×1.5 اجرا شده؛ `paid_order_count=0`؛ **VERIFIED_CASH=0** (گیت L2 لغو شد) |
| studio | پراکنده/کم‌سند | جزئی |

## ۲. اجزای فانل — کجا واقعاً هستن (بررسی امروز: tracked روی main?)
| جزء | روی main? | کجاست | شاهد |
|---|---|---|---|
| موتور لید (pack/lead) | ✅ | main + 138 | ls-tree + ssh |
| `tools/owner_digest.py` | ✅ | main | ls-files |
| `tools/lead_email_extract.py` | ❌ | fix-branch/PR (تلهٔ ۳۲ ایمیل free-text؛ ۳۴→۶۸) | قرارداد فانل 09-17 |
| `state/revenue-drive/revenue_state.py` (شمارنده‌ها) | ❌ | فقط runtime 138 | ssh ls امروز + قرارداد mixed-units |
| `tools/log_outcome.py` (#248) | ❌ | PR#248 (قرمز، notes-based CRM) | API files |
| `migrations/20260914_call_log.sql` (#261) | ❌ | PR#261 (سبز، جدول+seed بدون writer) | API files |
| j-draft generator (#262) | ❌ | PR#262 (تست قرمز، ۲ approve aram-ui) | check-runs امروز |

**قاعدهٔ ثابت این نقشه:** branch-only ≠ landed؛ PR قرمز ≠ آمادهٔ merge؛ جدول بدون writer ≠ CRM.
**گپ ساختاری:** هیچ PRای writer را به جدول call_log وصل نمی‌کند (نیاز به PR سوم).

## ۳. شمارنده‌ها و دام‌های واحد
`sent_today` = پیام‌ها (sent-log.jsonl) ≠ `sent_total` = شمار state پکت‌ها — واحدهای مخلوط بودند، با pre-image rename شدند. تولیدکنندهٔ هر دو: `revenue_state.py` روی 138. `season-meter.json` = رسید تقاضا (تایمر ۶ساعته).

## ۴. PAINT-L5-001 (حقیقت ارسال تاریخی)
REAL + AUTHORIZED (تاریخی): ۵ ردیف effect در بکاپ `ofn-daily/20260901T140621Z` + رأی مالک مکتوب ۰۹-۰۲ («بله اجازه دادم»، ۶ ارسال مجاز).
الان: WAL زندهٔ 138 = **۰ بایت** (دو بار امروز تأیید شد). `value_c=0` — «ایمیل، پول نیست»؛ تناقض والت هنوز open.
مشتری اول: پاسخ Absolute Strata (00:22Z 09-16) → پاسخ data داده شد؛ از آن موقع **هیچ VERIFIED_CASH جدیدی ثبت نشده**.

## ۵. صف PR فانل (وضعیت CI امروز، از check-runs)
| اولویت merge | PR | واقعیت | ریسک |
|---|---|---|---|
| ۱ | #261 | همه سبز؛ فقط گیت review؛ ۲۴ عقب | کم فنی؛ بی‌writer تا PR سوم خنثی |
| ۲ | #262 | تست قرمز (win+ubuntu ساده)؛ ۲ approve | تفکیک قرمزِ جدید/پیش‌موجود |
| ۳ | #260 | قرمز + گیت review؛ ۳۴ عقب | rebase + تفکیک |
| ۴ | #259 | تست سبز ولی fresh-base FAIL؛ ۶۵ عقب | rebase اجباری |
| — | #248/#251/#242/#212/#211/#215 | stale از ۰۹-۰۶..۰۹-۰۹ | فرسودگی/تقادم |

## ۶. قانون درآمد حاکم (یادآوری، عین سند)
ORDER-LAW فصل اصلاحی: **هیچ کار متا قبل از رسید تقاضای روزانه** · سقف متا ۱/روز تا اولین VERIFIED_CASH. هر تصمیم فانل باید با این ترتیب سازگار باشد.
