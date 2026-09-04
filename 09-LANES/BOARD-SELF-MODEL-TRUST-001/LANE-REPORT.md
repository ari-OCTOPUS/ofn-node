# BOARD-SELF-MODEL-TRUST-001

## What was done

Under the direct BOARD-CODE-001 grant, created a sparse, separate worktree on node 138 at /home/ari/ofn-worktrees/codex-self-model-input-trust-001, branch codex/self-model-input-trust-001, based on e00c8ed5be7ec6609c600bb7a5bc3b99ace3c3e9 (WORKTREE-RECEIPT.json in the local execution evidence directory). The main /home/ari/ofn checkout and its untracked files were not edited. PLAN.md was hash-pinned before tests.

Patched the existing ofn/kernel/self_model.py, already consumed by ofn/adapters/self_model_producer.py: reject malformed/nonfinite freshness windows and overflowing time arithmetic as unknown; require actual booleans for measured process/capability states; include missing/invalid brain-probe verdicts as unknown in the aggregate. Preserved raw probe details, schema, legitimate zero, measured absence, existing future tolerance and all operational gates. Added tests/test_self_model_input_trust.py; did not import a second organism runtime.

On this board, the original baseline passed 31 tests. The 9 new contract tests exposed 23 failing subtests and 8 errors on the preimage; these are malformed API arguments, not measured events (PREIMAGE-TESTS.json). The candidate passed 40 tests including the original self-model and kernel-purity suites (CANDIDATE-TESTS.json). Independent read-only review confirmed the exact candidate/test hashes and corrected a masked negative-control test before the board run (REVIEW.json). This demonstrates the narrow contract fix, not health or predictive improvement; no persistence/prior/random baseline was evaluated or beaten.

## What remains

CANON-001 still requires the explicit owner source designation. Promoting this branch into main, adapting the larger local EXEC-001 package to real consumers, and activation are not done. The observed ofn.service WorkingDirectory is /home/ari/ofn; its loaded module bytes/commit remain unverified. No other board was changed. Existing runtime/business loops and later owner rulings were not replaced with older documents.

## What failed

The first sparse-worktree setup left an empty index after --no-checkout. Read-only inspection confirmed only .git existed, then declared sparse paths were materialized using read-tree -mu HEAD. An SSH disconnect occurred before test upload; a separate read-only check confirmed no test file or receipt existed before sending through stdin. The first complete test output exceeded the local tool display budget; the exact board receipt was retained and a hash-linked summary retrieved without rerunning. Existing kernel-purity tests emitted ResourceWarning messages from unclosed read handles; both baseline and candidate still exited successfully. No tests were skipped or relaxed. Negative preimage failures are intentionally retained.

The root instructions reference docs/DISCOVERY.md and tools/reconcile.py, but both were absent in the inspected checkout. No reconciliation/whole-organism health claim was made.

## Evidence paths

- Board: this lane's PLAN.md, PREIMAGE-TESTS.json, CANDIDATE-TESTS.json, REVIEW.json and this report; the exact modified code and test in the owned worktree.
- Laptop: F:\octo-exec\EXEC-001\board-code\BOARD-SELF-MODEL-TRUST-001 holds original source, candidate source, test, report, worktree receipt and summaries linked to full board receipts by SHA-256.
- Service/repository observation: F:\octo-exec\EXEC-001\receipts\live\OBSERVATION-138.json and its immutable raw receipts. WorkingDirectory equality is not loaded-code proof or an owner source decision.

## Rollback steps

No service rollback is needed: main, deployment configuration, state and services were not changed. To reverse the isolated source patch later, first compare the current file to candidate SHA-256 c6a60a6c75ab48181d13d97fb0864408f8e7ddf792ddff8d231abf3fda06cb50, then restore only ofn/kernel/self_model.py from the recorded base/preimage SHA-256 67b24517f536d80459e4480fea16d65076c8756c3f8e1c387adf6b443b6eb0e8. Preserve subsequent work and receipts; do not reset main, delete the worktree, or run recursive cleanup. New test/report files can remain as provenance; retirement is a separate scoped action.
