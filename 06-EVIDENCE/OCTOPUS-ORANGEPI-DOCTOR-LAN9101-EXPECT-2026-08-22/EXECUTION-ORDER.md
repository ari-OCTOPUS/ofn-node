# EXECUTION-ORDER - Orange Pi doctor LAN:9101 expected PASS

**Authorization:** `OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-20260822`  
**Written (AEST):** 2026-08-22T21:19:00+10:00  
**Executor:** sensoriom @ sensorium-opi5pro (192.168.0.182)  
**WAVE0_hardware:** KEEP_LOCKED | **MQTT:** CLOSED  
**Scope:** doctor allowlist / expected listeners for **9101 only**  
**Hard:** do **NOT** close port; do **NOT** revert LAN OPEN

## Sequence

| Step | Action | Gate |
|------|--------|------|
| 0 | DISCOVER-FIRST: locate how live doctor encodes `metrics_bind` expected + `unexpected_listeners` / `lan_9101` (prefer config/allowlist under `/opt/octopus`; else script e.g. `octopus_doctor_readonly.py`) | Encode path + sha256 documented |
| 1 | Capture BEFORE: doctor readonly (`blocking_failed_ids`, full metrics_bind + unexpected_listeners + gap002_registry); `ss` :9101; UFW/firewall 9101 rules | BEFORE receipt |
| 2 | Confirm bind is intentional LAN OPEN (`0.0.0.0:9101` or `192.168.0.182:9101`) and UFW is LAN-only — **do not change bind/UFW allow direction** | SoT confirmed |
| 3 | Backup every file that will be edited (timestamped copy + sha256) | Backup PASS |
| 4 | Minimal patch: add expected bind allow `0.0.0.0:9101` **or** `192.168.0.182:9101`; set `lan_9101` expected true / allowlist entry; keep forbidden ports (`:8080`, `:9464`, etc.) unchanged | Syntax OK; 9101-only scope |
| 5 | Re-run doctor **readonly** | After report captured |
| 6 | Prove: `metrics_bind` PASS; `unexpected_listeners` PASS; `gap002_registry` still PASS; listen still LAN OPEN | PROVE PASS |
| 7 | Receipts + UFW LAN-only note + TO-LAPTOP exchange ack | Files present |

## Why this order

Discover prevents inventing a second doctor path. Backup enables rollback of allowlist only (not LAN bind). Prove gate requires both 9101 checks green **and** gap002 still passed **and** port still open.

## Parallelism

- Do **not** combine with WAVE0 hardware, MQTT, torch, Doctor auto-patch (broad), or LAN-9101 bind revert.
- Quiet board preferred.

## Abort

- Encode path missing / invent-only option → STOP, write NEED_OWNER path report (do not invent new doctor subsystem).
- Patch would require closing 9101 or reverting to loopback → STOP (forbidden).
- After patch, metrics_bind or unexpected_listeners still FAIL → STOP, do not broaden scope; report via ari.
- gap002_registry regresses → restore doctor files from backup immediately (ROLLBACK.md); do not touch open-gaps unless owner re-authorizes.
