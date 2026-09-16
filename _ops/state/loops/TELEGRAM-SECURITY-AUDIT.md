# Telegram Security Audit

Generated: 2026-08-20  
Scope: local code, fake-transport shadow tests, live process/config presence checks.  
No secret values, live messages, paid calls, or external Telegram requests were used.

## PASS in shadow

- Owner authentication is based on `from.id`, not `chat.id`.
- Missing owner configuration fails closed.
- Duplicate updates do not create a second task or effect.
- Durable intent is written before dispatch.
- Crash after intent resumes the same task/run.
- Crash after dispatch fails closed to reconciliation.
- Outbox exists before transport.
- Confirmed message keys are not resent after module restart.
- Unknown send outcomes are quarantined rather than retried.
- Kill switch blocks before outbox and transport.
- Raw message text is absent from durable event/outbox records.
- Explicit `ok=false` send attempts are no longer counted as ANSWERED.
- Multi-message replies receive independent deterministic receipts.

## OPEN / BLOCKED

- Production flag remains off and live process has not restarted into this code.
- No Telegram token/chat config is visible to this agent (boolean false); production canary is blocked.
- Existing `event_bridge.py` writes its dedupe signature before a direct send and can lose a failed alert for 24 hours.
- Callback nonce logic exists in the separate loop organ but the new durable center path does not yet bind all callback approvals to proposal/task/run/nonce.
- A baseline receipt rig has two pre-existing failures (`bridge-send-failed`, `ask-error` deep dispositions). Baseline `7836627` reproduces 15/17 without this patch, so these are registered open loops, not regressions introduced here.
- Webhook configuration was not queried from Telegram. Code topology is polling, with 409 rival-poller detection.

## Stop conditions honored

No live send, process restart, paid call, memory write-wave bypass, force push, destructive deletion, or secret display occurred.
