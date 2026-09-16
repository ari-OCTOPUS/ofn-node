# Telegram Dual-Outbox Contract (C05)

stamp_local: 2026-08-23T08:46:53+10:00  
schema: octopus-telegram-dual-outbox-contract/1  
status: DOCUMENTED  

## Hard rule
**Do NOT merge** the durable loop outbox with canary/prove sqlite (or any side-path queue). They are different trust classes.

## SoT (organism LIVE claims)
- **Path:** `F:/backup/_ops/state/telegram/loop/outbox/` (plus sibling `events/` under `loop/`)
- **Role:** Durable organism / center delivery truth for LIVE claims
- **Allowed claims when:** outbox row `state` / `delivery_truth` shows durable confirmation (e.g. `CONFIRMED` / `DELIVERY_CONFIRMED`) **and** matching loop `events` progress toward CLOSED where the slice requires it
- **Not sufficient alone:** presence of files, DRY_RUN_NO_SEND, DEAD_LETTERED without reconcile narrative

## Non-SoT (ephemeral prove / canary)
- **Examples:** `F:/backup/_ops/state/telegram/a18-owner-canary-rate-limit.sqlite3` and any `*-canary*.sqlite3` / RateLimitQueue used only by owner-approved canary scripts
- **Role:** Side-path prove that SenderBridge/transport can deliver under temporary `send_exceptions`
- **Allowed claims:** "canary outbound PASS" / "SenderBridge path exercised" — **never** "organism Full Loop LIVE" or "durable_loop CLOSED"
- **A18 VERIFY already states:** durable_loop hits for canary mids may be empty (`N/A_PATH`)

## How to speak in evidence / CURRENT-TRUTH
| Claim class | Requires |
|---|---|
| Organism LIVE delivery | Durable `loop/outbox` (+ events as required) |
| Canary / unlock prove | Canary sqlite or explicit side-path RESULT — label **non-SoT** |
| Full Loop inbound | Durable inbound CLOSED + receipts — not canary DMs alone |

## Related
- Gate: `_ops/telegram_center/live_telegram_gate.py` (unlock ≠ send)
- Wire fix: `06-EVIDENCE/OCTOPUS-TELEGRAM-WIRE-FIX-2026-08-23`
- A18 canary: `06-EVIDENCE/OCTOPUS-A18-OWNER-CHAT-CANARY-2026-08-23`
- Contradiction C05: `06-EVIDENCE/OCTOPUS-CONTRADICTION-SCAN-2026-08-23`

## Rollback
Delete this contract file and the helper/test; no runtime merge was performed.

## G08 extension — triple surfaces (2026-08-23T09:05:12+10:00)
- **SoT:** `loop/outbox` + `loop/events` only for organism LIVE claims
- **Non-SoT canary:** `a18-owner-canary-rate-limit.sqlite3`
- **Non-SoT other:** any `event-bridge` / `urgent` sidepaths under `state/telegram` — may exist for pacing/alerts; **never** merge into durable SoT; never cite as Full Loop CLOSED
