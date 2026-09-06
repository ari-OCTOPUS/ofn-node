# Token budgets and revenue-state pin

purpose: two ceilings (node + per-run) and a structural split between ready and send.
status: contract + kernel predicate. No send path opened.

## Two ceilings

| ceiling | module | unit | 0 means |
|---|---|---|---|
| node / tenant week | `ofn/kernel/quota.py` `NodeQuota` | billed tokens (visible × orchestration multiplier) | invalid (capacity must be positive) |
| call-count per rung | `ofn/kernel/callbudget.py` `CallBudget` | calls / day | uncapped (free rungs only) |
| per-run token cap | `TaskEnvelope.budget_tokens` (PR #74) + `may_consume_tokens` | tokens / run | **no spend authorized** (request 0 only) |

Both the node quota and the per-run cap must pass. Neither grants `send_authorized`.

## Ready ≠ authorized

`ofn/kernel/revenue_states.py`:

- `campaign_envelope_ready` / `policy_checked` / `quote_drafted` → `authorizes_external_effect` is **False**
- `send_authorized` / `quote_sent` → **refused** (this module does not grant them)
- `next_state_after_ready()` → **refused** (no transition exists)

PR #76 (`campaign_envelope` on `release/p0`) is the draft-artifact lane. It is not imported here; this pin holds on `main` so a merge cannot silently equate the two names.

## Tests

- `tests/test_revenue_states.py`
- PR #74 `tests/test_envelope.py::PerRunTokenCeiling` (per-run cap)
