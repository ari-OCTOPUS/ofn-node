# E2E Plan — `collect_diagnostics` (DESIGN ONLY — DO NOT EXECUTE)
**Token / session:** OCTOPUS-EDGE-AUDIT-STAGE0-1-2026-08-23 / Stage2  
**Control plane:** `nats://192.168.0.182:4222` (owner F)  
**Core:** `F:\backup\_ops` (owner E)  
**Evidence OK:** `/var/lib/octopus/evidence` + `F:\backup\06-EVIDENCE` (owner B)

## Goal
Prove Core can request diagnostics and receive a complete, schema-valid pack from Edge without mutating host safety state.

## Actors
| Role | Component | Notes |
|------|-----------|-------|
| Initiator | Laptop Core `_ops` | Publishes command; waits response / JetStream consumer |
| Bus | nats-server on Pi | Auth user with COMMAND publish + response subscribe |
| Edge | Sensorium / future Edge Gateway | Handles `collect_diagnostics`; never arms actuators |
| Evidence | Pi + laptop | Dual-write receipts |

## Proposed message contract (draft — freeze in BL-01)
### Request
- **Subject:** `octopus.command.sensorium` (existing COMMAND stream)  
- **Name:** `collect_diagnostics`  
- **Required fields (align with command_gate):** request_id, issued_at, issuer, command, params, nonce/signature if required by gate  
- **params (draft):**
  - `window_minutes` (default 360)
  - `include`: [`systemd`,`nats`,`mqtt_sot`,`feeds`,`homeo`,`doctor`,`wave0_soft`,`disk`]
  - `mutates`: **false** (hard)
  - `timeout_sec`: 60

### Response
- **Subject:** `octopus.sensorium.diagnostics.<request_id>` **or** reply-to `_INBOX.*`  
- **Body:** JSON envelope
  - `status`: PASS | DEGRADED | FAIL | UNKNOWN
  - `host`: hostname, machine_id, uptime
  - `checks[]`: {id, status, evidence_ref, note}
  - `artifacts[]`: relative paths under evidence session
  - `safety`: ARMED, actuator_authority, mqtt_policy, soft_latch
  - `schema`: `octopus.edge.diagnostics.v1`

## Sequence (happy path)
1. Preflight readonly: NATS listen 4222; sensorium active; ARMED=false  
2. Core publishes request (auth as Core user — **credential path TBD; do not invent**)  
3. Edge validates command_gate (FORBIDDEN if mutates=true or unknown cmd)  
4. Edge runs **readonly** collectors only (reuse Stage1 check taxonomy)  
5. Edge writes session under `/var/lib/octopus/evidence/session-diag-<ts>/`  
6. Edge publishes response + optional JetStream OBSERVATION/AUDIT audit line  
7. Core copies/pulls pack to `F:\backup\06-EVIDENCE\...` and asserts schema  

## Failure / status taxonomy (must not collapse)
| Outcome | Meaning |
|---------|---------|
| PASS | All included checks PASS; pack complete |
| DEGRADED | Process/bus up but ≥1 STALE/DEGRADED check (e.g. Doctor STALE) |
| FAIL | Collector error or gate reject |
| UNKNOWN | Bus timeout / no response / auth miss |
| ABSENT | Hardware path requested but not present (ESP32) — not FAIL |

## Safety rails (execute phase — still future)
- Refuse if `params.mutates != false`
- Refuse PWM/GPIO/ESP32 includes
- No systemd restart, no package upgrade, no firewall change
- Soft latch untouched
- Abort if Watchdog would be opened by agent (isolation)

## Test matrix (when EXECUTE approved)
| # | Case | Expect |
|---|------|--------|
| T1 | Happy path all includes | DEGRADED or PASS with pack |
| T2 | mutates=true | gate REJECT / FAIL |
| T3 | NATS down | Core UNKNOWN timeout |
| T4 | Unknown command | FORBIDDEN |
| T5 | include esp32 | ABSENT not FAIL |
| T6 | Concurrent 2 requests | both request_ids distinct packs |

## Preconditions before any EXECUTE
1. BL-01 contract JSON frozen on laptop evidence  
2. Core NATS credentials exist (discover, don’t invent)  
3. Owner explicit EXECUTE grant (separate from this plan)  
4. Stage1 audit pack linked as baseline  

## Explicit statement
**This document is a plan only. No E2E was executed in Stage2.**
