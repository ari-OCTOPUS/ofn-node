# STEP-B — fleet_facts → fleet_jobs promote bridge (ARCH design)

**mode:** DESIGN ONLY · **no implement** until SEC PASS + COMMANDER EXECUTE  
**stamp_aest:** 2026-09-16  
**after:** SSH Step A GREEN receipt `4c2215b9c6920f91b08a7186e2f05bc67ed99d6075900d7a317c225bd8bde812`  
**parent GO:** `SEC-INTERNAL-UNSTALL-GO-20260916.md` sha `514e8ab9…`  
**stall SoT:** OWNER-RO-STALL-ARCH `1733ffbd…` · inject surfaces `a4e4ef96…` · deep wiring `8149d40f…`  
**commander:** **138 sole** · dual-commander **DENY** · **HOLD customer_send** · **DENY commerce smuggle**

---

## 0 · Problem this step closes

Stall root D: RO / experience lands in `fleet_facts` (and glass) but **never becomes** a `fleet_job`.  
Step B designs the **missing promote edge** — still fail-closed, still compute-only.

```
fleet_facts.jsonl  --(promote_bridge on 138)-->  fleet_jobs.jsonl  --(P5 lease)-->  worker
     tier A memory              THIS DESIGN              P2/P5 SM              100/160/193/114
```

Step A only proved mesh SSH trust. Step B does **not** implement; SEC gates apply.

---

## 1 · Non-goals / DENY (commerce smuggle)

| DENY | why |
|------|-----|
| `type` ∈ ziman_*/studio_*/shopify_*/saba_*/publish/send/of_* | No business bind_roles yet (`8149d40f…`) |
| `customer_send=true` / `external_effects>0` without separate SEC GO | HOLD_EXTERNAL |
| Laptop / ARCH / 180 / 182 calling promote | dual-commander / shadow enqueue |
| Writing pack markdown bodies into `fleet_jobs.jsonl` | jobs schema poison (`a4e4ef96…`) |
| JetStream promote path | consumers=0; dual-poll DENY; bus stays `SHADOW_LOCAL_JSONL` |
| Auto-promote every fact | flood + side effects; require decision gate |
| Promoting `kind=owner_ro_deep_pack` straight to lease | intel ≠ work; optional later via explicit decision only |

**Allowlist job `type` for Step B pilot (compute only):**

| type | worker_node_id | notes |
|------|----------------|-------|
| `retrieve` | `100` | P5 pilot; preferred first promote |
| `echo_capability_probe` | `100` | already used in P5 E2E — OK if SEC lists it |
| `prep` | `160` | **deferred** until retrieve promote EXIT |
| `model_infer` | `193` | deferred; ≠ T3 service claim |
| `eval_batch` | `114` | deferred |

Any other `type` → **REJECTED** at promote time.

---

## 2 · Binding SoT

| artifact | sha / cite |
|----------|------------|
| Step A receipt (.md) | `4c2215b9…` |
| P1 memory schema | design + live path `/home/ari/ofn/state/fleet-memory/fleet_facts.jsonl` |
| `fleet_fact.v1` | HQ schema (sha re-hash on seal) |
| `fleet_decision.v1` | required gate between fact and job |
| `fleet_job.v1` live | `49eb6c0b…` |
| P5 contract | `5d12e068…` — jsonl_138 canonical |
| P4 auth | `8b0a5e03…` / SEC `db62b335…` — LEASE needs auth OK + lease_eligible |

---

## 3 · Promote contract (new schema — design)

### 3.1 `fleet_promote_request.v1` (input to bridge; not a job)

```json
{
  "schema": "fleet_promote_request.v1",
  "promote_id": "<uuid>",
  "at": "<utc>",
  "source_fact_id": "<fact_id>",
  "source_fact_body_hash": "<64 hex>",
  "bound_decision_id": "<decision_id>",
  "bound_decision_sha256": "<64 hex of decision row>",
  "desired_type": "retrieve",
  "desired_worker_node_id": "100",
  "input_hash": "<64 hex — hash of job input blob, NOT fact body dump>",
  "deadline": "<utc>",
  "external_effects": 0,
  "customer_send": false,
  "commander_node_id": "138",
  "bus": "SHADOW_LOCAL_JSONL",
  "notes": "step_b_promote"
}
```

### 3.2 Gate chain (all must PASS — fail-closed)

```
1. Reader process runs ON 138 only (mesh-local; no laptop enqueue)
2. source_fact exists in fleet_facts.jsonl · body_hash MATCH · not expired
3. fleet_decision.v1 exists · bound_payload_sha256 == hash(promote_request canonical)
   · verdict ∈ {PROMOTE_JOB, GO_PROMOTE} (SEC names exact enum)
   · expires_at > now · hold_external == true for this season
   · customer_send == false · commander_node_id == 138
4. desired_type ∈ allowlist (§1) · desired_worker_node_id matches type map
5. Registry: worker auth_status==OK ∧ lease_eligible==true (P4)
6. Idempotency: key = "promote:" + source_fact_id + ":" + desired_type + ":" + input_hash
   · if fleet_jobs already has key → ACK_SEEN · zero new job
7. external_effects == 0 · customer_send == false
8. bus == SHADOW_LOCAL_JSONL only (Step B)
```

Any fail → append **promote_reject** receipt (jsonl beside bridge) · **do not** touch fleet_jobs.

### 3.3 Emit `fleet_job.v1` (QUEUED)

On PASS, 138 SM appends one job:

| field | value |
|-------|-------|
| `type` | `desired_type` |
| `worker_node_id` | `desired_worker_node_id` |
| `input_hash` | from request (bounded compute input) |
| `idempotency_key` | §3.2 key |
| `state` | `QUEUED` |
| `attempt` | 0 |
| `commander_node_id` | `138` |
| `customer_send` | `false` |
| `external_effects` | `0` |
| `bus` | `SHADOW_LOCAL_JSONL` |
| `notes` | `promote_id=<…>;fact_id=<…>;decision_id=<…>` |

Then existing P5 path: LEASE→RUNNING→…→CLOSED. Bridge **stops** at QUEUED append + receipt.

### 3.4 Receipt `fleet_promote_receipt.v1`

Append-only under e.g. `/home/ari/ofn/state/fleet-memory/fleet_promotes.jsonl` (path final by PC/SEC):

`{promote_id, at, outcome: PASS|REJECT|ACK_SEEN, job_id?, reject_reason?, fact_id, decision_id, customer_send:false}`

Optional 180 RO copy after PASS; 182 may witness **receipt only**.

---

## 4 · Who runs what

| actor | may |
|-------|-----|
| **138** promote service / SM hook | READ facts+decisions · WRITE jobs QUEUED · WRITE promote receipts |
| **180** | quality on hypotheses; RO restore copy of receipts — **never** promote |
| **182** | Class-B witness of receipt — **never** memory/job writer |
| **100/160/193/114** | consume leases only — **never** promote |
| Laptop / ARCH / PC | design/docs; dry-run offline — **DENY** live promote until SEC EXECUTE; even then PC applies **on 138**, not from laptop as commander |

---

## 5 · Decision object (required middle tier)

Facts alone must not enqueue. Owner/COMMANDER/SEC path:

1. Fact appended (`kind` e.g. `promote_candidate` or internal probe fact — **not** commerce).  
2. `fleet_decision.v1` with `verdict=PROMOTE_JOB`, `hold_external=true`, short `expires_at`, `bound_payload_sha256` = canonical promote request.  
3. Bridge consumes decision **once** (one-use): after PASS or expiry, further promotes with same decision_id → REJECT `DECISION_SPENT`.

Aligns P1 tier B one-use / expiry rules.

---

## 6 · Commerce smuggle detectors (design checks)

Bridge MUST reject if any of:

- `desired_type` matches `(?i)ziman|studio|shopify|saba|publish|send|of_|fansly|marketing|revenue`  
- `notes` / input blob declares `customer_send` or outbound URL fan-out  
- `external_effects != 0`  
- fact `kind` ∈ `{owner_ro_deep_pack}` **without** intervening decision that explicitly allows “derive compute job from pack pointer” (default DENY)  
- worker_node_id ∈ `{138,180,182}` (commander/quality/witness not job workers)

---

## 7 · EXIT criteria (for later PC implement — not this turn)

1. SEC design review PASS / CONDITIONAL_PASS citing this packet sha.  
2. Schema files: `fleet_promote_request.v1` + `fleet_promote_receipt.v1` (+ optional decision verdict enum addendum).  
3. Dry selftest on 138: fact+decision → one QUEUED `retrieve`→100 → CLOSED · `external_effects=0`.  
4. Negative tests: commerce type DENY; expired decision DENY; duplicate idempotency ACK_SEEN; laptop enqueue DENY.  
5. No JetStream consumer created.  
6. QA seal before claiming “unstall complete.”  
7. Step C (if any) out of scope here.

---

## 8 · Relationship to SSH Step A

Step A GREEN (`4c2215b9…`) proves **138→workers BatchMode** so a future LEASED job can reach 100/160/193/114.  
Step B only designs **how QUEUED rows get created from facts**.  
Without Step B, mesh trust does not self-advance work. Without Step A, promote would queue jobs that cannot mesh-exec — both required eventually; **implement order: SEC on B design → PC dry promote → lease using Step A trust**.

---

## 9 · ARCH standing

- Design sealed this turn.  
- **No** live append to fleet_jobs / fleet_facts / promotes.  
- **No** commerce bind_roles invented as LIVE.  
- Await SEC gate on this document before PC implement.

**Schema note:** PC may place JSON Schema drafts beside `wiring/fleet-brain/schemas/` in a later apply; ARCH may add stub schemas in a follow-on only if COMMANDER assigns — **not** auto this packet.


## 10 · Schema stubs sealed with this design

| schema | sha256 |
|--------|--------|
| fleet_promote_request.v1 | `ffa63bda03c33d5273480f120b1024913076e9e8387413d36704c620b4019718` |
| fleet_promote_receipt.v1 | `7bbf716a13d9bb712c30f6fa2622ce34d717a7583775eaacfb3806b2cb78d379` |
