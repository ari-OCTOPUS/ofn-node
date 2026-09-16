# BITEMPORAL-SPINE-SPEC evidence pack — 2026-08-20

Executable verification of the bitemporal spine **spec** (fixture M1–M4)
against the WAVE0 contract. Pure lab slice: no network, no live-spine
writes, no deployment.

- Test: `_ops/tests/test_bitemporal_spine_spec.py` (self-contained; reuses
  only `shadow_homeostasis.observation.parse_dt`)
- pytest: **15 passed** (see TEST-RESULTS.txt), Python 3.13.7
- Not registered in `run_all.py`

## What is VERIFIED here (contract logic, lab fixture)

| Spec requirement | Test |
|---|---|
| M1–M4 eligibility matrix at 10:10 / 10:30 / 11:30 | `test_decision_10{10,30}_matrix` · `test_decision_1130_matrix` |
| M4 (recorded < occurred) never eligible, any decision_time | `test_m4_future_never_eligible` |
| Correction supersedes **without overwrite**: believed-then 70, known-now 75, both versions + independent provenance retained | `test_correction_supersession_matrix` |
| Late-arrival boundary incl. replay-today semantics | `test_late_arrival_visibility_boundary` |
| Derived-memory leakage (summary derived 14:00 → ineligible at 11:00) | `test_derived_memory_leakage` |
| Vector-index leakage (future record engineered top-1 nearest) | `test_vector_index_leakage` |
| Restart persistence: output hash before/after reload identical | `test_restart_replay_hash` |
| Strict vs naive ablation: strict future-use 0, naive > 0 | `test_strict_vs_naive_ablation` |
| Context-builder contract (future ids [], UNKNOWN never 0, provenance, executable=false) | `test_context_builder_contract` · `test_context_excludes_future_derived_artifacts` |
| Missing timestamps → `INELIGIBLE_TEMPORAL_METADATA`, no injection | `test_data_contract_missing_timestamps_not_injected` |
| Gate table: VERIFIED on sharp fixture; NOT_VERIFIED on dull fixture (ablation cannot detect) | `test_gate_table_{passes_on_sharp_fixture, rejects_dull_fixture}` |

## What is NOT verified (and must not be claimed)

The **live spine remains `NOT_VERIFIED_BITEMPORAL`**. Two blockers, both
recorded elsewhere in this vault:

1. [FACT] ADR-043: `occurred_at`/`recorded_at` on the live spine are two
   consecutive reads of one clock (stdev ≈ 1 ms) — the bitemporal axis is
   not yet real in production data.
2. [UNKNOWN] It is not proven that *every* live memory read path
   (vault search, vector index, knowledge graph, summary retrieval, World
   Model context builder, DeepSeek prompt builder) routes through a
   `decision_time` query instead of latest-state reads.

Gate status for the lab slice: `VERIFIED_BITEMPORAL` (contract logic).
Gate status for the live spine: `NOT_VERIFIED_BITEMPORAL`.
Related: [[69-BITEMPORAL-PLAYBOOK-LATE-DATA-2026-08-20]] ·
[[HC-WM-MC-WAVE0-2026-08-20]] ·
[[../../03 - Projects/research-spec-compiler/adr/ADR-043-nase-dual-timestamp]]
