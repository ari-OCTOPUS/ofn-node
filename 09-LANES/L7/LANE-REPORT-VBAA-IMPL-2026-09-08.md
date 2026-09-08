# LANE-REPORT — L7 VBAA IMPL (do not clobber LANE-REPORT.md)

GOV_VERSION=V8 · LADDER=L2 · VERIFIED_CASH=0
LANE_ID=L7 · MODE=PROPOSE_ONLY for live services · board=180
may_authorize=false · external_api=DISABLED

Prompt 2: three Class A/A2 implementations. No live service change. No push.

## What was done

`_ops/vbaa/` is unowned in `09-LANES/LANE-MATRIX.csv` (no other lane lists it). Tests already put `_ops` on `sys.path` and import `vbaa.*`, so the package was placed there. Not `src/`.

Three local branches, stacked:

| Order | Branch | SHA | What |
|---|---|---|---|
| 1 | `l7/vbaa-artifact-admission` | `2d825db` | package + ArtifactAdmission + RED fixtures/tests |
| 2 | `l7/vbaa-argument-provenance-guard` | `f7707f3` | ArgumentProvenanceGuard |
| 3 | `l7/vbaa-executor-handle-firewall` | `16fae16` | ExecutorHandleFirewall AST |

PRs: **local only**. No `git push`, no `gh pr create` (vault egress deny). Bodies: `09-LANES/L7/PR-BODY-VBAA-*.md`. Push is `status: open, requires: owner_decision`.

## Tests (this session)

Command: `python -m pytest tests/contract/vbaa/test_artifact_admission.py tests/contract/vbaa/test_argument_provenance_guard.py tests/contract/vbaa/test_executor_handle_firewall.py -q --noconftest --tb=short`

Result: **23 passed, 1 xfailed, 2 xpassed** (0.48s).

- ArtifactAdmission: 10 passed, 1 xfailed (`INV-CRYPTO`)
- ArgumentProvenanceGuard: 6 passed, 1 xpassed (`INV-DERIVED`; fail-closed `UNTRUSTED`)
- ExecutorHandleFirewall: 7 passed, 1 xpassed (`INV-SUBSTRING`; component-equality, `executory` not a hit)

Xfail markers were not deleted.

## What remains

- Owner push/PR of the three branches
- C1/C2 from `07-HANDOFF/VBAA-RED-OPEN-2026-09-08.md` still open (15-name list; lowest-risk trio vs registry)
- INV-CRYPTO still xfail (presence-only signature)

## What failed

- Remote PRs not opened (egress blocked by policy). Not a test failure.

## Evidence paths

| Claim | Value | Source | Grade |
|---|---|---|---|
| combined pytest | 23 passed, 1 xfailed, 2 xpassed, 0.48s | this-session pytest command above | E2 |
| admission SHA | 2d825db | `git log -1 --oneline` on `l7/vbaa-artifact-admission` | E2 |
| provenance SHA | f7707f3 | `git log -1 --oneline` on `l7/vbaa-argument-provenance-guard` | E2 |
| `_ops/vbaa/` lane | unowned | `09-LANES/LANE-MATRIX.csv` (no `_ops/vbaa` row) | E2 |

## Rollback

Per branch, delete the branch or revert that SHA. Do not `rm -rf`.

```
git checkout rescue/octopus-live-tree-20260821
git branch -D l7/vbaa-executor-handle-firewall
git branch -D l7/vbaa-argument-provenance-guard
git branch -D l7/vbaa-artifact-admission
```

Single-commit revert: `git revert 2d825db` / `f7707f3` / firewall SHA.

## Public API shipped

`_ops/vbaa/` as package `vbaa`:

1. `vbaa.artifact_admission.ArtifactAdmission(allowed_types, path_root).admit(artifact)`
2. `vbaa.argument_provenance_guard.ArgumentProvenanceGuard().check(arguments, provenance)`
3. `vbaa.executor_handle_firewall.ExecutorHandleFirewall().scan_python_tree(root, host_id="180")`
