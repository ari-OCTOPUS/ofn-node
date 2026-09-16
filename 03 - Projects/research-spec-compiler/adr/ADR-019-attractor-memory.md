# ADR-019 — Attractor memory: noisy retrieval as basin descent (H-GEO-02)

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/attractor_memory.yaml` (H-GEO-02, PASS 6/6) · `experiments/attractor_memory.py`
- **Decision rule (GO/NO-GO):** noisy_retrieval_advantage < 0.10 → DISCARD · [0.10,0.40) → OPTIMIZE · ≥0.40 → INTEGRATE

## Context

H-GEO-02 realizes the energy-landscape object of GEOMETRY.md §3 ("associative
memory = energy system; retrieval = falling to the floor of an attraction
basin" [P L59, L539]) — previously [SPEC], now [RUN]. A real Hopfield network
(Hebbian integer weights, zero diagonal, asynchronous sign-update descent to a
guaranteed fixed point) is compared against an exact-key hash lookup whose miss
falls back to a fair CRC-seeded 1/M guess — the non-strawman baseline, since it
strictly dominates fail-on-miss. Zero LLM, pure stdlib, fully deterministic
(everything CRC-seeded, universes memoized so all conditions are paired on
identical patterns, probes, and fallback draws).

**Frozen operating point** (pilot family 944000, calibration only): N=64 bits,
M=8 stored patterns (load 0.125), k=14 flipped bits (~22% corruption). Pilot
mean gap +0.685 over 5 seeds (range 0.567–0.833). The confirmatory family
944500+ is disjoint and was never piloted.

## Decision — pin the effect to basin geometry, not to "fuzzy beats exact"

The gated quantity is the mechanism-specific completion advantage:
`accuracy(attractor) − accuracy(exact_lookup)`, paired on identical probes.
Three zero/collapse controls plus a capacity ablation make the claim breakable:
`null_same_vs_same` (must be exactly 0), `clean_probe_gap` (k=0: exact lookup
is perfect, advantage must vanish), `saturating_noise_gap` (k=32 = 50%: probe
is as far as a random point; descent lands in spurious minima while exact keeps
its 1/M fallback, so the delta goes negative), and `overload_gap` (M=24, load
0.375 ≫ Hopfield capacity ~0.138N: cross-talk destroys the basins). The pilot
showed the paired delta genuinely goes negative under saturation and overload —
the primary is not structurally positive.

## Verdict

**INTEGRATE** — `python rsc.py run attractor_memory`, confirmatory family
944500 (disjoint from pilot 944000), 5 seeds, 2026-07-14. All numbers
[FACT: run log]:

| condition | mean | std |
|---|---|---|
| **noisy_retrieval_advantage** (primary) | **+0.612** | 0.160 |
| null_same_vs_same | 0.000 | 0.000 |
| clean_probe_gap (control) | −0.051 | 0.101 |
| saturating_noise_gap (control) | −0.119 | 0.022 |
| overload_gap (capacity ablation) | −0.051 | 0.013 |

- 0.612 ≥ 0.40 → **INTEGRATE**; failure_condition (≤ 0.0) not triggered.
  Confirmatory 0.612 sits below the pilot mean +0.685 but inside the pilot
  seed range (0.567–0.833) — no sign of pilot overfit.
- The controls carry the claim: on clean probes the advantage is ~0 (−0.051 —
  slightly negative, as preregistered, because at load 0.125 a stored pattern
  is occasionally not a stable fixed point); under saturating noise it is
  negative (−0.119: descent falls into spurious minima while the exact arm
  keeps its 1/M fallback); beyond capacity it collapses (−0.051). The
  advantage exists only inside the energy landscape's capacity bound and only
  for moderately corrupted probes — that is the attractor-completion
  signature, not "any fuzzy matcher beats exact match."

## Confirmed caveats (adversarial review)

1. **The kill line was set at zero, not at a SESOI** — failure_condition is
   `noisy_retrieval_advantage <= 0.0`, so any tiny positive advantage would
   survive it. Generous by construction; immaterial here because the effect is
   large (0.612, ~8 SE above 0 with 5 seeds) and the decision_rule's DISCARD
   band (< 0.10) supplies the practical smallest-effect gate — but a v2 should
   put the SESOI in the failure_condition itself.
2. **The primary must never be quoted without its controls.** Clean-probe
   −0.051 ± 0.101 (~0) and saturating −0.119 ± 0.022 (~0/negative) are what
   distinguish basin completion from generic fuzzy matching; +0.612 alone
   overstates the claim. Note the clean control is not exactly 0 — its slight
   negativity (occasional destabilized stored pattern) is itself Hopfield
   behavior near capacity.
3. **Synthetic binary patterns only.** The result holds for random bipolar
   patterns in {−1,+1}^64. The schema-key application to the kernel memory
   store — retrieving structured kernel entries from corrupted or partial
   cues — is future work and is NOT established here: real key distributions
   are correlated, and correlated patterns reduce Hopfield capacity below
   0.138N. Only flip-noise (exactly k corrupted bits) was tested; masked or
   partial probes were not.

## Scope guard

C0 (functional), synthetic bipolar patterns; the exact-lookup fallback and the
operating point are stipulated. No claim about biological memory and never a
phenomenal/qualia claim (C0–C3 firewall, GEOMETRY.md §0). Honest reading:
under moderate corruption, Hopfield basin descent retrieves stored random
patterns far better than an exact-key store with a fair guess fallback, and
the advantage disappears exactly where basin geometry says it must — clean
probes, saturating noise, and loads beyond capacity.
