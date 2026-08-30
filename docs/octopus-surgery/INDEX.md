---
type: moc
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, surgery, evidence, safety]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
sources:
  - "[[CHECKPOINT]]"
  - "[[DECISIONS]]"
documentation_lineage: rescue/octopus-live-tree-20260821
evidence_lineage: surgery/cognition-authority-denylist-20260830-170620
closeout_commit: b394b999b43ab12573ad574f33a5621a57c66686
evidence_commit: 470bb6031f1e51c9a8e6e1f1536c349e22a5200e
docs_branch: docs/octopus-campaign-sync-20260830
docs_base: 0f0e7f5345004284bd1355ff72b7b6ec68595dbd
deployed: false
merged_into_primary_vault: false
published_to_github: false
canonical_vault_status: NOT_SYNCED
---

# OCTOPUS surgery evidence index

Campaign files 00–08 were updated through five surgeries. Files 09–14 are
closeout-only.

- [[09-OWNER-ACTION-RUNBOOK]]
- [[10-POST-CAMPAIGN-ROADMAP]]
- [[11-MERGE-DEPLOY-CHECKLIST]]
- [[12-90-PERCENT-GATES.yaml]]
- [[13-OWNER-INBOX]]
- [[14-FINAL-CAMPAIGN-REPORT]]

This folder is committed on `docs/octopus-campaign-sync-20260830` in a clean
docs worktree based at `0f0e7f5345004284bd1355ff72b7b6ec68595dbd`.
The primary vault working tree on `rescue/octopus-live-tree-20260821` was not
used for this commit; unknown dirty vault files were not staged.
Status: `DOCS_WORKTREE_COMMITTED`. Canonical vault: `NOT_SYNCED`.

## Closure

- Outcome: `TEST_ONLY_GUARD`
- Production behavior changes: `0`
- Surgery commit: `57e1a2fecb770b62c459b67c10ff450fdcbe8632`
- `27/27` means 27 checks from one verifier, not 27 independent verifiers.
- Narrow cognition separation is verified only within the inspected policy scope.
- Cortex → provider: `SAFE_INFERENCE_BOUNDARY`.
- Provider adapters retain model-network and provider-credential capability.
- `code_brain → code_autonomy`: `APPROVED_EXECUTOR_BOUNDARY`.

## Navigation

- [[CHECKPOINT]]
- [[HANDOFF]]
- [[CHANGELOG]]
- [[DECISIONS]]
- [[00-CONCEPT-MAP|Concept Map]]
- [[01-DISTANCE-TO-90|Distance to 90%]]
- [[02-AGENT-CONTRACT|Agent Contract]]
- [[03-NEXT-SPRINT|Next Sprint]]
- [[04-SELF-MODEL-SPEC|Self-model Spec]]
- [[05-EVIDENCE-PROTOCOL|Evidence Protocol]]
- [[06-REALITY-MANIFEST.yaml|Reality Manifest]]
- [[07-TRACEABILITY-MATRIX.csv|Traceability Matrix]]
- [[08-RISK-REGISTER|Risk Register]]
- [[receipts/BASELINE-20260830T064824Z.json|Baseline receipt]]
- [[receipts/COGNITION-AUTHORITY-TESTS-20260830T071344Z.log|Test log]]
- [[receipts/SURGERY-COGNITION-AUTHORITY-DENYLIST-20260830T071700Z.json|Surgery receipt]]

No push, merge, deploy, restart, provider call or external effect was performed.

## Surgery 2

- LLM caller inventory: `5/6 → 8/8`.
- Lab gateway: `ISOLATED_LAB_ONLY`.
- Default network-capable entry: `BLOCKED_LAB_GATE`.
- Provider calls and external effects during tests: `0`.
- [[receipts/LLM-INVENTORY-LAB-GATEWAY-20260830T074618Z.log|Surgery 2 test log]]
- [[receipts/SURGERY-LLM-INVENTORY-LAB-GATEWAY-20260830T074700Z.json|Surgery 2 receipt]]

## Surgery 3

- Default runner network policy: `loopback-only`.
- Runtime state, manifest and diagnostics: per-run temporary storage.
- Live provider suite: preserved but denied unless two explicit signals are present.
- Cortex harness import ambiguity: `6/16 → 16/16`.
- [[receipts/HERMETIC-RUNNER-20260830T075600Z.log|Surgery 3 test log]]
- [[receipts/SURGERY-HERMETIC-RUNNER-20260830T075700Z.json|Surgery 3 receipt]]

## Surgery 4

- Observatory implementation: `NOT_FOUND_IN_CURRENT_LINEAGE`.
- Historical runtime body: `body_not_on_this_host`, not “never existed”.
- Current Brier/sample/verifier result: not reproducible.
- No historical code was copied into production.
- [[receipts/OBSERVATORY-PROVENANCE-GAP-20260830T080500Z.json|Observatory provenance gap]]

## Surgery 5

- Replay-safe `observation.v1` record: timestamps, uncertainty, calibration, provenance, privacy, simulation label.
- Fake and replay adapters only; no hardware or production sensor.
- Foundation tests: `15/15`; registered runner: `1/1`.
- Architecture guard remained `11/11`; inventory `8/8`; hermetic boundary `7/7`.
- [[receipts/OBSERVATION-V1-FOUNDATION-20260830T081800Z.log|Surgery 5 test log]]
- [[receipts/SURGERY-OBSERVATION-V1-FOUNDATION-20260830T081900Z.json|Surgery 5 receipt]]

## Campaign closeout (docs worktree; canonical vault NOT_SYNCED)

- [[09-OWNER-ACTION-RUNBOOK|Owner Action Runbook]]
- [[10-POST-CAMPAIGN-ROADMAP|Post-campaign Roadmap]]
- [[11-MERGE-DEPLOY-CHECKLIST|Merge/Deploy Checklist]]
- [[12-90-PERCENT-GATES.yaml|90-percent Gates]]
- [[13-OWNER-INBOX|Owner Inbox]]
- [[14-FINAL-CAMPAIGN-REPORT|Final Campaign Report]]
