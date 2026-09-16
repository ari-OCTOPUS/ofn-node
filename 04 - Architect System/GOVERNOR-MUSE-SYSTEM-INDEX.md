---
type: moc
status: active
created: 2026-07-06
updated: 2026-07-06
owner: آری
aliases: [GOVERNOR-MUSE, سیستم-گاورنر-میوز, penta-system]
summary: "نقشهٔ کاملِ سیستمِ GOVERNOR (سرپرستِ ۲۴ساعته) + MUSE (جعبه‌سیاهِ خلاقیت) + دکترِ تکاملی — از تطبیق تا اسکریپت‌های آماده."
tags: [moc, index, governor, muse, evolutionary-doctor, propose-only, learning-engine]
related: "[[00-Home]] · [[PROJECT]] · [[GENOMIC-ARCHITECTURE]] · [[MUTATION-WHITELIST]]"
---

# 🗺️ INDEX — سیستمِ GOVERNOR + MUSE (پنج‌گانه)

> **برای ایجنت‌های دیگر:** این نقشهٔ مرجعِ یک سیستمِ جدید است که ۲۰۲۶-۰۷-۰۶ طراحی، بازنگری و ساخته شد. **همه propose-only مگر جایی که «اعمال‌شد» علامت خورده.** قانونِ حاکم دست‌نخورده: propose→approve، read-only ژنوم، kill-switch، بودجه.

## چیست (یک بند)
دو ایجنتِ جدیدِ ژنوم‌نشین: **GOVERNOR** = سرپرستِ همیشه‌روشن (uptime · دکتر · گاردِ ژنوم · بودجه · تشدیدِ تلگرام؛ فقط propose). **MUSE** = جعبه‌سیاهِ خلاقیت (read-only به همه‌جا، ایده‌های مرزِ دیوانگی↔نبوغ با «ترسِ بی‌نهایت» → **دکترِ تکاملی** که غربال می‌کند و فقط بازمانده‌ها را به میزِ آری می‌فرستد). آنالوگِ زیستی: MUSE=somatic hypermutation، دکتر=clonal selection، ledger=وراثت، آری=فشارِ انتخاب.

## مبنا و طرح
- [[2026-07-06 RESEARCH-GENOME-RECONCILIATION-proposal]] — تطبیقِ تحقیق با ژنوم (۳ دریفت + ۲ دلتا + ۳ مردود)
- [[2026-07-06 PENTA-PROMPT-Governor-Muse-proposal]] — پرامپتِ مادرِ پنج‌فاز
- [[2026-07-06 METABOLIC-GOVERNOR-proposal]] — extension (جلسه ۲۰د): مغزِ سهمیه‌بندیِ API روی `budget_gate` (fitness/throttle/lend/burst)؛ **تعارض #۴ بسته: سقف = AU$30** → `_ops/budget/budgets.yaml`؛ shadow-پله‌ی همین INDEX؛ draft تا verdict

## پنج فاز (طراحی)
- [[2026-07-06 PHASE1-GOVERNOR-MUSE-CHARTER-proposal]] — منشورِ دو ایجنت *(آماده‌ی پیستِ آری در charter)*
- [[2026-07-06 PHASE2-GOVERNOR-SPEC-proposal]] — GOVERNOR
- [[2026-07-06 PHASE3-MUSE-SPEC-proposal]] — MUSE
- [[2026-07-06 PHASE4-MEMORY-INTEL-DOCTOR-proposal]] — حافظه + هوشمندی + دکترِ تکاملی
- [[2026-07-06 PHASE5-BACKUP-DR-INTERLOCKS-proposal]] — بک‌اپ + DR + قفل‌ها

## گزارش و بازنگری
- [[2026-07-06 PENTA-SYSTEM-REPORT+REVIEW]] — گزارشِ جامع + بازنگریِ adversarial (R1–R8)
- [[2026-07-06 REVIEW-FIXES-changelog]] — ۸ باگِ رفع‌شده با تستِ سندباکس

## شش runbookِ ساخت (اجرا سمتِ مالک)
- [[2026-07-06 BUILD-01-OFFBOX-BACKUP-runbook-proposal]] — بک‌اپ off-box *(قدم ۱)*
- [[2026-07-06 BUILD-02-GENOME-READONLY-GUARD-runbook-proposal]] — گاردِ ژنوم *(قدم ۲)*
- [[2026-07-06 BUILD-03-GOVERNOR-SHADOW-runbook-proposal]] — GOVERNOR shadow *(قدم ۳)*
- [[2026-07-06 BUILD-04-MUSE-DOCTOR-DRYRUN-runbook-proposal]] — MUSE/دکتر dry-run *(قدم ۴)*
- [[2026-07-06 BUILD-05-SHARED-BUDGET-runbook-proposal]] — بودجهٔ مشترک *(قدم ۵)*
- [[2026-07-06 BUILD-06-PILOT-TO-LIVE-CUTOVER-proposal]] — پایلوت→live *(قدم ۶)*

## اسکریپت‌های آماده (تست‌شده)
`scripts/SETUP-README.md` (نقطهٔ شروع) · `scripts/budget_gate.py` · `scripts/genome_guard.py` · `scripts/governor_shadow.py` · `scripts/backup-offbox.ps1` · `scripts/restore-drill.ps1` · `learning-engine/MUSE-QUARANTINE-LEDGER.md`

## چه چیزی اعمال شد ✅ در برابر فقط-مالک ⏳
- ✅ **اعمال‌شد:** رفعِ دریفت‌های ژنوم D1/D2/D3 (contract mode، STATE gate=LIFTED، ENGINE-PROMPT precedence) · اسکریپت‌ها در `scripts/` · این INDEX · لاگ در PROJECT/MUTATION-LEDGER.
- ⏳ **فقط-مالک (من نمی‌توانم):** پیستِ بلوکِ منشورِ فاز ۱ در `ARCHITECT_CHARTER` (charter برای ایجنت immutable) · `genome_guard --init` (تأییدِ ژنوم) · انتخابِ مقصدِ بک‌اپ + `rclone config` · زمان‌بندیِ Task Scheduler.

## ترتیبِ فعال‌سازی
بک‌اپ → گاردِ ژنوم → بودجه → GOVERNOR shadow → MUSE dry-run → (۳۰ روز پاک + verdict) → live. جزئیات: [[2026-07-06 BUILD-06-PILOT-TO-LIVE-CUTOVER-proposal]] §۳.
