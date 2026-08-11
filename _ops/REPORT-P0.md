# REPORT-P0

## خط حقیقت

```text
octopus-product-packed + ti-evidence-verified + security-gaps-closed
!= committed (pending owner vote) != master-merged != armed != AGI
```

## Done

### Production fixes (7 files)
- `context_bundle.py`: schema validation (`schema != SCHEMA` → reject)
- `dark_capabilities.py`: worktree parent scan bug + `test_intelligence` skip
- `integrations/outbound_https.py`: NOT_WIRED zero-mutation + `action_sha256` binding + approval expiry
- `owner_console/collab_memory.py`: state_dir containment + URL-decode secret scan
- `owner_console/collab_sim.py`: env restore + state_dir binding
- `owner_console/collaborator.py`: content-free memory summary + deterministic turn_id
- `telegram_center/approval_store.py`: mark_done approved-only + action_sha256 metadata
- `tool_request.py`: actionable rejection message

### Test Intelligence package (15 files)
- `test_intelligence/` — trace_schema, policy_oracle, chaos_proxy, discovery, dark_inventory, build_evidence, adapters (3), README, __init__ (2)
- `test_intelligence/redteam_cases.yaml` — 25 cases × 6 ASI codes
- `test_intelligence/evidence/` — dark-inventory.json + verification-summary.json

### New tests (10 files)
- `test_ti_trace_contract.py` — 8/8
- `test_ti_context_bundle_contract.py` — 13/13
- `test_ti_router_snapshot.py` — 8/8
- `test_ti_breaker_chaos.py` — 10/10
- `test_ti_collab_security.py` — 12/12
- `test_ti_discovery_eval.py` — 9/9
- `test_ti_policy_oracle.py` — 9/9
- `test_ti_redteam_injection.py` — 3/3 (25/25 cases)
- `test_ti_dark_inventory.py` — 4/4
- `tests/fixtures/lab_data.json` — synthetic lab fixture

### Existing tests fixed (11 files)
- `test_collab_components.py`, `test_dark_capabilities.py`, `test_dual_brain.py`,
  `test_flag_drift.py`, `test_outbound_https.py`, `test_outbound_https_approval_port.py`,
  `test_paid_router_dark_config.py`, `test_studio_telegram.py`, `test_telegram_channel.py`,
  `test_tg_approval_store.py`, `test_ziman_wiring.py`, `test_tool_request.py`

### Docs
- `PRODUCT-V1.md` — product definition
- `GOALS-OCTOPUS.md` — honest goal status
- `OWNER-ACTIONS-REQUIRED-2026-08-11.md` — three owner-only actions
- `test_evidence/paired-failure-matrix.json` — updated with final digest

## Evidence (paths + commands)

```text
Full suite:  python _ops/tests/run_all.py
  → 588/588 GREEN · exit=0 · zero SKIP/ENV_BLOCKED/TIMEOUT
  → output sha256:b4997eda32aa148acc2eee0eaa3cb6ddb21a4d5074af29152a90e8729a070b74

Target suites (18/18):  subprocess-isolated, exit=0, zero markers
  → _ops/test_evidence/paired-failure-matrix.json

TI selective (9 files):  76/76 checks + 25/25 red-team cases
  → _ops/test_intelligence/evidence/verification-summary.json

Dark scan:  368 flags · 271 dark · 81 tuning · live_source=absent
  → _ops/test_intelligence/evidence/dark-inventory.json

Validators:
  validate_contract.py: STATIC CONTRACT: PASS
  test_vault_hygiene_ratchet: 7/7
  test_obsidian_index_budget: 6/6
  test_manifest_truth: 4/4
  test_capability_manifest_registry: 10/10
  test_module_self_manifest: 4/4
  validate_frontmatter: PRE_EXISTING_DEBT:4 (not introduced by this session)
  find_broken_links: PRE_EXISTING_DEBT:1 curated + 25 operational (not introduced)

Whitespace: git diff --check clean (with cr-at-eol)
Syntax: py_compile clean (38 files)
Sensitive-literal scan: PASS (zero hits)
```

## Flags touched (before → after)

```text
NO flags armed. NO flags changed on live tree.
All changes are in worktree `octopus-integration-collaborator` only.

Dark flags found (structural, not armed):
  271 dark / 368 total (81 tuning, 0 partial, live_source=absent)
```

## Gates

- [x] TI tests on working tree: green (588/588 + 76/76 TI + 25/25 RT)
- [x] `PRODUCT-V1.md` exists
- [x] Zero runtime noise in staging plan (sqlite/WAL/SHM/jsonl excluded)
- [x] WORKLOCK files untouched (`run_all.py`, `wiring.py`, `center.py`, `orphan_scan.py`)
- [x] Whitespace clean
- [ ] Commit performed — **PENDING OWNER VOTE**

## NOT done / blocked

1. **Commit** — needs explicit owner "commit" vote
2. **`run_all.py` registration of `test_ti_*.py`** — WORKLOCK file, needs lane clearance
3. **`OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL=1`** — owner-only activation on live tree
4. **CSV واریزی‌ها** — owner-only data placement
5. **آدرس لید ۶۶۷۹۵۱** — owner-only information

## test_ti_*.py filenames for run_all.py registration

These 9 files should be added to `TESTS` list in `_ops/tests/run_all.py` when the lane is free:

```text
"test_ti_trace_contract.py",
"test_ti_context_bundle_contract.py",
"test_ti_router_snapshot.py",
"test_ti_breaker_chaos.py",
"test_ti_collab_security.py",
"test_ti_discovery_eval.py",
"test_ti_policy_oracle.py",
"test_ti_redteam_injection.py",
"test_ti_dark_inventory.py",
```

All are script-native (exit 0/1), not pytest — they should go in `TESTS`, not `PYTEST_TESTS`.

## Owner decisions needed

1. **Commit?** — `git add` only scoped files (listed below), then commit with message:
   `test(ti): grounded test-intelligence pack + close security gaps + PRODUCT-V1`
2. **Merge to master?** — default OFF; only if owner says yes
3. **P1 start?** — only after commit + three prerequisites in PRODUCT-V1.md

### Files to stage (commit scope)

```text
Source (8):
  _ops/context_bundle.py
  _ops/dark_capabilities.py
  _ops/integrations/outbound_https.py
  _ops/owner_console/collab_memory.py
  _ops/owner_console/collab_sim.py
  _ops/owner_console/collaborator.py
  _ops/telegram_center/approval_store.py
  _ops/tool_request.py

Tests (12 modified + 9 new + 1 fixture):
  _ops/tests/test_collab_components.py
  _ops/tests/test_dark_capabilities.py
  _ops/tests/test_dual_brain.py
  _ops/tests/test_flag_drift.py
  _ops/tests/test_outbound_https.py
  _ops/tests/test_outbound_https_approval_port.py
  _ops/tests/test_paid_router_dark_config.py
  _ops/tests/test_studio_telegram.py
  _ops/tests/test_telegram_channel.py
  _ops/tests/test_tg_approval_store.py
  _ops/tests/test_tool_request.py
  _ops/tests/test_ziman_wiring.py
  _ops/tests/test_ti_breaker_chaos.py
  _ops/tests/test_ti_collab_security.py
  _ops/tests/test_ti_context_bundle_contract.py
  _ops/tests/test_ti_dark_inventory.py
  _ops/tests/test_ti_discovery_eval.py
  _ops/tests/test_ti_policy_oracle.py
  _ops/tests/test_ti_redteam_injection.py
  _ops/tests/test_ti_router_snapshot.py
  _ops/tests/test_ti_trace_contract.py
  _ops/tests/fixtures/lab_data.json

Test Intelligence (15):
  _ops/test_intelligence/ (all files)

Docs (4):
  _ops/PRODUCT-V1.md
  _ops/GOALS-OCTOPUS.md
  _ops/OWNER-ACTIONS-REQUIRED-2026-08-11.md
  _ops/test_evidence/paired-failure-matrix.json
```

### Files to EXCLUDE from staging (runtime noise)

```text
_ops/agi2027_runtime/octopus_ops.sqlite3
_ops/agi2027_runtime/*.sqlite3-shm
_ops/agi2027_runtime/*.sqlite3-wal
_ops/budget/organ-gate-log.jsonl
_ops/state/channel-status.json
_ops/state/school-awareness.json
_ops/state/synapse-trail.jsonl
_ops/state/run_all_closeout.log
```

## Next phase entry criteria

- P1 can start only after:
  1. Owner votes "commit" and it's done
  2. Three prerequisites in PRODUCT-V1.md are met
  3. Owner says "start P1"
