# CURRENT TRUTH - Handoff x OWNER_REVIEW merge - 2026-08-22

**Owner decision:** MERGE equal value (do not delete either narrative).  
**Auth:** `OWNER-AUTHORIZATION-MERGE.md` / token `OCTOPUS-HANDOFF-MERGE-2026-08-22`  
**Timezone:** Australia/Sydney (UTC+10)  
**Post-merge addendum:** `merged/POST-EXECUTE-ADDENDUM-2026-08-22.md` (executions after merge write)

## Live posture (authoritative)

| Axis | State | Notes |
|---|---|---|
| WAVE0 hardware | **KEEP_LOCKED** / **BLOCKED_NEED_ESTOP** | Observe-only hardware; do not arm hardware reflex; **no unlock in this package** |
| WAVE0 software overlay | **SOFTWARE_ONLY_A0** executed on Pi | Overlay `software_only_a0.enabled`; hardware remains KEEP_WAVE0_LOCKED |
| MQTT 1883 | **CLOSED** | No unlock in this merge / post-execute |
| actuator_authority | **NONE** | Soft/hardware actuators locked (software_only_a0 does not grant actuator authority) |
| ABD+C | **PASS** | ABD soak PASS; CHG-C **C1 only** PASS |
| Keys | **IN-PLACE OK** | Export/rewrite forbidden |
| Money/webhook/work_pump | **Laptop SoT** | Center restart after Phase-3 **PASS** (`RESTART-PROCESS.ps1 center`; PID 14856→35916 @ 2026-08-22 19:28:37 AEST). Money/WIRING: `mining_wire`/`crypto_wire`/`accounting_amounts=true`; webhook **policy-only** (no setWebhook). |
| Phase-3 CONTROL_URL | `https://cp.master-painting.com` | Board2 Phase-3 **PASS** |
| LAN stability :9101 | **OPEN on 192.168.0.182:9101** | Doctor `lan_9101=OPEN`; metrics `http://192.168.0.182:9101/metrics` HTTP **200**; laptop firewall verify may still be pending |
| Doctor (readonly re-run) | **gap_001_open cleared**; **gap002_registry** still blocking | `OCTOPUS_DOCTOR_MAY_MERGE=1` **live** (flags-loaded) |

**SoT for live Pi metrics:** `merged/LOCAL-STATE-CARD.json` + CHG receipts under `06-EVIDENCE/OCTOPUS-ORANGEPI-*` + `merged/POST-EXECUTE-ADDENDUM-2026-08-22.md` + `06-EVIDENCE/OCTOPUS-CENTER-RESTART-AFTER-PHASE3-2026-08-22/RESULT.json`.

## What was merged (equal value)

### From LAPTOP-AGENT-HANDOFF (Aug17, preserved)

- SSH / board identity, inbound drop boxes, signing playbook
- Stability tunnel contract (`ssh -N -L 9101.`), reflex advisory A0
- `do_not` list (PWM/legs/MQTT/make-root/key export/etc.)
- gap001 already **TESTED_PASS** in handoff (post-reboot)
- Cognition/shadow staging notes (torch not live replace)

Archived byte-copy: `archive/LAPTOP-AGENT-HANDOFF.json` (+ root copy, session reports)

### From OWNER_REVIEW (Aug17 + packs, preserved)

- Decision **KEEP_WAVE0_LOCKED**, `executed_actions=0`, `planner_invocations=0`
- `actuator_authority=NONE`, no OA-T7/A0, narrative ≠ evidence rule
- Owner-review T0-T6 pack + final pack + `NARRATIVE_NOT_EVIDENCE.md`
- Audit phrase discipline (do not call ledger head = 266)

Archived: `archive/OWNER_REVIEW_DECISION.json`, `archive/owner-review/`, `archive/owner-review-final/`

### Doctor narrative

- Live doctor `latest.json` (2026-08-22) archived; post-execute readonly re-run: **gap_001_open cleared**; still **gap002_registry** blocking
- Doctor **MAY_MERGE** present on laptop disk; `OCTOPUS_DOCTOR_MAY_MERGE=1` **live** (flags-loaded)
- Interpretation: doctor artifact ≠ ABD+C failure; does **not** unlock WAVE0 hardware or MQTT

## Post-merge executions (after merge write; see addendum)

Already executed on Pi / laptop disk (do **not** re-unlock MQTT or hardware WAVE0):

1. **WAVE0 SOFTWARE_ONLY_A0** - overlay `software_only_a0.enabled`; hardware still **KEEP_WAVE0_LOCKED** / **BLOCKED_NEED_ESTOP**; MQTT **CLOSED**
2. **LAN:9101** - bound `192.168.0.182:9101`; doctor `lan_9101=OPEN`; metrics HTTP 200; laptop firewall verify may still be pending
3. **Board2 Phase-3** - **PASS** (`cp.master-painting.com`)
4. **Doctor readonly re-run** - `gap_001_open` cleared; `gap002_registry` still blocking
5. **Doctor MAY_MERGE** on laptop disk; `OCTOPUS_DOCTOR_MAY_MERGE=1` live (flags-loaded)
6. **Center restart after Phase-3** - **PASS** (`RESTART-PROCESS.ps1 center`; BEFORE PID 14856 → AFTER PID 35916 @ 2026-08-22 19:28:37 AEST; single center + 1 RUN-TG-CENTER loop). Evidence: `06-EVIDENCE/OCTOPUS-CENTER-RESTART-AFTER-PHASE3-2026-08-22/RESULT.json`

## Superseded claims (Aug17 FAIL gaps)

1. **`gap_001_open` as live blocker** → **SUPERSEDED** by handoff `gap001.TESTED_PASS` + ABD soak PASS (2026-08-22) + post-execute doctor readonly re-run (cleared).
2. **Doctor FAIL as operational posture blocking ABD+C** → **SUPERSEDED** for CHG A/B/D/C1; WAVE0 **hardware** stays locked by **owner posture**, not by stale Aug17 gap list.
3. **`next_action` = only GAP-001 maintenance window** → **SUPERSEDED** as sole story; next locks are WAVE0 hardware/MQTT/actuator policy + optional CHG-E/torch + deferred money/bridge/PAT items + laptop firewall verify for :9101.
4. **Phase-3 prove pending (CF 530)** → **SUPERSEDED** by Board2 Phase-3 **PASS**.
5. **stability_9101 LOOPBACK_ONLY** → **SUPERSEDED** by LAN bind `192.168.0.182:9101` / doctor `lan_9101=OPEN` (laptop firewall verify may still be pending).
6. **Center restart in flight / pending** → **SUPERSEDED** by Center restart after Phase-3 **PASS** (PID 14856→35916 @ 19:28:37 AEST).

Still open / careful:

- Doctor may still flag `gap002_registry` until registry/checkpoint settle
- File-auths exist for doctor/torch/LAN:9101/CHG-E/WAVE0/MQTT but **this package does not execute MQTT or hardware WAVE0 unlocks**
- Unsigned ckpt / sign paths remain laptop responsibility (no key export)
- **Still deferred:** bridge key rotate **cancelled**; GitHub DietPi PAT **pending owner**; money unlock thematic commit **blocked by germline index.lock** (do **not** force / do **not** remove `.git/index.lock`)
- Laptop firewall verify for LAN:9101 may still be pending
- WAVE0 hardware **KEEP_WAVE0_LOCKED** / MQTT **CLOSED** unchanged

## Read order for next agent

1. `OWNER-AUTHORIZATION-MERGE.md`
2. `merged/CURRENT-TRUTH.md` (this file)
3. `merged/POST-EXECUTE-ADDENDUM-2026-08-22.md`
4. `merged/LOCAL-STATE-CARD.json`
5. `merged/LAPTOP-AGENT-HANDOFF.merged-2026-08-22.json`
6. `merged/OWNER_REVIEW_DECISION.merged-2026-08-22.json`
7. Receipts: ABD soak, CHG-C C1, Board2 OFN/CP-URL / Phase-3 PASS, keys-inplace, doctor MAY_MERGE, Center restart RESULT.json
8. Archives under `archive/` if reconstructing Aug17 context

## Explicit non-actions

- Do **not** unlock WAVE0 **hardware** / MQTT
- Do **not** `git add -A`
- Do **not** export/rewrite keys
- Do **not** delete either source narrative
- Do **not** remove `.git/index.lock` / force germline commit