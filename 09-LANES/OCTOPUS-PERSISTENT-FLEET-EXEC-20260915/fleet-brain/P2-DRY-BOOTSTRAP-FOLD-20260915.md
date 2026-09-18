# P2 dry bootstrap fold (ARCH · 2026-09-15)

**receipt:** `P2-DRY-BOOTSTRAP-RECEIPT.json` sha `8cb8c296039209c25730106c571d4a489ff87d1982939b6942a364c7075166fc`  
**mode:** DRY_BOOTSTRAP · `external_effects=0` · commander 138  
**bus:** `SHADOW_LOCAL_JSONL` · `nats_durability=NOT_CLAIMED` (JetStream consumers=0)

## Paths (138)

| item | path |
|------|------|
| ledger | `/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl` |
| idempotency index | `…/idempotency_index.json` |
| module | `…/fleet_job_sm.py` |
| schema | `…/schemas/fleet_job.v1.schema.json` |

## Tests PASS

idempotency · UNKNOWN_no_silent_success · shell_job_type_REJECTED · happy_CLOSED_external_effects_0

## Cite

design SM `7323758d…` · ARCH support `a6079710…` · EXEC `52887e1a…`  
**STOP before P3** (PC). No production enqueue.
