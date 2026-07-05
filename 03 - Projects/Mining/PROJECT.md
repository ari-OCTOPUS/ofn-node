---
type: project
kind: area
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
owner: آری
risk_level: medium
autonomy_level: read-only
tags: [mining, crypto, orange-pi, esp32]
created: 2026-07-03
updated: 2026-07-06
---

# پروژه: Mining

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

شکار کوین‌های نوظهور CPU/ARM-پذیر با ناوگان کوچک (Orange Pi 5 Pro + ESP32) — آزمایش بلندمدت با معیار مرگ **survival-based** (D2)، نه payback. **tenant #3** (D-26)؛ برای architect فقط INFORM — execution مالی HARD_STOP (D-10).

## Current state (شواهد)

- کد بات‌ها: `Ai bots/` (sentinel، QuantumAlphaBot، deploy) و `Robo-data/` — .envها به secrets-export منتقل شد؛ توکن‌های hardcode در config.py/setup_main.sh redact شدند `[Verified: Phase 0]`
- `Mining-1/Hcash/config.env` (۳۶ متغیر نود) منتقل شد — pointer جایش است `[Verified]`
- کیف پول Monero: seed در چرخش — [[ROTATION_CHECKLIST]] ردیف ۱ `[Verified]`
- معماری بات‌ها: `Ai bots/ARCHITECTURE.md` `[Verified: وجود فایل]` · ماینرها (nanominer/xmrig/gminer) در `_Archive`
- سود/هزینه واقعی: `[To measure]` — هیچ عدد profitability تأییدشده‌ای ثبت نشده

## Assets & resources

۶ نود (طبق config قدیمی Hcash) `[Assumption — رجیستری تکمیل شود]` · Orange Pi 5 Pro + ESP32 · برق: قید ساختاری **<$0.05/kWh یا خورشیدی** — بالاتر از این، ماینینگ متوقف

## Active workstreams

1. تکمیل [[03 - Projects/Mining/Hardware Registry & Runbook|رجیستری سخت‌افزار]] (مالک). 2. اولین کوین با [[03 - Projects/Mining/Coin Scouting Framework|چارچوب شکار کوین]]. 3. راه‌اندازی مجدد بات‌ها بعد از rotation.

## KPIs

نود فعال/کل `[To measure]` · کوین‌های تحت آزمایش · uptime ناوگان `[To measure]` — payback و نقدشوندگی = فیلد اطلاعاتی، **نه** معیار قطع (D2)

## Agent interface

- **می‌خواند:** این manifest، رجیستری، لاگ آزمایش کوین‌ها، دیتای عمومی شبکه‌ها.
- **می‌نویسد:** گزارش death-watch، پیشنهاد کوین جدید (draft)، هشدار برق/آپتایم.
- **verdict انسانی:** هر خرید/فروش/برداشت، هر deploy روی نود، شروع/توقف هر آزمایش.
- **ممنوع:** SSH مستقیم به نودها (D-20 — فقط مسیر repo+deploy gate)؛ دسترسی به کیف پول (D-11).
- **Security Gate:** read-only تا بسته شدن CRITICALها.

## Open blockers

seed کیف پول در انتظار چرخش · رجیستری خالی · بات‌ها بدون .env (به‌عمد، تا rotation)

## Active Context

- تمرکز فعلی: بازسازی پایه (رجیستری + چارچوب) پیش از آزمایش کوین بعدی
- تغییرات اخیر: 2026-07-03 — Phase 0 (انتقال secretها) + ارتقا به manifest فاز ۱ + دو نوت چارچوب · 2026-07-04 — [[03 - Projects/Mining/04 - Research/SCOUT-B|SCOUT-B]] (تحقیق Track B) از Inbox به `04 - Research` منتقل شد · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد
- ۳ قدم بعدی: (۱) چرخش wallet/کلیدها (مالک) (۲) تکمیل رجیستری نودها (۳) انتخاب کوین #۱ با چارچوب
- تصمیم‌های باز: کدام نودها هنوز روشن/سالم‌اند؟

## Progress

- چه کار می‌کند: کد بات‌ها موجود (خاموش)؛ چارچوب‌ها تعریف شد
- چه مانده: rotation، رجیستری واقعی، اولین آزمایش ثبت‌شده
- مشکلات شناخته: هیچ عدد profitability معتبری نداریم؛ وضعیت فیزیکی نودها نامشخص

## Next actions

- [ ] چرخش Monero seed + کلیدها (مالک)
- [ ] تکمیل رجیستری سخت‌افزار
- [ ] آزمایش کوین #۱ طبق چارچوب

## نوت‌های مرتبط

- [[03 - Projects/Mining/Hardware Registry & Runbook|Hardware Registry & Runbook]] · [[03 - Projects/Mining/Coin Scouting Framework|Coin Scouting Framework]]
- [[03 - Projects/Mining/Mining|لاگ پیام‌های تلگرام — Mining]] · [[03 - Projects/Mining/Ai bots/ARCHITECTURE|Ai bots ARCHITECTURE]]
- [[03 - Projects/Mining/04 - Research/SCOUT-B|SCOUT-B (Track B)]]
