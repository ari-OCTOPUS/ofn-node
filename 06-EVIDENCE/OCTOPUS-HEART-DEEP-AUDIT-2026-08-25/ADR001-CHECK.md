# ADR-001 CHECK (no apply)
Stamp: 2026-08-25T08:16:03+10:00
KEEP: three hearts + pulse_arbiter. Doctor must write band, never period.

## Contract (interface.py)
- Doctor -> Heart: HeartParams (viable_band_lo/hi, daily_beat_cap). Explicit: no rate/bpm/period field.
- Heart -> Doctor: HeartSignal read-only (includes period_s as observation).
- ABS_BEAT_CAP_MAX = 2000. Code default daily_beat_cap = 288. Code default band = 0.5-6.0.

## Live setpoint (heart-setpoint-latest + shadow)
- band 0.4588 - 4.4484
- daily_beat_cap 2000
- epoch_seq 57
- ts setpoint file: 2026-08-24T07:36:53 (shadow still carries same band on 2026-08-25T08:11)

## control_law
- Derives period from velocity vs Doctor band (ADR-001 holds).
- Env default CARDIAC_DAILY_BEAT_CAP=288 but runtime uses HeartParams.daily_beat_cap (2000).
- Comment/env drift only. Do not change cap this wave.

## Verdict
ADR-001 HOLDS. Doctor is not writing period_s.
Later optional (separate GO): align env comment 288 vs live 2000. Not required to unlock anything.
