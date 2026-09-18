---
type: scope
status: active
created: 2026-09-05
tags: [octopus, execution, debug, provenance]
---

# R-EXEC-DEBUG-20260905

Owner dispatch: the reviewed NEXT-AGENT-PROMPT in 09-LANES/H-HANDOFF-RECONCILE-20260905/ (manifest-verified 2026-09-04T15:20:03Z). Mission: debug/evidence-repair of COMPLETE-20260904, then continue permitted work toward P10 under OWNER-DELEGATION-OCTOPUS-20260904 as bounded by AUTHORITY-DELTA.md.

Lane: this one only. Vault artifacts (reports/receipts) are written here. The mission run root F:/octo-exec/COMPLETE-20260904 is adopted per its own RESUME CHECKLIST; RUN-STATE.json edits only after ownership is established and only as documented corrections with provenance (never upgrading documentation claims to COMPLETE).

Code/test work happens in isolated worktrees created by this lane under F:/octo-exec (ofn-node clones), never in another lane's checkout. Boards are touched only read-only unless an authorized, in-scope operation with ACTION-MANIFEST + readback + rollback is executed.

Non-negotiables retained: no OCTOPUS_WIRE_*/OFN_WIRE_*/OBSERVATORY/CORTEX_HYPOTHESIS enablement; auto_email closed; blocked gates (secret_rotation, partner_precondition, miner_isolation, D1, D7, OWNER_KEY) stay closed absent real prerequisites; no force-push/history rewrite; no rm -rf; no synthetic data; no owner financial/consent/third-party-credential decisions; no self-elevation.

Exit: LANE-REPORT.md in this lane with evidence paths, failures, limits, rollback.
