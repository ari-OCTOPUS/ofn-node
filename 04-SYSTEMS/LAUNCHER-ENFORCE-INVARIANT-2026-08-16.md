---
type: design
status: draft
created: 2026-08-16
updated: 2026-08-16
created_by: agent
tags: [octopus, tcb, launcher]
sources:
  - "[[06-EVIDENCE/DEEP-TEST-1H-2026-08-16]]"
  - "[[06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16]]"
---

# Launcher invariant (gen-3 lesson, generalized) — DESIGN ONLY

Do not wire into TCB (`brain/daemon.py`, `brain/guardrails.py`, `brain/automation.py`) without an owner re-sign vote.

## Root cause [A]

A process that runs `_job_guard` → `guardrails.check_invariants` reads **its own process environment**, not `flags.cmd` on disk. Gen-3 daemon pid 27164 was started from a shell: `python -X utf8 -m brain.daemon`. Live env [A `psutil`]:

- `OCTOPUS_TCB_MANIFEST_ENFORCE=1` (good — armed)
- `SELF_CODE_ENABLED=1` (bad relative to flags.cmd, which has **no** such line; `test_no_go_envelope` requires it unset)
- `CORTEX_HYPOTHESIS` unset in daemon (flags.cmd has `=1` for the five `_ops` limbs)

Absence of enforce currently **does not** fail-closed: `check_invariants` sets `ok = anchors_ok and not (enforcement and tampered)`. Missing pubkey only sets `tampered` **if** `enforcement` is already true (`guardrails.py` ~214–216). That is the inverse of the no-pubkey path's intent once a live `_job_guard` loop is attached.

## Proposed invariant (text, not code)

1. No process that calls `_job_guard` / `check_invariants` in a live loop may remain attached unless the **boot banner** prints `enforcement=True` and `signature=valid`.
2. Boot is fail-closed if `OCTOPUS_TCB_MANIFEST_ENFORCE` is missing or not `1` — same class as `signature in (none, unsigned, no-key, error)` under enforce today.
3. Launchers must `setlocal` (or equivalent), load **only** `OCTOPUS-flags.cmd` last-wins, then exec. **Ambient shell must not win.**
4. Counter-example already on disk: `_ops/audit/consolidation_4d_tick.py` `_load_flags` uses `if k not in os.environ` → ambient wins. Scheduled-task env is usually clean; a manual `py` from a dirty shell is not.

## Audit [A] — who loads flags.cmd?

| launcher | loads flags.cmd? | runs `_job_guard`? | note |
|---|---|---|---|
| `RUN-ORGANISM.bat` / `RUN-CORTEX.bat` / `RUN-TG-CENTER.bat` / `RUN-LIVE.bat` / `run-live-headless.bat` | yes, `call OCTOPUS-flags.cmd` | no | five-limb |
| `RESTART-ALL.ps1` | abort if flags missing / bad CRLF; delegates | no | |
| `RESTART-PROCESS.ps1` gateway branch | yes (fix 2026-08-05) | no | other targets use `.bat` |
| `miniapp-watchdog.ps1` | yes | no | revive via gateway path |
| `cortex-watchdog.ps1` | no (revives `RUN-CORTEX.bat` which loads flags) | no | |
| `tg-center-watchdog.ps1` | no (revives `RUN-TG-CENTER.bat`) | no | |
| `live-watchdog.ps1` | no (revives `run-live-headless.bat`) | no | |
| `cockpit-brain-run.ps1` | yes (explicit last-wins parse) | no | comment documents the 08-04 trap |
| `python -m brain.daemon` (live pid 27164) | **inherited launching shell** | **yes** | no dedicated bat; `4d_system/start.bat` points at Desktop Streamlit |
| `4d_system/scripts/start_supervisor.bat` | no | supervisor, not `_job_guard` | task `4d_system_supervisor` **not** registered |
| `OCTOPUS 4d Consolidation Tick` | script tries flags but ambient-wins; action is `py` | no | LastResult 267011 never-run |
| `OCTOPUS 4d Poisoning Watch` | n/a (read-only) | no | LastResult 2147942402 `py` not found |
| `OCTOPUS-doctor-day` | action has no flags call | no | full `python.exe` path |

## Suggested non-TCB wrapper (not created this session)

`4d_system/scripts/start_daemon.bat`: `setlocal` → `call F:\backup\_ops\OCTOPUS-flags.cmd` → `cd 4d_system` → `python -X utf8 -m brain.daemon`. Refuse boot if `OCTOPUS_TCB_MANIFEST_ENFORCE` ≠ 1. Owner vote before registering a scheduled task (C-014 class). TCB boot-banner + fail-closed still needs re-sign.
