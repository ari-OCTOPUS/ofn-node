# PLAN — Orange Pi TORCH EXECUTE (CPU only)

**Authorization / Token:** `OCTOPUS-ORANGEPI-TORCH-20260822`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Written (AEST):** 2026-08-22T19:10:00+10:00  
**mutate_device:** true  
**Gate:** `BLOCKED_NEED_WHEEL_URL` until owner supplies verified CPU wheel

## Problem

`import torch` FAIL under system Python and `/opt/octopus/venv`. Prior auth-only folder had `mutate_device=false` and no install runbook.

## Goal

Install **CPU-only** torch into **`/opt/octopus/venv`**, keep CHG-B **MemoryMax** guards, never invent CUDA.

## Gate (must PASS before mutate install)

Owner must provide all of:
- Wheel URL (HTTPS) for **CPU** torch matching board arch (`aarch64`/`arm64` expected — confirm with `uname -m`)
- SHA256 of wheel
- Target Python version matching `/opt/octopus/venv`
- Explicit note: **no CUDA / no GPU stack invent**

Until then package status remains **`BLOCKED_NEED_WHEEL_URL`**. Sensoriom may run **read-only precheck** only.

## Allowed change set (after gate PASS)

1. Precheck: arch, venv path, `python -V`, before `pip show torch` / import status, WM/skill `MemoryMax` still 128M (or documented band).
2. Snapshot / backup venv metadata (pip freeze) for rollback.
3. Install owner wheel into `/opt/octopus/venv` only (`pip install` from URL or local staged wheel with SHA256 verify).
4. Verify: `/opt/octopus/venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available())"` → version OK, **`cuda.is_available() == False`** (CPU expected).
5. Confirm MemoryMax drop-ins unchanged (128M–256M capped; never remove).
6. Receipts + TO-LAPTOP ack.

## Explicitly forbidden

- Inventing CUDA/mali/nvidia wheels; unconstrained MemoryMax; LAN:9101; MQTT/PWM/legs; Doctor auto-patch; keys; zero-fill; hash rewrite; laptop SSH mutate.

## Success criteria

- `import torch` PASS in `/opt/octopus/venv`
- CUDA not enabled / not invented
- MemoryMax guards intact
- Or honest **BLOCKED_NEED_WHEEL_URL** with no install attempted
