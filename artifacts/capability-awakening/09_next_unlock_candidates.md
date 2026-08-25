# Next owner-decision candidates

These are non-executable candidates only. The consumed gate grants no authority for another experiment, external access, action, or service change.

## 1. Dedicated local-hypothesis canary

Candidate: run the already implemented memory-pressure/local-cortex-latency experiment under a new one-use owner gate.

Reason: this canary met its required two experiments before the third heartbeat's final no-new-work window, so no live association sample was produced. Any future result must remain an association, never causation, and may legitimately be `INSUFFICIENT_EVIDENCE`.

## 2. Longer local stability observation

Candidate: a separately approved, bounded, no-change soak of the active-local registry.

Reason: the current evidence proves only a 15-minute canary, not long-term stability. No heartbeat interval change or extra load is needed.

## 3. Ordinary-cycle integration review

Candidate: owner review of whether selected active-local capabilities should have a bounded ordinary-heartbeat entrypoint.

Reason: the one-use controlled-growth endpoint now correctly rejects reuse. Any recurring scheduler would be a new authority surface and needs its own budget, rollback, and gate.

## 4. Active Inference shadow validation

Candidate: additional pure synthetic matrix tests and receipt comparison while remaining `SHADOW`.

Reason: no action binding, policy execution, dependency install, or state-dimension increase is justified by this canary.

## Not candidates under current evidence

- External learning or any DeepSeek call
- WAN/arbitrary web access
- Telegram/email/external messaging
- Shell, autonomous service/systemd control, SSH, or network configuration
- Sensor recording or ESP32 actuation
- Purchases, financial action, owner-key access
- Identity rewrite, safety-gate modification, autonomy escalation, Wave 1, or executable action

READY_FOR_NEXT_OWNER_DECISION: `true`
