# LIVE-4 GO/NO-GO — وضعیت پرفلایت غیرزنده (2026-08-19)
① FX رکورد مالک: **PENDING** — قالب FX-RECORD-TEMPLATE.json آماده؛ اعتبارسنج (۵فیلد + ≤24h + hash) تست‌شده؛ بدون آن paid fallback=BLOCKED
② COST-OBS-1 production smoke: **PASS-synthetic** (۱۱/۱۱ تست + import + رسید سنتزی REPORTED/UNOBSERVABLE از مسیر پروموت‌شده؛ اولین رسید production واقعی در همان لحظهٔ اولین فراخوانیِ مجاز صادر می‌شود)
③ Allowlist صریح provider/model: **PASS** — fugu (فقط ≤500 کاراکتر) / deepseek (فقط fallback مجاز با FX معتبر) — در TAXONOMY منجمد
④ BASELINE-L3 + قواعد واجدیت + کد امتیازدهی منجمد و هش‌شده: **PASS** — BASELINE-L3.json(.sha256) + TASK-CLASS-TAXONOMY.json(.sha256) + هش learning_evaluator و live4_harness
⑤ داور کور + تصادفی‌سازی A/B: **PASS** — 8/8 تست پرفلایت (تصادفی‌سازی قطعی با seed + پوشش هر دو موقعیت + نگاشت کور + خروجی ناخوانا=None)
⑥ F3: **PASS-by-mechanical-exclusion** — نویسنده‌ها وصله شدند (INC1 + برچسب SYSTEM_DETERMINISTIC_RULE که هرگز در کالیبراسیون LLM امتیاز نمی‌خورد)؛ رکوردهای ناسازگار به‌صارت مکانیکی از واجدیت خارج می‌شوند (coverage_report)؛ fail-closed در سطح insert = کارت F3-full جدا
نتیجه: ۵/۶ PASS + ① منتظر پنج مقدار FX از مالک → با رسیدن FX-RECORD.json معتبر، GO.
