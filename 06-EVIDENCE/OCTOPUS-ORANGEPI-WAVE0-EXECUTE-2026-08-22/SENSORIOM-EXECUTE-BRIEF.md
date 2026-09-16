# SENSORIOM-EXECUTE-BRIEF — WAVE0 A0

OWNER EXECUTE GRANT `OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822` (base `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822`, AEST 2026-08-22T19:02:38+10:00): unlock WAVE0 on sensorium-opi5pro (192.168.0.182) under **software-only A0** per `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-WAVE0-EXECUTE-2026-08-22`.

**Supersede:** prior auth-only `mutate_device=false` → package `mutate_device=true` bounded. OWNER_REVIEW `KEEP_WAVE0_LOCKED` → proposed **UNLOCK** with conditions (`OWNER_REVIEW_DECISION.proposed.json`).

**Do:** (1) owner-accept UNLOCK conditions; (2) backup board.yaml/homeostasis; (3) set `actuator_authority=PERMITTED_SOFTWARE_A0`, keep hardware NONE / observe-only for GPIO; (4) leave `reflex_arming_criteria` unchanged (still forbids gpio/pwm/mqtt/leg); (5) A0 allowlist = software sinks only, zero host GPIO effects; (6) meet M7 single_actuator + lease_short + rollback_drill_prior; waive `operator_at_estop` only as `WAIVED_SOFTWARE_A0_ZERO_GPIO`; (7) write READY_TO_ARM; keep `ARMED.json armed=false` until **human** arms with short lease; (8) optional one leased software actuate; (9) receipts + TO-LAPTOP.

**MQTT:** KEEP CLOSED (no pairing this package).

**Hardware GPIO/PWM/leg:** **BLOCKED_NEED_ESTOP** — do not actuate if estop NOT_PRESENT; no invented PWM.

**Forbidden:** private keys, Doctor auto-patch, torch, LAN:9101, zero-fill, hash rewrite, money/webhook/work_pump, CHG-C, git add -A, MQTT open, legs, criteria widening, auto-arm.

**Status:** EXECUTE_READY (A0 software) · BLOCKED_NEED_ESTOP (hardware).
