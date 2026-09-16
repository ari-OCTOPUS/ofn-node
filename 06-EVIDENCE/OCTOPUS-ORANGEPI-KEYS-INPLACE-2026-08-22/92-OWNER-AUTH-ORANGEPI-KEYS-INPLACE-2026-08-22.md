---
schema: octopus.owner-authorization.note.v1
token: OCTOPUS-ORANGEPI-KEYS-INPLACE-20260822
evidence: F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-KEYS-INPLACE-2026-08-22/OWNER-AUTHORIZATION.json
date: 2026-08-22
timezone: Australia/Sydney
tags: [octopus, orangepi, keys, inplace, owner-authorization]
---

# 92 — Owner auth: Orange Pi keys in-place

## Decision
Allow **using existing on-board keys in place** on the Orange Pi.

## Allowed
- Use existing on-board keys where they already are
- Reference / authenticate with those keys without moving them

## Forbidden
- Export keys
- Rewrite keys
- Zero-fill
- In-place hash rewrite
- Copy keys off-device

## Notes
File authorization only. Does not mutate the device. Does not authorize `git add -A`.

## Evidence
- `OWNER-AUTHORIZATION.json` (this pack)
- Token: `OCTOPUS-ORANGEPI-KEYS-INPLACE-20260822`
- Timestamp: 2026-08-22T18:45:00+10:00
