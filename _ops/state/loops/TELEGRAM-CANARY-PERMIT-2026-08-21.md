# Bounded Owner-Only Telegram Live Canary — Permit Record

Generated: 2026-08-21  
Owner permit: OWNER PERMIT — BOUNDED OWNER-ONLY TELEGRAM LIVE CANARY (2026-08-21)
Baseline: `913cbcf`

## Status: NOT ARMED

The permit is recorded but the canary is **not armed**. Two hard blockers remain, exactly as stated by the owner:

1. `TOKEN_AVAILABLE: false` — the agent must not see or print credentials; the owner configures the live environment and only boolean availability is reported back.
2. Five real inbound owner events are required and only the owner can produce them; the agent must not fabricate or simulate owner events and call them production.

## Precondition ledger (verified 2026-08-21)

| Precondition | State |
|---|---|
| Post-fix verification: instant suite | 15/15 PASS |
| Post-fix verification: shadow roundtrip | 10/10 PASS |
| `direct_sends` in both suites | 0 |
| direct-send text lines in outputs | 0 |
| Telegram HTTP calls in suites | 0 (fake transports only) |
| `paid_calls` / `memory_mutations` in outputs | 0 / 0 |
| Output hashes retained | instant-suite.txt `e091682d…`, shadow-roundtrip.txt `f2f1d51b…` |
| LOOP-VERIFIER.json regenerated vs final code | confirmed=true, failed_checks=[] |
| STOP-TG-HEARTBEAT | present/ON |
| Instant-alert path | outbox-only |
| Engineering lease (center.py / durable_loop.py / tg_api.py) | no concurrent writer this session |

## Authorized scope when armed (per permit)

1. Enable `OCTOPUS_TG_DURABLE_OUTBOX` for the center process only.
2. Snapshot PID, port 8776, offset, pending intents, outbox depth, DLQ depth, last beat.
3. Restart ONLY the Telegram center process (never organism/cortex/daemon/live).
4. Wait for ≥3 healthy poll cycles; confirm no 409 rival poller.
5. Process exactly 5 real inbound owner events from the allowlisted chat.
6. Per-event audit: intent, ACK, dispatch marker, result, outbox record, delivery receipt `ok=true`, readback, task/run attribution.

## Hard limits

Exactly one canary window; no broadcast; no third-party chat; no heartbeat resumption; no paid model call (local/degraded response acceptable and labelled); no memory write; no Wave 1 unlock.

## Abort/rollback

Duplicate reply/effect; message to non-allowlisted chat; `ok=false` counted as delivered; null/fabricated/foreign task_id; 409 rival poller; offset regression or lost events; stuck pending intent; token/secret in any log/artifact/message; heartbeat spam resumes. Rollback = unset flag, restart center, verify legacy path, reconcile outbox/DLQ, write INCIDENT artifact.

## PRODUCTION_CLOSED criteria (unchanged, per permit)

real_events ≥ 5, duplicate_effects == 0, delivery_receipts_ok == 5, readbacks == 5, attribution ≥ 0.95 on sample, unauthorized_sends == 0, fabricated_task_ids == 0, memory_mutations == 0, paid_calls == 0, critical_regressions == 0, independent verifier confirmed == true.
