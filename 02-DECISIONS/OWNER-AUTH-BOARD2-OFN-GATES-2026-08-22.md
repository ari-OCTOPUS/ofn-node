---
type: decision
status: active
tags: [owner-authorization, board2, ofn-gates, 2026-08-22]
created: 2026-08-22
created_by: grok-bot-executor
token: OCTOPUS-BOARD2-OFN-GATES-20260822
---

# OWNER-AUTH — Board2 OFN gates (drop 4 from OFN_EXTRA_CLOSED_GATES)

Token: `OCTOPUS-BOARD2-OFN-GATES-20260822`

Supersedes earlier keep-closed default after owner late answer.

## Scope (narrow)

Drop **only** these from `OFN_EXTRA_CLOSED_GATES` on Board2 DietPi (`192.168.0.138` / `/home/ari/.config/ofn/node.env`):

- `fee_payment`
- `auto_payment`
- `live_email_send`
- `live_publish`

Leave all other closed gates closed. Do not touch `OFN_WIRE_OUTBOUND=0`, webhook_verify, or Phase-3 CONTROL_URL.

## Deferred

Owner skipped checkpoint **348** / **CHG-E** widget → deferred (see evidence `DEFER-CHECKPOINT-CHGE.json`).

## Evidence

- `F:\backup\06-EVIDENCE\OCTOPUS-BOARD2-OFN-GATES-2026-08-22\OWNER-AUTHORIZATION.json`
- `F:\backup\06-EVIDENCE\OCTOPUS-BOARD2-OFN-GATES-2026-08-22\DEFER-CHECKPOINT-CHGE.json`
- Marketing receipt: `F:\backup\06-EVIDENCE\BOARD2-OFN-GATES-2026-08-22\README.md`