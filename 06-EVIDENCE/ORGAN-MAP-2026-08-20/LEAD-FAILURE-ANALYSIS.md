# T70 — lead diagnosis (activation forbidden)

## Failure class

**ACK_TIMEOUT** (`phi-timeout:no-ack`)

Not CODE (no exception file besides last-failure). Not a customer/outbound action.

## Evidence (read-only)

| field | at last failure | live (same session) |
|---|---|---|
| state | timeout | alive |
| phi | 16.531 | 4.22 |
| phi_dead | 16.0 | 16.0 |
| silence_ms | 1_017_725 (~17 min) | varies |

**phi_calibration: NOT_COMPARABLE.** Failure phi and live phi differ by more than 5; they must not be ranked against each other until the unit is documented.

Restart does **not** hide this sample: silence was longer than `phi_dead` minutes. The on-disk note already says restart does not fix the cause.

## RFC (draft, not applied)

`RFC-lead-phi-ack-20260820` — log ack age and silence in one unit; keep activation off; no auto-restart; no customer contact.
