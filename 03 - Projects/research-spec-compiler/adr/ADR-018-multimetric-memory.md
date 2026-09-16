# ADR-018 — Multi-metric episodic memory: retrieval beyond semantic similarity (GEOMETRY.md §4)

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/multimetric_memory.yaml` (PASS 6/6) · `experiments/multimetric_memory.py`
- **Decision rule (GO/NO-GO):** retrieval_advantage < 0.05 → DISCARD · [0.05,0.10) → OPTIMIZE · ≥0.10 → INTEGRATE

## Context

GEOMETRY.md §4 formalizes اصل ۸ [P L667] — memory must index episodes by MORE
than semantic similarity — as a multi-metric space
`d_mem = (d_semantic, d_time, d_causal, d_provenance, d_outcome)`, marked
[SPEC]. This experiment moves that object to [RUN] for 4 of the 5 axes
(d_causal not instantiated; disclosed). Deterministic CRC-seeded grid-world,
full reuse of `gridworld_wm` + `memory_policy` lineage (ADR-012,
improve-not-rewrite), zero LLM. The stream is engineered so semantic-only
retrieval is GENUINELY insufficient: three life phases (14k stale early / 8k
trusted mid / 10k recent-but-POISONED late rollouts) write ~960 semantic keys
with cross-phase duplicates — same situation, conflicting advice — and the
poisoned late phase deliberately breaks the recency==quality shortcut.

## Decision — identical coverage, only vote ordering differs

Both rules see the IDENTICAL key set, so there is no coverage edge — the
advantage is pure indexing. `semantic_only` = plain majority over ALL matching
entries (frequency-weighted kNN — the natural, non-crippled semantic rule);
`multimetric` = the same matches, each vote weighted by
(recency + measured source win-rate + outcome)/3, equal thirds FROZEN a
priori. Primary metric = success(multimetric) − success(semantic_only) as
policies on the same 60 heldout tasks per universe. Seed discipline (ADR-001):
pilot family 942000 calibrated volumes and set the frozen bands (+0.112 mean);
confirmatory family 942500+ is disjoint and was never piloted.

## Verdict

**INTEGRATE** — `python rsc.py run multimetric_memory`, confirmatory family
942500 (disjoint from pilot 942000), 5 seeds, 2026-07-14. All numbers
[FACT: run log]:

| condition | mean | std |
|---|---|---|
| **retrieval_advantage** (primary) | **0.157** | 0.039 |
| recency_only_gain (ablation) | −0.015 | 0.045 |
| clean_stream_control | 0.000 | 0.000 |
| null_same_vs_same | 0.000 | 0.000 |

- 0.157 ≥ 0.10 → **INTEGRATE**; failure_condition (< 0.05) not triggered.
  Confirmatory mean exceeds both the pilot (+0.112) and the +0.10 hypothesis
  bar.
- **clean_stream_control is exactly 0.000** — the discriminating control: on a
  clean stream (no duplicates/poison) the weighting machinery buys nothing, so
  the advantage is CAUSED by the corrupted duplicates, not by the machinery
  per se.
- **recency_only_gain is NEGATIVE (−0.015)** — the time axis alone MISLEADS on
  this stream (the newest entries are poisoned): provenance/outcome are
  load-bearing, not redundant with recency.
- **null_same_vs_same is exactly 0** — no hidden asymmetry in the
  retrieval+evaluation path.

Honest reading: when semantic duplicates conflict across life phases,
weighting semantic ties by time + provenance + outcome recovers +0.157 heldout
success over semantic-only majority at identical key coverage — and the effect
vanishes exactly when the corruption is removed.

## Confirmed caveats (adversarial review)

1. **No per-axis ablation of provenance vs outcome.** `recency_only_gain`
   isolates the time axis, but provenance and outcome are only ever ablated
   JOINTLY — no provenance-only or outcome-only arm ran, so their individual
   contributions are not separated. By construction they are also correlated:
   reliability(source) is itself outcome-derived (measured source win-rate),
   which the spec discloses. The supported claim is "provenance+outcome are
   jointly load-bearing," not a per-axis attribution.
2. **"Two independent pipeline passes" was overstated (prose only).** The null
   condition recomputes the retrieval rule + evaluation twice, but the
   universe/stream build is memoized and shared across conditions — the null
   certifies determinism and symmetry of the retrieval+eval stage, not two
   independent end-to-end builds. Harmless to the verdict (conditions are
   MEANT to share one universe so only the retrieval rule varies); the
   docstring/spec prose was corrected alongside this ADR.
3. **Recency-only sign is not itself robust** (−0.015 ± 0.045). What is
   robust is what the ablation was preregistered to show: time-only weighting
   does NOT recover the advantage (−0.015 vs +0.157).

## Scope guard

C0–C3, synthetic grid-world episodic store; functional retrieval policy only.
No phenomenal/qualia claim; the C0–C3 ⇏ C4 firewall is respected. d_causal is
NOT instantiated — 4 of 5 axes of GEOMETRY.md §4 run; causality stays [SPEC].
Declared tradeoff: the multi-metric index costs three extra scalars per entry
plus a per-source reliability estimate, and on clean streams it buys exactly
0.000 — justified only where streams accumulate stale or unreliable
duplicates.
