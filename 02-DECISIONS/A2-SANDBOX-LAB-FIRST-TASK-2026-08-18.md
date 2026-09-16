---
type: proposal
status: draft
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, a2, sandbox, mirror, propose-only]
sources:
  - "[[../04-SYSTEMS/OCTOPUS-MAX-AUTONOMY-ROADMAP]]"
  - "[[../COUNCIL_REPORTS/2026-08-16-wave-01/A15_synthesis/OCTOPUS_REALITY_FREEZE]]"
  - "[[../00 - Inbox/2026-08-18 DECISION — A2 lab first task = mirror manifest verifier]]"
---

# A2 sandbox lab — first task lock (2026-08-18)

> **Banner 2026-08-18 ~03:00 +10:** owner approved A2-001. Canonical: [[A2-001-MIRROR-MANIFEST-VERIFIER]] · [[../06-EVIDENCE/A2-001-CANONICAL-DECISION-2026-08-18]]. `.191` did not rubber-stamp `octopus-bridge`. Verdict `UNKNOWN_CANONICAL` — no sandbox code in a guessed tree. `.180` still not activated. Promotion never automatic.

**OWNER-APPROVED-PROPOSAL on `.191`.** Lab on `.180` **not** started. Do not read this file as still “awaiting owner confirm.”

Inbox capture (Inbox-first): [[../00 - Inbox/2026-08-18 DECISION — A2 lab first task = mirror manifest verifier]]. Index: [[../07 - Knowledge/شناخت-اختاپوس/67-COUNCIL-CONSERVATIVE-PATH-A2-MIRROR-2026-08-18|۶۷]]. Stub: [[../06-EVIDENCE/A2-LAB-NOT-STARTED-AWAITING-OWNER-2026-08-18]]. Roadmap: [[../04-SYSTEMS/OCTOPUS-MAX-AUTONOMY-ROADMAP]]. Council freeze: [[../COUNCIL_REPORTS/2026-08-16-wave-01/A15_synthesis/OCTOPUS_REALITY_FREEZE]].

`.180` SERVICE-INVENTORY-AND-MIGRATION-MATRIX: **inventory in flight / pending**.

## Locked first A2 self-improve task

**Mirror manifest verifier** (hash, small manifest, unidirectional pull, receipt).

Rationale (do not water down): Council order is conservative: (1) A2 sandbox lab on `.180`, (2) mirror, (3) Typed Event Spine shadow, (4) Memory v1 on laptop, Graphiti only after write-contract fields exist. Among the three candidate first *jobs* inside the lab, **mirror comes before memory and before envelope-schema polish** because `.180` must not host memory/orchestration until it has a comparable snapshot/manifest/hash/unidirectional pull/receipt from `.191`. Memory Write Contract + tests is the correct *later* laptop-side gate (step 4), not tonight's first lab job. Evidence Envelope schema already has laptop sidecar `octopus-handshake-envelope/1` and Sensorium exchange v1.1; improving it is useful but not the bottleneck for continuity.

## Layers

| Layer | Where | Role |
|---|---|---|
| Canonical git | laptop `.191` | Source of truth |
| A2 lab | `.180` sandbox | Quarantined patches, test receipts, evidence envelopes. **Not started.** |
| Sensorium | `.182` | Observe only |
| Feet | `.138` | Reflex |
| Memory | laptop, write-gated | Step 4, not tonight |
| Broadcast | shadow | Event spine = step 3, not tonight |

## Execution order

1. A2 sandbox lab on `.180`
2. Mirror (first job inside the lab = this lock)
3. Typed Event Spine shadow
4. Memory v1 on laptop; Graphiti only after write-contract fields exist

## Not tonight

Graphiti · GWT action on `.182` (GWT v0 stays laptop or `.180`, read-only, no action; Sensorium publishes observations only) · event spine as a live job · Memory v1 · x402/wallet/stablecoin · merge/deploy/TCB/service/external action.

`survival` / `proposal_score` ranks pre-authorized A2 sandbox tasks only — never opens gates. Money/legal stay under the owner legal entity.

A2 lab itself remains sandbox-only. Models (proposed binding, **not** configured this session): Fugu non-Ultra = implementer; DeepSeek V4 Flash = reviewer.

## Decision (verbatim)

Decision: Start A2-Sandboxed Self-Improvement Lab on .180.
Scope: Only allowlisted internal code and tests.
Models: Fugu non-Ultra = implementer; DeepSeek V4 Flash = reviewer.
Output: Quarantined patches, test receipts, evidence envelopes.
Forbidden: merge, deploy, TCB change, service change, external action.
Budget: fixed nightly cap; one active job; maximum three jobs.

## Status

**Lab NOT started this session.** No process on `.180`.
