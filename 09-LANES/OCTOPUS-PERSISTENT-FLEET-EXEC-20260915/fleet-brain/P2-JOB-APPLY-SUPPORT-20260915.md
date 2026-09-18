# P2 job contract — APPLY SUPPORT (ARCH · docs+schema)

**stamp_aest:** 2026-09-15 ~13:35  
**after:** P1 dry persist `a3d586b5…` · P0 JetStream YES (0 consumers)  
**design SoT:** `P2-JOB-STATE-MACHINE-20260915.md` sha `7323758d2a9ec7588e3f3b391370eef5c47628a996df68283429be33f5fbae20`  
**SEC:** EXEC `52887e1a…` P2 — implement contract; EXIT = idempotency + UNKNOWN tests; **no production enqueue** yet  
**commander:** **138 only** · dual-commander **DENY** · HOLD customer_send

## Schema

| file | sha (compute on seal) |
|------|------------------------|
| `schemas/fleet_job.v1.schema.json` | `49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59` (live; was draft `49eb6c0b… (live)`) |

## Bus (fail-closed)

| option | status | use for P2 EXIT |
|--------|--------|-----------------|
| Shadow jsonl on 138 | **RECOMMENDED** | `…/state/fleet-jobs/fleet_jobs.jsonl` append-only |
| RAM WorkQueue | shadow only | **DENY** auto-replay / double-charge |
| NATS-182 JetStream | engine YES · **0 consumers** · no fleet-job stream | **DENY** claim durable brain bus until new stream+consumer receipt |
| Existing SENSORIUM/AUDIT/COMMAND | occupied | **DENY** hijack without ownership review |

## State machine (apply as guards, not loose strings)

```
QUEUED → LEASED → RUNNING → ACK_RESULT → PERSISTED → CLOSED
         ↘ FAILED → (retry) → QUEUED
         ↘ UNKNOWN | EXPIRED | REJECTED
```

ACK ≠ success. Unclear crash → **UNKNOWN** (never invent CLOSED).

## PC apply checklist (EXIT)

1. Place `fleet_job.v1.schema.json` under lane `P2/schemas/` and optionally 138 non-TCB mirror.  
2. Unit/table tests (local or on 138 dry):  
   - duplicate `idempotency_key` → single logical job  
   - kill mid-LEASED/RUNNING → UNKNOWN or FAILED + no dup `external_effects`  
   - `job_type=shell` → **REJECTED** / schema fail  
   - `commander_node_id≠138` → **REJECTED**  
   - `customer_send=true` → **REJECTED**  
3. Optional: one **synthetic** job row append-only ending CLOSED with `external_effects=0` — **not** production worker dispatch.  
4. Receipt: path+sha of tests + optional sample job + schema sha.  
5. **STOP** before P3 unless COMMANDER advances.

## Role capability map (post-P1 align)

| node | capability for `required_capability` |
|------|--------------------------------------|
| 100 | `retrieve` / `knowledge_retrieve` |
| 160 | `prep` / `knowledge_prep` |
| 193 | `model_infer` (HB may say model-server — **not** T3 service) |
| 114 | `eval_batch` |

QUEUED→LEASED still needs SEC `node_id` auth — heartbeat LIVE ≠ auth PASS alone.

## ARCH standing

Schemas + this support only. No live mutate / enqueue from ARCH.

## LIVE SCHEMA SoT (folded 2026-09-15)

**Canonical:** 138 `…/fleet-jobs/schemas/fleet_job.v1.schema.json` sha **`49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59`**.  
ARCH draft `d60c2e6e…` superseded — see `FLEET-JOB-SCHEMA-LIVE-FOLD-20260915.md`.
