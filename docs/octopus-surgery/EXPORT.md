# Public export note

This branch is a **sanitised portable extract** onto `github/main`
(`c1969bce5384f3371b916470299c991627c3d63c`). It is not a push of the
private vault lineage.

## What was transferred

- Replay-safe `observation.v1` contract: `octopus_observation/`
- Foundation tests: `tests/test_observation_v1_foundation.py` (15 checks)
- Campaign notes 00–14 and JSON receipts, with local filesystem paths redacted

## What was not transferred

- Vault Git history and Obsidian working tree
- `_ops/` runner, cognition deny-list, lab gateway, cortex harness
- `run_all.py` and the 827-test hermetic suite
- Runtime logs (`*.log` are ignored on this repository)
- Secrets, `OWNER_KEY`, D1/D7 actions, merge, or deploy

## Provenance

| Fact | Value |
|---|---|
| Evidence lineage | `surgery/cognition-authority-denylist-20260830-170620` |
| Evidence commit | `470bb6031f1e51c9a8e6e1f1536c349e22a5200e` |
| Docs worktree commit | `45c9f20bb02299db4269964abe1bc08eec7b89c1` |
| Docs branch | `docs/octopus-campaign-sync-20260830` |
| Canonical vault | `NOT_SYNCED` |
| Surgery 4 observatory | `NOT_FOUND_IN_CURRENT_LINEAGE` — not rebuilt |
| OWNER-09 | 770/827 hermetic passed on the vault lineage; `HERMETIC_BOUNDARY_VIOLATION` |
| This repository | does not contain `_ops`; OWNER-09 was not re-run here |

## Retest on this GitHub lineage

Command: `python -X utf8 -m pytest -q` in the export worktree, no `--live`.

- Portable observation.v1: 15/15 passed
- Full ofn-node suite on this Windows host: 2083 passed, 72 failed, 10 skipped
- The 72 failures are pre-existing POSIX/media/clock tests on Windows; none are `test_observation_v1_foundation`
- This is not a re-run of vault OWNER-09 (`run_all.py` is not in this repository)

Do not treat this PR as proof that the vault surgeries exist on ofn-node.
Only the portable observation contract was made to run on this lineage.
