---
type: receipt
status: superseded
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# organism_306 authorized — reload blocked

Superseded by `ORGANISM-306-RELOADED.md` after body restore + official bat.

Owner picked `organism_306`: load the live `OCTOPUS-flags.cmd` into the bare organism (306 missing keys, including EMAIL / LEAD_OUTBOUND / HARVEST).

Not done. Kill/relaunch would take the only living organism down with no body to start again.

## Evidence this session

| Check | Result | Source |
|---|---|---|
| organism PID | 18452 alive, `python -X utf8 organism.py`, profile `bare` | CIM + `flags-loaded-organism.json` |
| parent launcher | PID 18736 gone | CIM empty |
| `RUN-ORGANISM.bat` / `RESTART-*.ps1` | not on vault | search `_ops` |
| `opslib.py` | missing (`_ops/budget` has only yaml + pycache) | Path.exists |
| `wiring.py` / `live_loop.py` / `telegram_center/center.py` | missing | Path.exists |
| `_ops` root `*.py` | `organism.py`, `run_doctor_day.py`, `__init__.py` | listdir |

Center PID 18320 still runs from a deleted `RUN-TG-CENTER.bat`. Left running.

`RESTART-REQUESTED` / `STOP-ORGANISM` were **not** written.
