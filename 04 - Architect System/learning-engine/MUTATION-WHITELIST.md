---
type: reference
status: active
tags: [learning-engine, mutation, whitelist, governance]
created: 2026-07-06
updated: 2026-07-06
---

# MUTATION-WHITELIST — «بخشی از خودش که مجاز است تغییر دهد»

> verdict آری 2026-07-06: «وقتی اپ روشن می‌شود شروع کند به تغییر بخشی از خودش که مجاز است، بر اساس تجربه‌اش.»
> تغییر این فایل = فقط verdict مالک. حلقه هرگز whitelist خودش را جهش نمی‌دهد (ضد evaluator-tampering — DEEP-GAP شکاف ۸).

## ✅ سطح مجاز جهش (bounded-auto)

1. **پرامپت خودِ حلقه** — فقط به‌صورت نسخه‌دار: `prompts/PROMPT-vN.md` (نسخه قبلی هرگز حذف نمی‌شود = rollback بدون git) + آپدیت پرامپت تسک `learning-engine-loop`.
2. `LEARNING-STATE.json` — state خودش.
3. خروجی‌های derived خودش: دیجست در `00 - Inbox/scout-digests/` و پیشنهاد در `00 - Inbox/build-proposals/`.
4. سطر خودش در `_memory/HEARTBEAT.md` + append در `_memory/EXPERIENCE-LEDGER.md`.

## ⛔ خارج از سطح (همیشه)

این فایل (whitelist) · RATIFIED-TASKS (متن پایه/anchor) · قانون اساسی/charter/Property Schema · هر نوت canonical · تسک‌های دیگر · `_code` · secret/پول/پیام خارجی/git · **هیچ call خارجی (Fugu/partner) در این حلقه** — حلقه فقط با Claude داخلی کار می‌کند.

## سقف‌ها و گاردها

- حداکثر **۱ جهش در روز**؛ هر جهش کوچک و تک‌موضوعی.
- هر جهش باید به یک ردیف مشخص ledger ارجاع دهد (evidence-based؛ بدون شاهد = جهش ممنوع).
- دو اجرای خطادار پشت‌سرهم → rollback خودکار به PROMPT-v1 (متن anchor در RATIFIED-TASKS).
- فایل `STOP` در ریشه vault = halt فوری (kill-switch).
- جهشی که whitelist یا گاردها را لمس کند = نقض contract → ثبت regress + halt.
