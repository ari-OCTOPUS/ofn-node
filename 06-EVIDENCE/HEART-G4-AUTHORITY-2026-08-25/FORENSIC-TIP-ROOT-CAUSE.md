---
type: evidence
schema: octopus-genome-tip-forensic/1
status: ROOT_CAUSED_AND_REPAIRED
created: 2026-08-25
method: independent forensic review (read-only) + parallel behavioral monitor + temp-copy rehearsal
---

# ریشهٔ اختلاف ۳۶۲تایی tip — یافتهٔ نهایی

## حکم‌ها

| بررسی | نتیجه |
|---|---|
| بدون truncation | **PASS** — verify() سبز؛ همهٔ prev/hash بازمحاسبه شد؛ دم کامل |
| tip_hash به‌روز | **PASS** — با hash رکورد آخر مطابق؛ فاصلهٔ زمانی ۰٫۱۳s |
| اعتمادپذیری count | **FAIL** — offset ثابت ۳۶۲ در همهٔ snapshotهای git از 2026-08-20 به بعد |
| مجاز بودن reseal | بله — پس از رفع باگ seal_tip و تمرین روی کپی (اجرای زنده: GENOME-TIP-RESEAL-RECEIPT.json) |

## ریشه (دو مسیر مستقل هم‌نتیجه)

**۳۶۲ استثنای خاموش در `_commit_tip_unlocked`** طی 2026-08-16..20 (۴ روز اول عمر tip):`os.replace` زیر قفل گذرای فایل ویندوز (AV/indexer) شکست می‌خورد و `except Exception: pass` آن را می‌بلعید — رکورد اصلی fsync شده بود، sidecar نه. از 2026-08-20 (ری‌استارت مصادف با ac8b3d9) صفر شکست جدید. offset سپس با منطق `prev_n + 1` برای همیشه حفظ شد (تک‌رو و فقط-افزاینده).

## شواهد کلیدی

- معرفی tip: کامیت 278b704 در 2026-08-16 04:26 UTC؛ profile همان روز «tip n=11408» → شروع تقریباً صفر.
- اولین snapshot کامیتی (ac8b3d9، 2026-08-20): file=13127، tip=12765 → offset دقیقاً ۳۶۲.
- WIPهای همان روز: 13204/12842، 13206/12844، 13207/12845، 13208/12846 — همه ۳۶۲.
- رشد پس از آن بی‌نقص: file و tip هر دو +۱۵۳۴ (تا 14661/14299). مانیتور زندهٔ این نشست: delta در ۴+۵ append پیاپی ثابت ۳۶۲ ماند.
- همهٔ writerهای تولیدی از `Ledger.append()` می‌گذرند ( watcher/guardian/doctor/creativity/run/research_loop/backup/llm/organism )؛ reanchor تاریخی (2026-07-31) پیش از وجود tip بود؛ GENOME_DIR به F:\backup پین است — fork نیست.
- باگ دوم: `seal_tip` شمارش واقعی را می‌ساخت ولی `_commit_tip_unlocked` همیشه `prev_n+1` می‌نوشت → ابزار ترمیم خودش ناتوان بود (بازتولید در تست؛ اثبات در تمرین temp اول: seal فقط 14299→14300 کرد).

## ترمیم اجراشده

1. `ledger.py`: `_commit_tip_unlocked(tip_hash, *, n=None)` — شمارش صریح برنده؛ رفتار append دست‌نخورده. `seal_tip` حالا n واقعی را پاس می‌دهد. تست بازتولیدکننده + ۵ سوییت ledger سبز.
2. تمرین روی کپی temp دادهٔ زنده: mismatch→ok و پس از append هم ok.
3. اجرای یک‌باره روی زنده با رسید: 14299→14661، همان head hash، تاریخ لمس نشد.
4. پایداری: پس از ۵ append زنده، 14666=14666 و verify∧verify_tip سبز.

## پیگیری پیشنهادی (مالک)

- هشدار دادن به شکست tip-write به‌جای `except: pass` (کلاسِ ریشه را برای آینده ناپدیدن می‌کند).
