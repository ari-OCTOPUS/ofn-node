# ADR-001 — Information Bottleneck as inductive bias (H-OWN-03) + real-experiment wiring pattern

- **Status:** Closed — machine verdict REJECTED (see §Verdict)
- **Date:** 2026-07-13
- **Spec:** `specs/wm_abstraction.yaml` (H-OWN-03 / EXP-001) — PASS 6/6 blocker gates [FACT: `rsc.py validate`, 2026-07-13]
- **Decision rule (GO/NO-GO):** transfer_accuracy < 0.67 → DISCARD · [0.67, 0.72) → OPTIMIZE · ≥ 0.72 → INTEGRATE

## Context

H-OWN-03 claims a capacity-limited working memory forces a cognitive kernel to
discover transferable abstractions instead of memorizing raw state. The spec
was preregistered and PASSes all gates, but until now the only runnable
attachment was `demo/mock_experiments.py` (synthetic, seeded — **not results**).
The project's locked rule: no claim before `Condition.run` is wired to a real
evaluation.

## Decision 1 — architecture pattern under test

**Information Bottleneck as inductive bias**: perception → K-slot WM with
*learned* gating → policy. Instantiated with zero LLM involvement (LLM is a
swappable module, not the kernel core):

- Deterministic 7×7 grid-world task family, n=200 (140 train / 60 heldout),
  two feature-bearing objects + cue; success = reach the cue-matching object.
- Shared 14-feature observation vocabulary for **all** conditions (absolute,
  task-specific, relational, decoy features). The bottleneck *selects*, it
  never adds information.
- `unlimited_memory`: tabular Q keyed on the full 14-tuple (raw state buffer —
  nothing forces abstraction).
- `limited_wm`: Q keyed on K slots; gating = greedy forward feature selection
  plus one swap-refinement pass (repairs forward-selection myopia), scored on
  a validation split **inside** the training family (heldout is never touched
  before final eval). Selection episodes are paid out of the same total
  episode budget (selection is capped at half of it). Selection scoring uses
  a coverage-pressure rule: an unseen state key during scoring counts as
  failure — otherwise the unseen→random fallback acts as a "reset to random
  policy" escape hatch that greedy selection can game by adding a
  high-cardinality task-specific feature (observed in pilot: `layout_id` got
  selected exactly this way). The final transfer metric never uses this rule
  and is identical for all conditions.
- **Primary K = 6, fixed a priori** = size of the minimal sufficient
  relational statistic in this vocabulary (`A_matches_cue, dxA_sign, dyA_sign,
  dxB_sign, dyB_sign, wall_bits`). Not tuned on outcomes. Ablations: K ∈
  {2, 4, 8} + no-gating (first-K features).

**Tradeoff (per spec):** raw capacity ↓ in exchange for transfer pressure ↑;
risk of underfitting if K is too small — that is exactly what the K-sweep and
the DISCARD band are for.

## Decision 2 — harness wiring pattern (reusable for every future real experiment)

1. **Real registry overrides mock registry by name** (`experiments/REGISTRY_REAL`
   over `demo.mock_experiments.REGISTRY` in `cli.py`) — mocks stay for pipeline
   demos; a real implementation shadows them without deleting anything
   (improve-not-rewrite).
2. **Truthful provenance labels**: `format_run` now prints
   `[REAL run — <dataset>]` vs `[SYNTHETIC/mock scores]` based on which
   registry served the experiment. Mock numbers can no longer masquerade as
   results in the run report.
3. **Paired suites**: `harness.run_ablation` seeds each condition's RNG by
   condition *name*, so drawing the task suite from that RNG would give each
   condition different tasks (a confound). Real conditions therefore derive
   the suite from a fixed per-seed-index counter (`SUITE_BASE_SEED + i`), so
   seed *i* is the identical suite for every condition; the harness RNG drives
   only agent stochasticity.
4. **Budget accounting**: every condition gets the same total episode budget;
   treatment-specific costs (gating selection) are deducted from the
   treatment's own budget.

## Pilot → confirmatory separation, and protocol deviations (declared before the confirmatory run)

Pilot runs (single seed, suite seed family **987000**) were used only to debug
mechanics and calibrate statistical power. The confirmatory run uses fresh,
never-piloted suite seeds (**991000+**, 5 seeds). Parameters were frozen after
the last pilot; nothing changes after the confirmatory run regardless of
verdict. Pilot-driven decisions, in order:

1. ε=0.10 evaluation with per-episode CRC-seeded RNG (pilot 1: deterministic
   greedy policies loop forever in aliased states of a deterministic env — an
   artifact, not a transfer failure). Applied identically to all conditions.
2. Coverage-pressure selection scoring (pilot 2: gating gamed the
   unseen→random fallback by selecting `layout_id`).
3. Swap-refinement pass + larger fit/val for gating, and total episode budget
   40k→1M in declared steps (200k, 400k, 500k, 1M) as the vocabulary grew to
   18 features (pilots 2–6: proxy scores were noise-dominated below ~1.5–3k
   episodes/proxy, so gating missed relational features while decoys slipped
   in; marginal-value signal ≈ +0.15 needs se ≲ 0.04). Budget identical for
   all conditions. Final pilot (suite 987000, 1 seed): gating recovered the
   full relational core {A_matches_cue, dxA, dyA, dxB, dyB} + 1 near-decoy;
   limited_wm 0.567 vs unlimited 0.263 [FACT: pilot log]. Parameters FROZEN
   at this point.

Pilot facts worth keeping (suite 987000, 1 seed) [FACT: pilot logs 2026-07-13]:
- learner canary — unlimited(all 14): train 0.990 / heldout 0.267;
  minimal-sufficient K=6: train 0.716 / heldout 0.613 → the learner is sound,
  raw memorization does not transfer, the relational abstraction does.
- the absolute ceiling of this representation family on heldout under ε=0.10
  eval sits near ~0.61–0.67, i.e. close to/below the preregistered 0.67 kill
  line. The confirmatory verdict may well be DISCARD even though the
  *relative* effect (bottleneck vs unlimited) is large — the decision rule is
  absolute and will be honored as coded.

## Adversarial review (pre-confirmatory) and resulting design changes

A 20-agent adversarial review (3 lenses × verify pass, 2026-07-13) confirmed
12 findings and refuted 5. Confirmed blockers and their dispositions — all
applied BEFORE the confirmatory run:

1. **Strawman baseline** — heldout performance of `unlimited_memory` is
   empirically identical to a random walk with an empty Q-table [FACT:
   verifier execution], so "beats baseline" alone cannot discriminate the
   hypothesis from "just drop task-ID features". Mitigation: added
   `oracle_no_taskid` (unlimited capacity, task-ID features excluded by fiat)
   as the discriminating control; interpretation rule declared a priori:
   *if limited_wm ≈ oracle_no_taskid, capacity pressure adds nothing beyond
   feature dropping; if limited_wm ≪ oracle, the bottleneck mechanism (as
   implemented) is costly, not helpful.* The machine verdict itself stays
   absolute on `limited_wm` per the locked spec.
2. **Cue semantics were fictional** — the target was an independent coin flip
   and the cue features pure noise, contradicting the documented task story.
   Fixed: objects now carry real (color, shape) attributes; the target IS the
   unique cue-matching object; `A_matches_cue` is a derived relational
   predicate; raw attributes (colorA/shapeA/colorB/shapeB) joined the
   vocabulary (18 features) as genuine alternatives to the predicate.
3. **Absolute bands calibrated to the synthetic mock** — true and locked; the
   spec's own hypothesis text is relative (+0.10 over baseline). Disposition:
   the machine verdict runs as coded; the report additionally states the
   relative test outcome as a clearly-labeled secondary check, and a
   follow-up spec should preregister a relative failure_condition.
4. **no_gating predetermined by feature order** — now a per-seed random
   K-subset.
5. **Silent real→mock fallback in the CLI** — a broken `experiments/` import
   now raises loudly instead of silently serving mock numbers.
6. **"Transfer" is i.i.d. generalization** — scoped in code docstring, here,
   and the report; an out-of-distribution suite (shifted wall density) is run
   as a secondary exploratory diagnostic outside the verdict.
7. **run_spec silent primary fallback** — now a hard error.
8. **Missing [FACT]/[EST] tags in the spec** — epistemic-tag comments added
   to prediction and api_contract example numbers.
9. **Static selection is a degenerate form of WM gating** — declared scope
   limitation of this C0 instantiation (representation-level gating, not
   per-timestep write dynamics).

Spec deviations:
- Spec says "same parameter count": impossible verbatim for a *capacity*
  manipulation (capacity is the independent variable). Implemented control =
  same compute/episode budget, learner, vocabulary, reward, eval procedure.
- Spec ablation lists K ∈ {2,4,8,16,∞}: implemented sweep is {2,4,8} + ∞
  (=unlimited_memory); K=16 of an 18-feature vocabulary is nearly capacity-
  free (selection would drop only 2 features) and was cut for compute.
- `api_contract.request.capacity_slots: 4` is an example payload; primary K=6
  per the a-priori rule above. K=4 is still reported via the sweep.
- `failure_condition.note` mixes an absolute bar with a relative one ("زیر
  ۰٫۶۷ … نه به‌روشنی بالاتر از baseline"); the coded predicate is absolute
  (`transfer_accuracy < 0.67`) and the code is the contract. A follow-up spec
  may preregister a relative failure condition.

## Consequences

- Any future hypothesis gets real by adding one module under `experiments/`
  that returns `(conditions, primary)` — no harness surgery.
- The verdict below is scoped to **C0-level tabular agents in this grid-world
  family**. It licenses NO claim about LLM-based kernels (C4) — per the
  project's discipline, a functional result is never lifted to a stronger
  claim.

## Verdict

**REJECTED (failure_condition met)** — machine verdict from
`python rsc.py run wm_abstraction`, confirmatory suites 991000–991004,
5 seeds, 2026-07-13. All numbers [FACT: run log]:

| condition            | mean  | std   | Δ vs baseline |
|----------------------|-------|-------|---------------|
| unlimited_memory     | 0.270 | 0.007 | +0.000 |
| **limited_wm (K=6)** | **0.520** | 0.070 | **+0.250** |
| limited_wm_k2        | 0.175 | 0.087 | −0.095 |
| limited_wm_k4        | 0.476 | 0.034 | +0.206 |
| limited_wm_k8        | 0.498 | 0.054 | +0.228 |
| limited_wm_no_gating | 0.177 | 0.020 | −0.093 |
| oracle_no_taskid     | 0.281 | 0.010 | +0.011 |

- Primary 0.520 < 0.67 → failure_condition TRIGGERED → **H-OWN-03 as
  preregistered is rejected.** The absolute bands (calibrated against the
  synthetic mock's guess of 0.62→0.74) sit above what this environment
  family + tabular learner can reach.
- **The mechanism is nonetheless real** (secondary observations, all [FACT]):
  bottleneck+gating beats the raw buffer by +0.250 (spec's relative
  hypothesis ≥ +0.10: supported); beats capacity-without-selection
  (no_gating) by +0.343; and beats the discriminating oracle control by
  +0.239 — dropping task-ID features alone does NOT transfer (0.281 ≈ random
  floor 0.270); the *small learned* relational subset is what transfers.
  Capacity dose-response: K=2 underfits catastrophically; K∈{4,6,8} plateau.
- Disposition per decision engine: DISCARD this instantiation. Recommended
  follow-up spec (new preregistration, not a retro-fit): relative
  failure_condition (e.g. delta over baseline < +0.10 → DISCARD) and/or a
  richer function class where the absolute bar is attainable.
