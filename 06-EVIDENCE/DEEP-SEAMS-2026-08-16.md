---
type: evidence
status: active
updated: 2026-08-16
session: DEEP-SEAMS-SELFIMPROVE (مگاپرامپت دوازدهم)
agent: Cursor Grok 4.6 — ایجنت دوازدهم، زاویهٔ درزهای ماشینِ خودبهبودی
created: 2026-08-16 ~13:2x local
mode: بکش→درست کن→تست کن→ذخیره کن→بعدی · طبقهٔ A additive · حذف صفر · فلگ صفر · TCB لمس‌نشد
contradiction_registered: C-027, C-028
next_free_contradiction: C-029
tests_run: "test_goal_generator 12/12 · test_ledger_tip_commit 4/4 · test_self_improve_gauges 4/4 · test_genome_safety 7/7 · test_self_improve 11/11"
run_all_registration: "فایل‌های نو را گزارش می‌کنم نه ثبت — WORKLOCK روی run_all.py"
---

# درزهای ماشینِ خودبهبودی — 2026-08-16

مأموریت یک‌خطی: ماشین باید (۱) بسته باشد (۲) سنجیده شود (۳) رشدش دیده شود. هر جا یکی شکست = درز.

## STEP 0 — فکت‌چک مگاپرامپت با درخت زنده

| ادعای مگاپرامپت | فکت زنده | حکم |
|---|---|---|
| genome-system قلبِ آرزو، هیچ اسکنری داخلش نرفته | loop app `retired` 2026-07-17؛ ledger زنده ۱۱٬۳۹۸ ردیف؛ `verify()` ok؛ آخرین نوشتن 2026-08-16T02:54Z؛ ۸۶٪ ردیف = `SCHEDULER_DISPATCH`؛ `APPLY`/`GENOME_CHANGE`/`APPROVAL` = ۰؛ STATUS.version قفلِ 0.4.3 در حالی که ledger.py تا v0.4.7 رفته بود | ✅ هدف درست؛ «رشد ژنوم» ادعا است |
| memory/ بی‌manifest بی‌card | `_ops/memory/capability-manifest.json` وجود دارد (`visibility_only_manifest: true`، PHASE01 4-3) | ❌ کهنه — manifest هست، کارت تلگرام هنوز نه |
| neural وزن‌ها خوانده نمی‌شوند | `bcm-weights.json` step=186 را wiring + math_control می‌خوانند؛ `hebbian.json` ۳ جفت را spine می‌خواند (`assoc_strength`) | ❌ کهنه — خواننده دارند؛ نمایش‌تنها نیستند |
| self_goal_cycle دیوار نمایش | ۲۶ چرخه done تا 2026-08-16#1؛ **۲۴/۲۴ FAIL** `no-movement` روی یک `goal_key`؛ `attribution.claimed=0`؛ `recall-events=90` هرگز نوبت نگرفت؛ `deadline_cycles=2` در کاتالوگ بود و propose نمی‌خواندش | ✅ درز واقعی |
| آزاد C-027 | grep دو-مخزن: آزاد بود | ✅ |

## جدول چرخه‌ها

| # | هدف | درز | سنجه قبل | سنجه بعد | حکم | فرمان بازتولید |
|---|---|---|---|---|---|---|
| 1 | A3 اهداف درونی | `deadline_cycles` تزئینی بود؛ money-claimed با ۲۴ FAIL صدر را قفل کرده بود | ۲۴/۲۴ FAIL · ۱ goal_key · recall هرگز انتخاب نشد · claimed=0 در برابر events=90 | `propose()` → **recall-events baseline=90** · money `deadline-exhausted` streak=24 | **CLOSED** (C-027) | `python -X utf8 _ops/tests/test_goal_generator.py` (۱۲/۱۲) + `goal_generator.propose()` روی درخت زنده |
| 2 | A1 ledger | `verify()` حذفِ آخرین ردیف را ok می‌دهد (هم‌کلاس E3-tail) | کپی ۱۱٬۳۹۸ ردیف، حذف دم → `verify()=True ok` | `verify_tip()` همان کپی را `length mismatch` می‌کند؛ `verify()` عمداً LAW-دست‌نخورده | **CLOSED** (C-028) — sidecar از append بعدی / daily `seal_tip` | `python -X utf8 _ops/tests/test_ledger_tip_commit.py` (۴/۴) |
| 3 | A2 حلقهٔ improve | digest `rejected_categories={}` را شبیه «مالک رد نکرد» نشان می‌داد در حالی که فایل وجود نداشت | `improve-verdicts.jsonl` غایب · `auto_eligible=[]` · ACT_AUTO فایل هست | `_learning_report()`: `verdicts_file=False` · `verdicts_n=0` · `penalty_armed` صریح | **CLOSED** (gauge) | `python -X utf8 _ops/tests/test_self_improve.py` (۱۱/۱۱) |
| 4 | D پنج vital | خودیادگیری بدون متریکِ واحد | نرخ بستن حلقهٔ هدف نامرئی | `goal_loop_close_7d`: **۱۵ حکم / ۰ PASS / 0.0٪** · `internal_goals_moved_7d=0` · consolidation_24h=**۵** · pending sqlite fail-soft None | **CLOSED** (gauge وصل شد؛ عدد هنوز صفر است — این صداقت است) | `python -X utf8 _ops/tests/test_self_improve_gauges.py` (۴/۴) |
| 5 | B1 memory/ | مگاپرامپت «بی‌manifest» | — | manifest هست؛ `self_loop_ingest` trail=۲۰۵۵ و improve از آن proposal می‌سازد (خط ۶۳۱) | **METAPHORِ نامرئی بودن** — درزِ واقعی: `OCTOPUS_WIRE_MEMORY_READ` پیش‌فرض خاموش برای planner | grep + خواندن manifest |
| 6 | B2 neural/ | مگاپرامپت «هببیان display-only» | — | BCM+Hebbian هر دو مصرف‌کنندهٔ تولیدی دارند (wiring prune · math_control spine) | **METAPHORِ نخوانده‌شدن** — وزن‌ها خوانده می‌شوند؛ رشدِ کلیدِ `cycle-N` جداست | `math_control/spine.py:_hebbian_assoc` · `state/bcm-weights.json` |
| 7 | C experiments | پکیج نامرئی | صفر import تولیدی از بیرونِ خودش | صفر ماند (اتصال = رأی) | **NEEDS-VOTE** | `rg "hypothesis_engine.experiments" _ops --glob "*.py"` |

## بزرگ‌ترین درز بسته‌شده

**A3 / C-027:** حلقهٔ خودهدف‌گذاری ۱۶ روز فقط `attribution.claimed=0` را اندازه گرفت و روش را ۰→۱→۲ چرخاند بی‌آنکه کاندیدای بعدی را راه بدهد. `deadline_cycles=2` روی کاغذ بود. امروز همان فیلد اجرا می‌شود: نوبت به `recall-events=90` رسید — همان عددی که حلقهٔ recall امروز بالا برد و ماشینِ هدف هرگز ندید.

## بزرگ‌ترین درز بازِ رأی‌خواه

`hypothesis_engine/experiments` (deceptive-grid) صفر فراخوان تولیدی دارد — کد کامل، ارزش صفر. وصل‌کردن یا بازنشستگی نیاز به رأی دارد. هم‌خانواده: فلگ `OCTOPUS_WIRE_IMPROVE_LEARN=1` در flags.cmd هست ولی `improve-verdicts.jsonl` روی دیسک زنده هنوز نیست — رأی‌های improve از مسیر `live_loop` نمی‌آیند.

## آیا اختاپوس امروز از دیروز بهتر شد؟ با کدام عدد؟

**بله، با دو عدد که دیروز صفرِ پنهان بودند:**

1. **هدفِ درونیِ زنده عوض شد:** قبل = ۲۴ چرخه روی claimed=0 (حرکت صفر). بعد = `propose()` کاندیدای `recall-events` با baseline **۹۰** می‌دهد (همان M3 که امروز از ۵۸ به ۹۰ رسید). اولین بار است که سنجهٔ حرکت‌کرده وارد قیفِ خودهدف می‌شود.
2. **دمِ لجر دیگر نامرئی نیست:** قبل = حذف آخرین ردیف از ۱۱٬۳۹۸ → `verify()=ok`. بعد = `verify_tip()` همان حمله را می‌گیرد. `verify()` عمداً عوض نشد.

عددِ رشدِ خودِ حلقهٔ هدف هنوز **۰ PASS از ۱۵ حکمِ ۷روزه** است — gauge حالا این را می‌گوید، دیگر پنهان نیست.
