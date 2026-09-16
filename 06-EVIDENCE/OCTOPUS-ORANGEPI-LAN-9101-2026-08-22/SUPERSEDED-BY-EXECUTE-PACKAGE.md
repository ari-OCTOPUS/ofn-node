# SUPERSEDED - auth-only LAN:9101 package

**Status:** SUPERSEDED  
**Written (AEST):** 2026-08-22T19:22:00+10:00  
**Token (unchanged):** `OCTOPUS-ORANGEPI-LAN-9101-20260822`

This directory (`OCTOPUS-ORANGEPI-LAN-9101-2026-08-22`) was **auth-only** with `mutate_device=false` (file owner authorization; do not mutate the Orange Pi).

**Owner late-answer SUPERSEDES** that tunnel-only / auth-only default.

## Execute package (authoritative)

- Path: `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-2026-08-22\`
- `mutate_device`: **true**
- Scope: bind :9101 on LAN (change bind address only on existing stability service)
- Executor: sensoriom
- Do not treat this auth-only folder as the execute plan.

See EXECUTE package: `OWNER-AUTHORIZATION.json`, `PLAN.md`, `EXECUTION-ORDER.md`, `SENSORIOM-EXECUTE-BRIEF.md`, `ROLLBACK.md`.
