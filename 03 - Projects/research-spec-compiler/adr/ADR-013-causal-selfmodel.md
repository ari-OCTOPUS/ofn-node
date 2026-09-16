# ADR-013 — Self-model requires causal access? (H-OWN-07) — an honest negative

- **Status:** Closed — machine verdict **REJECTED** (failure_condition triggered) (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/causal_selfmodel.yaml` (H-OWN-07 / EXP-007, PASS 6/6) · `experiments/causal_selfmodel.py`
- **Decision rule (GO/NO-GO):** causal_advantage < 0.02 → DISCARD/REJECT · [0.02,0.05) → OPTIMIZE · ≥0.05 → INTEGRATE · failure_condition: `causal_advantage < 0.02` → reject

## Context

Operationalizes H-OWN-07 / EXP-007 (raw corpus, self-model ladder): the claim
that a **genuine** self-model must PREDICT its own error/failure states from
**causal access to its own internal computation**, not merely DESCRIBE the
situation from the outside. If description alone suffices, the introspective
advantage should collapse to ≤ 0. Deterministic 7×7 grid-world + tabular Q, zero
LLM, reusing `gridworld_wm` (improve-not-rewrite). Pilot family 984500 set the
decision bands, then FROZEN; the confirmatory family 984000 is disjoint.

## Decision — what it tests + mechanism

One tabular Q agent per seed is trained on 140 train tasks under the abstract
minimal-sufficient K=6 keying (a **fixed** 6-slot state key, not learned/selected
here). For each heldout EPISODE (task × start) two self-models predict, from
START-STATE features only (no outcome peeking), whether the agent will FAIL that
episode:

- **status_auc** (descriptive): failure from EXTERNAL task geometry only — BFS
  distance to target, BFS distance to the distractor, their difference, local
  wall count, Manhattan geometry (**5 features**). A competitive difficulty model,
  not a strawman.
- **causal_auc** (self-model): failure from the agent's OWN internal computation —
  max-Q and Q-gap at the start key, start/neighbour representational-bin coverage,
  local value landscape, and a short IMAGINED greedy self-rollout measuring
  novelty / low-confidence ahead (**7 features**).

**Primary metric = causal_advantage = AUC(causal) − AUC(status)**, paired per seed
(identical agent, episodes, classifier, split). Both self-models are FIT on a
150-episode split and SCORED on a **disjoint** 150-episode TEST split, over 5
seeds. Null control **shuffled_causal_auc**: identical causal features, FIT-split
labels permuted → tests whether the causal signal is real or an artifact.

## Confirmed caveats (adversarial review)

1. **`prediction.expected = +0.05` was the HYPOTHESIS, and the pilot already
   anticipated a negative.** [EST] +0.05 is H-OWN-07's preregistered minimal
   claim (the falsifiable target). The pilot note records the honest anticipation
   that it would land in DISCARD ([FACT: pilot 984500, 3 seeds] causal_advantage
   ~ −0.08). This is **hypothesis vs honest anticipation**, not a contradiction —
   the spec preregisters the claim it means to test *and* discloses that the
   pilot expected it to fail. The confirmatory run was left to decide, and did.
2. **Feature-count asymmetry: causal uses 7 features, status uses 5.** A
   pure-capacity story ("causal only lost because it is wider") is ruled out
   three ways: (a) both models are fit on one split and scored on a **disjoint**
   TEST split, where noise/extra features regress to ~0.5; (b) the
   **shuffled-label** control on the *same 7 causal features* collapses toward
   chance ([FACT: run log] shuffled 0.554 ± 0.062), so the width does not buy
   test AUC; (c) the 7-feature causal model still scores well above chance
   (0.650) — it carries real signal, it simply does not beat the 5-feature status
   label here. Extra width is therefore neutralized, not the cause of the loss.

**Fixes applied to the artifacts (honest-prose only, no gating field changed):**
disclosed the 7-vs-5 feature counts in the spec protocol and the experiment
docstring; corrected a misleading `n: 300` (fit+test conflated) to `n: 150` — the
scored heldout TEST episodes per seed — while noting the primary metric's
inferential n is **5 seeds**, not 150 episodes; and clarified that the K=6
representation is a fixed keying, not a learned/selected one. `metric.name`,
`failure_condition` (`< 0.02`), the decision bands, and `prediction.baseline/expected`
were left locked (post-run); re-validation prints [PASS] 6/6.

## Scope guard

C0–C3 functional self-prediction in a tabular grid-world only. The metric is
prediction skill about the agent's OWN task failures — functional access of a
controller to its own computational state. **Forbidden interpretation:**
introspection-as-experience, self-awareness, sentience, qualia. No phenomenal
(C4) claim is made or implied; the C0⇏C4 line is not crossed.

## Verdict

**REJECTED** — `python rsc.py run causal_selfmodel`, confirmatory family 984000,
5 seeds, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std | role |
|---|---|---|---|
| status_auc | 0.748 | 0.046 | descriptive baseline |
| causal_auc | 0.650 | 0.083 | self-model |
| shuffled_causal_auc | 0.554 | 0.062 | null control (≈ chance) |
| **causal_advantage** (primary) | **−0.098** | 0.064 | PRIMARY: causal − status |

- causal_advantage −0.098 < 0.02 → **failure_condition TRIGGERED → REJECTED**.
  It is negative on **all 5 seeds** ([FACT] range [−0.201, −0.013]), so the
  rejection is consistent, not a one-seed accident.
- **This is an honest negative, and it is publishable as one.** The internal
  causal signals are NOT noise: causal AUC 0.650 sits clearly above the shuffled
  control (0.554 ≈ chance) [FACT], confirming the start-state value/coverage/
  self-rollout features carry real information about the agent's own failures.
  The causal self-model simply **loses to the simpler status/geometry label**
  (0.748 vs 0.650) in THIS grid-world with THESE features.
- **Honest reading of H-OWN-07:** in this instantiation, a coarse *descriptive*
  account of task difficulty predicts the agent's own failures **better** than
  its internal *causal* signals. So "a genuine self-model requires causal access
  to beat description" is **rejected for this instantiation** — not disproven in
  general. A likely reason: on a small tabular grid-world the outcome is
  dominated by task geometry (distance to target vs distractor), which the status
  model reads directly, while the agent's value table is a noisier proxy for the
  same thing. The mechanism (causal read-out + imagined self-rollout) is
  implemented and carries signal; the environment just does not reward it over
  description. Whether causal access wins needs a task space where internal
  competence and external geometry **dissociate** (partial observability, learned
  mis-calibration, compositional transfer) — this substrate does not provide that.
- **Scope caveat (locked):** single grid-world substrate, one fixed K=6 keying,
  5 correlated confirmatory seeds; the primary paired statistic's inferential n is
  5 seeds (each AUC scored on 150 heldout TEST episodes). Verdict scoped to "this
  grid-world with these features," consistent with the pilot's honest anticipation.
