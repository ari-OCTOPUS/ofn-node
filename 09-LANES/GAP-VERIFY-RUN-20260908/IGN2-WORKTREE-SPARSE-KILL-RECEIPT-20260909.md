# RECEIPT — last armed sparse killed (ign2 worktree) + chief-reconciliation — 2026-09-09

GOV_VERSION=V8 · LADDER=L2 · lane: GAP-VERIFY-RUN-20260908

## Chief-reconcile claims vs disk (verified this session)

| Claim | Verdict | Evidence |
|---|---|---|
| #240 squash-merged, commit 8192e78a… | **CONFIRMED** | `gh pr view 240`: state=MERGED, mergedAt=2026-09-09T07:37:09Z, mergeCommit.oid=8192e78a1ba34535339b0b173ea8b8cfcbf3f4be |
| CLOSEOUT sha f82d3687… | **MISMATCH-open** | file exists at 00-SEASON/PROMPT-RUNS-20260909/CLOSEOUT-20260909.md but current sha256=1ecf628c…, git-blob=74613ce1… — file evidently edited after their hash; both values recorded, resolution: null |
| «vault demat هنوز ACTIVE ~40k skip-worktree» | **STALE for main repo / TRUE-origin found elsewhere** | main F:\backup: config.worktree sparse=false/false, pattern file DELETED, S-bits **0** (killed 2026-09-08 night, commit 9f99178; re-verified now). The ~40k number was their OP-0 agent's PRE-disable receipt + it still matched `_worktrees/ign2-pathology-slice-guard`: sparseCheckout=true with **43,741 S-bits** — killed today (below). |

## Worktree kill (judge's 3 conditions applied to the last armed copy)

- Target: `F:\backup\_worktrees\ign2-pathology-slice-guard` (dormant guard lane worktree)
- 1) pattern archived → `99-ARCHIVE/archive_sparse-pattern-ign2-worktree-20260909.txt`, then `git sparse-checkout disable` rc=0, pattern file under `.git/worktrees/<name>/info/` DELETED
- 2) worktree config zeroed: core.sparseCheckout=false, sparseCheckoutCone=false
- 3) census: **S-bits 0**; disk cost ~11GB (74→63GB free on F:)
- Order note: canonical folder (OP-1b) still not landed — order preserved

## End state

**The entire F:\backup tree family (main + all worktrees) is now sparse-free.**
Full-tree assumptions on F:\backup are SAFE. The chief's HOLD on that basis can be lifted.

## Rollback

`git -C _worktrees/ign2-pathology-slice-guard config --worktree core.sparseCheckout true && cp 99-ARCHIVE/archive_sparse-pattern-ign2-worktree-20260909.txt .git/worktrees/ign2-pathology-slice-guard/info/sparse-checkout` — not recommended.
