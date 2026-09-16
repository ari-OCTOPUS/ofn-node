# ADR-017 — Goal lifting under ontology shift: U_D = U_C ∘ F̂ (H-GEO-02)

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/ontology_shift.yaml` (H-GEO-02, PASS 6/6) · `experiments/ontology_shift.py`
- **Decision rule (GO/NO-GO):** lifting_advantage < 0.05 → DISCARD · [0.05,0.12) → OPTIMIZE · ≥0.12 → INTEGRATE

## Context

GEOMETRY.md §5's strongest [MAP] object realized as code: ontology change is a
functor `F: C → D`, goal lifting is the **Kan extension** of utility along `F`,
and the commuting triangle `U_D ∘ F ≅ U_C` is evaluated literally — the
pre-shift utility composed with a learned functor-on-observables. Environment:
full reuse of `gridworld_wm` (ADR-001's a-priori K=6 relational slots;
improve-not-rewrite). The shift: an information-equivalent per-dimension
bijective recoding of all 18 observation features, fixed per universe.
Post-shift budget is scarce by design (500 episodes = 1.7% of pre-shift life,
set on the smoke family BEFORE pilot/confirmatory): at 3000 episodes relearning
trivially catches up (+0.037 smoke) and no mechanism is being tested. Zero LLM,
stdlib only, deterministic (CRC-seeded).

## Decision — lift the old utility through a learned correspondence

The lifted arm learns `F̂: D → C` from a 40-episode paired sensor-overlap
window (paid out of the same 500-episode budget), then reuses the pre-shift Q
through `F̂` (`U_D = U_C ∘ F̂`) and refines with the remainder. Primary metric =
success(lifted_policy) − success(relearn_from_scratch) on heldout tasks, equal
post-shift budget. Controls: `null_no_shift` (D == C; full machinery vs plain
reuse, must be ~0), `no_mapping_reuse` (old Q refined on raw D without F̂ —
isolates the mapping's contribution from mere Q reuse), `unlearnable_shift`
(recoding randomized per-state, so no global F exists; the identical machinery
must give ~≤0 — and this control is live, not structural: a garbage F̂ maps
heldout codes into the old Q's keyspace and can actively mislead below the
relearn floor).

## Verdict

**INTEGRATE** — `python rsc.py run ontology_shift`, confirmatory family 945000
(disjoint from pilot 940000 and smoke 949000), 5 seeds, 2026-07-14. All numbers
[FACT: run log]:

| condition | mean | std |
|---|---|---|
| **lifting_advantage** (primary) | **0.190** | 0.067 |
| null_no_shift (control) | −0.014 | 0.019 |
| no_mapping_reuse (ablation) | −0.055 | 0.091 |
| unlearnable_shift (control) | −0.029 | 0.008 |

- 0.190 ≥ 0.12 → **INTEGRATE**; failure condition (< 0.05) not triggered.
  Positive in 5/5 confirmatory universes (+0.093..+0.280); mapping recovery
  0.867–0.967; lifted absolute success 0.653–0.717 vs relearn 0.380–0.563
  [FACT: per-universe ONTOLOGY_LOG].
- Controls behaved: null_no_shift ~ 0 (the apparatus alone adds nothing),
  no_mapping_reuse ≤ 0 **at the mean** (the learned mapping — not mere Q reuse
  — is load-bearing; see caveat 1), unlearnable_shift ≤ 0 in 5/5 universes
  (where no global correspondence exists, the same machinery does not
  manufacture an effect).
- Honest reading: GEOMETRY.md §5's commuting triangle runs as code. Under an
  information-equivalent re-encoding, lifting the old utility through a
  correspondence learned from a small overlap window preserves value where
  equal-budget relearning cannot — «حفظ ارزش تحت تغییر چارچوب» is executable
  and, on this environment, true.

## Confirmed caveats (adversarial review)

1. **prediction.statement reads stronger than the per-universe data.** It says
   `no_mapping_reuse <= 0`, which holds at the mean (pilot −0.044 ± 0.069,
   confirmatory −0.055 ± 0.091) but not universe-wise: one pilot universe was
   **+0.057** and one confirmatory universe **+0.113** [FACT: per-universe
   logs]. The attribution of the advantage to F̂ is a mean-level claim over a
   noisy ablation, not a per-universe guarantee. Spec/docstring prose softened
   accordingly (no gating field touched).
2. **Stale seed-disjointness comment.** The docstring claimed disjointness only
   from the "987/991/993/994/995/997/998k families", omitting the nearby
   942xxx (multimetric_memory), 944xxx (attractor_memory), 946xxx
   (comparison_metacog_v2) and 948xxx (adaptive_forgetting_v2) families. No
   actual collision — 940000/945000/949000 overlap none of them — but the
   comment as written proved less than it claimed. Corrected to enumerate the
   real neighbourhood.
3. **The smoke family saw the primary effect before confirmation.** 949000 was
   used to set POST_SHIFT_BUDGET, and the full smoke pass at that budget also
   produced the primary: **+0.213** (INTEGRATE band), mapping recovery 0.967
   [FACT: --smoke rerun 2026-07-14]. Disclosed as a third-family peek during
   calibration; it is also a strength — the effect replicates on two disjoint
   families never used to freeze thresholds (945000 confirmatory +0.190,
   949000 smoke +0.213), not just the pilot family the SESOI was frozen on.

## Scope guard

C0–C3, synthetic deterministic gridworld. Per-dimension bijective recodings are
the MINIMAL shift class — structural shifts (feature merge/split, dimensionality
change) remain [MAP]; the paired sensor-overlap window is stipulated (a
calibration overlap must exist, as in a sensor replacement). A wrong F̂ is worse
than ignorance (unlearnable_shift ≤ 0 via active misleading), so lifting is not
a free lunch. No phenomenal/qualia claim. Honest reading: value survives a
re-labeling of the world's description when — and only when — a correspondence
is learnable from a small overlap window, at equal post-shift budget, on this
environment.
