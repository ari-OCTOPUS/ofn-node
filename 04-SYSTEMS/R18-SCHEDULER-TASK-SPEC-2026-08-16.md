---
type: design
status: draft
created: 2026-08-16
updated: 2026-08-16
created_by: agent
tags: [octopus, r18, scheduler]
sources:
  - "[[02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/R18-DELTA-CONSOLIDATION-DESIGN]]"
  - "[[06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16]]"
---

# R18 scheduler decision — spec, not a second registration

`ConsolidationCycle` has code+tests (`test_consolidation_delta_r18.py` **5/5** [A]) and **no** caller in `daemon.py` / `automation.py` [A grep]. C-019 records that.

## Options

### (a) Windows scheduled task — recommended as reversible interim

- No TCB touch. Disable-ScheduledTask reverses it.
- **Must** `Get-ScheduledTask` same name first (C-014 duplicate-task class). Also do not collide with Microsoft `\Microsoft\Windows\Customer Experience Improvement Program\Consolidator` (wsqmcons.exe) — different path, similar English name.
- Use **full** `C:\Program Files\Python313\python.exe` like `OCTOPUS Observatory Hourly`. Do **not** use bare `py` (Poisoning Watch LastResult 2147942402; Tick LastResult 267011 never-run).
- Load flags with **last-wins override** of ambient env (see launcher invariant). `setlocal` in a `.cmd` wrapper.

### (b) daemon wiring

- Coherent with the 30s metabolic tick (housekeeping already in the loop).
- `brain/daemon.py` is TCB → needs owner re-sign of `trust-boundary.json`.
- Would still need the fail-closed enforce banner (T2).

**This sweep recommends (a) as interim and does not register a task.**

## Live fact this session must not duplicate [A]

A parallel recall-loop agent already created:

| field | value |
|---|---|
| Name | `OCTOPUS 4d Consolidation Tick` |
| State | Ready |
| LastResult | 267011 (`SCHED_S_TASK_HAS_NOT_RUN`) |
| LastRun | 1999-epoch placeholder |
| Action | `py -X utf8 F:\backup\_ops\audit\consolidation_4d_tick.py` |

Owner vote: ratify and fix launcher to `python.exe`, or Disable. This sweep will not create `OCTOPUS 4d R18 Consolidation` beside it.

## Spec if owner rebuilds (do not run)

```text
schtasks /Query /TN "OCTOPUS 4d Consolidation Tick"
# if exists: stop; do not /Create /F without vote

Name:    OCTOPUS 4d Consolidation Tick   (reuse, do not fork a second name)
Trigger: once per 6 hours, offset from "OCTOPUS 4d Poisoning Watch"
Action:  "C:\Program Files\Python313\python.exe" -X utf8 F:\backup\_ops\audit\consolidation_4d_tick.py
Start in: F:\backup\4d_system
Env:     wrapper .cmd with setlocal + call OCTOPUS-flags.cmd (last-wins)
```

Daemon hook remains owner card (TCB).
