# ADR-037: Hypothesis Engine — زیرسیستم Pydantic مستقل با adapter نازک

**وضعیت:** ACCEPTED — رأیِ مالک 2026-08-12 (گزینهٔ A: خودتقویتِ آزمون‌پذیر، invariant صداقت دست‌نخورده)
**تاریخ:** 2026-08-12 · **شماره:** 037 (بعد از ADR-036)

---

## زمینه

Hypothesis Engine (spec + impl + آزمایش) با مرجعِ Pydantic v2 + `BaseBrain` + `async` ساخته شده
که با قرارداد `_ops` (stdlib + تابعی) مغایر است. طبق اصل مرجعِ پروژهٔ ادغام: **مرجع پیروز است**
→ زیرسیتم مستقل در `_ops/hypothesis_engine/`، اتصال به cortex فقط با adapter نازکِ propose-only.

## تصمیم

1. **کابین Pydantic مستقل:** `impl/{base_brain,schemas,hypothesis_brain}.py` — تنها جایی که
   Pydantic مجاز است. وابستگی `pydantic>=2.0` (و `numpy` فقط برای experiments/) صریحاً اضافه شد.
2. **Registry + Validator:** `architecture/hypothesis-registry.yaml` +
   `_ops/scripts/validate_hypothesis_registry.py` — read-only، exit 0/1، قیود سخت
   (kill_condition در TESTING اجباری، may_gate فقط در EVIDENCED، سقف ۲۰ فعال، EIG≥0.3، cost≤4h).
3. **Adapter نازک:** `hypothesis_brain_run(cycle)` در `cortex.py` — propose-only، fail-soft،
   **بدون** دسترسی به ledger/Gate/autonomy_grant؛ خروجی فقط ranking برای کارتِ advisory از طریق
   live_loop. پیش‌فرض **خاموش** (`CORTEX_HYPOTHESIS=0`) تا رأی/فعال‌سازیِ صریحِ مالک.
4. **الگوی ADR-034:** neural→proposal — اینجا هم hypothesis→proposal؛ هیچ اجرای مستقیم.

## شواهد (evidence_level = SHADOW، شبیه‌سازیِ بازتولیدشده)

از آزمایش سه‌ایجنتی (۶۰۰ run، `_ops/hypothesis_engine/experiments/results.csv` + `analysis.py`،
بازتولیدِ محلی 2026-08-12):

| پیش‌بینی | نتیجه | داوری |
|---|---|---|
| P1: B بهتر از A در deceptive | 97% vs 0% کشف | ✅ قاطع |
| P1: B بهتر از C در deceptive | p=0.32، δ=−0.11 | ❌ رد |
| P2: B در benign بهتر نیست (تعامل) | B کندتر از A (p=0.0006) | ✅ تأیید |
| P3: ≥20% falsified-assist | 0/97 در deceptive | ❌ رد (معیار معیوب) |

**نتیجهٔ صادقانه:** مزیت فرضیه‌محوری **شرطی بر فریبندگی محیط** است؛ برتری عمومی بر novelty
اثبات نشد. این رکورد با هشدار «not superior to novelty» در capabilities-registry ثبت شد.

## رأیِ فاز ۰ (گزینهٔ A — پذیرفته‌شده)

- invariant صداقتِ بار-دار (`ARCHITECTURE-BIBLE.md:49-51` — «بدون phenomenal consciousness /
  qualia / sentience») **دست‌نخورده** ماند.
- BIBLE فقط **بسط** می‌یابد (پیوستِ §Hypothesis Engine به‌عنوان ابزارِ خودتقویتِ آزمون‌پذیر).
- خودِ موتور فرضیه، گزارهٔ «Octopus is AGI» را به‌دلیلِ `testability=0` رد می‌کند (auto-FALSIFIED)؛
  و آزمایشِ بازتولیدشده (B ≯ C) هرگونه ادعای برتریِ کلی را هم نقض می‌کند. مسیرِ صادقِ
  «هر راه را امتحان کن» = همان ازمون‌پذیری + گیت‌های مالک/ایمنی، بدونِ حتی یک ادعای «من AGI هستم».

## پیامدها

- **مثبت:** مسیرِ خودتقویتِ آزمون‌پذیر در حافظهٔ Octopus بدونِ تلهٔ خودفریبی؛ fail-closed در
  همهٔ مرزها (ledger/Gate/autonomy_grant هرگز لمس نمی‌شوند).
- **هزینه:** وابستگیِ pydantic به `_ops` (محدود به کابین)؛ پیچیدگیِ adapter.
- **خنثی‌شده:** هیچ اثر جانبیِ تولیدی (payment/email/lead/CRM) — همیشه رأیِ انسانی جدا.

## بدیل‌های ردشده

- **ادغام مستقیم در cortex بدون کابین:** نقضِ قرارداد stdlib `_ops` → رد.
- **may_gate در TESTING:** نقضِ fail-closed → رد.
- **ادعای AGI بدون invariant بازبینی:** نقضِ ADR-033 و DNA ی «شواهد-نه-ادعا»، و نقضِ دادهٔ
  آزمایشِ خود سیستم (B ≯ C) → رد.
