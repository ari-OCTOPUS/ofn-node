# LANE-REPORT — P1-CAPABILITY-TOKEN (session 2026-09-04T00:04Z)

Lane declared: P1-CAPABILITY-TOKEN / 110B park. `09-LANES/LANE-MATRIX.csv`
has L0–L9 only (no P1 row). Executable work is the existing #113
capability_token PR — park the live send path so 110A's merged pin
is green without a second 110B identifier.

## What was done

- Trigger: GitHub CI check-suite failure on
  `feat/110b-capability-token-20260903`
  @`404fa4a33d06cd06e35444bada65dc97abaa24c5` (PR #113).
  Failed checks: `test (ubuntu-latest)` job 100859640481,
  `test (windows-latest)` job 100859640773. Independently reproduced
  locally: `python3 -m pytest tests/test_r0_quote_closure.py`
  · `2026-09-04T00:02:42Z` · HEAD `404fa4a` · exit 1 ·
  **1 failed / 5 passed** —
  `test_send_path_modules_are_absent_from_this_pr`
  (`capability_token.py` exists and imported a live outbound adapter).
- `/workspace` stayed on
  `cursor/bc-bd6d8f40-98ec-4982-9825-d2bd61a72db2-585e` @`404fa4a`
  and was not written.
- Isolated worktree `/tmp/ofn-110b-park` on the same PR branch
  `feat/110b-capability-token-20260903` from origin #113 @`404fa4a`.
- Park: `verified_send` never imports an outbound adapter; good
  verify returns `TOKEN_PARKED` / `sent=False`; `grants_send` and
  `ready_is_authorized` structurally False. 110A pin updated: parked
  token file allowed; live transport name still fails. E3 +
  owner-absent chaos tests added.
- Prior unpublished park SHAs (memory `f7f81be` / `badb8b4` / …)
  are ABSENT on this host — recorded, not rewritten. Did not mint
  a second 110B PR. Did not force-push.

## What remains

- Publish this worktree onto #113 (same branch). CI re-run on the
  parked SHA. Merge still REVIEW_REQUIRED (do not merge; no admin
  bypass).
- Independent review of #113 after CI. Do not re-arm send.

## What failed

- #113 full-suite red on `404fa4a` (engineering defect: 110A pin vs
  live transport import). Locally fixed; remote still `404fa4a`
  until publish.
- `gh` CLI egress-blocked this-run. Job logs not re-fetched; cause
  independently reproduced from the 110A pin on this SHA.

## Evidence

- Command: `python3 -m pytest tests/test_r0_quote_closure.py tests/test_capability_token.py tests/test_chaos_capability_token.py tests/test_d26_canonical_bodies.py tests/test_r0_spine_restore.py tests/test_kernel_purity.py tests/test_envelope.py tests/test_run_store.py tests/test_token_ceiling.py tests/test_run_gate.py tests/test_chaos_owner_absent.py tests/test_tmpdir.py -q --tb=line`
- Timestamp: 2026-09-04T00:04:27Z
- Parent SHA: `404fa4a33d06cd06e35444bada65dc97abaa24c5`
- Exit: 0 · 223 passed / 2274 subtests / 0 failed / 0 skipped
- Receipt: `docs/octopus-surgery/architecture/2026-09-03/receipts/P1-CAPABILITY-TOKEN-PARK-20260904.json`
- D-27 SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH
- D-28 SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH
- Filesystem immutability: NOT claimed

## Rollback

- `git revert` the park commit on
  `feat/110b-capability-token-20260903`. Leaves `origin/main`
  untouched. Does not restore the live transport import (that was
  the defect).

## External effects

ZERO. Ready ≠ authorized. No send re-arm. No admin bypass.
Worktrees not pruned.
