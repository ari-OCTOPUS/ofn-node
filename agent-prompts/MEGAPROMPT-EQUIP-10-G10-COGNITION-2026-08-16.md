---
megaprompt_title: EQUIP موج E2 — گروه ۱۰ هوش، استدلال، Self-model
version: "1.0"
sequence: 10
group: 10
wave: E
requires: "G9 evidence not FAIL"
next: "MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md (Wave E FINAL)"
scan_after: true
written_by: "Cursor Grok 4.6 — 2026-08-16"
branch_name: "equip/g10-cognition-20260816"
---

# پیست

۱) SHARED · ۲) همین فایل.
آخرین گروه پیاده‌سازی. مدل/diagnostic/self-report را به authority تبدیل نکن.

# ماموریت: Governed Cognitive and Self-Model Layer

model router، Fugu، DeepSeek worker، hypothesis engine، causal components،
confidence ledger، SOG/Kalman diagnostics و SELF-MODEL-REALITY را کشف کن.

هدف: کیفیت تصمیم بالاتر؛ بدون اینکه مدل یا self-report حاکم شود.

## حقیقت این vault

- Fugu = مغز اصلی (پروب اخیر 429 — دوباره نزن).
- DeepSeek = worker ارزان. بودجهٔ هفتگی کم‌مصرف؛ ریسک = «مصرف‌کننده» نه دلار.
- live/center/gateway = `qwen2.5:1.5b` — به 7b برنگردان.
- CORTEX_HYPOTHESIS را عوض نکن.
- SOG/Kalman = diagnostic. C-029 کف عددی دارد؛ ZeroDivision برنگردان.
- identity_health knob می‌سازد — به پول/halt/مجوز وصل نکن (DA-5 / VOTE 3 باز).
- ADR-013 causal-selfmodel در این vault **REJECTED** (honest negative).
  ادعای علی را دوباره به‌عنوان authority برنگردان.
- S6 predictor = METAPHOR؛ persistence سایه در `_ops/predictor/persistence.py`.
  p_base را عوض نکن.
- claim_hypothesis API ممکن است صفر caller تولیدی داشته باشد — سیم بی‌رأی نکن.

## الزامات vertical slice

- routing policy: task class، privacy، cost، latency، risk.
- fallback chain محدود و observable.
- structured output schema برای plan / hypothesis / evidence / proposal.
- planner ≠ executor ≠ verifier. verifier context آلودهٔ executor را
  بدون پاک‌سازی نگیرد (MEA / LongHorizon-Harness).
- hypothesis: evidence level + falsification condition.
- confidence با outcome ledger کالیبره شود.
- causal claim جدا از correlation/prediction.
- self-model فقط از evidence runtime به‌روز شود.
- capability ادعایی بدون passing probe → VERIFIED نشود.
- identity_health: decomposition + CI/uncertainty.
- مدل اجازهٔ تغییر policy / goal / identity / owner rule ندارد.

## سناریوی acceptance

سه task: coding، retrieval، causal analysis.
نشان بده router مدل درست را انتخاب می‌کند، verifier خطای ساختگی را کشف
می‌کند، self-model فقط با نتیجهٔ probe به‌روز می‌شود.

پروب پولی نزن. coding/retrieval را با مدل محلی 1.5b یا fixture بساز.
causal analysis = تشخیص «این همبستگی است نه علت» روی دادهٔ مصنوعی.

## اسکن تخصصی

model-routing loop · unverifiable self-claims · confidence inflation ·
evaluator contamination · reward hacking · authority leakage from
diagnostics · goal drift · unsafe fallback · malformed structured output ·
hidden activation of disabled components.

## TECHNOLOGY OPTIONS — GROUP 10

تحقیق جدا 2026-08-16.

PRIMARY PAPERS:

- LLMRouter 2608.06867 (2026-08-07) — routing as sequential decision.
  https://huggingface.co/papers/2608.06867
- Kimi K3 2607.24653 — open MoE؛ **جایگزین Fugu بدون رأی مالک نیست.**
  https://huggingface.co/papers/2607.24653
- SkillOpt 2605.23904 — skills as external state.
- SkillsVote 2605.18401 — skill lifecycle governance.
- COLLEAGUE.SKILL 2605.31264 — فقط از Write Gate.
- ARIS 2605.03042 — adversarial harness پژوهشی.
- OTel GenAI `validate` span برای verifier/critic (گروه ۶) — اگر موجود است
  هر guardrail را span جدا pass/fail کن.
- LangGraph hierarchical subgraph / Magentic-One — فقط الگوی routing
  observable؛ هسته را عوض نکن.

DO

- router policy شفاف. planner ≠ executor ≠ verifier.
- skills فقط Write Gate + SkillsVote-style.
- SOG/Kalman diagnostic بمانند.

DO NOT

- Ouroboros / Co-Evolution 2608.10299 / Frontis-MA1 2607.28568 را مجوز
  تغییر policy/goals/identity بدان.
- CORTEX_HYPOTHESIS یا Council را مخفیانه فعال نکن.
- self-claim بدون probe → VERIFIED.

## خروجی

`06-EVIDENCE/EQUIP-G10-COGNITION-2026-08-16.md`.
سپس اسکن نهایی Wave E توسط ایجنت مستقل.
