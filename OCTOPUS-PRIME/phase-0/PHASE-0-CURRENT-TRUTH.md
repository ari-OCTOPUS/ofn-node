# PHASE-0-CURRENT-TRUTH — OCTOPUS safety substrate

> **تاریخ:** 2026-07-22 · **branch:** `blocker-fixes-2026-07-22` (worktree `F:\octopus-blocker-wt`)
> **master/live:** `05d2b5a` — **یک بایت هم تغییر نکرد.**
> قانون این سند: هر خط یا `[FACT: executed]` است، یا `[source-read]`، یا `[OPEN]`. هیچ سبزِ کاذب.

## حکم کلان: `CONDITIONAL — Phase 0 هنوز باز است`

- **LIVE MERGE:** NOT AUTHORIZED
- **LIVE ACTIVATION:** NOT AUTHORIZED
- سه BLOCKER: **end-to-end بسته نشده‌اند** (جزئیات زیر)

## وضعیت دقیق هر آیتم Phase 0

| آیتم | وضعیت | مدرک |
|---|---|---|
| اسکن source-first از `F:\backup` | `[FACT: executed]` | git grep/read روی HEAD `05d2b5a` |
| safety backup بیرون از live tree | `[FACT: executed]` | `F:\octopus-untracked-safety-2026-07-22` |
| **backup manifest + restore drill** | `[FACT: executed]` | `SAFETY-BACKUP-MANIFEST.json` (459 فایل، SHA-256) + `RESTORE-DRILL-REPORT.md` (459/459 byte-identical) |
| **flags census (بدون افشای secret)** | `[FACT: executed]` | `FLAGS-AUTHORITY-REPORT.md` — ۲۹ WIRE، ۲۷ armed، **۶ LIVE-EFFECT armed** |
| worktree ایزوله + master روی 05d2b5a | `[FACT: executed]` | `git worktree list` |
| **BLOCKER-1 (fail-closed کاملِ authorization→release→settle)** | `[FACT: executed]` (candidate) | commit `88d07f2`؛ invariant `authorized==False ⇒ released==0`؛ ۱۰/۱۰ تستِ hermetic |
| **BLOCKER-2 (id-bound routing)** | `[FACT: executed] جزئی` | commit `8b61aa0`؛ effect_id→release_one. **باقی‌مانده:** approval بدون effect_id هنوز batch → نیازمندِ ستون `proposal_id` (بخش C) |
| **BLOCKER-2 (فیکس کامل: proposal_id schema + migration)** | `[OPEN]` | طراحی در `CHRONO-SCHEMA-MIGRATION.md` (هنوز نوشته نشده) |
| **BLOCKER-3 (watchdog → canonical STOP)** | `[FACT: executed] جزئی` | commit `8b61aa0`؛ watchdog اصلاح شد. **باقی‌مانده:** کل global-halt matrix + integration test |
| global halt matrix | `[source-read] جزئی` | `GLOBAL-HALT-MATRIX.csv` — هستهٔ oracle/gate/watchdog FACT؛ organism/cortex/ps_writeback/launchers **OPEN** |
| **integration test (HALT-ALL → صفر effect)** | `[OPEN]` | نیازمندِ isolated test launcher (بخش F) |
| **isolated test launcher + full sandbox suite (۲۵۱ تست)** | `[OPEN]` | `opslib.ORG_ROOT` پیش‌فرض = literal `F:\backup` → اجرای امنِ کل suite هنوز ساخته نشده |
| flags disarm (owner packet) | `[FACT: executed]` (packet آماده) | `PHASE-0-OWNER-APPROVAL-PACKET.md` — پیشنهادِ disarm، **اجرا با مالک** |
| انتقال propagation-lab به ژنوم (بخش H) | `[OPEN] — عمداً بعد از Phase 0` | نباید هم‌زمان با جراحی safety انجام شود |

## آنچه در این نشست تضمین شد (صداقت روش)

- **live tree:** صفر بایت تغییر (mtime `F:\backup\_ops\state` قبل/بعدِ هر تست یکسان).
- **network call:** صفر (هیچ‌چیز اجرا نشد که شبکه بزند؛ تست‌ها fakeها را استفاده کردند).
- **secret exposure:** صفر (flags census فقط نامِ WIRE + 0/1؛ ۱ خطِ secret-ish شمرده و redact شد).
- **schema migration:** هنوز اجرا نشده (نه روی fixture نه live) — `[OPEN]`.
- **تعداد تست:** تست‌های بلاکر ۱۰/۱۰ pass (hermetic). کل ۲۵۱ تستِ repo: **اجرا نشد** (نیازمندِ launcher ایزوله — بخش F).

## سه BLOCKER — آیا end-to-end بسته شدند؟

- **BLOCKER-1:** بله، end-to-end (authorization gate روی release/settle + ماتریس تست). ✅ candidate.
- **BLOCKER-2:** خیر — نیمه (id-bound routing بله؛ حذف کاملِ batch برای money نیازمندِ schema). ⚠️
- **BLOCKER-3:** خیر — فقط watchdog؛ کل ماتریس halt + integration test لازم است. ⚠️

## merge readiness: **NO-GO** (طبق حکم مالک)
