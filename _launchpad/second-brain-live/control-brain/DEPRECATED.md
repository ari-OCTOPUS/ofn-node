# ⚠️ DEPRECATED — second-brain-live/control-brain مرده است

> Verdict 2026-07-18 integration-debug

## وضعیت

این دایرکتوری باقی‌مانده‌ی مفهومِ قدیمیِ "second brain" است. فایل‌های README،
batch، و skeleton پایتون دارد ولی **هیچ کدِ زنده‌ای در runtime فعال نیست**.

## معنای این برای توسعه‌دهنده

- تغییر در این دایرکتوری **تأثیری در ارگانیسم زنده ندارد**.
- `ANTHROPIC_BASE_URL` در `.env` این دایرکتوری به DeepSeek proxy شده — گمراه‌کننده است.
- `TELEGRAM_TOKEN` در `.env` این دایرکتوری همان bot ID `8187434784` است که با
  Octopus Unified (#1) تداخل دارد → خطرِ 409 اگه لانچ شود.
- سه باتِ تعریف‌شده این‌جا (Painting، Accounting، Control Brain) همگی DORMANT هستند.

## Canonical جایگزین

- مغز: `_ops/cortex/cortex.py`
- تلگرام: `_ops/budget/approval_channel.py` و `_ops/telegram_center/center.py`
- LLM: `_ops/cortex/model_router.py`
- کلیدها: `F:\backup\.env`

## توصیه

این دایرکتوری به‌عنوان **آرشیو** نگه‌داری شود. حذف نشود (شاید reference باشد).
هرگونه revival نیاز به تصمیمِ owner دارد. مرجع: `ARCHITECTURE-SOT.md`.
