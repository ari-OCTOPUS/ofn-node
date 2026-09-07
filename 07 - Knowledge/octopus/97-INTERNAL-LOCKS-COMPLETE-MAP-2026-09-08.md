---
type: knowledge
status: active
tags: [octopus, locks, gates, architecture, audit, governance]
created: 2026-09-08
updated: 2026-09-08
created_by: agent
sources:
  - "AGENTS.md §4 (blocked gates list)"
  - "board138 /home/ari/ofn/data/gates.json (v0.3)"
  - ".cursor/hooks/guard_flags.py (enforcement)"
  - "GOV-V8-REVENUE-IGNITION-2026-09-05.md"
---

# ۹۷ — نقشهٔ کامل قفل‌های درونی اختاپوس: ۳۴ قفل، ۷ طبقه، ۳ تناقض بزرگ (2026-09-08)

> 📌 این نوت جزئیات کامل قفل‌هاست. خلاصهٔ اجرایی + وضعیت عملگری + تصمیم‌های باز: [[01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08|داده‌های حیاتی]] · پاسخ‌های مالک و گام‌ها: [[01 - Dashboard/UNLOCK-PLAN-2026-09-08|پلن باز کردن قفل‌ها]]

## طبقه A — سه قفل مطلق GOV-V8 (هیچ‌کس باز نمی‌کند، حتی مالک)

| # | قفل | متن | وضعیت |
|---|---|---|---|
| 1 | **چاپ secret** | هیچ توکن/کلید/سیید/کیف پول چاپ، ارسال، کپی یا commit نمی‌شود | 🔒 بسته — load-bearing |
| 2 | **زنجیرهٔ رسید** | هیچ entry حذف یا بازنویسی نمی‌شود | 🔒 بسته — load-bearing |
| 3 | **PASS بی‌رسید** | هیچ PASS/LIVE بدون رسید هم‌دامنه اعلام نمی‌شود | 🔒 بسته — load-bearing |

## طبقه B — گیت‌های gates.json روی برد ۱۳۸ (مالک می‌تواند باز کند)

| # | گیت | state | agent_may_open | چه محافظتی |
|---|---|---|---|---|
| 4 | `secret_rotation` | closed_until_owner_rotates | false | جلوگیری از تغییر secretها قبل از چرخش کامل |
| 5 | `partner_precondition` | closed_until_owner_records | false | شرط همکار ثبت نشده — کدام همکار؟ مبهم |
| 6 | `wire_publish` | off_by_default | false | انتشار بیرونی — **کد مصرف‌کننده ندارد** (grep در kernel = خالی) |
| 7 | `owner_release` | requires_two_step | false | تأیید دومرحله‌ای مالک برای آزادسازی |
| 8 | `kill_switch` | must_block_when_active | false | اضطراری — فایل HALT-ALL |

## طبقه C — گیت‌های AGENTS.md (بدون تعریف در gates.json)

| # | گیت | کجا تعریف | وضعیت | تحلیل |
|---|---|---|---|---|
| 9 | `D1` (= D1_EXECUTION_AUTHORIZED) | guard_flags.py:9 | 🔒 بسته | **تناقض**: ارگانیسم در production اجرا می‌شود ولی D1 هنوز بسته است — یا D1 تعریف دیگری دارد یا بی‌اثر است |
| 10 | `D7` (= D7_AUTHORIZED) | فقط AGENTS.md | 🔒 بسته | تعریف پیدا نشد — احتمالاً مجوز اثر بیرونی |
| 11 | `OWNER_KEY` | guard_flags.py:9 | 🔒 بسته | کلید خصوصی مالک — برای عملیات حساس |
| 12 | `miner_isolation` | guard_flags.py:9 | 🔒 بسته | **موت است** — mining PARKED، این گیت چیزی محافظت نمی‌کند |

## طبقه D — ممنوعه‌های flag (enforcement = guard_flags.py hook)

| # | ممنوعه | وضعیت فعلی | تناقض |
|---|---|---|---|
| 13 | `OCTOPUS_WIRE_*` نباید روشن شود | **۱۹۵ عدد روشن است!** | ⚠️ **بزرگ‌ترین تناقض معماری** — hook جلوی روشن‌کردن در کد را می‌گیرد ولی ارگانیسم خودش ۱۹۵ تا را در OCTOPUS-flags.cmd روشن دارد |
| 14 | `OFN_WIRE_*` | وضعیت نامشخص | احتمالاً مشابه ۱۳ |
| 15 | `OBSERVATORY` | نامشخص | چه چیزی را gate می‌کند؟ تعریف گم شده |
| 16 | `CORTEX_HYPOTHESIS` | نامشخص | چه چیزی را gate می‌کند؟ |
| 17 | `auto_email` | 🔒 بسته | ایمیل مسیر ارتباطی نیست — تلگرام جایگزین شده؛ گیت moot |
| 18 | `PRODUCTION` | 🔒 بسته (hook) | **تناقض**: سیستم در production است ولی PRODUCTION flag بسته |

## طبقه E — قفل‌های ladder (GOV-V8)

| # | قفل | شرط باز شدن | وضعیت |
|---|---|---|---|
| 19 | L2 (فعلی) | OWNER-CANCEL cash-gate | فعال — VERIFIED_CASH=0 |
| 20 | L3 | net_margin_30d>0 + runway≥30d + 3×VERIFIED_CASH | 🔒 بسته — هیچ شرطی برقرار نیست |
| 21 | L4 | نامشخص | هرگز مستند نشد |
| 22 | `MAY_AUTHORIZE=false` | مالک | مطلق — ایجنت هرگز خودش را ارتقا نمی‌دهد |
| 23 | `hold_external=true` | مالک | همهٔ اثرهای بیرونی قفل |

## طبقه F — قفل‌های زمانی (خودکار منقضی می‌شوند)

| # | قفل | انقضا | چه چیزی می‌ایستد |
|---|---|---|---|
| 24 | standing GO | 2026-09-14T00:00Z (۶ روز) | mint loop · wake scheduler · packet pipeline |
| 25 | msg38 | 2026-09-08T12:10Z (~۲۴h) | NOT_PAID ثبت می‌شود → سیگنال منفی به calibration |
| 26 | L1 scoring | 2026-09-08 | امتیازدهی L1 |

## طبقه G — فایل‌های switch (حضور/غیاب)

| # | فایل | وضعیت | معنا |
|---|---|---|---|
| 27 | HALT-ALL | غایب | kill switch غیرفعال |
| 28 | STOP-ORGANISM | غایب | ارگانیسم آزاد |
| 29 | STOP-CORTEX | غایب | کورتکس آزاد |
| 30 | STOP-TG-CENTER | غایب | سنتر تلگرام آزاد |
| 31 | WATCHDOG-STALL-REVIVE | **حاضر** | بازیابی خودکار wedge مسلح |

## طبقه H — قفل‌های عملیاتی (fixable، نه governance)

| # | مشکل | اثر | راه‌حل |
|---|---|---|---|
| 32 | checkout1_poll Linux path | نمی‌توان وضعیت Shopify را از Windows چک کرد | port path به Windows |
| 33 | حسگر پول miswired | confirmed_revenue از پایٔ fitness می‌خواند | repoint به زیمان |
| 34 | METABOLIC-OBS | billed 1.07 ⟷ telemetry 0.00 | دو مسیر — نیاز به رأی مالک |

---

## سه تناقض بزرگ معماری

### تناقض ۱: ۱۹۵ فلخ wire روشن است در حالی که AGENTS.md می‌گوید «روشن نکن»

AGENTS.md §4: «Do not enable any flag matching OCTOPUS_WIRE_*»
واقعیت: `grep -c "^set OCTOPUS_WIRE.*=1" OCTOPUS-flags.cmd` = **۱۹۵**

**تفسیر:** hook جلوی **ایجنت** را می‌گیرد که در **کد** flag را روشن کند، ولی **ارگانیسم** خودش در فایل config خودشان را روشن دارد. این یعنی:
- قاعده برای ارگانیسم اعمال نمی‌شود (فقط برای ایجنت‌های ویرایشگر کد)
- یا ارگانیسم در زمانی روشن کرد که قاعده هنوز وجود نداشت
- یا قاعده فراموش شده و دیگر بار ندارد

### تناقض ۲: D1_EXECUTION_AUTHORIZED بسته ولی سیستم در production است

اگر D1 «مجوز اجرای production» است و سیستم در production اجرا می‌شود، یا:
- D1 تعریف دیگری دارد (مثلاً «مجوز deployment جدید» نه «اجرا»)
- یا D1 بی‌اثر است چون سیستم از مسیر دیگری به production رسید

### تناقاقد ۳: wire_publish در gates.json ولی هیچ کدی آن را مصرف نمی‌کند

grep در kernel/*.py = خالی. یعنی این گیت تعریف شده ولی هیچ منطقی آن را check نمی‌کند — **گیت بی‌بار است**.

---

## تحلیل: کدام قفلها واقعاً جلوی عملگری را گرفته‌اند؟

### قفلهایی که واقعاً مسیر پول را بسته‌اند:

| قفل | چگونه بسته | چه چیزی لازم است |
|---|---|---|
| **L2 (VERIFIED_CASH=0)** | نمی‌تواند به L3 برود → اثر بیرونی محدود | ۳ تراکنش VERIFIED_CASH |
| **hold_external=true** | هیچ اثر بیرونی بدون گیت صریح | مالک باید فعالاً باز کند |
| **standing GO انقضا** | ۶ روز → mint/halt loop می‌ایستد | تمدید با فرم هفت‌فیلدی |
| **checkout1_poll Linux** | نمی‌توان از Windows خرید را poll کرد | port به Windows |
| **msg38 NOT_PAID** | سیگنال منفی → calibration بدتر می‌شود | پاسخ مالک |

### قفلهایی که moot هستند (چیزی محافظت نمی‌کنند):

- `miner_isolation` — mining PARKED است
- `auto_email` — تلگرام جایگزین ایمیل شده
- `partner_precondition` — کدام همکار؟
- `wire_publish` — کد مصرف‌کننده ندارد
- `OBSERVATORY` — تعریف گم شده

### قفلهایی که درست کار می‌کنند:

- GOV-V8 سه قفل مطلق — صفر نقض امروز
- deny hooks — هر تلاش ثبت می‌شود
- kill_switch — آماده ولی غیرفعال
- standing GO expiry — زمان‌سنج درست

## جمع‌بندی: زنجیرهٔ قفلها که جلوی پول را گرفته است

```
D1/D7 بسته (production) ──┐
                           ├──→ hold_external=true ──→ هیچ اثر بیرونی
L2 (VERIFIED_CASH=0) ─────┤                           بدون گیت صریح مالک
                           │
standing GO (۶ روز) ──────┘──→ انقضا = توقف کامل
                           │
msg38 (۲۴h) ──────────────┘──→ NOT_PAID = سیگنال منفی
                           │
checkout1_poll (Linux) ────┘──→ نمی‌توان خرید را تأیید کرد
```

**نتیجه:** پنج قفل زنجیرهٔ پول را بسته‌اند. سه تا با رأی مالک باز می‌شوند (GO, msg38, hold_external)، یکی با کد (checkout_poll)، یکی با پول واقعی (L2→L3 نیاز به VERIFIED_CASH دارد).
