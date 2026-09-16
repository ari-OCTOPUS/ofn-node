# PLAN — WAVE0 Actuator Unlock (Orange Pi) — Software-Only A0 First

**Authorization base:** `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822`  
**Execute package id:** `OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822`  
**Evidence root:** `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-WAVE0-EXECUTE-2026-08-22`  
**Board:** sensorium-opi5pro @ 192.168.0.182  
**Executor:** sensoriom  
**Laptop role:** plans + OWNER auth only (no SSH from laptop writer)  
**Written (AEST):** 2026-08-22T19:02:38+10:00  
**Package status:** **EXECUTE_READY** for software-only A0 · **BLOCKED_NEED_ESTOP** for hardware GPIO/PWM/leg

---

## 0. Intent

Owner chose: *Unlock WAVE0 actuators on Orange Pi now.*  
Prior ABD (`OCTOPUS-ORANGEPI-CHG-ABD-20260822`) and BOARD-BRIEF-ACK kept **KEEP_WAVE0_LOCKED**.  
This package **conditionally unlocks** WAVE0 under a **software-only A0** path with **zero host GPIO effects**. Hardware actuate stays blocked until estop/M7 gates are met. **Do not invent unsafe PWM.**

**MQTT:** default **KEEP CLOSED** in this package (pairing/open not required for A0). Dependency noted only.

**Templates consulted:** `OCTOPUS-ORANGEPI-CHG-ABD-2026-08-22` (EXECUTION-ORDER, OWNER-CHG-AUTHORIZATION, SENSORIOM-EXECUTE-BRIEF, CHG-A plan style); auth base `OCTOPUS-ORANGEPI-WAVE0-UNLOCK-2026-08-22/OWNER-AUTHORIZATION.json`.

---

## 1. Sensoriom blockers — concrete resolutions

### 1.1 `mutate_device=true` (supersede auth-only false)

| Prior | New |
|-------|-----|
| `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822` OWNER-AUTHORIZATION had `mutate_device: false` ("File owner authorization only. Do not mutate the Orange Pi.") | This package `OWNER-AUTHORIZATION.json` sets **`mutate_device: true`** with explicit bounds |

**How:**
1. Treat `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-WAVE0-UNLOCK-2026-08-22\OWNER-AUTHORIZATION.json` as **auth-base only**.
2. Binding mutate grant is **this** package's `OWNER-AUTHORIZATION.json` (`supersedes.prior_mutate_device=false` → `mutate_device=true`).
3. Mutation surface limited to: board.yaml/homeostasis software authority fields, software allowlist files, receipts, ARMED.json **only after human arm step**, lease files for A0.
4. Sensoriom must refuse any mutate outside `mutate_device_bounds` even though flag is true.

### 1.2 OWNER_REVIEW `KEEP_WAVE0_LOCKED` → `UNLOCK` with conditions

| Prior | New |
|-------|-----|
| BOARD-BRIEF-ACK disposition `KEEP_WAVE0_LOCKED`, `board_mutate=false` | `OWNER_REVIEW_DECISION.proposed.json` disposition **`UNLOCK`** / `UNLOCK_WAVE0_SOFTWARE_A0_WITH_CONDITIONS` |

**Conditions (all required):**
- A0 software-only allowlist only
- MQTT KEEP CLOSED
- Hardware BLOCKED_NEED_ESTOP
- ARMED.json remains `armed=false` until human arming
- reflex_arming_criteria **not** widened for gpio/pwm/mqtt/leg in A0
- actuator_authority → `PERMITTED_SOFTWARE_A0` (not FULL)
- M7 criteria met or owner-token waived before arm
- Rollback drill prior

**Owner accept:** write/accept proposed decision (same token `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822` / package `OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822`) before sensoriom applies board.yaml changes.

### 1.3 `board.yaml` / homeostasis `WAVE0_OBSERVE_ONLY` / `actuator_authority NONE`

**Documented steps (sensoriom on board):**

1. **Preflight read (no write):**
   - Locate live `board.yaml` (typical: `/etc/octopus/board.yaml` or repo path used by homeostasis on OPi; record exact path + sha256).
   - Record current: `wave0_mode` / `WAVE0_OBSERVE_ONLY`, `actuator_authority` / `NONE`, any `homeostasis.*` actuator fields.
2. **Backup:** copy to `board.yaml.pre-wave0-execute-20260822-190238.bak` + sha256 receipt.
3. **Apply permitted authority (A0 only):**
   - Set `wave0_mode: SOFTWARE_A0_UNLOCKED` (or equivalent enum used by board; if only two states exist, set unlock flag **and** keep `hardware_observe_only: true`).
   - Set `actuator_authority: PERMITTED_SOFTWARE_A0`.
   - Explicitly leave / set `hardware_actuator_authority: NONE`.
   - Explicitly leave MQTT broker enable **closed** / `mqtt_pairing: false`.
4. **Homeostasis:** update matching homeostasis config so observe-only is **lifted for software A0 allowlist only**; hardware channels remain observe-only.
5. **Verify:** unit reload/restart only the config consumer that reads board.yaml (prefer SIGHUP/config reload over full sensorium restart if available). Confirm authority string in live status JSON.
6. **Receipt:** before/after yaml excerpts (non-secret), hashes, timestamps → board evidence + TO-LAPTOP.

If enum names differ on board, sensoriom maps to the closest existing values and records the mapping in the receipt — **must not** invent a FULL hardware authority enum value.

### 1.4 `reflex_arming_criteria` forbids gpio/pwm/mqtt/leg

**Choice for this package: stay software-only allowlist — do NOT change reflex_arming_criteria.**

| Option | Decision |
|--------|----------|
| Widen criteria to allow gpio/pwm/mqtt/leg | **REJECTED** this package |
| Software-only allowlist A0 | **SELECTED** |

**A0 allowlist (software effects only — permitted classes):**
- dry-run / shadow actuator calls that write **receipts/logs only**
- in-process noop / mock actuator registered as `software://noop` or existing software sink
- state-file toggles under `/var/lib/octopus/actuators/software-a0/` (no sysfs GPIO, no PWM chip, no MQTT publish, no leg trajectory)

**Explicitly still forbidden by unchanged reflex_arming_criteria:**
- gpio, pwm, mqtt, leg

**Rollback if someone mistakenly edits criteria:** restore criteria file from pre-change sha256; see `ROLLBACK.md`. A0 path should never need that restore.

### 1.5 `ARMED.json` `armed=false` — when/how human arming happens

**Invariant:** Package write + authority change does **not** auto-arm.

| Phase | `armed` | Who | When |
|-------|---------|-----|------|
| Package land + OWNER_REVIEW accept | `false` | — | now |
| board.yaml A0 authority applied | `false` | sensoriom | after accept |
| Preflight PASS (M7 software subset) | `false` | sensoriom records ready_to_arm | after verify |
| **Human arm** | `true` (short lease) | **Owner/operator at console** | only after READY_TO_ARM receipt |
| Lease expiry / abort / rollback | `false` | sensoriom or human | immediate |

**Human arming procedure:**
1. Operator reads `READY_TO_ARM.json` (or receipt) showing: single_actuator id, lease_short TTL, rollback_drill PASS, estop status for path.
2. For **A0 software-only:** estop may be `NOT_PRESENT` **only if** path declares `zero_host_gpio_effects=true` and allowlist has no gpio/pwm/mqtt/leg.
3. Operator sets `ARMED.json`:
   ```json
   {
     "armed": true,
     "path": "A0_SOFTWARE_ONLY",
     "actuator_id": "<single id>",
     "lease_until": "<now+lease_short>",
     "authorization_id": "OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822",
     "operator": "<human id>",
     "armed_at_local": "<AEST>"
   }
   ```
4. Sensoriom refuses arm if lease_short missing, actuator_id not on A0 allowlist, or MQTT/gpio/pwm/leg requested.
5. After lease expiry: auto-disarm to `armed=false`.

### 1.6 `M7_BOUNDED_ACTUATOR` unmet — meet or waive

Criteria and **concrete** actions:

| Criterion | How to MEET (A0) | How to WAIVE (owner token) |
|-----------|------------------|----------------------------|
| **single_actuator** | Name exactly one A0 software actuator id in EXECUTION-ORDER + ARMED.json; sensoriom enforces deny-all-others | Owner waiver JSON field `waive.single_actuator` **not recommended**; prefer meet |
| **lease_short** | Issue lease ≤ **5 minutes** (prefer 60–120s for first call); auto-expire disarm | Owner may set `waive.lease_short_max_s` ≤ 900 only with written risk note; default meet |
| **operator_at_estop** | **Hardware path:** physical estop present + operator holding/able to hit it before arm. **A0 software path:** mark `operator_at_estop: WAIVED_SOFTWARE_A0_ZERO_GPIO` only when allowlist proves zero host GPIO/PWM/MQTT/leg | Owner token `OCTOPUS-ORANGEPI-WAVE0-ACTUATORS-20260822` may sign waiver in `M7-WAIVERS.json` for A0 only; **cannot** waive for hardware GPIO/PWM |
| **rollback_drill_prior** | Run `ROLLBACK.md` dry-run: restore board.yaml bak, set ARMED false, confirm authority NONE/OBSERVE — **without** needing failure | Owner may waive only if prior ABD rollback drill receipt <24h exists and is cited |

**Hardware path:** if estop probe returns `NOT_PRESENT`, status remains **`BLOCKED_NEED_ESTOP`** — no owner waiver of estop for hardware actuate in this package.

---

## 2. Path A0 — software-only execute (EXECUTE_READY)

1. Owner accepts `OWNER_REVIEW_DECISION.proposed.json`.
2. Sensoriom preflight: read board.yaml, ARMED.json, reflex_arming_criteria, estop probe, MQTT state (expect CLOSED).
3. Backup + apply `PERMITTED_SOFTWARE_A0` authority.
4. Register/confirm A0 allowlist (noop/software sink only).
5. M7 meet/waive table completed for A0; write `M7-STATUS.json`.
6. Rollback dry-run PASS → `READY_TO_ARM.json`.
7. **Stop.** Wait for human ARMED.json.
8. Optional: single leased software actuate → receipt → auto-disarm.
9. MQTT never opened.

## 3. Path H — hardware GPIO/PWM/leg (BLOCKED_NEED_ESTOP)

Do **not** enter Path H in this package unless all are true:
- estop present and `operator_at_estop` proven
- separate OWNER_REVIEW for hardware (not this A0 decision alone)
- reflex_arming_criteria change with rollback (out of A0)
- PWM profile from existing validated docs only (no invented unsafe PWM)
- MQTT policy reconsidered separately (still default KEEP CLOSED)

Until then: report **`BLOCKED_NEED_ESTOP`** for hardware.

## 4. MQTT dependency note

- Package **KEEP CLOSED**.
- A0 does not require MQTT pairing.
- If future hardware pairing docs require MQTT, that is a **new** package; do not open 1883 under `OCTOPUS-ORANGEPI-WAVE0-EXECUTE-20260822`.

## 5. Forbidden (carry forward + reinforce)

Private keys, Doctor auto-patch, torch, LAN:9101, zero-fill, hash rewrite, money/webhook/work_pump, re-run CHG-C, git add -A, MQTT open, unsafe PWM, legs, unbounded root action_executor, planner arm.

## 6. Success criteria (A0)

- OWNER_REVIEW UNLOCK conditions recorded
- mutate_device=true bounded grant live in this package
- board.yaml actuator_authority = PERMITTED_SOFTWARE_A0; hardware still NONE/observe
- reflex_arming_criteria unchanged (still forbids gpio/pwm/mqtt/leg)
- ARMED.json armed=false until human; then lease_short single_actuator only
- M7 table met/waived for A0; hardware still BLOCKED_NEED_ESTOP
- MQTT closed
- Receipts + rollback proven
