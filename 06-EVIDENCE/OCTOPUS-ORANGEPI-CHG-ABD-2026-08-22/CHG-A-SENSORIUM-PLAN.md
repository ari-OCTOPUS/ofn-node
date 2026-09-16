# CHG-A — Sensorium watchdog / deferred index load

**Authorization:** `OCTOPUS-ORANGEPI-CHG-ABD-20260822` (package A+B+D)  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER-CHG grant only (no SSH/mutate from this writer)  
**Written (AEST):** 2026-08-22T16:53:45+10:00

## Problem (evidence)

- `BOARD-DEEP-DIAGNOSIS-ACK`: BOOTING loads ~**4.7G** evidence+indexes; **WatchdogSec=30** → SIGABRT before READY; `store.py` `_save_index` full JSON rewrite remains.
- Sensorium NRestarts ~**1411** (SENSORIOM-DELTA-1521); crash storm.

## Goal

Stop the sensorium watchdog storm so the unit reaches READY and pets the watchdog before heavy index work completes (or with a longer WatchdogSec window).

## Allowed change set (pick ONE primary path; may combine carefully)

### Path A1 — WatchdogSec raise (preferred first, lowest code risk)

1. Record before state: `systemctl show` for the sensorium unit → `WatchdogSec`, `NRestarts`, `ActiveEnterTimestamp`, `FragmentPath`.
2. Drop-in override only (prefer drop-in over editing vendor unit):
   - `WatchdogSec=120` minimum; prefer **180–300s** if BOOTING historically exceeds 2 minutes on 4.7G load.
3. `daemon-reload` + restart **sensorium only**.
4. Confirm READY within new window; watchdog pets; NRestarts stops climbing.

### Path A2 — Defer heavy index load until after READY + watchdog pet

1. Locate sensorium boot path that calls `store.py` `_save_index` / full index rewrite during BOOTING.
2. Split boot:
   - Phase READY: load minimal config, open store read-light, signal systemd READY, start watchdog pet loop.
   - Phase POST-READY: heavy index load / rewrite (or skip rewrite if index fresh).
3. Keep `_save_index` full rewrite behavior documented; do **not** casually truncate observations; do **not** zero-fill sensors.
4. If a tainted CPU window YAML is implicated in boot load, **quarantine** (move aside with hash receipt) file named like `TAINTED_WINDOW_sensorium-cpu.yaml` — quarantine only, no content rewrite.

### Incidental to A (allowed)

- Quarantine `TAINTED_WINDOW_sensorium-cpu.yaml` with before/after path + sha256 receipt.
- Do **not** perform broad E compaction.

## Explicitly forbidden during A

- open 9101 to LAN; MQTT/PWM/legs; arm reflex; planner; Doctor auto-patch; private keys/make-root-v2; zero-fill sensors; truncate observations casually; in-place hash rewrite; unconstrained WM; torch WM; C/E package work.

## Verification

- Unit stays active ≥15–30 min without SIGABRT watchdog kill.
- READY reached; journal shows pet / no Watchdog timeout.
- NRestarts plateau (delta ~0 over soak window).
- Receipt JSON under board evidence + copy summary to `/var/lib/octopus/inbound/TO-LAPTOP/exchange/` if channel available.

## Rollback

1. Remove WatchdogSec drop-in (or restore previous `WatchdogSec=30`).
2. Revert any defer-index code change to last known-good deploy hash (record hash before apply).
3. Restore quarantined YAML from quarantine path if boot regresses without it.
4. `daemon-reload` + restart sensorium; confirm behavior matches pre-CHG baseline (document honestly even if baseline was crashing).
5. Stop further A mutation; report FAIL with journals.

## Success criteria

- Sensorium READY stable; watchdog storm stopped; no forbidden surface touched; receipts written.
