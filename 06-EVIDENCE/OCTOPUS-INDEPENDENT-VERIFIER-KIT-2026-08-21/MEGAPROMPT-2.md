---
type: architecture-debug-plan
scope: wave1-canary-n1
owner: Ari
date: 2026-08-21
execution_authorized: true
live_send_authorized: false
webhook_authorized: false
paid_calls_authorized: false
---

# MEGAPROMPT 2 — WAVE1 single-message canary (reconstructed)

Source: `02-DECISIONS/OWNER-ORDER-WAVE1-2026-08-21.md` (full text of prompts 2–4
was not stored in the kit; this session executes the **stated gates**).

Sequence already completed: Megaprompt 1 SIG-IV `SECURITY_SHADOW_PASS` at
`bfbb03f36a6510eafe6d4910625895a127c14e7c` (commit `6830a1f`).

## Authorized now

- Kill-switch, rollback, fake-transport drill, queue measurement
- `FIXTURE_ONLY` n=1 through `SenderBridge` + isolated sqlite
- Evidence files in this kit

## Forbidden until a separate G-CANARY-OUT answer

- Real Telegram HTTP / `sendMessage`
- Webhook
- Paid calls
- More than one recipient or more than one live message
- Auto-resend of `tg:223883344` / `tg:223883346` (`UNCERTAIN_SEND_OUTCOME`)

## Preconditions (owner order)

1. Independent verification PASS — done (Megaprompt 1)
2. Owner chat target — `TELEGRAM_OWNER_CHAT_ID` **not present in this agent process** (boolean false)
3. Kill switch test — `t_g_kill_switch_blocks_before_outbox_and_transport`
4. Rollback / restart-safe deferral — Wave E restart at retry_after±1
5. Fake transport drill — this file's n=1 fixture + Wave E bridge cycle
6. Queue: `delivery_reconciliation.pending()==0`; two historical outbox rows remain `NEEDS_RECONCILIATION` and must stay held
