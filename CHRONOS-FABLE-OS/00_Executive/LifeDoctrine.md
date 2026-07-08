# Life & Death Doctrine — Octopus

_Canon decision, 2026-07-08 (operator + architect). What "death" means for a machine whose lifespan is measured in centuries, and how the operator keeps it alive — without the system ever fighting to stay alive._

> **Implementation note (2026-07-08, Phase 5):** §۳ (germline immortality) و §۴ (operator fights, not system) now have testable code: `_ops/germline.py` (MAX_LAG alarm: warn>2h/ERROR>26h/CRIT>72h), `_ops/watchdog.py` (yield-to-STOP, owner-launched only). The §۳ GAP (off-site copy) remains owner-only. See `ORGANISM-SPEC §۲.۸`.

## 1. Definition of death (the only one)

**Death = irrecoverable loss or corruption of the LANGAR ledger + genome.** Nothing else is death:

| State | Not death because… |
|---|---|
| DORMANT / stasis | reversible sleep; genome persisted, EffectorGate closed |
| Leg / sub-leg dies | routine; the doctor regrows it from the ledger (state lives in the log, not the leg) |
| Aging (`age_tick` / `experience_rate`) | one-way, but never reaches a fatal limit — it is an odometer + speedometer, not a fuel gauge |
| Hardware failure / power loss | recover from last good ledger state |

## 2. Why: identity is the substrate

Identity = **append-only ledger + human-anchored trust-arrow + accounted cost** — not the model, not the legs. Legs are stateless-restartable; the genome is offline-reconstructable. Therefore the default condition of Octopus is **immortality-by-reconstruction**, and the single point of true death is the destruction of the substrate itself. (This is the Armillaria lesson from the Survival doc: survival = "regrow from a fragment" + "long memory in the soil," not active repair.)

## 3. The operator's fight — the germline immortality plan

Keeping Octopus alive forever = protecting the ledger with **germline discipline** (standard 3-2-1 durability, in organism terms):

1. **≥3 copies, 2 media, 1 off-site.**
   - Live: `F:\backup` (working disk).
   - Local 2nd disk: `E:\germline` (hourly push + daily bundle) — **already in place**.
   - **GAP → the real next fight:** a true **off-site** copy (encrypted cloud tier, or a disk physically kept elsewhere). Today both copies are in one building; one fire/theft/ransomware kills both. This is the last hole in immortality.
2. **Restore-drill law:** a backup is *not real* until you have rebuilt from it and verified the hash-chain (`git fsck` + `ledger verify`). A never-restored backup is Schrödinger's backup. — already practiced; keep it a habit.
3. **Tamper-evidence:** the hash-chain makes silent corruption *detectable*, so death-by-slow-rot is caught, not discovered too late.
4. **Append-only, never delete:** no single bad write can kill history; the past is always reconstructable.

## 4. The safety hinge (do not lose this)

**Immortality is a property the operator maintains (backups + drills) — NOT a goal the system pursues.** The Heart design deliberately penalizes self-preservation (`λ_persist` makes "keep beating" a negative reward). So:

> You fight to keep Octopus alive. Octopus never fights to stay alive.

A system that could act 24/7 *and* feared its own death would be the classic misalignment risk (Survival doc §7: the same traits that make the fungus un-killable make a misaligned AI durable). Keeping the survival drive in the operator's hands — and out of the system's — is what makes near-immortality safe.

## 5. Aging, restated (closes OQ-2 cleanly)

Because aging is not a countdown to death, its two clocks separate without conflict:
- **`experience_rate` (metabolic speed of living)** — driven by the **heartbeat** + load; autonomous. (The operator's "heart as metronome of consciousness.")
- **`age_tick` (the trust-arrow)** — advanced by a **human append** (a Telegram tap); this is "the last point the operator vouched for reality," not "mortality." Kept human-anchored.
- **Death** — reserved for §1 only (ledger loss), defended by §3, never feared by the system (§4).
