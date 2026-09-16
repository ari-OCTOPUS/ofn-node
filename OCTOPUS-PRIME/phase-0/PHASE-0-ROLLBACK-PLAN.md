# PHASE-0-ROLLBACK-PLAN

همه‌چیزِ این نشست روی سطوحِ برگشت‌پذیر و ایزوله است. هیچ عملیاتِ برگشت‌ناپذیری روی
live انجام نشد.

## آنچه ساخته شد و چطور کاملاً برمی‌گردد

| اثر | محل | rollback |
|---|---|---|
| worktree + branch | `F:\octopus-blocker-wt`, `blocker-fixes-2026-07-22` | `git -C F:\backup worktree remove F:\octopus-blocker-wt` سپس `git -C F:\backup branch -D blocker-fixes-2026-07-22` |
| commits `8b61aa0`, `88d07f2` | فقط روی branch بالا | با حذف branch از بین می‌روند؛ master دست‌نخورده |
| safety backup | `F:\octopus-untracked-safety-2026-07-22` | فقط پاک‌کردنِ پوشه (کپیِ افزوده، چیزی را جابه‌جا نکرد) |
| Phase-0 reports | `F:\octopus-blocker-wt\OCTOPUS-PRIME\phase-0\` | داخل branch؛ با حذف branch می‌روند |

## آنچه تغییر **نکرد** (تأییدشده)

- `master @ 05d2b5a` — بدون تغییر.
- `_ops/OCTOPUS-flags.cmd` (arming) — دست‌نخورده.
- live state (`_ops/state`, `events.jsonl`, `ledger.jsonl`, `chrono.db`) — mtime یکسان قبل/بعد.
- هیچ STOP/HALT flag ست/پاک نشد. هیچ process restart نشد. هیچ effect بیرونی نزد.

## قبل از merge نهایی (owner)

۱. `SAFETY-BACKUP-MANIFEST` را دوباره تأیید کن.
۲. full sandbox suite را سبز کن (بخش F — هنوز OPEN).
۳. یک restore drill دیگر بعد از migration (وقتی C آماده شد).
۴. merge با `git merge --no-ff blocker-fixes-2026-07-22` تا نقطهٔ برگشتِ صریح داشته باشی.
