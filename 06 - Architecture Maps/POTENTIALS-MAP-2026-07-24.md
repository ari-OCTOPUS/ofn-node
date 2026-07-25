# 🗺️ POTENTIALS-MAP — نقشه‌ی پتانسیل‌های ترکیب 4D × BlackBox × _ops
> تاریخ: ۲۰۲۶-۰۷-۲۴ (جلسه‌ی kimi) · فاز صفرِ مگاپرامپتِ سنتز · همه‌چیز propose-only
> برچسب‌ها: [FACT] امروز روی دیسک دیده شد · [FACT-0717] در کاوشِ ۰۷-۱۷ verify شده · [FACT-0724] از گزارشِ HANDOFF/P5 · [inferred] استنتاج

| # | پتانسیل | شواهد | تلاش | اثر | وضعیت |
|---|---|---|---|---|---|
| 1 | **SENSE روی خودِ ارگانیسم** — SOG روی جریانِ رویدادِ خودِ اختاپوس → اولین متریکِ خودآگاهیِ عملیاتی | `_ops/state/events.jsonl` (schema event.v2) [FACT] + `4d_system/core/metrics.py::empirical_shadow/fit_shadow_parameters` [FACT] | wiring | خودآگاهی | ✅ **ساخته شد** (`_ops/synapse/sense.py`، flag-off) |
| 2 | **مانیتورِ trajectory → «منبع ۵» event_bridge** — درسِ ۱۷٬۰۰۰ اکشنِ ExploitGym | `_ops/telegram_center/event_bridge.py` (الگوی ۴ منبع + cursor) [FACT] + CONTAINMENT-PLAN §P3 [FACT-0724] | wiring | ایمنی | ✅ ماژول ساخته شد (`trajectory_monitor.py`)؛ wiring = tap |
| 3 | **egress deny-by-default** — P1: حذفِ «قابلیتِ محیطیِ پیش‌فرضِ شبکه» | CONTAINMENT-PLAN §P1 [FACT-0724] | wiring در clientها | ایمنی | ✅ policy module ساخته شد (`egress_policy.py`)؛ enforce = tap |
| 4 | **anchor_hash به‌عنوان DNA مشترک** — اثرانگشتِ `0.012553\|0.122520\|0.135073` در همه‌ی پیشنهادها | `4d_system/docs/schemas/b6.sog.proposal.v1.json` [FACT] + `core/model.py` [FACT] | — | اعتماد/ردِ جعل | ✅ پیاده در sense.py |
| 5 | **ژنوم‌خوان در حلقه** — خواندنِ `values.yaml` + tailِ `ledger.jsonl` پیش از هر پیشنهاد → پیشنهادهای خودبه‌خود سازگارتر (ردِ کمتر = زحمتِ کمتر) | `07 - Knowledge/genome-system/` [FACT-0717] + الگوی `brain/kernel_consumer.py` (file-bridge read-only) [FACT-0717] | <۱روز | زحمتِ کمتر | پیشنهاد — حالتِ `_job_synapse` بعدی |
| 6 | **قالبِ creativity-blackbox برای self_code/meta_research** — {why_genius, why_insane, kill_criteria, smallest_test, reversible} → کیفیتِ پیشنهاد + verdictِ سریع‌تر | `07 - Knowledge/genome-system/agents/creativity-blackbox` [FACT-0717] + `4d_system/brain/self_code.py` [FACT-0717] | <۱روز | کیفیت | پیشنهاد |
| 7 | **۶ الگوی SOG روی ارزیابیِ legs** — DualTrackEvaluation/ShadowRouter/NullModelRejection… روی سیگنال‌های business_brain → ارزیابیِ منصفانه بدونِ self-scoring | `4d_system/brain/patterns.py` [FACT-0717] + `_ops/wiring.py` [FACT] | چندروز | هوشی | پیشنهاد |
| 8 | **کالیبراسیونِ ThompsonBandit با open_score** — noveltyِ frontier 4D → بازوهای octopus_core | `octopus_core/telemetry.py` [FACT] + `4d_system/brain/self_evolve.py` open_score [FACT-0717] | چندروز | هوشی | پیشنهاد |
| 9 | **world جدید برای حلقه‌ی سیناپس** — نمایشِ زنده‌ی SENSE (فقط view) از طریق nervous-system extractor | `OCTOPUS/worlds/` [FACT] + `nervous-system/` extractor pattern [FACT-0717] | ۱روز | مشاهده‌پذیری | پیشنهاد |
| 10 | **داوریِ red-team ژنوم برای H1–H14** — evolutionary-doctor به‌عنوان داورِ خارجیِ فرضیه‌های 4D (monitor_separate_from_metric) | `brain/hypotheses.py` ۱۴ فرضیه [FACT-0717] + genome-system/agents/evolutionary-doctor [FACT-0717] | چندروز | اعتبار | پیشنهاد |
| 11 | **خودنگاره‌ی واحد** — `self_portrait.md` (4D) + self_model کورتکس (_ops) + وضعیتِ guardian ژنوم → یک کارتِ هویت | [FACT-0717] هر سه منبع | <۱روز | خودآگاهی | پیشنهاد |
| 12 | **SURV-1 به‌عنوان INV-13ِ پیشنهادی** — fitness فقط از درآمدِ CONFIRMED/ATTRIBUTED ÷ هزینه × ۱.۲ | `app/src/nbb_cp/fitness.py` + `lifecycle.py` [FACT-0717] | فقط proposal رسمی | بقا | پیشنهاد — نیازمند VQ |

## قانونِ اجرا
هر پتانسیل فقط با: (الف) فلگِ default-OFF · (ب) Current/Delta/Preserved/Rollback · (ج) smallest_testِ برگشت‌پذیر · (د) هیچ self-scoring — اندازه‌گیرِ هر سیستم بیرون از همان سیستم است.
