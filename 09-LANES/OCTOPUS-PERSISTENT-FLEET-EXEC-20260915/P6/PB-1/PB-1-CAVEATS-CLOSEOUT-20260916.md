# PB-1 CAVEATS CLOSE-OUT — 2026-09-16

**status:** `PASS_WITH_CAVEAT` (caveats partially closed; not invent overall PASS)  
**task:** OWNER GO Priority B — PB-1 caveats close-out RO+fix  
**HOLD customer_send:** intact · **customer_send:** false · **dual_commander:** false · commander **138**  
**138 powered off:** **NO** · laptop power-off: **NO** (quiet no-new-SSH only)

Prior CLOSE json sha `8a24e456…` · matrix was `ac4dbb18…`.

## 1) laptop_dependency_probe → **PROBED_SHORT_WINDOW_PASS**

| field | value |
|-------|-------|
| method | deliberate quiet window — **no new laptop SSH** to 138 |
| laptop | machineId `2edb534d-…` · LAN **192.168.0.191** |
| start | `2026-09-16T04:32:12Z` · FJ lines **356** · last CLOSED `job-d6b25156…` @ `04:31:37Z` |
| end | `2026-09-16T05:16:38Z` · FJ lines **362** · CLOSED count **58** |
| quiet | **~44.4 min** with no new laptop→138 SSH |
| proof CLOSED | timer `05:01:36Z` → **`job-ddd3364e9d3d4c3d` CLOSED** @ `05:01:37Z` worker **193** model_infer · effects=0 · customer_send=false |
| NOT claimed | full laptop power-off / unreachable-LAN; overall laptop-free marketing |

## 2) scheduler-heartbeat → **STALE_REMAINS** (not refreshed)

| field | value |
|-------|-------|
| file | `/home/ari/ofn/state/fleet-scheduler/scheduler-heartbeat.json` |
| file `at` | `2026-09-15T04:31:26Z` (unchanged) |
| timer | **healthy** — active/waiting · LastTrigger `05:01:36Z` · Result=success |
| ExecStart | `capaware_scheduler.py` (closes jobs; **does not write HB**) |
| HB writer | `fleet_scheduler.py` — **not** unit ExecStart |
| why STALE remains | refuse hand-edit / invent fresh HB while writer unwired; continuity via jsonl CLOSED |

## 3) NATS → **NOT_CLAIMED** (consumers **0**)

| check | result |
|-------|--------|
| nats CLI | absent |
| nats-server unit | **absent** |
| ports 4222/8222 | none |
| process | none |
| jetstream_consumers | **0** |
| durability claim | **NOT_CLAIMED** — DENY invent durable |

## 4) Matrix note (honest)

PB-1 stays **`PASS_WITH_CAVEAT`**. overall **OPEN**. Update caveats/notes only — **do not** invent PASS / laptop-free / NATS durable / fresh HB.

## DENY / HOLD

- DENY NATS durable · DENY usable-42 TOPS · DENY overall laptop-free marketing  
- DENY claim continuous HB capability from STALE file  
- **HOLD customer_send**

— PB-1 caveats close-out · 2026-09-16T05:17:30Z · HOLD customer_send

**receipt_json_sha256:** `1b2ef8da1322e84eecacfc255a91e78a5c3650639f03673d8bc00252feb92479`
