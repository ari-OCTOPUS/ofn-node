---
type: project
kind: area
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
owner: آری
risk_level: critical
autonomy_level: read-only
tags: [crypto, investing, etoro]
created: 2026-07-03
updated: 2026-09-07
---

# پروژه: Crypto - etoro

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

مدیریت پرتفوی eToro + تحقیق داده‌محور (lunarcrush/cryptoquant) برای تصمیم بهتر — با حاکمیت سختِ [[04 - Architect System/architect/ARCHITECT_CHARTER|§Trading Autonomy]]: **خرید همیشه انسانی؛ فروش خودکار فقط با قاعده از پیش ثبت‌شده.**

## Current state (شواهد)

- تحلیل‌ها و دیتای موجود: `CELC_deep_briefing_v2_2026-06-16.md`، سه خروجی lunarcrush (June 2026)، `cryptoquant_ai_prompt_2026-06-14`، `spacing_x_expectancy_protocol.md` `[Verified: نوت‌های همین پوشه]`
- اسکرپرها/بات‌ها در `03 - Projects/Mining/Ai bots` (sentinel، QuantumAlphaBot) — .envهایشان به secrets-export منتقل شد؛ تا rotation غیرفعال `[Verified: Phase 0]`
- ثبت پوزیشن ساختاریافته: هنوز وجود ندارد → [[03 - Projects/Crypto - etoro/Portfolio Registry|Portfolio Registry]] (خالی، امروز ساخته شد)
- مسیر اجرای خودکار روی eToro: وجود ندارد `[Assumption — eToro برای retail API معاملاتی نمی‌دهد؛ فعلاً ایجنت فقط هشدار می‌دهد و اجرا دستی است]`

## Assets & resources

حساب eToro `[To measure — مالک]` · دیتاسورس‌ها: LunarCrush + CryptoQuant + Coinalyze (کلیدها در چرخش — [[ROTATION_CHECKLIST]]) · کلیدهای exchange (Bybit/OKX): **off-box، صفر دسترسی LLM** (D-11)

## Active workstreams

1. پر کردن Portfolio Registry با پوزیشن‌های فعلی (مالک). 2. ثبت exit_rules هر پوزیشن. 3. راه‌اندازی مجدد اسکرپرها بعد از rotation.

## KPIs

٪ پوزیشن‌های دارای thesis + invalidation + exit_rules (هدف ۱۰۰٪) · تعداد هشدارهای درست/غلط `[To measure]`

## Agent interface

- **می‌خواند:** این manifest، Portfolio Registry، دیتای اسکرپرها، نوت‌های تحقیق.
- **می‌نویسد:** نوت تحقیق (قالب: [[03 - Projects/Crypto - etoro/Research Template|Research Template]])، فیلدهای evidence، هشدار به تلگرام.
- **verdict انسانی:** هر BUY (هر مبلغ)، هر SELL اختیاری، هر تغییر در exit_rules یا [[03 - Projects/Crypto - etoro/Standing Rules|Standing Rules]].
- **مجاز خودکار (فقط بعد از باز شدن Security Gate + وجود مسیر اجرا):** SELL/TRIM طبق exit_rules ثبت‌شده — با ورودی ledger + نوتیف فوری تلگرام.

## Open blockers

Security Gate بسته (کلیدهای exchange CRITICAL) · رجیستری خالی · مسیر اجرای خودکار ندارد

## Active Context


- بدون منبع زنده؛ فعالیتی در سیزن درآمد ندارد؛ dumpها جدا از سیزن.
- ۳ قدم بعدی: هیچ تا تصمیم مالک.
- باز: آرشیو یا احیا.

## Progress

- 2026-09-07: بدون تغییر.
- 2026-09-07: بدون منبع زنده؛ dumpها جدا از سیزن.
- **۲۰۲۶-۰۸-۰۱ — چه کار می‌کند:** فقط تحلیل‌های موردیِ کهنه و دیتای خامِ روی دیسک (۲۱ asset، ‏`completeness=11%`، ‏۱۰ snapshot). صفر ترید، صفر PII، فقط‌خواندنی.
- **۲۰۲۶-۰۸-۰۱ — چه مانده:** بی‌تغییر — رجیستری، قواعد، اتصالِ زندهٔ دیتا؛ و حالا به‌علاوهٔ یک رأیِ مالک دربارهٔ ادامه یا توقفِ رسمی.
- **۲۰۲۶-۰۸-۰۱ — مشکلات شناخته:** `age_days=46.9` و آخرین تحلیل ۲۰۲۶-۰۶-۱۵ ⇒ هر خروجیِ این پا ساختاراً کهنه است · کلیدها هنوز در انتظارِ چرخش‌اند · `completeness=11%` یعنی حتی دادهٔ موجود هم ناقص است.
- چه کار می‌کند: تحلیل‌های موردی + دیتای خام موجود
- چه مانده: رجیستری، قواعد، اتصال زنده دیتا
- مشکلات شناخته: کلیدها در انتظار چرخش؛ دیتای lunarcrush/cryptoquant از June 2026 کهنه شده

## Next actions

- [ ] ورود پوزیشن‌ها به رجیستری (مالک)
- [ ] exit_rules برای هر پوزیشن
- [ ] چرخش کلیدها → فعال‌سازی مجدد اسکرپرها

## نوت‌های مرتبط

- [[03 - Projects/Crypto - etoro/Portfolio Registry|Portfolio Registry]] · [[03 - Projects/Crypto - etoro/Research Template|Research Template]] · [[03 - Projects/Crypto - etoro/Standing Rules|Standing Rules]]
- [[03 - Projects/Crypto - etoro/Report - Crypto - etoro - Data Stack under AU30|Report - Data Stack under AU30]]
- [[03 - Projects/Crypto - etoro/spacing_x_expectancy_protocol|spacing_x_expectancy_protocol]] · [[03 - Projects/Crypto - etoro/CELC_deep_briefing_v2_2026-06-16|CELC deep briefing v2]]
- [[03 - Projects/Crypto - etoro/Crypto - etoro|لاگ پیام‌های تلگرام]]
