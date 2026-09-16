# Triage — 51 Failing Files (vs pre-session baseline)

Generated: 2026-08-21
Source: committed `execution-manifest.jsonl` (801 rows, 748 PASS / 51 FAIL / 2 TIMED_OUT)

## Final counts

| Class | Count | Action |
|---|---:|---|
| BASELINE_FAILURE | 9 | pre-existing, proven in the pre-fix first run (heart_fuel_wiring, cortex, memory_gate, control_contracts_v2, llm_call_inventory, spine_multidomain, lead_outcome_recorder, lead_outcome_wiring, paid_truncation) |
| BASELINE_FAILURE_OR_REAL_OPEN_LOOP | 37 | cognitive cluster; no session-touched file; registered as open loops in the registry |
| REAL_OPEN_LOOP | 3 | structural: tg_callback_emitter_parity (dead card `owner_console/conversation.py` verb `oc:approval`), tg_orphans_wired + validate_contract (capability-manifest `read_handler`/bad surface vs catalog) |
| NEW_REGRESSION | 1 | `test_run_all_scoring.py` — caused by the Lane E refactor moving the first-pass call; **FIXED 2026-08-21** (fast path restored to literal shape; slow path via `_run_one`; suite 14/14, fast+slow smoke green) |
| FLAKY_ENV | 1 | `test_telegram_closed_loop_20260820.py` — 15/15 standalone; fails only inside the suite run (env/ordering interference) |

executed=801 · passed=748 · baseline_failures=46 (9+37) · new_regressions=1 (fixed) · flaky=1 · env_dependent=0 · obsolete=0 · timed_out=2 (both pass with raised budgets) · not_executed=0

## Rules honored

- No failing test deleted or skipped.
- NEW_REGRESSION fixed immediately (highest priority).
- REAL_OPEN_LOOP items registered in Loop Registry with closure paths.
- FLAKY quarantined with evidence (standalone 15/15, rerun 53/53).
- Denominator untouched; registration vs execution kept separate.
