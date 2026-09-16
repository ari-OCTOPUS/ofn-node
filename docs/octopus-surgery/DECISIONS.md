---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, surgery, decisions, governance]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
sources:
  - "[[CHECKPOINT]]"
  - "[[00-CONCEPT-MAP]]"
---

# Surgery 1 decisions

## S1-D01 — Result classification

`TEST_ONLY_GUARD` is final. Production behavior changes equal zero.

## S1-D02 — Verifier wording

`27/27` means 27 checks executed by one verifier. The claim that these were
27 independent verifiers is `CONTRADICTED` and must not be restored.

## S1-D03 — Cognition boundary

Narrow cognition separation is `VERIFIED` only for the policy’s enumerated
source paths. This is not a system-wide claim.

## S1-D04 — Provider boundary

Cortex → provider is `SAFE_INFERENCE_BOUNDARY`. Provider adapters may retain
model-network and provider-credential capability because they expose inference
responses, not approval or executor authority.

## S1-D05 — Executor boundary

`code_brain → code_autonomy` is `APPROVED_EXECUTOR_BOUNDARY`, not provider-only.
Proposal generation does not imply owner approval.

## S1-D06 — Gate namespaces

OFN `secret_rotation` remains distinct from rotation-vault mechanisms. Surgery 1
does not change either.

## S1-D07 — Provenance

The parent manifest, surgery receipt, resulting manifest and Git commit remain
separate immutable provenance values listed in [[CHECKPOINT]].

## S1-D08 — Operations

No push, merge, deployment, runtime restart, provider call, external effect or
owner-gate modification is authorized or recorded by this synchronization.
