# ROLLBACK — Orange Pi TORCH EXECUTE

**Authorization:** `OCTOPUS-ORANGEPI-TORCH-20260822`  
**Safe state:** no broken partial torch; `/opt/octopus/venv` importable; MemoryMax intact

## Steps

1. If install started: `pip uninstall torch` (and torchvision/torchaudio if pulled) inside `/opt/octopus/venv` only.
2. Optionally restore from pre-install `pip freeze` snapshot / venv backup tarball if taken.
3. Confirm `import torch` returns to prior FAIL or prior known-good version (document honestly).
4. Confirm WM/skill **MemoryMax** still set (128M–256M); restore drop-ins if altered.
5. Receipt ROLLBACK-ACK; do not re-attempt without new owner wheel URL.

## If BLOCKED_NEED_WHEEL_URL (no install)

- No mutate rollback needed; leave package BLOCKED; do not invent wheels.
