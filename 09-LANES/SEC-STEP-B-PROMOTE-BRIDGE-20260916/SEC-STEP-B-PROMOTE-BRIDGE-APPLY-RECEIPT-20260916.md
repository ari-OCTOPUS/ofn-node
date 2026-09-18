# SEC Step B APPLY RECEIPT — promote bridge (retrieve→100 pilot)

- **task_id:** SEC-STEP-B-PROMOTE-BRIDGE-APPLY
- **stamp_aest:** 2026-09-16T13:06:34+10:00
- **EXECUTE:** `SEC-STEP-B-PROMOTE-BRIDGE-EXECUTE-20260916.md` sha `f506b159ee67bccbe138a1791d4a0a40d1ccfb6644fa5c0e02873256aeb2ffd9` (**MATCH**)
- **ARCH design:** `STEP-B-PROMOTE-BRIDGE-DESIGN-20260916.md` sha `87fc6f3d7beff1bf137763654579ccd7ee92e2655aa4069e58e2cee7c403d219` (**MATCH**)
- **SSH Step A:** sha `4c2215b9c6920f91b08a7186e2f05bc67ed99d6075900d7a317c225bd8bde812` (**MATCH** · GREEN)
- **outcome:** **ok**

## 1. Design sha MATCH

| artifact | sha256 | result |
|----------|--------|--------|
| EXECUTE | `f506b159ee67bccbe138a1791d4a0a40d1ccfb6644fa5c0e02873256aeb2ffd9` | **MATCH** |
| DESIGN | `87fc6f3d7beff1bf137763654579ccd7ee92e2655aa4069e58e2cee7c403d219` | **MATCH** |
| SSH A | `4c2215b9c6920f91b08a7186e2f05bc67ed99d6075900d7a317c225bd8bde812` | **MATCH** |

## 2. Schema paths + shas

| schema | HQ path | 138 path | sha256 |
|--------|---------|----------|--------|
| fleet_promote_request.v1 | `wiring/fleet-brain/schemas/fleet_promote_request.v1.schema.json` | `/home/ari/ofn/state/fleet-memory/schemas/…` | `ffa63bda03c33d5273480f120b1024913076e9e8387413d36704c620b4019718` (**MATCH** design stub) |
| fleet_promote_receipt.v1 | `wiring/fleet-brain/schemas/fleet_promote_receipt.v1.schema.json` | `/home/ari/ofn/state/fleet-memory/schemas/…` | `7bbf716a13d9bb712c30f6fa2622ce34d717a7583775eaacfb3806b2cb78d379` (**MATCH** design stub) |

Bridge: `/home/ari/ofn/state/fleet-memory/fleet_promote_bridge.py` sha `cd00c2fcce84dfdbda50fc23fb040631f6e216e58ccda759ded095f7faa2eea6`

## 3. Dry/E2E

| field | value |
|-------|-------|
| fact_id | `fact-b1e8d328bff54e46` |
| decision_id | `dec-fc4948d35b5a4e40` |
| promote_id | `prm-3bb4aada75c44519` |
| job_id | `job-d7af47b150bc4135` |
| worker | **100** |
| type | **retrieve** |
| path | QUEUED→LEASED→RUNNING→ACK_RESULT→PERSISTED→**CLOSED** (P5 SM) |
| outcome | **PASS** |
| external_effects | **0** |
| customer_send | **false** |
| bus | **SHADOW_LOCAL_JSONL** |
| receipt_id | `rcpt-stepb-job-d7af47b150bc4135` |

## 4. Negative-test results

| test | result | detail |
|------|--------|--------|
| commerce type DENY (`shopify_sync`) | **PASS** | `COMMERCE_TYPE_DENY type=shopify_sync` |
| commerce type DENY (`ziman_gallery_push`) | **PASS** | `COMMERCE_TYPE_DENY type=ziman_gallery_push` |
| duplicate idempotency ACK_SEEN | **PASS** | job_id `job-d7af47b150bc4135` · outcome ACK_SEEN |
| expired decision DENY | **PASS** | `DECISION_EXPIRED` |
| non-138 enqueue DENY | **PASS** | `NON_138_ENQUEUE local_node_id=180` |
| prep→160 deferred DENY | **PASS** | `PILOT_DEFERRED type=prep worker=160` |

## 5. Proofs

- `external_effects=0` · `customer_send=false` · `commander_node_id=138` · `bus=SHADOW_LOCAL_JSONL`
- **No** JetStream promote path · **no** consumer create (this apply)
- Selftest result sha `18bbdc17c272bfac89e51f73aa9adb44106827d98fbaced09c3a617e8a46bde7`

## 6. Confirm prep/160 **not** enabled

- Pilot enablement: `retrieve→100` (+ optional `echo_capability_probe→100`)
- `prep→160` / `model_infer→193` / `eval_batch→114` → **PILOT_DEFERRED** (proven)

## Paths touched (138)

- `/home/ari/ofn/state/fleet-memory/fleet_promote_bridge.py` (**created**)
- `/home/ari/ofn/state/fleet-memory/step_b_selftest.py` (**created**)
- `/home/ari/ofn/state/fleet-memory/schemas/fleet_promote_{request,receipt}.v1.schema.json`
- `/home/ari/ofn/state/fleet-memory/fleet_decisions.jsonl` (**created**)
- `/home/ari/ofn/state/fleet-memory/fleet_promotes.jsonl` (**created**)
- `/home/ari/ofn/state/fleet-memory/promote_decision_spent.json` (**created**)
- `/home/ari/ofn/state/fleet-memory/fleet_facts.jsonl` (append promote_candidate facts)
- `/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl` + `idempotency_index.json` (one retrieve job)

## DENY intact

commerce · JetStream promote · prep/160·193·114 widen · laptop/180/182 promote writer · dual-commander · power-off 138 · customer_send=true · flood auto-promote


— PC apply under SEC-STEP-B-PROMOTE-BRIDGE-EXECUTE · retrieve→100 pilot · outcome **ok** · no secrets

- **receipt_md_sha256:** `cb1443ab4c35536aabc75086b7d6abbb823bb2c5885784bca660b7c1f267dc29`  *(hash of body above this line)*
