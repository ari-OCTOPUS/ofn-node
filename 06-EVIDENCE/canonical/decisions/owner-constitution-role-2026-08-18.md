---
type: evidence
status: active
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, custodian, constitution, owner-gate, node-191]
sources:
  - "[[../../04-SYSTEMS/DUAL-BRAIN-CONSTITUTION]]"
  - "[[../../_ops/octopus_mcp/CONSTITUTION]]"
  - "[[../../agent-prompts/_PROJECT_INSTRUCTIONS]]"
  - "[[../../00 - Inbox/2026-08-18 DOCTRINE — boards-always-on + autonomy mandate (owner D13)]]"
---

# Owner constitution / role — observed record (.191)

`observed_at`: **2026-08-18T03:03:54+10:00**
OS local offset **UTC+10** (`tzutil`: AUS Eastern Standard Time). August in Sydney is AEST, not UTC+11.

Recorder: OCTOPUS-CUSTODIAN-191 on `DESKTOP-KA9RFN5`. WAVE0_OBSERVE_ONLY. L2 Armed. EFFECT NONE. Production FALSE. This file is an observation, not a new grant.

## Owner

- Human owner name in dual-brain constitution: **Armin** (`04-SYSTEMS/DUAL-BRAIN-CONSTITUTION.md`).
- Tie-break: after mutual veto, owner votes `ok / no / later` (same file, §۳).
- Vault constitution for agents is read-only: `agent-prompts/_PROJECT_INSTRUCTIONS.md` (imported by `CLAUDE.md`). Agents do not edit it.
- MCP / multi-brain protocol: `_ops/octopus_mcp/CONSTITUTION.md` v1.1 — five MVP roles; owner verdicts pulled from `_ops/owner-verdicts.yaml` / `_ops/owner_verdicts.py` (env wins).

## This node (.191)

| field | observed value |
|---|---|
| node_id | `.191` |
| hostname | `DESKTOP-KA9RFN5` |
| authority | `CANONICAL_EVIDENCE_AND_OWNER_GATE` |
| mode | `READ_ONLY_BY_DEFAULT` |
| write_scope | append-only canonical evidence + owner-approved records |
| WAVE | `WAVE0_OBSERVE_ONLY` |
| effect | `NONE` |
| production | `FALSE` |

`.191` verifies, records, quarantines, or rejects. It does not implement experimental code, apply TCB patches, ack dispatched commands, or promote A2 jobs.

## Standing owner doctrine still on disk (not re-voted this pass)

- **D13 boards-always-on:** boards `.138` / `.182` are 24/7 backbone; laptop is intermittent. Inbox: `00 - Inbox/2026-08-18 DOCTRINE — boards-always-on + autonomy mandate (owner D13).md`.
- **A2-001:** OWNER-APPROVED-PROPOSAL; execution node `.180`; proposal origin `.138`; canonical authority `.191`; promotion never automatic. See `02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER.md`.
- **P-ACK-1 withdrawn:** only owner closes `unknown_outcome`. Command `01a00d3d-…` remains dispatched.
- **EQUIP-G2 + JOB-RESEARCH:** owner-approved patches exist in Inbox; TCB ceremony unapplied (verified this pass: strings absent from `4d_system/brain/automation.py` and `daemon.py`).

## What this record is not

Not a new constitution. Not a TCB edit. Not an A2-001 path choice. Not clearance of `GITWRITE-FAILED`.
