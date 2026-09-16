# Stage A — Preflight

- Timestamp: 2026-08-11 ~21:36 AUSEST
- Verdict: **PASS**
- Mode: read-only inventory; no flag file or production behavior changed.

## Hard invariants

| Limb snapshot | `OCTOPUS_NEURAL_LEARNED_APPLY` | `OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL` |
|---|---:|---:|
| center | `0` | `1` |
| cortex | `0` | `1` |
| live | `0` | `1` |
| miniapp-gateway | `0` | `1` |
| organism | `0` | `1` |

Effective flag source: `_ops/state/flags-loaded-*.json` (fresh boot snapshots around 21:09–21:10 local).

## Limb map

| Limb | PID | Start time | Command |
|---|---:|---|---|
| cortex | 22976 | 21:09:40 | `python -X utf8 cortex/cortex.py` |
| center | 21968 | 21:10:05 | `python -X utf8 telegram_center/center.py` |
| gateway | 14904 | 21:10:15 | `python -X utf8 telegram_center/miniapp_gateway.py` |
| live | 21528 | 21:10:17 | `python -X utf8 live/server.py` |
| organism | 15916 | 21:10:38 | `python -X utf8 organism.py` |
| brain_worker | — | — | in-organism / no separate process found |

Ports verified: organism `127.0.0.1:8771`; gateway `127.0.0.1:8774`.
No active `STOP-*`, `HALT-ALL`, or `RESTART-REQUESTED` marker was found.

## Live organism state

Source: `_ops/state/ORGANISM-STATE.json`

```text
ts=2026-08-11T21:36:46
started=2026-08-11T21:10:38
beat=31677
protective_skip=false
protective_proposal=protective_proposal
protective_mode=false
frozen=false
```

## Authority check

- ADR-034 status: ACCEPTED; neural direct apply demoted.
- Capability truth: TESTED / SHADOW / trace_only / may_gate=false / production_apply_enabled=false.
- Runtime agrees with ADR and WORKLOCK evidence manifest.
- No discrepancy recorded.
