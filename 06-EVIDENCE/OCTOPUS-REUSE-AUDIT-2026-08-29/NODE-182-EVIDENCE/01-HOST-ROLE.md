---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-182, roles, disputed]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
  - "[[01-TRUTH/CONTRADICTIONS]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/02-ROLE-AUTHORITY]]"
---

# 01 — Host role

```text
SIGNED_ROLE_REGISTRY_FOUND=NO
NODE_182_ROLE=DISPUTED
NODE_182_ROLE_STATUS=DISPUTED
MAY_AUTHORIZE=false
MAY_EXECUTE=false
WITNESS_182_RUNTIME=NOT_OBSERVED
observed_at=2026-08-29T05:30:00Z
method=merge_signed_and_unsigned_role_sources
scope=this_host_only
```

## Identity (documented, not re-probed)

| field | value | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| hostname | `sensorium-opi5pro` | L191 findings §2; health 09-32-182; obs182_extract.json | prior SSH artifacts | 2026-08-27..28 | documented_remote | DOCUMENTED |
| eth0 / asserted_ip | `192.168.0.182` | L191; Phase 0 envelope | prior SSH | 2026-08-28 | documented_remote | DOCUMENTED |
| kernel (prior) | Linux 6.1.115-vendor-rk35xx aarch64 | L191 §2 | prior SSH | 2026-08-28 | documented_remote | DOCUMENTED |
| this session identity | NOT_OBSERVED | this pack | no SSH | 2026-08-29T05:30:00Z | this_host_only | NOT_OBSERVED |

Two **planes** share the same IP. Mixing them is the role bug.

| plane | path (prior) | function | source | observed_at | truth_status |
|---|---|---|---|---|---|
| Sensorium | `/opt/octopus` + units `octopus-sensorium.service` | observation / WAVE0 locked | C-034; health 09-32-182b | 2026-08-17..28 | DOCUMENTED |
| Mesh witness | `/root/octopus-mesh` + `octopus-witness-worker.service` | lab-witness oneshot | obs182_extract.json timer | 2026-08-27T02:30:47Z | DOCUMENTED |

## Role sources (rank, not merge)

| id | claim about 182 | signed | plane | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|---|---|
| A2-001 | **silent** — not assigned. 138 origin, 180 execute, 191 canonical, EFFECT NONE | YES (owner block verbatim) | A2 sandbox only | `02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER.md:16-57` | file_read | 2026-08-18 | A2_scoped | REPO_VERIFIED |
| C-034 | **observe** — laptop brain · legs board · Sensorium observation | owner-verified contradiction | Sensorium | `01-TRUTH/CONTRADICTIONS.md:532-541` | file_read | 2026-08-17 | topology | DOCUMENTED |
| unsigned V2 `_NODE_ROLES` | **lab-witness**, `may_authorize` default false | NO | OFN cockpit projection | P2-DISCOVERY/02:66 @ 138 `6881337` | documented snapshot | 2026-08-28 | 138_file | DOCUMENTED |
| 180 pack `nodes.json` / `agent_roles.json` / `policy.json` | **lab-witness**, `may_authorize=false` | NO | unsigned live 180 mesh | P2-DISCOVERY/02:57 | owner-pasted pack | 2026-08-29 | documented_remote | DOCUMENTED |
| 182 systemd | Description: `node 182, lab-witness, may_authorize=false` | unit text ≠ owner signature | mesh worker | obs182_extract.json; health 09-32-182:28 | artifact | 2026-08-27 | documented_remote | DOCUMENTED |
| L191 EDGE-8 | **witness for this run** | NO | spine table | `OCTOPUS-L191-FINDINGS-2026-08-28.md:173` | forensic report | 2026-08-28 | documented_remote | DOCUMENTED |
| Cursor session rule | 182 witness; 180 quality-only | NO | operator | user rule this session | session | 2026-08-29 | session_only | DOCUMENTED |
| signed `{138,180,182}×{Producer,Witness,Executor,Receipt}` | — | — | mesh | P2-DISCOVERY/02:68 | search | 2026-08-29 | this_host_only | NOT_FOUND |

A2-001 is signed and **scoped**. It does not fill a mesh registry seat. IP and hostname are not role proof.

## Authority matrix (182 only)

| capability | grant | source | method | observed_at | scope | truth_status |
|---|---|---|---|---|---|---|
| Producer of `proposal.v1` | NO | L191 EDGE-5 = 180 | doc | 2026-08-28 | documented_remote | DOCUMENTED |
| Planner | NO | no signed title | merge | 2026-08-29 | this_host_only | NOT_FOUND |
| Witness (OFN/EDGE-8) | DISPUTED | V2/systemd/L191 vs C-034 vs A2 silent | merge | 2026-08-29 | this_host_only | DISPUTED |
| Executor / `owner_decide` | NO | live decide is 138; A2 execute=180 EFFECT NONE | P2-DISCOVERY.md; A2-001 | 2026-08-18..29 | this_host_only | DOCUMENTED |
| Receipt issuer (effect) | DISPUTED / no signed seat | ADR-11 proposed only (P2 02:78) | merge | 2026-08-29 | this_host_only | DISPUTED |
| may_authorize | false | all unsigned live labels + worker `may_authorize: False` | artifact | 2026-08-26..29 | documented_remote | DOCUMENTED |
| may_execute | false | no source grants execute | merge | 2026-08-29 | this_host_only | DOCUMENTED |

```text
NODE_182_ROLE=DISPUTED
NODE_182_ROLE_STATUS=DISPUTED
MAY_AUTHORIZE=false
MAY_EXECUTE=false
```

Do not mint P2 bindings from this table.
