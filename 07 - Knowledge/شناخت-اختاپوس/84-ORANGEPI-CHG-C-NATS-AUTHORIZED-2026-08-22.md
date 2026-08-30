# 84 - Orange Pi CHG-C NATS capacity authorized (2026-08-22)

**AEST:** 2026-08-22T18:28:49+10:00  
**Auth ID:** `OCTOPUS-ORANGEPI-CHG-C-NATS-20260822`  
**Links:** [[83-ORANGEPI-CHG-ABD-AUTHORIZED-2026-08-22]] · evidence `06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-C-NATS-2026-08-22/` · prior ABD `06-EVIDENCE/OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22/`

## Decision

Owner authorized Orange Pi package **C (NATS capacity) only** after ABD A+D+B PASS and post-ABD soak PASS. Executor: **sensoriom** on `sensorium-opi5pro` (192.168.0.182). Laptop writes plans + OWNER-CHG grant only — does not SSH/mutate the Pi. Board2 GitHub creds remain deferred.

## Package

| CHG | Summary |
|-----|---------|
| C1 (first) | JetStream retention trim / stream limits on safe streams; prefer limit tighten over purge |
| C2 (if needed) | Raise NATS `MemoryMax` via drop-in to **768M** preferred; **1G** hard ceiling with free-RAM proof; never unconstrained |

**Baseline:** MemoryMax 512MiB; MemoryCurrent ~498–523M; peak 512M; NRestarts=0; active ~4d+.

**Not authorized:** E compaction · Board2 GitHub creds · MQTT 1883 · leg01 · WAVE0 unlock

## Still forbidden (global)

private keys/make-root-v2 · MQTT 1883 / PWM / legs / root action_executor · arm reflex · planner · Doctor auto-patch on Pi · torch WM · open 9101 to LAN · zero-fill sensors · in-place hash rewrite · unconstrained memory · leave WAVE0 actuators

## Next

Paste `SENSORIOM-EXECUTE-BRIEF.txt` to sensoriom; collect C receipts on TO-LAPTOP exchange; keep Board2 wire queued until creds authorized separately.

## Execution result
- C1 PASS JetStream retention; MemoryCurrent ~487M→~58M
- C2 MemoryMax raise NOT applied
- WAVE0 locked; MQTT/leg untouched
