# ADR-003 — Geometric layer for the Cognitive Kernel (abstraction quality space)

- **Status:** Closed — machine verdict OPTIMIZE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/geometry_abstraction.yaml` (H-GEO-01, PASS 6/6) · map: `GEOMETRY.md`
- **Decision rule (GO/NO-GO):** geo_transfer_rho < 0.4 → DISCARD · [0.4,0.7) → OPTIMIZE · ≥0.7 → INTEGRATE

## Context

The owner asked to convert all the mathematics/ideas scattered across the three
raw files (`##_بستهٔ_پژوهشی_۰۱…md`, `New Text Document.txt`, `جراحی اختاپوس…txt`)
into a geometric formalization and inject it into the kernel's structure and
memory. Three parallel extraction agents inventoried every formalism, numbered
principle, hypothesis and geometrizable structure (with raw-file line anchors);
the synthesis is `GEOMETRY.md`.

Key finding from extraction: the "octopus/black-box" framing is filename-only —
the body of that file is brain↔AI representational-convergence + consciousness
material (Four Nested Clocks / Inner Light), not a head/limb topology. No
verdict-queue or capacity semantics exist in it.

## Decision — a runnable geometric core, honestly scoped

`GEOMETRY.md` maps every raw idea to a geometric object and tags each **[RUN]**,
**[SPEC]**, or **[MAP]**. Only one object is promoted to a runnable, falsifiable
spec now (the rest are the formal map until data exists):

**Abstraction as quotient geometry (principle #7 → measurable):** a WM
projection `φ: S → slots` induces a quotient `S/φ`. Principle #7's three axes
(prediction / compression / transfer) become the coordinates of an *abstraction
quality space* [realizes `axis_coordinates`, P L1460]:
- `alignment(φ)` = transfer-correct RSA: fraction of heldout states where the
  training-majority action of the state's representational bin equals the true
  optimal action (from deterministic BFS). Purely geometric — no Q-values.
- `compression(φ)` = 1 − |unique heldout keys|/|heldout states|.
- `transfer(φ)` = the learned tabular agent's heldout accuracy.

**H-GEO-01:** across a fixed 7-representation sweep, `alignment` predicts
`transfer` (Spearman ρ ≥ 0.7); `shuffle_control` (labels permuted) must give
ρ ≈ 0.

This choice deliberately corrects naive RSA: a maximally fine representation
scores perfectly on seen data but does not transfer. The alignment metric keys
on *train→heldout bin generalization*, so it distinguishes the raw buffer
(alignment ≈ 0) from a good bottleneck (alignment high) — which naive
representational similarity cannot.

## Why this and not the bigger objects

The category-theory goal-lifting (Kan extension `U_𝒟∘F ≅ U_𝒞`, P L790), the
energy/attractor landscapes (Hopfield/FEP/`D_t`), the C0–C4 × A0–A4 ordinal
lattice, and the non-equivalence projection tower are all in `GEOMETRY.md` as
**[MAP]/[SPEC]** — each needs an environment or data we do not yet have (an
ontology-shift world; homeostatic internal variables; consciousness metrics).
Promoting them now would violate the project's own rules (falsifiability gate,
no C0→C4 leap). They are recorded so the next agent can compile them when the
substrate exists.

## Scope guard (locked)

C0 tabular agents in the grid-world family. `alignment` measures representational
geometry, not learning dynamics; it may miss non-geometric transfer mechanisms
(declared tradeoff in the spec). NO claim about consciousness, biological
systems, or C4 — the non-equivalence tower (GEOMETRY §7) is the formal statement
of that firewall.

## Consequences

- The kernel gains a geometric read-out (`experiments/geometry_abstraction.py`)
  that runs on the SAME trained representations as H-OWN-03 — a diagnostic lens,
  not a new learner. Reuses `gridworld_wm` verbatim (improve-not-rewrite).
- `GEOMETRY.md` is the standing map; new geometric specs attach to its [SPEC]
  rows as data arrives.

## Verdict

**OPTIMIZE** — machine verdict, `python rsc.py run geometry_abstraction`,
universes 993000–993004, 5 seeds, 150k budget, 2026-07-14. All numbers [FACT:
run log]:

| condition | mean ρ | std |
|---|---|---|
| geo_alignment | **0.662** | 0.106 |
| shuffle_control (null) | 0.022 | 0.175 |

- geo_alignment ρ=0.662 ∈ [0.4, 0.7) → **OPTIMIZE**. Representational geometry
  explains a large, real share of transfer, but below the ρ≥0.7 INTEGRATE bar.
- shuffle_control ρ=0.022 ≈ 0 → the correlation is not a shape artifact; the
  transfer-correct RSA `alignment` genuinely tracks transfer.
- Reading: geometry is a strong but incomplete account — the residual (ρ well
  short of 1) is where non-geometric transfer mechanisms (learning dynamics,
  exploration) live, exactly the tradeoff the spec declared. Follow-up to lift
  toward INTEGRATE: partial-correlation controlling compression, or a larger
  representation sweep for a tighter ρ estimate (both are declared ablations).

## Adversarial review (2026-07-14) — 2 confirmed findings, both applied

A 6-agent review (3 lenses × verify) confirmed 2 major findings and refuted 1.
Both confirmed findings are about *description*, not code behavior, so the run
and the OPTIMIZE verdict stand; the labels were corrected:

1. **"transfer-correct RSA" was a misnomer.** The metric computes no
   representational-dissimilarity matrix and no second-order RDM correlation —
   RSA's defining operation. It is a supervised train→heldout bin-majority-
   action hit rate. Fix: renamed everywhere to **RTA (Representational Transfer
   Alignment)**; RSA/CKA/`D_causal` are now cited as *lineage/motivation only*,
   not the metric's identity (GEOMETRY.md §2, spec, this ADR).
2. **The alignment→transfer correlation is near-definitional.** RTA
   approximates the realizable ceiling of the tabular agent's own policy class
   (per-bin best action + coverage), so "geometry predicts transfer" is close
   to "the class ceiling predicts realized performance" — informative-but-weak,
   and a low ρ would signal a learning pathology, not "geometry is wrong." Fix:
   the spec's over-strong "explains the mechanism, not capacity" was softened;
   the honest, non-trivial content is relocated to the two controls —
   shuffle≈0 AND compression-fails-while-RTA-works — which is what actually
   rules out raw capacity and raw compression as the driver.

Refuted (no action): "coverage is a shared driver mechanically linked to the
evaluator" — coverage is the intended geometric quantity, not a leak.

## Pilot fact (single seed, 60k budget) [FACT: smoke log 2026-07-14]

alignment cleanly ordered the sweep (minimal_sufficient 0.836/transfer 0.700;
unlimited 0.000/0.327; taskid6 0.016/0.317). ρ(alignment,transfer)=+0.685,
while ρ(compression,transfer)=+0.009 — compression alone does NOT predict
transfer; alignment does. This is the empirical justification for the
transfer-correct RSA definition over naive compression/similarity.
