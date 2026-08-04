# 11 — Flag rollback plan

`OCTOPUS-flags.cmd` is **not tracked in git** (confirmed: `git ls-files | grep -i
"OCTOPUS-flags"` returns nothing in this repo). This run did not modify it, so there is
nothing to roll back from this session. Documented here in case a future session needs it.

## If a future edit to this file needs reverting

Since git cannot help (untracked), the file's own directory already carries manual restore
points on disk (`F:\backup\_ops\`):
- `OCTOPUS-flags.cmd.bak-2026-07-25`
- `OCTOPUS-flags.cmd.bak-2026-07-25-thesis`
- `OCTOPUS-flags.cmd.bak-20260801-043932`
- `OCTOPUS-flags.cmd.bak-20260801-090623`
- `OCTOPUS-flags.cmd.bak-arm-20260801-152217`
- `OCTOPUS-flags.cmd.broken-20260801-092004` (named "broken" — do not restore from this one
  without checking why it was marked broken first)

None of the above were used or touched in this session. Restoring any of them would also
revert the 7 owner-approved flags added 2026-08-04 — a future agent should copy just the
specific `set` lines it needs to change, not wholesale-restore an old backup, to avoid
silently un-arming today's owner decisions.
