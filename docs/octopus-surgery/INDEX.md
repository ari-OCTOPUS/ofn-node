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

This public copy is sanitised evidence on `ari-OCTOPUS/ofn-node`.
It is not the canonical Obsidian vault.
`CANONICAL_VAULT_CONTENT = OBSIDIAN_CONTENT_SYNCED_GIT_BRANCH_SEPARATE`.
`PRIMARY_RESCUE_BRANCH = DIRTY_NOT_SYNCED`.
Local vault branch publication remains `LOCAL_VAULT_BRANCH_PUBLICATION_FORBIDDEN`.

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

No local vault or surgery branch was pushed.
One sanitized GitHub-lineage export branch was pushed as PR #6.
No merge, deploy, restart, provider call or external effect occurred.

## STAGE-01 lineage scan (2026-09-01)

Read-only cross-check of the STAGE-00, CB Insights/Hugging Face, and
10-aspect uploads against this GitHub tree. Propose-only.
`scope=this_host_only`. Vault paths are `body_not_on_this_host`.

- [[stage-01-lineage-scan/2026-09-01/STAGE-01-REPORT|STAGE-01 report]]
- [[stage-01-lineage-scan/2026-09-01/CONTRADICTIONS|STAGE-01 contradictions]]
- [[stage-01-lineage-scan/2026-09-01/CONCEPT-REGISTRY.json|Concept registry]]
- Scanner: `tools/gap_scan.py` · tests: `tests/test_gap_scan.py`
- Live counts stay in `tools/repo_baseline.py`, not in this index.
- D-26 recorded at `docs/architecture/DECISION-canonical-bodies-2026-09-01.md`;
  `implementation_authorized=false`.

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

## Campaign closeout

- [[09-OWNER-ACTION-RUNBOOK|Owner Action Runbook]]
- [[10-POST-CAMPAIGN-ROADMAP|Post-campaign Roadmap]]
- [[11-MERGE-DEPLOY-CHECKLIST|Merge/Deploy Checklist]]
- [[12-90-PERCENT-GATES.yaml|90-percent Gates]]
- [[13-OWNER-INBOX|Owner Inbox]]
- [[14-FINAL-CAMPAIGN-REPORT|Final Campaign Report]]
