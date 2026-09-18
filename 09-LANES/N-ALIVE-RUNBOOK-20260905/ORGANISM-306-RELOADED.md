---
type: receipt
status: done
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# organism_306 — reloaded

Owner authorized `organism_306`. This session restored the skip-worktree `_ops` body from `HEAD`, then used the official restart protocol.

## Restore

- Missing tracked `_ops` code (not `.mimosa`, not `state`, not `OCTOPUS-flags.cmd` / `OCTOPUS.env`) checked out from `HEAD` after `--no-skip-worktree`.
- Key paths now exist: `budget/opslib.py`, `wiring.py`, `live_loop.py`, `RUN-ORGANISM.bat`, `telegram_center/center.py`, `telegram_center/RUN-TG-CENTER.bat`.
- Dry import: `lead_discovery_beat` and `legs_cultivation_beat` present on this vault (`wiring.py`).
- Retry left 17 files still missing (mostly tests / lock races). Not required for boot.

## Reload

1. Wrote `_ops/RESTART-REQUESTED` (empty).
2. Old PID 18452 (`bare`) exited. `127.0.0.1:8771` free.
3. Deleted `RESTART-REQUESTED` so the new process would not exit on first tick.
4. Started `RUN-ORGANISM.bat`. Did **not** write `STOP-ORGANISM`.

## After (source: `_ops/state/flags-loaded-organism.json`)

| Field | Value |
|---|---|
| pid | 10896 |
| profile | `live` |
| env_n | 343 |
| missing_count | 0 |
| alarm | false |
| bind | `127.0.0.1:8771` (not `0.0.0.0`) |
| `FUGU_VIA_CENTRAL_GATE` | 1 |
| `OCTOPUS_WIRE_LEAD_OUTBOUND` | 1 |
| `OCTOPUS_WIRE_EMAIL` | 1 |
| `OCTOPUS_WIRE_HARVEST` | 1 |
| `OCTOPUS_WIRE_LEAD_DISCOVERY` | 1 |
| `OCTOPUS_WIRE_LEG_CULTIVATE` | 1 |
| `STUDIO_LLM_CLOUD_VIA_ROUTER` | ABSENT from this snapshot catalog (`file_flags` has no such key). File still has `=1` and the bat called `OCTOPUS-flags.cmd`. |

Center PID 18320 left running. No send claimed. No SSH to 138.
