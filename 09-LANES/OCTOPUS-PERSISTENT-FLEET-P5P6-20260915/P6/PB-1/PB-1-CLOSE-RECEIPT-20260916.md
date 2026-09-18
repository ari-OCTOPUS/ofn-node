# PB-1 CLOSE RECEIPT — 2026-09-16

**status:** `PASS_WITH_CAVEAT`  
**window_start_utc:** `2026-09-15T04:03:36Z`  
**window_end_utc:** `2026-09-16T04:17:42Z`  
**wall_clock_hours:** **24.235** (≥24.0 gate MET)  
**gate_utc:** `2026-09-16T04:03:36Z`  
**customer_send:** `false` · **HOLD**  
**dual_commander:** `false` · commander `138`  
**bus:** `jsonl_138` · **nats_durability:** `NOT_CLAIMED` · consumers `0`  
**DENY:** NATS durable · usable-42 TOPS · overall laptop-free marketing claim · early/simulated 24h PASS

## Outcome (honest)

Wall-clock soak **≥24.0h** with live 138 continuity evidence (fleet_jobs.jsonl growth + CLOSED jobs through window).  
**Not** an unqualified PASS: laptop-off probe still **NOT_YET**; scheduler HB file **STALE**.

## Live 138 RO (close tick)

| metric | value |
|--------|-------|
| 138 up | yes (DietPi; uptime ≈27.6h) |
| fleet_jobs.jsonl lines | **350** (was 325 @ tick 02:35Z) |
| last CLOSED | `job-65128c52ac684bb5` ack_at `2026-09-16T04:01:37Z` worker **100** |
| CLOSED after window start | **54** |
| customer_send | **false** (hold_external_sot + may_authorize_sot) |
| dual_commander | **false** (deny list + commander_node_id=138) |

## Sample job (start chain)

`job-432175b362774fae` → **CLOSED** on 100 · effects=0 · result_hash `20f96048585c74e3…` · ack `2026-09-15T04:03:37Z` · jsonl lines 22–27.

## Prior evidence

| artifact | sha / note |
|----------|------------|
| matrix before | `69521d9f77424d5954aa08ffa62375b9e3335e5e21490697524b3d7823a1213a` · PB-1 **IN_PROGRESS** · wall field **18.4564** (stale) |
| intermediate | `5937c980aa852cf019da522caf6bb083d7d9cf1c905de0365550554db356aa7b` · elapsed_at_write **22.5361** · last_tick `2026-09-16T02:35:46Z` |
| soak routine | `pb-1-24h-soak-watch` ticks ok (incl. `b8129547…`) |

## Caveats

- laptop_dependency_probe remains NOT_YET — no deliberate laptop-off / isolation probe during soak window; critical_path inventory asserts laptop_required=false but full probe not executed
- fleet-scheduler/scheduler-heartbeat.json stale (at=2026-09-15T04:31:26Z) — STALE file ≠ continuous HB capability; continuity evidenced instead by jsonl CLOSED growth through window
- NATS_DURABILITY=NOT_CLAIMED; jetstream_consumers=0 — DENY durable NATS claim
- DENY usable-42 TOPS (PB-5 nominal only; not in scope of this close)
- overall matrix remains OPEN (PB-4 NOT_RUN; QA overall seal still required; no laptop-free marketing claim)
- HOLD customer_send intact

## Matrix update note

PB-1 row: `IN_PROGRESS` → `PASS_WITH_CAVEAT`; set `ended_at`/`wall_clock_hours`; witness → this CLOSE receipt; **overall remains OPEN**.

— PC_CLOSE · 2026-09-16T04:17:42Z · HOLD customer_send

**receipt_json_sha256:** `8a24e456395a808397f49f1e660934ea565017e54ce41dc9b9222db9ad9c03fb`
