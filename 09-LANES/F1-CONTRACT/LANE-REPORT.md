# LANE-REPORT — F1-CONTRACT (session 2026-09-03T13:00Z)

Declared file-lock zone: `/tmp/ofn-f1-contract` on `feat/f1-contract-20260903`.
`/workspace` stayed on `cursor/taskenvelope-system-hardening-1d5d` @`6b0353280b6aca63bcc7e64a6dd63b830470d630` (#162 SHA) and was not written.

Lane ID: F1-CONTRACT. Not in `09-LANES/LANE-MATRIX.csv` (L0–L9). Existing PR #162 owns `contracts/runtime_truth_v1.py`. This session only pins checkout identity. Did not edit LANE-MATRIX.csv. Did not open a second F1 PR.

## What was done
- First-read: `docs/octopus-os/MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` absent on this body and `origin/main` @`6f9298a85fd9dfc04670cb6b161732830ed421b6` — UNKNOWN, not FALSE.
- D-27 pointer SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH vs prior memory. D-28 pointer SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH. Evidence level B. Filesystem immutability UNKNOWN. Not claimed immutable.
- Trigger: CI `test (windows-latest)` job `100656285087` on #162 @`6b0353280b6aca63bcc7e64a6dd63b830470d630`. Independently confirmed: `test_frozen_lock_matches_contract` compared lock `0701aeff94ac92e993c9b9d52d4c9e75837a75c1f8b48a2528b4c9ec9d87ae02` to working-tree hash `bad38e2496e138d07dccee0135de1a6cf0098f6f1477d99dfce89e1901717b4b`. Reproduced on this host: LF bytes MATCH lock; LF→CRLF bytes MATCH the Windows hash. Checkout artefact, not a contract edit.
- Added `contracts/.gitattributes` (`*.py` / `*.lock` `eol=lf`). Freeze test now hashes LF-canonical bytes (second witness; pattern `tests/test_doctor_lane_contract_map.py`). E3: CRLF is the known CI hash and not the lock; a content edit still breaks the lock; lone CR normalizes; attributes pin is present. `FROZEN.lock` and `runtime_truth_v1.py` were not rewritten.

## What remains
- Independent CODEOWNERS review of #162 after Windows CI on the follow-up SHA. Merge blocked (REVIEW_REQUIRED) even if CI greens.
- `quote_sent` / `send_authorized` remain owner-blocked. No newer scoped authorization after the later disarm/hold.
- Incidents append is on existing `docs/octopus-os-incidents-20260902` only (do not mint a fifth incidents PR).
- `tools/runtime_truth.py` (#163 mention in `tests/test_no_llm_import_in_reflex.py`) was not opened here.

## What failed
- Windows CI on parent `6b0353280b6aca63bcc7e64a6dd63b830470d630` — 1 failed / 4399 passed / 26 skipped / 3410 subtests · `2026-09-03T12:56:27Z` · job `100656285087`. Cause: CRLF checkout. This commit is the fix.
- `gh pr view 162` denied by `.cursor/hooks/deny_egress.py`. Job log via `gh run view --job 100656285087 --log-failed` succeeded earlier in the same session.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| related suite | 43 passed / 2274 subtests / 0 failed / 0 skipped / exit 0 @ 2026-09-03T12:59:57Z / parent `6b0353280b6aca63bcc7e64a6dd63b830470d630` | docs/octopus-surgery/architecture/2026-09-02/receipts/F1-CONTRACT-WIN-LF-20260903.json | E3 | verified |
| freeze file | 12 passed @ 2026-09-03T13:00:04Z | same receipt | E3 | verified |
| Windows CI parent | 1 failed / 4399 passed / 26 skipped @ 2026-09-03T12:56:27Z | gh run view --job 100656285087 --log-failed | E3 | verified |
| LF digest | 0701aeff94ac92e993c9b9d52d4c9e75837a75c1f8b48a2528b4c9ec9d87ae02 | contracts/FROZEN.lock + this-host sha256 | E3 | verified |
| CRLF digest | bad38e2496e138d07dccee0135de1a6cf0098f6f1477d99dfce89e1901717b4b | CI log + this-host LF→CRLF | E3 | verified |
| D-27 blob | sha256 c55f9085… / 5469 bytes | this-host file | E2 | verified |
| D-28 blob | sha256 c79f0e74… / 16212 bytes | this-host file | E2 | verified |
| MASTER-BLUEPRINT / CONTRIBUTING | absent | origin/main @6f9298a | E0 | UNKNOWN, not FALSE |
| Filesystem immutability | not claimed | — | E0 | UNKNOWN |

## Rollback steps
1. Revert the follow-up commit on `feat/f1-contract-20260903` that adds `contracts/.gitattributes`, the freeze-test witnesses, the receipt, and this report. Do not rewrite `FROZEN.lock` or `runtime_truth_v1.py`.
2. Do not delete archives or prune worktrees.
3. Do not touch envelope / events / run_store / campaign_envelope / CODEOWNERS or weaken gates.
