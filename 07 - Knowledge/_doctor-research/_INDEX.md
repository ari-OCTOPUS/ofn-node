---
type: moc
status: active
created_by: agent
created: 2026-07-06
updated: 2026-07-06
tags: [doctor, research, moc]
---

# _doctor-research — خط لولهٔ تحقیق دکتر تکاملی

> خروجی خودکارِ تسک زمان‌بند ساعتی **doctor-research-aggressive**. هر ساعت هر ۸ ستون با جستجوی تازه **به‌روزرسانی/عمیق‌تر** می‌شود (نه بازنویسی کور). منبع پرامپت‌ها: [[00 - Inbox/2026-07-06 0410 DOCTOR-RESEARCH-PROMPTS]]. تصمیم‌های باز §۹: [[00 - Inbox/Prompt - دکتر مغز تکاملی (Evolutionary Doctor) 2026-07-05]].

## ۸ ستون → فایل

| # | ستون | تصمیم باز §۹ / شکاف | فایل |
|---|---|---|---|
| P1 | تابع برازندگی | §۹.۲ | [[fitness-function-design]] |
| P2 | ارزیاب مستقل / canary | ستون ۲ + شکاف ۲/۸ | [[canary-adversarial-evaluator]] |
| P3 | مرز invariant↔mutable | §۹.۱ | [[invariant-mutable-boundary]] |
| P4 | جهش‌نامهٔ فعال | شکاف ۴ | [[active-mutation-ledger]] |
| P5 | ریتم حلقهٔ فکری | §۹.۵ + ستون ۳ | [[loop-rhythm-convergence]] |
| P6 | حافظهٔ tiered | شکاف ۱۱/۱۲ + §۶ | [[tiered-memory-consolidation]] |
| P7 | دفاع تزریق | ستون ۳ + §۵.۵ | [[injection-defense-loop]] |
| P8 | بنچمارک شرکت‌ها | — | [[industry-benchmark-selfimprove]] |

## verdict مالک (فقط آری پر می‌کند)

هر نوت خودارزیابیِ ایجنت را دارد؛ verdict نهاییِ «مفید/نه» با توست (خوراک ستون ۲ دکتر):

| فایل | آخرین به‌روزرسانی | verdict آری |
|---|---|---|
| fitness-function-design | 2026-07-06 | ⬜ pending |
| canary-adversarial-evaluator | 2026-07-06 | ⬜ pending |
| invariant-mutable-boundary | 2026-07-06 | ⬜ pending |
| active-mutation-ledger | 2026-07-06 | ⬜ pending |
| loop-rhythm-convergence | 2026-07-06 | ⬜ pending |
| tiered-memory-consolidation | 2026-07-06 | ⬜ pending |
| injection-defense-loop | 2026-07-06 | ⬜ pending |
| industry-benchmark-selfimprove | 2026-07-06 | ⬜ pending |

## لاگ اجرا (append-only)

- 2026-07-06 — پوشه و ایندکس ساخته شد.
- 2026-07-06 06:18 — دور راه‌اندازی (اجرای دستی اول): ۸/۸ نوت ساخته شد؛ مجموع ~۷۴ منبع (P1:10 · P2:10 · P3:5 · P4:8 · P5:10 · P6:15 · P7:7 · P8:9). verdict مالک: pending. تذکر: PoisonedRAG واقعی ۲۰۲۴ است؛ چند preprint تازهٔ ۲۰۲۶ از طریق alphaXiv/hf.co سایت شده‌اند.
- 2026-07-06 06:22 — دور خودکار: 8/8 نوت به‌روز شد؛ ~۹۰ منبع پس از merge (P1:12 · P2:14 · P3:7 · P4:10 · P5:11 · P6:17 · P7:8 · P8:11). همه منابع موجود verify شدند، ~۱۵ منبع تازهٔ ۲۰۲۶ اضافه شد (merge نه بازنویسی).
- 2026-07-06 ~06:34 — سنتز [[00 - Inbox/DOCTOR-SYNTHESIS]] موجود یافت شد (۸/۸ یافته → ۷ تصمیم §۹ نگاشت شده). این اجرا: **NOOP-honest دور دوم** — همهٔ ۸ نوت `updated: 2026-07-06` دارند (هیچ‌کدام >۷ روز کهنه نیست) → طبق قاعده، هیچ تحقیقی انجام نشد. منتظرِ verdictهای آری در انتهای DOCTOR-SYNTHESIS.
- 2026-07-06 06:35 — دور خودکار، **قطع‌شده توسط مالک**: ۸ ایجنت راه افتاد؛ ۲/۸ نوت (P1 fitness، P2 canary) قبل از توقف merge شدند (چند منبع arXiv/OpenReview تازه، کامیت 86fc199)؛ ۶ ایجنت دیگر بدون نوشتن متوقف شدند. سنتز regen نشد (تغییر محتوایی معنادار نبود). نوت‌ها همگی سالم و `updated: 2026-07-06`.
- 2026-07-06 07:xx — دور خودکار (کامل): ۸/۸ نوت merge شد؛ ~۱۱۸ منبع پس از merge (P1:16 · P2:18 · P3:9 · P4:14 · P5:13 · P6:20 · P7:11 · P8:17)؛ ~۲۲ منبع تازهٔ ۲۰۲۶ اضافه (merge نه بازنویسی، هیچ منبع معتبری حذف نشد). سنتز regen شد.
- 2026-07-06 09:29 — دور خودکار (کامل): ۸/۸ نوت merge شد؛ ~۱۶۵ منبع پس از merge (P1:21 · P2:22 · P3:15 · P4:18 · P5:18 · P6:26 · P7:19 · P8:26)؛ ~۴۵ منبع تازهٔ ۲۰۲۶ اضافه (merge نه بازنویسی، هیچ منبع معتبری حذف نشد). سنتز regen شد.
- 2026-07-06 10:22 — دور خودکار (کامل): ۸/۸ نوت merge شد؛ ~۱۸۳ منبع پس از merge (P1:23 · P2:24 · P3:18 · P4:20 · P5:20 · P6:30 · P7:19 · P8:29)؛ ~۱۸ منبع تازهٔ ۲۰۲۶ اضافه (merge نه بازنویسی، هیچ منبع معتبری حذف نشد). سنتز regen شد.
