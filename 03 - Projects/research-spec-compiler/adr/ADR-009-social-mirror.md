# ADR-009 — Social Mirror: a self/other model that transfers only when the goal is defined by the other

- **Status:** Closed — machine verdict **INTEGRATE** (`social_specific_advantage` = 0.398 ≥ 0.25 band) · honest reading: effect is real but ~¼ of the DiD is a control-arm penalty, not pure transfer; the conservative pure-transfer component (`gain_social`) is ≈ +0.30
- **Date:** 2026-07-14
- **Spec:** `specs/social_mirror.yaml` (H-OWN-01, PASS 6/6) · `experiments/social_mirror.py` · reuses `experiments/gridworld_wm.{_step, train, evaluate}` verbatim (improve-not-rewrite)
- **Decision rule (GO/NO-GO):** `social_specific_advantage` < 0.10 → DISCARD (also the `failure_condition`) · [0.10, 0.25) → OPTIMIZE · ≥ 0.25 → INTEGRATE

## Context

H-OWN-01 asks whether a self/other model is *specifically* more useful when the
agent must **distinguish its own goal from another agent's**, rather than merely
read a self-referential cue. The trap this spec is built to avoid: a "social
feature helps" result that is really just "an extra feature helps." The design
neutralises that with a **difference-in-differences (DiD)** across two task
families — one where the other agent's heading defines the self-goal (social) and
one where the other is present but irrelevant (control) — using two keyings of
**matched cardinality** so there is no state-space confound.

Two conditions, each a **fixed** tabular-Q keying (no run-time selection):
- `self_only` keys on the self-marker `cue_bit` (slot 5) + 4 object-direction
  signs + wall-context.
- `social_mirror` keys on `other_heading_A` (slot 6) + the same 4 signs +
  wall-context. Same key length (6), so no extra-feature confound.

On heldout **confusion** tasks `cue_bit` is randomised, so `self_only` collapses
to chance in both families; `social_mirror` transfers in the social family (the
heading still identifies the complement-goal) and collapses in the control family
(heading irrelevant).

## Decision — what it tests, and the mechanism

Primary metric (falsifiable, can be ≤ 0):

```
gain_social               = acc(social_mirror | social heldout)  - acc(self_only | social heldout)
gain_control              = acc(social_mirror | control heldout) - acc(self_only | control heldout)
social_specific_advantage = gain_social - gain_control            # the DiD
```

The DiD nets out any generic effect of the heading feature: `self_only` behaves
identically across families, and the heading's cardinality is matched, so what
survives is "the gain from *needing* to distinguish self from other." The quantity
goes to 0 whenever the social representation fails to form or fails to transfer; a
trivial agent that ignores the other scores exactly 0 (the `null_control` pins
that zero-point). The gated content is the **magnitude** clearing a pilot-set
SESOI of 0.10, with INTEGRATE at ≥ 0.25.

Mechanism, stated honestly: this is **not** a learned signal-selector. Each
condition is a hardwired keying; "learning" is only the Q-table each fixed keying
fills during training. The self/other contrast is drawn **between** conditions and
families by the DiD, never inside a single agent.

## Confirmed caveats (adversarial review)

1. **OVERCLAIM on "learning to select" — fixed in this pass.** The original
   docstring/spec prose said the learner "must LEARN which signal to trust" and
   the topology named a "goal-signal *selection*." The code does no such thing:
   `SELF_ONLY_SLOTS = (5, 0, 1, 2, 3, 4)` and `SOCIAL_SLOTS = (6, 0, 1, 2, 3, 4)`
   are **fixed slot tuples** — there is no gating, no selection, no signal-choice
   head. Prose in `social_mirror.py` (docstring) and `social_mirror.yaml`
   (`protocol`, `architecture.topology`) has been corrected to "fixed
   matched-cardinality keyings." No gating field (metric, thresholds, bands,
   baseline/expected) was touched; `validate` still prints `[PASS]` 6/6.

2. **`expected = 0.40` was pilot-optimistic.** It was rounded down from the pilot
   family 979000 mean DiD **+0.428** [EST/FACT: pilot log 2026-07-14, 3 seeds].
   The confirmatory family (980000+) is disjoint. Its canonical 5-seed harness run
   gives DiD **0.398** [FACT], but a 3-seed smoke on that same confirmatory family
   gives DiD **0.343** [FACT: `python -m experiments.social_mirror --confirm`,
   2026-07-14]. The point estimate is seed-count/RNG-sensitive across ~0.34–0.43;
   all of these clear INTEGRATE (≥ 0.25), but the prereg `expected` sat at the
   optimistic top of that spread. (Left unchanged: `expected` is locked post-run.)

3. **The DiD is partly driven by `gain_control` ≤ 0, i.e. the irrelevant-other
   feature is dead weight.** `architecture.tradeoff` predicts exactly this: keying
   on the other agent when it is irrelevant yields an ambiguous value table, so
   `gain_control` goes negative. On the confirmatory run `gain_control` = **-0.099**
   (standalone) / **-0.100** (inside the DiD condition) [FACT]. Because
   DiD = `gain_social` − `gain_control`, that negative control term *adds* ≈ 0.10
   to the headline. The **conservative pure-transfer component is `gain_social`
   alone ≈ +0.30** (standalone 0.313; inside-DiD 0.298; 3-seed smoke 0.287) [FACT].
   Roughly a quarter of the 0.398 headline is the control-arm penalty, not social
   transfer. Even so, the conservative reading (`gain_social` ≈ +0.30) independently
   clears the 0.25 INTEGRATE line.

## Scope guard

- **C0 tabular grid-world agents.** Deterministic 7×7 world, two objects, tabular
  Q. No LLM, no neural net, no continual/online agent.
- **"self/other model" is operationalised as which goal-signal the fixed Q-key
  conditions on** — nothing more. "Observing the other" is abstracted to a single
  heading feature.
- **Access/functional only, scope C0–C3.** No claim about phenomenal
  self-awareness, qualia, sentience, or "the agent has a self." The word "mirror"
  is a task label, not a consciousness claim.
- Single grid-world family; results scoped to it. Cross-environment generality is
  out of scope and untested here.

## Verdict

**INTEGRATE** — `python rsc.py run social_mirror`, 5 confirmatory seeds
(family 980000+), 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std | role |
|---|---|---|---|
| null_control | 0.008 | 0.043 | zero-point (≈ 0 ✓) |
| irrelevant_other_gain (`gain_control`) | -0.099 | 0.047 | control (≤ 0, as predicted) |
| social_gain (`gain_social`) | 0.313 | 0.049 | reported (pure transfer) |
| **social_specific_advantage** (DiD, primary) | **0.398** | 0.077 | **gated** |

Per-seed DiD: {0.325, 0.400, 0.490, 0.300, 0.475} [FACT]. Inside the primary
condition, `gain_social` = 0.298 ± 0.072 and `gain_control` = -0.100 ± 0.028 [FACT].

- `social_specific_advantage` = 0.398 ≥ 0.25 → **INTEGRATE**; `failure_condition`
  (< 0.10) not triggered. The effect is real and well above the SESOI: keying on
  the other agent transfers to confusion tasks **specifically when the self-goal is
  defined by the other**, and confers no benefit when the other is irrelevant.
- **Honest reading:** the headline 0.398 is inflated by a negative control arm
  (`gain_control` ≈ -0.10) — the "irrelevant other" feature is dead weight, which
  is itself a *correct* prediction of the architecture but is not evidence of
  transfer. The conservative pure-transfer number is `gain_social` ≈ +0.30, which
  still clears INTEGRATE on its own. So: a genuine self-vs-other transfer effect,
  moderate in size, not the ≈ +0.43 the pilot advertised.
- **Scope caveat (locked):** C0 tabular, single grid-world family, fixed keyings
  (not a learned selector). Verdict is scoped to "this environment family"; the
  claim is functional transfer, never phenomenal self-awareness.

## Consequence

INTEGRATE licenses treating the self/other disambiguation keying as a **sanctioned
transferable relational representation** within the C0 grid-world kernel line —
i.e. it may be reused as a building block in later specs, with the honest caveat
that its value is the pure-transfer `gain_social` ≈ +0.30, not the control-inflated
0.398. It does **not** license any phenomenal-self language, any cross-environment
generality claim, or any autonomous action; those remain out of scope and, where
relevant, owner-gated under the Central Law firewall (ADR-007).
