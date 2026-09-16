# OCTOPUS Edge — Stage2 Architecture AS-IS vs TO-BE
**Date:** 2026-08-23 (Australia/Sydney)  
**Scope:** Orange Pi `sensorium-opi5pro` + laptop Core `F:\backup\_ops`  
**Mode:** READ-ONLY discovery (no mutate, no E2E execute)  
**Inputs:** Stage0–1 audit DEGRADED; owner answers E/B/F + A+C+D+E

## 1. AS-IS (proven from live board)

### Host / runtime
| Item | Value |
|------|--------|
| Hostname | `sensorium-opi5pro` |
| OS | Linux 6.1.115 aarch64 (DietPi-class) |
| Agent unit | `octopus-sensorium.service` → `/opt/octopus/venv/bin/python -m octopus_sensorium.app` |
| Code root | `/opt/octopus/current` → release `sensorium-software-v1` (+ `wave0-current` sibling) |
| PYTHONPATH | `/opt/octopus/current/src` |
| User | `octopus` (ProtectSystem=strict; no PWM device allow) |
| Watchdog | WatchdogSec=180 (drop-in) |
| MemoryMax | 1536M (YELLOW raise) |

### Control / data plane today
```
                    LAN 192.168.0.0/24
Laptop Core (_ops) ----?----> nats://192.168.0.182:4222  (JetStream)
                                      |
                    +-----------------+------------------+
                    |                                    |
            nats-server (nats user)              mosquitto 127.0.0.1:1883
            http monitor 127.0.0.1:8222           auth, WAN CLOSED
                    |
         octopus-sensorium (user sensorium)
         publishes: octopus.sensor.*, sensorium.*, world.*, audit.*
         subscribes: octopus.command.*, octopus.leg.*, _INBOX.*
                    |
         +----------+----------+------------------+
         |          |          |                  |
   host sensors  meta sensors  evidence store   offline buffer
   (thermal/    (anomaly/     /var/lib/octopus
    process/     contradiction…)
    fs/sys)

Side paths (not in sensorium process):
  octopus-external-feeds.timer → ingest_phase_a.py → NATS OBSERVATION (OCT-FEED-*)
  octopus-homeo-feeds-snapshot.timer → homeo_feeds_snapshot.py → JSON advisory only
  octopus_doctor_readonly.py (script; STALE in Stage1 audit)
```

### JetStream streams (code SoT in `natsbus.STREAMS`)
SENSORIUM, OBSERVATION, FEATURE, SENSOR_HEALTH, WORLD, AUDIT, COMMAND, LEG

### Safety / authority (code + live SoT)
- Code defaults: `ACTUATOR_AUTHORITY=NONE`, `MQTT_STATE=DISABLED`, `LEG_AUTHORITY=DENIED`, `WAVE0_MAX_AUTONOMY=OBSERVE_ONLY`
- Live soft unlock: `PERMITTED_SOFTWARE_A0` + software latch (≠ physical estop)
- MQTT SoT: `LOCAL_LOOPBACK_AUTH_OPEN__WAN_KEEP_CLOSED`
- App docstring: **Never issues actuator commands**
- Isolation: `assert_no_pwm_write`, reject actuator manifests
- Physical Path H / ESP32 / safety_mcu: **ABSENT / deferred**

### What exists vs what is missing for “Edge Gateway”
| Present | Missing / UNKNOWN |
|---------|-------------------|
| NATS client (`natsbus` / `messaging/nats_client`) | Dedicated Edge Gateway process/service name |
| Subject helpers + offline buffer | Proven Core→Edge `collect_diagnostics` E2E |
| Command gate (ALLOWED/FORBIDDEN) | Typed identity state machine as first-class module export for Core |
| Doctor readonly script | Fresh Doctor PASS (Stage1 = STALE) |
| Homeo feeds snapshot (advisory) | Homeostasis as active repair (by design: diagnose-only) |
| Evidence under `/var/lib/octopus` | Unified evidence schema synced with Core `_ops` |

### Laptop Core (Stage2 note)
- Owner: Core = `F:\backup\_ops`
- Stage2 did **not** deep-scan Core code in this pass; TO-BE assumes Core will own command initiation and consume edge evidence over NATS.

## 2. TO-BE (target Edge architecture)

```
Core (_ops)  --auth NATS-->  Edge Gateway (new thin layer OR evolved sensorium command path)
                                |
                    +-----------+-----------+
                    |                       |
              Diagnostics API         Observe plane (existing)
              collect_diagnostics     sensors + feeds + homeo snap
              identity SM             NATS publish OBSERVATION/...
              evidence pack write     doctor readonly findings
                                |
                         Safety gate (unchanged hard locks)
                         ARMED=false until owner GO
                         no PWM/GPIO/ESP32 without Path H
```

### Design principles (locked)
1. **Diagnose ≠ mutate** — Doctor/Homeostasis never auto-apply without owner path.
2. **Process alive ≠ service active ≠ functional health ≠ E2E success** (Stage1 definitions).
3. **MQTT stays loopback-auth**; WAN closed.
4. **Soft latch ≠ physical estop**.
5. Edge Gateway mutations only **after** this Stage2 pack + explicit GO (owner D).

## 3. Backlog (severity / deps / tests)

| ID | Item | Sev | Depends | Test / prove |
|----|------|-----|---------|--------------|
| BL-01 | Document + freeze NATS subject contract (Core↔Edge) | P0 | Stage2 | Contract JSON + consumer dry-run |
| BL-02 | Design `collect_diagnostics` E2E (plan only) | P0 | BL-01 | Plan review; no execute |
| BL-03 | Implement Edge Gateway diagnostics handler | P1 | BL-02 + GO(D) | Unit + NATS roundtrip mock |
| BL-04 | Identity / readiness SM export for Core | P1 | BL-01 | State table tests |
| BL-05 | Doctor freshness: rerun readonly + wire STALE policy | P1 | — | Doctor PASS + age SLA |
| BL-06 | Evidence pack schema sync Core↔Pi | P2 | BL-03 | Schema validate fixtures |
| BL-07 | MQTT bridge policy align code `DISABLED` vs live loopback | P2 | MQTT SoT | Contradiction close note |
| BL-08 | Physical Path H / ESP32 (deferred) | P3 | parts + estop | Hardware prove pack |
| BL-09 | Telegram Board2 vs Pi claim close | P2 | out_of_lane | Contradiction HOLD |
| BL-10 | git provenance for `/opt/octopus` (git_info empty) | P2 | — | RELEASE.json + SHA256SUMS as SoT |

## 4. Explicit non-goals this stage
- No Doctor mutate/repair
- No ARM / PWM / GPIO / ESP32
- No MQTT WAN open
- No E2E execute of collect_diagnostics
- No Git push

## 5. Next gate
Owner approved **A+C+D+E**: artifacts (A) done → this Stage2 (C) → E2E **plan** (E) → **then** D mutate only with fresh GO on concrete PR scope.
