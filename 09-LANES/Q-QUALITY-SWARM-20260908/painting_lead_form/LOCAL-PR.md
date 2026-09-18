# Local PR bundle — painting store-only lead form

Not pushed (AGENTS.md: no external network from this session).
No GitHub PR URL.

## Intent

Class A2 from `BIZ-LEG-BLOCKERS.md`: persist a painting lead with `baseline_action=0`.
No send, no pay, no `0.0.0.0`.

## Files

- `09-LANES/Q-QUALITY-SWARM-20260908/painting_lead_form/lead_form.py`
- `09-LANES/Q-QUALITY-SWARM-20260908/painting_lead_form/test_lead_form_realtime.py`

## Test plan

```
python 09-LANES/Q-QUALITY-SWARM-20260908/painting_lead_form/test_lead_form_realtime.py
```

Must show a real row on disk after submit; empty name fail-closed; `baseline_action==0`.

## Merge

Owner/other lane may copy into `_ops/legs/` later. This lane does not wire `OCTOPUS_WIRE_*`.
