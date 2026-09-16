# Branch-topology surgery + sparse incident receipt — 2026-09-08 (owner «yes i want»)

GOV_VERSION=V8 · LADDER=L2 · lane: GAP-VERIFY-RUN-20260908 · no history rewritten

## What was done

1. **rescue fast-forwarded** `ba1e7be → ab54c89` (`git branch -f`, ref move only) so the trunk carries all 12 commits that had accumulated on `l7/vbaa-executor-handle-firewall` (3 VBAA + 9 parallel/session commits incl. backup-GREEN, FX pin, offer-card, H9 accrual, PROMPT-NEXT, H9-TESTBATTERY battery).
2. **HEAD switched** l7→rescue (same SHA ab54c89, working tree expected unchanged).
3. **`l7/vbaa-executor-handle-firewall` reset to `16fae16`** — restoring its clean meaning (VBAA-only review stack). `l7/vbaa-artifact-admission` (2d825db) and `l7/vbaa-argument-provenance-guard` (f7707f3) untouched.

## Incident: sparse-checkout de-materialization (recovered)

The same-SHA checkout triggered the repo's non-cone sparse rules (`/*` + `!/*/`, ~50k tracked files de-materialized as long-standing normal state in this clone) and REMOVED three clean tracked dirs from the working tree:
- 09-LANES/QD-BRIDGE-REALTESTS-20260908 (10 files)
- 09-LANES/GAP-VERIFY-RUN-20260908 (7 files)
- 09-LANES/H9-TESTBATTERY-20260909 (11 files — the parallel battery agent's lane; dir removal implies no uncommitted content existed there)

**Recovery:** all 28 files restored from the rescue tree via `git show`; byte-for-byte integrity verified (sha256 disk == blob, ALL MATCH). No data loss.

**Standing lesson (added to memory):** in this clone, ANY `git checkout` (even same-SHA) can de-materialize sparse-excluded clean tracked files — after any branch switch, scan tracked-vs-disk for the day's paths and restore from tree before continuing.

## End state (verified)

- HEAD = `rescue/octopus-live-tree-20260821` @ ab54c89
- `16fae16..rescue` = 10 commits (non-VBAA work on trunk)
- l7 stack = 2d825db → f7707f3 → 16fae16 (clean VBAA review lineage, mirrored to ari-OCTOPUS/vbaa-patches PRs #1/#2/#3)
- VBAA files are in the rescue tree (de facto lineage since 8+ commits built on them); review still happens on the PR repo
- locked log files (`_ops/state/telegram/*.log`) survived (unlink failed on locked handles — benign)

## Rollback

`git branch -f rescue/octopus-live-tree-20260821 ba1e7be && git branch -f l7/vbaa-executor-handle-firewall ab54c89` (pure ref moves).
