---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [metabolic-governor, telemetry, budget, stage-report]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 1930 PROMPT-PACK — سه پرامپت مرحله‌ای (متابولیسم-مناظره-تکثیر)]]"
  - "[[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه]]"
---

# STAGE1-REPORT — متابولیسم (تلمتری واحد + گیت per-organ + Governor سایه)

> قرارداد پک: پرامپت ۲/۳ اول این را می‌خوانند — دانش انباشته می‌شود، دوباره کشف نمی‌شود.

## چه ساخته شد

- `opslib.py` — کتابخانهٔ مشترک (مسیرها/env، micro-USD صحیح، ‏`fx_aud_per_usd` پین‌شده، ‏`LockedJson` اتمیک به سبک budget_gate، پل ledger ژنوم `NOTE`+subtype، پرچم‌های STOP/FREEZE/ACTIVATION، ‏`live_gate_open` دوقفله).
- `telemetry.py` — خوانندهٔ واحد دو منبع حقیقت + تلهٔ «متر صفر» + تطبیق I3.
- `organ_gate.py` — گیت per-organ روی budget_gate دست‌نخورده؛ state در `organ-state.json`؛ لاگ `organ-gate-log.jsonl`.
- `governor_epoch.py` — گاورنر سایه با **epoch آلوستاتیک** (پایه ۶۰ دقیقه، بین base/4 و base×2؛ فشار = max(velocity, deadline-sigmoid ۱۴روزه, anomaly))؛ dry قطعی $0؛ مود LLM دوقفله + خود-متر شدن با ارگان ARCHITECT_SYS.
- `04 - Architect System/prompts/metabolic-governor-v0.1.txt` — عین §۱ سند METABOLIC.

## چه verify شد (اعداد دقیق)

- منابع حقیقت فقط دو تا: `07 - Knowledge/genome-system/ledger/ledger.jsonl` (METRIC/llm_cost_usd — نوشتهٔ `common/llm.py:82-85`) و `_launchpad/second-brain-live/control-brain/core.db` جدول usage (نوشتهٔ `core/gateway.py:86-96`). ‏`budget-state.json` تا اولین reserve روی دیسک نیست.
- تلهٔ «or 0»: ‏`llm.py:77-78` و `gateway.py:87-93` — تلمتری این‌ها را `suspect_zero` می‌شمارد، نمی‌بلعد.
- `budget_gate.py`: ‏`CEIL_DAY_USD=2.0` هاردکد (:13)؛ پارامتر agent بی‌اثر؛ باگ واحد ارزی DISASTER (:90) — **دست‌نخورده، SHARD برای verdict V1**؛ تفسیر لایهٔ ما: سقف burst روزانه.
- خواندن core.db فقط `mode=ro` (سه نویسندهٔ همزمان sqlite موجود است).
- کپی staging ژنوم در `07 - Knowledge/_backups/.staging-20260706-172057/` → هر grep بدون exclude دوبار می‌شمارد.
- قیمت DeepSeek (این جلسه، api-docs.deepseek.com): ‏v4-flash ‏$0.14/$0.28 در 1M (cache-hit ‏$0.0028)؛ بازنشستگی aliasها 2026-07-24 15:59 UTC. → [[_ops/budget/budgets-proposed-diff|diff پیشنهادی]].

## تله‌های خورده و راه‌حل

| تله | راه‌حل |
|---|---|
| کنسول ویندوز cp1252 | ‏`reconfigure(encoding="utf-8")` در opslib + اجرای همه‌چیز با `-X utf8` |
| هزینه USD × سقف AUD (کم‌نمایی ۳۰-۵۰٪) | همهٔ محاسبات در micro-USD صحیح؛ تبدیل فقط با نرخ پین `fx_aud_per_usd` |
| float جمع‌زدنی خطادار | واحد `micro(usd)` صحیح (int) در کل لایه |
| دو نمونهٔ همزمان state-writer | ‏`LockedJson` (O_EXCL + steal قفل کهنه >۳۰s — همان الگوی budget_gate) |
| EVENT_TYPES بستهٔ ledger | همیشه `NOTE` + ‏`payload.subtype` (V2 پیش‌فرض)؛ زنجیره فیلد `prev` |
| شکست append به ledger | ‏fail-soft برای مشاهده: alert + ‏`ledger-fallback.jsonl`؛ خرج‌کردن جای دیگر fail-closed گیت می‌شود |

## نگاشت business→organ نهایی (telemetry.ORGAN_MAP)

| business/actor | organ |
|---|---|
| ziman | ZIMAN |
| projectf | PROJECT_F |
| debate | DEBATE_LOOP |
| metabolism / governor / evolution | ARCHITECT_SYS |
| کل استک genome-system | GENOME_SYS |
| painting · accounting | **UNMAPPED** (عمداً — تا verdict ارگان‌های PAINTING/ACCOUNTING در [[_ops/budget/budgets-proposed-diff|diff پیشنهادی]]؛ حدس ممنوع) |

## آیتم‌های باز

- ‏verdict V1: عدد لوپ (پیش‌فرض AU$5/ماه) + تکلیف CEIL_DAY_USD + قفل نهایی قیمت از کنسول platform.
- ‏verdict V2: ماندن بر NOTE+subtype (پیش‌فرض اعمال‌شده) یا type نو در ledger.py.
- ‏verdict روی diff پیشنهادی (نرخ پین، DEBATE_LOOP، replication، دو ارگان نو).
- ‏`billed_usd`: مالک روز ۳، عدد کنسول DeepSeek را در epoch-json می‌نویسد (شرط مرگ: واگرایی >۲۰٪ → STOP-METABOLIC خودکار).
