# OP-0 EXECUTION RECEIPT — sparse-checkout permanently disabled (2026-09-09)

GOV_VERSION=V8 · LADDER=L2 · authority: judge ruling «A با سه شرط اجباری» · lane: GAP-VERIFY-RUN-20260908

## Pre-state (snapshot)

- git 2.51.0.windows.1 (≥2.36 ✓ auto-bit-clear semantics)
- F: free 81GB · no index.lock · organism alive (beat 67202, 5.7min fresh)
- skip-worktree bits: **40,504 / 51,190**
- `.git/config.worktree`: core.sparseCheckout=true, sparseCheckoutCone=false
- `.git/info/sparse-checkout`: non-cone `/*` + `!/*/`, sha256 `6c392891…`, mtime 2026-09-05 18:59

## Execution (judge's three conditions, in order)

1. **`git sparse-checkout disable`** → rc=0. Pattern archived BEFORE deletion to
   `09-LANES/GAP-VERIFY-RUN-20260908/sparse-checkout-archived-20260905.bak` +
   `99-ARCHIVE/archive_sparse-checkout-pattern-20260909.txt`, then `.git/info/sparse-checkout` DELETED (condition 1: disable alone leaves the pattern armed for a future `init`).
2. **config.worktree zeroed explicitly**: `core.sparseCheckout=false`, `core.sparseCheckoutCone=false` (condition 1b).
3. **S-bit census (condition 2): `git ls-files -t | grep -c ^S` = 0** — disable+2.51 cleared all 40,504 bits.
4. **True-missing census**: `git ls-files -z` vs disk → **0 of 51,207 tracked files missing** (earlier "4,773 missing" was a quoting artifact — ls-files quotes non-ASCII names; `-z` is the only honest census).
5. git status dirty-set stable (993 vs 961 pre-op — no mass deletions, no clobbering; disable rc=0 means no untracked-overwrite conflicts).
6. Organism alive throughout (beat 67219 mid-op).

## Condition 3 (order) & the no-checkout rule

- A executed BEFORE OP-1b (canonical folder not yet landed — order preserved).
- The «no more checkouts» rule is **LIFTED** (condition 2 complete = zero armed bits). Checkouts are now ordinary-safe in this repo.

## Judge's prediction tested — NOT confirmed

Full-tree search after materialization: canonical toolchain (gap_sources.yaml 41KB /
gap_ledger.py 12KB / test_gap_ledger.py / business-legs-wiring/) is **not in this repo's
tracked tree and not on disk** — it never lived here (the sparse bug ate ~4.5k OTHER
files, all restored). Canonical delivery by judge/owner remains the sole OP-1b input;
after landing: diff two sources → `--verify-chain` both → switch to canonical →
fold verify results via yaml + update `test_verify_status_starts_unvalidated` together.

## Rollback

`git config --worktree core.sparseCheckout true && git config --worktree core.sparseCheckoutCone false && cp 99-ARCHIVE/archive_sparse-checkout-pattern-20260909.txt .git/info/sparse-checkout && git sparse-checkout reapply` — NOT recommended (re-arms the trap).
