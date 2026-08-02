---
type: status
project: Octopus
date: 2026-08-02
status: live-smoked
tags: [octopus, telegram, g03, wal, owner-control]
---

# Octopus Current Truth — 2026-08-02

## What Octopus is

Octopus is an owner-controlled multi-agent operating system.
The human owner controls real-world effects through Telegram.

## Current production truth

G-03 is now wired to production.

- Commit: `50de1c8 wire owner-controlled G03 outbound WAL`
- Support files: `c5a047e track agi2027 control support files`
- Cleanup: `center.py` hook line endings checked/fixed after final wiring

## Telegram control

Live smoke passed:

- `/ops` → OK
- `/outbound status` → OK
- `/now` → passthrough OK

Active flags:

```json
{
  "OCTOPUS_WIRE_TG_CONTROL": "1",
  "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "1",
  "OCTOPUS_WIRE_VALUE_LEDGER": "1"
}
```

## Outbound WAL

Current observed outbound state:

```json
{"failed": 1, "sent": 4}
```

No open ambiguous item was observed:

- `sending`: 0
- `needs_owner`: 0

## Human-control commands

Owner commands now available:

```text
/ops
/outbound status
/outbound recover
/outbound mark-sent <effect_id>
/outbound cancel <effect_id>
/outbound retry <effect_id>
```

## Honest boundaries

Still not done:

- No real customer email smoke yet.
- Project-F is still blocked until `PROJECTF_API_BASE_URL` and `PROJECTF_API_TOKEN` exist.
- Do not use full `python -m pytest _ops -q` as the gate yet; an older test module exits during pytest collection.

## Correct test gate

Use:

```powershell
python _ops\agi2027_control\run_tests.py
```

Expected:

```text
Ran 23 tests
OK
```

## If rollback is needed

Disable flags in:

```text
_ops/agi2027_runtime/managed_flags.json
```

Set:

```json
{
  "OCTOPUS_WIRE_TG_CONTROL": "0",
  "OCTOPUS_WIRE_LEAD_OUTBOUND_WAL": "0"
}
```

Then restart Telegram center.
