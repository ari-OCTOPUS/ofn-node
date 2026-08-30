---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, roles, authority, disputed]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[_ops/octopus_mcp/CONSTITUTION]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
---

# 02 — Role authority

```text
SIGNED_ROLE_REGISTRY_FOUND=NO
NODE_182_ROLE=DISPUTED
NODE_182_ROLE_STATUS=DISPUTED
P2_BINDING=BLOCKED
LOCAL_MINTING=FORBIDDEN
observed_at=2026-08-29T04:50:00Z
scope=this_host_only
```

Two stories are both in circulation. They use overlapping English words for **different planes**. Mixing them is the bug.

## Narratives

**A — spine/business chain (L191 EDGE table)**  
180 produces `proposal.v1` and must drain it to 138. 182 is “witness for this run” (EDGE-8). Owner receipt is a separate later edge (EDGE-9, armed on PC).  
Source: `06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28.md:164-175`. Signed: NO. Precedence: forensic run report. Runtime enforcement: NO. Truth: `DOCUMENTED`.

**B — board operating roles (180 live registry + Cursor session rule)**  
138 = commander / executor / sole OFN ledger owner.  
180 = quality-brain / evolutionary steward / `PROPOSE_ONLY` / `may_authorize=false`.  
182 = independent lab-witness / `may_authorize=false`.  
Source: owner-pasted 180 pack 2026-08-29 (`nodes.json`, `agent_roles.json`, `policy.json`); Cursor user rule for this session. Signed: NO. Precedence: live unsigned registry on 180 + operator rule. Runtime enforcement on 180: `DOCUMENTED` as `may_authorize=false` in those JSON files (not re-read here). Truth: `DOCUMENTED`.

**C — owner-signed A2-001 only (2026-08-18)**  
138 = proposal origin. 180 = execution node. 191 = canonical authority. Autonomy `A2_SANDBOX_ONLY`. `EFFECT AUTHORITY: NONE`. 182 **not assigned**. Receipt v1 `observer_node: ".180"` is an A2 integrity hint, not an OFN witness grant.  
Source: `02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER.md:16-57`. Signed: **owner block verbatim**. Precedence: **high for A2-001 only**. Runtime: quarantined on 191; `lab_execution: NOT_STARTED`. Truth: `REPO_VERIFIED`.

Narrative A is **not** a signed contract. Closest fragments: 180 wrote `proposal.v1` (live EDGE-5); 138 has local `witness_mint`; ADR-11 (proposed) wants 182 content receipts. That is not “138=witness, 182=receipt issuer.”

Narrative B matches unsigned V2 `_NODE_ROLES`, 180 pack, systemd witness unit, and this session rule. It **conflicts** with A2-001 on 180 (quality-only vs execution node) and with C-034 / Sensorium charter (182 = observation, not OFN witness).

A and B are not automatically contradictory if “witness” in A means EDGE-8 *capability* on 182. They **are** contradictory if A is read as “138 is the witness.” L191 names 138 as mint target (EDGE-7), not witness.

## Source register

| path | SHA256 | commit | date | signed | precedence | claim | runtime enforcement | truth |
|---|---|---|---|---|---|---|---|---|
| 180 `/root/octopus-mesh` `nodes.json` / `agent_roles.json` / `policy.json` | UNKNOWN here | n/a (mesh has no .git per 180 pack) | 2026-08-29 pack | NO | highest **unsigned live** map on 180 | 138 commander/ledger-owner; 180 quality-brain PROPOSE_ONLY; 182 lab-witness; all may_authorize=false | DOCUMENTED on 180 worker/policy | DOCUMENTED |
| 180 `MEGAPROMPT-138-COMMANDER-V2-ANATOMY.md` | UNKNOWN here | UNKNOWN | cited in 180 pack | NO | prompt, not registry | 138 commander/executor/sole ledger | none | DOCUMENTED |
| 180 `MEGAPROMPT-182-WITNESS-V2-VERIFY.md` | UNKNOWN here | UNKNOWN | cited in 180 pack | NO | prompt | 182 independent witness | none | DOCUMENTED |
| Cursor user rule (this session) | n/a | n/a | 2026-08-29 | NO | session constraint | 180 quality brain PROPOSE_ONLY; 138 ledger; 182 witness | session only | DOCUMENTED |
| `F:\backup\_ops\octopus_mcp\CONSTITUTION.md` | not hashed this turn | tracked vault | 2026-08-03 | NO (git-tracked ≠ signed) | vault MCP protocol | five **agent** roles, not node 138/180/182 | MCP server guards | REPO_VERIFIED |
| `06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28.md` | not hashed this turn | vault | 2026-08-28 | NO | forensic | EDGE-6 180→138 send; EDGE-8 witness 182 | none | DOCUMENTED |
| `01 - Dashboard/HANDOFF.md` | not hashed this turn | vault | 2026-08-29 | NO | session index | EDGE-6 blocked; dual transmit on 180 | none | DOCUMENTED |
| `02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER.md` | not hashed this turn | vault | 2026-08-18 | YES (owner block) | high for A2-001 only | 138 proposal origin; 180 execution; 191 canonical; 182 silent; effect none | A2 sandbox only | REPO_VERIFIED |
| `01-TRUTH/CONTRADICTIONS.md` C-034 | not hashed this turn | vault | 2026-08-17 | owner-verified | high for “182 exists”; **not** OFN witness | laptop brain · legs board · Sensorium observation | no | DOCUMENTED |
| 138 V2 `_NODE_ROLES` in `cockpit_v2_read_model` @ `6881337` | not hashed this turn | 138 snapshot | 2026-08-28 | NO | high for **what V2 would project**; overridable by `config/nodes.json` | 138 commander-router-ledger-owner; 180 quality-brain; 182 lab-witness; `may_authorize` default false | yes **if** that file is loaded (PID 1351408 did not load P1; file predates P1) | DOCUMENTED |
| 182 `octopus-witness-worker.service` (obs182 extract) | UNKNOWN here | n/a | 2026-08-26/27 | unit text ≠ owner signature | medium as live label | “node 182, lab-witness, may_authorize=false” | oneshot timer ~3 min | DOCUMENTED |
| Signed node registry covering `{138,180,182} × {Producer,Witness,Executor,Receipt}` | — | — | — | — | — | — | — | NOT_FOUND |

No source is a **signed mesh role registry**. A2-001 is signed and **scoped**; it does not fill that seat. IP addresses and filenames were not used as role proof.

## Role matrix (unsigned live map vs spine vocabulary)

| Node | Producer | Planner | Witness | Executor | Receipt issuer | May authorize | Evidence |
|---|---|---|---|---|---|---|---|
| 138 | **DISPUTED** — A2-001: proposal origin. Live EDGE-5: 180 built `proposal.v1`. V2: commander, not producer | commander/reconciler (B) | NO as canonical (local `witness_mint` = STRUCTURAL only; P2 REJECT) | **DISPUTED** — B/charter: OFN business execute via `owner_decide`. A2-001: execution = 180 | OFN ledger / `complete_manual` exist; ADR-11 (proposed) wants 182 content receipt | false in V2 default | A2-001:52-54; L191; `_NODE_ROLES`; P2-DISCOVERY.md:68-70 |
| 180 | YES on live cognition path (EDGE-5) | no signed Planner title | NO | **DISPUTED** — A2-001 execution node (`EFFECT NONE`). B/session: quality only | A2 receipt **observer** only (`observer_node: ".180"`) | false | A2-001:16-57; L191:169; 180 pack |
| 182 | NO | NO | **DISPUTED** — unsigned/runtime lab-witness vs C-034/Sensorium observation vs A2-001 silent | NO | **DISPUTED** — ADR-11 proposed content receipt; Narrative A “receipt issuer” has no signed seat | false | `_NODE_ROLES`; 182 unit; L191:173; C-034; A2-001 (182 absent) |
| 191 | NO | NO | NO | NO | A2-001 canonical evidence/owner gate; EDGE-9 owner-receipt file may sit here | owner only | A2-001:54; L191 EDGE-9 |

## Required questions

| Question | Answer | Truth |
|---|---|---|
| Does Witness 182 require `draft-11`? | String `draft-11` / `DRAFT-11` / `draft_11`: **zero matches** in `06-EVIDENCE`, `07 - Knowledge`, `08-PLANS`, `OCTOPUS`, `agent-prompts` (follow-up search). No artifact ties 182 to draft-11. Prior owner law is **unconfirmed**, not disproven. If still valid, pre-draft-11 binding is reject. | NOT_FOUND / UNKNOWN |
| Can receipt and witness be the same node? | Signed sources do **not** authorize a merge. Unsigned OFN docs split them. Fake E2E on 138 mints then receipts **in tests only**. | DOCUMENTED |
| Can 138 witness its own execution? | Not as canonical witness. P2 REJECTS `witness_mint` inside `owner_decide`. Local mint = `STRUCTURAL_PASS` only; no `EXECUTABLE_PASS`. | DOCUMENTED |
| Can producer mint witness identifiers? | 138 module **can** mint deterministic STRUCTURAL `request_id`. Embedding that as 182 truth is REJECT. Live 180→138 drain is EDGE-6 broken, so producer path did not reach 182 on the documented run. | DOCUMENTED |
| What if 182 is unavailable? | Observed: EDGE-8 `MISSING_FOR_RUN`; worker oneshot, dead between ~3 min ticks. Proposed P2 RED: missing 182 → fail-closed (**not implemented**). No signed failover to 138/180/191. | DOCUMENTED |

```text
NODE_138_ROLE=commander_reconciler_ledger_owner (unsigned live) / mint_target (spine)
NODE_180_ROLE=quality_brain_PROPOSE_ONLY / proposal_producer (spine EDGE-5)
NODE_182_ROLE=lab_witness (unsigned live) / EDGE-8_witness (spine)
NODE_182_ROLE_STATUS=DISPUTED
```

Disputed means: no signed mesh registry; A2-001 is signed but **A2-scoped** and silent on 182; C-034 names 182 as Sensorium observe; unsigned V2/systemd name 182 lab-witness. Do not mint P2 bindings from this table.
