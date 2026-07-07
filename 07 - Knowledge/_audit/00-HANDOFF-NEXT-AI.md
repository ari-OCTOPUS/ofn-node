---
title: HANDOFF — برای AI بعدی، اول این را بخوان
created: 2026-07-05
session: ممیزی ۷فازی + Dedup dry-run روی 07 - Knowledge (Cowork)
status: ممیزی کامل ✅ · Dedup فاز A کامل، فاز B اجرا نشد (اقدامی لازم نبود)
---

# 🤝 HANDOFF — نقطه‌ی شروع AI بعدی

## تو کجای کاری
در ۲۰۲۶-۰۷-۰۵ یک ممیزی کامل read-only روی `07 - Knowledge` انجام شد (طبق پرامپت فایل `MASTER-Second-Brain-Cowork-Handoff.md` کاربر). **هیچ فایلی از vault تغییر نکرد یا حذف نشد** — تنها خروجی، ۹ فایل همین پوشه‌ی `_audit/` است.

## ترتیب خواندن
1. **همین فایل** — وضعیت و قواعد.
2. `MASTER_REPORT.md` — نتیجه‌ی کل ممیزی + ۱۰ اقدام ROI + ۳ سؤال از کاربر.
3. `DEDUP_PLAN.md` — نتیجه: صفر تکراری byte-for-byte؛ فقط تصمیم‌های انسانی باز.
4. بقیه بر حسب نیاز: `INVENTORY` (۱۱۰ فایل) · `FOLDER_MAP` · `CONTENT_DIGEST` · `KNOWLEDGE_MAP` · `HYGIENE_REPORT` · `OPEN_LOOPS`.

## ۵ واقعیت کلیدی که نباید دوباره کشف کنی
1. **زنجیره‌ی تحقیق P0–P7 کامل است (۸/۸ + P2b + X1)** — ولی `MAP.md`، `Projects.md` و `Roadmap.md` هنوز آن را ناقص نشان می‌دهند (stale). به نقشه‌ها اعتماد نکن؛ به nodes اعتماد کن.
2. **توکن Silabi در کد سالم است** (`TELEGRAM_TOKEN` از env، خط ۶۶). آیتم TODO.md قدیمی است؛ فقط revoke توکن قدیمی نزد owner مانده.
3. **`Marathon/امواج مغزی/` = ~۶۰MB داده‌ی ژنتیکی (PII).** هرگز نخوان، پارس نکن، جابه‌جا نکن مگر با دستور صریح کاربر. `Marathon/تمرینات ورزشب/دیتا.txt` هم مشتق DNA است.
4. **دو رژیم لینک:** لایه‌ی بالا wikilink دارد؛ کل `فیوژن هیپنوتیزم` (۵۲ فایل) ارجاع مسیری backtick — «یتیم» بودنشان در گراف Obsidian ظاهری است.
5. **نام پوشه‌ی اصلی دو فاصله دارد:** `هیپنوتیزم␣␣و خودآگاهی`. هر مسیر دستی بدون این نکته می‌شکند.

## قواعد لازم‌الاجرا (از خود vault)
- **O-04:** داده‌ی شخصی/سلامت فقط-لپ‌تاپ؛ وارد هیچ سرویس ابری نشود.
- **_TagSpec:** تگ معرفتی 【E】established / 【S】speculative / 【P】fiction-canon — fiction هرگز evidence نیست (X1 مرز را تعریف کرده).
- **Read-only پیش‌فرض:** هر تغییر مخرب فقط با تأیید صریح کاربر (`APPROVED: اجرا کن`).

## کارهای باز به‌ترتیب اولویت (جزئیات در OPEN_LOOPS.md)
1. 🔴 خروج داده‌ی ژنتیکی از vault → cold storage (منتظر تصمیم کاربر درباره‌ی مقصد).
2. 🟠 revoke توکن قدیمی BotFather (owner-only).
3. 🟡 sync سه سند stale (MAP/Projects/Roadmap) — تغییر کوچک، ولی نیازمند اجازه‌ی write.
4. 🟡 fix لینک `[[ROTATION_CHECKLIST]]` در PROJECT.md.
5. تصمیم‌های باز کاربر: canonical نقشه‌ی قلب (۴ نسخه)، سرنوشت ۴ placeholder، برچسب snapshot روی PROJECT_EXPORT_COMPLETE.
6. **فاز عمل شروع نشده:** صفر لاگ تمرین، صفر داده‌ی HRV — تئوری اشباع است؛ منطقی‌ترین قدم بعدی پروژه اجراست، نه تحقیق بیشتر.

## محدوده‌ی این ممیزی
فقط `07 - Knowledge`. ریشه‌ی `backup` (CLAUDE.md، .agentignore، secrets-export، شاخه‌های 00–10، _Duplicates، _memory) **دیده نشد**. اگر کاربر دسترسی ریشه داد: اول CLAUDE.md و .agentignore را بخوان، بعد ممیزی را به کل vault گسترش بده و خروجی‌ها را در `_memory/audit/` بگذار (محل استاندارد طبق فایل Master کاربر).
