---
type: log
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, surgery, changelog, evidence]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
sources:
  - "[[CHECKPOINT]]"
  - "[[DECISIONS]]"
---

# Surgery evidence changelog

## 2026-08-30 — Surgery 1

- Added capability-aware cognition authority policy and AST guard.
- Recorded outcome `TEST_ONLY_GUARD`; production behavior changes remain `0`.
- Classified cortex → provider as `SAFE_INFERENCE_BOUNDARY`.
- Classified `code_brain → code_autonomy` as `APPROVED_EXECUTOR_BOUNDARY`.
- Preserved provider model-network and provider-credential capability.
- Corrected “27 independent verifiers” to “27 checks from one verifier”.
- Kept OFN `secret_rotation` distinct from rotation-vault mechanisms.
- Preserved completion estimates: Code 56% ± 7%, Evidence 41% ± 8%,
  Operational 29% ± 9%, Overall 39% ± 7%.
- Copied the committed evidence bundle byte-for-byte into the canonical Obsidian
  vault and added navigation notes without rewriting the valid manifest or receipt.
- Pushes, merges, deployments, restarts, provider calls and external effects: `0`.

## 2026-08-30 — Surgery 2

- Repaired the LLM caller inventory from 5/6 to 8/8.
- Classified the full-loop flash gateway as `ISOLATED_LAB_ONLY`.
- Added a deny-by-default gate before credential lookup, budget reservation or provider construction.
- Required explicit lab mode, non-production zone, approved lab entrypoint,
  `executable=false`, and `external_action=false`.
- Added deterministic production-deny and explicit-lab-allow tests.
- Provider calls, external effects, restarts and deployments remained `0`.
- GitHub publish was withheld: the local vault and `github/main` have no merge base.

## 2026-08-30 — Surgery 3

- Made the official runner deny external network by default.
- Moved child state, execution manifest and flaky diagnostics to per-run temporary storage.
- Removed provider/sender credentials from hermetic child environments without reading values.
- Preserved the live provider test behind `--live` plus a dedicated owner-authorization signal.
- Added a controlled external-network denial test and temporary-state write test.
- Fixed `test_cortex.py` module/package resolution explicitly; 6/16 became 16/16.
- Full default inventory is 826 suites; the long evaluation was not executed in this surgery.

## 2026-08-30 — Surgery 4

- Exhausted current branch, all refs, germline/GitHub refs, preservation artifacts,
  the documented Desktop path, known backups and exact runtime database names.
- Found no `run_observatory.py`, Bayesian implementation, live-store verifier,
  backtest executable or claim database in the current lineage.
- Recorded historical reports without promoting their Brier/sample claims.
- Classified the runtime body as `body_not_on_this_host`.
- Added a minimum replacement contract; copied zero historical code.

## 2026-08-30 — Surgery 5

- Added an immutable observation.v1 record contract beside the existing parser.
- Added fake and replay adapters; both are simulation/replay only.
- 15/15 foundation tests cover masquerade, uncertainty, immutability, stale, authority and provenance.
- No hardware, network, provider or production sensor was used.

## 2026-08-30 — Campaign closeout

- Added owner runbook, roadmap, merge/deploy checklist, 90% gates, inbox and final report.
- HISTORICAL_SNAPSHOT (campaign closeout, before selective export): GitHub publish of the local vault/surgery branch was blocked: public remote, no merge base.

## 2026-08-30 — OWNER-09 rerun and scoring repair

- Re-ran `python -X utf8 _ops/tests/run_all.py` without `--live` at `470bb60`.
- Result: 770/827 passed, 57 failed, 1 live skipped, 1459s, `HERMETIC_BOUNDARY_VIOLATION`.
- Restored 12 tracked residue paths after measurement.
- Repaired `test_run_all_scoring.py` so nested e2e does not inherit isolation-boot PYTHONPATH.
- Repair commit: `d6eeadd40d867bdc082dbc287c48e24be280a335` (14/14 via `run_all --only`).
- Did not rerun the 827-suite after that one-file repair.

## 2026-08-30 — Final PR 6 documentation reconciliation

- PR #5 closed superseded (not merged).
- PR #6 is the canonical selective export (`OPEN_AS_PR_6`).
- Four focused CI checks passed (`ci_last_observed_before_docs_commit: PASS`).
- Same-env differential regressions = 0.
- Obsidian docs branch and content synchronization remain
  `OBSIDIAN_CONTENT_SYNCED_GIT_BRANCH_SEPARATE`; primary rescue is `DIRTY_NOT_SYNCED`.
- Merge and deploy remain unauthorized.
- Local OWNER-09 remains `HERMETIC_BOUNDARY_VIOLATION`.
