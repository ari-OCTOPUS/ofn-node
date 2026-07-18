# ⚠️ DEPRECATED — این دایرکتوری deploy نشده است

> Verdict 2026-07-18 integration-debug

## وضعیت

`survival-gateway/` یک **proxy LiteLLM برای deployment سرور** است (Layer 0 gateway).
`docker-compose.yml` و `litellm_config.yaml` موجود است با مدل‌های GLM، DeepSeek، Fugu
و سقفِ $80/30d. ولی **هرگز deploy نشده و در runtime محلی فعال نیست**.

## معنای این برای توسعه‌دهنده

- کلیدهای API در `survival-gateway/.env` هستند ولی **تنها برای reference** — organism از
  فایلِ کانونی `.env` در ریشه می‌خواند، نه از اینجا.
- هیچ کدِ `_ops/` به port 4000 یا survival-gateway اشاره نمی‌کند.
- تغییر در این دایرکتوری **تأثیری در ارگانیسم زنده ندارد**.

## Canonical جایگزین

- LLM keys: `F:\backup\.env` (canonical، gitignored)
- LLM routing: `_ops/cortex/model_router.py`
- Budget: `_ops/budget/budgets.yaml`

## اگر خواستی deploy کنی

این یک پروژه‌ی آینده‌است (deployment سرور ابری). فعلاً organism محلی LLM را مستقیم
از model_router می‌خواند. survival-gateway فقط وقتی لازم می‌شود که:
1. چند client بخواهند از یک proxy مشترک استفاده کنند.
2. rate-limiting و metering مرکزی لازم شود.

مرجعِ معماری: `ARCHITECTURE-SOT.md` در ریشه.
