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
| **Memory Gate** | `_ops/memory/gate.py` + `memory_store.py` | `OCTOPUS_WIRE_MEMORY_GATE` | ❌ صفر producer | ✅ (وقتی صدا شود) | **library-only** |
| **Event Spine** | `_ops/spine/event_spine.py` | `OCTOPUS_WIRE_SPINE` | ❌ صفر `dual_write` caller | ✅ (وقتی صدا شود) | **library-only** |
| **Context fencing** | `_ops/cortex/context_fence.py` | `OCTOPUS_WIRE_CONTEXT_FENCE` | ❌ در مسیرِ cortex نیست | ✅ (وقتی صدا شود) | **library-only** |

**خلاصه:** ۶ تکه reachable/wired؛ ۳ تکه library-only (incubating). زنجیرهٔ کامل
تصمیم→اثر→نتیجه **سرتاسر اثباتِ‌کارکرد** دارد (Lead recorder از drون `lead_discovery_beat`
یک receiptِ E1 + outcomeِ delivered می‌سازد، `memories_used` را از Memory Gate پر می‌کند
اگر db موجود باشد، verdict=PENDING بدونِ جعل). سه تکهٔ باقی «کتابخانه‌اند»: منطق + تست +
flag دارند ولی هنوز از هیچ beatِ ارگانیسم صدا زده نمی‌شوند.

## چرا سه تکه عمداً هنوز سیم‌کشی نشده (نیازمندِ رأیِ مالک)
هر کدام یک **انتخابِ طراحیِ محتوایی** است، نه کارِ مکانیکی — و هر کدام مسیرِ حساسِ متفاوتی را لمس می‌کند:
- **Memory Gate** ← منبعِ حافظه چیست؟ (owner-factها از تلگرام؟ self-knowledge از دکتر؟ سنتزِ LLM؟)
  این تعیین می‌کند «ارگانیسم چه چیزی به‌یاد می‌سپارد». `self_knowledge` سخت‌گیرانه ADVISORY می‌ماند.
- **Event Spine** ← کدام نقاطِ انتشار dual-write کنند (outcome/decision/mission)؟ شadow-log، اما چند call-site.
- **Context fencing** ← کجای مسیرِ داغِ LLMِ cortex اعمال شود؟ بالاترین ارزشِ امنیتی (ضدِ tekحریفِ prompt)
  ولی مسیرِ مرکزیِ تماسِ مدل را لمس می‌کند.

## کارهای owner-gated (به ترتیبِ ارزش)
1. **سیم‌کشیِ ۳ تولیدکنندهٔ باقی** (Memory Gate / Event Spine dual-write / context fencing در cortex) — هرکدام flag-off، additive، با تستِ reachability مثلِ `test_lead_outcome_wiring`.
2. **decomposeِ `wiring.py`** (۲۳۵۴ خط، ۶۶ def — بافتِ عصبیِ مرکزی): strangler façade **high-blast-radius**؛ نیازمندِ staging + پوششِ کاملِ beat، نه اجرای کورِ خودمختار.
3. **Mutation Chamber** (سندباکسِ جهشِ کد، بدونِ شبکه/egress): قابلیتِ خودتغییردهیِ **جدید**؛ نیازمندِ scopeِ صریحِ مالک — نه زیرِ ماموریتِ «یکپارچه‌سازیِ تکه‌های موجود».
4. **`journal_bridge` CoA** (تنها redِ باقیِ suite): نگاشتِ category→حساب (تست `5200` انتظار دارد، کد `6000`) — رأیِ حسابداریِ دامنهٔ پول.
5. **فعال‌سازی:** حذفِ `_ops/STOP-ORGANISM` (ارگانیسم از ۱۹ژوئیه halt است) + ستِ flagها + restart.

## ناوردی‌های حفظ‌شدهٔ این جلسه
- STOP-ORGANISM بایت‌به‌بایت دست‌نخورده (۳۳ بایت، ۱۹ژوئیه)؛ درختِ زنده `F:\backup` کاملاً untouched؛ ارگانیسم restart نشد.
- هر کامیت additive + flag-off + مستقل + FF-cleanِ master + push به germline (`E:/germline/octopus.git`).
- صفر secret/پول/send/LIVE؛ kill-switch هرگز حذف/ضعیف نشد؛ هیچ تستی جعل نشد (تنها redِ باقی = pre-existingِ CoA، صادقانه گزارش‌شده).

مرجع‌ها: [[CONTROL-PLANE-HALT-2026-07-20]] · [[EFFECT-TAXONOMY-E0-E4-2026-07-20]]
