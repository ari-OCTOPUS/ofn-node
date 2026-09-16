# OCTOPUS HEART — FULL AUDITABLE PROPOSAL (NO APPLY)
Stamp: 2026-08-25T07:52:00+10:00
Producer: Ios (vault). Owner KEEP: three hearts + pulse_arbiter — do not delete/rewrite.
Action this wave: PROPOSE ONLY. No code edit, no flag flip, no wire open, no jsonl delete.

## Locked (do not implement against)
- Vote producers: cardiac / control_law / rhythm
- `pulse_arbiter.py` consensus, color, brake, pulse-arbiter.v1
- No silent rehash of SIM to open production_wire
- No invent Δ_self to pass Gate-0

## Live contradiction (SoT to resolve later, not now)
| Surface | Period | Wire |
|---|---|---|
| arbiter-latest | ~98.34s GREEN 3/3 | wire_open=true, advisory_only=true |
| heart.shadow / control_law | ~265–267s | production_wire.open=false |
| organism.heart | period_shadow ~267s | wire_open=false |
| organism.arbiter | 98.34s | wire_open=true |
| cardiac vote | ~42.4s mice | GREEN |

One body, three clocks. Proposal is to name a single **reported SoT** without merging hearts.

---

## P0 — Name one reported period (docs + reader only)
**Goal:** humans/agents stop treating 98s and 267s as the same "heartbeat".
**Do:** add a tiny `heart/sot_period.py` *reader* (or a field on heartstate) that emits:
`{advisory_period_s: arbiter.effective, shadow_period_s, organism_sleep_s, sot: "advisory|shadow|split", reason}`
**Don't:** change arbiter math; don't feed shadow period into arbiter; don't open production_wire.
**Done when:** heartstate-latest (or a new `sot-period-latest.json`) shows both numbers + which one organism actually slept on. Tests: read-only fixture, no live tick required.
**Risk:** R0. Reversible: delete reader.

## P1 — Gate-0 / producers audit (read + evidence)
**Goal:** explain why Δ_self=0 forever blocks hybrid wire (one of two CLOSED reasons).
**Do:** evidence note: last N velocity-stream / heart-signals samples; whether delta_self estimator has enough samples (MIN_DELTA=48); whether Gate-0 is still intended lock vs stale lock.
**Don't:** write fake CONFIRMED events; don't lower MIN_DELTA; don't set gate0 true.
**Done when:** `GATE0-AUDIT.json` with counts, last timestamps, verdict INTENDED_LOCK | STALE_NO_INPUT | BROKEN_PRODUCER.
**Risk:** R1 (read ledger/chrono). No mutate.

## P2 — SIM hash / sog_math lock hygiene
**Goal:** second CLOSED reason is "hash ≠ SIM-REPORT". Audit freshness of `PULSE-EQUATIONS-LOCKED.json` vs `sim_heart` report.
**Do:** compare hashes; record mismatch fields; propose *owner* re-lock procedure (run sim → write lock → evidence) as a later GO.
**Don't:** rewrite CANONICAL anchors; don't auto-rehash; don't flip OCTOPUS_WIRE_BIO / PULSE.
**Done when:** `SIM-LOCK-DIFF.json`. Status likely HOLD_UNTIL_OWNER_GO.
**Risk:** R2 if someone "fixes" hash to open wire — forbid.

## P3 — doctor_setpoint + ADR-001 (keep contract, document)
**Goal:** keep Doctor→HeartParams (band, not period). Document current band 0.46–4.45 vs default 0.5–6.0 and daily_beat_cap 2000 vs code default 288.
**Do:** table in proposal evidence; optional later: align env CARDIAC_DAILY_BEAT_CAP comments with live 2000.
**Don't:** let Doctor write period_s.
**Done when:** ADR-001 still holds in a 1-page CHECK.
**Risk:** R0.

## P4 — work_pump + heart_wires (dead cadence trim — propose list only)
**Goal:** list templates/wires that fire on beat but no-op (flag off).
**Do:** inventory work-plan.json vs last work-log; thesis/coherence/identity flags vs heart-wires-latest.json.
**Don't:** delete templates this wave; propose disable-list for later GO.
**Done when:** `WIRES-DEAD.md` with last-run + flag.
**Risk:** R1 if we disable a silent health snapshot — so propose only.

## P5 — money / life / fuel / budget_judge (boundary)
**Goal:** decide which are *heart-axis* vs *should move out* of `_ops/heart/`.
**Propose (not move):**
- stay near heart: `fuel_meter` (API burn per beat), `budget_judge` (beat budget, dry default)
- candidate extract later: `money_pulse`, `life_economy`, `life_currency` (business metaphor; not pacemaker)
**Don't:** move files this wave (breaks imports).
**Done when:** owner ticks stay/move per module.
**Risk:** R1 import graph.

## P6 — state rot (archive, never rm latest)
**Goal:** shrink noise without losing SoT.
**Propose later GO:** rotate/quarantine append-only giants older than lock date:
- arbiter-shadow.jsonl (~1.0MB) + divergence (~2.9MB)
- tick-timing.jsonl (~1.6MB)
- math-control-observe.jsonl (~2.0MB)
- fuel-stream / velocity-stream / money-pulse jsonl
Already have 2026-08-08 quarantine sidecars — same pattern.
**Don't:** delete `*-latest.json`, arbiter-latest, heart-shadow-latest, heartstate-latest.
**Done when:** owner GO + checksummed archive folder.
**Risk:** R1 if latest overwritten.

## P7 — doc drift
**Goal:** HEARTS-BRAINS-4D-STATUS / Metaphor Decode / HEARTS-TIME quote old periods (75s / 42s / 126s).
**Do:** patch *status docs only* to "read live arbiter-latest + shadow" or stamp SUPERSEDE pointing at this pack.
**Don't:** rewrite Octopus_Heart_Design_v1 theory as if live.
**Done when:** STATUS file has 2026-08-25 live row.
**Risk:** R0.

---

## Implementation order (when owner GO later)
1. P0 reader (safe)
2. P1 Gate-0 evidence
3. P2 SIM lock diff
4. P7 docs
5. P4/P6 only with explicit GO
6. P5 move = separate refactor GO
Never: arbiter rewrite, heart removal, production_wire open, invent Δ_self

## Explicit non-goals
- No Shopify / Board2 / money movement
- No live Telegram
- No PWM / WAVE0
- No apply in this pack

## Owner next
Tick which P# may become a later GO. Until then this folder is proposal-only.
