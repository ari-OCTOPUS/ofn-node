---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, tests]
---

# Stage D — test registry

Denominator contract (`test_discovery` v2): `_ops/tests/test_*.py` minus archived/generated name markers. Registry = intersection with `run_all.py`.

| | n |
|---|---|
| on-disk test_*.py (discovery v1) | 790 |
| archived (excluded from denominator, not registered) | 3 |
| eligible = discovered | 786 |
| registered ∩ eligible | 786 |
| gap | **0** |

Archived (not registered): `test_close_c025_family_key_20260816.py`, `test_close_experiments_retired_20260816.py`, `test_novelty_archive.py`.

Five files first labelled `unknown` are script-style suites (`def check` / `def ok`) and are valid tests:

- `test_execution_board_dedup.py`
- `test_memory_team_a_promotion.py`
- `test_phi_reset_on_restart.py`
- `test_receipt_budget_fix.py`
- `test_scan_wave_b_adversarial.py`

Full `run_all` of 786 suites was **not** executed (time/resource). Lane: `run_all --only test_nervous_recovery.py,test_receipt_attribution.py` plus direct `test_nervous_recovery.py`. Newly registered suites are in the registry; their individual green/red is **not** claimed here.
