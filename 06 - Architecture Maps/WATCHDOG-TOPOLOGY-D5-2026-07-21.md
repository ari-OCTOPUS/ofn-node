---
type: architecture
status: active
tags: [architecture, watchdog, halt-all, telegram, deployment]
created: 2026-07-21
updated: 2026-07-21
---

# Watchdog topology — HALT-ALL coverage + TG-centre registration design (D5, 2026-07-21)

Design/audit artifact. SOURCE-ONLY change; nothing here registers or touches a live scheduled
task — applying to the live machine is the owner-gated **deploy** step, not this work.

## 1. Supervisor inventory (after D5)

| Watchdog (source) | Supervises | Registered task at BASE | Honors HALT-ALL | Honors architect STOP | Scoped off-switch |
|---|---|---|---|---|---|
| `04 - Architect System/scripts/organism-watchdog.ps1` (**the twin — registered**) | organism 8771 **+ cortex 8772** | yes (`organism-watchdog`) | **now yes (D5)** | yes (`F:\backup\STOP`) | `STOP-ORGANISM` |
| `_ops/cortex-watchdog.ps1` | cortex 8772 | no | yes (D-G) | yes | `STOP-CORTEX` |
| `_ops/live-watchdog.ps1` | live cockpit 8773 | yes (`OCTOPUS-Live-Watchdog`) | yes (D-G) | yes | `STOP-LIVE` |
| `_ops/tg-center-watchdog.ps1` | TG group centre (poller) | **no (gap)** | **now yes (D5)** | yes | `STOP-TG-CENTER` |
| `_ops/watchdog.py` | organism (py) | (invoked path) | yes (D-G) | yes | `STOP-ORGANISM` |

HALT-ALL marker = `F:\backup\_ops\HALT-ALL` (single source: `opslib.HALT_ALL = OPS / "HALT-ALL"`).
Architect STOP marker = `F:\backup\STOP`.

## 2. The twin gap D5 closed (item 1)

The **registered** organism watchdog is the twin in `04 - Architect System/scripts/`, not the
`_ops` copies. At BASE it yielded only to `F:\backup\STOP` and `_ops\STOP-ORGANISM` — it had **no
HALT-ALL check**, so a global panic could not stop it from reviving BOTH the organism (8771) and
the cortex (8772) it supervises. D5 adds one ADD-only guard, senior to persistence:

```powershell
if (Test-Path (Join-Path $VAULT "_ops\HALT-ALL")) { exit 0 }   # silent yield to global HALT-ALL
```

Placed immediately after the existing STOP / STOP-ORGANISM yields (both untouched). This can only
ADD a refusal-to-revive condition — it never makes the watchdog more eager. The twin uses the
`$VAULT` idiom (not the `$ops` + `Split-Path` idiom of the `_ops` watchdogs); `Join-Path $VAULT
"_ops\HALT-ALL"` resolves to the same `F:\backup\_ops\HALT-ALL` marker.

## 3. TG-centre watchdog registration design (item 2)

`_ops/tg-center-watchdog.ps1` supervises the Telegram group command centre (`center.py`, a poller
with no HTTP port — liveness is a process/command-line probe, not a port probe). At BASE it had
**no registered scheduled task**, so if the centre died unplanned nothing revived it.

D5 also brought this watchdog under HALT-ALL (same ADD-only guard as cortex/live) so the registered
task can honestly honor **STOP-TG-CENTER + HALT-ALL + architect STOP**.

Registration script: **`_ops/register-tg-center-watchdog.ps1`** (source only; DRY-RUN unless `-Apply`).

Design parameters:
- **Task name:** `OCTOPUS-TG-Center-Watchdog`
- **Action:** `powershell.exe -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\tg-center-watchdog.ps1`
- **Working directory:** `F:\backup\_ops` (so the watchdog's relative `Join-Path` calls resolve;
  it relaunches `telegram_center\RUN-TG-CENTER.bat`).
- **Trigger:** every 5 minutes, indefinitely (matches cortex/live cadence).
- **Single-instance:** `MultipleInstances = IgnoreNew` — critical, because `RUN-TG-CENTER.bat` is
  a self-restarting loop; two overlapping ticks would spawn a second centre that 409-fights the
  first over `TG_CENTER_BOT_TOKEN`. `ExecutionTimeLimit = 4 min` caps a wedged tick.
- **Markers honored (inside the watchdog, not the scheduler):** HALT-ALL, architect STOP,
  STOP-TG-CENTER — the task never revives the centre while any of those exist.

schtasks fallback (if the ScheduledTasks cmdlets are unavailable): `schtasks /Create` cannot set
`MultipleInstances`, so a plain
`schtasks /Create /TN OCTOPUS-TG-Center-Watchdog /SC MINUTE /MO 5 /TR "powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\tg-center-watchdog.ps1"`
must be paired with a task-XML import that sets `<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>`
and `<WorkingDirectory>F:\backup\_ops</WorkingDirectory>`; prefer the cmdlet wrapper.

## 4. Owner-gated / deferred

- **Applying any of this to the live machine** (running `register-tg-center-watchdog.ps1 -Apply`,
  or otherwise creating/modifying the scheduled task) is the owner-gated deploy step. D5 did not
  execute it and registered nothing.
- The deploy step also chooses the task **principal** (which user / run-whether-logged-on / run
  level) — left unset here to mirror the minimal existing watchdog registrations.

## 5. Verification (source/grep level; no PowerShell executed)

`_ops/tests/test_stop_contract.py` asserts, at source level:
- the twin `organism-watchdog.ps1` now `Test-Path`s HALT-ALL **and** still references
  `STOP-ORGANISM` and the architect STOP (`Join-Path $VAULT "STOP"`);
- all three `_ops` `.ps1` watchdogs (cortex, live, **tg-center**) `Test-Path` HALT-ALL **and**
  still check architect STOP via `Split-Path $ops -Parent` + `'STOP'`.
