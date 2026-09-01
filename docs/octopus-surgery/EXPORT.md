# Public export note

This branch is a sanitised portable extract onto `origin/main`
(`c1969bce5384f3371b916470299c991627c3d63c`). Local vault history was not published.

## Required publication statements

1. Changes were selectively reapplied from a separate local germline lineage.
2. Local vault history was not published.
3. All included code was retested against GitHub main.
4. Omitted local surgeries are listed below.
5. This PR does not authorize deployment.
6. This PR does not open D1, D7, OWNER_KEY or secret rotation.
7. No live provider call was performed.
8. No physical sensor was activated.
9. Opening the PR does not change production behavior.

## Exported

- `octopus_observation/` replay-safe observation.v1 contract
- `tests/test_observation_v1_foundation.py`
- Sanitised campaign notes 00–14 and JSON receipts

## Omitted (local-only)

- Cognition deny-list AST guard (`_ops` sources absent here)
- LLM inventory and lab gateway
- Hermetic `run_all.py` and cortex import fix
- Observatory recovery (still `NOT_FOUND_IN_CURRENT_LINEAGE`)
- Vault Git history and dirty primary working tree
- Runtime `.log` files

## Provenance

- Evidence lineage: `surgery/cognition-authority-denylist-20260830-170620`
- Local surgery final commit: `bf6f45ec28f71fd221ea7c751ec7e19687089164`
- Canonical vault: `NOT_SYNCED` at export time
- OWNER-09: 770/827 on the vault lineage; `HERMETIC_BOUNDARY_VIOLATION`
- Canonical PR: https://github.com/ari-OCTOPUS/ofn-node/pull/6
- Superseded PR: #5 `CLOSED_SUPERSEDED`
- Same-env differential (`python -X utf8 -m pytest -q`): base 3545/3638 passed, head 3560/3653 passed; 82 failed + 1 error on both; `PUBLIC_EXPORT_REGRESSIONS = 0`
- Historical unlabeled counts 72 and 2073/82 are not this measurement
- CI: focused `observation-contract` workflow; result recorded in the PR body after push
- Merge/deploy: `NOT_AUTHORIZED`
