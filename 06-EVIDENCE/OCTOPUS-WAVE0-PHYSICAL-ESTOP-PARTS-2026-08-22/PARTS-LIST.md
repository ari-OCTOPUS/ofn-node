---
tags: [octopus, wave0, physical-estop, parts-list, 2026-08-22]
date: 2026-08-22
timezone: Australia/Sydney
---

# 91 / PARTS-LIST — WAVE0 Path H physical e-stop (Orange Pi 5 Pro style)

**Evidence package:** `F:\backup\06-EVIDENCE\OCTOPUS-WAVE0-PHYSICAL-ESTOP-PARTS-2026-08-22\PARTS-LIST.md`  
**Obsidian mirror:** `F:\backup\07 - Knowledge\octopus\91-WAVE0-PHYSICAL-ESTOP-PARTS.md`  
**Written (AEST):** 2026-08-22T22:40:00+10:00  
**Board class:** Orange Pi 5 Pro style (`sensorium-opi5pro` @ 192.168.0.182)  
**Target path:** WAVE0 **Path H** `operator_at_estop` (physical)

## Honest status (do not invent PASS)

| Layer | State | Evidence |
|---|---|---|
| Software estop latch | **PROVE PASS** | `06-EVIDENCE\OCTOPUS-ORANGEPI-WAVE0-EXECUTE-2026-08-22\FROM-PI\RECEIPT-WAVE0-ESTOP.json` → `result=PROVE_PASS_SOFTWARE_LATCH` |
| Hardware / Path H | **BLOCKED_NEED_ESTOP** — **NOT PASS** | Same receipt: `safety_mcu=ABSENT`, `estop_channel=NOT_PRESENT`, `labeled_estop_pin_mapping=NONE_FOUND`, `gpio_pwm_invented=false` |
| Meaning | Software latch **≠** physical operator_at_estop | Latch is reversible software kill only; does not satisfy Path H |

**Hard rules for this list:** no PWM invent; no invented GPIO pin numbers; no claim that buying parts = unlock. Wiring/pin assignment requires a later discover + owner sign-off package after hardware arrives.

Prices are **ESTIMATE** only (AUD primary, USD rough), retail hobby/industrial ballpark as of 2026-08 — verify before purchase.

---

## Parts

### 1) NC mushroom e-stop pushbutton — **REQUIRED**

| Field | Value |
|---|---|
| What | 22 mm or 40 mm **Normally Closed (NC)** maintained / twist-to-release mushroom head, industrial panel mount |
| Why | Operator_at_estop physical interrupt; NC so wire-break / unplug fails safe (open = stop) |
| Class | Safety-rated where practical (e.g. IEC 60947-5-5 style); dual NC contacts preferred if feeding a safety relay |
| Qty | 1 (recommend +1 spare OPTIONAL) |
| ESTIMATE | AUD 25–80 / USD 15–50 |
| Notes | Do **not** use momentary-only without a latching safety relay if you need maintained stop |

### 2) Safety relay / contactor class — **REQUIRED** (for any power path to actuators)

| Field | Value |
|---|---|
| What | Safety relay (category-oriented) **or** contactor with force-guided / mirror contacts that drops actuator **power** when e-stop opens |
| Why | MCU/GPIO alone is not a safety disconnect. Path H needs power-side removal, not only a software flag |
| Class | Prefer a listed safety relay module (e.g. single-channel e-stop monitoring with reset) over a bare coil relay for anything that can move |
| Qty | 1 minimum |
| ESTIMATE | AUD 80–350 / USD 50–220 (module); contactor-only cheaper but weaker as "safety class" |
| Notes | Software latch PROVE PASS does **not** replace this. Size contacts to actuator supply current (TBD on discover — do not invent amp ratings here) |

### 3) GPIO / optocoupler isolation interface — **REQUIRED** (sense channel to Pi)

| Field | Value |
|---|---|
| What | Optocoupler (or isolated digital input module) between e-stop/safety-relay **monitor contact** and Orange Pi GPIO input |
| Why | Protect Pi 3.3 V domain; avoid feeding raw 24 V industrial circuits into SoC pins; keep fail-safe sense of "estop asserted" |
| Class | Bidirectional clarity: one side = dry NC monitor from safety relay; Pi side = 3.3 V logic via opto |
| Qty | 1 channel minimum (2 OPTIONAL for dual-channel sense) |
| ESTIMATE | AUD 5–40 / USD 3–25 (breakout / PLC-style isolated DI) |
| Notes | **No PWM invent. No pin number invent.** `labeled_estop_pin_mapping=NONE_FOUND` on board today — assign pins only in a later discover receipt after hardware exists. Do not claim OCT-SENSE-088 or PWM paths. |

### 4) Cable / wiring — **REQUIRED**

| Field | Value |
|---|---|
| What | Flexible multi-core for e-stop loop (recommend dual NC channels if relay requires); separate low-voltage sense pair to opto; ferrules; panel glands |
| Suggested | 0.5–1.0 mm² (AWG 20–18) for 24 V e-stop loop; keep sense wiring short and strain-relieved |
| Qty | Enough for panel → enclosure → Pi (measure run; typically 2–5 m kit) |
| ESTIMATE | AUD 15–60 / USD 10–40 |
| Notes | Yellow/red e-stop convention; label both ends. Keep actuator power cabling separate from Pi USB/Ethernet |

### 5) Enclosure / panel — **REQUIRED** (operator reachable)

| Field | Value |
|---|---|
| What | Insulated enclosure or machine panel cutout so mushroom is **reachable by operator without opening the Pi case** |
| Class | IP54+ if workshop dust/liquid risk; e-stop on **yellow background** per common machine practice |
| Qty | 1 |
| ESTIMATE | AUD 20–120 / USD 15–80 |
| Notes | Pi itself stays in its own case; e-stop is operator hardware, not a hat soldered "for now" |

---

## Optional (nice-to-have, not Path H blockers by themselves)

| Item | Role | ESTIMATE |
|---|---|---|
| Spare NC mushroom head | Maintenance swap | AUD 25–80 / USD 15–50 |
| Illuminated reset PB (blue/green) | Supervised reset after e-stop clear (if safety relay requires monitored reset) | AUD 15–50 / USD 10–35 |
| 24 V DIN PSU (if not already present) | Industrial e-stop loop supply | AUD 40–120 / USD 25–80 |
| DIN rail + terminals | Clean wiring inside enclosure | AUD 20–70 / USD 15–45 |
| Second isolated DI channel | Dual-channel e-stop sense diversity | AUD 5–40 / USD 3–25 |
| Cable mute / shield | Noisy motor environments | AUD 10–40 / USD 5–25 |

**Not on this list (explicitly out of scope / forbidden invent):** PWM drivers, motor H-bridges, leg actuators, "temporary" direct GPIO→coil without relay, MQTT as e-stop transport, software-only "good enough for Path H".

---

## Integration notes (honest)

1. Buy/install physical chain **before** any Path H hardware unlock package.
2. After install: discover labeled pin mapping on Pi; write a new evidence receipt; **then** owner may authorize Path H — not before.
3. MQTT enable ABD (separate package) is **not** a substitute for this e-stop chain.
4. Keep software latch in place as defense-in-depth; it remains ≠ physical.

## Rough kit total (REQUIRED only)

| Bundle | ESTIMATE |
|---|---|
| Lean (mushroom + basic safety relay + opto + cable + small enclosure) | AUD **150–650** / USD **100–420** |
| Stronger (listed safety relay + DIN PSU + proper panel) | AUD **300–900** / USD **200–600** |

Label every quote **ESTIMATE** until a supplier cart is locked.

## Related evidence

- `F:\backup\06-EVIDENCE\OCTOPUS-ORANGEPI-WAVE0-EXECUTE-2026-08-22\FROM-PI\RECEIPT-WAVE0-ESTOP.json`
- `F:\backup\06-EVIDENCE\OCTOPUS-ALL-DOORS-2026-08-22\POINTERS.md`
- Season rollup: WAVE0 hardware = KEEP_LOCKED / BLOCKED_NEED_ESTOP
