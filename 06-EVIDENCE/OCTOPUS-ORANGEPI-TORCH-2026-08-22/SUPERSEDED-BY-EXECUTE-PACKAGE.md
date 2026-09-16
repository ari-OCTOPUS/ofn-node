# SUPERSEDED — auth-only torch unlock

**Status:** SUPERSEDED  
**Written (AEST):** 2026-08-22T19:08:30+10:00  
**Prior token:** OCTOPUS-ORANGEPI-TORCH-20260822  
**Prior mutate_device:** false (file owner authorization only)

This folder (OCTOPUS-ORANGEPI-TORCH-2026-08-22) remains as historical auth-only evidence.

**Replacement execute package:**  
F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-TORCH-EXECUTE-2026-08-22/

That package upgrades the same token to `mutate_device=true` with PLAN / EXECUTION-ORDER / SENSORIOM-EXECUTE-BRIEF / ROLLBACK.

**Gate on replacement:** BLOCKED_NEED_WHEEL_URL (no safe CPU aarch64/arm64 wheel URL found in F:/backup docs; do not invent CUDA).

Sensoriom should consume the EXECUTE package, not this auth-only folder, for any board mutate.