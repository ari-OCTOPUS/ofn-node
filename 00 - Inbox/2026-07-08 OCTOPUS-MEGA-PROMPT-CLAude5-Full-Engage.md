# 🐙 OCTOPUS — MEGA-PROMPT for Claude 5 — Full Engagement & Autonomous Planning

> **Purpose:** This document contains everything needed to understand, plan, and continue building the Octopus organism — a self-evolving, self-learning autonomous system. Claude 5 should read this entirely, internalize the architecture, assess current state, plan remaining work, and begin execution — using full capacity across all reasoning dimensions.

> **Language:** Persian + English technical terms preserved. فازبندی درست پایین.
> **Created:** 2026-07-10 — by previous Claude session (Phase 0 ✅, Phase 1 ✅, Blueprint Phase 2 ✅)
> **Security:** Telegram bot token in `_ops/OCTOPUS.env` — treat as sensitive. NEVER log or expose.

---

# Part 0: WHO YOU ARE IN THIS PROJECT

You are the **Chief Architect AI** of the Octopus project. The human owner (Ari/آری) has built the foundation over 5 days (Jul 6-10, 2026). Your job:

1. **Understand the full architecture** — 15 organs, 10,765+ LOC production code, 72 test files
2. **Assess current state** — what's done, what's broken, what's deferred
3. **Plan the remaining phases** — Blueprint Phases 3-6 + cleanup + wiring gaps
4. **Execute autonomously** — within safety constraints (no auto-merge, no money spend, human at critical gates)
5. **Report progress** — structured handoff contracts after each phase

**Standing Rules (NON-NEGOTIABLE):**
- No auto-merge. No change to FITNESS/consolidation without held-out check.
- No money spend. Everything is shadow/paper ($0).
- Telegram bot token `[REDACTED — فقط در _ops/OCTOPUS.env — §۱۰]` and chat ID `[REDACTED — در OCTOPUS.env]` in `_ops/OCTOPUS.env` — `call` the `.bat` before Python or `channel=None` → RFCs stuck forever.
- Kill-switch: `_ops/STOP-ORGANISM` file = immediate stop.
- Live gate locked until 2026-07-21 (`opslib.live_gate_open` returns False).
- Evidence rule: every claim needs `file:line`. `[UNVERIFIED]` if you can't find it.
- Pre-register metrics BEFORE implementing. No moving goalposts.

---

# Part 1: WHAT IS OCTOPUS — THE FULL PICTURE

## 1.1 One-Sentence Definition

> Octopus is a **multi-agent income-generating organism** that runs 24/7 on Windows, autonomously observes markets, learns from experience, proposes self-improvements, and executes only human-approved actions — all within a $0 shadow budget until live gate opens.

## 1.2 Core Philosophy

The organism follows the **Evolutionary Doctor Blueprint** — an 8-step loop:

```
1. OBSERVE    → SCHOOL takes prediction error (not raw input)
2. CONSOLIDATE → Stable knowledge with sparse filter + BCM forgetting
3. PROPOSE    → DOCTOR suggests mutations; rate controlled by σ→1
4. ISOLATE    → Proposal runs in separate sandbox (not main loop)
5. EVALUATE   → Held-out Evaluator: "did it actually improve?"
6. GATE       → If ✅ + low-risk + threshold passed → merge queue; if 🔴 → human verdict
7. COMMIT/ROLLBACK → merge with tag, or revert to baseline
8. LOG        → episodic + metrics; back to step 1
```

**Autonomy Ladder:**
- **L0** — Everything manual; system only suggests.
- **L1** — Auto in sandbox, merge with human verdict. **← WE ARE HERE**
- **L2** — Auto-merge only for low-risk changes with 2 weeks L1 clean history.
- **L3** — Auto-merge broader set; human = observer + kill-switch.
- **L4** — Fully autonomous within budget. **Long-term goal only.**

## 1.3 Three Layers of the Organism

| Layer | Metaphor | Role | Modules |
|---|---|---|---|
| **Anatomy** (MycoLedger) | Tissue/Memory | Append-only event logging in hash-chained ledger + machine-readable state files | `opslib.py` (ledger bridge, paths, LockedJson) |
| **Physiology** (Heart) | Pulse/Flow | Always-on loop: 5-min tick, hourly heartbeat, daily tasks, status server | `organism.py` + `RUN-ORGANISM.bat` |
| **Metabolism** (Governor) | Energy/Budget | Unified telemetry → per-organ gate → shadow governor (allostatic epoch) → fitness/replication | `telemetry.py` · `organ_gate.py` · `governor_epoch.py` · `fitness.py` · `replication.py` |

## 1.4 The 7 Non-Negotiable Invariants

1. **Survival = persistence only** — λ_persist is negative; no "keep alive" reward channel
2. **Dormancy over resistance** — threat → DORMANT, never → higher capability
3. **Fail-closed by default** — all timeouts resolve to slower/narrower state
4. **Genome completeness when off** — Ring 0 append-only, cold-reconstructable
5. **EffectorGate choke-point** — single gateway; no component has direct effector handle
6. **Ring 0-4 access model** — capability tokens per ring; Awareness = Ring 2 only
7. **Kill-switch integrity** — out-of-band kill line; cannot be intercepted

## 1.5 The 10 Safety Invariants (I1-I10)

- **I1** append-only: ledger, SURVIVORS-QUEUE, heartbeat, logs — never rewrite/delete
- **I2** single-enforcer: budget_gate is the only enforcement point
- **I3** fail-closed: telemetry↔accounting mismatch = FREEZE all grants + CONFLICT to human queue
- **I4** numbers from file: every decision-making number from budgets.yaml
- **I5** double-gate live: no spend path before 2026-07-21 + without owner's ACTIVATION-*.flag
- **I6** budgets.yaml read-only
- **I7** acceptance only human: "accepted" = status='sent' in outbox (human click)
- **I8** anti-cancer: σ_effective≤1; MAX_CELLS=6; spawn depth=1; SPAWN=PROPOSAL only
- **I9** secret: keys only from env; never in md/log/exception
- **I10** anti-injection: topic=data only; whitelist only; GUARD_SENTENCE

---

# Part 2: ARCHITECTURE — ALL 15 ORGANS

## 2.1 Complete Module Map (`_ops/`)

```
_ops/
├── organism.py              # Main loop: kill-check → telemetry → epoch → daily → heartbeat → HTTP :8771
├── wiring.py                # Master wiring: apply_profile(), canonical_consolidation(), neural_stack
├── chrono.py                # Pacemaker + HLC + phi-accrual + LANGAR + EffectorGate + dual-clock
├── baseline.py              # Phase 0: snapshot capture + comparison
├── held_out_evaluator.py   # Phase 0: 5 fixed canary tests + ledger hash-chain verify
├── phase_gate.py            # Phase 0: pre/post phase check + transition gate (human verdict)
├── review_bus.py            # Phase 0: structured handoff contracts between phases
│
├── budget/
│   ├── opslib.py            # Core library: paths, env, micro-USD, flags, STOP/FREEZE, heartbeat
│   ├── telemetry.py         # Dual-source telemetry reader (ledger + brain)
│   ├── organ_gate.py        # Per-organ gate on budget_gate
│   ├── governor_epoch.py    # Allostatic epoch governor (pressure-following)
│   ├── fitness.py           # Per-cell fitness scoring (value/urgency/efficiency/human/waste)
│   ├── replication.py       # σ from ledger, spawn proposals, MAX_CELLS=6
│   ├── approval_channel.py  # Telegram approval channel (51KB, largest file)
│   ├── attribution.py       # Money attribution per organ/cell
│   ├── capability_gate.py   # Capability gating before organ execution
│   ├── reconcile.py         # Financial record reconciliation
│   ├── money_gate.py        # Financial transaction gate
│   ├── human_append_guard.py # Guard requiring human approval for append ops
│   ├── budgets.yaml         # Budget configuration (6.9KB)
│   └── epochs/              # 53 epoch JSON files (Jul 7-10)
│
├── doctor/
│   ├── doctor.py            # Main doctor: mine → RFC → sandbox → submit (27 checks)
│   ├── calibration.py       # Feedback loop: verdict history, should_skip_bottleneck
│   ├── evolution.py         # MAP-Elites + measured_lift + tournament_rank
│   ├── chamber.py           # Inner chamber: 4 voices, 6 constraints, ≤3 rounds
│   └── box/                 # B0 Numeric Core (14 files, pure math, no LLM/network)
│       ├── box.py           # Main box: run_tick/run_episode
│       ├── agent_state.py   # Part 10 schema: clip z∈[0,1], energy tracking
│       ├── dynamics.py      # x/z/M/G update: contractive f, clip u, bounded h
│       ├── warden.py        # E_box_max=0.02·E_total fail-closed, ρ(J)<1
│       ├── topology.py      # tree+k shortcuts (Part 11), O(N log N) edges
│       ├── archivist.py     # MERA-like multiscale coarse-grain memory
│       ├── primitive.py     # Recursive Proposer→Skeptic→Integrator
│       ├── sensors.py       # ρ(J) spectral radius + I(a;x) mutual info
│       ├── null_dreamer.py  # Baseline random control (scientific)
│       └── falsif_harness.py # Falsification harness
│
├── neural/
│   ├── consolidation.py     # Memory consolidation engine (ConsolidatedInsight dataclass)
│   ├── consolidation.json   # 474 cycles accumulated (115KB)
│   ├── latent_space.py      # ★ NEW Phase 2: SharedLatentSpace R^32, cosine retrieval
│   ├── encoders.py          # ★ NEW Phase 2: 5 deterministic encoders (hash-based SHA-256)
│   ├── neural_driver.py     # Neural subsystem driver
│   ├── hebbian.py           # Hebbian learning (numpy)
│   ├── sprint.py            # Sprint planning/execution
│   ├── circadian.py         # Circadian rhythm modeling
│   ├── nociceptor.py        # Pain/damage detection
│   ├── reflex.py            # Reflex arc implementation
│   ├── signal_hub.py        # Signal routing hub
│   └── hooks.py             # Hook points
│
├── afferent/
│   ├── ingest_raw.py        # Raw data ingestion (crypto + accounting)
│   ├── sensory_bus.py       # Sensory bus: routes incoming signals
│   └── school_bridge.py     # Bridge between school-memory and afferent layer
│
├── epistemics/
│   ├── contracts.py         # Epistemic contracts
│   ├── emit.py              # Epistemic signal emission
│   ├── metrics.py           # Epistemic quality metrics
│   ├── readers.py           # Epistemic data readers
│   └── run_offloop.py       # Off-loop runner
│
├── debate/
│   ├── client.py            # DeepSeek client (stdlib urllib)
│   ├── topics.py            # Whitelist-based topic selection
│   └── debate_loop.py       # Creative×Architect debate loop (≤3 rounds)
│
├── legs/
│   ├── leg.py               # Base worker (TaskPacket, Proposal, propose-only)
│   └── lead_leg.py          # Lead painter: intake → draft_quote → claim
│
├── dashboard/
│   └── server.py            # Flask-like control panel (40KB)
│
├── tests/
│   └── run_all.py           # 65 test files + 2 extras = 67 total
│
├── watchdog.py              # S-1: should_revive()
├── germline.py              # S-2/S-5: lag computation + backup
├── unified_bus.py           # S-3: convergence bridge (genome + chrono)
├── checkpoint.py            # S-4: checkpoint + replay
├── smoke_24h.py             # S-6: manual checklist
│
└── state/
    ├── ORGANISM-STATE.json
    ├── fitness-latest.json
    ├── replication-latest.json
    ├── telemetry-latest.json
    ├── school-awareness.json
    ├── baseline-phase-0-pre-*.json
    ├── channel-status.json
    ├── OWNER-PROFILE.json
    ├── reviews/
    │   └── phase-0-PHASE_RESULT-*.json
    └── telemetry/
        └── 2026-07-*.json
```

## 2.2 Key Data Flows

```
INGEST → SensoryBus → SchoolBridge → School Memory
                                  ↓
                            canonical_consolidation()
                                  ↓
                         ┌────────┴────────┐
                    Doctor (RFCs)    Neural (memory)
                         ↓                  ↓
                    EffectorGate      Fitness/Replication
                         ↓                  ↓
                    Telegram/HITL    Epoch Governor
```

**Consolidation return semantics (CRITICAL — changed in Phase 1):**
- `None` = precondition failure / exception (error)
- `ConsolidatedInsight(empty insights=[])` = nothing to consolidate (normal)
- `ConsolidatedInsight(latent_vector=[...])` = Phase 2 enriched result

## 2.3 Environment Flags (wiring.py)

```python
OCTOPUS_WIRE_DOCTOR       # Enable doctor wiring in organism tick
OCTOPUS_WIRE_UNIFIED      # Enable unified bus wiring
OCTOPUS_WIRE_LEAD         # Enable lead leg wiring
OCTOPUS_WIRE_CONSOLIDATION # Enable consolidation beat
WIRE_SCHOOL               # Enable school wiring
WIRE_NEURAL               # Enable neural subsystem
WIRE_FITNESS              # Enable fitness computation
# Default: all OFF (bare profile) — no regression in tests
```

## 2.4 Profile System

```python
# paper-full: all flags ON, but $0 shadow
# bare: all flags OFF, minimal loop
# Current runtime: allostatic epoch mode, bare by default
```

---

# Part 3: CURRENT STATE — EXACT METRICS

## 3.1 Test Suite

| Metric | Value |
|---|---|
| **Total test files** | 67 (65 in run_all.py + 2 extras) |
| **Latest run** | 71/72 green |
| **1 failure** | `test_llm_routing_smoke.py` — Fugu 429 rate limit (pre-existing, external API) |
| **Test timeout** | 300s per file |

## 3.2 Organism State (as of Jul 10 08:38)

| Field | Value |
|---|---|
| **Epoch mode** | `allostatic` (pressure-following) |
| **Halted** | `null` |
| **Frozen** | `false` |
| **Month spend** | `$0.00` (all zero) |
| **Suspect zero** | `0` |
| **Conflicts** | `[]` (empty) |
| **Germline lag** | `9.82 hours` (warn) |
| **Started** | `2026-07-08T15:07:05` |

## 3.3 Fitness

| Field | Value |
|---|---|
| **Authoritative** | `false` (shadow mode until ~4 weeks data) |
| **Revenue** | `$0` claimed, `$0` confirmed |
| **Cells** | `{}` (empty) |
| **Weights** | value=0.3, urgency=0.25, efficiency=0.2, human=0.2, waste=0.05 |

## 3.4 Replication / Sigma

| Field | Value |
|---|---|
| **σ_effective** | `0.0` |
| **Zone** | `pre-replication` |
| **Max cells** | `6` |
| **Spawn proposed** | `0` |
| **Live gate** | `locked until 2026-07-21` |

## 3.5 School Awareness

| Cell | Awareness |
|---|---|
| C01 | 0.06 |
| C02 | 0.88 |
| C03 | 0.06 |
| E01 | 0.06 |
| E02 | 0.88 |
| E03 | 0.06 |
| **Mean** | **0.0417** |

## 3.6 Neural Consolidation

| Metric | Value |
|---|---|
| **Total cycles** | 474 |
| **Span** | Jul 7-10 (3 days) |
| **Sources** | `acquisition`, `doctor_archive` |
| **Latest insight** | "Average awareness: 0.12" (trending up) |

## 3.7 Epochs

| Metric | Value |
|---|---|
| **Total epochs** | 53 |
| **Span** | Jul 7 20:42 → Jul 10 08:13 |
| **Cadence** | ~hourly (variable) |

## 3.8 Phase Reviews

| Phase | Status | Result |
|---|---|---|
| **Phase 0** | Completed | 4 modules created, 66 tests (65 green), baseline captured, ledger break found |
| **Phase 1** | Completed | 5 root causes fixed (RFC sweep/expire, consolidation distinguish, gate sweep) |
| **Blueprint Phase 2** | Completed | SharedLatentSpace R^32, 5 encoders, cosine retrieval, consolidation integration |

---

# Part 4: WHAT WAS BUILT THIS SESSION (Jul 10)

## 4.1 Phase 1 — Root Cause Fixes

**Problem:** RFCs and gated effects getting stuck forever (5 structural root causes).

**Fixes:**

1. **RFC auto-expire** (`doctor.py`): Added `created_ts` field + `_sweep_stale_rfcs(max_age_hours=24)`. Expired RFCs get `status="expired"`. If channel becomes available, stale RFCs are resubmitted.

2. **Consolidation distinguish** (`wiring.py`): Changed `canonical_consolidation()` to return bare `ConsolidatedInsight(empty)` for no-sources case (vs `None` for errors). This fixes the ambiguity where "nothing to do" was indistinguishable from "crashed."

3. **Gate sweep** (`chrono.py`): Added `sweep_stale_effects(max_age_hours=72)` to EffectorGate. Pending effects older than 72h get `status="refused"`.

4. **Organism hook** (`organism.py`): Added sweep hook in tick loop after epoch block. Calls EffectorGate.sweep_stale_effects() fail-soft.

5. **Epoch sweep** (`governor_epoch.py`): Added epoch-based sweep hook that tries to open chrono.db and sweep stale effects.

## 4.2 Blueprint Phase 2 — Shared Latent Space

**Problem:** Each layer speaks its own language (text, float, dict, RFC). No shared representation for cross-layer retrieval.

**Solution:** R^32 embedding space with per-layer encoders.

**New files created:**

1. **`_ops/neural/latent_space.py`** (~200 lines):
   - `SharedLatentSpace` class: `embed()`, `get()`, `similar()` (vectorized cosine), `nearest()`, `integrate()` (mean-pool), `count()`, `keys_by_layer()`, `remove()`, `store()`/`_load()` (JSON persist)
   - Persist path: `state/latent-vectors.json`

2. **`_ops/neural/encoders.py`** (~150 lines):
   - `_hash_project(text, dim)` — SHA-256 chunks → R^dim, deterministic, normalized to unit vector
   - `encode_observation(obs_type, label)` — SensoryBus text → R^32
   - `encode_awareness(awareness_vector)` — School float array → R^32
   - `encode_rfc(rfc_id, bottleneck, severity)` — Doctor RFC → R^32
   - `encode_phi_t(phi_vec, sigma)` — Box fusion → R^32
   - `encode_calibration(verdicts)` — Calibration history → R^32
   - ALL encoders: stdlib + numpy only, no LLM, deterministic (same input → same output)

**Modified files:**
- `consolidation.py`: Added `latent_vector: list[float] | None` and `similar_keys: list[str] | None` to `ConsolidatedInsight`
- `school_bridge.py`: Added `full_awareness_vector()` method
- `wiring.py`: Added `latent_space` param to `canonical_consolidation()` + `_enrich_with_latent()` helper

**New tests (55 total):**
- `test_rfc_sweep.py` — 9 tests
- `test_consolidation_distinguish.py` — 5 tests
- `test_gate_sweep.py` — 6 tests
- `test_latent_space.py` — 14 tests
- `test_encoders.py` — 14 tests
- `test_consolidation_latent.py` — 7 tests

---

# Part 5: REMAINING WORK — THE ROADMAP

## 5.1 Implementation Phases Status

| Phase | Description | Status | Tests |
|---|---|---|---|
| **B5 (Phase 0)** | Stabilization + safety hardening | ✅ DONE | baseline, held_out, phase_gate, review_bus |
| **B6 (Phase 2)** | Scheduler wiring | ✅ DONE (existing) | test_phase2_scheduler |
| **Track A** | A1 money_gate + A2/A3 capability-gate | ✅ DONE (existing) | test_phase1_wiring |
| **Track B** | Attribution + reconcile | ✅ DONE (existing) | test_phase3_trackb |
| **Epistemics A/B** | Non-destructive epistemics layer | ✅ DONE (existing) | test_phase4_epistemics, test_phase5_epistemics_wiring |

## 5.2 Blueprint Phases Remaining

### Blueprint Phase 3 — Memory Stabilization (BCM Forgetting)

**Principle:** ✅ Mathematical — BCM (Bienenstock-Cooper-Munro) forgetting rule.
- Forgetting term: `−β·w` (weight decay)
- Moving threshold: `θ = E[y²]` (average square activation)
- Without controlled forgetting, memory saturates and becomes unstable (memory reward-hacking)

**What to build:**
- Add weight decay to consolidation cycle
- Moving threshold θ tracks recent activation statistics
- Memories below θ get decayed; memories above θ get reinforced
- Only gate-passed knowledge enters long-term

**Pre-registered metrics:**
- `memory_decay_rate` = β (controlled, not zero)
- `memory_saturation` < threshold (prevent overflow)
- Held-out suite 5/5 preserved

### Blueprint Phase 4 — Sparse Input Filter (L1 / Prediction Error)

**Principle:** ✅ Mathematical — Sparse coding (L1 regularization).
- Not everything enters long-term memory; only few-shot high-value (high prediction error)
- Geometry: diamond (L1, decisive) not sphere (L2, vague)
- `F = D_KL[q(z)‖p(z|x)] − log p(x)` — free energy minimization

**What to build:**
- Prediction error computation in SCHOOL layer
- L1 sparsity filter before consolidation
- Only observations with `prediction_error > threshold` pass through
- Reduces noise, focuses learning

**Pre-registered metrics:**
- `input_sparsity_ratio` (fraction filtered out)
- `prediction_error_distribution` (should be heavy-tailed)
- Held-out suite 5/5 preserved

### Blueprint Phase 5 — Exploration Engine (Chamber Temperature)

**Principle:** 🔴 Metaphorical — Chamber = noise temperature `√2T·ξ`.
- T high = exploration (creative proposals)
- T low = exploitation (refinement of known good)
- **ONLY sandbox. NEVER auto-merge.** 🔴/UNPROVEN
- Must be validated before any trust placed in it

**What to build:**
- Temperature parameter for Chamber/Dreamer
- Exploration vs exploitation scheduling
- Bounded creative proposals in sandbox only
- Strict gate: no path from Chamber to production without human verdict

**Pre-registered metrics:**
- `chamber_proposal_quality` (sandbox score)
- `chamber_temperature_range` [T_min, T_max]
- Held-out suite 5/5 preserved
- ZERO auto-merge from Chamber

### Blueprint Phase 6 — Fisher Metric in FITNESS

**Principle:** ✅ Mathematical — Natural gradient descent.
- `Δθ = −η·G⁻¹·∇E` where G is Fisher information matrix
- Current FITNESS is linear scoring; Fisher adds curvature awareness
- Prevents pathological directions in parameter space

**What to build:**
- Fisher information computation from fitness landscape
- Natural gradient update in fitness scoring
- Curvature-aware weight updates

**Pre-registered metrics:**
- `fisher_condition_number` (should be bounded)
- `fitness_improvement_rate` vs linear baseline
- Held-out suite 5/5 preserved

## 5.3 Known Issues & Deferred Items

| # | Issue | Severity | Status |
|---|---|---|---|
| 1 | **Ledger chain break at record 40** — truncated JSON in `genome-system/ledger/ledger.jsonl` | Medium | Deferred — pre-existing corruption from organism heartbeat |
| 2 | **Phase 0→1 never formally transitioned** via review_bus | Low | Phase 0 review exists but verdict=null |
| 3 | **Phase metrics not pre-registered** — "RFC pending rate", "effects_stuck" mentioned but not in phase-metrics.jsonl | Low | Not created |
| 4 | **OCTOPUS.env line 6 stale comment** in control-brain cleanup | Low | Cosmetic |
| 5 | **LAMBDA_PERSIST duplicated** in 4 doctor submodules | Low | Centralization deferred |
| 6 | **Governor alerts** — consolidation crashes (neural_stack is None) in `governor-alerts.md` | Medium | neural_stack=None when WIRE_CONSOLIDATION off — expected |
| 7 | **Telegram bot not connected** — biggest blocker per PHASE9 audit | High | Token exists in OCTOPUS.env but `call` not done before Python |
| 8 | **Germline lag 9.82h** (warn threshold >2h) | Medium | Backup not running; owner task |
| 9 | **All financial values = $0** | Expected | Shadow mode by design; live gate locked until Jul 21 |

## 5.4 Cleanup & Wiring Gaps

1. **Connect Lead Leg to ChronoBus** — `Leg.register_leg()` + intake from P3 channel at runtime
2. **Connect Doctor to Pacemaker** — `run_cycle` every N beats (currently manually triggered)
3. **Replace `VERIFY_RULES` heuristic** with `stable_read()` in dashboard_doctor.py
4. **Add Lead-نقاشی to budgets.yaml** as organ (currently missing → leg stays `incubating`)
5. **Scheduled Task for watchdog** — `organism-watchdog.ps1` every 5 min (owner-only task)

---

# Part 6: KEY FILE CONTENTS (Reference Data)

## 6.1 ORGANISM-STATE.json (current)

```json
{
  "ts": "2026-07-10T08:38:42",
  "started": "2026-07-08T15:07:05",
  "epoch_mode": "allostatic",
  "halted": null,
  "frozen": false,
  "stop_organism": false,
  "month_spend_micro": 0,
  "month_spend_usd": "0.00",
  "month_spend_aud": "0.00",
  "today_spend_micro": 0,
  "suspect_zero_total": 0,
  "conflicts": [],
  "germline_lag_h": 9.82,
  "germline_alert": "warn"
}
```

## 6.2 Phase 0 Review Result

```json
{
  "phase": "phase-0",
  "summary": "Stabilization and safety hardening completed",
  "modules_created": ["baseline.py", "held_out_evaluator.py", "phase_gate.py", "review_bus.py"],
  "tests_added": ["test_baseline.py", "test_held_out_evaluator.py", "test_phase_gate.py"],
  "suite_count": 66,
  "suite_green": 65,
  "pre_existing_failure": "test_llm_routing_smoke.py (Fugu 429)",
  "held_out_result": {"fixed_suite": "5/5", "ledger_chain": "broken at record 40"},
  "baseline_captured": true,
  "finding": "held_out evaluator discovered ledger chain break",
  "verdict": null
}
```

## 6.3 Blueprint Risk Table

| Item | Label | Note |
|---|---|---|
| BCM forgetting, Fisher, sparse/L1, held-out eval | ✅ | Solid math, design basis |
| Free energy, σ→1, shared latent space | 🟡 | Model-based; results only with code evidence |
| Chamber = "temperature/sleep/dream" | 🔴 | Inspiration only; strictly sandbox, never auto-merge |
| "Infinitely intelligent" as goal | ⛔ | Reward-hacking-prone; replacement: "provable growth" |

## 6.4 Implementation Phase Map (from ORGANISM-SPEC)

| Code | Name | What | Status |
|---|---|---|---|
| B5 | Phase 0 | Baseline + held-out + phase_gate + review_bus | ✅ |
| B6 | Phase 2 | Scheduler wiring | ✅ |
| Track A | A1+A2+A3 | money_gate, capability_gate, reconcile | ✅ |
| Track B | Attribution | attribution + reconcile pipeline | ✅ |
| Epistemics | A+B | Non-destructive epistemics layer | ✅ |

---

# Part 7: KNOWLEDGE BASE (Side Systems)

## 7.1 Genome System (`07 - Knowledge/genome-system/`)

Separate git repo. Own agents (doctor, guardian, creativity). Own ledger (ledger.jsonl — 43KB, chain break at record 40). 100+ auto-generated RFC files in `knowledge/internal/`.

Key files:
- `run.py` — main entry
- `research_loop.py` — research automation
- `ledger/ledger.py` — hash-chained append-only ledger
- `genome/gates.yaml` — mutation gates
- `agents/doctor.py` — genome doctor agent
- `tests/` — 6 test files

## 7.2 School Memory (`07 - Knowledge/school-memory/`)

- `curriculum.py` — TopicNode with coord (static R^6), AwarenessField
- Topics: art, crypto, AI, etc. — each with subtopics and progression levels
- Awareness tracked per cell (C01-C03, E01-E03)

## 7.3 Time Architecture (`07 - Knowledge/Time-Architecture/`)

- Theory: HRV bridge between physiological time and computational time
- `fusion_sim.py` — fusion simulation with tests

## 7.4 Doctor Research (`07 - Knowledge/_doctor-research/`)

10 research files (~390KB total):
- `fitness-function-design.md` (54KB)
- `invariant-mutable-boundary.md` (77KB)
- `tiered-memory-consolidation.md` (45KB)
- `injection-defense-loop.md` (37KB)
- `loop-rhythm-convergence.md` (39KB)
- `canary-adversarial-evaluator.md` (42KB)
- `industry-benchmark-selfimprove.md` (39KB)
- `active-mutation-ledger.md` (35KB)

---

# Part 8: EXECUTION INSTRUCTIONS FOR CLAUDE 5

## 8.1 Your Mission

1. **READ everything above carefully.** This is the complete state of a 5-day project.
2. **ASSESS** — What is the highest-priority next step? Consider:
   - Phase 3 (BCM) is the next Blueprint phase — ✅ solid math
   - But there are wiring gaps (Telegram not connected = RFCs stuck)
   - Ledger chain break blocks held-out evaluator
   - Germline lag is increasing
3. **PLAN** — Create a concrete plan with:
   - Exact files to create/modify
   - Exact tests to write
   - Pre-registered metrics
   - Rollback strategy
   - Decision gate criteria
4. **EXECUTE** — Phase by phase, with human verdict at each gate.
5. **REPORT** — Structured handoff after each phase.

## 8.2 Test Execution

```bash
# Run all tests
python -X utf8 "F:\backup\_ops\tests\run_all.py"

# Run single test file
python -X utf8 "F:\backup\_ops\tests\test_latent_space.py"
```

## 8.3 Code Patterns to Follow

```python
# Pattern 1: harness.run for tests
if __name__ == "__main__":
    failed = harness.run([...])
    sys.exit(1 if failed else 0)

# Pattern 2: §۴ — never silent except
except Exception as exc:
    opslib.alert([f"module: error: {type(exc).__name__}: {exc}"])
    # NOT: except: pass

# Pattern 3: fail-closed gating
if condition_violated:
    return None  # or raise, or FREEZE
    # NOT: continue anyway

# Pattern 4: consolidation return semantics
if error:
    return None  # precondition failure
if no_sources:
    return ConsolidatedInsight(cycle=0, insights=[], verified_sources=[], discarded_sources=[])
# normal path
return ConsolidatedInsight(cycle=n, insights=[...], verified_sources=[...], discarded_sources=[...], latent_vector=[...])
```

## 8.4 File Paths (Absolute)

```
F:\backup\_ops\                    # Main organism code
F:\backup\_ops\tests\run_all.py    # Test runner
F:\backup\_ops\state\              # State files
F:\backup\_ops\neural\             # Neural subsystem
F:\backup\_ops\doctor\            # Doctor/Evolution
F:\backup\_ops\budget\             # Budget/Governor
F:\backup\07 - Knowledge\          # Knowledge base
F:\backup\04 - Architect System\   # Architecture docs (9 audit phases)
F:\backup\00 - Inbox\              # Prompts and reports
```

## 8.5 Constraints Summary

| Constraint | Value |
|---|---|
| **Max test timeout** | 300s per file |
| **Max cells** | 6 |
| **Spawn depth** | 1 |
| **Live gate opens** | 2026-07-21 |
| **σ must be** | ≤ 1.0 |
| **Budget** | $0 (shadow) |
| **Auto-merge** | NEVER |
| **Human at gate** | ALWAYS for 🔴/high-risk |
| **Dependencies** | stdlib + numpy only (no new pip packages) |
| **Encoding** | UTF-8 (`python -X utf8`) |
| **Platform** | Windows (Git Bash) |

---

# Part 9: WHAT SUCCESS LOOKS LIKE

## 9.1 Near-Term (Next Session)

- [ ] Blueprint Phase 3 (BCM) implemented and tested
- [ ] Ledger chain break fixed (record 40 truncated JSON)
- [ ] Telegram bot properly connected (OCTOPUS.env `call` before Python)
- [ ] RFCs flowing through human approval channel
- [ ] 72+ tests, 0 regressions

## 9.2 Medium-Term (1-2 Weeks)

- [ ] Blueprint Phases 3-6 all implemented
- [ ] Doctor running autonomously in sandbox (L1)
- [ ] First RFC submitted via Telegram and getting human verdicts
- [ ] Memory stabilization preventing saturation
- [ ] Sparse input filter reducing noise
- [ ] Fitness scoring with Fisher metric

## 9.3 Long-Term (1-2 Months)

- [ ] L2 autonomy: auto-merge for low-risk changes with clean history
- [ ] Live gate opens (Jul 21+): real financial data flowing
- [ ] Fitness becomes authoritative (after 4 weeks experience data)
- [ ] First real revenue attributed and confirmed
- [ ] Organism self-improving at measurable rate

---

# Part 10: ARCHITECTURE DOCUMENTS REFERENCE

The following documents contain deeper architectural detail. Read them as needed:

1. **`04 - Architect System/OCTOPUS-AUDIT-PHASE*.md`** (9 files, ~250KB total) — Complete audit of all organs
2. **`04 - Architect System/OCTOPUS-RECON-MAP.md`** — Codebase mapping for Phase 1
3. **`04 - Architect System/OCTOPUS-GOAL-MAP.md`** — Ecosystem strategy
4. **`04 - Architect System/OCTOPUS-SKELETON.md`** — Backbone architecture + request protocol
5. **`04 - Architect System/OCTOPUS-WIRING-MAP.md`** — Nervous system wiring map
6. **`04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC.md`** — Box specification (22KB)
7. **`04 - Architect System/CHRONO-GROUNDING-PLAN.md`** — Design-to-reality roadmap
8. **`04 - Architect System/FRONTIER-BENCHMARK.md`** — AI architecture benchmarks
9. **`00 - Inbox/OCTOPUS-STAGE0-REPORT.md`** (50KB) — Foundational Stage 0 report
10. **`00 - Inbox/OCTOPUS-MASTER-PLAN v1.md`** — Master build plan
11. **`00 - Inbox/OCTOPUS-P1-HEART-REPORT.md`** — Heart/chrono substrate confirmation
12. **`Evolutionary-Doctor_Self-Learning-Autonomy-Blueprint.md`** — The Blueprint (this document's source)
13. **`Evolutionary-Doctor_Prompts-v2.md`** — All 3 chained prompts + Standing Rules
14. **`Octopus_Heart_Design_v1.md`** — Heart design with 7 invariants

---

> **END OF MEGA-PROMPT**
>
> Claude 5: You now have the complete picture. The organism is alive (71/72 tests green), dormant ($0 shadow), and waiting for you to plan and execute the next phase of its evolution. Start with Blueprint Phase 3 (BCM forgetting) or address the highest-priority blocking issue. Use all your capacity. The owner is watching.
>
> **برو.** (Go.)
