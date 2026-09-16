---
type: research
status: inbox
created_by: agent
tags: [research, synthesis]
created: 2026-07-04
updated: 2026-07-04
---

# اجرایی — 2026-07-04 (exec-digest شبانه)

> یک صفحه، اسکیم‌شدنی. بالاترین-salienceهای امروز با یک‌خطِ **آماده-verdict**. جزئیات: [[00 - Inbox/scout-digests/2026-07-04 synthesis|سنتزِ کامل]] · صفِ کامل: [[00 - Inbox/scout-digests/_TRIAGE-BOARD|_TRIAGE-BOARD]].

**داستانِ امشب در یک خط:** ناوگان از «جمع‌آوری» عبور کرد و یک **معماریِ زیستیِ خودمحافظ** سرِهم کرد — سیستمِ ایمنی (۵ گیتِ fail-closed) + حافظهٔ خواب (۳ فعلِ persist/consolidate/retrieve) + بازخوردِ تکاملی — همه زیرِ یک قیدِ واحد: **حلقه بدونِ لنگرِ واقعیتِ بیرونی فرومی‌پاشد (Model-Collapse/MAD).** هیچ‌چیز اعمال نشد؛ همه منتظرِ verdictِ آری.

## ۵ تصمیمِ نوکِ صف (آماده-verdict)

| # | تصمیم | یک‌خطِ آماده-verdict | جنس · هزینه |
|---|---|---|---|
| 1 | [[00 - Inbox/scout-digests/2026-07-04 1744 selfimprove\|Quorum Gate]] — κ≥0.7 را بردار | «عددِ ۰.۷ در v3 خراب است؛ حذفش کنم و با per-action allowlist + conformal-abstention جایگزین شود؟» | safety · **گام۰ بدون‌کد، امشب** |
| 2 | [[00 - Inbox/scout-digests/2026-07-04 philosophy\|ضدِ MAD]] — لنگرِ خارجی | «هر دورِ selfimprove ملزم شود ≥۱ منبعِ خارجیِ غیرِ-fleet بیاورد + یک decision-journal برای کالیبراسیون؟» | deep · قاعده (قیدِ بالادستیِ همه) |
| 3 | [[00 - Inbox/scout-digests/2026-07-04 2054 selfimprove-safety\|Anoikis]] + [[00 - Inbox/scout-digests/2026-07-04 1911 selfimprove\|Apoptosis]] | «وقتی kernelِ ایمنی spawn نشد ران **halt** شود نه سکوت؟ `except`ِ عریض باریک و `ALLOW_COOPERATIVE_FALLBACK=False` شود؟» | safety · کد، پشتِ گیتِ rotation (HAR) |
| 4 | [[00 - Inbox/scout-digests/2026-07-04 2031 selfimprove-memory\|Slow-Wave]] + [[00 - Inbox/scout-digests/2026-07-04 2050 selfimprove-memory\|Retrieval-Gated]] | «اجازه بده همین consolidator شبانه episodic→semantic (K≥۳ deposit مستقل، با backlinkِ lossless) + reinforce-on-retrieval را آزمایش کند؟» | memory · **گام۰ روی خودِ consolidator** |
| 5 | [[00 - Inbox/scout-digests/2026-07-04 2049 selfimprove\|Fitness Ledger]] + [[00 - Inbox/scout-digests/2026-07-04 2008 selfimprove\|Calibrated-Confidence]] | «کلیدهای `verdict/outcome` + `_FITNESS-LEDGER` را شروع کنم تا اعتمادِ هر lane با پیامدِ *واقعی* کالیبره شود؟» | orchestration · گام۰ (فقط VIEW روی frontmatter) |

## فوری و واقعی (opsec — نه معماری؛ سریع‌ترین برد)

از [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]: (۱) `.env` داخلِ vault در `کاریابی/bot/` → باید بیرون رود. (۲) نشتِ نامِ [Project-F] در ۴ فایل (نقضِ charter §6). (۳) `spacing_x_expectancy_protocol` بدجاافتاده در Crypto → به `07 - Knowledge`. (۴) تناقضِ ظرفیتِ Ziman (کد=۳۰ ولی PROJECT «ثبت‌نشده»). **کم‌ریسک‌ترین و سریع‌ترین verdictها همین‌هایند.**

## ۳ الگوی نوِ بین‌پروژه‌ای (امشب به [[00 - Inbox/scout-digests/_Mycorrhizal Map|نقشه]] افزوده شد)

- **P6 Backpressure** — صفِ verdict = صفِ لیدِ Lead = صفِ سیگنالِ Crypto → همه admission-control/WIP-cap می‌خواهند.
- **P7 حلقه را با واقعیت ببند** — بدونِ بازخوردِ پیامدِ واقعی، هم selfimprove هم Lead (تبدیلِ لید) هم Crypto (P&L) «کور» بهبود می‌دهند.
- **P8 death-watch** — «قبل از ماین، chain-liveness چک کن» = «قبل از ران، اتصالِ kernel چک کن» (Mining ↔ Anoikis).

## دامنه‌ای‌های آمادهٔ promote (تأییدِ سریع)

`crypto`→Crypto · `mining`→Mining · `accounting`→Accounting · `hypnosis`→`07 - Knowledge` · `philosophy`→architect `02-Research`.

## چه امشب تغییر کرد

نقشهٔ مایکوریزایی رشد کرد (P6/P7/P8 + ردیفِ `selfimprove`)؛ `_TRIAGE-BOARD` به ۱۲ آیتمِ تازه رتبه‌بندی شد؛ سنتزِ کامل بازنویسی شد. **Evaporation: هیچ** (همهٔ ۳۰ دیجست <۱۴ روز؛ اولین کاندید ~۲۰۲۶-۰۷-۱۸). یک کاندیدِ prune: دیجستِ ۲۰۲۶ (light/defer، جذب‌شده در Costimulation).
