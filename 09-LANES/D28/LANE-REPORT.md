# LANE-REPORT — D28 (session 2026-09-02T15:52Z)

Lane declared: D28. Not in origin/main `09-LANES/LANE-MATRIX.csv` (L0–L9).
File-lock: `tests/test_cockpit_v2_frontend.py` (Windows `node --check` timeout
is UNKNOWN, not syntax). Incidents append on existing #73 only.

## What was done

- Diagnosed PR #67 Windows CI job 100316226517: `test_all_javascript_has_valid_syntax`
  raised `subprocess.TimeoutExpired` after 10s on `web/cockpit-v2/src/api.js`
  and `web/cockpit-v2/src/app.js`.
- Local `node --check` on both files: exit 0 at 2026-09-02T15:51:55Z. Timeout
  is UNKNOWN, not a syntax verdict. D-28 did not change those JS files
  (`git diff origin/main...HEAD` empty on them).
- Concurrent body landed `f1e6ec2cc91a0867dce1d561b13d1d39ec9f0f66`
  (`stdin=DEVNULL` + one retry, 30s). This body rebased onto that tip
  (no force-push) and layered E3: Windows budget 60s, timeout returned as
  UNKNOWN after retry, warmup, `shutil.which`. Nonzero `node --check`
  still fails closed.
- E3 locks: Windows budget > 10s; timeout retried then returned as UNKNOWN;
  syntax error still returncode 1; success does not retry.
- Updated existing #67. No duplicate D-28 PR. Did not touch `ofn/config.py`,
  flags, gates, CODEOWNERS, or send path.

## What remains

- Windows full-suite on the new HEAD is UNKNOWN until CI reruns. Do not claim
  green from this host.
- Merge still needs all required checks and independent CODEOWNERS review.
  Do not merge from this body.
- Complementary P1 modules remain review-blocked. Not touched.

## What failed

- `python3 -m pytest` is absent on this host (`ModuleNotFoundError`). Used
  stdlib unittest. status: verified_absent.

## Evidence

- Command: `python3 -m unittest tests.test_cockpit_v2_frontend tests.test_d28_edge -v`
- Timestamp: 2026-09-02T15:52:43Z
- Parent SHA: `e9cf84b84453d08578064b402f3044eb287f7d11`
- Exit: 0 · 38 passed / 0 failed / 0 skipped
- Receipt: `docs/octopus-surgery/architecture/2026-09-02/receipts/D28-WIN-NODE-CHECK-20260902.json`
- D-27 pointer SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH
- D-28 pointer SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH
- Filesystem immutability: NOT claimed

## Rollback

- `git revert` the commit that lands this helper on `cursor/d28-edge-runbook-ea6b`.
- Leaves prior D-28 policy commits intact.

## External effects

ZERO. Collection-only. Ready ≠ authorized. No send re-arm. No admin bypass.
Worktrees not pruned.
