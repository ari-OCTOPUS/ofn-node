# ADR-012 — Memory as a resource-rational retention policy (utility-gated write/forget)

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/memory_policy.yaml` (H-OWN-06 / EXP-003b, PASS 6/6) · `experiments/memory_policy.py` · reuses `experiments/gridworld_wm.py` (improve-not-rewrite)
- **Decision rule (GO/NO-GO):** gated_advantage < 0.05 → DISCARD · [0.05,0.10) → OPTIMIZE · ≥0.10 → INTEGRATE

## Context

Operationalizes H-OWN-06 / EXP-003b: are writing / retrieving / forgetting
resource-rational **DECISIONS** rather than indiscriminate database ops? The
falsifiable form: under a **BOUNDED** store of capacity C, a policy that retains
the highest-utility entries should transfer better, at EQUAL capacity, than one
that writes everything and evicts blindly — and that edge must **VANISH** when
the store is unbounded (no decision to make). Confirmatory seed family 983000+,
disjoint from the 983500 pilot that set the bands.

## Decision — what it tests + mechanism

Per grid-world universe: train one base tabular-Q policy on a **fixed** 6-slot
minimal-sufficient abstraction, roll it out greedily, and consolidate winning
trajectories into a ~830-key episodic pool `{key → majority winning action}`,
each key carrying a retention weight = its visitation count on winning
trajectories. The pool is compressed to capacity **C=60** by three FIXED
retention rules, and each compressed memory is evaluated AS A POLICY on the same
60 heldout tasks with gridworld's frozen `evaluate()` (hit → stored action,
miss → CRC-seeded random fallback):

- **append_all** — capacity-blind: a uniformly random C-subset (random eviction).
- **recency** — capacity-blind but deterministic FIFO (keep the newest C).
- **gated** — resource-rational: keep the top-C keys by retention weight.

Primary metric = **gated_advantage** = success(gated) − success(append_all) at
equal bounded C — paired (same universe, base policy, pool; only the retention
rule differs), everything CRC-seeded per seed-index so the three conditions share
one build. No learning at eval, no LLM. Genuine falsifiability: success is a
TRAJECTORY-level property (a correct action is needed at every key on the path to
goal), so retaining the individually-most-needed keys does NOT guarantee whole
successful paths survive — the advantage can come out ≤ 0.

## Confirmed caveats (adversarial review, 2026-07-14)

Three findings were verified and are disclosed here rather than buried:

1. **The machine gate uses the WEAKEST baseline.** `gated_advantage` scores gated
   against `append_all` = random eviction — the easiest baseline to beat. The
   stronger deterministic control (FIFO / recency) is REPORTED outside the
   verdict as `gated_vs_recency` = **+0.247** [FACT: run log]. Gated beats even
   that FIFO baseline (recency here does no better than random eviction), which
   **DEFENDS** the result — the edge is specific to retention UTILITY, not "any
   non-random rule beats random." But the honest disclosure stands: the number
   that drives the INTEGRATE verdict is measured against the weak baseline.

2. **Pilot → confirmatory drift.** The bands were frozen on pilot family 983500,
   which expected **+0.14** (gated−append_all +0.143 ± 0.011 [FACT: pilot log]).
   The confirmatory family 983000+ came in at **+0.204** [FACT: run log] — about
   **+45%** over the pilot expectation (+0.06 absolute [EST: derived from the two
   FACT means]). The verdict is robust to the drift (both ≥0.10 → INTEGRATE), but
   the effect is larger on the confirmatory family than preregistered, so the
   point estimate is family-dependent, not a settled magnitude.

3. **Mild objective coupling.** The retention weight is derived from WINNING
   training trajectories and the eval metric is WINNING success — the utility
   signal is coupled to the objective it is later scored on, so part of gated's
   edge may reflect that coupling rather than pure resource-rationality. What it
   is **NOT**: a spurious extra-capacity effect. The `null_unbounded` control =
   **0.000** [FACT: run log] — at capacity ≥ pool size all three rules keep the
   entire pool, so the delta is exactly 0. The advantage is therefore genuinely
   caused by capacity **PRESSURE** (not by gated hoarding more useful entries in
   absolute terms), even though the utility estimate itself is train-coupled and
   not eval-independent.

## Scope guard (locked)

C0/C1 — episodic-store retention as a policy over a FIXED abstract
representation. "Utility" is functional need-probability (winning-visitation
frequency) only. No claim about phenomenal memory, qualia, or per-timestep write
dynamics inside an LLM. The C0⇏C4 (phenomenal/qualia) line is not crossed; scope
stays C0–C3.

## Verdict

**INTEGRATE** — `python rsc.py run memory_policy`, confirmatory family 983000+,
5 seeds, C=60, 2026-07-14. All numbers [FACT: run log]:

| condition | value | role |
|---|---|---|
| **gated_advantage** (primary) | **+0.204** | gated − append_all @ equal bounded C |
| gated_vs_recency | +0.247 | reported control (gated − FIFO), outside the verdict |
| null_unbounded | 0.000 | control: unbounded capacity pins the zero-point |

- gated_advantage +0.204 ≥ 0.10 → **INTEGRATE**; failure (<0.05) not triggered.
  The null exactly 0 pins the zero-point.
- **Honest reading:** at a bounded store, retaining the highest-utility episodic
  entries transfers materially better than writing-everything-and-forgetting-
  blindly, and beats even a deterministic FIFO — memory behaves as a
  resource-rational retention policy **in this instantiation**. Three caveats
  temper the strength: the gated verdict is measured against the weak (random)
  baseline; +0.204 sits ~45% above the pilot's +0.14; and the utility signal is
  train-coupled to the eval objective (though the unbounded null = 0 rules out a
  spurious capacity artifact). This is INTEGRATE-strength for THIS substrate
  (flat tabular grid-world, fixed good abstraction). Follow-ups before treating
  "memory is a decision policy" as settled beyond this instantiation: gate the
  primary metric on the FIFO baseline (not random), preregister the confirmatory
  magnitude to close the drift, use an eval-decoupled utility estimator, and test
  a compositional task space this substrate lacks.
