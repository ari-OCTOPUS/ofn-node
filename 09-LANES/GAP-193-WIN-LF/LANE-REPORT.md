# LANE-REPORT — GAP-193-WIN-LF (session 2026-09-04T16:03Z)

Declared file-lock zone: `/tmp/ofn-193-win-lf` on local `feat/gap-193-win-lf-followup` (push target `rescue/main-board-integ-20260904`).
`/workspace` stayed on `cursor/taskenvelope-system-hardening-c359` @`8819e42efb5e8fb815d979b500105f15c34cab8b` (#193 SHA) and was not written.

Lane ID: GAP-193-WIN-LF. Not in `09-LANES/LANE-MATRIX.csv` (L0–L9). Existing PR #193 owns the organism-shadow freeze on this SHA. This session only pins checkout identity. Did not edit LANE-MATRIX.csv. Did not open a second #193. Did not rewrite `registry.py` / `metacontrol.py`. Did not rewrite #194.

## What was done
- First-read: `docs/octopus-os/MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` absent on this body and `origin/main` @`7510c991a07088cc0a0c2097370eb0ba5d976e3a` — UNKNOWN, not FALSE.
- D-27 pointer SHA-256 `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` (5469 bytes) MATCH vs prior memory. D-28 pointer SHA-256 `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` (16212 bytes) MATCH. Evidence level B. Filesystem immutability UNKNOWN. Not claimed immutable.
- Trigger: CI `test (windows-latest)` job `101086693364` on #193 @`8819e42efb5e8fb815d979b500105f15c34cab8b`. Independently confirmed: `test_captured_source_identity_and_frozen_files` compared freeze `e3ef142d…` to working-tree hash `cfa730c9…`. Reproduced on this host: LF bytes MATCH freeze; LF→CRLF bytes MATCH the Windows hash. Checkout artefact, not a contract edit.
- `require-independent-approval` also failed on the same suite (author cursor[bot] / ari322, approvals none — trigger-reported). Gate working as designed (issue #51, GOV-V6). Did not weaken CODEOWNERS / branch protection / required-approvals. No admin bypass.
- Added `shadow_homeostasis/.gitattributes` (`*.py` `eol=lf`) and root `.gitattributes` (`registry.py` / `metacontrol.py` `-text`). Freeze test now hashes LF-canonical bytes (second witness; pattern `tests/test_brain_schema.py`). E3: CRLF is the known CI hash and not the freeze; a content edit still breaks the freeze; lone CR normalizes; both attributes pins are present. Frozen sources were not rewritten.
- Collision recorded open: #194 already carries the same pin (`06a2854` + `80d98ff` on `refs/pull/194/head` `1c3e7c03…`). Did not rewrite #194. Did not open a second #194.

## What remains
- Independent CODEOWNERS review of #193 after Windows CI on the follow-up SHA. Merge blocked (REVIEW_REQUIRED) even if CI greens.
- `quote_sent` / `send_authorized` remain owner-blocked. No newer scoped authorization after the later disarm/hold.
- Incidents append is on existing `docs/octopus-os-incidents-20260902` only (do not mint a sixth incidents PR).

## What failed
- Windows CI on parent `8819e42efb5e8fb815d979b500105f15c34cab8b` — 1 failed / 4529 passed / 28 skipped / 3450 subtests · `2026-09-04T15:58:56Z` · job `101086693364`. Cause: CRLF checkout. This commit is the fix.
- `require-independent-approval` — REVIEW_REQUIRED, not an engineering defect.
- `pytest` module absent on this host (`ModuleNotFoundError`). Suite via stdlib unittest.
- First related-suite attempt included `tests.test_campaign_envelope` — `ModuleNotFoundError` (module absent on this SHA). Not treated as a product failure. Reran without that name.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| organism_shadow | 24 passed / 0 failed / exit 0 @ 2026-09-04T16:03:31Z / parent `8819e42efb5e8fb815d979b500105f15c34cab8b` | docs/octopus-surgery/architecture/2026-09-04/receipts/GAP-193-WIN-LF-20260904.json SHA-256 `d9eef65bd4622c4fc6990b7c3b8ed53f6ce587a092963be44814c58995a50f14` (5823 bytes) | E3 | verified |
| related unittest | 267 passed / 0 failed / 0 skipped / exit 0 @ 2026-09-04T16:03:43Z | same receipt | E2 | verified |
| Windows CI parent | 1 failed / 4529 passed / 28 skipped @ 2026-09-04T15:58:56Z | gh run view --job 101086693364 --log-failed | E3 | verified |
| LF registry | e3ef142d2254c0e430b98c39f244dfb14e7e4ecd33ef58b8ad3d348daefa767b | this-host sha256 | E3 | verified |
| CRLF registry | cfa730c9d9cda268f89b69c7b11ef8a1dec8f5d9d390a0db36f1d098d2e96ae4 | CI log + this-host LF→CRLF | E3 | verified |
| D-27 blob | sha256 c55f9085… / 5469 bytes | this-host file | E2 | verified |
| D-28 blob | sha256 c79f0e74… / 16212 bytes | this-host file | E2 | verified |
| MASTER-BLUEPRINT / CONTRIBUTING | absent | origin/main @7510c99 | E0 | UNKNOWN, not FALSE |
| Filesystem immutability | not claimed | — | E0 | UNKNOWN |

## Rollback steps
1. Revert the follow-up commit on `rescue/main-board-integ-20260904` that adds `shadow_homeostasis/.gitattributes`, root `.gitattributes`, the freeze-test witnesses, the receipt, and this report. Do not rewrite `registry.py` or `metacontrol.py`.
2. Do not delete archives or prune worktrees.
3. Do not touch envelope / events / run_store / campaign_envelope / CODEOWNERS or weaken gates.
