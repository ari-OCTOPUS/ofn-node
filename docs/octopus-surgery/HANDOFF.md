---
type: handoff
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, surgery, handoff, safety]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
sources:
  - "[[CHECKPOINT]]"
  - "[[08-RISK-REGISTER]]"
---

# Surgery 1 handoff

Surgery 1 is technically complete as `TEST_ONLY_GUARD`; production behavior
changed by zero. Canonical evidence is indexed at [[INDEX]].

## Boundary state

- Narrow cognition separation is verified only in the policy’s inspected source set.
- Cortex provider access is `SAFE_INFERENCE_BOUNDARY`, not execution authority.
- Provider adapters still own model-network and provider-credential capability.
- `code_brain → code_autonomy` is explicitly an `APPROVED_EXECUTOR_BOUNDARY`.
- Proposal creation remains distinct from approval and execution.
- `27/27` is one verifier’s 27 checks, not 27 independent verifiers.
- OFN `secret_rotation` remains a separate gate family.

## Next three evidence-backed tasks

1. Repair the pre-existing LLM caller inventory and classify/fence the lab gateway.
2. Make the full runner hermetic for network and runtime-state writes.
3. Recover current observatory strategy/verifier provenance and reproduce Brier evidence.

Do not infer send, revenue, booking or production readiness from this handoff.
Do not begin Surgery 2 without a separate directive.
