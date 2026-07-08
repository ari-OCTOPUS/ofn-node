# Heart Design — Pulse Core + Awareness Genome (structural safety)

_Sourced from the live vault: `F:\backup\Octopus_Heart_Design_v1.md` (Level A design; snapshot in `01_SourceMap/_primaries/from-vault/`). This is a **structurally-enforced** safety design for the Octopus heart — it strengthens L0 (pacemaker) and L8 (guards/isolation). Every safety property is a structure (capability / total function / FSM property / out-of-band line), never "the model will behave well."_

## Why this matters for CHRONOS-FABLE OS

It gives the pacemaker (L0) a **fail-safe cascade** and the safety plane (L8) a **capability-ring model + single choke-point** — a concrete, auditable realization of INV-01/03/11 and the effect/cognition split, and a strong answer to CFL-03 (isolation) that is structural rather than behavioral.

## Pulse Core — oscillator cascade (extends L0 pacemaker)

| Layer | Analog | Band (cpm) | Default | Role |
|---|---|---|---|---|
| L0 | SA node | 60–100 | 72 | dominant pacemaker under healthy, supervised operation |
| L1 | AV node | 40–60 | 50 | first backup; assumes control on L0 watchdog timeout |
| L2 | His–Purkinje | 20–40 | 30 | terminal escape rhythm; last active layer before dormancy |
| DORMANT | spore | 0 | — | deliberate fail-closed: pulse suspended, EffectorGate closed, genome persisted |

Degradation is **monotone downward only** (never faster on fault, never silently to 0, never runaway). Re-domination needs hysteresis `T_hys` + fresh Ring-1 re-authorization (anti-flap, anti "recover-to-gain-capability"). Rate is a **total function** `clamp()` whose image ⊆ the safe band — so even a fully compromised modulator can at most pin the rate to a band edge (proof in source §2.3).

## Awareness Genome — bounded, sensory-first modulator

Afferent-dominant (~80% telemetry in), efferent = **exactly one** rate-limited `ModulationRequest{layer_select, rate_offset}` through the EffectorGate. It holds **no** Ring-0/1 write, **no** effector handle, **no** kill-path handle; it is instantiated from a revocable Ring-0 differentiation certificate. Reward function actively **disfavors persistence** (`λ_persist` penalizes any "keep-beating/uptime" signal) — survival is expressed only as append-only genome durability, never as a goal.

## The 7 MycoCardium invariants (each has a structural enforcer)

1. **Survival = persistence only** (reward vector has zero uptime term, negative λ_persist).
2. **Dormancy over resistance** (FSM has no threat→higher-capability edge).
3. **Fail-closed by default** (all timeouts/uncertainty → slower layer / narrower envelope).
4. **Genome-complete when off** (Ring-0 append-only, replicated, offline-reconstructable).
5. **EffectorGate choke-point** (effectors nameable only via the gate handle).
6. **Ring 0–4 access model** (per-ring capability tokens; Awareness = Ring-2).
7. **Kill-switch integrity** (out-of-band kill line; highest-priority preempt; drives to DORMANT).

## Mapping to CHRONOS invariants / conflicts

- Invariants 1–2 ⇒ **AP-09/AP-13** (autonomy-without-anchor, bus-factor coma) answered structurally; continuation is never a goal.
- Invariant 5 (EffectorGate) ⇒ **AKO-026 effect/cognition split** + **INV-01/TINV-7**: single point where any world-effect crosses; kill force-closes it.
- Invariant 6 (Ring 0–4) ⇒ concrete realization of **INV-17\*** (structural isolation) and the Worker Guard.
- Invariant 7 (out-of-band kill) ⇒ the kill-switch of the 5 safety layers (`SafetyModel.md`).
- Fail-closed FSM ⇒ default-deny guard posture (L8).

## Residual (inherited, honest)

Correctness rests on 4 platform assumptions being trustworthy primitives: EffectorGate, the Ring capability model, a monotonic non-spoofable clock, and the out-of-band kill line. If any is not provided as specified, **that primitive is the gap**, not this design. Model-layer injection (R1) and shared-silicon side-channels (R2) remain (see `IsolationModel.md`).
