---
type: recorded-note
status: active
tags: [octopus, owner-ruling, od-1, kill-switch, safety-critical]
updated: 2026-09-17
authority: owner
subject: OD-1 kill-switch path fragmentation
---

# OWNER RULING — OD-1: KILL-SWITCH PATH FRAGMENTATION

**Recorded verbatim. Owner decision. Date: 2026-09-17.**
Source: owner directive received in session 2026-09-17 (EMERGENCE-SAFE-SURGERY lane).
Registered by: planning/audit lane. This entry **records**; it does not open, close,
or modify any gate (`AGENTS.md` §4: "Blocked is a decision, not a defect").

---

## Decision

**Option B — canonical oracle + read-only doctor + loud mismatch detection.**

## Verbatim text of the decision

> ۱) یک halt oracle رسمی تعیین شود.
>    تمام اسناد، runbookها، agent promptها و ابزارهای عملیاتی باید به همان
>    مسیر canonical اشاره کنند.
>
> ۲) هیچ compatibility path نباید بی‌صدا باقی بماند.
>    هر مسیر قدیمی HALT باید یکی از این دو وضعیت را داشته باشد:
>    - alias سازگار که مکانیکی و قابل‌اثبات به oracle رسمی متصل است؛ یا
>    - deprecated که وجود/استفاده از آن هشدار بلند و receipt تولید می‌کند.
>
> ۳) یک ابزار فقط‌خواندنی halt-oracle doctor ساخته شود.
>    این ابزار حق ایجاد، حذف، تغییر یا arm کردن هیچ HALT file را ندارد.
>    فقط باید evidence جمع کند و نتیجه را ثبت کند.
>
> ۴) doctor باید برای هر process/service مربوط به Octopus گزارش دهد:
>    - service / process identity
>    - نسخه یا commit/runtime identity
>    - مسیر دقیق halt که آن process واقعاً resolve و read می‌کند
>    - وضعیت فایل: absent / present / malformed / unreadable / symlink
>    - وضعیت نهایی predicate: RUNNING / HALTED / UNKNOWN
>    - legacy halt fileهای کشف‌شده
>    - اختلاف میان oracle رسمی، اسناد، environment/config و runtime
>    - verdict: WIRED / TESTED_ONLY / DOC_ONLY / UNVERIFIED
>
> ۵) هر mismatch باید fail-loud باشد:
>    - receipt ماشینی append-only
>    - سطح severity
>    - دلیل دقیق
>    - مسیرهای درگیر
>    - owner-action-required=true در مواردی که تغییر runtime یا governance لازم است
>
> ۶) هیچ آزمایش زنده‌ای روی HALT انجام نشود:
>    - نه ایجاد فایل HALT
>    - نه حذف فایل HALT
>    - نه restart service
>    - نه تغییر environment
>    - نه تغییر budget / gate / systemd
>    تا زمانی که یک طرح آزمایش جداگانه و مجاز وجود داشته باشد.
>
> ۷) خروجی lane:
>    - report فقط‌خواندنی
>    - receiptهای doctor
>    - نقشهٔ oracleهای واقعی
>    - فهرست mismatchها
>    - patch proposal جداگانه، اما بدون اعمال patch

## Owner's stated rationale (verbatim)

> پیشنهاد من **گزینهٔ B** است: یک oracle رسمی، همراه با doctor و هشدار برای
> مسیرهای قدیمی. این هم مشکل واقعی را حل می‌کند و هم جلوی بازتولید همان خطای
> «سند می‌گوید کنترل هست، runtime چیز دیگری می‌خواند» را می‌گیرد.

## Standing constraints attached to this ruling

Two directive clauses from the same owner message bind this and the following lane:

> ۱) هنوز هیچ تغییری در ofn/**، HALT، budget، data/gates.json، systemd،
>    daemon، flags یا مسیر live انجام نده.

> ۲) OD-1 مربوط به kill-switch path fragmentation باز بماند.
>    هیچ مسیر HALT را canonical نکن، هیچ فایل HALT نساز، و هیچ kill-switch
>    آزمایشی روی node زنده فعال نکن تا رأی صریح مالک ثبت شود.

**Interpretation recorded for the next agent:** the owner has now *decided the
policy* (B), and has simultaneously *forbidden acting on it* until a separate
authorized experiment plan exists. So clause 1 of the ruling (canonical oracle) is
**decided but not yet permitted to execute**. The doctor (clauses 3–5) is authorized
to be **built read-only**; running it against live hardware is a separate step.

## Status

| Item | State |
|---|---|
| Policy decision | **DECIDED — Option B** |
| Canonical-oracle change (clause 1) | **DECIDED, NOT EXECUTED** (owner forbids changes until a separate authorized plan) |
| Doctor build (clauses 3–5) | **AUTHORIZED (read-only)** — spec at `09-LANES/LIVE-PATH-GATE-AUDIT-20260917/HALT-ORACLE-DOCTOR-SPEC.md` |
| Doctor run on live hardware | **NOT AUTHORIZED** — requires a separate plan |
| Any HALT file create/delete/arm | **FORBIDDEN** |
| Any restart / env / budget / gate / systemd change | **FORBIDDEN** |

Related: `07-HANDOFF/OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md` (now `status: decided`),
`plans/OCTOPUS-SAFETY-MAP-v1.md` §3 (D-3, D-9),
`09-LANES/LIVE-PATH-GATE-AUDIT-20260917/REPORT-GATE-ENQUEUE-AND-EGRESS-AUDIT.md`.
