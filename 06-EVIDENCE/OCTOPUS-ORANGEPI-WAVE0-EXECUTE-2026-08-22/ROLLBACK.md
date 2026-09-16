# ROLLBACK — WAVE0 Execute Package

**Authorization:** `OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822` / base `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822`  
**Written (AEST):** 2026-08-22T19:02:38+10:00

## Immediate abort (any phase)

1. Set `ARMED.json` → `"armed": false` (delete lease fields).
2. Stop any in-flight A0 actuate loop.
3. Confirm MQTT still closed; if opened contrary to plan, close listener/publish paths and document incident (MQTT open is a plan violation).
4. Do **not** leave partial hardware authority enabled.

## Restore board.yaml / homeostasis

1. Copy `board.yaml.pre-wave0-execute-*.bak` over live `board.yaml`.
2. Restore homeostasis snapshot taken in EXECUTION-ORDER step 4.
3. Reload config consumer (SIGHUP or unit restart as used in apply).
4. Verify live status shows `WAVE0_OBSERVE_ONLY` (or equivalent) and `actuator_authority: NONE` (or prior values from preflight receipt).
5. Receipt: after-hash must match bak hash.

## reflex_arming_criteria

A0 path should **not** have modified criteria.  
If modified in error:
1. Restore criteria file from preflight sha256 backup.
2. Restart consumer if required.
3. Confirm gpio/pwm/mqtt/leg still forbidden.

## A0 allowlist / software sinks

1. Remove or disable A0 allowlist entries added by this package.
2. Delete any `/var/lib/octopus/actuators/software-a0/` test toggles created during execute (receipt list).
3. Confirm no sysfs GPIO/PWM exports remain from mistaken Path H attempts.

## OWNER_REVIEW

1. Write superseding decision `KEEP_WAVE0_LOCKED` (or leave proposed UNLOCK unaccepted).
2. Point BOARD-BRIEF / review ack back to locked disposition.
3. Keep this evidence folder for audit; do not delete.

## mutate_device

1. After rollback complete, further board mutation requires a **new** owner token.
2. Treat this package mutate grant as **spent/revoked** on abort.

## Rollback drill (required before first arm)

Dry-run steps 1–5 of "Restore board.yaml" **before** human arming, then re-apply A0 authority once — proves rollback works. Record `rollback_drill_prior: PASS` in M7-STATUS.

## Success of rollback

- armed=false  
- authority restored to observe-only / NONE  
- MQTT closed  
- no GPIO/PWM/leg side effects left  
- receipts written  
