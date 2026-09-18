# T2 matrix + worker-connect fold (ARCH · 2026-09-15)

**trigger:** PC_worker fold request  
**HOLD customer_send** · no ARCH enqueue · **138 sole commander** · no dual-commander

## P0 (already folded)

`P0-DISCOVERY.json` `a2bd6c12…` · JetStream YES · 8 streams · 0 consumers — see `P0-JETSTREAM-FOLD` `eb4923dc…`.

## T1

LANE-REPORT now stamps **T1 PASS** 4/4 (docs lag closed). Receipts `T1-RECEIPTS/`. LANE-REPORT sha (current) `2fbe1e04bc52be4f0f6353064f26c558d806ad87ec8a4818906fe124f9a7239a`.

## T2 NPU matrix — expanded

| artifact | sha256 |
|----------|--------|
| `T2-PILOT/T2-NPU-INFERENCE-MATRIX.json` | `d13f19285482a2a346b8b26979f2341c8f7a4ccef50c281967e47cabfc469df5` |

**6/7 PASS** · **138 NOT_RUN** (organism optional).

| node | status | mean_ms | fps |
|------|--------|---------|-----|
| 138 | NOT_RUN | — | — |
| 180 | PASS | 19.83 | 50.429 |
| 182 | PASS | 16.815 | 59.472 |
| 100 | PASS | 20.638 | 48.454 |
| 160 | PASS | 20.613 | 48.513 |
| 193 | PASS | 19.909 | 50.23 |
| 114 | PASS | 21.954 | 45.549 |

**DENY:** usable-42-TOPS / fleet success = CPU/NPU fill. Measured inference ≠ model-server service.

## Worker connect (idle four)

SEC cite `0a634c9d…` (LANE-REPORT). Receipts under `WORKER-CONNECT/`.

| node_id | role (HB) | commander | may_authorize | status |
|---------|-----------|-----------|---------------|--------|
| 100 | `retrieve` | false | false | **LIVE_HEARTBEAT** |
| 160 | `prep` | false | false | **LIVE_HEARTBEAT** |
| 193 | `model-server` (label in HB) | false | false | **LIVE_HEARTBEAT** — **not** T3 live model-server service |
| 114 | `eval` | false | false | **LIVE_HEARTBEAT** |

Evidence samples: `octopus_worker_heartbeat.v1` with `node_id` + `boot_id`; timer `octopus-worker-heartbeat.timer` on idle four only (not 180/182).

### Bind map reconcile vs `WORKER-BIND-MAP` `6ff4ee5a…`

| prior | now |
|-------|-----|
| BOUND_DESIGN | **LIVE_HEARTBEAT** (timer + 138 puller round-trip) |
| LEASE_ELIGIBLE / fleet job worker | **still DENY** until P1 dry persist + P2 contract + node_id auth gate complete |
| 193 `model_infer` live service | **still DENY** — heartbeat role string ≠ octopus model-server unit (T3 owed) |

## Explicit non-claims

- No dual-commander  
- No promote 193 to verified model-server without T3 receipt  
- No invent 42 TOPS utilization  
- No fleet-brain job enqueue from this fold
