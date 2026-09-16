# Research-Spec Compiler

Turn a raw research **idea** into an **executable, falsifiable spec** — and refuse
the ones that are secretly prose. Built to plug straight into the *Cognitive
Kernel 0.1* research loop (idea → ADR → EXP → decision), but the compiler is
domain-generic.

> The rule it enforces (from your own note):
> **no metric → useless · no falsifiability → pseudo-research · no api_contract → not connectable · no mvp → not runnable · no decision_rule → no closure.**

## What's in the box

```
research-spec-compiler/
├─ rsc.py                         # entry point (validate / run / list / scaffold)
├─ spec_compiler/
│  ├─ model.py                    # 11 canonical fields + YAML/JSON loader (stdlib)
│  ├─ validator.py                # the linter: 5 killer gates + consistency checks
│  ├─ harness.py                  # ablation runner + decision-rule engine
│  └─ cli.py
├─ demo/mock_experiments.py       # SYNTHETIC seeded experiments (so `run` works, zero data)
├─ specs/
│  ├─ debate_extraction.yaml      # worked example (multi-agent debate)
│  ├─ wm_abstraction.yaml         # real project hypothesis H-OWN-03 / EXP-001
│  └─ _broken_example.yaml        # intentionally fails, to show the linter bite
├─ schema/
│  ├─ research_spec.schema.json   # JSON Schema (CI / editor validation)
│  └─ research_spec.template.yaml # blank template with inline guidance
├─ prompts/spec_compiler_system_prompt.md   # reusable "idea → spec" prompt
└─ tools/spec_compiler.html       # interactive tool: live validation + JSON/YAML export
```

## The schema (11 fields)

`idea · hypothesis · prediction · metric · experiment · failure_condition ·
architecture · api_contract · mvp · evaluation · decision_rule`

Each maps to a gate. The five **killers** are enforced hard (they fail the
build); consistency checks (e.g. the kill line must sit inside
`[baseline, expected]`) are warnings.

## Quickstart

No install needed for validation of the JSON mirrors (stdlib only). YAML needs
`pip install pyyaml`.

```bash
cd research-spec-compiler

python rsc.py list                                   # see specs + runnable experiments
python rsc.py validate specs/debate_extraction.yaml  # -> PASS
python rsc.py validate specs/_broken_example.yaml    # -> FAIL (5 reasons)
python rsc.py run debate_extraction                  # ablation -> verdict INTEGRATE
python rsc.py run wm_abstraction                      # ablation -> verdict INTEGRATE
python rsc.py scaffold specs/my_idea.yaml             # blank spec to fill
```

Open `tools/spec_compiler.html` in a browser for the same 5 gates, live, with a
decision-rule map and JSON/YAML export.

## The two demos

| spec | metric | baseline → expected | kill line | expected verdict |
|------|--------|---------------------|-----------|------------------|
| `debate_extraction` | F1 | 0.71 → 0.83 | F1 < 0.75 | **INTEGRATE** |
| `wm_abstraction` (H-OWN-03) | transfer_accuracy | 0.62 → 0.74 | < 0.67 | **INTEGRATE** |

## How it connects to the Cognitive Kernel project

- **Faithful to the corpus.** `wm_abstraction` encodes H-OWN-03 / EXP-001, with
  the metric anchored to reference-file **principle #7** (*abstraction is stable
  when useful for prediction / compression / transfer*) → metric = transfer.
- **ADR linkage.** Each spec's `architecture.pattern` is the thing an ADR
  commits to; the `decision_rule` is the GO/NO-GO the project asks for.
- **No overclaiming.** `demo/mock_experiments.py` returns **synthetic** seeded
  scores so the pipeline runs before real data exists. The harness prints
  `[SYNTHETIC/mock scores]`. Swap `Condition.run` for the real evaluation to go
  live — do not report mock numbers as results (matches the project's C0–C4
  discipline: never lift a functional result to a stronger claim).

## Real experiments (`experiments/`)

Real (non-synthetic) implementations live in `experiments/` and are registered
in `experiments.REGISTRY_REAL`. A real entry **overrides the synthetic mock of
the same name** in the CLI, and the run header switches from
`[SYNTHETIC/mock scores]` to `[REAL run — <dataset>]`, so mock numbers can
never masquerade as results.

- `experiments/gridworld_wm.py` — H-OWN-03 gone live: deterministic grid-world
  task family, tabular Q-learning, K-slot WM bottleneck with *learned* gating
  (greedy forward selection + swap refinement, paid from the same episode
  budget). Design decisions, pilot/confirmatory separation and the verdict are
  recorded in `adr/ADR-001-wm-bottleneck-real-harness.md`.
- `experiments/drake_kernels.py` — Monte-Carlo "Drake census" over simulated
  universes (`adr/ADR-002`); `specs/drake_multiverse.yaml` is the intentionally
  FAILING companion (unfalsifiable by design).
- `experiments/geometry_abstraction.py` — H-GEO-01: geometrizes principle #7 as
  **RTA** (Representational Transfer Alignment, *not* RSA) and tests that it
  predicts transfer. The full geometric formalization of the raw research corpus
  is in `GEOMETRY.md`; the layer decision is `adr/ADR-003`.
- `experiments/homeostasis.py` — EXP-003: a deterministic `HomeostasisWorld`
  (`D_t = Σ wᵢ|sᵢ−sᵢ*|`) testing a predictive-self-model (MPC) vs reactive
  control under OOD perturbation (`adr/ADR-005`).
- `experiments/consolidation.py` — H-OWN-04 / EXP-002: schema-library
  consolidation vs raw replay at equal budget (`adr/ADR-006`).
- `experiments/wm_transfer_gain.py` — H-OWN-03 v2: the relative preregistration
  (paired transfer gain) after v1's absolute bar scored REJECTED (`adr/ADR-004`).
- `experiments/organism_bridge.py` + `experiments/hybrid_organism.py` —
  H-HYBRID-01: the read-only afferent bridge into the live octopus organism
  (`F:\backup`, `mode=ro&immutable=1`) + the four-mechanism hybrid cortex organ
  that learns to self-predict the body's event stream (`adr/ADR-008`). The
  owner-gated shadow-attach proposal is in `attach-proposal/`.

## Full spec ↔ verdict map (real runs)

| spec | ADR | verdict |
|------|-----|---------|
| `wm_abstraction` (H-OWN-03, absolute bar) | ADR-001 | **REJECTED** |
| `drake_kernels` (Drake census) | ADR-002 | **OPTIMIZE** |
| `geometry_abstraction` (H-GEO-01 / RTA) | ADR-003 | **OPTIMIZE** |
| `wm_abstraction_v2` (H-OWN-03 relative) | ADR-004 | **OPTIMIZE** |
| `homeostasis` (EXP-003) | ADR-005 | **OPTIMIZE** |
| `consolidation` (H-OWN-04) | ADR-006 | **INTEGRATE** |
| — governance (Central Law, 3 gates) | ADR-007 | accepted |
| `hybrid_organism` (H-HYBRID-01) | ADR-008 | **OPTIMIZE** (after re-gating) |
| `social_mirror` (H-OWN-01) | ADR-009 | **INTEGRATE** (DiD 0.398) |
| `comparison_metacog` (H-OWN-02) | ADR-010 | **INTEGRATE** (+0.019, attribution caveat) |
| `prospective_memory` (H-OWN-05) | ADR-011 | **INTEGRATE** (0.475) |
| `memory_policy` (H-OWN-06) | ADR-012 | **INTEGRATE** (0.204) |
| `causal_selfmodel` (H-OWN-07) | ADR-013 | **REJECTED** (−0.098, honest negative) |
| `control_signals` (H-OWN-08) | ADR-014 | **INTEGRATE** (0.355) |
| `adaptive_forgetting` (EXP-004) | ADR-015 | **OPTIMIZE** (0.056) |
| `retrieve_compute` (EXP-005) | ADR-016 | **INTEGRATE** (0.031) |
| `ontology_shift` (H-GEO-02, Kan) | ADR-017 | **INTEGRATE** (0.190) |
| `multimetric_memory` (Principle 8) | ADR-018 | **INTEGRATE** (0.157) |
| `attractor_memory` (Hopfield) | ADR-019 | **INTEGRATE** (0.612) |
| `comparison_metacog_v2` | ADR-020 | **OPTIMIZE** (0.005) |
| `adaptive_forgetting_v2` (vs FIFO) | ADR-021 | **REJECTED** (0.023, honest negative) |
| `drake_multiverse` | — | **FAIL** (unfalsifiable, by design) |

The C×A claims lattice is realized as data: `CLAIMS_LEDGER.csv` (built by
`tools/build_claims_ledger.py`, tested by `tools/test_claims_ledger.py`).

See `adr/README.md` for the ADR index. Run `python tests/test_specs_and_registry.py`
to check every real spec passes, the broken ones fail, and the registry is
well-formed.

## Extending

1. `python rsc.py scaffold specs/<name>.yaml`, fill it (or use the HTML tool /
   the system prompt in `prompts/`).
2. `python rsc.py validate specs/<name>.yaml` until PASS.
3. Add a real experiment module under `experiments/` returning
   `(conditions, primary)` and register it in `experiments/__init__.py`
   (mocks in `demo/mock_experiments.py` are for pipeline demos only).
4. `python rsc.py run <name>` → machine verdict via `decision_rule`.
5. Record the architectural commitment as an ADR in `adr/`.
