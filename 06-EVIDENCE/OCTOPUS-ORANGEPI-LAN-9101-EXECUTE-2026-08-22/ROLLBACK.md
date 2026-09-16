# ROLLBACK - Orange Pi LAN:9101 EXECUTE

**Authorization:** `OCTOPUS-ORANGEPI-LAN-9101-20260822`  
**Written (AEST):** 2026-08-22T19:22:00+10:00  
**Target safe SoT:** `127.0.0.1:9101` + laptop `ssh -N -L` local forward

## Steps

1. Reverse the **same** knob used in execute (drop-in / board.yaml field / env / CLI) — restore listen address to **`127.0.0.1:9101`** (or exact pre-CHG recorded value).
2. Remove LAN-only firewall allow for TCP 9101 if it was added during execute.
3. `daemon-reload` if systemd touched; restart **only** the 9101-owning unit.
4. Confirm `ss`: 9101 on loopback only (not `0.0.0.0`, not LAN IP unless that was pre-state).
5. Doctor: if an existing `lan_9101` field was updated during execute, restore prior assertion / document loopback+tunnel SoT in receipt. Do **not** Doctor auto-patch.
6. Laptop access path: `ssh -N -L 9101:127.0.0.1:9101` (or documented equivalent) to 192.168.0.182; verify health via `http://127.0.0.1:9101/` through the tunnel.
7. Receipt: `ROLLBACK-ACK` with before/after listen addresses, unit name, config path restored.

## Abort / escalate

If unit fails to bind loopback after rollback -> stop further mutate; leave unit stopped if safer; report journals to owner via ari.
