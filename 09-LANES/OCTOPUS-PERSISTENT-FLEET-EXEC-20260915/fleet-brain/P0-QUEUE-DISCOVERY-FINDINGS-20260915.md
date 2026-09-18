# P0 — Queue discovery findings (OWNER GO FULL · map)
**stamp_aest:** 2026-09-15  
**phase:** P0 DESIGN · docs/interfaces · **no live fleet-brain enqueue** until SEC EXECUTE-READY on proposal `e5cacff0…`  
**HOLD customer_send:** true · **no dual-commander** (138 sole commander)  
**cites:** ARCH `17eb76e1…` · T0 `e62c7851…` / `ca17b6cd…` · `DECISION-brain-queue-ram.md` · `worker.py` sha prefix `0d1afd6f…`

## T1 heartbeats

**T1 NOT_RUN** in `ACTIONS-LOG.md` (post-T0 docs only). Role reconcile uses **T0 only** until PC files T1 heartbeat receipts.

## Surfaces found (reuse-first)

| id | path / host | durability | consumer | fit for fleet brain |
|----|-------------|------------|----------|---------------------|
| **Q-BRAIN-RAM** | `ofn/worker.py` `WorkQueue` + ledger shadow | RAM + THINK_QUEUED ledger; **no auto-replay** | `Worker.step` on 138 | Thinking only; **not** cross-node dispatch |
| **Q-AUTONOMY** | `/home/ari/ofn/state/autonomy/queue.jsonl` | append jsonl | autonomy-supervisor | Task state transitions — keep separate |
| **Q-OWNER-REPLY** | `OWNER-QUEUE.md` + `reply_queue_bridge.py` | file + idempotency_key | glass/TG owner | Owner proposals — keep separate; `grants_send=false` |
| **Q-REVENUE-SEND** | `state/revenue-drive/send_*` | local | revenue-drive | **DENY reuse** (customer_send HOLD) |
| **Q-NATS-182** | `nats-server.service` on **182** (T0) | persistence/JetStream **UNKNOWN** | sensorium/fusion stack likely | **Candidate bus** for fleet jobs after JetStream+consumer proof |
| **Q-NATS-138** | nats-server | **inactive** on 138 | — | Do not assume local NATS |
| **Q-CONTROL-138** | octopus-router / verify-dispatcher / supervisor | process | 138 control plane | Map job_id through existing control before new dispatcher |

## Existing Job shape (brain) — evidence

`Job`: `tenant, task, prompt, idem_key, max_rung, estimated_tokens, attempts, owner_approved_deep, not_before`  
`WorkQueue.submit` dedupes `(tenant, idem_key)`; FIFO with backoff; requeue to tail.

## Fleet job contract (target interface — design only)

Extend **without** replacing Q-BRAIN-RAM:

```
FleetJob {
  job_id, idempotency_key, job_type,
  input_ref, input_hash,
  required_capability, target_node_id,
  deadline, attempt,
  lease_owner, lease_expiry,
  resource_budget,
  result_ref, result_hash, receipt_id,
  commander_node_id = "138"   # immutable — no dual-commander
}
```

**Discovery remaining (P0 exit):**
1. Prove JetStream (or not) on 182; list stream/consumer names  
2. Trace one existing verify-dispatcher job_id end-to-end if any  
3. Document MQTT vs NATS ownership on 182  
4. Fold T1 heartbeats when PC files them  

**P0 recommendation:** shadow fleet jobs on **jsonl ledger on 138** first (append-only), optionally publish to NATS-182 after SEC PASS — do **not** auto-replay RAM WorkQueue.


---

## Addendum A — SEC EXECUTE-READY + JetStream READ (2026-09-15)

**SEC:** `GO-PERSISTENT-FLEET-EXEC` sha `52887e1a…` — phased P0→P6 PASS; ARCH map `17eb76e1…` MATCH.  
**JetStream READ:** see `P0-JETSTREAM-READ-20260915.md` — still **UNKNOWN** (182 SSH deny; :8222 timeout from 138).  
**Live apply:** PC starts P0 discover; ARCH folds receipts only — no enqueue.


---

## Addendum B — P0 live JetStream YES (2026-09-15)

**Receipt:** `P0-DISCOVERY.json` sha `a2bd6c12…` (lane `OCTOPUS-PERSISTENT-FLEET-EXEC-20260915/P0/`).  
**Fold packet:** `P0-JETSTREAM-FOLD-20260915.md` (supersedes UNKNOWN `c6bba165…`).

| verdict | value |
|---------|-------|
| JETSTREAM | **YES** (182) |
| consumers | **0** → `PARTIAL_ZERO_CONSUMERS` |
| streams (8) | FEATURE LEG OBSERVATION SENSORIUM SENSOR_HEALTH WORLD AUDIT COMMAND |
| NATS 138 | **ABSENT** (unit not found) |
| :8222 LAN | UNREACHABLE (localhost bind on 182) |

No fleet-brain job stream yet. No enqueue.
