---
tags: [security, checklist, G-01]
created: 2026-07-03
closes: G-01 (بخش عملیاتی — rotation فقط از دست اپراتور برمی‌آید)
---

# چک‌لیست چرخاندن کلیدها (G-01)

> **⛔ superseded (2026-07-03):** نسخه canonical و کامل‌تر → [[ROTATION_CHECKLIST]] در ریشه vault (Phase 0). این نوت فقط برای تاریخچه نگه داشته شده. توجه: برخلاف «تصمیم اپراتور» ثبت‌شده در پایین، در Phase 0 همه فایل‌های secret (از جمله `_code`) با تأیید اپراتور به `secrets-export/` منتقل شدند.

## وضعیت راستی‌آزمایی‌شده (2026-07-03)

- ✅ هیچ secret ای در **git tracking یا تاریخچه** نیست (AI-sume تنها ریپوست، بدون remote، بدون commit حاوی secret).
- ✅ gitignore ها کامل شدند: ریشهٔ `ai-farm` (umbrella جدید)، `langar-pro` (جدید)، AI-sume و fusion-mvp (از قبل خوب بودند).
- ⚠️ ریسک واقعی **سطح دیسک** است: فایل‌های زیر مقدار واقعی دارند و در هر کپی/بکاپ نشت می‌کنند.

## فایل‌های حاوی secret واقعی (جابجا نشده‌اند — تصمیم اپراتور)

| فایل | کلیدها |
|---|---|
| `_code/ai-farm/AI-sume/langar/.env` | BOT_TOKEN، OWNER_ID |
| `_code/ai-farm/AI-sume/langar-pro/.env` | POSTGRES_PASSWORD، DATABASE_URL (پسورد داخلش)، REDIS_URL، OPENAI_KEY، BRAVE_API_KEY |
| `_code/ai-farm/fusion-mvp/.env` | ANTHROPIC_API_KEY |
| `_code/ai-farm/fusion-mvp/logs/igk_state/.kernel_key` | کلید کرنل igk |
| `_code/ai-farm/AI-sume/langar/langar.db` | دادهٔ واقعی حافظه (شخصی) |

## اقدامات تو (به ترتیب، ~۱۵ دقیقه)

- [ ] **BOT_TOKEN**: BotFather → `/revoke` → توکن جدید → آپدیت `.env`
- [ ] **ANTHROPIC_API_KEY**: console.anthropic.com → API Keys → کلید قبلی را Disable، جدید بساز
- [ ] **OPENAI_KEY**: platform.openai.com → API Keys → revoke + جدید
- [ ] **BRAVE_API_KEY**: پنل Brave Search API → regenerate
- [ ] **POSTGRES_PASSWORD + DATABASE_URL**: پسورد جدید بگذار (استقرار نشده، فقط `.env` را عوض کن)
- [ ] **.kernel_key**: بعد از استقرار واقعی igk دوباره generate می‌شود؛ فعلاً فقط مطمئن شو کپی نشده
- [ ] **`_meta/pre-reorg-backup-2026-07-03.zip` را حذف یا به دیسک آفلاین ببر** — همهٔ secrets داخلش کپی شده‌اند ⚠️
- [ ] بعد از rotation: `gitleaks detect` روی `_code` اجرا کن (معیار MVP: صفر یافته)

## قانون از این به بعد (P3-همسو)

مقدار کلید فقط در `.env` (خارج از git) — هرگز در کد، سند، chat export، یا zip بکاپ. کلید age/kernel روی دستگاه agentic نماند (P10) — مقصد: password manager یا دیسک آفلاین.
