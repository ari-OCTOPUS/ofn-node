# CHG-C - NATS capacity (JetStream trim first, then capped MemoryMax)

**Authorization:** `OCTOPUS-ORANGEPI-CHG-C-NATS-20260822` (package C only)  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER-CHG grant only (no SSH/mutate from this writer)  
**Written (AEST):** 2026-08-22T18:28:49+10:00  
**Prior:** ABD `OCTOPUS-ORANGEPI-CHG-ABD-20260822` A+D+B PASS; post-ABD soak PASS (`SOAK-POST-ABD-ACK.json`)

## Problem (evidence)

- NATS unit near **MemoryMax=512MiB**: MemoryCurrent ~**498–523M**, peak **512M**, **NRestarts=0**, active ~**4d+**.
- Sensorium recovered post-ABD (WatchdogSec=180, NRestarts=0, MemoryCurrent ~1.0G). Latent **bus risk** if pub/sub + JetStream retention grow further while NATS sits at the 512M ceiling.
- Prior ABD package **excluded C**; owner now authorizes **C only**. Board2 GitHub creds remain deferred.

## Goal

Relieve NATS memory pressure with the **least invasive reversible change**: prefer JetStream retention / stream limits first; raise systemd MemoryMax only if trim is insufficient or unsafe. Keep MemoryMax capped. Do not touch MQTT 1883, legs, or WAVE0 actuators.

## Allowed change set (ordered)

### Path C1 — JetStream retention trim / stream limits (PREFERRED FIRST)

1. Before state (record in receipt):
   - `systemctl show <nats-unit>` → MemoryMax, MemoryCurrent, MemoryPeak, NRestarts, ActiveEnterTimestamp, FragmentPath.
   - JetStream inventory: stream names, `messages`, `bytes`, `first_seq`/`last_seq`, current `max_msgs` / `max_bytes` / `max_age` / `discard` / storage type (file vs memory). Prefer `nats` CLI or server HTTP monitoring already local — do **not** open new LAN listeners.
2. Safety screen before trim:
   - Identify streams that are **observability / telemetry / ephemeral** vs any that are durability-critical for ABD ledger or WAVE0.
   - **Do not purge** streams needed for ledger integrity or actuator command history.
   - Prefer tightening **limits going forward** (`max_age`, `max_bytes`, `max_msgs`, discard=old) over destructive one-shot purge when possible.
3. Apply **minimal** limit tighten or retention trim on safe streams only; one stream at a time; record before/after `bytes` and MemoryCurrent.
4. Re-check MemoryCurrent after each change; allow brief settle. Target: MemoryCurrent **comfortably under** 512M (e.g. ≤~400M) with headroom.
5. If C1 alone restores ≥~20% headroom under 512M and NRestarts stay 0 → **stop; do not raise MemoryMax**.

### Path C2 — Raise MemoryMax (only if C1 insufficient or unsafe)

1. Before: same `systemctl show` snapshot + free board RAM (`MemAvailable`). Account for sensorium ~1.0G, WM/skill ~128M caps, OS headroom on ~3.8Gi class board.
2. Drop-in override only (prefer drop-in over editing vendor unit):
   - **Proposed default: `MemoryMax=768M`** (evidence-based: current ~0.5G working set + ~50% headroom after sensorium recovery traffic).
   - **Hard ceiling this CHG: `MemoryMax=1G`** — use 1G **only** if 768M still OOMs / peaks after C1 and free RAM proof shows ≥~1.2G MemAvailable after raise (do not starve sensorium/OS).
   - Never remove MemoryMax; never set infinity / unconstrained.
3. `daemon-reload` + restart **NATS unit only** (not sensorium/WM/skill unless they fail health after NATS bounce — then document; do not expand scope).
4. Confirm unit active; MemoryCurrent under new max with headroom; NRestarts does not climb.

## Explicitly forbidden during C

- MQTT **1883** / MQTT broker changes; PWM/legs; **leg01** user work; root action_executor  
- arm reflex; planner; Doctor auto-patch on Pi; private keys / make-root-v2  
- torch WM; open **9101** to LAN; zero-fill sensors; in-place hash rewrite  
- unconstrained memory / deleting MemoryMax  
- E evidence compaction; Board2 GitHub credential setup  
- Unlock or leave WAVE0 actuators; any actuator mutate  

## Verification

- MemoryCurrent stays under effective limit with clear headroom (post-C1 under 512M, or post-C2 under 768M/1G).
- NRestarts remains 0 (or delta 0 over soak ≥15–30 min).
- NATS clients (sensorium bus) reconnect healthy; no MQTT 1883 involvement.
- Receipt JSON: path chosen (C1/C2/both), before/after MemoryMax+MemoryCurrent+peak, stream limit deltas, free RAM note, forbidden-surface untouched affirmation.
- Copy summary to `/var/lib/octopus/inbound/TO-LAPTOP/exchange/` if channel available.

## Rollback

### C1 rollback
1. Restore prior stream `max_age` / `max_bytes` / `max_msgs` / discard from receipt.
2. Do **not** attempt to resurrect purged messages; document data loss window if any purge was used.
3. Re-measure MemoryCurrent; if pressure returns, escalate to C2 rather than re-purging aggressively.

### C2 rollback
1. Remove MemoryMax raise drop-in (or restore `MemoryMax=512M`).
2. `daemon-reload` + restart NATS; confirm return to 512M cap.
3. If instability after rollback: keep NATS running at last stable known-good; STOP further mutation; report FAIL with journals.

## Success criteria

- NATS capacity risk relieved (trim and/or capped raise ≤768M default / ≤1G ceiling); MemoryCurrent monitored; NRestarts=0; no MQTT 1883 / leg01 / WAVE0 / forbidden surfaces touched; receipts written.