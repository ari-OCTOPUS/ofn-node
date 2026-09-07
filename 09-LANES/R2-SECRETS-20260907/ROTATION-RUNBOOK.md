# ROTATION-RUNBOOK — کارت R2/R3 (مالک: فقط تو می‌توانی این‌ها را بزنی)

لِین `R2-SECRETS-20260907` · 2026-09-07 · GO مالک («ALL»)
قاعده: **نام کلیدها فقط؛ هیچ مقداری در هیچ‌جا نوشته نشده و نمی‌شود.**

## آنچه من همین حالا انجام دادم (انجام‌شده، با رسید)

1. **ممیزی**: تمام فایل‌های secret در درخت **untracked و gitignored** هستند — نشت به ایندکس/تاریخچهٔ فعلی گیت صفر (تنها نگرانی تاریخچه: اسنپ‌شات‌های `.mimosa` = کارت R5، جدا).
2. **انتقال ۱۰ کپی بدون-مصرف** به `C:/Users/Armin/.octopus-secrets-archive/` (بیرون از repo و مسیرهای robocopy/mirror؛ proفایل کاربر = ACL تک‌کاربره):
   - `.env.bak-20260810` (دوبل plaintext کلیدهای زنده)
   - `4× _ops/OCTOPUS.env.bak-*` (متریال کلید قدیمی)
   - `_ops/secrets/ziman-maliheh/` ×۳: **bank + TFN + کدهای بازیابی 2FA شاپیفای** (حساس‌ترین دادهٔ کل vault)
   - `2× google-ga4/oauth-client.json.bak-*`
   در محل‌های قبلی README اشاره‌گر گذاشتم؛ فایل‌های زنده (`.env`، `_ops/OCTOPUS.env`، `_ops/secrets/*.env`، `token.json`، `oauth-client.json`) **دست‌نخورده‌اند** و سرویس‌ها بی‌وقفه ادامه دارند.
3. `witness/witness.key` **منتقل نشد** — مصرف‌کنندهٔ زنده دارد (`witness/witness_verify.py`)؛ مهاجرتش به‌روزرسانی کد می‌خواهد، در کارت پایین.

## چک‌لیست چرخش — به‌ترتیب (هر بند بعد از چرخش، کپی آرشیوی مربوطش قابل حذف است)

| # | کلید/فایل | کجا | اقدام تو | بعدش |
|---|---|---|---|---|
| ۱ | `GITHUB_TOKEN_OPI` (github_pat_…) | `.env` ریشه | GitHub → Settings → Developer settings → Fine-grained tokens → **Revoke** قدیمی + ساخت جدید → مقدار جدید در `.env` | هیچ یادداشت ابطالی وجود نداشت؛ `GITHUB_TOKEN_PC` قبلاً DEAD-401 علامت خورده |
| ۲ | توکن تلگرامِ تاریخismatch ۰۷-۱۰ | ثبت‌شده در `AGENT_QUESTIONS.md` 2026-07-10 (redacted) | اگر هنوز همان Bot token است: BotFather → `/revoke` → جدید → هر سه `*_BOT_TOKEN` در `.env` به‌روز | تأیید کتبی چرخش در همان نوت (توصیهٔ «اکید» آن روز هنوز بی‌پاسخ است) |
| ۳ | `TELEGRAM_BOT_TOKEN` + `TG_ZIMAN_STUDIO_BOT_TOKEN` + `TG_CENTER_BOT_TOKEN` | `.env` | BotFather revoke/جدید per bot (فقط اگر فکر می‌کنی لو رفته؛ فعلاً کار می‌کنند) | — |
| ۴ | `GMAIL_APP_PASSWORD` | `.env` | Google Account → Security → App passwords → حذف + جدید | — |
| ۵ | `OCTOPUS_CB_SECRET` | `.env` | بازتولید در سرویس مبدأ (کلید ضعیف‌نما بود) | — |
| ۶ | `POCKETSMITH_API_KEY` · `FUGU_API_KEY`/`SAKANA_API_KEY` · `ZAI_API_KEY`/`GLM_API_KEY` · `DEEPSEEK_API_KEY` · `OPENAI_API_KEY` · `ANTHROPIC_API_KEY` | `.env` | چرخش از کنسول هر پرووایدر (اولویت: هرکدام در `.mimosa` اسنپ‌شات ۰۸-۲۰ هم هست) | — |
| ۷ | کدهای بازیابی 2FA شاپیفای | آرشیو امن (منتقل‌شده) | Shopify → دو-step → بازتولید کدهای جدید → نسخهٔ جدید را فقط در password keeper نگه دار | کد قدیمی در آرشیو را نابود کن |
| ۸ | `.mimosa` در تاریخچهٔ گیت (R5) | `.git/hook-state/*` | تصمیم: پذیرش ریسک **یا** بازنویسی تاریخچه (filter-repo) — کارت باز | — |
| ۹ | `witness.key` + شاید کلید W-2 | `witness/` | اگر مهاجرت می‌خواهی: هم‌زمان مسیر در `witness_verify.py` عوض شود | — |
| ۱۰ | `4d_system/.env` و `_build/lead-naghshi-portable/.env` | درخت‌های جدا/مرده | چرخش یا حذف امن آن درخت‌ها (خارج از این lane) | — |

## وضعیت امنیتی پس از این لِین

کپی‌های plaintext داخل repo: از **~۱۷ فایل فعال/تاریخی به ۷ فایل زندهٔ لازم** (`.env`، `OCTOPUS.env`، `brain/deepseek/sakana env`ها، `token.json`، `oauth-client.json`، `witness.key`) کاهش یافت؛ بقیه در آرشیو تک‌کاربرهٔ بیرون-repo، با pointer در محل. صفر قطعی سرویس (هیچ فایل مصرف‌شده‌ای جابه‌جا نشد).
