# OCTOPUS-ORANGEPI-MQTT-1883-ENABLE-ABD-2026-08-22

ABD-style **execute** package: discover-first enable MQTT 1883 on Orange Pi (local bind + auth required).

| File | Role |
|------|------|
| OWNER-AUTHORIZATION.json | Binding auth; mutate_device=true; tokens ALL-DOORS + OCTOPUS-MQTT-ENABLE-ABD-20260822 |
| PLAN.md | Discover-first mosquitto/existing broker; bind 127.0.0.1 OR LAN 192.168.0.0/24 only; auth required; doctor expectations |
| EXECUTION-ORDER.md | Steps 0→N for sensoriom |
| SENSORIOM-EXECUTE-BRIEF.md | Copy-paste brief for sensoriom agent |
| ROLLBACK.md | stop+disable + restore CLOSED |
| README.md | This index |

**Supersedes:** `../OCTOPUS-ORANGEPI-MQTT-1883-2026-08-22/` (auth-only, mutate_device=false, RECEIPT BLOCKED_NEED_RUNBOOK / mqtt CLOSED).  
**Does not:** unlock WAVE0 hardware / Path H; invent PWM/GPIO; treat software estop latch PROVE PASS as physical.  
**Credentials:** `DISCOVER_OR_GENERATE_LOCAL_ONLY` — never invent secrets into this laptop package.  
**Written (AEST):** 2026-08-22T22:40:00+10:00. Executor=sensoriom. Laptop writer does not SSH.  
**Status:** WRITTEN — pending sensoriom execute.
