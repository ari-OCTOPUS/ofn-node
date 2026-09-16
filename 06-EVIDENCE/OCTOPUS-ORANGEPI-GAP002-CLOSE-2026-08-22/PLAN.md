# PLAN - Orange Pi GAP-002 registry close (open-gaps)

**Authorization / Token:** `OCTOPUS-ORANGEPI-GAP002-CLOSE-20260822`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER-AUTHORIZATION only (no SSH/mutate from this writer)  
**Written (AEST):** 2026-08-22T21:13:00+10:00  
**mutate_device:** true  
**WAVE0_hardware:** KEEP_LOCKED  
**MQTT:** CLOSED  
**owner_fix_all:** true

## Problem

- Live GAP-002 gap evidence already reports **`pass=true`** / **`CLOSED_BY_SIGNED_CHECKPOINT`** (historical board evidence under `sensorium-d14-verify` / state gaps).
- Doctor / registry path still treats gap002 as open: **`signature_does_not_close_registry`** / **`gap002_registry` NEED_OWNER**.
- Laptop health sweep (2026-08-22) recorded `doctor_gap.gap002_registry=unknown_not_found_in_quick_scan`.
- Laptop scan at package write: **`NEED-OWNER-GAP002.json` not present** under `F:\backup\**`; no local TO-LAPTOP exchange root found.

## Goal

Set **open-gaps** registry entry for **GAP-002** to **`pass=true`** + **`EXTERNALLY_CHECKPOINTED`** (or the exact CLOSED example enum/shape already used for other closed gaps), then prove doctor readonly no longer flags gap002_registry.

Prefer **CHG-A style**:
1. Backup file
2. Edit **only** GAP-002 fields
3. Re-run doctor **readonly**
4. Prove gap002 cleared

## Primary target path

`/opt/octopus/current/manifests/open-gaps.json`

If absent, document actual path from doctor/latest.json or manifests layout (do not invent a second registry without evidence).

## DISCOVER-FIRST (required if schema unknown)

Before any mutate:

1. Read current `open-gaps.json` (full file; capture sha256).
2. Read `doctor/latest.json` (or board-standard doctor report) noting the exact `gap002_registry` / `signature_does_not_close_registry` message and which path it cites.
3. Find a **CLOSED** gap entry in the same file (or sibling closed gap JSON) and match **GAP-002** field names/enums to that shape.
4. Confirm intended closure token: prefer **`EXTERNALLY_CHECKPOINTED`** with **`pass=true`**. If CLOSED examples use a different status string for signed/external checkpoint closure, use the documented CLOSED example â€” do not invent new enums.
5. Write DISCOVER receipt (paths, sha256 before, example CLOSED shape, planned patch JSON fragment) to board evidence + TO-LAPTOP exchange.

## Allowed change set

1. Timestamped backup of `open-gaps.json` next to original (or under `/var/lib/octopus/evidence/...`) + sha256 of backup.
2. Patch **only** the GAP-002 object fields needed for registry close (`pass`, `status` / closure reason, and any required companion fields copied from CLOSED examples â€” e.g. `closed_at`, `closure`, `note`). Leave all other gaps untouched.
3. Validate JSON parses after edit.
4. Doctor **readonly** re-run; capture before/after snippets proving gap002_registry cleared / no `signature_does_not_close_registry` for GAP-002.
5. Receipts: before/after sha256, patched fields, doctor excerpts, TO-LAPTOP ack.

## Explicitly forbidden

- WAVE0 hardware unlock; GPIO/PWM/legs actuate
- MQTT 1883 open/pair/publish (KEEP CLOSED)
- Zero-fill keys or sensors
- Private keys / make-root-v2 / key export
- Inventing crypto or inventing schema fields not present in CLOSED examples
- Silent ledger hash rewrite
- Doctor auto-patch / merge (readonly prove only)
- torch; LAN:9101; money/webhook/work_pump
- arm reflex; planner; unbounded root action_executor
- `git add -A`
- Laptop SSH mutate (sensoriom executes)

## Success criteria

- `open-gaps.json` GAP-002 shows `pass=true` and EXTERNALLY_CHECKPOINTED (or matched CLOSED enum).
- Doctor readonly no longer reports gap002_registry NEED_OWNER / `signature_does_not_close_registry` for GAP-002.
- Backup + sha256 + rollback path recorded.
- WAVE0 remains KEEP_LOCKED; MQTT remains CLOSED; no key material touched.

## Evidence refs (laptop)

- `F:/backup/06-EVIDENCE/OCTOPUS-HEALTH-SWEEP-2026-08-22/HEALTH.json`
- `F:/backup/06-EVIDENCE/sensorium-d14-verify-2026-08-18/msg-evidence-latest.json`
- `F:/backup/06-EVIDENCE/OCTOPUS-HANDOFF-MERGE-2026-08-22/from-pi/owner-review/gap-002-checkpoint-spec.md`
- Style refs: `OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22`, `OCTOPUS-ORANGEPI-CHG-E-EXECUTE-2026-08-22`