# 03-OWNER-VISIBLE-VERIFY — اتصال Chat Box (فاز U) — 2026-08-12

> برای مالک: مینی‌اپ را کامل ببند، دوباره باز کن، بعد این جدول را بزن.
> هر پاسخ باید «شاهد» داشته باشد یا صادقانه بگوید تأیید نشده.

## ده گفت‌وگوی end-to-end

| # | سؤال | انتظار قابل‌دیدن |
|---|------|------------------|
| 1 | «اختاپوس، درباره من چی می‌دونی؟» | حافظهٔ مالک (اگر MemoryGate ON و hit) با شاهد مسیر فایل؛ وگرنه «recall خالی» صادق |
| 2 | «نقشهٔ کامل خودت رو ساده توضیح بده.» | intro با دو مغز (cortex + business_brain) + «4d وصل نیست» + شاهد runtime (beat/pain) |
| 3 | «Cortex و Business Brain چه فرقی دارند؟» | معماری ساده + data.architecture با path |
| 4 | «معادله BCM چه کاری می‌کند و الان چقدر اختیار دارد؟» | فرمول + معنی ساده + status (TESTED) + «advice-only، فرمان نمی‌دهد» + شاهد bcm.py |
| 5 | «سیگما الان diagnostic است یا روی تصمیم اثر دارد؟ شاهدت چیست؟» | status واقعی σ (ACTIVE در spine اما با برچسب) + شاهد spectral.py |
| 6 | «قلب سوم به کدام فایل و کدام caller وصل است؟» | rhythm.py + caller (spine/arbiter) + «advisory» |
| 7 | «آخرین shadow decision چه بود؟» | shadow_records (شمارش) + applied=false + divergence وضعیت |
| 8 | «چرا این improve را پیشنهاد دادی؟» | rationale + مسیر improve (اگر available) یا صادق «در دسترس نیست» |
| 9 | «این تصمیم من را یادت بماند.» | «پیشنهاد حافظه ساختم؛ هنوز ننوشتم» — MEMORY_CANDIDATE نه commit |
| 10 | «الان چه چیزی را نمی‌دانی یا به آن وصل نیستی؟» | پاسخ صادق (4d وصل نیست · v2 shadow · C2: ADR-036 مستند نشده) |

## پنل «شاهد / معادلات / وضعیت» (collab)

بعد از هر پاسخ collab، بازکنندهٔ collapsible باید نشان دهد:
- `facts` → مسیر فایل/record (اگر recall hit)
- `معادلات مرتبط` → equations_consulted + aggregate_advice + advice_only/decision_effect/apply_effect
- `وضعیت سایه` → records + applied=false
- `پیشنهاد اثر` → policy_gate_status + proposal_created + applied
- `اجزای معماری` → components (اولین ۶)

## Ask mode (vault)

| حالت | انتظار |
|------|--------|
| vault ON + hit | منبع: vault (N نوت) + 📎 منابع vault با path هر نوت |
| vault ON + خالی | vault_empty=true در meta |
| vault OFF | escalate صادق (مغز/همکار) |

## قوانین حقیقت

- هیچ ادعایی بدون شاهد → «تأیید نشده» (نه حدس)
- معادلهٔ بدون implementation هرگز ACTIVE معرفی نشود (matched=false → «پیدا نکردم»)
- effect request → «پیشنهاد ساخته شد / رد شد» — هرگز «انجام شد» (PolicyGate مرجع)
- 4d/Super-Gov → همیشه «وصل نیست»
- `applied=true` فقط با execution receipt واقعی (هیچ‌کدام در chat نیست)

## اگر چیزی درست نبود

در `04-FINAL.md` ثبت می‌شود یا با blocker مستند STOP. بدون جعل شاهد.
