# WORK-PUMP-DIAG (no apply)
Stamp: 2026-08-25T08:28:00+10:00
KEEP: cardiac + control_law + rhythm + pulse_arbiter
Apply: NO

## Symptom
life_economy-latest (2026-08-19T23:50:45) marks organ `work_pump` status=RETIRED (credits 0, sleep_cycles 3, retired_at same ts). work_pump still fires: health 2026-08-25 06:50, gap_report 00:55, web_research 01:04.

## Coupling
There is none. `life_economy.py` is a metaphor sim (credit/sleep/retire). Its own comment: RETIRE does not delete code/files/organs. It simulates `organism` + `work_pump` as ledger rows only. Last events file mtime 2026-08-19. Not a controller.

`work_pump.pump_step` gates are only:
- `opslib.STOP_ORGANISM` / `halted()` kill-switch
- `opslib.frozen()` FREEZE
Neither is set.

Wiring call site (`wiring.py` heart_beat): `if flag("OCTOPUS_WIRE_HEART_WORK")` then `work_pump.pump_step`. Live flags: `OCTOPUS-flags.cmd` line 15 `set OCTOPUS_WIRE_HEART_WORK=1`.

## Verdict
INTENDED_LIVE, not a stale runaway. The stale artifact is life_economy snapshot (6 days old), not the pump. Health/gap/web_research unpaid templates are still doing real work.

## Propose (not applied)
If owner later wants pump off: set `OCTOPUS_WIRE_HEART_WORK=0` in `OCTOPUS-flags.cmd` (reversible; rollback = set back to 1). Do not edit `heart/work_pump.py`. Do not honor life_economy RETIRED as a stop signal without a separate design GO.

## Why no apply now
Disabling the flag would stop health snapshots. That is a behavior change, not a fix for a broken coupling. Config disable is safe+reversible but not justified by this diagnosis.
