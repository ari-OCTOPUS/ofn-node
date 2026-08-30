# OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-2026-08-22

ABD-style execute package: bind Orange Pi :9101 on LAN (bind-address only).

| File | Role |
|------|------|
| OWNER-AUTHORIZATION.json | Binding auth; mutate_device=true; token OCTOPUS-ORANGEPI-LAN-9101-20260822 |
| PLAN.md | SoT 127.0.0.1 + ssh -N -L; discover existing knob; LAN bind; doctor lan_9101 implications |
| EXECUTION-ORDER.md | Numbered steps for sensoriom |
| SENSORIOM-EXECUTE-BRIEF.md | Copy-paste brief for sensoriom agent |
| ROLLBACK.md | Restore 127.0.0.1 + tunnel |

**Supersedes:** `../OCTOPUS-ORANGEPI-LAN-9101-2026-08-22/` (auth-only, mutate_device=false).  
**Written (AEST):** 2026-08-22T19:22:00+10:00. Executor=sensoriom. Laptop writer does not SSH.
