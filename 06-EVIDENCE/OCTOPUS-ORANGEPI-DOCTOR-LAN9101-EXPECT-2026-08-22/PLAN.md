# PLAN - Orange Pi doctor LAN:9101 expected PASS (metrics_bind + unexpected_listeners)

**Authorization / Token:** `OCTOPUS-ORANGEPI-DOCTOR-LAN9101-EXPECT-20260822`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER-AUTHORIZATION only (no SSH/mutate from this writer)  
**Written (AEST):** 2026-08-22T21:19:00+10:00  
**mutate_device:** true  
**WAVE0_hardware:** KEEP_LOCKED  
**MQTT:** CLOSED  
**owner_fix_all:** true  
**Scope:** doctor allowlist / expected listeners for **9101 only**

## Problem

- GAP-002 registry close **passed** (`gap002_cleared=true`; `gap002_registry` passed).
- Doctor readonly still **FAIL** blocking on:
  - `metrics_bind`
  - `unexpected_listeners`
- Root cause: **LAN:9101 is intentionally OPEN** on `0.0.0.0` (UFW LAN-only) per `OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-2026-08-22`. Doctor still encodes **loopback-only** expectation (`expected: 127.0.0.1:9101`, `lan_9101: false`).
- Treating intentional LAN OPEN as FAIL is wrong SoT. **Do not close the port. Do not revert LAN OPEN.**

## Goal

Update doctor **expected** encoding so intentional LAN:9101 (`0.0.0.0:9101` **or** `192.168.0.182:9101`) + UFW LAN-only note is **PASS** for `metrics_bind` and `unexpected_listeners` only. Prove doctor readonly no longer FAILs those two; **gap002_registry stays passed**.

## Laptop discovery (partial — DISCOVER-FIRST still required on Pi)

Historical / handoff evidence shows:

| Surface | Finding |
|---------|---------|
| Live report shape | `octopus.doctor-check.v1` with `expected` / `observed` |
| `metrics_bind` (pre-LAN) | `expected: "127.0.0.1:9101"`; pass when loopback |
| `unexpected_listeners` (pre-LAN) | `expected: { forbidden: [], lan_9101: false }` |
| Script path (owner-review) | `/opt/octopus/scripts/octopus_doctor_readonly.py` |
| Hardcoded logic (historical copy) | `lan_9101 = any(9101 line without 127.0.0.1:9101)`; metrics_bind requires `127.0.0.1:9101` and `not lan_9101`; unexpected_listeners requires `not lan_9101` |
| GAP-002 after receipt | `doctor_after_blocking: [metrics_bind, unexpected_listeners]`; gap002 cleared |
| LAN bind SoT | Intentional OPEN (`0.0.0.0` or `192.168.0.182`) + UFW LAN-only |

Exact **live** encode path (config vs hardcoded vs policy allowlist) may differ under `/opt/octopus/current/**` — **sensoriom must DISCOVER-FIRST** before mutate.

## DISCOVER-FIRST (required)

Before any mutate:

1. Capture doctor readonly BEFORE: status, `blocking_failed_ids`, full `metrics_bind` + `unexpected_listeners` check objects, and `gap002_registry.passed`.
2. Confirm live listen: `ss -lntup` for `:9101` — expect `0.0.0.0:9101` and/or `192.168.0.182:9101` (do **not** change bind).
3. Confirm UFW/firewall: LAN-scoped allow for TCP 9101 (document rule); do **not** open WAN.
4. Locate encode surface under `/opt/octopus` (and `/etc/octopus` if referenced):
   - Prefer **config/allowlist/policy** knob for expected bind / `lan_9101` if one already exists.
   - Else script that sets `metrics_bind` / `unexpected_listeners` expected (historical: `octopus_doctor_readonly.py`).
   - Document actual path + sha256 + relevant snippet in DISCOVER receipt.
5. Prefer minimal edit: add expected bind allow for `0.0.0.0:9101` **or** `192.168.0.182:9101` and set `lan_9101` expected **true** (or equivalent allowlist entry) + UFW note in receipt. Do **not** invent new doctor subsystems or new ports.
6. Write DISCOVER receipt (paths, sha256 before, planned patch fragment) to board evidence + TO-LAPTOP.

## Allowed change set

1. Timestamped backup of every file edited + sha256.
2. Patch **only** doctor expected/allowlist logic for **9101** (`metrics_bind` + `unexpected_listeners` / `lan_9101`).
3. Accept observed bind `0.0.0.0:9101` **or** `192.168.0.182:9101` as PASS when UFW/firewall remains LAN-only (note in receipt; do not weaken ACL).
4. Validate JSON/YAML/Python syntax after edit (as applicable).
5. Doctor **readonly** re-run; capture before/after proving:
   - `metrics_bind` passed
   - `unexpected_listeners` passed
   - `gap002_registry` still passed
6. Receipts: before/after sha256, bind observed, UFW note, doctor excerpts, TO-LAPTOP ack.

## Explicitly forbidden

- Close TCP 9101 / stop metrics listener / revert to `127.0.0.1:9101`
- WAN/open-internet exposure; broaden UFW beyond LAN
- WAVE0 hardware unlock; MQTT open; zero-fill; key export
- Doctor auto-patch / merge beyond this 9101 expected-listener scope
- Invent new checks/ports/services; edit unrelated doctor checks
- Touch open-gaps / rewrite gap002 (must stay pass=true)
- torch; money/webhook/work_pump; arm reflex; planner; root action_executor
- `git add -A`; laptop SSH mutate

## Success criteria

- Doctor readonly: `metrics_bind` **PASS**; `unexpected_listeners` **PASS**.
- `gap002_registry` remains **PASS** / cleared.
- Live listen still LAN OPEN (`0.0.0.0:9101` or `192.168.0.182:9101`); UFW LAN-only documented.
- Backup + rollback path recorded; WAVE0 KEEP_LOCKED; MQTT CLOSED; no key material touched.

## Evidence refs (laptop)

- `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-GAP002-CLOSE-2026-08-22/RECEIPT-GAP002-CLOSE.from-pi.json`
- `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-GAP002-CLOSE-2026-08-22/EXECUTE-SUMMARY.json`
- `F:/backup/06-EVIDENCE/OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-2026-08-22/`
- `F:/backup/06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/from-pi/doctor-latest.json`
- `F:/backup/06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/from-pi/owner-review/tests/octopus_doctor_readonly.py`
- `F:/backup/06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/from-pi/owner-review/doctor-spec.md`
- Style refs: `OCTOPUS-ORANGEPI-GAP002-CLOSE-2026-08-22`, `OCTOPUS-ORANGEPI-LAN-9101-EXECUTE-2026-08-22`
