# P3 — 180 restore-copy design (ARCH · RO docs)

**stamp_aest:** 2026-09-15 ~13:36  
**after:** P2 dry bootstrap `8cb8c296…`  
**SEC:** EXEC `52887e1a…` P3 — 138 writer + 180 verified restore **copies**  
**mode:** DESIGN + schema · **180 RO** · PC/organism apply drills  
**commander:** **138 sole** · dual-commander **DENY** · auto-failover 180→commander **DENY**  
**HOLD customer_send**

## Binding SoT

| artifact | cite |
|----------|------|
| EXEC P3 | `52887e1a…` EXIT = restore readback MATCH manifest |
| Memory path | P1 `299c7e90…` — optional 180 restore-copy after 138 persist |
| QA PB-3 | `QA-PERSISTENT-BRAIN-4TESTS-ACCEPTANCE-DRAFT` — verified backup → separate path → RPO/RTO |
| Umbrella | `17eb76e1…` — 180 = quality + recoverable memory copies |

## Roles (immutable)

| node | P3 role |
|------|---------|
| **138** | **primary writer** of fleet-memory + fleet-jobs SoT |
| **180** | **read-only restore-copy host** + quality gate (tier C) — **never** commander / sole writer |
| laptop | observe/dev only — **DENY** critical path |

## Scope of what gets copied

| store (138) | copy to 180 | notes |
|-------------|-------------|-------|
| `state/fleet-memory/fleet_facts.jsonl` (+ decision/hyp if present) | verified snapshot under **separate** path | append-only friendly |
| `state/fleet-jobs/` ledger+index (optional) | separate path | not production enqueue |
| `memory.sqlite` (if in backup_job scope) | **Online Backup API / restore_job only** | **DENY** raw copy of open DB |

## Interfaces

### `fleet_restore_manifest.v1`

Schema: `schemas/fleet_restore_manifest.v1.schema.json`  
Required: `source_node_id=138`, `copy_node_id=180`, `backup_method`, `snapshot_sha256`, `verified=true` before restore, `dual_commander=false`.

### Apply flow (PC — RO on 180 until verify)

```
1. On 138: create snapshot (online backup or verified jsonl tar)
2. Compute snapshot_sha256 + write manifest (verified=false)
3. Transfer to 180 separate path (e.g. /home/ari/ofn/state/fleet-memory-restore-copies/<manifest_id>/)
4. On 180: verify sha MATCH → set verified=true (still RO — no promote to writer)
5. Optional restore drill into NON-live dir on 180 (never overwrite 138 live; never make 180 commander)
6. Readback sample keys/hashes MATCH → record RPO_seconds / RTO_seconds
7. Receipt: manifest sha + readback log + RPO/RTO
```

## DENY

- Dual-commander / auto failover 138→180  
- Power off 138 for this drill  
- Open-file sqlite copy as “backup”  
- Treating 180 mirror as sole SoT  
- Laptop in critical path  
- customer_send / revenue queues  
- Restoring onto live 138 writer without scoped GO  

## EXIT (for PC)

Restore readback **MATCH** manifest receipt + RPO/RTO recorded. ARCH provides design/schema only.

**Schema sha:** `51900041868b2c7591fc0ffb3470453ed82af864da3a867ec0dd5769d6170e86`
