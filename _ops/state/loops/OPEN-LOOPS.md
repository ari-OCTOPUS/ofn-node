# Open Loops

Generated: 2026-08-20

The machine-readable source is `LOOP-REGISTRY.json` (42 seeded seams). Key open/high-impact loops verified in this session:

1. **S-T01 / Telegram events without production consumer closure.** Durable consumer is implemented and shadow-tested but activation flag is off; no live restart/canary.
2. **S-T02 / Direct Telegram send without durable closure.** New center path is shadow-closed; legacy `event_bridge.py` still marks dedupe before direct send and has no delivery outbox.
3. **S-B05 / brain_core parity NO_BASELINE.** Current state has `compared=6442`, `matched=0`, `missing_old=6442`.
4. **S-A03 / calibration feedback.** Calibration artifact is current, but this session did not establish a verified `calibration-latest → improve` causal effect.
5. **S-A01 / self-knowledge confidence.** Latest state now says confidence `null` and “not calibrated”; historical hardcoded 0.4 appears mitigated, but no independent causal verifier was run here.
6. **Wave 1 reconciliation.** Sidecar lock, entry gates, older verifier, and later closeout disagree; only read-only canary-sidecar status is accepted.
7. **Receipt rig baseline debt.** `test_phase0_receipt_rig.py` remains 15/17 on baseline and patched tree (`bridge-send-failed`, `ask-error` deep dispositions).
8. **Full-suite cognitive failures.** Pre-existing failures remain in heart-fuel wiring, cortex, memory gate, control contracts, LLM inventory, spine/lead memory wiring, and paid truncation.

No open loop is represented as production closed.
