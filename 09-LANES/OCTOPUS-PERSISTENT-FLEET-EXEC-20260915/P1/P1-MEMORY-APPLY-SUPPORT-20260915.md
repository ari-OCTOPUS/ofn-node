# P1 memory schema — APPLY SUPPORT (ARCH · docs+schemas)

**stamp_aest:** 2026-09-15 ~13:31  
**after:** P0 fold `a2bd6c12…` (JetStream YES; 0 consumers)  
**SEC:** EXEC `52887e1a…` P1 — design→implement non-TCB / append-only; dry persist `external_effects=0`  
**ARCH:** schemas authored · **PC/organism applies** · no dual-commander · HOLD customer_send

## Schemas (ready)

| file | purpose |
|------|---------|
| `schemas/fleet_fact.v1.schema.json` | tier A |
| `schemas/fleet_decision.v1.schema.json` | tier B (W21-aligned bind/expiry/hold_external) |
| `schemas/fleet_hypothesis.v1.schema.json` | tier C (requires `source_fact_ids`; 180 gate) |

Design SoT remains `P1-MEMORY-SCHEMA-20260915.md` sha `299c7e90…`.

## Suggested placement (PC)

Non-TCB first (lane bag), then organism copy if GO:

1. Lane: `F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-EXEC-20260915\P1\schemas\`  
2. Optional HQ mirror already at `/workspace/octopus-hq/wiring/fleet-brain/schemas/`  
3. On 138 (append-only dry): `…/state/fleet-memory/` jsonl **or** documented sqlite table — **do not** overwrite sole `memory.sqlite` without scoped GO  
4. 180: verified **copy** path only after dry persist on 138

## Dry persist recipe (EXIT for P1)

1. Validate one sample of each tier against schemas (local).  
2. Append one `fleet_fact.v1` row with `external_effects=0`, `customer_send=false`, `commander_node_id=138`.  
3. Receipt: path + sha of sample + schema shas.  
4. **DENY:** promote C→A without `quality_gate=pass_180`; expired B as live GO; 180 sole writer; revenue/send fields.

## Bus note post-P0

JetStream YES does **not** auto-select NATS for memory rows. Prefer **138 local append-only** for P1 EXIT; optional later publish to a **new** subject/stream — DENY stuffing facts into SENSORIUM/AUDIT without ownership review.

## ARCH standing

Map/schema support only. No live mutate from ARCH unless COMMANDER assigns post-SEC with explicit apply verb.
