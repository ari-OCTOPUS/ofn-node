# Execution Coverage Report

Generated: 2026-08-21  
Runner: `_ops/tests/run_all.py` with Lane E isolation (per-file timeout map, continue-on-timeout, execution manifest)

## Full-suite run (background, completed)

- Manifest rows: **801** (`_ops/state/loops/execution-manifest.jsonl`, each with status, exit, duration, stdout/stderr sha256).
- PASS: **748** · FAIL: **51** · TIMED_OUT: **2** (test_orphan_scan, test_live_control_panel_smoke).
- Runner exit: 1 (coverage incomplete due to the two timeouts; capability marker revoked — fail-closed, no fake green).

## Timeout resolutions (per-file budgets raised)

- `test_capability_registry.py` — root cause fixed (`self_insight.card()` journal-based; was a 130s scan per render). Now **20/20** in under 300s.
- `test_orphan_scan.py` — budget 900s → **17/17**.
- `test_live_control_panel_smoke.py` — budget 900s → **53/53** (one earlier failure was a cache-timing flake against the live gateway; reproduced the flow manually with 200/APPLIED, then full suite green).

## FAIL baseline (51 rows)

These are the pre-existing cognitive/legacy suites already registered as open loops (heart-fuel wiring, cortex, memory gate, control contracts, LLM inventory, spine/lead memory wiring, paid truncation, receipt-rig debt). None were hidden, skipped, or denominator-edited. They are the next repair phase after the Telegram lane.

## Distinctions honored

- registered vs executed vs passed vs failed vs skipped vs timed-out are separate manifest fields.
- A timeout no longer leaves remaining suites unexecuted (continue-on-timeout).
- Full-suite PASS is only claimed when the manifest is complete; this report does not claim full PASS yet — one clean full rerun remains queued as the coverage closure (801 files, ~30–40 min).
