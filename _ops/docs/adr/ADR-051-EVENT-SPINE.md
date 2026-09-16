# ADR-051: Unified Event Spine (UNIFY U-1 + U-2)

## Status: ACCEPTED (2026-09-08, MP-UNIFY-01)

## Context
12+ modules write to events.jsonl independently. No unified identity chain.

## Decision
Single `spine.py` module as the ONLY way to emit events. Closed type enum
(48 types). Run_id propagation from root trigger to final effect. Idempotency
keys derived from run_id + action_hash.

## Migration Plan
1. New code uses spine.emit() exclusively
2. Legacy events.emit() calls migrated gradually (each module one PR)
3. spine.validate_log() audits compliance
4. Direct events.jsonl writes = lint error once migration complete
