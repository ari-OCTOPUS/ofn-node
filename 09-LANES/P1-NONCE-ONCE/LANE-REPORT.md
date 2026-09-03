# LANE-REPORT — P1-NONCE-ONCE (session lxxix, 2026-09-03)

Declared file-lock zone: `/tmp/ofn-p1-nonce-once` on `feat/p1-nonce-once-20260903`.
`/workspace` stayed on `cursor/taskenvelope-system-hardening-18f4` @`a981086302c2b562bd02c55402ccc619afe4ef1e` (same SHA as `origin/main` #172) and was not written.

Lane ID: P1-NONCE-ONCE. Not in `09-LANES/LANE-MATRIX.csv` (L0–L9). Complementary kernel nonce/once admission. Did not edit LANE-MATRIX.csv.

## What was done
- First-read: `docs/octopus-os/MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` absent on `origin/main` @`a981086302c2b562bd02c55402ccc619afe4ef1e` — UNKNOWN, not FALSE.
- D-27 pointer SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH vs prior memory. D-28 pointer SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH. Evidence level B. Filesystem immutability UNKNOWN. Not claimed immutable.
- Trigger: cron `17 * * * *` @2026-09-03T22:27:04.935Z. Body `bc-b68360e1-82b8-4dbe-837a-696ad185e1c3`. Owner-absent. REVIEW_REQUIRED still blocks merge of already-open PRs (issue #51, GOV-V6). Not an engineering defect. Did not merge. Did not weaken the independence gate.
- Added kernel-pure `admit_nonce` + `NonceDecision` and `pin_once` + `OnceDecision` / `OnceIndex`. Admit is a START (HALT refuses). replay_check continues under HALT. First consume of `(nonce, run_id)` admitted. Second consume `already_consumed`. Same nonce on another run `nonce_collision`. peek never writes. Timeout is UNKNOWN, not a concurrent-write proof. Ready ≠ authorized. Distinct from `event_id` (`evt-`), `dedup` (`kind, ref`), and `idempotency` (envelope hash). Not wired into `run_store.py`. HALT stops STARTS, not in-flight consume.

## What remains
- Independent CODEOWNERS review of this PR then leftover review-blocked PRs. Merge blocked (REVIEW_REQUIRED).
- `quote_sent` / `send_authorized` remain owner-blocked. No newer scoped authorization after the later disarm/hold.
- Wiring these classifiers into `run_store.py` waits for owner review (do not edit that file here).
- Incidents append is on existing `docs/octopus-os-incidents-20260902` only (do not mint a fifth incidents PR). Unpublished lxx–lxxviii remain first identifiers. Next published append is lxxix on lxxiii `74d548f`.

## What failed
- `python3 -m pytest` is absent on this image (`ModuleNotFoundError`). Canonical run used stdlib unittest. Exit 0.
- `gh pr list` denied by `.cursor/hooks/deny_egress.py`. Open PRs measured via local `origin/*` refs from this-run fetch only.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| P1 suite | 267 passed / 0 failed / 0 skipped / exit 0 @ 2026-09-03T22:33:50Z / parent `a981086302c2b562bd02c55402ccc619afe4ef1e` | docs/octopus-surgery/architecture/2026-09-02/receipts/P1-NONCE-ONCE-20260903.json | E3 | verified |
| nonce_class methods | 43 passed | tests/test_nonce_class.py recount 2026-09-03T22:33:49Z | E3 | verified |
| once_pin methods | 33 passed | tests/test_once_pin.py recount 2026-09-03T22:33:49Z | E3 | verified |
| chaos nonce-once | 12 passed | tests/test_chaos_nonce_once.py recount 2026-09-03T22:33:49Z | E3 | verified |
| D-27 blob | sha256 c55f9085… / 5469 bytes | this-host file on origin/main | E2 | verified |
| D-28 blob | sha256 c79f0e74… / 16212 bytes | this-host file on origin/main | E2 | verified |
| MASTER-BLUEPRINT / CONTRIBUTING on main | absent | origin/main @a981086 | E0 | UNKNOWN, not FALSE |
| Filesystem immutability | not claimed | — | E0 | UNKNOWN |

## Rollback steps
1. Revert the commit that adds `ofn/kernel/nonce_class.py`, `ofn/kernel/once_pin.py`, and the three test modules on `feat/p1-nonce-once-20260903`.
2. Do not delete archives or prune worktrees.
3. Do not touch `/workspace` trigger checkout or weaken gates.
