# OWNER-ORDER — WAVE0 soft e-stop unlock (software latch only)

**Package:** `F:\backup\06-EVIDENCE\OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-2026-08-23\`  
**Written (AEST):** 2026-08-23T01:04:00+10:00  
**Timezone:** Australia/Sydney (UTC+10)  
**Authorizer:** owner via ari  
**Tokens:** `OCTOPUS-WAVE0-SOFT-ESTOP-UNLOCK-20260823` + `OCTOPUS-ALL-DOORS-OPEN-20260822`

## Owner choice

- **ACCEPT risk** for WAVE0 **hardware unlock with software latch only**.
- **No physical e-stop** required for this soft-unlock path.
- Physical Path H / PARTS-LIST remains **deferred (LATER)** — not cancelled; still required for true `operator_at_estop` physical PASS.
- Soft-unlock is **authorized** now under owner risk acceptance.

## Accepts

WAVE0 hardware unlock with software latch only; no physical e-stop.

## Rollback

Assert software latch → `KEEP_LOCKED`.

## Honest boundaries (do not invent PASS)

| Layer | State after this order |
|---|---|
| Software estop latch | Already **PROVE PASS**; remains defense-in-depth |
| Soft unlock (owner risk) | **AUTHORIZED** (this package) — auth files only until executor runs unlock |
| Physical Path H / parts | **DEFERRED** — still `BLOCKED_NEED_ESTOP` for physical; buy/install later |
| MQTT 1883 | Unchanged — enable ABD WRITTEN pending execute; listener CLOSED until sensoriom |

## Links

- Auth: `OWNER-AUTHORIZATION.json`
- Result / remaining doors: `RESULT.md`
- Season rollup: `F:\backup\07 - Knowledge\octopus\90-SEASON-ROLLUP-2026-08-22.md`
- Parts (physical deferred): `F:\backup\07 - Knowledge\octopus\91-WAVE0-PHYSICAL-ESTOP-PARTS.md`
- ALL-DOORS: `F:\backup\06-EVIDENCE\OCTOPUS-ALL-DOORS-2026-08-22\`
