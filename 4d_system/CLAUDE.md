# CLAUDE.md — NBB-CP / Second Brain Super-Governor · Project Governance

این فایلِ کوتاهِ حاکمیتی است که هر session خودکار می‌خواند. جزئیاتِ کامل در
`docs/` است؛ این‌جا فقط قواعدِ غیرقابل‌مذاکره + سندهای کانونی.

## اسناد کانونی (منبعِ حقیقت)
- `docs/CODING_AGENT_PROMPT.md` — پرامپتِ مهندسیِ اصلی: mission، invariants (INV-1..12)، architecture contract، ۸ فاز و gateها، per-phase report template.
- `docs/SPEC_v0.2.md` — مشخصاتِ NBB Control Plane.
- `docs/SKELETON_HARDENING.md` — تاریخچه‌ی سخت‌سازی + کارهای deferred.
- `docs/SECOND-BRAIN-SUPERGOVERNOR-v0.2.md` — معماریِ لایه‌ی بالاتر (۸ مغز روی Obsidian Vault؛ NBB = کامپوننتِ B6). **SPEC است، هنوز ساخته نشده.**
- `docs/SELF_IMPROVEMENT_DOCTRINE.md` — قانونِ کاملِ IMPROVE-DON'T-REWRITE.

---

## STRICT SAFETY RULES (سیستمِ فعلی حذف/تخریب نمی‌شود)

1. **Invariants مقدس‌اند (INV-11).** هیچ invariant حذف/renumber/تضعیف نمی‌شود؛ فقط با اجازه‌ی مالک می‌توان INV-13+ افزود. اگر یک الزامِ فاز با invariant تضاد داشت، invariant برنده است و تو **می‌ایستی و گزارش می‌دهی**.
2. **kern/ خالصِ stdlib می‌ماند** (`tests/test_import_lint.py` اثبات است). جهتِ وابستگی: `kernel ← adapters ← app ← api/ui` — هرگز برعکس. LangGraph فقط داخلِ `adapters/llm/`.
3. **یک choke-point.** همه‌ی effectها از `ControlPlaneService.execute` عبور می‌کنند (INV-4). مسیرِ اجرای دوم = defect.
4. **Fail closed.** حالتِ ناشناخته → shadow/deny + ثبتِ INCIDENT + توقف. Cassette miss = error، نه mock fallback.
5. **پول = integer cents سرتا‌سر.** float نزدیکِ ledger = defect. cap فقط در `NBB_GLOBAL_CAP_CENTS`.
6. **رازها هرگز وارد repo/ledger/cassette نمی‌شوند** (scrub؛ الگوی `sk-` در commit ممنوع).
7. **اگر تصمیمی از spec + invariants استخراج نمی‌شود، بایست و از انسان بپرس.** حدس‌زدن روی «قانون» = INV-12.
8. **suite همیشه سبز.** رفتار جدید با تستش در همان commit؛ باگ ⇒ اول regression test. بین فازها refactor نکن.

---

## IMPROVE, DON'T REWRITE (نسلِ بعدی فقط بهبود می‌دهد)

> نسخه‌ی کامل: `docs/SELF_IMPROVEMENT_DOCTRINE.md`

هر agent بعدی فقط سیستم قبلی را **بهبود** می‌دهد، **بازنویسی نمی‌کند**.
`Improve, don't rewrite. Extend, don't replace. Inherit, don't reset.`

- قابلیت جدید **کنارِ** قابلیت قبلی اضافه شود، نه جایگزینش.
- نسخه‌ی قبلی همیشه حفظ شود (versioning)؛ حذف ممنوع مگر با اجازه‌ی صریح.
- interface و رفتارِ بیرونیِ موجود تغییر نکند.
- **هر تغییرِ بزرگ‌تر از ~۳۰٪ یک ماژول، یا هر تغییرِ interface، یا حذفِ نسخه‌ی قدیمی = "rewrite" → اول بپرس.**
- قبل از هر بهبود این چهار را نشان بده: **Current / Delta / Preserved / Rollback**.
- اگر تغییر شبیه بازنویسی شد، آن را به چند بهبودِ کوچکِ امن بشکن و اجازه بگیر.

**قانون طلایی:** نسلِ بعدی باید **فرزندِ** سیستمِ فعلی باشد، نه غریبه‌ای که جایگزینش می‌شود. تکامل بله؛ انقلاب/بازنویسی نه — مگر با اجازه‌ی صریحِ مالک.
