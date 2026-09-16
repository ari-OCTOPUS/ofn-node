# PLAN - Orange Pi LAN:9101 EXECUTE (bind-address only)

**Authorization / Token:** `OCTOPUS-ORANGEPI-LAN-9101-20260822`  
**Authorization ID:** `OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-20260822`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER auth only (no SSH/mutate from this writer)  
**Written (AEST):** 2026-08-22T19:22:00+10:00  
**mutate_device:** true  
**Supersedes:** `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-LAN-9101-2026-08-22` (auth-only, mutate_device=false)

## Current SoT (do not invent)

- **Listen:** `127.0.0.1:9101` (loopback only).
- **Laptop access path:** `ssh -N -L ...` local forward to board `127.0.0.1:9101`.
- **Healthy service name (board deep diagnosis):** `stability`.
- **Laptop evidence gap:** no on-disk `board.yaml` / systemd unit text / stability python bind source for :9101 was found under searched laptop evidence. **Executor discovers the existing knob on the board** and changes **bind address only** — do not invent a new protocol, port, service, or HTTP API.
- Prior ABD/CHG packages listed **open 9101 to LAN** as forbidden; this owner late-answer **explicitly authorizes** that bind change only.

## Goal

Bind **:9101 on LAN** so laptop tools can reach `192.168.0.182:9101` **without** an always-on `ssh -N -L` tunnel. Prefer `0.0.0.0:9101` or explicit LAN IP `192.168.0.182:9101`. Keep ACL/firewall LAN-scoped. Keep WAVE0/MQTT/keys/CHG-C locked. Preserve clean rollback to `127.0.0.1` + SSH local forward.

## Allowed change set (bind address only)

### 1) Precheck / discover existing knob (REQUIRED before mutate)

Record before-state in receipt:

1. `ss -ltnp` filtered to port 9101 — confirm process + listen address.
2. Map PID to unit: `systemctl status` / `ps -fp` / `systemctl list-units '*stabil*' '*9101*'`.
3. Inspect **existing** config surfaces only (whichever already owns the bind):
   - **systemd:** `systemctl cat <unit>`; drop-ins under `/etc/systemd/system/<unit>.d/` (CHG-A pattern used `octopus-sensorium.service.d/` — expect analogous stability unit if that owns 9101).
   - **board.yaml** (or board config already loaded by that unit): existing `host` / `bind` / `listen` / `addr` field for stability/:9101 — edit that field only.
   - **stability python:** existing CLI flag / env (`HOST`/`BIND`/`LISTEN_ADDR` or equivalent already used) — flip that knob only.
4. Firewall before: nft/iptables/ufw rules mentioning 9101 (if any).
5. Doctor: locate existing `lan_9101` check; record current expected assertion (likely loopback-only / tunnel SoT).

**STOP** if :9101 is not owned by an identifiable existing stability/doctor control-plane service — do not invent a listener.

### 2) Apply LAN bind (minimal)

1. Prefer drop-in / env override / board.yaml field over editing vendor unit or rewriting python.
2. Set listen to `0.0.0.0:9101` OR `192.168.0.182:9101` (prefer explicit LAN IP if the existing knob supports host-only bind).
3. Host firewall ACL (if active): allow LAN subnet only (e.g. `192.168.0.0/24`) to TCP 9101; refuse WAN/open-internet.
4. `daemon-reload` if systemd touched; restart **only** the 9101-owning unit.

### 3) Doctor `lan_9101` implications (do not invent new doctor features)

- After LAN bind, any doctor check that asserts loopback-only or requires tunnel SoT may **FAIL** — expected; document in receipt; do **not** Doctor auto-patch.
- If an existing doctor note/field named `lan_9101` already exists, update it to reflect LAN-open + this auth token + timestamp.
- If no such field exists, do **not** invent a new doctor subsystem — record implication in the execute receipt only.

### 4) Verify

1. On Pi: `ss` shows intended LAN/non-loopback listen for :9101.
2. From laptop on LAN (no `ssh -N -L`): reach the **existing** health path on `http://192.168.0.182:9101/` (do not invent endpoints).
3. Confirm MQTT 1883 / WAVE0 / torch / keys / CHG-C untouched.

### 5) Receipts

- Board evidence JSON + TO-LAPTOP exchange ack citing this package path.
- Include before/after listen addresses, unit name, config path edited, firewall delta, doctor `lan_9101` implication note.

## Explicitly forbidden

- WAVE0 actuators invent/unlock/arm; MQTT invent/open 1883; private key export/rewrite; zero-fill; re-run CHG-C
- Doctor auto-patch; torch WM; invent new protocol/port/service/API
- WAN/open-internet exposure; change auth/TLS/payload schema beyond bind + ACL
- PWM/legs/root action_executor/arm reflex/planner; in-place hash rewrite; casual truncate
- Laptop writer SSH/mutate (sensoriom executes)

## Success criteria

- :9101 reachable on LAN from owner laptop without `ssh -N -L`
- Bind change used **existing** stability/board.yaml/systemd/env knob only
- Firewall LAN-scoped if present; doctor `lan_9101` implications documented; ROLLBACK.md path clear; no forbidden surfaces touched
