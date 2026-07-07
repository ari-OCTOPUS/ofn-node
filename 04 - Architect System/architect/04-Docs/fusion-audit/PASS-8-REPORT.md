---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 8 — Refactor Plan (plan only)

Role: convert AUDIT.md findings into a ranked, one-item-per-fix refactor plan. This pass produces
**no code**. The full plan with effort, verification, sequencing, and approval flags is in
`REFACTOR_PLAN.md` (same folder).

## Method
- One plan item per finding (or per tightly-coupled cluster).
- Ranked by **risk-reduction per hour**: severity × reachability ÷ effort.
- Effort: S (≤1h) / M (≤4h) / L (>4h).
- Any item touching **IGK kernel, HITL gate, kill-switch, or the audit/Anchor Ledger** is flagged
  `HUMAN-APPROVAL-REQUIRED` — these are the load-bearing safety surfaces and must not be changed
  without the owner in the loop.
- Only the **TOP 5** are approved for the next work session; everything else is backlog until a
  re-audit.

## Summary of the ranking outcome (detail in REFACTOR_PLAN.md)
The top of the list is dominated by **silent-failure and false-assurance** fixes, because they buy
the most safety per hour:

1. **R-01** — Make IGK failure fail-CLOSED, not fail-open (P1-01/P4-02). *HUMAN-APPROVAL-REQUIRED.*
2. **R-02** — Route human verdicts through the signed kernel audit / sign the main log
   (P2-01/P2-02/P2-03). *HUMAN-APPROVAL-REQUIRED.*
3. **R-03** — Wire the judge panel to use (or explicitly retire) its LLM output (P4-01/P6-07).
4. **R-04** — Remove false-assurance controls: enforce `MAX_STEPS`, and either implement or delete
   the `external_write` HITL requirement and the dead `Supervisor.review` (P4-03/P2-05/P4-04).
5. **R-05** — Add a timeout/watchdog to kernel IPC (P6-01). *HUMAN-APPROVAL-REQUIRED (touches
   kernel client + kill-switch latency).*

Backlog (ranked): grounding rewire/enable path (R-06), single canonical held-out + audit source
(R-07/R-08), unify the two kill-switch paths (R-09), config-as-immutable-settings (R-10), typed
interfaces (R-11), plus the low-severity hygiene items (R-12..R-16).

See `REFACTOR_PLAN.md` for the full table, verification steps, and dependencies.
