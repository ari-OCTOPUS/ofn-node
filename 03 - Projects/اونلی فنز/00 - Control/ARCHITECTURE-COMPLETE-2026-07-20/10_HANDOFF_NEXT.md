---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, handoff]
created: 2026-07-20
updated: 2026-07-20
---

# 10 · HANDOFF — پرامپت خودکفا برای ایجنت بعدی

```text
تو ایجنت بعدیِ Project-F هستی (پوشهٔ «03 - Projects/اونلی فنز»). قبل از هر کاری:
1) بخوان: 00 - Control/GATE-STAMP-2026-07-20.md → حکم فعلی PAGE_SETUP (تا مالک عوضش نکرده: NO-GO).
2) بخوان: DecisionLog.md بخش «2026-07-20 — Forced Completion Sprint» — SoT تصمیم‌هاست؛ VERDICT_QUEUE فقط سینی رأی.
3) بخوان: 00 - Control/SCAN-LOCK-2026-07-20.md (شواهد قفل) + ARCHITECTURE-COMPLETE-2026-07-20/01..09.

قواعد سختِ تغییرناپذیر:
- هیچ اکانت/پست/DM/پرداخت/KYC/BotFather تولیدی تا GATE-STAMP=GO با امضاهای DecisionLog.
- _ops/STOP-ORGANISM را هرگز حذف/دور نزن؛ تست‌ها با monkeypatch مدارا می‌کنند (tests/README.md).
- PII هرگز echo نمی‌شود؛ اشخاص فقط A/C؛ نام C دیگر در هیچ identifier سورس نیست — برنگردانش.
- body-expansion منجمد است (DL-2026-07-20-BODY-FREEZE)؛ فقط رضایت مکتوب دوطرفه بازش می‌کند.
- عدد تست فقط با فرمان+خروجی واقعی (runnerها: tests/README.md؛ آخرین عدد صادق: 209/209).

اگر مالک ballot را پر کرده بود (00 - Control/OWNER-BALLOT-2026-07-20.md):
- جواب‌های ۱–۴ را عیناً به DecisionLog منتقل کن (status → APPROVED)، manifest.gates.G0 را فقط اگر DL-G0 امضا شد CLOSED کن، هر دو VERDICT_QUEUE را همگام کن، و GATE-STAMP را بازنویسی کن.
- Q10/Q11 = مجوز merge برنچ sprint؛ Q8=YES ⇒ چرخش شماره/بررسی filter-repo را به مالک یادآوری کن.

کارهای در صف (بدون نیاز به GO): R2/R3/R6/R12 از 07_BACKLOG_REMAINING.md (کوچک و درون‌پوشه).
کارهای گِیت‌دار: R9 (scrub ‏Sydney از کپی عمومی — قبل از هر bio) · R10 (انتقال PII — فقط رأی مالک) · R5 (pf_os — فقط ADR جدید).

پایان جلسه: PROJECT.md (Active Context/Progress) + HANDOFF داشبورد + دو validator طبق قانون اساسی.
```

نکتهٔ worktree: این sprint روی برنچ `claude/project-f-governance-sprint-515cf3` در worktree ‏`parallel-agents-7bf4ec` است؛ pf_os و SYNTH-05 و state زندهٔ langar_config فقط در درخت زندهٔ `F:\backup` هستند. قبل از merge، دیف را با مالک مرور کن.
