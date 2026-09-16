# EXECUTION-ORDER — Orange Pi TORCH EXECUTE

**Authorization:** `OCTOPUS-ORANGEPI-TORCH-20260822`  
**Written (AEST):** 2026-08-22T19:10:00+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)

## Sequence

| Step | Action | Gate |
|------|--------|------|
| 0 | Confirm owner wheel URL+SHA256+Python match present | Else **STOP → BLOCKED_NEED_WHEEL_URL** |
| 1 | Read-only precheck (arch, venv, MemoryMax) | Receipt PRECHECK |
| 2 | pip freeze / venv snapshot for rollback | Snapshot saved |
| 3 | SHA256 verify wheel; install into `/opt/octopus/venv` only | Hash match |
| 4 | `import torch` verify; assert no CUDA invent | PASS + cuda False |
| 5 | Re-check WM/skill MemoryMax still capped | 128M–256M present |
| 6 | Receipts + TO-LAPTOP ack | Files present |

## Abort

Missing wheel URL, hash mismatch, CUDA/GPU stack pull, MemoryMax removal → STOP, ROLLBACK if install started, report via ari.
