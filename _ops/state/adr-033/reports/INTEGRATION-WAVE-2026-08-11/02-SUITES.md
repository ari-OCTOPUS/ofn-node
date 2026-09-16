# Stage C — Suite Regression

## Gate result

- Required eight-suite gate: **PASS — 8/8 green**
- WORKLOCK / `run_all.py`: **untouched**
- Environment for test subprocesses: APPLY=`0`, PROPOSAL=`1`
- Log: `minimum-suites.log`

| Suite | Result |
|---|---|
| test_adr033_control_plane | PASS |
| test_approval_state | PASS |
| test_signals_registry_schema | PASS |
| test_registry_semantic_validator | PASS |
| test_kalman_shadow_pipeline | PASS |
| test_bcm_hebbian_shadow_e2e | PASS |
| test_nociceptor_chaos_shadow | PASS |
| test_adr034_neural_demote | PASS |

## Optional full `run_all.py`

Full suite was executed twice (not required as a replacement for the gate):

1. `full-run-all.log`: exposed a false ratchet regression because `_ops/_bak/**/center.py` was counted as production.
2. After the additive scanner repair, `full-run-all-after-fix.log`: required gate remains green; several pre-existing/non-gate debts remain red.

### Additive fixes completed

| Problem | Diagnosis | Additive repair | Verification |
|---|---|---|---|
| Telegram send ratchet 2→3 | inert `_bak` snapshot double-counted a production send site | exact exclusion of `_bak` / `patch_backups`; regression tests | `test_tg_send_audit.py`: 28/28 |
| LLM inventory/fence false bypass | inert `_bak/**/model_router.py` counted as live caller | exact non-production directory exclusion | inventory 6/6; fence 3/3 |
| dashboard profile-default red | test read live `OCTOPUS-flags.cmd`, so BARBELL override contaminated profile logic | isolate `_read_env_overrides` as the existing bare-profile test already does | `test_dashboard.py`: all checks green |

### Remaining full-suite discrepancies (not concealed)

1. **`test_pain_calibration.py` is pre-ADR-034 contract.** It expects neural `override=True` / `protective_halt`; accepted ADR-034 requires proposal-only (`override=false`, `executable=false`). Updating this test is a safety-contract rewrite (>30% semantics) and requires an explicit owner/ADR-alignment decision. Runtime was not weakened to satisfy it.
2. **`test_phantom_guards.py` reports real ledger debt.** Ten WORKLOCK-registered suites exist on disk but are not tracked by git; seven newly declared flags and seven resolved declarations drifted from the frozen ledger. The test was not silenced. Commit/tracking remains owner-controlled.
3. **`test_tg_callback_emitter_parity.py` attribution false-positive.** Runtime code proves `owner_console/conversation.py` emits `oc:*` and center routes `oc:*`; the scanner attributes the module to the approval bot and demands `oc` there. No live card is dead. Scanner graph repair is deferred rather than adding an unsafe approval-router verb.

No production outbound effect occurred during these suites.
