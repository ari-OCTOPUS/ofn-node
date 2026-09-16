---
type: evidence
created: 2026-08-12
owner_verdict: "نمیخوام مرزی بمونه"
---

# NO-BOUNDARY — باز کردن مرزهای باقی‌مانده (2026-08-12)

## Armored flags

| Flag | Value |
|---|---|
| `OCTOPUS_WIRE_LEAD_FIRST_RESPONSE_LLM` | 1 |
| `OCTOPUS_WIRE_VALUE_LEDGER` | 1 |
| `OCTOPUS_ENFORCE_MONEY_FSM` | 1 |
| `OCTOPUS_INITIATIVE_UNCAPPED` | 1 |
| `OCTOPUS_WIRE_PULSE_ARBITER_SHADOW` | 1 |
| `OCTOPUS_WIRE_CRITICALITY_OTLP` | 1 |
| `OCTOPUS_LEAD_DAILY_SEND_CAP` | 100 |
| `OCTOPUS_IMPROVE_REFRACTORY_H` | 0 |
| `OCTOPUS_COLLAB_MODEL_DAILY_CAP` | 200 |
| `LIVE-ENABLED.flag` | created (money live_gate AND still needs per-action human approval + CAPABILITY-OK) |

## Policy

- Talk Discovery / ADR-033: hard-forbidden emptied → owner-approval actions
- `talk-discovery-policy.v2` · `ADR-033-v2`
- Lead send cap env-overridable (`outbound_worker._lead_daily_send_cap`)

## Still structural (not capability toggles)

| Item | Why kept |
|---|---|
| `OCTOPUS_KILL_SWITCH` | `1` = HALT; emergency stop must stay available |
| `OCTOPUS_STATE_DIR` | path override, not a wire |
| `OCTOPUS_OTLP_ALLOW_REMOTE` | remote telemetry exfil |
| memory `may_authorize=False` | architectural constant in ingest return paths (no consumer grants control from memory) |
| money **per-action** human approval | `capability_gate.require` AND of LIVE ∧ CAPABILITY-OK ∧ approval ∧ money_gate |

## Tests

`test_approval_state` · `test_cognitive_unify` · `test_adr033_control_plane` · `test_lead_send_cap` → all green

## Rollback

```bat
rem reverse the no-boundary block in OCTOPUS-flags.cmd
del F:\backup\_ops\state\LIVE-ENABLED.flag
```

Restart organism/cortex/center.
