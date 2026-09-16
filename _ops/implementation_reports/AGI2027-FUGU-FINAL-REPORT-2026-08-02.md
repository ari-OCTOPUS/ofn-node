> [!IMPORTANT]
> Superseded status update — 2026-08-02
>
> This report was created before the final production wiring.
> Final truth now:
> - G-03 is wired to production lead_outbound_transport.
> - Commit: 50de1c8 wire owner-controlled G03 outbound WAL.
> - Support files committed in: c5a047e track agi2027 control support files.
> - Telegram live smoke passed:
>   - /ops OK
>   - /outbound status OK
>   - /now passthrough OK
> - Flags:
>   - OCTOPUS_WIRE_TG_CONTROL=1
>   - OCTOPUS_WIRE_LEAD_OUTBOUND_WAL=1
>   - OCTOPUS_WIRE_VALUE_LEDGER=1
> - Remaining:
>   - no real customer email smoke yet
>   - Project-F remains blocked until PROJECTF_API_* credentials exist
>
---
# AGI2027 / Fugu / Telegram Control â€” Final Execution Report

Generated: 2026-08-02 (ZCode)
Root: `F:\backup`
Install location: `_ops/agi2027_control/` (NOT `_octopus/` â€” see Â§0 below)

---

## 0. What changed vs the dropped-in PowerShell runner (and why)

The PowerShell runner you pasted was written by a model that had **no disk access** and
therefore could not see three real problems. Before running it I scanned `F:\backup` and
made three corrections, each evidence-backed:

1. **Install path.** The runner would create `_octopus/__init__.py` and
   `_octopus/agi2027_control/`. But `_octopus/` already exists (since 2026-07-18) as a
   **live infrastructure** directory (`config/`, `logs/`, `manifests/`, `quarantine/`,
   `queue/`, `reports/`, `state/`). Dropping a package there is a collision. **Fix:**
   installed under `_ops/agi2027_control/` instead. Confirmed post-run: `_octopus/` is
   byte-for-byte unchanged.

2. **Full-drive scan.** `FuguFootprint.scan` used `ROOT.rglob("*")` from `F:\backup` â€”
   exactly what every megaprompt Â§0 forbids (2 AV engines, 3-6ms/file, has hung the
   laptop). **Fix:** `FuguFootprint` now defaults to scanning `_ops/` only; a wider scan
   requires an explicit `root=` opt-in.

3. **Honesty about wiring.** I grepped: **0 production readers** of the new flags/modules
   (`OCTOPUS_WIRE_TG_CONTROL`, `OCTOPUS_WIRE_VALUE_LEDGER`, `OCTOPUS_SYNC_AGENT_BACKEND_SUMMARY`,
   `try_handle_control`, `ProjectFAdapter`, `PROJECTF_API_*`, `FUGU_MAX_API_KEY`). The
   runner's "PASS" verdict would have been a **green-lie**: the unit tests pass, but nothing
   in the live organism reads any of it. **Fix:** the report below labels these as `STAGED`
   (not wired) and the G-03 / Project-F / Telegram hooks as `NEEDS_OWNER_HOOK`.

## 1. Safety
- fake_green: **false**
- external calls performed: **false**
- credentials changed: **false** (`.env` untouched â€” secrets only)
- production code edited: **false** (only new files under `_ops/agi2027_control/`)
- `_octopus/` live infrastructure: **unchanged**

## 2. Installed files (all new, all under `_ops/agi2027_control/`)
- `runtime.py` â€” AuditLog, IdempotencyStore, PolicyGate, OutboundWriteAheadLedger,
  ProjectFAdapter, AdaptiveValueLedger, FuguFootprint, ManagedFlags, ControlPlane
- `__init__.py`, `integration.py`, `rollback.py`, `run_tests.py`
- `tests/__init__.py`, `tests/test_runtime.py`

## 3. Tests â€” REAL result
```
python -X utf8 _ops/agi2027_control/run_tests.py
Ran 14 tests in 0.096s â€” OK â€” TEST_EXIT=0
```
Two real bugs were found-and-fixed during this run (not hidden):
- **WinError 32** on SQLite handles during tempdir cleanup â†’ added `close()` methods +
  `try/finally` in tests.
- **LOW_IMPACT logic bug**: `owner_visible=True` was inflating `useful`, so a costly
  no-output leg never flagged low. Fixed: `useful` now counts only real value
  (output_score + settled effects); observation alone does not lift a leg out of LOW_IMPACT.

The pre-existing `tests/test_sync_agent.py` still passes **10/10** â€” nothing broke.

## 4. STAGED flags (0 production readers â€” verified before this run)
| flag | meaning | status |
|---|---|---|
| `OCTOPUS_WIRE_TG_CONTROL` | enable Telegram control adapter | STAGED â€” no prod reader |
| `OCTOPUS_WIRE_VALUE_LEDGER` | enable adaptive value ledger | STAGED â€” no prod reader |
| `OCTOPUS_SYNC_AGENT_BACKEND_SUMMARY` | compact sync_agent summary | STAGED â€” no prod reader |

These are settable via the ControlPlane's `managed_flags.json` (separate from
`OCTOPUS-flags.cmd`), and explicitly reported as `staged_not_wired` by the API.

## 5. NEEDS_OWNER_HOOK / BLOCKED (honest)
| id | status | why |
|---|---|---|
| G-03-LIVE-SMTP-HOOK | NEEDS_OWNER_HOOK | Write-ahead ledger installed + tested. NOT auto-wired into `legs/lead_outbound_transport.py` SMTP boundary â€” wiring must be an explicit owner-approved edit. Activation snippet in `runtime._snippet`. |
| TELEGRAM-CENTER-LIVE-HOOK | NEEDS_OWNER_HOOK | ControlPlane + `try_handle_control` installed + tested. `telegram_center/center.py` was NOT blind-edited. Activation: set flag + call `try_handle_control(text, {is_owner})` in the owner message handler. |
| PROJECTF-EXTERNAL-API | BLOCKED_UNTIL_CONFIGURED | ProjectFAdapter is real + tested in BLOCKED/READY modes. External call requires `PROJECTF_API_BASE_URL` + `PROJECTF_API_TOKEN` + owner+safety gates. No credentials exist. |

## 6. Recommended next step
**G-03 is the only one that touches real customers** (lead outbound is armed, cap=10).
The ledger is ready; the one-line SMTP-boundary hook is the highest-value, lowest-risk
wiring â€” but it must be an explicit owner-approved code edit, not this package.

---

## Rollback
```powershell
# The package is additive; to remove it entirely:
Remove-Item -Recurse -Force F:\backup\_ops\agi2027_control
# (rollback.py restores from a backup dir if one was made; none was needed here â€” all files are new.)
```
