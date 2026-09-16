---
type: registry
project: "[[Accounting/PROJECT]]"
status: active
layer: truth-layer
tags: [accounting, module-registry, canonical]
created: 2026-07-13
updated: 2026-07-13
---

# 03 · Module Registry — مالکیت canonical

> یک canonical به‌ازای هر مسئولیت. اگر جایی نسخهٔ دومی از این‌ها دیدی، آن نسخه stale است.

## ماژول‌های کد

| ماژول | مسیر canonical | مالکِ مسئولیت | زبان/وابستگی | وضعیت |
|---|---|---|---|---|
| ANZ Importer | `importer/anz-import.js` | ingestion بانک → draft ledger (dedup, GST, دسته‌بندی, پرچم, reconcile) | Node.js (بدون شبکه) | ✅ tested ۱۳/۱۳ |
| Importer config | `importer/config.js` | قواعد قابل‌ویرایش: حساب‌های بیزنس، associates، نگاشت vendor، آستانه‌ها | Node.js | active |
| Telegram Bot | `app/bot.js` | ورودِ داده + صف verdict | node-telegram-bot-api | نیازمند `TELEGRAM_BOT_TOKEN` (env، خارج از repo) |
| DB layer | `app/database.js` | schema + ذخیره (bank_import, business_transactions) | better-sqlite3 | active |
| Personal dashboard | `app/personal-dashboard.js` | نمای مالی شخصی | express + chart.js | active |
| Business dashboard | `app/business-dashboard.js` | نمای ATO/compliance | express + chart.js | active |

## قراردادها و state (ماشین‌خوان)

| فایل | مسئولیت |
|---|---|
| `MANIFEST.yaml` | قرارداد اتصال به مغز مرکزی (blackbox_potential, control_surface, kill_switches) |
| `contracts/adapter.yaml` | رابط read-only (status/report/compliance_scan/audit) + hard_gated_actions |
| `PROJECT.md#Active-Context` | live status (منبع حقیقت وضعیت) |
| `DecisionLog.md` | تصمیم‌ها | `OpenQuestions.md` | سؤالات باز | `VERDICT_QUEUE.md` | صف تأیید |

## داده (canonical)

| مجموعه | مسیر | نکته |
|---|---|---|
| بانک ANZ (statements + ledger + reconcile) | `finance/` | FinOS drop-in، event-sourced |
| شیت‌های خام خانواده | `data/حساب کتاب/*.xlsx` | PII |
| پرامپت‌های مالیاتی (۱۳) | `finance/TaxPrompts/` | SOPها |
| ledger واگرا | `finance/_RECONCILE-ledger-variants/` | ⚠️ منتظر verdict |

## قاعده‌ها
- **افزودن ماژول جدید** → اول این رجیستری را آپدیت کن، بعد کد.
- **نوت‌بوک/آزمایش** هرگز منبع حقیقت نیست (این پروژه اصلاً notebook ندارد).
- بارگذاری state طبق MANIFEST: `PROJECT.md → INDEX.md → docs/Ecosystem-Rollout-Plan.md`.
