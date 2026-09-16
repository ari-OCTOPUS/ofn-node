---
type: report
status: ready
tags: [gap-analysis, architecture, evaluation-security, governance]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[04 - Architect System/architect/04-Docs/2026-07-06 0245 GAP-ANALYSIS-2026]]"
  - "[[04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v2]]"
  - "https://arxiv.org/abs/2606.10062"
  - "https://arxiv.org/pdf/2603.11337"
---

# بازبینی DEEP-GAP-ANALYSIS v2.0 — راستی‌آزمایی + نگاشت به اندام‌های موجود

> متن کامل v2.0 که آری فرستاد در chat است؛ ثبت رسمی آن پس از verdict ساختار پیشنهادی پایین. این نوت سه چیز می‌دهد: (۱) نتیجه spot-check منابع، (۲) **نگاشت شکاف‌ها به اندام‌هایی که از قبل در SYSTEM-BLUEPRINT-v2 طراحی شده‌اند** — تا دوباره‌سازی نشود، (۳) پیشنهاد مسیر اجرا.

## ۱. راستی‌آزمایی (spot-check دو منبع بحرانی‌ترین)

- **FRS / privacy-utility frontier (شکاف ۱۳):** paper واقعی است — arXiv 2606.10062 «Deployment-Time Memorization in Foundation-Model Agents»؛ ادعاهای PR/AER دقیقاً match. ✅
- **evaluator-tampering (شکاف ۲/۸):** پایه پژوهشی واقعی است — RewardHackingAgents (arXiv 2603.11337): نرخ exploit ۰–۱۳.۹٪ بین ۱۳ مدل frontier، و «evaluator locking تلاش‌های tampering را حذف می‌کند» match. ✅
- **⚠️ اما:** خود دامنه‌های وبلاگی (swarmsignal، clawrxiv، fable5.app، ai-blogs، paperdive و…) در جستجو مستقلاً پیدا/تأیید نشدند — paperهای زیرین واقعی‌اند، بلاگ‌های واسطه نامطمئن. قبل از اقدام روی هر شکاف، منبع اصلی (arXiv) مبنا باشد نه بلاگ.

## ۲. نگاشت به اندام‌های موجود — مهم‌ترین یافته بازبینی

v2.0 از روی فایل‌های آپلودی ساخته شده و **SYSTEM-BLUEPRINT-v2 را ندیده**. حداقل ۷ شکاف از ۱۶، اندام طراحی‌شده (و بعضاً نیمه‌ساخته) در همین vault دارند — مسیر درست «سیم‌کشی اندام موجود» است، نه ساخت لایه نو:

| شکاف v2 | اندام موجود | وضعیت |
|---|---|---|
| ۲ ارزیاب بدبین | judge بین‌خانواده‌ای (Gemini برای Claude، kappa ≥0.7) — blueprint §۴ | طراحی‌شده؛ context-تازه/تنش ۵–۱۵ دوره را ندارد → گسترش، نه ساخت |
| ۸ holdout/gaming | گیت سه‌شرطی: anchor 50–100 + **held-out unseen** + صفر failure نو + refresh فصلی ~۲۵٪ (ضد Goodhart) — §۴ | طراحی‌شده؛ `held_out.json` واقعی = BACKLOG-11 |
| ۱۴ policy-engine جدا | P3 (constraints خارج از prompt) + جدول `action_policy` + PatchManager — §۶ | دقیقاً همین الگو؛ ساختش BACKLOG-08 |
| ۶ ارزیابی per-layer | eval سه‌لایه L1/L2/L3 + چهار span — §۸ | جزئی؛ coverage-honesty و regression-injection ندارد |
| ۱۲ sleep/consolidation | `mycelial-consolidator` شبانه + evaporation/TTL | زنده! فقط ADD/UPDATE/DELETE/NOOP روی ledger ندارد |
| ۱۱ execution-state | DBOS-style journaling (D-15) — §۷ | طراحی‌شده، اجرا نشده؛ + P-08 (idempotency_key) در build-proposals/08 |
| ۱۵ cost attribution | مدل بودجه دو-mode + alert پلکانی + گزارش هفتگی — §۵ | orchestration-token جداسازی ندارد → افزودنی کوچک |

شکاف‌های واقعاً نو (اندام ندارند): **۱** (mutation_target multi-lever)، **۴** (FAILURE→REPAIR)، **۵** (dependency graph)، **۷** (consensus-gate)، **۹** (delegation-eligibility)، **۱۰** (alignment-signal مستقل)، **۱۳** (FRS test)، **۱۶** (reframe استراتژیک).

## ۳. جمع‌بندی و مسیر پیشنهادی (verdict با آری)

- تز مرکزی v2 درست و هم‌راستا با آدیت‌های قبلی خود vault است: **۶ شکاف بحرانی = یک مسئله واحد evaluation-security، پیش‌شرط L2.**
- پیشنهاد: به‌جای ۱۶ کار، **یک workstream «EVAL-SECURITY»** در BACKLOG با این ترتیب: (الف) BACKLOG-11 (held-out واقعی) + judge بین‌خانواده context-تازه → شکاف‌های ۲/۸؛ (ب) BACKLOG-08 (action_policy) → شکاف ۱۴؛ (پ) `mutation_target` + alignment-invariants دست‌نویس آری → شکاف‌های ۱/۱۰؛ (ت) ارتقای consolidator به reconsolidation → شکاف ۱۲.
- شکاف ۱۳ (FRS) مستقل و مهم برای C17 — یک تست دوره‌ای، قابل‌افزودن به scripts.
- شکاف ۱۶ هشدار استراتژیک سالمی است و با P7 (بودجه پیچیدگی) خود blueprint هم‌صداست: convenience layer نساز.
