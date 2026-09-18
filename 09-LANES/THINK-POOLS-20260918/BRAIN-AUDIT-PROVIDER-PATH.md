# BRAIN AUDIT — مسیر پروایدرها (بخش اول ممیزی مغزها، اجراشده)

دستور مالک: «پروایدرها را درست کن، تموم مسیر». نتیجهٔ زندهٔ نهایی:

| پروایدر | مدل | دایالکت | جواب smoke | تأخیر | حکم |
|---|---|---|---|---|---|
| local-llamacpp-180 (رایگان، برد ۱۸۰) | qwen3-0.6b-q4_0 | llamacpp | ✅ (با تکرار — مشخصهٔ 0.6b) | 2.6s | CONGRUENT |
| deepseek | deepseek-flash | openai | ✅ Paris | 0.78s | CONGRUENT |
| openai | gpt-5.6-terra | openai-v2 | ✅ Paris | 2.07s | **DRIFT→FIXED** |
| anthropic | claude-sonnet-5 | anthropic | ✅ Paris | 1.43s | **DRIFT→FIXED** |
| gemini | gemini-3.8-flash | google | ✅ Paris | 1.44s | **DRIFT→FIXED** |
| sakana-fugu | fugu-ultra | openai | ⛔ اعتبار تمام (429) | — | EXHAUSTED (درست حذف و جایگزین شد) |

## سه نقصِ مسیر که رفع شد (هرکدام با تشخیص دقیق، نه حدس)

1. **env-split:** کلیدها بین `secrets.env` و `external-models.env` تقسیم بودند؛
   کارخانه حالا خودش هر دو را load می‌کند (مقدارها هرگز چاپ نمی‌شوند).
2. **openai 400:** RemoteBrain پارامتر قدیمی `max_tokens` می‌فرستاد؛ مدل‌های جدید
   `max_completion_tokens` می‌خواهند. آداپتور `OpenAICompatBrain` (فقط برای openai؛
   بقیه RemoteBrain دست‌نخورده).
3. **anthropic 400:** کلید workspace-scoped نیست ⇒ هدر `anthropic-workspace-id`
   لازم (شناسه‌ای که مالک ۰۹-۱۳ فراهم کرده؛ فقط نام env خوانده می‌شود).

## معماری نهایی

`brain_factory.build(tier)` → تصمیم از `provider_routing` (credit-aware،
tier-gated، pin-محترم) → endpoint از `chat_url()` رجیستری موجود → آداپتورِ
دایالکت درست → یک surface واحد `answer(task, prompt)`. Fail-closed: بدون
endpoint/کلید/مدل، خطا — نه حدس.

هزینهٔ کل smoke: ~۳۰۰ توکن خروجی در ۶ فراخوانی (چند سنت؛ زیر سقف ۲$ کمپین).
شواهد: `evidence/WHOLE-PATH-SMOKE.txt` · `evidence/BRAIN-FACTORY-MATRIX.txt`
