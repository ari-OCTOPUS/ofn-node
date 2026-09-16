# Pi UNDISCOVERED top 10 — 2026-08-23 (post EDGE-NEXT + homeo mirror)

Live notes baked in. No PWM/ARM. Pack: this folder + Pi `/var/lib/octopus/evidence/session-undiscovered-20260823/`

1. **PHYSICAL_ESTOP** — safety_mcu ABSENT; soft latch only (`SOFTWARE_LATCH`). soft≠physical.
   - paths: `/etc/octopus/config/board.yaml`, snapshot `safety` block

2. **ESP32** — Phase B / physical sensor ingest still deferred (owner WAVE0: no parts buy yet).
   - paths: owner strategy memory; Pi state has no live ESP32 lane

3. **HOMEO_FRESHNESS** — `homeo_ok` still intermittent; `unknown=['prediction_calibration']`. Authority mirror OK; freshness HOLD remains.
   - paths: `/var/lib/octopus/state/homeostasis/latest.json`, `/opt/octopus/scripts/stability_monitor.py`, `OCTOPUS-HOMEO-MIRROR-ALIGN-2026-08-23`

4. **DOCTOR_RESIDUAL** — doctor PASS but `metrics_observation_age` not present on :9101; `boot_report.json` ancient (not live bus SoT).
   - paths: `/var/lib/octopus/state/doctor/latest.json`, `/var/lib/octopus/state/boot_report.json`, stability `:9101/metrics`

5. **QUARANTINE_THERMAL** — still on disk: `OCT-SENSE-053.THERMAL-RANGE_CHECK.json`, `wave01-range.json`.
   - paths: `/var/lib/octopus/state/quarantine/`

6. **MQTT** — live listen `127.0.0.1:1883` only (WAN closed). Risk is stale CLOSED docs vs SoT `LOCAL_LOOPBACK_AUTH_OPEN__WAN_KEEP_CLOSED`.
   - paths: `/etc/mosquitto/`, `/var/lib/octopus/state/mqtt/`

7. **FEEDS** — live `ok_count=7` / `expected=7` / `fail=[]` (less dark than feared); still weak on reading-quality / long-soak confidence / total field clarity.
   - paths: `/var/lib/octopus/state/homeostasis/feeds_snapshot.json`, `/var/lib/octopus/state/external_feeds/`

8. **GATEWAY_POST_FREEZE** — v1 only diagnostics executable; other former cmds dark by design; laptop→NATS:4222 direct still timed out (E2E via Pi publish).
   - paths: `command_gate.py`, `NATS_CONTRACT_BL01.json`, `OCTOPUS-EDGE-NEXT-2026-08-23\m3-allowlist\`

9. **NATS_ACL** — `octopus-core` E2E user present; production Core ACL beyond diagnostics + secret rotation policy still open.
   - paths: `/etc/nats-server.conf`, `/etc/octopus/secrets/nats-core-e2e.env`

10. **TELEGRAM_CONTROL** — keep dark on Pi (Board2 only). Must not become WAVE0 control.
   - paths: Board2/marketing; contradiction-scan pack

Also-seen: STORAGE stamp present; GAP-001 maintenance-window close may still need owner test.
