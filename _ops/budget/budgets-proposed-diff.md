---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: idea
tags: [budget, metabolic-governor, proposal]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه]]"
  - "[[04 - Architect System/2026-07-06 METABOLIC-GOVERNOR-proposal]]"
  - "https://api-docs.deepseek.com/quick_start/pricing (fetch 2026-07-06)"
---

# diff پیشنهادی budgets.yaml — فقط PROPOSAL (H7: اعمال = فقط verdict مالک)

> ‏budgets.yaml فقط‌خواندنی است (verdict-خورده 2026-07-06). این نوت **پیشنهاد** است؛
> هیچ خطی از آن اعمال نشده. تا verdict، کد از پیش‌فرض‌های fail-closed خودش استفاده می‌کند
> (`opslib.fx_aud_per_usd` → ‏1.5 با تگ EST؛ ‏`opslib.organ_table` → ‏DEBATE_LOOP با cap پیش‌فرض 5).
> بعد از verdict، همین مقادیر از budgets.yaml خوانده می‌شوند و تگ‌ها FACT می‌شوند.

## ۱) نرخ پین ارز (بستهٔ تلهٔ «USD هزینه‌ها × AUD سقف‌ها»)

```yaml
global:
  aud_per_usd: 1.5        # نرخ پین USD→AUD؛ هم‌ارز ثابت AUD در budget_gate.py — منبع تبدیل تلمتری/گیت
```

## ۲) ارگان لوپ مناظره (V1 — پیش‌فرض پک: AU$5/ماه)

```yaml
loop:
  DEBATE_LOOP: {floor: 0.5, cap_monthly: 5}    # AUD؛ headroom ماهانه بعد از این: ≈ AU$14
```

## ۳) قفل قیمت routing (راستی‌آزمایی‌شده از api-docs.deepseek.com — ‏2026-07-06)

```yaml
routing:
  econ:
    price_in: 0.14         # USD/1M cache-miss [FACT: api-docs.deepseek.com/quick_start/pricing]
    price_out: 0.28        # USD/1M [FACT]
    price_in_cache_hit: 0.0028   # فقط اطلاعی؛ est بدترین‌حالت هرگز cache-hit فرض نمی‌کند
  reason:
    price_in: 0.14         # همان v4-flash در thinking-mode؛ توکن reasoning با نرخ output
    price_out: 0.28
```

- تأیید مستقل: بازنشستگی aliasهای `deepseek-chat`/`deepseek-reasoner` در **2026-07-24 15:59 UTC** — با خط 🔴 موجود budgets.yaml هم‌خوان.
- ‏v4-pro (جایگزین [OPEN] ردیف reason): ‏$0.435/$0.87 — پرومو؛ تصمیم tier با مالک.
- قفل نهایی: مالک یک نگاه به کنسول platform.deepseek.com بیندازد (قیمت billing واقعی حساب خودش) — منبع بالا docs رسمی است نه صفحهٔ billing حساب.

## ۴) تکثیر (اعداد قفل‌شدهٔ پک — الان در کد default اند، باید config شوند)

```yaml
replication:
  max_cells: 6             # ضد Goodhart
  spawn_depth: 1           # ساب‌ایجنت حق SPAWN-PROPOSAL ندارد تا verdict جدا
  accept_threshold: 0.40   # آستانهٔ نرخ پذیرش برای SPAWN-PROPOSAL
```

## ۵) دو ارگان جدید (الان در تلمتری `UNMAPPED:painting` / `UNMAPPED:accounting` می‌افتند)

```yaml
projects:
  PAINTING:    {floor: 1, human_priority: 1.0}   # بیزنس نقاشی — business=painting در core.db/usage
  ACCOUNTING:  {floor: 1, human_priority: 1.0}   # حسابداری — business=accounting؛ privacy: sensitive (ژنوم)
```

- ⚠️ جمع floorها بعد از این دو: ‏AU$8 → ‏AU$10 (+ explore ‏AU$3 + ‏DEBATE_LOOP ‏AU$5) → headroom رقابتی ≈ ‏AU$12/ماه. اگر تنگ است، floor این دو را 0.5 بگذار.
- بعد از verdict، این تغییر کدی هم لازم است (یک‌خطی، additive): افزودن `"painting": "PAINTING"` و `"accounting": "ACCOUNTING"` به `ORGAN_MAP` در `_ops/budget/telemetry.py`.
- **به‌روزرسانی 2026-07-10 (جلسه ۴۴):** پای Lead-نقاشی (`wiring.make_lead_leg`) حالا `organ="PAINTING"` است (قبلاً `LEAD_PAINTING` — با این diff ناسازگار بود و حتی بعد از verdict هم incubating می‌ماند). یعنی **همین §۵ بعد از verdict تو، money_link پا را هم active می‌کند** — هیچ تغییر کد دیگری لازم نیست. تا آن موقع پا incubating و propose-only است (INV-14).

## تکلیف باز (خارج از این diff — verdict V1)

- ‏`CEIL_DAY_USD=2.0` هاردکد budget_gate.py: تفسیر فعلی لایهٔ ما = «سقف burst روزانه» (۲$×۳۰روز > AU$30 → نرخ پایدار نیست). فیکس در budget_gate v2 فقط با verdict.
