# Open Loops

Generated: 2026-08-21 (updated)

Machine-readable source: `LOOP-REGISTRY.json` / `LOOP-REGISTRY.jsonl`.

## Containment verified (not closed)

- `LOOP-TELEGRAM-UNOWNED-INSTANT-ALERT` — `CONTAINED_VERIFIED` on 2026-08-21 after verification run (instant 15/15, shadow roundtrip 10/10, direct_sends=0). Not CLOSED: task_id=None, terminal=BLOCKED — the path still has no real identity.

## Verified open

1. **S-T01 / Telegram events without production consumer closure.** Durable consumer implemented and shadow-tested; activation flag off; no live restart/canary.
2. **S-T02 / Direct Telegram send without durable closure.** Center path shadow-closed; `event_bridge.py` still marks dedupe before direct send and has no delivery outbox.
3. **S-B05 / brain_core parity NO_BASELINE.** `compared=6442`, `matched=0`, `missing_old=6442`.
4. **S-A03 / calibration feedback.** No independently verified causal `calibration-latest → improve` effect this session.
5. **Wave 1 reconciliation.** Sidecar lock, entry gates, older verifier, later closeout disagree; only read-only canary-sidecar status is accepted.

## New registered debts (2026-08-21)

6. **LOOP-EVENT-BRIDGE-PRE-SEND-DEDUPE** — IN_PROGRESS: `event_bridge.py` now marks seen only after confirmed delivery; outbox QUEUED/DELIVERY_FAILED/CONFIRMED/DLQ rows; bounded pending retry (3 attempts); `test_event_bridge_outbox` 3/3. Live process loads the new module on next center restart.
7. **LOOP-LEGACY-RECEIPT-UNCONFIRMED** — IN_PROGRESS: truth labels `DELIVERY_CONFIRMED/DELIVERY_FAILED/LEGACY_UNCONFIRMED` plus counts/denominator in the collector view; legacy rows are not rewritten; `test_telegram_durable_loop` 15/15.
8. **LOOP-RUN_ALL-TIMEOUT** — IN_PROGRESS: per-file timeout map (capability_registry 900s), continue-on-timeout, `execution-manifest.jsonl` with stdout/stderr sha256; timed-out suites revoke the capability marker; `test_runner_timeout_isolation` 3/3 + smoke. Root cause of the capability_registry hang remains open.

## Pre-existing cognitive failures (next phase)

heart-fuel wiring, cortex, memory gate, control contracts, LLM inventory, spine/lead memory wiring, paid truncation; plus `test_phase0_receipt_rig` 15/17 (bridge-send-failed, ask-error deep dispositions).

No production-closed loop was added.
