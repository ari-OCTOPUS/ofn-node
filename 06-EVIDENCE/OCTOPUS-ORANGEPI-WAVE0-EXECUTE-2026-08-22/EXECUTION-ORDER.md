# EXECUTION-ORDER — WAVE0 Execute Package (A0 first)

**Authorization:** `OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822` (base token `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822`)  
**Written (AEST):** 2026-08-22T19:02:38+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)  
**Laptop:** plans + auth only  

## Status

| Surface | Status |
|---------|--------|
| Software-only A0 allowlist | **EXECUTE_READY** |
| Hardware GPIO/PWM/leg | **BLOCKED_NEED_ESTOP** |
| MQTT 1883 | **KEEP CLOSED** (no pairing in this package) |

## Sequence (mandatory)

| Step | Action | Gate |
|------|--------|------|
| 0 | Confirm package files present under evidence root | all six required files |
| 1 | Owner accepts `OWNER_REVIEW_DECISION.proposed.json` → UNLOCK with conditions | disposition UNLOCK |
| 2 | Read-only preflight: board.yaml, homeostasis, ARMED.json, reflex_arming_criteria, estop probe, MQTT state | record hashes |
| 3 | If Path H requested and estop `NOT_PRESENT` → **STOP hardware**; continue A0 only | BLOCKED_NEED_ESTOP for H |
| 4 | Backup board.yaml / homeostasis | bak + sha256 |
| 5 | Apply `actuator_authority=PERMITTED_SOFTWARE_A0`; keep hardware NONE; keep MQTT closed | verify live status |
| 6 | Confirm reflex_arming_criteria **unchanged** (still forbids gpio/pwm/mqtt/leg) | no criteria edit |
| 7 | Install/confirm A0 software allowlist (single actuator id, e.g. `software://noop` or board-local software sink) | single_actuator |
| 8 | Meet M7: lease_short policy + rollback_drill_prior dry-run; waive operator_at_estop **only** as WAIVED_SOFTWARE_A0_ZERO_GPIO | M7-STATUS.json |
| 9 | Write `READY_TO_ARM.json`; leave `ARMED.json` **armed=false** | human wait |
| 10 | **Human** arms ARMED.json with lease_short + single actuator_id | armed=true leased |
| 11 | Optional: one A0 software actuate under lease → receipt → auto-disarm | no GPIO/PWM/MQTT/leg |
| 12 | TO-LAPTOP exchange ack + package receipts | done A0 |

## Do not

- Open MQTT / pair / publish
- Edit reflex_arming_criteria to allow gpio/pwm/mqtt/leg
- Arm automatically from laptop writer
- Invent PWM profiles
- Proceed to hardware without estop

## Abort

Any forbidden surface, criteria widening without new OWNER_REVIEW, MQTT open attempt, or GPIO write → execute `ROLLBACK.md`, set ARMED false, report to owner via ari.
