---
type: architecture
status: active
tags: [architecture, unification, spine, memory, events, decisions, outcomes, reachability]
created: 2026-07-20
updated: 2026-07-20
---

# وضعیتِ ستونِ فقراتِ یکپارچه — spine حافظه/رویداد/تصمیم/نتیجه

> نقشهٔ صادقانهٔ «چه چیزی واقعاً سیم‌کشی شده» طبقِ متدِ خودِ مالک: هر تکه روی **سه محور**
> نمره می‌گیرد — **flag** (وجودِ کلید) · **reachable** (آیا beat/producerِ واقعی صدایش می‌زند) ·
> **side-effect** (آیا اثرِ واقعیِ پایدار دارد). «wired» یعنی هر سه ✅. صرفِ وجودِ flag بدونِ
> caller = آنتی‌الگوی dead-flag (همان RUNNER_APPLY که مالک نقد کرد) — این‌جا صادقانه «library-only»
> برچسب می‌خورد، نه «done».

## ستونِ فقراتِ ساخته‌شده (همه روی master، همه flag-off، همه off-disk backup روی germline)

| تکه | فایل | flag | reachable | side-effect | نمره |
|---|---|---|---|---|---|
| **Taxonomy** (واژگانِ یگانه) | `_ops/outcomes/taxonomy.py` | — | ✅ همه import می‌کنند | ✅ | **بنیادی/wired** |
| **Decision Receipt** (immutable) | `_ops/outcomes/decision_receipt.py` | — | ✅ via Lead recorder | ✅ رسیدِ پایدار | **reachable** |
| **Outcome Store** | `_ops/outcomes/outcome_store.py` | — | ✅ via Lead recorder | ✅ رویدادِ پایدار | **reachable** |
| **Lead recorder** (تولیدکننده) | `_ops/outcomes/lead_outcome_recorder.py` | `OCTOPUS_WIRE_LEAD_OUTCOME` | ✅ `lead_discovery_beat` | ✅ receipt+outcome | **۳/۳ wired** |
| **HALT-ALL** (D-G) | `_ops/watchdog.py` + دو `.ps1` | — | ✅ همهٔ supervisorها | ✅ توقفِ احیا | **wired** |
| **E0–E4 effect matrix** | `taxonomy` + `decision_receipt` | — | ✅ receipt اعتبارسنجی | ✅ ردِ کلاسِ نامعتبر | **wired (validation)** |
| **Memory Gate** | `_ops/memory/gate.py` + `memory_store.py` | `OCTOPUS_WIRE_MEMORY_GATE` | ✅ `_record_lead_decisions` (episodic) | ✅ نوشتِ حافظه | **۳/۳ wired** (LEG-08) |
| **Event Spine** | `_ops/spine/event_spine.py` | `OCTOPUS_WIRE_SPINE` | ✅ `_record_lead_decisions` (dual-write) | ✅ رویدادِ SoT | **۳/۳ wired** (LEG-07) |
| **Context fencing** | `_ops/cortex/context_fence.py` | `OCTOPUS_WIRE_CONTEXT_FENCE` | ✅ `model_router.ask` (screen) | ✅ alertِ injection | **۳/۳ wired** (آیتم۲) |

> **به‌روزرسانی ۲۰۲۶-۰۷-۲۰ (شب، دستور «همرو انجام بده»):** هر سه تکهٔ library-only **reachable
> شد** (پشتِ همان flagهای پیش‌فرض‌خاموش، additive، fail-soft، تستِ reachability). دیگر
> **صفر dead-flag** در ستونِ فقرات. + قرمزِ حسابداریِ `journal_bridge` بسته شد (test-isolation،
> چارت دست‌نخورده) → **کلِ suite ۲۲۲/۲۲۲ سبز** (اولین‌بار در این قوس؛ capability marker نوشته شد).
> کامیت‌ها: `8373ec9`(حسابداری) `d859612`(spine) `0b338a2`(fence) `40c1ac4`(memory) روی master، germline backup.

**خلاصه:** اکنون **۹ تکه wired/reachable؛ صفر library-only، صفر dead-flag**. زنجیرهٔ کامل
تصمیم→اثر→نتیجه **سرتاسر اثباتِ‌کارکرد** دارد؛ سه تکهٔ حافظه/رویداد/فنس همه از beat صدا زده
می‌شوند (episodic write · dual-write SoT · screen ورودیِ LLM). همه پشتِ flagِ پیش‌فرض‌خاموش.

## سیم‌کشیِ سه تکه (چگونه reachable شد — همه additive/flag-off/fail-soft)
- **Memory Gate** → `_record_lead_decisions` یک حافظهٔ **episodic** از متادیتای تصمیم می‌نویسد
  (PII-free — فقط IDهای داخلی). منبعِ self-contained، نه owner-fact/LLM. `self_knowledge` ADVISORY ماند.
- **Event Spine** → همان helper زنجیرهٔ **decided→delivered** را با correlationِ مشترک dual-write می‌کند.
- **Context fencing** → `model_router.ask` ورودیِ LLM را **screen** می‌کند (observe-only؛ injection→alert؛
  هرگز prompt را mutate/block نمی‌کند — گامِ بلاک owner-gated).

## کارهای owner-gated (به ترتیبِ ارزش)
1. **decomposeِ `wiring.py`** (اکنون ~۲۴۲۰ خط پس از سیم‌کشی‌ها — بافتِ عصبیِ مرکزی): strangler façade
   **high-blast-radius**؛ نیازمندِ baselineِ تمیز + پوششِ کاملِ beat + verify، نه اجرای کورِ خودمختار.
2. **Mutation Chamber** (سندباکسِ جهشِ کد، بدونِ شبکه/egress): قابلیتِ خودتغییردهیِ **جدید**؛ نیازمندِ scopeِ صریحِ مالک.
3. **[P0 مالی] گاردِ drawdown:** implِ فرضیِ روی برنچِ `claude/three-heart-rhythm-math-c69082`
   **catastrophically stale** است (۳۲۷۱ فایل، ۳.۷M حذف) → **un-mergeable**. تنها مسیرِ امن =
   **re-implementِ تازه روی master** (additive به `budget_gate.py`، shadow-default، flag `HH_DRAWDOWN_ENFORCE`،
   spec از `test_drawdown_enforcer`) — ولی آستانهٔ spike یک **تصمیمِ سیاستِ مالیِ مالک** است. پیش‌نیازِ هر مسیرِ پول.
4. **فعال‌سازی (رأیِ مستقل و آخر):** حذفِ `_ops/STOP-ORGANISM` (ارگانیسم از ۱۹ژوئیه halt) + ستِ flagها + restart.

**بسته‌شده این دور (دستور «همرو انجام بده»):** قرمزِ حسابداری `5200/6000` (test-isolation، چارت دست‌نخورده،
suite ۲۲۲/۲۲۲ سبز) · سیم‌کشیِ هر ۳ تکهٔ library-only.

## ناوردی‌های حفظ‌شدهٔ این جلسه
- STOP-ORGANISM بایت‌به‌بایت دست‌نخورده (۳۳ بایت، ۱۹ژوئیه)؛ درختِ زنده `F:\backup` کاملاً untouched؛ ارگانیسم restart نشد.
- هر کامیت additive + flag-off + مستقل + FF-cleanِ master + push به germline (`E:/germline/octopus.git`).
- صفر secret/پول/send/LIVE؛ kill-switch هرگز حذف/ضعیف نشد؛ هیچ تستی جعل نشد (تنها redِ باقی = pre-existingِ CoA، صادقانه گزارش‌شده).

مرجع‌ها: [[CONTROL-PLANE-HALT-2026-07-20]] · [[EFFECT-TAXONOMY-E0-E4-2026-07-20]]
