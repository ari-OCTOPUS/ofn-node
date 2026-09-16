# DISCREPANCIES — تضادهای vault ↔ runtime (جدی‌ترین خروجی این اسکن)

هر ردیف: ادعا ↔ واقعیت اندازه‌گیری‌شده، با منبع دو طرف. طبق پروتکل §۷ هیچ‌کدام
یک‌طرفه انتخاب نشده‌اند؛ `resolution: null` یعنی باز.

| # | ادعای vault | واقعیت runtime (07:05–07:12Z) | وضعیت |
|---|---|---|---|
| D-1 | CURRENT-TRUTH: «G22 enforcement LOADED» (بعد از B8) | کد در executor زنده هست؛ اما probe رفتاری ۳۴+ دقیقه هیچ disposition نگرفته — رفتار اثبات‌نشده (F-012) | partial — resolution: null |
| D-2 | «حلقهٔ یادگیری بسته live» (چند سند) | تایمرها زنده‌اند؛ اما fleet-jobs: ۶۱/۹۱ ردیف غیرپایانی — بافر واقعی صف نشسته (F-005) | partial |
| D-3 | گزارش‌های قدیمی‌تر: «B5 real cycle runs» | `budget_allows('B5') = CIRCUIT_BREAKER_OPEN` از 06:38Z (F-011) | open — ریشه‌یابی بدهکار |
| D-4 | CURRENT-STATE.json (بادی-ادپت): «PB-4 NOT_RUN»، «corpus ۶ fact» | PB-4 همان روز IMPROVED 0.75/0.0 شد؛ facts=371 — tracker هرگز به‌روز نشد (F-035) | resolved-by-evidence: tracker کهنه؛ خود tracker باید اصلاح شود |
| D-5 | AGENTS.md → ENTRYPOINT-2026-09-04 کانونیکال | سه نسخهٔ جدیدتر (0906/0907) + هیچ entrypointی لین forensic lane و ORIENTATION.md را ندارد (F-036) | open |
| D-6 | مگاپرامپت این مأموریت: «07-INCIDENTS/ را اسکن کن» | آن دایرکتوری اصلاً وجود ندارد؛ رخدادها در 06-EVIDENCE تخم‌گذاری شده‌اند | open — ساختار vault با سند فرمان drift کرده |
| D-7 | W24-lane (09-13): «G8 deploy blocked by class-B quota» / «5 queued» | G8-021 امروز DEPLOYED+VERIFIED شد؛ گزارش بسته نشده و next-agentها را گمراه می‌کند | resolved-by-evidence; سند کهنه |
| D-8 | G16/G18 در گزارش W24 «open» | هر دو در نشست 09-13/14 اصلاح شدند (mode:patch + 384tok) — مستندات update نشد | resolved-by-evidence; سند کهنه |
| D-9 | 138-WIRING notes: «llama 8081 روی 138» | پروب: DOWN + باینری غایب (09-08)؛ llama-lab واقعی روی 180 اجرا می‌شود | open — سه ادعا، یک آشتی‌ساز لازم (F-082) |
| D-10 | زنجیرهٔ NEXT-ACTIONS بادی-ادپت: B1 (retrieve روی 100) و D1 (مدل روی 193) «BUILD_READY» | هر دو ساخته‌شده‌اند (t3 systemd روی 193؛ ingestion/evaluator زنده) — tracker از ساخت بی‌خبر است | resolved-by-evidence; tracker کهنه |
| D-11 | ROUND31: «۱۲ فایل هم‌نام content-UNVERIFIED» | همچنان UNVERIFIED — pre-incident hash برای احراز وجود ندارد (غیرقابل حل بدون snapshot قبلی) | permanent-open — با دلیل ثبت شد |
| D-12 | VITAL-DATA: «OP-2 transfer منتظر تصمیم مالک» (09-11) | هیچ رسید تصمیمی بعدی نیست؛ وضعیت واقعی نامعلوم | open |

**الگوی غالب (یافتهٔ ساختاری):** بیشتر تضادها از نوع «runtime جلو زده، سند عقب
مانده» است (D-4/D-7/D-8/D-10) — یعنی به‌روزرسانی Obsidian گلوگاه اصلی حافظه است، نه
کار مهندسی. تضادهای از نوع «سند ادعا می‌کند، runtime ندارد» (D-1/D-2/D-3/D-9)
خطرناک‌ترند و همگی در FORGOTTEN-100 رتبه بالا گرفته‌اند.
