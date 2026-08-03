# Decision Record — nbb-cp-kre Verification (2026-08-03)

**Decision ID:** DR-NBB-CP-KRE-VERIFY
**Date:** 2026-08-03
**Decision level:** D3 (sandbox verification, not live)

## Context
nbb-cp-kre registered as BASELINE_PREEXISTING STAGED_READONLY_TOOL. Needed verification before any live use.

## Verification performed
1. ✅ Created isolated `.venv` (not global pip)
2. ✅ Installed deps inside venv only
3. ✅ Import check passed
4. ✅ Ran `run_pipeline` on PRE-0 (14 files, safe sample)
5. ✅ Dashboard-only mode: HTTP 200 on port 8599
6. ✅ PRE-0 unchanged after scan (14 files before/after)
7. ✅ Test artifacts cleaned up (.venv, kre-out-test removed)

## NOT done
- ❌ Watcher/live mode NOT enabled
- ❌ Full vault scan NOT performed (only PRE-0 sample)
- ❌ Dashboard NOT left running

## Decision
- Status: VERIFIED_SAFE_READONLY_TOOL
- Can be run safely with venv + small vault
- Watcher mode still requires separate DR
- Full vault scan should use cache + off-peak timing

## Rollback
- All test artifacts removed
- No changes to vault
- No global Python changes
