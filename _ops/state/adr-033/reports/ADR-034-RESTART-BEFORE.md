# ADR-034 Controlled Restart — BEFORE

- captured_at: 2026-08-11T21:08:40+10:00
- note: brain_worker is not a separate live process; neural path runs inside organism.py

## Processes

| Process | PID | Start time (local) | Command |
|---|---|---|---|
| organism | 23724 | 2026-08-11 20:29:21 | `python -X utf8 organism.py` |
| brain_worker | — | — | not running as standalone PID |
| cortex | 9164 | 2026-08-11 20:24:39 | `python -X utf8 cortex\cortex.py` |
| center | 22532 | 2026-08-11 20:25:10 | `python -X utf8 telegram_center\center.py` |
| live | 4352 | 2026-08-11 20:25:21 | `python -X utf8 live\server.py` |
| miniapp_gateway | 9476 | 2026-08-11 20:39:28 | miniapp_gateway.py |

## Effective flags (flags-loaded-organism.json)

| Flag | Effective value |
|---|---|
| OCTOPUS_NEURAL_LEARNED_APPLY | **1** (STALE — pre-containment snapshot) |
| OCTOPUS_NEURAL_PROTECTIVE_PROPOSAL | **absent/None** |
| Source-of-truth file | `OCTOPUS-flags.cmd` already has APPLY=0, PROPOSAL=1 (not yet loaded by live PID) |

## protective_skip provenance (LEGACY — do not judge success/fail)

| Field | Value |
|---|---|
| protective_skip | true |
| protective_mode | true |
| protective_reason | `pain=0.38>0.35 [+learned=0.25:rhythm_amber] — non-essential paused` |
| protective_proposal | absent |
| writer | `organism._write_state` → `_ops/state/ORGANISM-STATE.json` |
| source_path (historical) | pre-ADR-034 `protective_override` → `action=protective_halt` → `_protective_skip=True` |
| state.started | 2026-08-11T20:29:21 |
| state.ts | 2026-08-11T21:08:26 |
| beat | 31649 |

Interpretation: this is a **legacy control write** from the old neural→halt path (learned fold + calibrated threshold). It is not treated as pass/fail of containment; post-restart must prove the new neural path does not rewrite skip from pain.
