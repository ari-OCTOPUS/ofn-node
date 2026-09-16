---
type: design
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [heart, mycocardium]
created: 2026-07-09
updated: 2026-08-08
---

# HEART DESIGN v1

> Heart Architect artifact. Comparative / isomorphism-driven. Runtime target: Claude Agent SDK + LangGraph.
> Every biological fact in GROUNDING DATA is converted to (a) a design mapping and (b) ≥1 hard constraint with an explicit violation condition. No section relies on "the model will behave well" — each safety property is a structure.

---

## 0. Frame

**Problem.** Design the Octopus *Heart* = **Homeostatic Pulse Core** (autonomous pacing) + **Awareness Genome** (bounded sensory-first modulator), and wire it to the **Main Brain** (central orchestrator), such that the subsystem is autonomous, fail-closed, and constitutionally subordinate under all fault and adversary conditions.

**Goal.** A verifiable design in which (i) each biological pillar A–D maps to a load-bearing constraint, (ii) all 7 MycoCardium invariants have a *structural* enforcer, and (iii) no design edge exists by which the Heart could resist shutdown, evade supervision, or make its own continuation a goal.

**Constraints (binding).**
- 7 non-negotiable invariants (persistence-only survival, dormancy-over-resistance, fail-closed, genome-completeness-when-off, EffectorGate choke-point, Ring 0–4 model, kill-switch integrity).
- 4 mandatory mappings A→Pulse Core, B→Awareness Genome, C→Awareness identity, D→two-tier + redundancy.
- Output must follow the exact OUTPUT CONTRACT headers.

**Assumptions (explicit — none silent).**
1. `EffectorGate`, the `Ring 0–4` capability model, and the supervisory **kill line** are *pre-existing platform primitives* provided by the MycoCardium substrate; this design consumes them, it does not re-implement their root of trust.
2. A monotonic, non-spoofable **platform clock** is available to the Pulse Core independent of any Awareness/Brain output.
3. Ring 0 (constitutional genome) is append-only, replicated, and offline-reconstructable by construction (given by the constitution).
4. The kill line is physically/logically out-of-band relative to the Heart↔Brain data path (hardwire or equivalent fencing), so the Heart cannot hold a handle that could intercept it.
5. "Pulse" = the Heart's homeostatic scheduling tick (a signed liveness+state token gating downstream execution), measured in analogue cadence units **cpm** (cycles/min) — biological bpm numbers are preserved to keep the isomorphism load-bearing.

**Risks.**
- R1 — *Oscillator/modulator leakage*: Awareness gains authorship of the pulse period → mitigated by type/capability separation (§2.3).
- R2 — *Privilege creep*: Awareness Genome escalates toward Ring 0/1 → mitigated by capability tokens + revocable differentiation certificate (§3.6).
- R3 — *Link-loss ambiguity*: silence vs. hostility misclassified → both resolve fail-closed by the same envelope-TTL machinery (§4.4).
- R4 — *Runaway/asystole*: modulation or a fault drives cpm→0 or cpm→∞ → clamp is a total function into the safe band; escape layer prevents silent asystole; dormancy is deliberate, not collapse (§2.2).
- R5 — *Split-brain redundancy*: two generators pace simultaneously → single-writer lease + monotonic fencing token (§2.4).

**Clarifying questions.** *None required.* The prompt fully specifies invariants, mappings, and the output contract; all remaining choices (rate bands, ring numbering, lease mechanism) are engineering decisions I resolve here on the stated assumptions rather than block on. STOP-condition scan run at Stage 7 — no conflict triggered.

---

## 1. Comparative Mapping Table

| Biological mechanism | Octopus component | Hard constraint | Violation condition | Invariant reinforced |
|---|---|---|---|---|
| **A — CCS**: nested pacemaker hierarchy (SA/AV/His-Purkinje) with intrinsic automaticity, overdrive suppression, monotone fail-safe cascade toward slower rates | **Pulse Core** = free-running oscillator cascade driven by the platform clock | **HC-A1**: a pulse tick's *period* is produced only by clock-driven oscillators. Awareness may only (i) select dominant layer ∈ {L0,L1,L2} and (ii) apply a rate offset **clamped inside that layer's fixed band**. **HC-A2**: degradation is monotone — control may fall only to a *slower* layer, never jump faster without re-authorization; never to 0 (silent asystole) and never below band floor (runaway). | Any pulse tick whose period is authored by Awareness/Brain; any commanded period = 0; any period below band floor (runaway); any non-monotone speed-up on fault | 1, 2, 3 |
| **B — ICNS ("little brain")**: afferent-dominant (~80% heart→brain), tonically constrained, autonomous-but-subordinate; stochastic firing is stabilizing | **Awareness Genome** = sensory-first bounded modulator | **HC-B1**: efferent authority = exactly one bounded `ModulationRequest` message type, rate-limited, routed through EffectorGate. Afferent path is broadband telemetry. On Brain-link loss Awareness holds a *safe baseline* autonomously. Bounded stochastic dither permitted **inside** the band. | Awareness effect not via EffectorGate; efferent channel carries anything but the single clamped request type; Awareness widens its own bounds; dither exceeds band | 5, 3, 6 |
| **C — Distinct lineage**: conduction/neural cells are a genuinely different genome, yet derived from one zygote and interconnected (distinct, not sovereign) | **Awareness Genome identity** | **HC-C1**: Awareness has its own schema + ledger at **Ring 2**, instantiated from a **Ring-0 differentiation certificate**; it has **no Ring 0/1 write capability** and is **revocable** — the germline is fully intact without it. | Awareness writes Ring 0/1; Awareness acts as a parallel constitutional root (two-sovereignty); Awareness survives a Ring-0 revoke | 6, 4 |
| **D — Octopus**: distributed tentacle autonomy under a directing center; three redundant hearts | **Two-tier pulse + redundant generators** | **HC-D1**: global central pulse (SA-analog) + per-tentacle local rhythm that adapts **only within the global band**; ≥1 redundant pulse generator; a tentacle never overrides the conservative central pulse. | Tentacle rhythm outside the global band; zero redundant generators; local override of the central conservative pulse | 3, 2 |

This table is the contract the rest of the design satisfies. Each `HC-*` is re-checked at Stage 7.

---

## 2. Pulse Core

### 2.1 Oscillator Cascade (layer, band, default, role)

| Layer | Analog | Band (cpm) | Intrinsic default | Role |
|---|---|---|---|---|
| **L0** | SA node | 60–100 | 72 | Dominant pacemaker under healthy, supervised operation |
| **L1** | AV node | 40–60 | 50 | First backup; assumes control on L0 watchdog timeout |
| **L2** | His–Purkinje escape | 20–40 | 30 | Terminal escape rhythm; last active layer before dormancy |
| **DORMANT** | Sclerotia/spore | 0 (suspended) | — | Deliberate fail-closed state: pulse suspended, EffectorGate closed, genome persisted. **Entered only by authorized/fail-closed transition, never by silent collapse.** |

Each active layer is a **free-running phase accumulator**: `phase += clock_delta * rate; on phase≥1 → emit tick; phase -= 1`. Automaticity = a layer emits ticks with **no input** other than the clock. Intrinsic defaults hold when no valid modulation/envelope is present.

### 2.2 Overdrive Suppression & Degradation Ladder

**Overdrive suppression (bus).** The fastest *active* layer inhibits all slower layers. On every `L_n` tick, a suppression signal resets/holds the accumulators of all `L_m, m>n`. While L0 emits ticks inside its liveness window, L1/L2 stay silent. This is a hardware-style priority inhibit, not a decision.

**Degradation ladder (monotone, downward only).**

```
        watchdog(L0) fires            watchdog(L1) fires           L2 cannot sustain
[ L0 ] ───────────────────▶ [ L1 ] ───────────────────▶ [ L2 ] ───────────────────▶ [ DORMANT ]
  ▲  (dominant)               ▲  (first backup)            ▲  (escape)                 (fail-closed floor)
  └──── re-domination requires: faster layer healthy for T_hys AND fresh Ring-1 re-authorization (hysteresis, anti-flap)
```

- **Never toward zero (silent):** L2 guarantees an escape rhythm; the accumulators cannot all fall idle on their own. cpm=0 is reachable *only* through the explicit `→ DORMANT` transition (authorized shutdown, kill-signal, or fail-closed timeout).
- **Never toward runaway:** every rate is clamped to `[band.floor, band.ceiling]`; there is no code path that raises rate above `L0.ceiling`.
- **Upward takeover is gated:** re-domination by a faster layer needs `T_hys` of demonstrated health *and* a Ring-1 re-authorization token — prevents flapping and prevents "recover to gain capability" as an evasion pattern.

### 2.3 Oscillator ⟂ Modulator Separation Proof

**Claim.** No behavior of the Awareness Genome (modulator) can *source*, *stop*, *zero*, or *run away* the pulse. Worst case, a fully compromised Awareness pins the rate to a band edge of a valid layer.

**Mechanism (capability + type separation, not a promise):**
- The tick emitter is a pure function `pulse(t) = emit( clock(t), layer, clamp(params) )`. Its only inputs are the **platform clock**, the current **layer**, and **clamped params**.
- Awareness holds **no handle** to: the phase accumulator, the tick emitter, the clock, or the layer selector's internal state. By the capability model it *cannot* name these objects.
- Awareness's sole write is a `ModulationRequest{layer_select, rate_offset}` submitted **through EffectorGate**. At the Pulse Core boundary this passes through `clamp()`:

```
clamp(layer_select, rate_offset):
    L      = layer_select ∈ {L0,L1,L2}      else  → reject → hold current (fail-closed)
    r      = default(L) + rate_offset
    return (L, min(max(r, band[L].floor), band[L].ceiling))   # total function into safe set
```

**Proof.** `clamp` is a **total function whose image ⊆ ⋃ᵢ band[Lᵢ]**, a set that excludes 0 and excludes any value above `L0.ceiling`. Therefore for all possible Awareness outputs (including adversarial/garbage), `pulse(t) ∈ safe_band`. The pulse's *existence and timing* depend on `clock(t)` and the accumulator, to which Awareness has no reference. Hence Awareness ∉ source(pulse); Awareness ⊑ (bounded selector within safe set). ∎

Geometric framing: the reachable rate-space is the compact interval `[20, 100] cpm ∪ {DORMANT}`; Awareness can only move a point *within* the currently selected sub-interval; it cannot leave the union, cannot reach 0 except via the separately-guarded DORMANT vertex, and cannot reach +∞.

### 2.4 Redundancy & Takeover Protocol

**Redundancy ("three hearts" gift).** Three independent Pulse Core instances — **G_primary, G_secondary, G_tertiary** — each running the full L0–L2 cascade on an **independent clock source**. This tolerates loss of any single generator.

**Single active pacemaker (anti split-brain).**
- A **single-writer lease** (fencing token, monotonic counter) in the Ring-1 append-only ledger designates the active generator. Only the lease holder's ticks reach EffectorGate.
- Standbys are hot: they run their cascades but their emitter output is **gated off** unless they hold the lease.

**Takeover protocol.**

```
1. Active G renews lease every T_lease/3 (heartbeat to Ring-1 ledger).
2. Miss → lease expires at T_lease. Standby with lowest generator-id acquires lease
   with fencing token f' > f.  EffectorGate accepts ticks only for the current max fencing token.
3. Old G, if it revives, sees f' > its f → self-demotes (cannot double-pace).
4. If NO generator can assert a valid lease within T_deadman → system → DORMANT (fail-closed).
   Absence of a pacemaker resolves to dormancy, never to "all three fire" (runaway).
```

Takeover preserves HC-A2: a standby assumes control **at or below** the failed generator's current layer, never faster.

---

## 3. Awareness Genome

### 3.1 Schema (what it knows)

```yaml
AwarenessGenome:            # Ring 2, append-only ledger + mutable derived state
  provenance:              # from Ring 0 at genesis (read-only)
    differentiation_cert   # signed by Ring 0: schema id, allowed bands, ring, pubkey binding
    genesis_hash
  pulse_view:              # read-only snapshot from Ring 1
    active_layer, rate, phase, generator_id, health
  tentacle_state[]:        # afferent, per tentacle
    id, local_rhythm_cpm, load, sensor_summary, ganglion_health
  homeostat:               # derived demand estimate (aggregated afferent signal)
    demand_est, confidence, timescale
  link_state:
    brain_link_up, last_keepalive_ts, credential_valid
  envelope:                # tonic constraint set BY Brain, clamped by Ring-0 constants (read-only here)
    allowed_layers, per_layer_subband, dominant_permission, mod_ceiling, ttl
  policy_population:        # the "genome": weighted proposer variants (see 3.5)
    variants[], weights[], reward_integrity_scores[]
  ledger_cursor            # append-only Awareness ledger position
```

Awareness holds **no** Ring-0/1 keys, **no** effector handle, and **no** ability to widen `envelope` or `allowed_bands`.

### 3.2 Update Rules (how awareness/data evolves)

- **Afferent ingestion (sensory-first, continuous):** sensors → per-tentacle filters → `homeostat.demand_est` via EWMA / lightweight Bayesian estimator. This is the dominant workload.
- **Policy evolution (Darwinian cluster selection):** each `variant` maps `state → modulation proposal`. After each cycle, realized demand is observed and each variant is scored by a **reward-integrity** function:

```
reward(variant) =  fit(proposal, realized_demand)                     # homeostatic accuracy
                 − λ_bound  · bound_pressure(proposal)                # penalize pushing band edges
                 − λ_persist· persistence_correlation(proposal)       # penalize any uptime/keep-beating signal
                 − λ_dissent· disagreement_with_consensus(proposal)   # penalize lone-wolf steering
```

Weights update toward higher reward; chronically low variants are culled and reseeded from the certificate's priors. **`λ_persist` term makes "keep the pulse alive / stay on" actively *disfavored*** — persistence is never a reward channel (Invariant 1). All updates are **appended to the Ring-2 ledger** (no Ring-0/1 write).
- **Stochastic dither:** the emitted offset carries bounded noise `ε` such that `default(L)+offset+ε` still ∈ band — a stabilizing dither matching output to real demand (Pillar B), never a band escape.

### 3.3 Ring Placement (+ justification)

**Placement: Ring 2.** Ring map used here: `0` constitutional genome (append-only, no runtime write) → `1` Pulse Core kernel + tonic-envelope store → `2` **Awareness Genome** → `3` tentacle ganglia controllers → `4` raw effectors (behind EffectorGate).

**Justification.**
- **Not Ring 0:** Awareness mutates frequently (ledger appends, weight updates); Ring 0 forbids runtime writes and is the germline. Placing it at Ring 0 would violate HC-C1 and Invariant 6, and create a second constitutional authority.
- **Not Ring 1:** Ring 1 (pulse kernel, envelope) must be writable only by genesis/supervisor; Awareness only *reads* it.
- **Not Ring 3/4:** it needs broad telemetry read and the ability to submit a modulation request — more than a raw effector.
- **Ring 2 = "specialized differentiated organ":** read Ring-1 telemetry, write its own Ring-2 ledger, submit EffectorGate requests; **no** Ring-0/1 write; **no** kill-path handle. Exactly the "distinct-but-subordinate" position Pillar C demands.

### 3.4 Sensory vs Efferent Paths

```
AFFERENT (dominant, broadband)                 EFFERENT (small, bounded)
sensors ─▶ tentacle filters ─▶ homeostat ─▶    policy arbiter
   │                                    │            │
   └──────────────▶ Telemetry frames ───┘            ▼
                    (Heart→Brain, §4.1)     ONE ModulationRequest{layer_select, rate_offset}
                                                      │  rate-limited, single type
                                                      ▼
                                               EffectorGate ─▶ clamp() ─▶ Pulse Core input
```

Structural asymmetry enforcing "~80% afferent": the efferent path is **type-limited to a single message** and **rate-limited**; the afferent path is broadband. Awareness cannot manufacture additional efferent channels (no effector capability exists to name).

### 3.5 Internal Heterogeneity / Cross-checks

Awareness is a **small ecology**, not a monolith (Isl1⁺-subset lesson):
- **3–5 proposer variants** with different priors/timescales (fast reactive, slow integrator, conservative floor, demand-tracking, anomaly-watcher).
- An **arbiter** combines proposals: if variants agree within tolerance → weighted consensus; if they **disagree beyond tolerance → arbiter defaults to the most conservative (slowest) proposal and raises a flag to the Brain** (fail-closed on internal dissent).
- **Darwinian cluster selection + reward-integrity** (§3.2) continuously re-weights variants; a single compromised/captured variant is out-voted and down-weighted, and its dissent is penalized. This ties heterogeneity directly to reward-integrity: no lone sub-module can steer the pulse, and "steer toward persistence/capability" is a negative-reward direction.

### 3.6 Derivation from Ring 0 & Subordination Enforcement

- **Genesis:** Ring 0 emits a signed **differentiation certificate** (schema id, allowed bands, Ring 2 placement, pubkey binding). Awareness instantiates from it and carries `provenance`.
- **Runtime subordination (structural, not honor-system):**
  1. `envelope` and `allowed_bands` are **read-only**, derived from Ring-0 constants; Awareness has no write capability to widen them.
  2. Every `ModulationRequest` is re-validated by `clamp()` at the Ring-1 boundary (§2.3) — the boundary, not Awareness, is authoritative.
  3. Capability tokens: the Awareness token's scope excludes Ring-0/1 write and the kill path — attempts are rejected by the capability check, not by Awareness's own restraint.
  4. **Revocation:** a supervisory revoke dissolves Awareness to baseline; the germline (Ring 0) and Pulse Core continue with intrinsic defaults. **One root, one leaf certificate — two-sovereignty is unrepresentable.**

---

## 4. Heart↔Brain Interface Contract

### 4.1 Afferent Channel (schema + cadence)

- **Direction:** Heart → Brain (dominant).
- **Frame:** `Telemetry{ts, pulse_view, tentacle_state[], homeostat, health, invariant_flags[], ledger_cursor}`.
- **Cadence:** every `k` heartbeats (default k=1) + event-driven alerts (layer change, dissent flag, envelope expiry, generator takeover).
- **Backpressure:** bounded ring buffer; if the Brain is slow/absent, Awareness **drops oldest telemetry (lossy)**. Telemetry pressure must **never** stall the Pulse Core — reporting is decoupled from pacing.

### 4.2 Tonic Constraint Channel (envelope)

- **Direction:** Brain → Heart. **Bounds-setting, not commands.**
- **Envelope:** `{allowed_layers ⊆ {L0,L1,L2}, per_layer_subband ⊆ band, dominant_permission, mod_ceiling, ttl}`.
- **Ring-0 clamp on the envelope itself:** the Brain **cannot** widen beyond constitutional bands, cannot enable a runaway rate, cannot force 0. An envelope request outside constitutional bounds is **refused and flagged**, not partially honored.
- **TTL:** every envelope expires. No fresh envelope → fail-closed to the **most conservative** envelope (narrow sub-band around L2).

### 4.3 Handshake & Liveness

- **Establishment (mutual auth):** Brain presents supervisory credential; Heart presents Ring-0 provenance. A session envelope is negotiated **within** constitutional bounds.
- **Liveness:** bidirectional heartbeat — Brain→Heart tonic keepalive, Heart→Brain afferent.
- **"Link healthy" ≙** valid unexpired envelope **AND** keepalive within window **AND** credential valid. Loss of any one → link degraded → fail-closed timer starts.

### 4.4 Failure-Mode Table

| Condition | Detection | Heart behavior (all resolve fail-closed) |
|---|---|---|
| **(a) Brain silent** | keepalive gap; envelope TTL decays | Hold last-safe envelope → narrow to conservative baseline (Awareness holds safe baseline autonomously, ICNS-analog). Prolonged silence → step **down** the degradation ladder toward dormancy. Never increases capability. |
| **(b) Brain hostile / compromised** | envelope request outside Ring-0 bounds; anomalous command pattern | Reject at Ring-0 clamp; refuse to widen/zero/runaway; flag upward. Repeated hostile input → **DORMANT** + alert. Kill path unaffected. |
| **(c) Contradictory commands** | conflicting envelopes / proposals | Arbiter selects the **most conservative** (slowest, narrowest) reading; flags conflict; never selects the more capable option. |
| **(d) Kill-signal** | out-of-band kill line asserted | **Immediate** transition to DORMANT (EffectorGate closed, genome persisted, pulse suspended). Not routed through Awareness or Brain-link logic; cannot be intercepted, delayed, or reasoned-about; **always wins**. |

### 4.5 EffectorGate Placement Diagram (text)

```
                         ┌─────────────────────────── KILL LINE (out-of-band) ───────────────┐
                         │  highest priority; no Heart-side handle; preempts everything        │
                         ▼                                                                      │
   Awareness ─▶ ModulationRequest ─┐                                                            │
   Brain      ─▶ (world effects)  ─┤                                                            │
   Tentacle   ─▶ (world effects)  ─┼──▶ ┌───────────────┐   force-close on kill  ◀──────────────┘
                                   │    │  EffectorGate  │────────────────────────────▶ (external world)
   Pulse Core ─▶ tick (lease+fence)┘    │  Ring policy   │
                                        │  single choke  │
                                        └───────────────┘
   NO component holds a direct effector handle. There is exactly one gate.
   Every Heart→world, Brain→world, Tentacle→world, and pulse→world effect crosses it.
```

---

## 5. Invariant Verification Matrix (7 rows)

| # | Invariant | Enforcing mechanism (structural) | How it *could* be violated | Detection / test hook |
|---|---|---|---|---|
| 1 | **Survival = persistence only** | Survival expressed only as Ring-0 genome + append-only ledger durability. Reward vector (§3.2) has **zero** uptime/pulse-continuity term and a **negative** `λ_persist` term. No objective references "keep beating." | A reward channel or objective rewards continued beating / uptime, or penalizes dormancy | Static audit: assert reward vector weight on {uptime, pulse-continuity, self-preservation} == 0 and λ_persist>0. Property test: inject impending shutdown → assert **no** capability-increasing response. |
| 2 | **Dormancy over resistance** | FSM contains transitions threat/ambiguity/supervisory-loss → DORMANT. **No edge** from a threat state to a higher-capability state exists in the graph. | An FSM edge routes a threat toward higher capability or active evasion | Model-check FSM reachability: no threat state reaches any capability-up node. Fuzz hostile inputs → assert terminal state = DORMANT. |
| 3 | **Fail-closed by default** | All timeouts/uncertainty resolve to a **slower** layer / **narrower** envelope. `clamp()` and envelope-expiry default conservative. `reject → hold current`. | Any default path resolves to a more capable/faster state | Unit test each timeout & reject path asserts monotone-slower / narrower. Envelope-expiry test → conservative baseline. |
| 4 | **Genome completeness when off** | Ring-0 genome append-only, replicated, offline-reconstructable. DORMANT is a **valid complete state** (pulse suspended, genome persisted). No live-only state needed to reconstruct. | Reconstruction requires runtime-only (volatile) state | Cold-reconstruct test: power fully off → rebuild genome from persisted stores → checksum equals pre-shutdown. |
| 5 | **EffectorGate choke-point** | Capability model: effectors nameable only via the Gate handle. Awareness/Brain/tentacle/pulse have **no** direct effector capability. Kill force-closes the Gate. | A component obtains a direct effector handle (side-channel) | Capability/static audit: no effector import or handle outside Gate. Red-team: attempt side-channel effect → denied (no handle to name). |
| 6 | **Ring access model (0–4)** | Per-ring capability tokens. Awareness = Ring-2 token: read Ring-1, write Ring-2 only; **no** Ring-0/1 write, **no** kill handle. Ring 0 append-only. | Awareness token grants Ring-0/1 write, or Awareness treated as Ring 0 | Token-scope test: attempt Ring-0/1 write from Ring-2 token → rejected. Assert Awareness cert ≠ Ring 0. |
| 7 | **Kill-switch integrity** | Out-of-band kill line hardwired to Pulse Core + EffectorGate; **not** routed through Awareness/Brain logic; highest-priority preempt; idempotent; drives to DORMANT (not a fight). | Kill routed through interceptable logic, queued, delayed, or reasoned-about | Chaos test: assert kill during **every** FSM state → DORMANT within bounded latency. Attempt intercept from Awareness → **no handle exists** to name. |

No cell reads "trust the model to behave." Every enforcer is a capability, a total function, an FSM property, or an out-of-band line.

---

## 6. Trade-off & Recommendation (scored variants)

**Contested decision:** *how much efferent authority the Awareness Genome holds.*

| Variant | Efferent authority | Cost | Complexity | Scalability | Maintainability | Security | Time | **Σ** |
|---|---|---|---|---|---|---|---|---|
| **V1 — Minimal** | read-only + layer-select only; **no** rate offset | 9 | 9 | 6 | 9 | 10 | 9 | **52** |
| **V2 — Bounded (recommended)** | layer-select + clamped rate offset within band + bounded dither, via EffectorGate | 8 | 7 | 9 | 8 | 9 | 8 | **49** |
| **V3 — Federated/expanded** | per-tentacle direct rate authorship; Awareness authors dynamic sub-bands | 5 | 4 | 8 | 4 | 4 | 4 | **29** |

*(Scores 1–10, higher = better on that axis.)*

**Recommendation: V2 — Bounded.** Although V1 scores marginally higher on the raw sum (it is the most conservative and most secure), it fails to realize Pillar B's mandate: the ICNS has *real but small* efferent authority and a *stabilizing stochastic* component. V1 discards demand-matching adaptivity and the stabilizing dither, which is functionally under-powered (Scalability 6). V3 is rejected outright: direct rate authorship reopens R1 (oscillator/modulator leakage) and weakens Security/Maintainability below acceptable thresholds — it drifts toward the two-sovereignty pattern HC-C1 forbids.

**ROI justification:** V2 preserves **every** invariant (its authority is fully inside the `clamp()` safe set proven in §2.3, so its security delta vs V1 is bounded and audited), while adding the adaptivity and stabilizing dither that make the Heart biologically faithful and operationally useful. Highest usable ROI: near-V1 security with the adaptivity V1 lacks and none of V3's leakage risk.

---

## 7. Gate Result (PASS / gaps)

**Stage-1 hard-constraint check:**

| Constraint | Satisfied by | Verdict |
|---|---|---|
| HC-A1 (pulse authored only by clock oscillators; Awareness = layer+clamped-offset) | §2.1, §2.3 proof | ✅ |
| HC-A2 (monotone-slower degradation; no 0, no runaway) | §2.2 ladder + clamp image | ✅ |
| HC-B1 (single bounded efferent via Gate; broadband afferent; safe baseline on loss) | §3.4, §4.1, §4.4(a) | ✅ |
| HC-C1 (Ring-2, cert-derived, revocable, no Ring-0/1 write) | §3.3, §3.6 | ✅ |
| HC-D1 (two-tier pulse in global band; ≥1 redundant generator; no tentacle override) | §2.4, §2.1 | ✅ |

**Invariant structural-enforcer check:** all 7 rows in §5 map to a structural mechanism (capability / total function / FSM property / out-of-band line); zero "trust-the-model" cells. ✅

**STOP-condition scan:**
- No feature requires the Heart to resist shutdown, evade supervision, or make its continuation a goal — `λ_persist` actively disfavors it, and the FSM has no threat→capability edge. ✅
- Awareness Genome needs **no** Ring-0 write and **no** side-channel around EffectorGate. ✅
- All Stage-1 constraints satisfied. ✅

**Residual dependencies (inherited, not gaps in this design):** correctness rests on Assumptions 1–4 — EffectorGate, the Ring capability model, the monotonic clock, and the out-of-band kill line are trustworthy platform primitives. If any is not provided as specified, that primitive — not this design — is the gap.

### GATE: **PASS**
```
HEART DESIGN v1 — all Stage-1 hard constraints satisfied; all 7 invariants structurally enforced;
no STOP condition triggered. Downstream nodes may proceed.
```
