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
updated: 2026-07-29
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

- **2026-07-29 (اسکنِ سطحِ تلگرام) — 🔴 کهنه‌ترین پا.** طبق [[../../OCTOPUS-DOCTOR/50-اسکن‌ها/TG-GROUP-SCAN-PACKAGE-2026-07-29|TG-SCAN-PACKAGE]]، سلولِ crypto در ORGANISM-STATE ‏`live=false` با سنِ **۴۴.۱ روز** است — یعنی تاپیکِ 📈 در گروه دایجستی نشان می‌دهد که دادهٔ پشتش یک ماه‌ونیم تکان نخورده. پای «نمایشی» (digest-only): صفر فرمانِ اختصاصی از تلگرام، فقط pause/resume. این با EdgeClassifier ِ سیم‌نشده و NO_ACTION ِ دائمی هم‌خوان است — پس عددِ کهنه نشانهٔ خرابی نیست، نشانهٔ **نبودِ جریانِ داده** است.
- **2026-07-06 (جلسه ۱۷):** کد پروژه به `_code/` منتقل شد (B1 پلن NONMD-TRIAGE؛ propose→executed با verdict آری). لاگ کامل: `00 - Inbox/nonmd-move-log-2026-07-06.csv`.

- تمرکز فعلی: ساخت رجیستری پوزیشن‌ها با exit_rules
- تغییرات اخیر: 2026-07-03 — ارتقا به manifest فاز ۱ + سه نوت قالب · 2026-07-04 — [[03 - Projects/Crypto - etoro/Report - Crypto - etoro - Data Stack under AU30|Report - Data Stack under AU30]] از Inbox منتقل شد (استک free-API + مهاجرت اسکرپر به API رسمی) · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد
- ۳ قدم بعدی: (۱) مالک: پوزیشن‌های فعلی را وارد رجیستری کند (۲) exit_rules هر پوزیشن (۳) rotation کلیدها → اسکرپرها روشن
- تصمیم‌های باز: آیا مسیر اجرای خودکار اصلاً ساخته شود یا alert-only بماند؟

## Progress

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
