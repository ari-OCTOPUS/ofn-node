---
type: reference
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, marketing, tooling]
created: 2026-08-03
updated: 2026-08-03
---

# PROVENANCE — growth_arch

## کد از کجا آمد

- **منبع:** کیتِ خارجی که مالک تحویل داد (zip ِ روی دسکتاپ)، زیرپوشهٔ `growth-archaeologist`.
- کیت شاملِ یک زیرپوشهٔ دوم به نامِ `fugu-api-brain` هم بود — آن **آورده نشد**؛ حکمِ ارزیابی رویش REJECT بود.
- از خودِ `growth-archaeologist` فقط `src/`، `test/`، `contracts/`، `fixtures/` و `package.json` آورده شد. پوشهٔ `output/` ِ مبدأ آرتیفکتِ یک اجرای نمونه بود و آورده **نشد**؛ حالا `output/` هنگام اجرا ساخته می‌شود و در `.gitignore` ِ محلی نادیده گرفته شده.

## راستی‌آزمایی

- **۲۰۲۶-۰۸-۰۳** — در محلِ مبدأ: ۷/۷ تست سبز.
- **۲۰۲۶-۰۸-۰۳** — دوباره در همین محلِ جدید (`03 - Projects/اونلی فنز/growth_arch/`) با Node ‏v24.8.0:
  - `node --test test/*.test.js` ← ‏۷ pass / ۰ fail، exit=0.
  - `node src/cli.js analyze --input fixtures/sample_entities.json --out output` ← `ok: true`، exit=0؛ هر هشت فایلِ خروجی ساخته شد و JSONهایشان parse شدند.
  - **هیچ تغییری در کد لازم نبود** — مسیرهای نسبی همه درون-پوشه‌ای‌اند و با جابه‌جایی نشکستند.

## بازرسیِ ایمنی (۲۰۲۶-۰۸-۰۳)

- importهای واقعی فقط: `node:fs/promises`، `node:path`، `node:crypto` (و `node:test` / `node:assert/strict` در تست‌ها).
- صفر موردِ `fetch(`، `child_process`، `exec`/`spawn`، `eval`، `XMLHttpRequest`، `WebSocket`، `axios`؛ صفر توکن/کلید.
- تنها URLهای موجود: شناسه‌های JSON Schema (`json-schema.org`، `example.local`) و URLهای جای‌نگهدارِ `example.com` داخلِ fixture — داده‌اند، نه فراخوانی.
- صفر dependency ِ بیرونی؛ `npm install` لازم نیست و زده نشد.

## لینک‌ها

- ارزیابی: [[03 - Projects/اونلی فنز/02 - Research/FUGU-BRAIN-KIT-EVAL-2026-08-03]]
- راهنمای استفاده: [[03 - Projects/اونلی فنز/growth_arch/README.fa]]
