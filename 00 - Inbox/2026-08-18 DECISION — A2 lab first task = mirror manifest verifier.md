---
type: knowledge
status: inbox
updated: 2026-08-18
created: 2026-08-18
created_by: agent
tags: [octopus, a2, sandbox, mirror, propose-only]
sources:
  - "[[../04-SYSTEMS/OCTOPUS-MAX-AUTONOMY-ROADMAP]]"
  - "[[../COUNCIL_REPORTS/2026-08-16-wave-01/A15_synthesis/OCTOPUS_REALITY_FREEZE]]"
  - "[[../07 - Knowledge/شناخت-اختاپوس/66-VERIFIER-EVIDENCE-ENVELOPE-2026-08-18]]"
---

# DECISION — A2 lab first task = mirror manifest verifier

> **Banner 2026-08-18 ~03:00 +10:** owner approved A2-001 as OWNER-APPROVED-PROPOSAL. Canonical block: [[../02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]] · inventory: [[../06-EVIDENCE/A2-001-CANONICAL-DECISION-2026-08-18]] · [[2026-08-18 DECISION — A2-001 inventory-first not octopus-bridge canonical]]. Sandbox code **not** built — verdict `UNKNOWN_CANONICAL`. `.180` still not activated. Promotion never automatic.

**State: OWNER-APPROVED-PROPOSAL; `.180` still not started.** Inventory halt on `.191` (do not treat this note as “awaiting owner confirm” anymore).

WAVE0_OBSERVE_ONLY. L2 propose-only. autonomy_delta=0. This session did **not** start the lab, raise autonomy, edit TCB, clear GITWRITE-FAILED, start/stop services, SSH to `.180` / `.138` / `.182`, copy secrets, install Graphiti/Neo4j, wire NATS Leaf, or put Global Workspace on Sensorium.

Canonical copy: [[../02-DECISIONS/A2-SANDBOX-LAB-FIRST-TASK-2026-08-18]]. Short index: [[../07 - Knowledge/شناخت-اختاپوس/67-COUNCIL-CONSERVATIVE-PATH-A2-MIRROR-2026-08-18|۶۷]]. Evidence stub: [[../06-EVIDENCE/A2-LAB-NOT-STARTED-AWAITING-OWNER-2026-08-18]]. Local sources (no pre-signed cloud URLs): [[../04-SYSTEMS/OCTOPUS-MAX-AUTONOMY-ROADMAP]] · [[../COUNCIL_REPORTS/2026-08-16-wave-01/A15_synthesis/OCTOPUS_REALITY_FREEZE]].

`.180` SERVICE-INVENTORY-AND-MIGRATION-MATRIX: **inventory in flight / pending**.

## Locked first task

**Mirror manifest verifier** — hash, small manifest, unidirectional pull, receipt.

`.180` must not host memory/orchestration until it has a comparable snapshot/manifest/hash/unidirectional pull/receipt from `.191`. Among the three candidate first *jobs* inside the lab, **mirror comes before memory and before envelope-schema polish**.

Envelope schema already has laptop sidecar `octopus-handshake-envelope/1` and Sensorium exchange v1.1 ([[../07 - Knowledge/شناخت-اختاپوس/66-VERIFIER-EVIDENCE-ENVELOPE-2026-08-18|۶۶]]). Improving it is useful but **not** the bottleneck for continuity.

## Layers (council)

| Layer | Where | Role tonight |
|---|---|---|
| Canonical git | laptop `.191` | Source of truth. Write stays here. |
| A2 lab | `.180` sandbox | Quarantined patches, test receipts, evidence envelopes only. **Not started.** |
| Sensorium | `.182` | Observe. Publishes observations only. No Global Workspace action. |
| Feet | `.138` | Reflex. No money/legal change this stage. |
| Memory | laptop, write-gated | Memory v1 **later** (path step 4). Graphiti only after write-contract fields exist. |
| Broadcast | shadow | Typed Event Spine shadow is path step 3 — **not** tonight. |

## Execution order (council, conservative)

1. **A2 sandbox lab on `.180`** — stand up the quarantined lab (owner confirm first).
2. **Mirror** — first job *inside* the lab = mirror manifest verifier (this lock).
3. **Typed Event Spine shadow** — after mirror receipts exist.
4. **Memory v1 on laptop** — Memory Write Contract + tests is the correct *later* laptop-side gate, not tonight's first lab job. Graphiti only after those write-contract fields exist.

## Explicitly NOT starting tonight

- Graphiti / Neo4j
- Global Workspace on Sensorium (`.182`). GWT v0 stays on laptop or `.180`, **read-only, no action**. Sensorium publishes observations only.
- Typed Event Spine (except as a later path step, not this job)
- Memory v1 / Memory Write Contract as the first lab job
- Envelope-schema polish as the first lab job
- x402 / wallet / stablecoin. Money and legal stay under the owner legal entity.
- Merge, deploy, TCB change, service change, external action

`survival` / `proposal_score` ranks **pre-authorized A2 sandbox tasks only**. It never opens gates.

## Decision (verbatim — proposed binding)

Decision: Start A2-Sandboxed Self-Improvement Lab on .180.
Scope: Only allowlisted internal code and tests.
Models: Fugu non-Ultra = implementer; DeepSeek V4 Flash = reviewer.
Output: Quarantined patches, test receipts, evidence envelopes.
Forbidden: merge, deploy, TCB change, service change, external action.
Budget: fixed nightly cap; one active job; maximum three jobs.

Models are a **proposed binding**. Providers were **not** configured this session.

## Status this session

**Lab NOT started.** No process launched on `.180`. No activation until owner confirm.
