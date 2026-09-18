# P5 — Job-path contract (OWNER GO · ARCH design)

**stamp_aest:** 2026-09-15 ~13:49  
**mode:** DESIGN · docs/interfaces · PC implements · SEC gates · QA seals  
**aligned_to:** `NEXT-AGENT-MEGAPROMPT.md` sha `7ab84e03df7ca708abeb8cb4178c2d7cf10bc00e9b17a20d2c41588c26508f07`  
**EXEC umbrella:** `52887e1a…` (live apply still phased; this packet = NEXT P5 job-path)  
**commander:** **138 sole** · dual-commander **DENY** · **HOLD customer_send**  
**DENY:** revenue-drive / money APPROVE_PAT queues · shell-as-job_type · dual poll

---

## 0. Binding SoT

| artifact | sha / cite |
|----------|------------|
| NEXT P5→P6 megaprompt | `7ab84e03…` |
| Live `fleet_job.v1` schema | `49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59` |
| P2 SM design | `7323758d…` |
| P2 dry bootstrap | `8cb8c296…` — ledger `/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl` |
| P4 auth | SEC `db62b335…` · receipt `d8844e96…` · LEASE_ELIGIBLE 100/160/193/114 |
| JetStream P0 | `a2bd6c12…` — YES · **consumers=0** · no brain stream yet |

---

## 1. Verdict — preferred bus

| option | stronger for first job_type? | decision |
|--------|------------------------------|----------|
| **P2 shadow/live jsonl SM on 138** | **YES** — SM+tests+schema live; single writer 138; no dual poll | **CANONICAL for P5 EXIT** |
| New JetStream consumer on 182 | Not yet — consumers=0; no `FLEET_JOB` stream; dual-poll risk if HB path + JS both lease | **OPTIONAL later** — only with SEC approve + exactly one durable |

**Do not** claim NATS durable for brain jobs until `consumers>=1` proof on a dedicated fleet stream.

---

## 2. One job_type first (pilot)

| field | value |
|-------|-------|
| Live schema `type` | `retrieve` |
| Capability | knowledge retrieve (node **100**) |
| Why first | smallest side effects; aligns role retrieve; `external_effects=0` |
| Later types | `prep`→160 · `model_infer`→193 · `eval_batch`→114 (same path, new `type`) |

Proposal names (`job_type`, `target_node_id`, …) map to **live** fields:

| proposal | live `49eb6c0b…` |
|----------|------------------|
| `job_type` | `type` |
| `target_node_id` | `worker_node_id` |
| `required_capability` | implied by `type` (+ registry capability) |
| `bus` | `SHADOW_LOCAL_JSONL` for pilot (required) |

---

## 3. Canonical path — producer → queue → consumer → receipt

```
[producer] 138 commander only
    fleet_job_sm → append QUEUED row (idempotency_key unique)
        ↓
[queue]    /home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl
           + idempotency_index.json
        ↓
[lease]    138 offers LEASED to worker_node_id iff
           registry auth_status=OK ∧ lease_eligible=true
           ∧ before deadline ∧ not dual-commander
        ↓
[consumer] worker 100 (retrieve) — ACK lease → RUNNING
           compute result → result_hash (external_effects=0)
        ↓
[receipt]  138 ACK_RESULT → PERSISTED → CLOSED
           receipt_id on 138; optional 180 RO copy later
           optional 182 Class-B witness of receipt artifact only
```

### Roles (fixed)

| node | role | P5 part |
|------|------|---------|
| **138** | commander / queue owner / receipt writer | producer + lease authority |
| **100** | retrieve | **pilot consumer** |
| **160** | prep | deferred job_type |
| **193** | model_infer | deferred (≠ T3 model-server service) |
| **114** | eval_batch | deferred |
| **180** | quality / restore_copy_RO | never commander / never lease issuer |
| **182** | lab_witness / NATS host | witness receipts only — not second memory writer |

### Guards (fail-closed)

- `commander_node_id=138` · `customer_send=false` · `type≠shell`  
- QUEUED→LEASED: P4 registry OK (SEC)  
- Crash mid-flight → **UNKNOWN** (no invent CLOSED)  
- Idempotent retry only; no blind non-idempotent effects  
- Single consumer of leases for a job_id — **no dual poll** (jsonl lease owner exclusive)

---

## 4. Optional JetStream design (not default)

Only if SEC approves **after** jsonl P5 EXIT (or explicit stronger need):

| item | value |
|------|-------|
| Stream | `FLEET_JOB` (new — **DENY** hijack SENSORIUM/AUDIT/COMMAND) |
| Subjects | `octopus.fleet.job.>` |
| Durable consumer | **exactly one** name: `fleet_job_worker_v1` |
| Deliver | to 138 dispatcher **or** single worker pull — **never both** |
| Proof | `consumers>=1` · deliver · ACK · idempotent redelivery receipt |
| Fallback | jsonl remains SoT until proof |

If both jsonl and JS active → **DENY** (dual path / dual poll).

---

## 5. DENY list

- Revenue-drive / send_queue / APPROVE_PAT money queues  
- Dual-commander / 180 auto-failover  
- Dual getUpdates / dual lease pollers  
- Claiming JetStream brain durable with consumers=0  
- Production enqueue of `prep`/`model_infer`/`eval_batch` before pilot `retrieve` CLOSED+QA  
- customer_send / GO-B4  
- Free-form shell job_type  

---

## 6. P5 EXIT (PC + QA)

1. One end-to-end: 138 QUEUED → 100 LEASED→RUNNING → receipt CLOSED · `external_effects=0`  
2. QA seal on receipt chain  
3. Bus = jsonl (or JS only if §4 proven)  
4. LANE-REPORT updated  
5. **STOP** before P6 acceptance claims  

---

## 7. ARCH standing

Contract only. No live enqueue from ARCH. PC implements; SEC gates JS consumer create; QA seals.


---

## Alignment — SEC-P5-JOB-PATH-GATE `3e8bd525…` (2026-09-15)

**SEC SoT:** `/workspace/octopus-hq/wiring/SEC-P5-JOB-PATH-GATE-20260915.md`  
sha `3e8bd525748531e747761cfaa4345b8a39af8758ea3bf7c565e3da1ea8ba27ec`  
**Verdict:** **CONDITIONAL_PASS** — this addendum wins for the job-path slice.

### Match table

| SEC rule | ARCH contract |
|----------|---------------|
| Primary bus jsonl on 138 | §1 CANONICAL · pilot `retrieve`→100 |
| JetStream ≤1 named durable + proof else NOT_CLAIMED | §4 optional `fleet_job_worker_v1`; no dual-poll with jsonl |
| Leases only OK+lease_eligible | §3 guards · P4 |
| DENY revenue / dual-commander / shell | §5 |
| EXIT E2E + QA; else `bus=jsonl` + NATS_DURABILITY=NOT_CLAIMED | §6 |

**No change to preferred path.** PC implements under SEC CONDITIONAL_PASS. ARCH design only.
