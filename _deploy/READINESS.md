---
type: knowledge
status: active
created_by: agent
created: 2026-07-06
updated: 2026-07-06
tags: [deploy, readiness]
---

# READINESS — چک‌لیست آمادگی دیپلوی (deploy-lab)

> این فایل توسط لوپ **deploy-lab-loop** در هر اجرا بازنویسی می‌شود. معیار DONE: هر ۷ ردیف سبز در دو اجرای متوالی، **یا** باقیماندهٔ غیرسبزها همگی «blocked-on-owner».

| # | چک | وضعیت | جزئیات (2026-07-06، بعد از پاس بزرگ ۸-ایجنتی) |
|---|---|---|---|
| 1 | فرانت‌متر: `validate_frontmatter.py` → ۰ خطا | ✅ | ۲۲۵ نوت، صفر خطا (۳۳→۰؛ بستهٔ `_audit` استانداردسازی شد، متادیتای اضافی به بدنه منتقل شد — بدون از‌دست‌رفتن اطلاعات) |
| 2 | لینک: `find_broken_links.py` → ۰ شکسته | ✅ | ۵۴۰ نوت، صفر لینک شکسته (placeholder → متن ساده؛ لینک SECRETS-ROTATION → متن ساده چون فایل عمداً untracked است، الگوی `*secret*` در `.agentignore`) |
| 3 | Inbox خالی: فقط `AGENT_QUESTIONS.md` | 🟡 blocked-on-owner | ۳۳ فایل + ۲ پوشه route شد (→ architect/04-Docs و 03-Exports، همهٔ لینک‌ها اصلاح). باقیمانده ۲ استثنای مستند: `DOCTOR-SYNTHESIS.md` (pinned — تسک زندهٔ doctor به همین مسیر می‌نویسد؛ جابه‌جایی = تغییر پرامپت تسک، تصمیم مالک) و پوشهٔ `scout-digests/` (خروجی زندهٔ ناوگان اسکات؛ جای دائمی = تصمیم مالک) — **هیچ آیتم پردازش‌نشده‌ای نمانده** |
| 4 | کد اجراشدنی | 🟡 blocked-on-owner | syntax ✅ (node --check ۷/۷ · py_compile ۳/۳) · **npm install ❌**: better-sqlite3 روی Node v24.8 پری‌بیلت ندارد + build محلی بدون VS Build Tools شکست می‌خورد. سه گزینهٔ مالک: (الف) نصب VS Build Tools؛ (ب) ارتقای better-sqlite3 در package.json به نسخهٔ دارای پری‌بیلت node-24؛ (ج) اجرا با Node LTS (20/22) از طریق nvm. یک تعارض ثانویه هم ثبت شد: chartjs-node-canvas ↔ chart.js@^4 (با `--legacy-peer-deps` رد می‌شود) |
| 5 | اسکن secret: ۰ یافتهٔ واقعی | ✅ | CLEAN — ۷ مورد pattern-match همگی false-positive/template تأییدشده (فایل‌های نام‌match نشده باز نشدند) |
| 6 | PROJECT.mdهای فعال با Active Context/Progress تازه | ✅ | هر ۸ شناسنامه refresh شد (`updated: 2026-07-06`) |
| 7 | HANDOFF تازه و فقط-wikilink | ✅ | بازنویسی شد (زیر ۶۰ خط) |

**سبز کامل: ۵/۷ · بقیه (۲): همگی blocked-on-owner → وضعیت DONE-قابل‌قبول طبق معیار**

## blocked-on-owner (تصمیم‌های لازم برای ۷/۷ کامل)

1. **چک ۴ — npm:** یکی از سه گزینهٔ بالا (پیشنهاد: گزینهٔ ب — ارتقای better-sqlite3؛ کم‌دردسرترین و داخل repo).
2. **چک ۳ — DOCTOR-SYNTHESIS.md:** بماند در Inbox (هم‌راستا با تسک زندهٔ doctor) یا منتقل شود به `07 - Knowledge/_doctor-research/` + آپدیت پرامپت تسک.
3. **چک ۳ — scout-digests/:** جای دائمی (ماندن در Inbox به‌عنوان استیجینگ ناوگان، یا پوشهٔ اختصاصی).

## یادداشت merge-back

بعد از DONE، پیشنهاد merge به vault اصلی (فقط با verdict مالک): `git -C "C:\Users\Armin\Desktop\backup" pull "C:\Users\Armin\Desktop\backup-deploy-lab" master` — توجه: vault زنده از لحظهٔ clone (کامیت 0e2715f) جلو رفته؛ merge ممکن است conflict بخواهد.
