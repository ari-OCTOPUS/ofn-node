---
type: owner-authorization
status: active
tags: [owner-grant, unlock, orangepi, lan-9101, 2026-08-22]
created: 2026-08-22
created_by: grok-bot
token: OCTOPUS-ORANGEPI-LAN-9101-20260822
timezone: Australia/Sydney (UTC+10)
timestamp: 2026-08-22T18:48:14+10:00
---

# 89 — Orange Pi LAN:9101 Unlock — 2026-08-22

Owner file authorization for **Orange Pi LAN:9101 unlock**.

- **Token:** `OCTOPUS-ORANGEPI-LAN-9101-20260822`
- **Evidence:** `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-LAN-9101-2026-08-22\OWNER-AUTHORIZATION.json`
- **mutate_device:** false (no Pi mutation)
- **git:** do not `git add -A`

## Allowed
- LAN:9101

## Forbidden
- private keys export/rewrite
- Doctor auto-patch
- torch
- MQTT 1883
- zero-fill
- hash rewrite
- money/webhook/work_pump
- re-run CHG-C
- WAVE0 actuators

## Notes
File owner authorization only. Sydney timestamp recorded in JSON. No device mutation in this step.

## SUPERSEDED (2026-08-22T19:22:00+10:00)

Execute package supersedes this auth-only unlock: `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-2026-08-22\` (`mutate_device=true`). See `SUPERSEDED-BY-EXECUTE-PACKAGE.md`.
