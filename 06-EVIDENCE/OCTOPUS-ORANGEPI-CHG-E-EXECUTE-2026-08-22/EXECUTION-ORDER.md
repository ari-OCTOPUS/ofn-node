# EXECUTION-ORDER — Orange Pi CHG-E EXECUTE

**Authorization:** `OCTOPUS-ORANGEPI-CHG-E-20260822`  
**Written (AEST):** 2026-08-22T19:10:00+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)

## Sequence

| Step | Action | Gate |
|------|--------|------|
| 1 | Disk free space + classify hot vs cold inventory | Inventory JSON |
| 2 | Build reversible archive of cold set | Archive written |
| 3 | sha256 manifest + verify archive readback spot-check | Manifest PASS |
| 4 | Move/remove cold originals from hot path | Only after step 3 |
| 5 | Index rebuild on remaining hot set | Rebuild PASS |
| 6 | Sensorium READY soak (no watchdog storm) | READY stable |
| 7 | Receipts + TO-LAPTOP ack | Files present |

## Why this order

Archive+verify **before** delete/move prevents irreversible loss. Index rebuild **after** cold removal prevents stale index pointing at missing cold objects. READY soak catches boot regressions early.

## Parallelism

- Prefer quiet board (not during WAVE0 hardware or TORCH install).
- Do not combine with casual observation truncate jobs.

## Abort

Manifest FAIL, READY regression, any truncate/zero-fill temptation → STOP, restore from archive (ROLLBACK.md), report via ari.
