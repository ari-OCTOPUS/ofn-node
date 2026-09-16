---
type: proposal
subtype: INFRA_PROPOSAL
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-verdict
tags: [octopus, gateway, litellm, worker, routing, proposal]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
relates_to: "[[OCTOPUS-BASE-MAP-v0]] §I + §I₂ · files(1).zip"
---

# GATEWAY WIRING — راه ب (GLM + DeepSeek روی LiteLLM)

> **این چیست:** proposalِ سیم‌کشیِ دو حمال (GLM=کدنویس، DeepSeek=دیباگ/حجم) به gateway ِ `files(1).zip`. طبقِ **propose-only** + **owner-applied**: من فقط diff می‌دهم؛ **تو Windows-side اعمال/commit می‌کنی**. هیچ کلیدی این‌جا نیست (I9). این گرهِ `INFRA_PROPOSAL` §I نقشه را از «کاندید» به «سیم‌کشی‌شدهٔ shadow» می‌برد — هنوز زنده/enforce نمی‌شود.

## اصل صفر (سه سؤال، قبل از اعمال)
1. **کِی دلار می‌شود؟** این حمال‌ها کدِ سه پا (Lead-نقاشی اول) را تولید می‌کنند → خروجی به سمتِ درآمدِ paper. `[EST]`
2. **ارزان‌ترین نسخه؟** GLM Lite $۱۸ + DeepSeek top-up ~$۱۰ = زیرِ سقفِ $۸۰. ✅
3. **اگر ۵ روز غیبت زدی؟** gateway روی loopback و shadow می‌ماند؛ هیچ مسیرِ خرج‌دارِ auto باز نمی‌شود (I5) → می‌چرخد، نمی‌میرد. ✅

---

## گام ۱ — کلیدها در `.env` (فقط دستگاهِ تو، هرگز در چت/git)
به `.env.example` این دو خط اضافه شود (مقدار را در `.env` واقعی بگذار):
```
DEEPSEEK_API_KEY=
ZAI_API_KEY=
```
و در سرویسِ `litellm` ِ `docker-compose.yml` (بخشِ environment):
```
DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY:-}"
ZAI_API_KEY: "${ZAI_API_KEY:-}"
```

## گام ۲ — افزودن دو worker به `litellm_config.yaml` → `model_list`
```yaml
  # ---------- WORKER: GLM (کدنویسِ اصلی) ----------
  - model_name: glm-coder
    litellm_params:
      model: openai/glm-4.6                 # ⚠️ verify مدل‌id فعلیِ planت (GLM-5.2؟) در docs.z.ai
      api_base: https://api.z.ai/api/paas/v4  # ⚠️ verify base_urlِ OpenAI-compatible planت
      api_key: os.environ/ZAI_API_KEY

  # ---------- WORKER: DeepSeek (دیباگ + حجم) ----------
  - model_name: deepseek-bulk
    litellm_params:
      model: deepseek/deepseek-v4-flash     # deepseek-chat بعد از 2026-07-24 deprecate → v4-flash
      api_key: os.environ/DEEPSEEK_API_KEY
```
و در `fast` group هم به‌عنوان fallbackِ ارزان اضافه‌شان کن (اختیاری ولی توصیه):
```yaml
  - model_name: fast
    litellm_params:
      model: deepseek/deepseek-v4-flash
      api_key: os.environ/DEEPSEEK_API_KEY
```

## گام ۳ — routing در `litellm_settings.fallbacks`
```yaml
  fallbacks: [
    {"glm-coder": ["deepseek-bulk", "fast"]},
    {"deepseek-bulk": ["fast"]},
    {"heavy-reasoning": ["fast"]}
  ]
```
منطق: اگر GLM بیفتد → DeepSeek؛ اگر DeepSeek → fast. هیچ‌وقت سیستم نمی‌ایستد.

## گام ۴ — `budgets.yaml` (فقط verdict تو — I4/I6)
`budgets.yaml` فقط‌خواندنی و عدد-از-فایل است؛ **من دست نمی‌زنم**. تو این‌ها را verdict بده:
- `routing.glm.base_url` و `routing.deepseek.base_url` (تا آن‌موقع مسیرِ orchestr **shadow**).
- سقفِ ماهانهٔ per-worker (پیشنهاد: GLM subscription جدا؛ DeepSeek زیرِ سقفِ $۸۰).

## گام ۵ — اعمال + smoke (Windows-side، خودت)
```
make up
make health          # liveness + readiness سبز
# تستِ هر worker از میانِ گیت‌وی:
curl ... -d '{"model":"glm-coder","messages":[{"role":"user","content":"تست"}]}'
curl ... -d '{"model":"deepseek-bulk","messages":[{"role":"user","content":"تست"}]}'
make spend           # هزینه ثبت شد؟
```
سبز شد → path-scoped commit فقط این فایل‌ها (`litellm_config.yaml`, `docker-compose.yml`, `.env.example`). **`.env` هرگز.**

## گام ۶ — ثبت در Ledger (این تصمیم گم نشود)
یک `NOTE(INFRA_PROPOSAL)` در ledger ژنوم append شود:
> «gateway wiring: glm-coder + deepseek-bulk اضافه شد؛ shadow؛ base_urlها verify-pending؛ کلیدها env-only.»

---

## verify-debt (اخلاقِ معرفتی — قبل از اتکا)
- `[EST]` model-id و `api_base` ِ GLM planت را در **docs.z.ai** تأیید کن (GLM Coding Plan ممکن است endpoint/id متفاوت از pay-per-token بدهد).
- `[EST]` آیا GLM Coding Plan (subscription) در LiteLLM/OpenAI-compatible کار می‌کند یا فقط داخلِ coding-agentها؟ با یک call تست کن — اگر نه، fallback: DeepSeek حملِ اصلی + GLM از راهِ Claude Code.
- `[تثبیت‌شده]` DeepSeek = OpenAI-compatible، در LiteLLM با `deepseek/` provider کار می‌کند.

## گاردریل‌ها
propose-only · secret env-only (I9) · gateway روی `127.0.0.1` · cost cap `$۸۰/۳۰d` + fail-closed دست‌نخورده · هیچ money-effector · commit path-scoped Windows-side.

## checkpoint
پس از سبزشدنِ smoke، راه ب کامل است و gateway آمادهٔ P3 (تلگرام) و بعد P4 (Lead-نقاشی) است. **قدمِ بعدی روی نقشه بی‌تغییر: P3.**
