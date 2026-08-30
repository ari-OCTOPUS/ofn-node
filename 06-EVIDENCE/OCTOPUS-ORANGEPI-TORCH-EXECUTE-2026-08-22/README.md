# OCTOPUS-ORANGEPI-TORCH-EXECUTE-2026-08-22

ABD-style **execute** package for Orange Pi torch unlock.

- **Token:** OCTOPUS-ORANGEPI-TORCH-20260822
- **mutate_device:** true (sensoriom executes; laptop plans/auth only)
- **Gate:** **BLOCKED_NEED_WHEEL_URL** — executable package exists; install blocked until owner supplies CPU wheel URL+SHA256+Python match
- **Supersedes:** `../OCTOPUS-ORANGEPI-TORCH-2026-08-22/` (auth-only)

## Files

| File | Role |
|------|------|
| OWNER-AUTHORIZATION.json | mutate_device=true execute auth |
| PLAN.md | install runbook + MemoryMax guard + owner supply list |
| EXECUTION-ORDER.md | step order 0→7 |
| SENSORIOM-EXECUTE-BRIEF.md | one-screen grant for sensoriom |
| ROLLBACK.md | uninstall / venv restore |
| OWNER-WHEEL-SUPPLY.template.json | owner fills to unblock |

## Verdict

**Package path ready; install BLOCKED on wheel URL.**