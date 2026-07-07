---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [replication, fitness, darwinian, stage-report]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 1930 PROMPT-PACK — سه پرامپت مرحله‌ای (متابولیسم-مناظره-تکثیر)]]"
  - "[[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه]]"
---

# STAGE3-REPORT — تکثیر (fitness + انتخاب طبیعی، همه سایه)

> وضعیت داده: **pre-replication** — هنوز صفر EXPERIENCE زنده در ledger. هر عدد این گزارش
> ساختار است نه اندازه‌گیری؛ جدول واقعی بعد از ~۴ هفته دادهٔ EXPERIENCE پر می‌شود (قفل جلسه ۱۶).

```yaml
sigma_epoch_state:
  epoch_mode: allostatic     # طول epoch تابع فشار (velocity/deadline/anomaly)، نه clock
  sigma: n/a (pre-replication)
```

## جدول fitness واقعی

| cell | acceptance_rate | cost_per_accepted | waste | fitness | وضعیت |
|---|---|---|---|---|---|
| — | n/a | n/a | n/a | n/a | ‏`authoritative: false` تا ۲۸ روز دادهٔ EXPERIENCE |

تعریف قفلِ پذیرش (در کد `fitness.py` عیناً): «پذیرفته» = فقط رکورد `logs/outbox.jsonl` با ‏`status='sent'` (پس از کلیک انسان) **و** تطبیق‌پذیر با core.db؛ ‏mismatch>۱۰٪ = حذف cell + alert. ‏survive معمار هرگز شمرده نمی‌شود؛ ‏pending نه می‌سوزاند نه امتیاز می‌دهد.

## تصمیم‌های شبیه‌سازی

- شبیه‌سازی روی دادهٔ واقعی هنوز اجرا نشده (ledger زنده خالی است) — تست‌های سوئیت (`test_fitness_sigma.py`) مکانیک را روی دادهٔ ساختگی ایزوله سبز کرده‌اند: بدون نقض GLOBAL_CAP/FLOOR، ‏σ>1 → ‏ALERT محور سرطان + توقف، ‏PROJECT_F مستثنا.
- ‏n<8 سلول: چارک بی‌معنا → آستانهٔ ثابت (fitness>0.6 → +٪ · <0.3 → −٪) طبق پک.
- اولین شبیه‌سازی واقعی: بعد از smoke یک‌شبه + چند روز دیتای organism (خروجی `replication-latest.json` روزانه ساخته می‌شود).

## سلول‌های نزدیک به آستانهٔ SPAWN

هیچ — پیش‌شرط SPAWN-PROPOSAL: ‏≥۱۰ پیشنهادِ verdict-شده و ‏acceptance ≥۴۰٪ (پیش‌فرض [SPEC] در [[_ops/budget/budgets-proposed-diff|diff پیشنهادی]])؛ فعلاً صفر پیشنهاد verdict-شده وجود دارد.

## درس‌های مکانیک انتخاب (از ساخت و تست)

1. ‏σ_effective باید از ledger (رویدادهای واقعی) بیاید نه از شمارندهٔ خود لوپ — وگرنه خودتبانی.
2. سقف‌ها ضد Goodhart لایه‌لایه‌اند: ‏MAX_CELLS=6 + عمق ۱ + ضمیمهٔ ۱۰ پیشنهاد به کارت SPAWN (مالک trivial-farming را می‌بیند) + ‏cost_per_accepted هم‌وزن acceptance_rate.
3. ‏EXTINCTION هرگز خودکار نیست؛ ‏HIBERNATE فقط «پیشنهاد» بعد از ۵ epoch بی‌خروجی.
4. ‏DEADLINE SHIELD: ددلاین <۱۴ روز → هرگز زیر floor (سیگموید در governor_epoch همین را تغذیه می‌کند).

## آیتم‌های باز (ورودیِ verdict «اولین enforcement واقعی»)

- ‏~۴ هفته دادهٔ EXPERIENCE → ‏`authoritative: true` شدن fitness (خودکار نیست؛ شرط داده + verdict).
- ‏`ACTIVATION-REPLICATION.flag` فقط-مالک و فقط ≥ 2026-07-21.
- بعد از اولین SPAWN-PROPOSAL شایسته: ردیف در `05 - Agents/AGENT_REGISTRY.md` + diff سلول نو در budgets.yaml (هر دو پشت verdict).
- ‏۳۰ روز بدون SPAWN-PROPOSAL شایسته = بازطراحی تکثیر، نه اصرار (شرط مرگ پک).
