---
type: truth
status: active
tags: [octopus, discovery, backlog, directive-9]
created: 2026-08-20
updated: 2026-08-20
authority: OWNER-DIRECTIVE-09 §۷ (فایل backlog)
columns: task_id, title, layer, priority, status, verdict, evidence_path, session
status_vocab: PROPOSED | RUNNING | DONE | BLOCKED | REJECTED | SUPERSEDED
---

# DISCOVERY-BACKLOG — موتور کشف خودگردان (شروع: 2026-08-20 جلسهٔ ZCode)

فرمول اولویت (§۵): ‏`2×truth_risk + 1.5×blocker + 1×info_gain + 0.5×cheap − 2×safety − 1×deps`
(هر مؤلفه ۰–۳). سهمیهٔ هر جلسه: ۵ تسک برتر + ۱ کاوش.

| task_id | title | layer | priority | status | verdict | evidence_path | session |
|---|---|---|---|---|---|---|---|
| DISC-20260820-01 | چارچوب بنچمارک سوگیری داور (۲۰ تسک، ۱۲۰ جفت، ۵ داور، هیت‌مپ) — اجرای آفلاین با داورهای دارای سوگیری تزریقی | understanding | **11.5** | DONE | CONFIRMED (۵/۵ سوگیری تزریقی بازیابی) | 06-EVIDENCE/DISC-01-JUDGE-BIAS-2026-08-20.md | ZCode #9 |
| DISC-20260820-02 | داشبوردمحاکاه Active Inference با pymdp (grid-world، EFE، اسلایدر epistemic/pragmatic، نمودارهای زنده) — آفلاین | decision | **9.0** | DONE | CONFIRMED (اجرا + اسموک‌تست سرِ دیگر) | 06-EVIDENCE/DISC-02-ACTIVE-INFERENCE-2026-08-20.md | ZCode #9 |
| DISC-20260820-03 | تحلیل سوگیری جایگاه روی دادهٔ واقعی موجود (k9-triple + پایلوت، بدون فراخوان تازه) | understanding | **8.5** | DONE | CONFIRMED (ناپایداری جفت‌محور؛ n=6 اجرا) | 06-EVIDENCE/DISC-03-REAL-JUDGE-AUDIT-2026-08-20.md | ZCode #9 |
| DISC-20260820-04 | ممیزی استاتیک: هر مسیری که executable را true می‌کند | safety | **8.0** | DONE | CONFIRMED (صفر مسیر تازه؛ ۲ مسیر گاردی) | 06-EVIDENCE/DISC-04-EXECUTABLE-AUDIT-2026-08-20.md | ZCode #9 |
| DISC-20260820-05 | مرور گزارش T48 پس از 15:49 و حکم LIVE-B | senses | 7.5 | BLOCKED | گزارش هنوز نیامده (زمان‌بندی 15:49) | — (پس از رسیدن) | ZCode #9 |
| DISC-20260820-06 | سنسورهای مرده: متریک‌هایی که هرگز تغییر نمی‌کنند (پنجرهٔ ۷ روز) | senses | 6.5 | PROPOSED | — | — | — |
| DISC-20260820-07 | نسبت ثبت evidence به beat: چند درصد beatها evidence دارند | memory | 6.0 | PROPOSED | — | — | — |
| DISC-20260820-08 | حساسیت skill score به مؤلفه‌ها (کدام مؤلفه بی‌اثر است) | decision | 6.0 | PROPOSED | — | — | — |
| DISC-20260820-09 | پوشش lease: آیا همهٔ نویسنده‌های واقعی از آن می‌گذرند (static) | safety | 5.5 | PROPOSED | — | — | — |
| DISC-20260820-10 | surprise سادهٔ تاریخی و همبستگی با AMBER/RED | decision | 5.0 | PROPOSED | — | — | — |
| DISC-20260820-11 | حافظه‌های مشتق بی‌اعتبارشده پس از دادهٔ دیررس | memory | 4.5 | PROPOSED | — | — | — |
| DISC-20260820-12 | کاوش: نگاشت متریک‌های زنده به مؤلفه‌های مدل مولد (پل Active Inference) | decision | 4.0 (کاوش) | PROPOSED | — | — | — |

قاعدهٔ §۴ رعایت شد: هر تسک اجراشده falsifier عددی دارد (در evidence هرکدام).
تسک‌های نیازمند فراخوان پولی/داور واقعی فقط به‌صورت پیش‌ثبت امضایی ثبت می‌شوند
(کارت PRE-REG-JUDGE-BIAS-REAL در evidence تسک ۰۱).

| DISC-20260820-13 | نویسندهٔ جفت‌مارکر C-047 (استاتیک §۱۰ دستور #۱۲) | safety | 8.5 | DONE | CONFIRMED (RESTART-PROCESS.ps1؛ اصلاح + تست ۶/۶) | 06-EVIDENCE/DIRECTIVE-12-REPORT-AGENT-B-2026-08-20.md | ZCode #12 |
| DISC-20260820-14 | نگاشت Active Inference + surprise اکتشافی (§۹) | decision | 7.0 | DONE | NOT_READY_FOR_ACTIVE_INFERENCE (GREEN 17.33 vs AMBER 17.81 nat · n_AMBER=56) | 06-EVIDENCE/DIRECTIVE-12-REPORT-AGENT-B-2026-08-20.md | ZCode #12 |
| DISC-20260820-15 | صدور خودکار LIVE-B پس از داده‌ها (§۱۱) | senses | 7.0 | PROPOSED | — (منتظر تلگرام+server_created) | — | — |

| DISC-20260820-16 | parser RBA کامل با schema-validation + logging ردیفی + reconciliation ماهانه (درخواست مالک) — **منجمد تا حلقهٔ بسته** (§۱ مگادستور #۱۳) | senses | 6.0 | REJECTED-FROZEN | — | — | ZCode #13 |
| DISC-20260820-17 | شبیه‌ساز audit-log هش‌چین SHA-256 + signing + notarization + dashboard شکست‌ها (درخواست مالک) — **منجمد تا حلقهٔ بسته** (§۱ مگادستور #۱۳) | safety | 5.5 | REJECTED-FROZEN | — | — | ZCode #13 |
| DISC-20260820-18 | تداخل 409 Telegram: center/approval_channel همان bot token را long-poll می‌کنند؛ راه‌حل = توکن اختصاصی کاکپیت (رأی مالک) | governance | 7.5 | BLOCKED | — | research/full_loop/telegram_cockpit.py (env: TELEGRAM_COCKPIT_TOKEN) | ZCode #13 |
