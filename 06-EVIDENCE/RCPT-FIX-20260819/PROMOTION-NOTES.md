# RCPT-FIX-20260819 — CORE-AUTO-DEBUG promotion (owner standing decision CORE-LIVE-LEARNING-01)

## Scope (3 defects closed)
- **RCPT-1** budget_before basis = remaining daily budget (was: the call's own cost_usd → all 82 receipts showed negative budget_after). Wired: model_router.py `budget_before_aud=remaining_budget_aud(_rp)`; logic in cost_receipt.py::remaining_budget_aud (today's COMPLETE receipts, cap 30 AUD per LEARNING-FIRST-BUDGET-EXPANSION-01).
- **RCPT-2** COST_UNOBSERVABLE / per-call-cap violation today blocks the general paid path — the fail-closed promise in the COST-OBS-1 comment, now actually read. Wired: `_ask_paid` pre-check via cost_receipt.py::paid_blocked_today → `_paid_log(error="paid_blocked_cost_unobservable")`, no dispatch.
- **G10/G11** reservation window reset (start_override) and stop now always write an independent receipt to `_ops/state/cortex/reservation-receipts.jsonl` (schema reservation-receipt/1) with previous counters — reset is never an invisible effect (ODN-6 governance).

## Diff honesty note
`_ops/cortex/model_router.py` is git-tracked BUT the working tree contained pre-existing uncommitted owner changes; therefore the full `git diff` (702+/613−) is NOT this promotion. This promotion's exact changes are `RCPT-HUNKS.diff` (the two RCPT hunks, -U6 context). `cost_receipt.py` and `live4_reservation.py` are untracked-new files; their complete promotion snapshots are included (`*.promotion-snapshot`).

## Tests
`_ops/tests/test_receipt_budget_fix.py` — **15/15 PASS** (test-output.txt): remaining-budget math (today-only, cap-only-COMPLETE), adapter end-to-end budget_after≥0, blocked detection (UNOBSERVABLE + cap_violation + clean-day negative), reservation receipt on reset/stop with previous counters, syntax of all three modules, static wiring assertions (old bug line absent).

## Runtime proof (step 10 — behavior actually changed)
RUNTIME-PROBE.txt: two real production receipts after promotion (traces paid-primary-1787110217124, paid-secondary-1787110224190): before 29.985215 → after 29.985194 ≥ 0; second: 29.985194 → 29.985173 ≥ 0. **First non-negative budget_after receipts in the repo's history** (previous 82: all negative).
G10/G11 production receipt pending the next real window event (re-arm of the primary reservation) — logic unit-proven; the 02:32Z window-expired stop predates this patch.

## Rollback
`git checkout -- _ops/cortex/model_router.py` (restores tracked state incl. owner's pre-existing edits — see honesty note) + restore the two snapshots from this dir. Receipts already written remain valid (schema unchanged).

## Non-TCB · reversible · no external authority · no scheduler · no secrets.
