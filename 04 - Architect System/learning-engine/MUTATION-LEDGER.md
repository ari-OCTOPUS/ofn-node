---
type: log
status: active
tags: [learning-engine, mutation, append-only]
created: 2026-07-06
updated: 2026-07-06
---

> [!warning] ledger عملیاتی جهش‌ها = ردیف‌های `learning-loop·auto` در `_memory/EXPERIENCE-LEDGER.md` (طبق پرامپت تسک). این فایل فقط ایندکس محلی اختیاری است.

# MUTATION-LEDGER — جهش‌نامه Engine (append-only)

> هر جهش یک ردیف؛ هرگز ویرایش/حذف ردیف قدیمی. `kind`: mutate | revert | noop-honest | propose.

| تاریخ | نسخه پرامپت | kind | ردیف تجربه مبنا | فرضیه/تغییر | نتیجه |
|---|---|---|---|---|---|
| 2026-07-06 | v1 | bootstrap | verdict آری «تغییر بخش مجاز خودش براساس تجربه، هر بار اپ روشن می‌شود» | ساخت هسته: ENGINE-PROMPT v1 + حلقه ساعتی `learning-engine-loop` + مرز جهش whitelist §۰.۳ | فعال — اولین اجرای واقعی ~دقیقه ۳۵ ساعت بعد |
| 2026-07-06 | v1→v2 | mutate | EXPERIENCE-LEDGER ردیف مربوط به این تکمیل (شمار کل=47) + header PROMPT-v2 | تکمیلِ جهشِ نیمه‌کارهٔ اجرای قبل: `ledger_cursor` از رشتهٔ تاریخی به عددِ صحیح تغییر کرد (باگ: ردیف‌های «امروز» هرگز > cursorِ «امروز» نمی‌شدند) — این بار هم فایلِ v2 هم `update_scheduled_task` هم STATE واقعاً اعمال شدند | فعال — prompt_version=v2، ledger_cursor=47، mutation_count=1؛ سقفِ امروز پر شد |
| 2026-07-06 | — | propose | verdict آری «طراحی سیستم» | سیستمِ GOVERNOR+MUSE: ۱۵ سندِ propose + ۶ اسکریپت ([[GOVERNOR-MUSE-SYSTEM-INDEX]]) | آماده — اجرا سمتِ مالک به ترتیبِ BUILD-06 |
| 2026-07-06 | — | fix | بازنگری با اجرای واقعیِ کد | ۸ باگ رفع شد (budget race/fail-open، governor silent-failure ۲ لایه، guard portable، backup flag، R1) — تست‌شده | [[2026-07-06 REVIEW-FIXES-changelog]] |
| 2026-07-06 | — | apply | verdict آری «اعمال کن» | رفعِ دریفت‌های ژنوم D1 (contract mode→propose-only+target) · D2 (STATE gate→LIFTED) · D3 (ENGINE-PROMPT precedence/تک‌whitelist) | اعمال‌شد — برگشت‌پذیر (git/backup) |
