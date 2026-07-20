# ✅ Project-F VERDICT_QUEUE

> Content-free. Do not add identity/platform/media details here.
> ⚖️ **2026-07-20 (DL-2026-07-20-DECISION-SOT):** این جدول فقط «سینی رأی» است، نه مجوز. هر وضعیت اینجا تا ثبت در [[DecisionLog]] غیرالزام‌آور است؛ در تعارض، محافظه‌کارترین (OPEN) برنده است.

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| PF-V1 | GATE 0 حل شده؟ | yes/no | **open** — «temporary-A» (07-16) فقط مجوز prep بود؛ بستن G0 فقط با امضای [[DecisionLog#DL-2026-07-20-G0 — حقیقتِ GATE 0\|DL-2026-07-20-G0]] | outward actions |
| PF-V2 | Branch انتخاب شده؟ | A/B/unknown | **open (UNKNOWN)** — اقامت C روی دیسک قابل‌اثبات نیست؛ ثبت فقط در DL-2026-07-20-G0 | ops path |
| PF-V3 | توافق دو نفره نوشته شده؟ | yes/no | **superseded → DL-2026-07-20-AGREEMENT** — متن کامل درفت شد؛ امضا **قبل از Day-Zero** (نه بعد از درآمد — آن حالت G0 را وارونه می‌کرد) | consent/legal |
| PF-V4 | قوانین ۸گانه ثابت‌اند؟ | yes/no | **yes** (تأیید شده — بدون تغییر از ۲۰۲۶-۰۷-۰۳) | hard rules |
| PF-V5 | فعلاً فقط research/drafts بماند؟ | yes/no | **INVALID-pending → DL-2026-07-20-PF-V5** — «Full Aggressive» (07-16) هرگز وارد DecisionLog نشد؛ تا `APPROVED: REVOKE` یا `APPROVED: RATIFY-CONDITIONAL` از A، مجوز لانچ نیست (پیش‌فرض: REVOKE) | scope |
| PF-STRUCT-V1 | انتقال واقعی فایل‌ها طبق `00 - Control/OBSIDIAN-STRUCTURE-v1.md`؟ | yes-all / yes-docs-only-not-code / no-keep-flat / later | superseded → PF-STRUCT-V2 | Obsidian filing |
| PF-STRUCT-V2 | اجرای `00 - Control/MIGRATION-MAP-2026-07-12.md` (فقط اسناد؛ کد سرجایش)؟ | yes-phase1-only / yes-phases-1-2 / yes-all-doc-phases / no / later | open | dedup + Obsidian filing |
| PF-STATE-RESET-V1 | reset ‏`studio/drafts.json` به `[]`؟ (۲۴۴ ردیف ۱۰۰٪ تستی؛ نسخهٔ فعلی آرشیو می‌شود) | yes/no/later | **done** (2026-07-16: ۲۱ ردیف به `_Archive/studio-state-snapshots/` منتقل شد) | runtime state |
| PF-CODE-REFACTOR-V1 | rename شناسه‌های سورس حاوی نام C در `studio/` (opsec) — refactor گیت‌دار؟ | yes/no/later | **implemented-on-branch (2026-07-20)** — طبق §C1 مگاپرامپت مالک؛ ratify نهایی = ballot Q11. توجه: پیش‌فرض «PII در git نیست» غلط بود (SCAN-LOCK §6: PII در docs/تست/selftest tracked است) | opsec hygiene |
| PF-LAUNCH-SAFETY | فعال‌سازی safety nets (warm-up/DM HITL/warning kill) برای لانچ؟ | yes/no | **done (کد ساخته شد 07-16)** — ادعای «۱۰۰/۱۰۰ سبز» بازنشسته؛ عدد صادق فقط در DL-2026-07-20-TESTS. نکته: باگ fail-open ‏ChannelLocks روی JSON خراب در sprint ‏07-20 فیکس شد | launch readiness |
