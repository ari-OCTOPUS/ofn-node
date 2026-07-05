---
type: project
kind: area
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
owner: آری
risk_level: critical
autonomy_level: read-only
tags: [ai, automation, telegram, meta-system]
created: 2026-07-03
updated: 2026-07-06
---

# پروژه: architect

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه (مادر) میزبانِ ستون است؛ node در §۳ رجیستریِ اتصال (build/test/delete پشتِ verdict).

**هدف:** سیستم هوش مصنوعیِ خودکدنویس که همهٔ پروژه‌ها را بازرسی و کنترل می‌کند و از طریق تلگرام به من وصل است.

**دو ماژول:**

1. **محقق و طراح** — تحقیق خودکار و خودبهبودی براساس معماری‌ای که طراحی می‌کنیم.
2. **رئیس کل** — کنترل و بازرسی تمام سیستم‌ها و پروژه‌های دیگر؛ رابط من با کل اکوسیستم از طریق تلگرام.

**نقش در اکوسیستم:** لایهٔ مادر — همهٔ پروژه‌های دیگر (Accounting، Crypto، Mining، Lead-نقاشی، Ziman، اونلی فنز «Project-F»، هیپنوتیزم) زیر نظارت این سیستم اجرا و کنترل می‌شوند.

**قاعده حریم Project-F:** پروژه اونلی فنز در هر خروجی cross-domain (تلگرام، داشبورد، گزارش) فقط با کد «Project-F» ارجاع می‌شود — نه نام پلتفرم، نه هویت پارتنر، نه جزئیات محتوا. جزئیات فقط داخل پوشه خود پروژه.

## Active Context

- تمرکز فعلی: فاز ۱ اجرا شد — [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]] نوشته شد (verdict Phase 0 داده شد 2026-07-03)؛ **Security Gate بسته** تا چرخش CRITICALها
- تغییرات اخیر: 2026-07-03 — Phase 0 (secretها → secrets-export) + charter + manifest v2 همه دامنه‌ها + آدیت ۸-پاسه fusion-mvp کامل شد: ۰ Critical / ۴ High — [[04 - Architect System/architect/04-Docs/fusion-audit/AUDIT|AUDIT]] و [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN|REFACTOR_PLAN]] (TOP-5 با پرچم HUMAN-APPROVAL) · طراحی [[04 - Architect System/architect/01-Project/BRAIN-UPGRADE-LOOP|BRAIN-UPGRADE-LOOP]] (D-28) و [[04 - Architect System/architect/01-Project/OBSIDIAN-SYNC|OBSIDIAN-SYNC]] (D-29) ثبت شد؛ BACKLOG #21–#24
- ۳ قدم بعدی: (۱) rotation کلیدها (مالک) → باز شدن گیت (۲) اجرای TOP-5 آدیت با تأیید انسانی (۳) پرامپت Phase 4 — [[00 - Inbox/Prompt - Phase 4 Real Integration|Real Integration]]
- تغییرات اخیر: 2026-07-04 (agent) — بازبینی adversarial v3: [[04 - Architect System/architect/02-Research/Report - Architect - Adversarial Review v3 2026-07-04|Report Adversarial Review v3]]؛ ۶ دلتای اصلاحی به [[04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v3-proposal|v3-proposal §۶.۵]] افزوده شد (status=proposal دست‌نخورده، verdict با آری). یافته کلیدی: MAST (شکست multi-agent ۴۱–۸۷٪) استناد رسمی P7/D-02؛ عدد judge kappa≥0.7 غیرواقعی → حذف پیشنهاد شد؛ Mem0 graph = lock-in (فقط لایه vector OSS)
- تغییرات اخیر: 2026-07-04 (triage با verdict آری) — corpus تحقیق از Inbox به [[04 - Architect System/architect/02-Research/SCOUT-SUMMARY|02-Research]] منتقل شد (SCOUT-A/C/DEEP + گزارش‌های Architect + 20 AGI + پرامپت‌های اجراشده)؛ نقشه روابط: [[04 - Architect System/architect/02-Research/Report - Vault Relationship Map 2026-07-04 v3|v3 = canonical]]، v1/v2 و دو Self-Audit → `02-Research/_superseded` با status: archived؛ [[04 - Architect System/architect/04-Docs/AUDIT-PHASE3|AUDIT-PHASE3]] → 04-Docs؛ INGEST-INVENTORY و INGEST-EXCLUDED-SECRETS → 01-Project
- تغییرات اخیر: 2026-07-05 (agent) — منشور خودهدایتِ بازنویسی ساخته شد: [[MYCOLEDGER-REBUILD-CHARTER-proposal]] (status: proposal) — پرامپتِ سیستمِ عاملِ کدنویس (Codex/Claude Desktop) که پروژه را milestone-به-milestone تا «پایدار برای تستِ زنده» (M0..M2) بازنویسی می‌کند؛ v2 و [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]] دست‌نخورده، اجرا پشتِ §Security Gate، verdict با آری
- تصمیم‌های باز: خارج‌سازی secrets-export (مالک) · O-01 (VPS) · O-04 (محل داده شخصی — default: لپ‌تاپ) · verdict ۶ دلتای v3 (مالک)

## Progress

- چه کار می‌کند: —
- چه مانده: —
- مشکلات شناخته: —

## Next actions

- [ ] —

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[03 - Projects/Accounting/Accounting|Accounting]]
- [[03 - Projects/Lead-نقاشی/Lead-نقاشی|Lead-نقاشی]]
- [[03 - Projects/اونلی فنز/اونلی فنز|اونلی فنز]]
