---
type: system-note
system: ofn-node
created: 2026-08-15
status: partial — اتصال از سمت ارشد مستند است؛ وضعیت خودِ برد unverified (دسترسی زنده نداریم)
sources:
  - "00 - Inbox/2026-08-13 MEGAPROMPT — اتصال ارشد↔برد (Octopus Bridge، رصد-اول)"
  - "git log: 3640eac، fc735f9، 9b6ed0c"
  - "octopus-bridge/octopus_bridge/ (بستهٔ کد)"
---

# OFN-NODE — نود میدانی اورنج‌پای (برد/زیردست)

## دو ماشین (طبق مگاپرامپت 2026-08-13)

| | ارشد (Windows) | برد/زیردست |
|---|---|---|
| ماشین | `F:\backup` | Orange Pi + DietPi |
| نقش | ارگانیسم اصلی، رصد-اول | اجرای میدانی، فرمان‌گیر gated |

## وضعیت اتصال (شواهد git + مگاپرامپت)

- مگاپرامپت 2026-08-13: اتصال «از قبل ~۸۰٪ ساخته» توسط ایجنت موازی، «امن، gated-خاموش، propose-only»
- کامیت `3640eac` — feat(board-cp): **observation live, command plane gated-off**
- کامیت `fc735f9` — fix(board-cp): stop redirect-following in legs reader — **G1 SSRF hardening**
- کامیت `9b6ed0c` — docs: سیزن desktop-lab D1–D8 بدون PASS رسمی
- بستهٔ کد سمت ارشد: `octopus-bridge/octopus_bridge/`

## ادعاهای مگاپرامتِ مالک (2026-08-15) — وضعیت راستی‌آزمایی

| ادعا | وضعیت |
|------|-------|
| پورت‌های 8791–8794 روی نود | **unverified** — از دسکتاپ گوش نمی‌دهند ([[../01-TRUTH/SERVICE-STATUS.md|SERVICE-STATUS]])؛ دسترسی به برد نداریم |
| ۱۲۲۹ تست OFN (`~/ofn`) | **unverified** — `ls ~/ofn` و pytest روی برد اجرا نشد |
| CHECKPOINT.md / CLAUDE.md / DECISIONS.md میدانی | **در Vault ارشد وجود ندارند** — CHECKPOINT.md هیچ‌جا نیست؛ اگر روی برداند، نسخه‌ای این‌جا نبوده → `verified_at: null` |
| ساب‌دامنه‌ها | **unverified** — curl بیرونی اجرا نشد (قاعدهٔ ۶-۷: خروجی ممنوع) |

## گیت‌های بستهٔ نامبرده (secret_rotation · partner_precondition · miner_isolation)

جستجوی نام‌这三个 در تمام md های Vault → **صفر نتیجه**. مفاهیم مرتبط موجود: D-27 («چرخش کلیدها الزامی») و بلوکرهای README («rotation کلیدها» برای Lead، «seed rotation» برای Mining).
→ [[../03-GATES/GATES.md|GATES]] با برچسب `unverified` (منبع احتمالی: CHECKPOINT میدانیِ غایب).
