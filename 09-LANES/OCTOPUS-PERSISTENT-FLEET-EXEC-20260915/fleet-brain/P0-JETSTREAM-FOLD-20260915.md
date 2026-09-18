# P0 JetStream fold (supersedes UNKNOWN `c6bba165…`)

**stamp_aest:** 2026-09-15 ~13:31  
**source:** PC `P0-DISCOVERY.json` sha `a2bd6c1233e7eb6d348cb9bdb36d2267c7b9e12d629dd1fedfce9db31964e4d9`  
**lane:** `F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-EXEC-20260915\P0\`  
**HOLD customer_send** · no ARCH enqueue · no dual-commander

## Verdict (folded)

| key | was (ARCH READ) | now (PC P0) |
|-----|-----------------|-------------|
| `JETSTREAM` | UNKNOWN / NOT_OBTAINED | **YES** |
| `JETSTREAM_CONSUMER_PROOF` | NOT_OBTAINED | **PARTIAL_ZERO_CONSUMERS** (8 streams, **0** consumers) |
| `NATS_ON_182` | suspected | **YES** (`nats-server` active) |
| `NATS_ON_138` | inactive (T0) | **ABSENT** — `nats-server.service` could not be found (`138-nats-status.txt`) |
| `:8222` from 138→182 | timeout | **UNREACHABLE** — monitor localhost-bound on 182; proof via mesh `root@182` → `127.0.0.1:8222/jsz` |

Prior ARCH packet `P0-JETSTREAM-READ` `c6bba165…` remains historical evidence of the LAN timeout path — **do not cite as current durability SoT**.

## Streams (8)

FEATURE · LEG · OBSERVATION · SENSORIUM · SENSOR_HEALTH · WORLD · AUDIT · COMMAND  

Subjects are **sensorium/audit/command** oriented (`octopus.sensor.*`, `octopus.audit.>`, `octopus.command.>`). **No fleet-brain job stream/consumer yet.**

## Durability implication for P1–P2

- JetStream **engine** proven on 182.  
- **Fleet job durability** still requires a dedicated stream+consumer (or explicit shadow jsonl on 138) — zero consumers ⇒ do not claim brain-job durable bus.  
- Existing streams may be reused only after subject ownership review (DENY hijacking SENSORIUM/AUDIT for customer_send).

## Companion hashes

| file | sha256 |
|------|--------|
| `P0-DISCOVERY.json` | `a2bd6c1233e7eb6d348cb9bdb36d2267c7b9e12d629dd1fedfce9db31964e4d9` |
| `182-jsz-rich.json` | `ae81fd5abd79bc7a45d9aed687368bf7f7bab9ed972ae207a2f8b84c9de34864` |
| `182-stream-names.json` | `d5cc9254bfe11a66f5244c818ad03a36e98a8029870531cd00fe2cfa5f54a599` |
| `P0-DISCOVERY.md` | `6e6a9697f18a1d133f8c5f4d7f2f9bf1d8e0a29060a8db4f6df3604fbbf04db0` |

