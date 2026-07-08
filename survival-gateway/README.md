# Survival Stack — Layer 0 (Gateway) + Layer 5 (Risk-Governance)

اولین آجرِ سیستم: یک **gatewayِ ضدِ lock-in** که هر call به مدل از آن رد می‌شود. مبتنی بر **LiteLLM proxy** (open-source، MIT) — همان انتخابِ لایه‌ی ۰ در هَند‌آفِ AI/AGI. مدل = موتورِ تعویض‌پذیر؛ گیت‌وی = لایه‌ای که paradigm-shift نابودش نمی‌کند.

> **این آجر عمداً به GPU/مدلِ local وابسته نیست.** LiteLLM سبک است و روی هر VPS می‌چرخد. tierِ مدلِ localِ (Ollama) در آجرِ بعدی و بعد از دانستنِ مشخصاتِ Hetzner اضافه می‌شود.

---

## نگاشت به لایه‌های هَند‌آف
- **پوشش‌داده‌شده حالا:** Layer 0 (00-Orchestrator/router — سطحِ gateway)، Layer 5 (Risk-Governance: cost cap + kill-switch + audit).
- **آماده‌ی اتصال بعداً:** Layer 1 (heavy API tier وصل است؛ local tier معلق)، Layer 4 (Tools/MCP — LiteLLM از MCP پشتیبانی می‌کند، بعداً)، Layer 2 (vault/memory)، Layer 6 (golden set/eval).
- **مهم — scope صادقانه:** audit در این آجر فقط **call‌های مدل** را می‌پوشاند (spend logs + json logs). auditِ «tool call» و «memory write» که در charter آمده متعلق به Layer 4/Layer 2 است و اینجا **هنوز نیست**.

---

## پیش‌نیاز
Docker + Docker Compose. Postgres همراهِ compose می‌آید (نیازی به نصبِ جدا نیست — spend/budget/keys آنجا ذخیره می‌شوند).

## راه‌اندازی (۵ دقیقه)
```bash
cp .env.example .env
#  → LITELLM_MASTER_KEY و LITELLM_SALT_KEY و POSTGRES_PASSWORD را عوض کن،
#    و کلیدِ حداقل یک provider (ANTHROPIC/OPENAI/GEMINI) را بگذار.

make up          # بالا آوردن
make health      # باید liveness = "I'm alive!" و readiness db=connected بدهد

# تستِ یک call از میانِ گیت‌وی:
curl -s http://127.0.0.1:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"fast","messages":[{"role":"user","content":"سلام، تست"}]}'
```
داشبورد: `http://127.0.0.1:4000/ui` (کاربر `admin`، پسورد = master key).

---

## قراردادِ routing (منطقِ لایه ۰ — در orchestrator پیاده می‌شود، نه در LiteLLM)
LiteLLM فقط دو **گروه** را سرو می‌کند؛ *انتخابِ* گروه کارِ caller است:

| شرط | گروه | مثال |
|---|---|---|
| یک قدمِ میانیِ غلط، جوابِ نهایی را خراب می‌کند (multi-step, verifiable) | `heavy-reasoning` | طراحی، اثبات، سنتزِ چندمنبعی |
| lookup / rewrite / extraction / حجیم / ارزان | `fast` | خلاصه، format، دسته‌بندی |
| (بعداً) offline / محرمانه / رایگان | `local-fast` | معلق تا مشخصاتِ Hetzner |

هر گروه fallbackِ cross-provider دارد (Anthropic ↔ OpenAI/Gemini) → اگر یک provider بیفتد، سیستم نمی‌ایستد.

---

## ضمانت‌های governance (baked-in) و کلیدِ تنظیمشان
- **Cost cap (سقفِ سخت):** `litellm_settings.max_budget: 80` + `budget_duration: "30d"` (USD). تنها یک عدد را عوض کن.
- **Fail-closed:** `fail_closed_budget_enforcement: true` (نشد spend را verify کند → 503) و `allow_requests_on_db_unavailable: false` (DB افتاد → reject). enforcement مقدم بر availability.
- **Kill-switch:** `make kill` (= `docker compose down`) → گیت‌وی می‌رود، هر call پایین‌دستی fail-closed می‌شود. (فلگِ `SYSTEM_ENABLED` وقتی معنا پیدا می‌کند که Layer آرکستریتور بالای این بنشیند.)
- **Audit — دو جریان:**
  1. **Postgres spend logs** (`LiteLLM_SpendLogs`): هر request با model/tokens/cost/timestamp، ماندگار و query-پذیر — auditِ اصلی. گزارش: `make spend` یا `/global/spend/report`.
  2. **json logs** (`json_logs: true` + docker `json-file` با rotation): جریانِ زنده‌ی append-only. `make logs`.
- **Privacy پیش‌فرض:** بدنه‌ی prompt/response ذخیره **نمی‌شود** (`store_prompts_in_spend_logs: false`, `turn_off_message_logging: true`) — فقط metadata+cost. اگر capture کامل خواستی، این دو را flip کن (trade-off صریح).
- **رازها:** فقط `.env` (git-ignored)؛ credentialها با `LITELLM_SALT_KEY` رمز می‌شوند. گیت‌وی روی `127.0.0.1` bind است — بیرون نده مگر با reverse-proxy + TLS.
- **enforcementِ محکم‌تر (توصیه):** علاوه بر سقفِ global، یک **virtual key** با `max_budget` خودش برای app بساز (`/key/generate`) تا مصرفِ اپ از master جدا و سقف‌دار شود.

---

## امنیت (مهم)
- image روی `v1.85.0-stable` **pin** است — هرگز `latest`.
- **incidentِ مارس ۲۰۲۶** روی LiteLLM `1.82.7/1.82.8` (رفع در `1.83.0`) — از این نسخه‌ها پرهیز. `[تثبیت‌شده]`
- قبل از هر bump: signature را با `cosign` verify کن و advisoryها را در `github.com/BerriAI/litellm/releases` چک کن (دستور در بالای `docker-compose.yml`).

---

## قدمِ بعدی (یک آجر)
افزودنِ **tierِ مدلِ local (Layer 1 light)** با Ollama — قفلِ فعلی: مشخصاتِ Hetzner.
- **بدونِ GPU:** Phi-4-mini (3.8B, ctx 128K) یا Qwen3-4B، quantization پیش‌فرض Q4، سرویسِ `ollama` در compose + بخشِ `local-fast` در config uncomment.
- **با GPU:** مدلِ بزرگ‌تر ممکن می‌شود.

## بدهیِ باز / verify (اخلاقِ معرفتیِ پروژه)
- id دقیقِ مدل‌ها در `litellm_config.yaml` placeholder است — با کنسولِ providerها تأیید کن.
- کلیدهای budget را مقابلِ داکِ نسخه‌ی pin‌شده verify کن (schema جابه‌جا می‌شود).
- این build را در DecisionLog/Ledgerِ خودت ثبت کن؛ وقتی track «vault» را زدیم، همین پوشه اولین ورودیِ vault می‌شود (منبعِ حقیقتِ واحد).
