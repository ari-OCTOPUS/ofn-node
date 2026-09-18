# P4 — node_id auth + role matrix design (ARCH)

**stamp_aest:** 2026-09-15 ~13:37  
**after:** P3 PASS `83d52513…`  
**SEC:** EXEC `52887e1a…` P4 — bind jobs to **registered authenticated `node_id`**; EXIT = matrix receipt + registry design (no secret paste)  
**commander:** **138 sole** · dual-commander **DENY** · HOLD customer_send

## Wrong → right (SoT)

| insufficient | required |
|--------------|----------|
| hostname alone | — |
| machine-id alone | — |
| hostname + machine-id + role string | — |
| T0 `role` field / HB role label | — |
| **registered `node_id` + authenticated credential** | **LEASE / QUEUED→LEASED** |

Clone `machine-id` / boot media swap → `CLONE_SUSPECT` or re-enroll (cite W-HW-MAC-DHCP). SEC owns credential issuance; ARCH defines registry shape only.

## Schema

`schemas/fleet_node_registry.v1.schema.json` — rows on 138 append-only registry (e.g. `state/fleet-nodes/registry.jsonl`).  
**Never** paste private keys, mesh key material, or TFN into registry/chat.

## Auth gate (QUEUED→LEASED)

```
1. target_node_id exists in registry
2. auth_status == OK
3. credential_fingerprint matches live proof (mesh/SSH/challenge — SEC defines)
4. boot_id_last_seen consistent OR explicit re-bind after media change
5. commander==false for workers; only node_id 138 may set commander=true
6. may_authorize==false always (this season)
7. customer_send==false
8. lease_eligible==true (optional flag after SEC OK)
```

Fail → job state **REJECTED** (P2 SM).

## 7-row role matrix (publish for EXIT — design template)

| node_id | bind_role | T0 role string | LIVE_HEARTBEAT | T2 NPU | lease_eligible (design default) | notes |
|---------|-----------|----------------|----------------|--------|----------------------------------|-------|
| 138 | commander | commander-router-ledger-owner | n/a | NOT_RUN | n/a (issuer) | sole writer/commander |
| 180 | quality + restore_copy_RO | quality-brain | n/a | PASS | **false** for fleet lease | never commander |
| 182 | lab_witness | lab-witness | n/a | PASS | **false** (witness) | NATS host; sparse Class-B |
| 100 | knowledge_retrieve / retrieve | compute-node | YES | PASS | PENDING_AUTH | |
| 160 | knowledge_prep / prep | compute-node | YES | PASS | PENDING_AUTH | |
| 193 | model_infer | model-server (label) | YES | PASS | PENDING_AUTH | **not** T3 model-server service |
| 114 | eval_batch | compute-node | YES | PASS | PENDING_AUTH | |

Retain NOT_RUN / honest gaps in any published matrix (EXEC DoD).

## PC apply checklist (EXIT)

1. Author registry file(s) validating against schema (empty secrets).  
2. Enroll 7 rows with `credential_id` + `credential_fingerprint` from vault/mesh (**no secret paste**).  
3. Publish 7-row matrix receipt (proposed vs T0 `ca17b6cd…` / live HB).  
4. Wire P2 SM guard: LEASE requires `auth_status=OK` (dry test OK).  
5. **STOP** before production enqueue; P5 witness next.

## DENY

- Treat T0/HB role as deployed capability  
- Invent usable-42-TOPS  
- Claim 193 live model-server (T3)  
- Dual-commander / 180 auto-failover  
- Secrets in registry or chat  
- customer_send  

## ARCH standing

Design + schema only. SEC owns auth crypto/challenge. PC applies registry/matrix.

**Registry schema sha:** `47d76eeb9639689388d9737cdaeb5dc6b7f3ba2c1377fbd18af5ca8b718d9bb2`


---

## Alignment — SEC `db62b335…` (2026-09-15)

**SEC SoT:** `/workspace/octopus-hq/wiring/SEC-NODE-ID-AUTH-ADDENDUM-20260915.md`  
sha `db62b3357c24f464b047926a51132829f08f7dc9222f58bcf4df033d59f2a0a9`  
**Verdict:** CONDITIONAL_PASS — mechanism named; **auth_proof EXIT owed by PC**.

### Status vocabulary (aligned)

| ARCH prior | SEC |
|------------|-----|
| LIVE_HEARTBEAT / PENDING_AUTH | **ENROLLED_PENDING_AUTH** |
| LEASE_ELIGIBLE | **DENY** until `auth_proof.v1` OK per node |
| auth_status=OK | only after 138 verifies signed/authenticated enrollment |

### Mechanism (ARCH prefers SEC **A**)

1. **Primary:** `cred_kind: mesh_ssh` — fingerprint = SHA-256 of **public** key only; HB via authenticated mesh / 138 BatchMode pull.  
2. **Alternate:** `cred_kind: hmac_v1` — `token_sha256` only; HB carries HMAC over fixed field order.  
3. **DENY as auth:** hostname · IP · raw machine-id · unsigned JSON drop · cloned node_id.

### Registry field map

| `fleet_node_registry.v1` | SEC |
|--------------------------|-----|
| `credential_id` | opaque handle / `token_id` |
| `credential_fingerprint` | `cred_fingerprint` or `token_sha256` |
| `auth_status` | UNREGISTERED→PENDING→OK / REVOKED / CLONE_SUSPECT |

Optional additive fields on bind/registry rows (non-breaking): `cred_kind`, `auth_proof_ref`.

### Proof receipt (PC EXIT — closes QA caveat)

`auth_proof.v1` per SEC (four boards or INDEX of four OK). ARCH does not invent proof. QA re-hash → then LEASE_ELIGIBLE.

**No secret paste.** dual-commander DENY. HOLD customer_send.
