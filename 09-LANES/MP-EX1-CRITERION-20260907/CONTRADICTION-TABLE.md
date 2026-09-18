---
type: report
status: open
tags: [octopus, ex1, contradiction]
updated: 2026-09-07
---

# شرط متناقض EX1 — متن قرارداد کنار شاهد

قرارداد: `C:/Users/Armin/Downloads/MEGAPROMPT-OCTOPUS-v3-EXECUTABLE-2026-09-07.md`  
نسخهٔ داخل سند: `v3.0 · EXECUTABLE` · id=`MP-EXEC-ORDER-v3`  
SHA256 این نشست: `ca736a4724ddac884fd39108dc6089e907fba6f1439ba61ff71cc7681cdaa4e3`  
Verifier و آستانه برای سبز شدن تغییر نکرد.

نتیجهٔ قرارداد v3.0 حفظ می‌شود: **NOT_PASSED**. log `H-F` / `H-G`.

| id | متن دقیق شرط | محل | شاهد مخالف | طبقه |
|---|---|---|---|---|
| EX1-T1 | `expect: status=OK · هر دو رکورد موجود · calib_tail و reason_code عیناً مطابق گزارش` | v3.0 §EX-1 خطوط ۱۱۴–۱۱۵ | هر دو رکورد موجودند؛ `calib_tail` روی ۱۹۴۲۹۸ مطابق است؛ کلید `reason_code` در هر دو ردیف `false` است؛ کلید موجود `reason` است | قرارداد نام کلید را می‌خواهد که writer ننوشته |
| EX1-T2 | `+ سه فیلد اجباری در هر رکورد: loaded_source_revision · consumer_path · read_receipt_id` | v3.0 §EX-1 خط ۱۱۵ | هر شش خانه در live و prefix = false (`LIVE-READBACK.json` + log `H-D`) | قرارداد فیلد داخل‌ردیف می‌خواهد؛ schema نویسنده آن کلیدها را ندارد |
| EX1-T3 | `verify: … سپس python -m tools.verify_chain --from-zero روی همان بازه` و `expect: status=OK` | v3.0 §EX-1 خطوط ۱۱۲–۱۱۴ | ابزار در رسید قبلی E0؛ این نشست سورس را دوباره اسکن نکرد. جانشین اجراشده: seq-monotonic روی بایت مشاهده‌شده، نه همان ابزار | قرارداد ابزاری را می‌نامد که پیاده‌سازی‌اش پیدا نشد |
| EX1-T4 | `on_fail: کل lane متوقف. اگر پایهٔ دو رسید سست باشد، شش گام بعدی روی هوا بنا می‌شوند.` | v3.0 §EX-1 خط ۱۱۹ | lane اجرایی قبلی با سه تناقض باز ادامه داد و `BLOCKERS=none` نوشت (`MP-EXEC-EX1-EX2-20260907/LANE-REPORT.md`) | انحراف اجرایی از همان قرارداد؛ این lane آن را PASS نمی‌کند |
| EX1-T5 | `22:30Z → standing_go_minted seq 194329 با mint_evidence.calib_tail` | v3.0 §۱.۱ جدول ۱.۱ | `mint_evidence` و `calib_tail` روی ۱۹۴۳۲۹ در snapshot غایب‌اند (log `H-C`) | ادعا در جدول وضعیت (REPORTED) از ردیف خام قوی‌تر است |

شاهد سطح‌رسید (`EX1-VERIFICATION-RECEIPT.json` فیلدهای `read_receipt_id` / `consumer_path` / `loaded_source_revision`) مخالف EX1-T2 نیست؛ مال خواندن ۰۹-۰۷ است، نه کلید داخل ردیف.

`resolution` همهٔ ردیف‌ها: `null` · `status: open` تحت قرارداد v3.0.

## پیاده‌سازی در برابر قرارداد

| شکاف | اگر ایراد پیاده‌سازی باشد | اگر ایراد قرارداد باشد |
|---|---|---|
| EX1-T1 `reason` در برابر `reason_code` | writerهای بعدی `reason_code` enum بنویسند؛ ردیف قدیم دست نخورد؛ تست: کلید روی ردیف تازه اجباری است | v3.1 بپذیرد که `reason` تاریخی معادل `reason_code` نیست و فقط ردیف‌های پس از تاریخ قطع را بسنجد |
| EX1-T2 trio | `audit_append` بعدی سه فیلد را در همان JSON تصمیم بنویسد؛ تست منفی: ردیف بدون trio رد شود | v3.1 trio را برای تصمیم‌های پس از قطع اجباری کند؛ تاریخی = UNKNOWN |
| EX1-T3 verifier | پیاده‌سازی `tools.verify_chain --from-zero` یا نام‌بردن ابزار واقعی در دستور جدید | v3.1 صریحاً seq-monotonic را verifier ضعیف‌تر بنامد؛ v3.0 همچنان NOT_PASSED |
| EX1-T5 mint_evidence | mintهای بعدی `mint_evidence.calib_tail` بنویسند؛ backfill ممنوع | §۱.۱ را به «REPORTED، در ردیف خام نبود» تصحیح نسخه‌بندی‌شده کن |

هیچ‌کدام از ستون‌های بالا در این lane اجرا نشد. پیش‌نویس نسخه‌بندی: `EX1-ACCEPTANCE-v3.1-DRAFT.md` — **adopt نشده**.
