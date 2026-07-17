---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [deep-scan, architecture, octopus, handoff, capability-map]
created: 2026-07-17
updated: 2026-07-17
created_by: agent (deep-scan session)
audience: next-agent
sources:
  - "[[_ops/ORGANISM-SPEC]]"
  - "[[_ops/organism]]"
  - "[[_ops/cortex/cortex]]"
  - "[[_ops/heart/producers]]"
---

# 🐙 DEEP-SCAN — معماریِ طرز فکرِ اختاپوس (قلب‌ها، مغزها، پاها)

> **این سند برای ایجنتِ بعدی است.** تمامِ پتانسیل‌ها و کانال‌های ارگانیسم، ریشه‌یابیِ ضعفِ
> عملکرد («ژنتیک پُره، عملکرد ضعیف») و نردبانِ فعال‌سازی. هیچ حافظه‌ی نشستِ قبلی لازم نیست —
> همه‌چیز از روی کد و stateِ زنده استخراج شده.
>
> **رأیِ مالکِ محرک:** «معماری که کردم خیلی پیچیده‌تره — اختاپوس ژنتیکش پره ولی عملکردش ضعیف
> تر از ژنشومشه. پس شروع کن.»
>
> آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۷ (beat 7119، سیستم زنده).

---

## ۰) خلاصه‌ی اجرایی — «چرا پُر-ژن، کم-عمل؟»

ارگانیسمِ اختاپوس **سه‌لایه‌ی کامل، ۶۰+ ماژول، ~۱۸٬۶۰۰ خط کد، ۵۸ فلگِ wiring** دارد — ولی
**تقریباً همه‌ی مسیرهای پولی/عملیاتی پشتِ فلگ‌های default-OFF قفل‌اند** و فقط دو کسب‌وکار
(Ziman، Lead-نقاشی) پایه‌گذاری شده‌اند. علتِ «عملکردِ ضعیف» **نه نقصِ معماری، که چهار گسستِ
سطحِ بالاست**:

| # | گسست | شواهدِ زنده (beat 7119) | ضربه |
|---|---|---|---|
| **G1** | **پاهای پیشنهاد ساز می‌کنند ولی کسی تحویل نمی‌گیرد** | `proposals_emitted=0` در live state؛ `Leg.emit_proposal()` فقط به `self._proposals` اپند می‌زند، هیچ bus/human-consumer ای به آن وصل نیست | تمامِ زیمان/لید/حسابداریِ propose-only **بی‌سر» اند |
| **G2** | **هیچ مسیرِ پولیِ زنده‌ای باز نیست** | `month.aud=0`, `velocity_per_hr=0.083` (تقریباً فقط heartbeat)، `delta_self_live=0.0`، `confirmed_revenue=0`. همه‌ی `ACTIVATION-*.flag` ها غایب‌اند | هیچ یادگیریِ واقعیِ بسته (P_closed) ممکن نیست چون داده‌ی تأییدشده صفر است |
| **G3** | **حلقه‌ی یادگیریِ خودارتقایی باز است نه بسته** | `improve.py` + `goal_directed.py` + `auto_approve.py` طراحیِ بسته دارند ولی `measure()` فقط ۳ کلید را نگاه می‌کند (`confirmed_revenue`/`revenue_cells`/`total_discoveries`) که همگی صفرند → هرگز outcome ثبت نمی‌شود → verdict-penalty هیچ‌وقت به‌روز نمی‌شود | مغز نمی‌داند چه چیزی کار کرد |
| **G4** | **تقاطعِ intake‌های موازی** | `LiveLoop.process_lead()` → `leg.intake(name,aud,cell)` ولی `lead_quote.create_quote()` → `lead_to_intake(lead,scored)` → `QuoteIntake`. دو شکلِ متفاوت، یک مسیرِ فیزیکی. همیشه یکی از دو مسیر dead-code است | سرگیجه‌ی wiring؛ ریسکِ لیدِ گم‌شده |

**نتیجه‌ی تحلیلی:** ارگانیسم یک **مغزِ کامل (cortex) و قلبِ کامل (chrono+heart+cardiac)** روی یک
**بدنِ تقریباً فلج (legs بی‌consumer، live-loop ناقص)** سوار است. قلب می‌تپد (67.88s)، مغز فکر
می‌کند (cycle 85، coherence 0.93)، ولی بدن چیزی تولید/فروش نمی‌کند.

> **پیش‌بینیِ کلیدی:** اگر **فقط G1 و G2** بسته شوند (تحویلِ proposal به کانالِ انسانی + بازشدنِ
> حداقلِ یک مسیرِ پولیِ paper)، `velocity` از 0.083 به ۰.۳+ می‌رسد، `delta_self` از صفر خارج
> می‌شود، و **حلقه‌ی یادگیریِ مغز برای نخستین‌بار داده‌ی واقعی می‌خورد.** این یعنی تمامِ
> زیرساختِ عصبی از حالتِ idle به active تبدیل می‌شود — بدونِ هیچ کدِ جدیدی، فقط wiring.

---

## ۱) آناتومی — سه‌لایه‌ی ارگانیسم (با شماره‌ی پورت/پروسه)

ارگانیسم چند-پروسه‌ی جدا با قفلِ تک‌نمونه‌ی bind-انحصاری روی loopback است. هر کدام crash مستقل دارد.

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  معمار (آری) — انسان. تنها منبعِ human-append / verdict / پول     │
   └───────────────────────────┬─────────────────────────────────────┘
                               │ Telegram (approval_channel) + /lead + /stop
   ╔═══════════════════════════╧═══════════════════════════════════════╗
   ║  لایه‌ی ۱ — فیزیولوژی (HEART = جریان/ضربان)                         ║
   ║  ┌────────────────────────────────────────────────────────────┐  ║
   ║  │ Pacemaker (chrono.py)  :8771؟ نه — heartbeat row، HLC، phi  │  ║
   ║  │   beat=7119 · HLC monotonic · phi-accrual liveness          │  ║
   ║  │   EffectorGate (TINV-7: تنها passage به دنیای بیرون)         │  ║
   ║  │   LANGAR chain (genome ledger age_tick)                     │  ║
   ║  ├────────────────────────────────────────────────────────────┤  ║
   ║  │ Heart shadow (producers.py + control_law.py)                │  ║
   ║  │   velocity_meter · internal_cpi · delta_self_estimator      │  ║
   ║  │   period_s = f(σ, velocity, CPI, budget)  — کنترل‌لای ۷لایه   │  ║
   ║  ├────────────────────────────────────────────────────────────┤  ║
   ║  │ Cardiac allometry (cardiac.py) — ۳ قانونِ زیستی [default-OFF]│  ║
   ║  │   bio_rhythm · BeatBudget · Baroreflex                      │  ║
   ║  ├────────────────────────────────────────────────────────────┤  ║
   ║  │ Work pump (work_pump.py) — execution engine                  │  ║
   ║  │   ۵ template: health/gap_report/web_research/paid_lane       │  ║
   ║  ╚══════════════════════════════════════════════════════════════╝  ║
   ╠═════════════════════════════════════════════════════════════════════╣
   ║  لایه‌ی ۲ — مغز (CORTEX = کنترلگر)   :8772  پروسه‌ی جدا             ║
   ║  ┌────────────────────────────────────────────────────────────┐  ║
   ║  │ cortex.py run_cycle() — orchestrator                        │  ║
   ║  │   registry.sweep → align_work_plan → think (model_router)   │  ║
   ║  │   + ۱۲ زیرسیستم: stress/innervation/ignition/improve/...    │  ║
   ║  ├────────────────────────────────────────────────────────────┤  ║
   ║  │ model_router — ۳ لایه‌ی مغز: ollama($0)/GLM/Fugu (paid)       │  ║
   ║  ├────────────────────────────────────────────────────────────┤  ║
   ║  │ Live Loop (live_loop.py) + Live Server :8773 — نخاع+اتاق کنترل│  ║
   ║  ╚══════════════════════════════════════════════════════════════╝  ║
   ╠═════════════════════════════════════════════════════════════════════╣
   ║  لایه‌ی ۳ — متابولیسم (BUDGET = انرژی/سهمیه) + پاها (LEGS)         ║
   ║  ┌────────────────────────────────────────────────────────────┐  ║
   ║  │ budget_gate (خارجی، تنها enforcer) ← organ_gate (per-organ)  │  ║
   ║  │ governor_epoch (آلوستاتیک، سایه‌ی $0)                        │  ║
   ║  │ approval_channel (Telegram) — تنها مسیرِ human-append         │  ║
   ║  ├────────────────────────────────────────────────────────────┤  ║
   ║  │ Legs (workerهای ایزوله، propose-only):                       │  ║
   ║  │   Lead-نقاشی · Ziman · Accountant · Cartographer · Mining... │  ║
   ║  ╚══════════════════════════════════════════════════════════════╝  ║
   ╚═════════════════════════════════════════════════════════════════════╝
                               │
                               ▼
                  genome ledger.jsonl (LANGAR، append-only، hash-chain)
```

| پورت | پروسه | نقش | kill تمیز |
|---|---|---|---|
| 8768 | app (مغزِ قدیمی/ژنوم) | لامعطّل — دست نمی‌زنیم | — |
| 8770 | dashboard | داشبوردِ داشبورد | — |
| **8771** | **organism.py** | **حلقه‌ی واحدِ همیشه-روشن + state API** | `_ops/STOP-ORGANISM` |
| **8772** | **cortex.py** | **مغزِ کنترلگر** | `_ops/STOP-CORTEX` |
| **8773** | **live/server.py** | **اتاقِ کنترل + hologram + /ask** | — |
| 8790 | panel/server.py | پنلِ مالک (پروفایل/projects) | — |

---

## ۲) قلب — چگونه فکر می‌کند (CHRONO + Heart + Cardiac)

قلب سه‌لایه‌ای است و **چیزی نمی‌فهمد، فقط تند/آرام می‌تپد**. هوشِ قلب در **تغییرِ ریتم** است.

### ۲.۱ Pacemaker (chrono.py) — بسترِ زمان
- **HLC (Hybrid Logical Clock):** ساعتِ منطقیِ CockroachDB، مونوتونیکِ سخت (TINV-1). هر رویداد مهر می‌خورد. پاها هرگز wall-clock نمی‌خوانند (TINV-5).
- **phi-accrual:** آشکارسازِ زنده‌بودنِ هر پا (alive→suspected→failed). پای failed → قلابِ `doctor.restart_from_known_good()`.
- **EffectorGate (TINV-7):** **تنها passage به دنیای بیرون.** سیکلِ `request(pending) → release_gated_effects(releasable) → settle(world)`. `settle` فقط اگر `release_ref` موجود باشد (یعنی LANGAR-append قبلاً رخ داده). `sweep_stale_effects(72h)` اثرهای معلق را auto-refuse می‌کند.
- **LANGAR (genome ledger):** زنجیره‌ی hash. `on_human_judgment()` تنها تابعی است که `age_tick` را جلو می‌برد (TINV-3). هر تأییدِ تلگرامی = ۱ append = ۱ stepِ پیرشدن.
- **Metabolic aging:** `wear += WEAR_BASE * (1 + rate/cap)` — پاهای پرمشغله سریع‌تر پیر می‌شوند.

### ۲.۲ Heart Shadow (producers + control_law) — چرا این ریتم؟
سه سنجه‌ی زنده (همه read-only، provenance خارجی — ضدِ self-grading):
1. **velocity_meter** — توانِ عبورِ شناخت/ساعت. ورودی: CONFIRMED attribution + EFFECT_SETTLED + consolidation + heartbeat. وزنِ `confirmed=۳×` (پول سنگین‌تر). **زنده: 0.083/hr** ← فقط از heartbeat می‌آید، چون attribution صفر است.
2. **internal_cpi** — تورمِ واسط ∈ [۰,۱]. نویزِ attribution + mismatchِ reconcile + suspect-zero. **زنده: 0.0** ← داده نیست.
3. **delta_self_estimator** — Δ_self (SOG). دو پیش‌بین blind/informed روی استریمِ velocity؛ `½log(S_b/S)`. ceiling زنده هم محاسبه می‌شود. **زنده: 0.0** ← استریم خالی.

**control_law.heart_step():** pure function با **۷ لایه‌ی fail-closed**:
σ-missing → σ-stale → σ-tainted → σ-over-cap → delta-drift → no-velocity → anti-futility.
هر کدام رد شود → period = MAX (900s deep rest). **period فعلی 67.88s** چون هیچ گیت نمی‌بندد (σ=0 یعنی نه over-cap نه tainted).

> **نکته‌ی تحلیلی:** وقتی velocity=0، `no-velocity-source` گیت باید period را به MAX ببرد، ولی `baro_factor=0.708` نشان می‌دهد که قلب در حالتِ "هیچ داده‌ای ولی زنده‌ام" می‌تپد. این یعنی **قلب برای سیستمِ بی‌داده صرفاً liveness signal است** — پتانسیلِ شناختی‌اش idle است.

### ۲.۳ Cardiac Allometry (cardiac.py) — زیست‌شناسیِ ضربان [default-OFF: `OCTOPUS_WIRE_BIO`]
سه قانونِ بیولوژیک که فعلاً خاموش‌اند:
- **Law 1 (bio_rhythm):** period = BASE × (mass/REF)^¼. موش سریع، نهنگ آرام. mass = اندام‌های فعال + درآمدِ تأییدشده.
- **Law 2 (BeatBudget):** کاپِ روزانه‌ی ضربان (288). وقتی تمام شد، فقط resting beat. **ارگانیسم را مجبور می‌کند انتخابگر باشد.**
- **Law 3 (Baroreflex):** پاسخ به محرک. فروش → factor 0.6 (تندتر)، CONFLICT → 1.5 (آرام‌تر).

> **پتانسیل:** روشن‌کردنِ `OCTOPUS_WIRE_BIO=1` ارگانیسم را از clock-based به truly-allostatic تبدیل می‌کند. اما فعلاً پرِ ریسک است چون mass=1 (تقریباً صفر اندام فعال) → period نزدیکِ BASE می‌ماند → سودِ کمی دارد تا وقتی G2 (درآمد) حل شود.

### ۲.۴ Work Pump (work_pump.py) — عضلات
5 template اجرا می‌کند روی ریتمِ قلبِ سایه: health(6h) · gap_report(12h) · web_research(12h,$0) · paid_search(24h,locked) · llm_learn(24h,locked). فعلاً **paid lane پشتِ `ACTIVATION-WORK-LLM.flag` + تاریخِ 2026-07-21 قفل است.**

---

## ۳) مغز — چگونه فکر می‌کند (CORTEX)

مغز، پروسه‌ی جدا روی :8772 است. هر چرخه (`run_cycle`): `sweep → align → ۱۲ زیرسیستم → think → state`. ریتم = `2× periodِ قلبِ سایه` (قلب تند → مغز تندتر).

### ۳.۱ زیرسیستم‌های مغز — وضعیت زنده

| زیرسیستم | فایل | وضعیت | فلگ | کارِ یک‌خطی |
|---|---|---|---|---|
| **registry sweep** | registry.py | ✅ LIVE | — | آگاهیِ همگانی از state-fileها |
| **align_work_plan** | cortex.py | ✅ LIVE | — | مرتب‌سازیِ کران‌دارِ نقشه‌ی کارِ $0 |
| **think** | cortex.py | ✅ LIVE | — | فکرِ کوتاه با مغزِ محلی/پرداخت‌شده |
| **stress** | stress.py | ✅ LIVE | — | هومئوستاتِ استرس/ترس (۵ زیرسیستم) |
| **innervation** | innervation.py | ✅ LIVE | — | نقشه‌ی عصب‌کشی + نقطه‌ی مرده |
| **model_router** | model_router.py | ✅ LIVE | — | ۳ لایه‌ی مغز: ollama/GLM/Fugu |
| **improve** | improve.py | ✅ LIVE | `ACTIVATION-SELF-IMPROVE-AUTO` | حلقه‌ی خودارتقایی + ۶ منبعِ سیگنال |
| **self_model** | self_model.py | ✅ LIVE | — | AST-walkِ کدِ خود → نقشه‌ی خودآگاهی |
| **goal_directed** | goal_directed.py | ✅ LIVE | — | ضدِ circular + intent→outcome |
| **synthesis** | synthesis.py | ✅ LIVE | — | مغزِ پژوهش → ۳ پیشنهادِ متقاطع |
| **business_brain** | business_brain.py | ✅ LIVE | — | مغزِ دومِ درآمد (Lead+Project-F) |
| **part_loops** | part_loops.py | ✅ LIVE | — | لوپِ یادگیری برای هر بخش |
| **auto_approve** | auto_approve.py | ✅ LIVE (auto: OFF) | `ACTIVATION-SELF-IMPROVE-AUTO` | طبقه‌بندیِ ریسک + اعمالِ knob |
| **doctor** | doctor.py | ✅ LIVE (partial) | چند `OCTOPUS_WIRE_*` | انگلِ تکاملی: mine→RFC→sandbox→submit |
| **calibration_probe** | calibration_probe.py | 🔶 SHADOW | `CORTEX_SELF_MONITOR` | بایاس‌سنجیِ ادعاهای خود |
| **consolidate** | consolidate.py | 🔶 SHADOW | `CORTEX_CONSOLIDATE` | تثبیتِ حافظه |
| **ignition** (GWT) | ignition.py | 🔴 OFF | `CORTEX_IGNITION` | workspace attention / WTA |
| **ignition_softwta** | ignition_softwta.py | 🔴 OFF | `IGNITION_SOFT_WTA_SHADOW` | soft-WTA سایه |
| **code_autonomy** | code_autonomy.py | 🔴 OFF | `ACTIVATION-CODE-AUTONOMY` | خود-تغییرِ کد با ۷ گیت |

### ۳.۲ حلقه‌ی یادگیری — چگونه بسته/باز است؟

حلقه‌ی خودارتقایی **طراحی‌ی بسته** دارد ولی **خروجیِ واقعی ندارد**:

```
  observe (self_audit + self_model + stress + innervation + business_brain + synthesis)
      │
      ▼
  analyze (improve.generate_proposals — ۶ منبع → دسته‌بندی)
      │
      ▼
  evaluate (goal_directed.rerank — circular حذف، impact امتیاز)
      │
      ▼
  decide  (auto_approve.decide — risk classify + ۵ self_test)
      │
      ├── auto (L1): فقط ۳ knobِ $0 پشتِ ACTIVATION flag  [خاموش]
      └── owner (L2): RFC/telegram، یا code_autonomy  [خاموش]
      │
      ▼
  learn (record_verdict + goal_directed.measure + _close_intents)
      │
      ▼
  outcome ← BUT measure() فقط نگاه می‌کند به:
              confirmed_revenue · revenue_cells · total_discoveries
              ─────────────────────────────────────────────────────
              همه‌ی صفر!  ←  هیچ‌وقت outcome ثبت نمی‌شود
              ←  verdict-penalty هیچ‌وقت به‌روز نمی‌شود
              ←  حلقه واقعاً باز است
```

> **پیش‌بینی:** تا وقتی G2 (مسیرِ پولی) حل نشود، مغز **به‌طورِ ساختاری نمی‌تواند یاد بگیرد کدام
> پیشنهاد کار می‌کند.** این ریشه‌ی «عملکردِ ضعیف» است — نه کدِ بد، که **فقدانِ سیگنالِ برتر.**

### ۳.۳ سه لایه‌ی مغز (model_router)
| لایه | مدل | هزینه | گیت |
|---|---|---|---|
| local | ollama `qwen2.5:1.5b` | $0 | همیشه |
| secondary | GLM | paid | `ACTIVATION-CORTEX-PAID.flag` + تاریخ |
| primary | Fugu (DeepSeek) | paid | `ACTIVATION-CORTEX-PAID.flag` + تاریخ |

> **زنده:** اکنون `think` با local کار می‌کند. paid پشتِ flag + 2026-07-21. `route_scorer` پشتِ `CORTEX_ROUTE_SCORER`.

---

## ۴) پاها — چگونه کار می‌کنند (LEGS)

هر پا `Leg` (legs/leg.py) را implements می‌کند: `TaskPacket` در ورودی، `Proposal` در خروجی. **ساختاری propose-only** — هیچ متدِ send/publish/pay وجود ندارد.

### ۴.۱ موجوداتِ پا

| پا | فایل | وضعیت | revenue | گلوگاه |
|---|---|---|---|---|
| **Lead-نقاشی** | lead_quote.py + lead_leg.py | ✅ LIVE (propose) | **بالا** — تنها پاچ درآمدی | دو intake موازی (G4)؛ `draft_quote` در LiveLoop فراخوانی نمی‌شود |
| **Ziman Gallery** | ziman_leg.py | ✅ LIVE (propose) | غیرمستقیم — محتوای مارکتینگ | محتوای hardcoded فارسی (نه LLM)؛ ceiling دائماً ۶/هفته |
| **Accountant** | accountant.py | ✅ LIVE (flag-gated) | — — حافظه‌ی مالی | `OCTOPUS_WIRE_POCKETSMITH` خاموش؛ ps_writeback stub |
| **Accounting pulse** | accounting_leg.py | 🔶 SHADOW | — | فقط freshness checker |
| **Cartographer** | cartographer_leg.py | 🔴 OFF | — | `OCTOPUS_WIRE_CARTOGRAPHER` خاموش |
| **Mining** | mining_leg.py | 🔴 OFF | — | `OCTOPUS_WIRE_MINING` خاموش |
| **Email inbound** | email_inbound.py | 🔴 OFF | — | `OCTOPUS_WIRE_EMAIL` خاموش |
| **Lead discovery** | lead_sense.py + lead_scorer.py | 🔴 OFF | پتانسیلِ بالا | `OCTOPUS_WIRE_LEAD_DISCOVERY` خاموش |

### ۴.۲ گلوگاهِ ساختاریِ G1 — پاهای بی‌سر
`Leg.emit_proposal()` فقط به `self._proposals_emitted` اپند می‌زند. **هیچ consumer ای در wiring این لیست را extract و به bus/telegram/انسان نمی‌رساند.** `LiveLoop` فقط draft‌های مغز و lead را process می‌کند، نه proposal‌های پاها را. یعنی هر پا در تاریکی پیشنهاد می‌سازد و پیشنهاد می‌میرد.

> **پتانسیلِ G1:** اگر یک «Proposal Router» ساخته شود که `_proposals_emitted` را بگیرد و
> کارتِ تلگرامی بسازد، **تمامِ پاهای propose-only فوراً به کانالِ انسانی وصل می‌شوند** — این
> ارزان‌ترین بردِ معماری است.

### ۴.۳ گلوگاهِ G4 — تقاطعِ intake
| مسیر | ورودی | خروجی |
|---|---|---|
| LiveLoop.process_lead | `leg.intake(name, aud, cell)` | publish bus → attribution → CONFIRMED |
| lead_quote.create_quote | `lead_to_intake(lead, scored)` → `QuoteIntake` → `leg.draft_quote()` | JSON persist → HTML render |

این دو **هرگز به هم وصل نیستند**. لازم: یک adapter یا حذفِ یکی.

---

## ۵) متابولیسم — چگونه پول/انرژی جریان می‌یابد (BUDGET)

### ۵.۱ اصلِ تک-نافذ (Single-Enforcer, I2)
```
  ارگان (TaskPacket) ──→ organ_gate.reserve(organ, est_usd)
                              │
                              ▼  deny-chain:
                              STOP/FREEZE → unknown organ → state unreadable
                              → organ monthly cap (AUD) → budget_gate.reserve (GLOBAL)
                              │
                              ▼
                          allow/deny
```
**`budget_gate` (خارجی، در `04-Architect/scripts/`) تنها enforcer است.** هر عددی از `budgets.yaml` (read-only، I6).

### ۵.۲ TELEGRAM = تنها مسیرِ human-append (TINV-7 / I7)
```
  مالک روی کارتِ تأیید کلیک می‌کند
      │
      ▼
  approval_channel._do_approve(effect_id)
      │
      ▼
  on_human_judgment(judgment, gate, ledger)
      │
      ├── ledger.append("APPROVAL", ..., is_human=True)  [LANGAR append]
      │       └── age_tick += 1
      │
      └── gate.release_gated_effects(entry)
              └── pending → releasable (+ release_ref = hashِ append)
      │
      ▼
  gate.settle(effect_id)
      └── تنها passage: force_closed? + releasable? + release_ref?
              → EFFECT_SETTLED NOTE به ledger
```
**هیچ اثرِ برگشت‌ناپذیری بدونِ LANGAR-append قبلی settle نمی‌شود.** این قلبِ امنیتیِ ارگانیسم است.

### ۵.۳ گاورنرِ آلوستاتیک (governor_epoch)
epoch_length = `base × (1 - 0.75×pressure)`, فشار = max(spend_velocity, deadline_proximity, anomaly). فشارِ بالا → epoch کوتاه (۱۵min)، آرام → بلند (۱۲۰min). **همیشه سایه‌ی $0** — هیچ enforce. فعلاً fitness مقادیر neutral stub (0.5) دارند چون «۴ هفته داده لازم است».

### ۵.۴ تلگرام — ۸ کانالِ انسانی موجود

| دستور/کار | کار | وضعیت |
|---|---|---|
| `/status` | snapshot فقط‌خواندنی | ✅ |
| `/lead name\|AUD\|cell` | mint LEAD PROPOSAL | ✅ |
| کارتِ تأیید | ۳-button human-append → settle | ✅ |
| کارتِ RFC | `[merge]/[reject]` doctor | ✅ |
| `/stop` | STOP-ORGANISM | ✅ |
| `/review` `/books` `/sync` | حسابداریِ گفت‌وگویی | ✅ (پشتِ flag) |
| `_dispatch_act` | out-of-band act requests | ✅ |
| `/reentry` | Re-entry Packet پس از gap | ✅ |

> **گلوگاهِ زنده‌ی تلگرام:** `governor debate failed (non-fatal): KeyError: 'text'` و
> `price_in/price_out در budgets.yaml قفل نشده`. این دو خطا در governor-alerts تکرار می‌شوند و
> مسیرِ debate + llm-epoch را silently می‌شکنند.

---

## ۶) نقشه‌ی کاملِ کانال‌ها (CHANNEL MAP)

| کانال | جهت | محتوا | گیت | وضعیت |
|---|---|---|---|---|
| Telegram poll | inbound | دستورِ مالک + کارت‌ها | allowlist + token | ✅ زنده |
| Telegram push | outbound | کارت/کار/نوتیف | — | ✅ زنده |
| genome ledger | append-only | LANGAR hash-chain | is_human=1 or beat=1440 | ✅ زنده |
| chrono.db | single-writer SQLite | heartbeat/HLC/effects | beat barrier | ✅ زنده |
| ORGANISM-STATE.json | machine-state | full snapshot هر tick | LockedJson | ✅ زنده |
| cortex-state.json | machine-state | مغز cycle | LockedJson | ✅ زنده |
| heart-shadow-latest | machine-state | ۳ سنجه + period | LockedJson | ✅ زنده |
| HTTP :8771/:8772/:8773 | read API | state + /ask | loopback bind | ✅ زنده |
| events.jsonl | append-only | اتوماسیون dashboard | content-free | ✅ زنده |
| **Proposal delivery** | **پاها → انسان** | **کارت‌های پیشنهاد** | **—** | **🔴 گسستِ G1** |
| **PocketSmith API** | inbound مالی | txn | `OCTOPUS_WIRE_POCKETSMITH` | 🔴 خاموش |
| **ps_writeback** | outbound مالی | labels | flag | 🔴 stub |
| Email inbound | inbound | ایمیل | `OCTOPUS_WIRE_EMAIL` | 🔴 خاموش |

---

## ۷) پیش‌بینیِ پتانسیل‌ها — اگر روشن کنیم چه می‌شود؟

> هر ردیف: فلگ → اثرِ اول → اثرِ ثانویه → ریسک.

| # | فعال‌سازی | اثرِ اول | اثرِ ثانویه | ریسک |
|---|---|---|---|---|
| **A** | **بستنِ G1: Proposal Router** (wiring، نه flag) | همه‌ی پاها به تلگرام وصل | `velocity` از heartbeat به proposal-flow می‌رسد؛ `_proposals_emitted>0` | پایین — فقط wiring |
| **B** | **بستنِ G2: اولین مسیرِ پولیِ paper** (مثلاً Lead-نقاشی end-to-end) | `confirmed_revenue>0` | `velocity` ↑، `delta_self` از صفر خارج، حلقه‌ی یادگیری مغز داده می‌خورد | متوسط — نیاز به verdict |
| **C** | `OCTOPUS_WIRE_LEAD_DISCOVERY=1` | sense→score→propose لید | لیدِ جدید → quote → درآمد | پایین — propose-only |
| **D** | `OCTOPUS_WIRE_POCKETSMITH=1` | txn زنده از API | حافظه‌ی مالیِ واقعی، dashboardِ صادق | متوسط — credential مالک |
| **E** | `ACTIVATION-SELF-IMPROVE-AUTO.flag` | مغز ۳ knob را خودش تنظیم می‌کند | حلقه‌ی یادگیری‌ی L1 بسته می‌شود | پایین — whitelist محدود |
| **F** | `CORTEX_IGNITION=1` | attention mechanism (GWT) | urgent signal برنده می‌شود و broadcast | متوسط — رفتارِ مغز تغییر می‌کند |
| **G** | `OCTOPUS_WIRE_BIO=1` | ضربانِ زیست‌شناختی | با درآمد، mass↑ و period↓ | بالا (فعلاً mass=1) |
| **H** | `OCTOPUS_WIRE_EVOLUTION=1` | MAP-Elites tournament | RFC‌ها در نسل‌ها بهتر می‌شوند | متوسط |
| **I** | `OCTOPUS_WIRE_BOX=1` | Box-of-Agents micro-world | شبیه‌سازیِ تکامل پیش از پیشنهاد | متوسط |
| **J** | `ACTIVATION-CODE-AUTONOMY.flag` | خود-تغییرِ کد | ارگانیسم کدِ خود را بهبود می‌دهد | **بالا** — ۷ گیت ولی |

> **ترتیبِ پیشنهادی (بالا→پایین ریسک، بالا→پایین بازده):** **A → E → C → B → D → F → H → G → I → J.**
> هرگز قبل از A+B به J نرسید — خود-تغییرِ کد بدونِ سیگنالِ واقعی خطرناک است.

---

## ۸) گسست‌ها و ضعف‌های تایید‌شده (FAILURES)

### ۸.۱ خطاهای زنده (از governor-alerts، beat 7119)
- `governor debate failed: KeyError: 'text'` — مسیرِ debate در epoch silently می‌شکند (احتمالاً LLM response shape).
- `governor llm epoch failed: price_in/price_out در budgets.yaml قفل نشده` — price قفل نیست → fallback به dry.
- `invoice persist failed: PermissionError WinError 5` — رقابتِ فایل روی `LEAD-REV.json.tmp` (LockedJson ولی باز هم race).
- `tg_api editMessageText failed: HTTPError` — تلگرام edit‌ها گاهی fail.

### ۸.۲ گسست‌های ساختاری (Deep-Scan یافته‌ها)
1. **G1 — Proposal delivery gap** (بالا). پاها پیشنهاد می‌سازند ولی هیچ‌کس تحویل نمی‌گیرد.
2. **G2 — No live revenue path** (بحرانی برای یادگیری). velocity=0.083، delta_self=0.
3. **G3 — Learning loop effectively open** (بحرانی برای تکامل). `measure()` صفر می‌بیند.
4. **G4 — Parallel intake intersection** (ریسکِ لیدِ گم‌شده). دو مسیرِ intake ناسازگار.
5. **LiveLoop advisory subscriber no-op** — `_emit_advisory()` خطِ 157 `pass` است؛ subscriber‌ها notify نمی‌شوند.
6. **TOCTOU در `_next_qt_num`** (lead_quote) — رقابت روی شماره‌ی quote.
7. **`backup_health()` بدونِ consumer** — OBS-02 fix آماده ولی کسی نمی‌خواند.
8. **`CHRONO_RETAIN_BEATS=0`** — جدول‌های chrono بی‌نهایت رشد می‌کنند.
9. **`precision_weight` disabled** (`HEART_PRECISION_WEIGHT=0`) — active-inference gain scheduling خاموش.
10. **`E_shadow` locked** (`HEART_W_SHADOW=0.0`) — جمله‌ی یادگیریِ قلبِ سایه خاموش.

### ۸.۳ «ژنتیک پُر، عملکرد کم» — ریشه‌یابی
| ریشه | شواهد |
|---|---|
| **زیرساختِ کامل روی بدنِ فلج** | ۱۲ زیرسیستمِ مغز + ۳ لایه‌ی قلب + ۸ کانالِ تلگرام، ولی proposals_emitted=0 و revenue=0 |
| **حلقه‌ی یادگیری بدونِ سیگنال** | delta_self=0 چون velocity_stream خالی است چون attribution صفر است |
| **هر فلگِ کم‌ریسک هم خاموش** | ۵۸ OCTOPUS_WIRE_*، اکثر OFF — حتیbcm/sparse/epistemics که در profile‌اند به‌سختی داده دارند |
| **wiring کامل ولی consumer ناقص** | LiveLoop یک bus می‌سازد ولی advisory subscribers no-op‌اند؛ legs emit می‌کنند ولی consumer نیست |

---

## ۹) نردبانِ فعال‌سازی برای ایجنتِ بعدی (عملی، کم‌ریسک→بالا‌ریسک)

> **اصل:** هیچ کدِ جدیدی ننویس تا G1/G2 نبسته شود. همه‌چیز wiring + verdict است.

### فاز ۱ — وصل‌کردنِ بدن (کم‌ریسک، wiring صرف)
- [ ] **۱.۱ Proposal Router بساز** (توصیه: در `live_loop.py` یا `wiring.py` تابعی که هر N beat `leg._proposals_emitted` را gather کند و کارتِ تلگرامی بسازد). ← بستنِ G1.
- [ ] **۱.۲** intake adapter (G4): یکی از دو مسیرِ lead را canonical کن. توصیه: `LiveLoop.process_lead` را به `lead_quote.create_quote` وصل کن.
- [ ] **۱.۳** advisory subscriber no-op را پر کن (live_loop.py خط 157) — signals واقعاً broadcast شوند.
- [ ] **۱.۴** `live_loop._emit_advisory` را تست کن: subscriber‌ها notify می‌شوند؟

### فاز ۲ — روشن‌کردنِ حلقه‌ی یادگیری
- [ ] **۲.۱** `ACTIVATION-SELF-IMPROVE-AUTO.flag` بساز (مالک) → مغز ۳ knob را خودش تنظیم می‌کند. ← E.
- [ ] **۲.۲** `goal_directed.measure()` را گسترش: به‌جز ۳ کلید، `velocity_per_hr` و `proposals_delivered` را هم ببین. ← بستنِ G3.
- [ ] **۲.۳** `OCTOPUS_WIRE_LEAD_DISCOVERY=1` → لیدِ جدید → quote. ← C.

### فاز ۳ — اولین مسیرِ پولیِ paper (با verdict)
- [ ] **۳.۱** lead discovery → `lead_to_intake` → `create_quote` → Telegram draft → مالک ارسال → `mark_sent` → revenue tracking. ← بستنِ G2.
- [ ] **۳.۲** بعد از اولین CONFIRMED: `velocity` ↑، `delta_self` خارج از صفر، مغز برای نخستین‌بار outcome می‌بیند.

### فاز ۴ — پتانسیلِ پنهان
- [ ] **۴.۱** fix `governor debate KeyError: 'text'` (response shape).
- [ ] **۴.۲** fix `price_in/price_out` در budgets.yaml (verdict).
- [ ] **۴.۳** `CORTEX_IGNITION=1` → attention. ← F.
- [ ] **۴.۴** `OCTOPUS_WIRE_EVOLUTION=1` → MAP-Elites. ← H.
- [ ] **۴.۵** `OCTOPUS_WIRE_POCKETSMITH=1` (با credential مالک). ← D.

### فاز ۵ — عمیق (با احتیاط)
- [ ] **۵.۱** `OCTOPUS_WIRE_BIO=1` (فقط وقتی mass>2). ← G.
- [ ] **۵.۲** `ACTIVATION-CODE-AUTONOMY.flag` (فقط وقتی حلقه‌ی یادگیری سبز). ← J.

---

## ۱۰) قواعدِ سخت برای ایجنتِ بعدی 🔒

نقض = خرابیِ طراحی (از ORGANISM-SPEC §۳):

1. **I1 append-only** — ledger/SURVIVORS/heartbeat/لاگ هرگز بازنویسی/حذف.
2. **I2 تک-enforcer** — `budget_gate` تنها نقطه‌ی enforce؛ این لایه فقط MEASURE/propose.
3. **I3 fail-closed** — ناسازگاری تلمتری↔حسابداری = FREEZE + [CONFLICT]؛ واگرایی>۲۰% = STOP-METABOLIC.
4. **I4 اعداد از فایل** — هر عددِ تصمیم‌ساز از budgets.yaml.
5. **I5 گیت دوقفله‌ی زنده** — هیچ مسیرِ خرج‌دار پیش از 2026-07-21 و بدون `ACTIVATION-*.flag`.
6. **I6 budgets.yaml فقط‌خواندنی** (H7).
7. **I7 پذیرش فقط انسانی** — «پذیرفته» = کلیکِ انسان در Telegram + تطبیق.
8. **I8 ضدسرطان** — σ≤1، MAX_CELLS=6، عمقِ spawn=1، SPAWN فقط PROPOSAL.
9. **I9 secret** — کلید فقط از env؛ هرگز در md/لاگ/exception.
10. **I10 ضدتزریق** — topic = داده؛ فقط whitelist؛ GUARD_SENTENCE.
11. **TINV-7** — هیچ اثرِ برگشت‌ناپذیر بدونِ LANGAR-append قبلی settle نمی‌شود.
12. **§۴ خطای خاموش ممنوع** — هر استثنا → alert + ادامه.

**کارهایی که بدونِ verdict نکن:** بازکردنِ مسیرِ پولی، خاموش‌کردنِ shadow، تغییرِ سقف، publish/send، دست‌زدن به budgets.yaml، اعمالِ code_autonomy.

---

## ۱۱) اجرای سریع (مرجع)

```bash
# تستِ کل
python -X utf8 "F:\backup\_ops\tests\run_all.py"

# state زنده
curl -s http://127.0.0.1:8771/api/organism | python -m json.tool
curl -s http://127.0.0.1:8772/api/cortex | python -m json.tool

# خطاها
tail -40 _ops/governor/governor-alerts.md

# تعویضِ flag بدون restart (runtime)
# → ویرایشِ _ops/OCTOPUS-flags.cmd

# kill تمیز
touch _ops/STOP-ORGANISM
```

---

## ۱۲) فهرستِ منابع (برای دیپ‌خوانیِ ایجنتِ بعدی)

| موضوع | فایل |
|---|---|
| spec کل | `_ops/ORGANISM-SPEC.md` |
| حلقه‌ی اصلی | `_ops/organism.py` |
| مغز | `_ops/cortex/cortex.py` |
| قلبِ سایه | `_ops/heart/producers.py` + `control_law.py` |
| pacemaker | `_ops/chrono.py` |
| cardiac | `_ops/cardiac.py` |
| پایِ پایه | `_ops/legs/leg.py` |
| پای درآمدی | `_ops/legs/lead_quote.py` |
| تلگرام | `_ops/budget/approval_channel.py` |
| گاورنر | `_ops/budget/governor_epoch.py` |
| اهدافِ مالک | `_ops/GOALS-OCTOPUS.md` |
| نمونه‌ی handoff | `03 - Projects/Ziman Galerry/00-Control/AGENT-HANDOFF.md` |

---

> **پیامِ پایانی برای ایجنتِ بعدی:** این ارگانیسم **ناقص نیست — ناتمام است.** مغز و قلب
> کامل‌اند؛ بدن منتظرِ wiring است. **اولین و مهم‌ترین کار: بستنِ G1 (Proposal Router) و
> G2 (اولین مسیرِ پولی).** هیچ‌چیزِ دیگری قبل از این، بازدهِ واقعی نمی‌دهد. وقتی velocity
> از ۰.۰۸۳ خارج شد، تمامِ زیرساختِ عصبی که الان idle است خودبه‌خود بیدار می‌شود.
