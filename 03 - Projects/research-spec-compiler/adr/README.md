# ADR index — Cognitive Kernel 0.1 architectural decisions

Each ADR records one architectural commitment and its **machine verdict** from a
real `rsc.py run` on preregistered `decision_rule` bands. Every experiment was
adversarially reviewed; confirmed findings were applied before closing.

| ADR | commitment | spec | verdict |
|-----|-----------|------|---------|
| [ADR-001](ADR-001-wm-bottleneck-real-harness.md) | Information-Bottleneck WM (absolute bar) + real-harness pattern | `wm_abstraction` | **REJECTED** (0.520 < 0.67) — mechanism real (+0.25) |
| [ADR-002](ADR-002-drake-census-pattern.md) | Monte-Carlo Drake census over seeded universes | `drake_kernels` | **OPTIMIZE** (f_transfer 0.600) |
| [ADR-003](ADR-003-geometric-layer.md) | Geometric layer — RTA (not RSA) abstraction geometry | `geometry_abstraction` | **OPTIMIZE** (ρ 0.662) |
| [ADR-004](ADR-004-relative-threshold-preregistration.md) | Relative-threshold preregistration for capacity manipulations | `wm_abstraction_v2` | **OPTIMIZE** (gain 0.169) |
| [ADR-005](ADR-005-homeostasis-allostasis.md) | Homeostatic MPC self-model vs reactive control | `homeostasis` | **OPTIMIZE** (advantage_ood 0.029) |
| [ADR-006](ADR-006-consolidation-library-learning.md) | Consolidation as library learning vs raw replay | `consolidation` | **INTEGRATE** (+0.045) |
| [ADR-007](ADR-007-central-law-governance.md) | Owner's Central Law governance (AGI/economy/ethics gates + verdict firewall) | — | accepted |
| [ADR-008](ADR-008-hybrid-cortex-organism-attach.md) | Hybrid cortex organ; kernel learns the live body & decides to attach | `hybrid_organism` | **OPTIMIZE** (bottleneck_advantage 0.036, after re-gating) |
| [ADR-009](ADR-009-social-mirror.md) | H-OWN-01 Social Mirror Self-Model (distinguish self/other) | `social_mirror` | **INTEGRATE** (DiD 0.398; expected pilot-optimistic) |
| [ADR-010](ADR-010-comparison-metacog.md) | H-OWN-02 Comparison-driven metacognition (social self-calibration) | `comparison_metacog` | **INTEGRATE** (brier_reduction +0.019) — attribution caveat: skill-gap term only ~+0.005 |
| [ADR-011](ADR-011-prospective-memory.md) | H-OWN-05 Prospective memory (retained intentions under interruption) | `prospective_memory` | **INTEGRATE** (0.475; buffer-vs-none, capacity never binds) |
| [ADR-012](ADR-012-memory-policy.md) | H-OWN-06 Memory as a resource-rational retention policy (utility-gated) | `memory_policy` | **INTEGRATE** (gated_advantage 0.204; gated>FIFO too, but gate uses weak baseline) |
| [ADR-013](ADR-013-causal-selfmodel.md) | H-OWN-07 Self-model requires causal access (predict own failure) | `causal_selfmodel` | **REJECTED** (causal_advantage −0.098; status label beats internal signals here) |
| [ADR-014](ADR-014-control-signals.md) | H-OWN-08 Regret as a shift-invariant control signal (defined math, NOT emotion) | `control_signals` | **INTEGRATE** (regret_advantage_ood 0.355; synthetic-env caveat) |
| [ADR-015](ADR-015-adaptive-forgetting.md) | EXP-004 Adaptive forgetting under drift (utility-decayed eviction) | `adaptive_forgetting` | **OPTIMIZE** (0.056 vs never-forget; sub-SESOI vs FIFO) |
| [ADR-016](ADR-016-retrieve-vs-compute.md) | EXP-005 Learned retrieve-vs-compute scheduler (costs in objective) | `retrieve_compute` | **INTEGRATE** (0.031 over the BETTER pure strategy) |
| [ADR-017](ADR-017-ontology-shift.md) | H-GEO-02 Goal lifting under ontology shift (Kan-extension realized) | `ontology_shift` | **INTEGRATE** (lifting_advantage 0.190) |
| [ADR-018](ADR-018-multimetric-memory.md) | Principle-8 multimetric memory (semantic+time+provenance+outcome) | `multimetric_memory` | **INTEGRATE** (0.157; recency-only misleads) |
| [ADR-019](ADR-019-attractor-memory.md) | Hopfield attractor completion vs exact lookup under noise | `attractor_memory` | **INTEGRATE** (0.612; synthetic patterns only) |
| [ADR-020](ADR-020-comparison-metacog-v2.md) | H-OWN-02 v2 — mechanism-isolated skill-gap gate (ADR-010 follow-up) | `comparison_metacog_v2` | **OPTIMIZE** (delta_gain 0.005 — mechanism real but tiny) |
| [ADR-021](ADR-021-adaptive-forgetting-v2.md) | EXP-004 v2 — adaptive vs FIFO, the honest hard gate (ADR-015 follow-up) | `adaptive_forgetting_v2` | **REJECTED** (0.023 < SESOI 0.03 — any forgetting captures most value) |
| [ADR-022](ADR-022-d10-abc-architecture-comparison.md) | D10-ABC — single-model vs orchestrator vs multi-agent (architecture comparison, DISTINCT from Mining D-10) | `d10_abc_architecture_comparison` | **PENDING** — preregistration frozen; fake harness validates plumbing; confirmatory run needs owner verdict |

## Cross-cutting discipline (holds across every ADR)

- **Truthful provenance** — real runs print `[REAL run — <dataset>]`; synthetic
  mocks print `[SYNTHETIC/mock scores]` and are never reported as results. A
  broken real registry hard-errors instead of silently serving mocks.
- **Pilot → freeze → confirmatory** — parameters are frozen on a pilot seed
  family, then the confirmatory run uses a disjoint fresh family (991000 /
  993000 / 994000 / 996000 / 997000 / 998000, etc.).
- **Adversarial review each round** — 3-lens (correctness / methodology /
  faithfulness) × verify. Notable catches applied before finalizing: the
  ε-restart replay confound (ADR-006), the sim/executor MPC mismatch (ADR-005),
  the "RSA" mislabel (ADR-003), and the trivially-clearable gate + strawman
  baseline (ADR-008, re-gated from an inflated INTEGRATE to an honest OPTIMIZE).
- **Scope firewall** — C0–C3 only; the C0⇏C4 (phenomenal/qualia) line is never
  crossed. The economy gate reorders the queue, never a verdict (ADR-007).

## Related maps

- `../GEOMETRY.md` — the geometric formalization of the raw research corpus.
- `../attach-proposal/` — the owner-gated shadow-attach blackbox contract.
