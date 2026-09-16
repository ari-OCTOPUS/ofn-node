# OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-2026-08-22

Owner fix-all execute package: doctor treat intentional **LAN:9101 OPEN** as expected **PASS** (`metrics_bind` + `unexpected_listeners`).

| File | Role |
|------|------|
| `OWNER-AUTHORIZATION.json` | Token `OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-20260822`; `mutate_device=true`; `owner_fix_all=true`; WAVE0 KEEP_LOCKED; MQTT CLOSED; scope=doctor 9101 expected listeners only |
| `PLAN.md` | Problem/goal/allowed/forbidden + DISCOVER-FIRST + laptop discovery |
| `EXECUTION-ORDER.md` | Ordered steps discover→backup→patch→doctor prove |
| `SENSORIOM-EXECUTE-BRIEF.md` | Short grant for sensoriom |
| `ROLLBACK.md` | Restore doctor allowlist/script backup; keep LAN:9101 OPEN |
| `SOURCE-SCAN.json` | Laptop discovery results |
| `PACKAGE-STATUS.json` | Package readiness |

**Executor:** sensoriom on sensorium-opi5pro (192.168.0.182)  
**Laptop writer:** plans + auth only — **does not SSH**  
**Hard:** do **not** close :9101; do **not** revert LAN OPEN; gap002 must stay passed
