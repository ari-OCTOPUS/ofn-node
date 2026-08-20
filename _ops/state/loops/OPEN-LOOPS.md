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

6. **LOOP-EVENT-BRIDGE-PRE-SEND-DEDUPE** — `event_bridge.py` marks a content signature seen before direct send (`event_bridge.py:165-170`); a failed alert can be suppressed for 24 hours. Must be routed through the durable outbox.
7. **LOOP-LEGACY-RECEIPT-UNCONFIRMED** — legacy receipt rows without `ok` remain ANSWERED-compatible; that is compatibility, not delivery confirmation. Must be explicitly labeled `LEGACY_UNCONFIRMED`.
8. **LOOP-RUN_ALL-TIMEOUT** — `run_all.py` blocks full coverage on a 300-second per-file timeout at `test_capability_registry.py`. This is an `UNBOUNDED` loop: it needs its own lane and time budget instead of holding the whole suite hostage.

## Pre-existing cognitive failures (next phase)

heart-fuel wiring, cortex, memory gate, control contracts, LLM inventory, spine/lead memory wiring, paid truncation; plus `test_phase0_receipt_rig` 15/17 (bridge-send-failed, ask-error deep dispositions).

No production-closed loop was added.
