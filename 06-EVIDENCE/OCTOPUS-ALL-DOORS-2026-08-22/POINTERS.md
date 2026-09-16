# POINTERS â€” MQTT enable / WAVE0 e-stop ABD (discovered only; no invent)

Date: 2026-08-22
Search root: F:\backup
Source of truth for MQTT enable verdict: prior laptop plan search (no enable runbook found).

## MQTT enable runbooks

- **Verdict:** no OPEN/enable MQTT 1883 runbook under F:\backup (no PLAN.md / SENSORIOM-EXECUTE-BRIEF / step procedure to open broker or unlock actuators).
- Search receipt: F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-MQTT-1883-2026-08-22\LAPTOP-MQTT-PLAN-SEARCH.json
- Auth-file-only (mutate_device=false): F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-MQTT-1883-2026-08-22\OWNER-AUTHORIZATION.json
- Knowledge mirror: F:\backup\07 - Knowledge\ (file 87-ORANGEPI-MQTT-1883-UNLOCK-2026-08-22.md under Knowledge tree)
- Keep-closed / forbid MQTT: F:\backup\agent-prompts\DISCOVERY-PHASE1-05-COMMAND-POLICY-2026-08-18.md
- Keep-closed CHG-C NATS (explicitly do not touch MQTT 1883): F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-CHG-C-NATS-2026-08-22\CHG-C-NATS-PLAN.md
- Keep-closed brief: F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-CHG-C-NATS-2026-08-22\SENSORIOM-EXECUTE-BRIEF.txt

## WAVE0 e-stop / ABD templates (keep-closed package; not an unlock enable runbook)

- ABD package root: F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22\
  - EXECUTION-ORDER.md
  - SENSORIOM-EXECUTE-BRIEF.txt (Forbidden: MQTT/PWM/legs; Keep WAVE0 actuator lock)
  - OWNER-CHG-AUTHORIZATION.json (wave0: KEEP_WAVE0_LOCKED)
  - CHG-A-SENSORIUM-PLAN.md
  - CHG-B-WM-SKILL-PLAN.md
  - CHG-D-LEDGER-PLAN.md
  - README.md
  - SOAK-POST-ABD-ACK.json
- WAVE0 unlock auth-file-only (not enable runbook): F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-WAVE0-UNLOCK-2026-08-22\OWNER-AUTHORIZATION.json
- WAVE0 evidence / gates:
  - F:\backup\06-EVIDENCE\WAVE0-OWNER-EXEC-A-D-2026-08-18.md
  - F:\backup\06-EVIDENCE\canonical\receipts\WAVE0-OWNER-EXEC-A-D-2026-08-18.json
  - F:\backup\06-EVIDENCE\NERVOUS-RECOVERY-2026-08-20\WAVE0_PASS.json
  - F:\backup\06-EVIDENCE\NERVOUS-RECOVERY-2026-08-20\WAVE0-GATES.json
  - F:\backup\_ops\nervous_recovery\wave0_governor.py
  - F:\backup\_ops\state\waves\WAVE0-APPEND-ONLY-MANIFEST.json
- Architect WAVE0 notes: F:\backup\04 - Architect System\2026-07-31 WAVE0-WAVE2 - concrete diffs (awaiting GO).md

## Related all-doors / archive supply (this run)

- F:\backup\06-EVIDENCE\OCTOPUS-ALL-DOORS-2026-08-22\OWNER-AUTHORIZATION.json
- F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-CHG-E-EXECUTE-2026-08-22\OWNER-ARCHIVE-SUPPLY.json
- Laptop archive dir created: \\192.168.0.191\octopus-main\octopus-evidence-archive

## Update 2026-08-22T22:40 AEST — enable ABD now WRITTEN (pending execute)

Prior verdict (no enable runbook) is **historical**. Owner GO package now exists:

- Enable ABD root: F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-MQTT-1883-ENABLE-ABD-2026-08-22\
  - PLAN.md / EXECUTION-ORDER.md / OWNER-AUTHORIZATION.json (mutate_device=true; tokens OCTOPUS-ALL-DOORS-OPEN-20260822 + OCTOPUS-MQTT-ENABLE-ABD-20260822)
  - SENSORIOM-EXECUTE-BRIEF.md / ROLLBACK.md (stop+disable) / README.md
- Bind policy in plan: 127.0.0.1 OR LAN 192.168.0.0/24 ONLY; auth required; NO WAN/UFW public 1883; credentials DISCOVER_OR_GENERATE_LOCAL_ONLY
- Listener still CLOSED until sensoriom execute — do not invent PASS
- Physical e-stop parts (Path H still BLOCKED_NEED_ESTOP): F:\backup\06-EVIDENCE\OCTOPUS-WAVE0-PHYSICAL-ESTOP-PARTS-2026-08-22\PARTS-LIST.md
- Knowledge: F:\backup\07 - Knowledge\octopus\91-WAVE0-PHYSICAL-ESTOP-PARTS.md
