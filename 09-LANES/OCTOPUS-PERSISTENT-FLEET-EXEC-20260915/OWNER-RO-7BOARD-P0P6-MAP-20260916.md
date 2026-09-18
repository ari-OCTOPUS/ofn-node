# OWNER RO — 7-board roles + persistent-fleet P0–P6 topology

**mode:** architecture map only · **no implement**  
**stamp:** 2026-09-16 · ARCH reply to COMMANDER  
**commander:** **138 sole** · dual-commander **DENY** · **HOLD customer_send**  
**193:** bind_role `model_infer` · T0 label `model-server` · **≠ T3 live model-server service**

## Binding SoT (prefer SEC-aligned)

| slice | sealed sha256 |
|-------|----------------|
| EXEC umbrella | `52887e1a088d6d4e87f2a8c14879db392a647d450afe8473ea0a5e620022d268` |
| NEXT megaprompt | `7ab84e03df7ca708abeb8cb4178c2d7cf10bc00e9b17a20d2c41588c26508f07` |
| P4 design (aligned) | `8b0a5e03c4df626cb735a54ba16e0a02c948f23c9a9066d7fe0354e107316cd2` |
| P4 registry schema | `47d76eeb9639689388d9737cdaeb5dc6b7f3ba2c1377fbd18af5ca8b718d9bb2` |
| SEC P4 | `db62b3357c24f464b047926a51132829f08f7dc9222f58bcf4df033d59f2a0a9` |
| P5 contract (aligned) | `5d12e068568cdcc694ac1c8de6c5e36c623832727244814a36303ed7862c82d7` |
| SEC P5 | `3e8bd525748531e747761cfaa4345b8a39af8758ea3bf7c565e3da1ea8ba27ec` |
| live `fleet_job.v1` | `49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59` |
| P6 design (aligned) | `4dea603014747a966bfaf9da3dd40b2378f283b462b4ed83923095920140851b` |
| SEC P6 | `9cd862efcad4ee98cb021913c1a92ab5d1fc7766915ce47e2a646bcbb72c9c3c` |
| matrix schema | `91bacbc63d793c11a4a61180206b564130aa9e2a8b93eec7f9c78df9822bf321` |

Pre-align superseded where noted: P4 `63da5b5c…` · P5 `75b71c43…` · P6 `0b38466b…`.

---

## 7-board role matrix (P4 registry + bind map)

| node_id | LAN | bind_role | P5 / fleet part | lease |
|---------|-----|-----------|-----------------|-------|
| **138** | .138 | commander | sole producer · lease issuer · queue/receipt writer | issuer (not worker lease) |
| **180** | .180 | quality + restore_copy_RO | review / P3 restore copies only | **never** commander / never lease issuer |
| **182** | .182 | lab_witness | NATS/JetStream host · Class-B witness | not second memory writer |
| **100** | .100 | knowledge_retrieve | P5 pilot consumer (`retrieve`) | LEASE iff auth OK |
| **160** | .160 | knowledge_prep | deferred `prep` | LEASE iff auth OK |
| **193** | .193 | model_infer | deferred infer · **≠ T3 model-server service** | LEASE iff auth OK |
| **114** | .114 | eval_batch | deferred eval · never auto-promote | LEASE iff auth OK |

Auth gate (QUEUED→LEASED): registered `node_id` + `auth_status=OK` + credential fingerprint match — **not** hostname / machine-id alone (`47d76eeb…` / SEC `db62b335…`).

Evidence path (design): `retrieve(100) → model(193) → review(180?) → persist(138)` with `prep(160)` feeding index and `eval(114)` offline.

---

## P0–P6 topology (sealed)

```
[P0 bus] 182 JetStream YES · consumers=0 · 138 nats ABSENT
          → NATS durability NOT_CLAIMED until ≤1 durable + proof
[P1 mem] 138 fleet_facts/decisions/hypotheses (dry persist)
[P2 SM]  138 fleet_jobs.jsonl shadow/live SM · states fail-closed
[P3 RO]  180 /opt/octopus-restore-copies/… · dual-commander DENY
[P4 auth] registry.v1 on 138 · mesh_ssh FP preferred · LEASE gated
[P5 path] CANONICAL bus = jsonl_138
          138 QUEUED → LEASED(100) → RUNNING → CLOSED · external_effects=0
          JetStream FLEET_JOB optional later: exactly one durable fleet_job_worker_v1
          DENY dual-poll jsonl+JS
[P6 accept] PB-1…PB-6 matrix · overall OPEN until QA
            PB-1 ≥24h wall-clock · no early PASS
```

| phase | what | key live / design shas |
|-------|------|------------------------|
| P0 | queue/JetStream discovery | discovery `a2bd6c12…` · fold `eb4923dc…` |
| P1 | dry memory persist | receipt `a3d586b5…` |
| P2 | job SM bootstrap | receipt `8cb8c296…` · schema `49eb6c0b…` |
| P3 | restore copies on 180 | receipt `83d52513…` PASS 9/9 |
| P4 | node_id auth + 7-row registry | design `8b0a5e03…` · SEC `db62b335…` |
| P5 | job path E2E | contract `5d12e068…` · E2E `4ea146a8…` · QA `76b6d7da…` PASS_WITH_CAVEAT |
| P6 | acceptance matrix | design `4dea6030…` · measure `5de63c27…` · fold `c0ba7ac9…` · overall **OPEN** |

P6 measure snapshot (honest): PB-1 **IN_PROGRESS** · PB-2/3/5/6 **PASS** · PB-4 **NOT_RUN** · bus `jsonl_138` · NATS **NOT_CLAIMED**.

---

## Standing DENY (map)

- Dual-commander / 180 auto-failover  
- 193 as live T3 model-server service  
- Usable-42-TOPS / NPU-as-success  
- JetStream brain durable with consumers=0  
- customer_send / revenue queues / shell job_type  
- Early PB-1 PASS before ≥24.0h wall-clock  

**ARCH:** map only · no enqueue · no implement this turn.
