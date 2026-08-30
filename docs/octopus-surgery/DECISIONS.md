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

## S2-D01 — Lab gateway

The gateway is `ISOLATED_LAB_ONLY`. Presence of a provider credential is not
authorization. The gate is checked before key status, budget or client creation.

## S2-D02 — Explicit admission

Admission requires all of: explicit lab mode, runtime zone `lab|test`, an
allowlisted lab entrypoint, `executable=false`, and `external_action=false`.
No environment variable was added as a generic bypass.

## S2-D03 — Inventory

Every known provider caller must be classified as router-fenced, adapter-fenced,
lab-gated or choke primitive. Residual callers remain forbidden.

## S2-D04 — GitHub publication

No push or PR is permitted from this lineage: `github/main` and the local vault
branch have no merge base. Repair requires an explicit repository migration,
not force push, merge, rebase or history rewrite.

## S3-D01 — Hermetic default

The default runner is offline except loopback, strips provider/sender credentials,
forces outbound flags off, and redirects state/artifacts to a temporary root.

## S3-D02 — Live tests

Live tests remain present. They are not part of the hermetic default and require
both `--live` and `OCTOPUS_ALLOW_LIVE_TESTS=1`. Neither was used.

## S3-D03 — Capability marker

Default and `--only` hermetic runs do not refresh or revoke the runtime capability
marker. Persistent marker behavior remains available only for explicit isolated
or `--live-state` execution.

## S3-D04 — Cortex import

The test imports `cortex.cortex` explicitly. Path-order manipulation is no longer
used to choose between the package and module.

## S4-D01 — Observatory lineage

The implementation and runtime claim stores are `NOT_FOUND_IN_CURRENT_LINEAGE`.
This does not assert that they never existed.

## S4-D02 — Historical metrics

Historical values including 0.80, 0.99, n=114 and Brier tables are narrative
artifacts until reproduced from actual claim records. They cannot score current
measurement quality.

## S4-D03 — No resurrection from prose

No strategy, verifier or database is reconstructed by copying formulas or values
from documentation. Replacement begins from a versioned fixture and independent
producer/scorer/verifier boundaries.

## S5-D01 — Contract beside parser

The new `observation.v1` record lives in `observation_record.py`. The USGS/HN
`parse_body` adapter remains unchanged.

## S5-D02 — Replay only

Fake and replay adapters may not emit an unlabeled physical observation. A real
sensor is out of campaign scope.

## S5-D03 — Local vault branch publication remains forbidden

`ari-OCTOPUS/ofn-node` is PUBLIC and has no merge base with this vault. Pushing
the surgery or rescue branch would publish vault history.

## S5-D04 — Selective public export is PR 6

Canonical export: https://github.com/ari-OCTOPUS/ofn-node/pull/6
PR 5 is `CLOSED_SUPERSEDED`. Merge remains `NOT_AUTHORIZED`.
