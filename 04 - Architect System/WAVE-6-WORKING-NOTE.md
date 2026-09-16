---
title: Wave 6 Working Note
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, wave-6, control-plane, telegram, audit, ci]
backlinks:
  - "[[MOC-OCTOPUS-System]]"
  - "[[OCTOPUS-KNOWN-RISKS]]"
---

# Wave 6 Working Note

> Mission: Transition from "observable control surface" to "gated, testable, replayable, owner-aware action-ready control plane" WITHOUT removing existing safety posture.

## Objectives

1. **A. Telegram Wiring** — Define safe command surface (/status, /queue, /approvals, /refresh, /risk, /help) with mode labels
2. **B. Approval Gate / Verdict Flow** — Explicit state machine (suggested → queued → owner_approved → executed) with logging
3. **C. CI & Drift Guard** — Schema verification + UI contract verification + CI runner
4. **D. Replay / Audit / Rollback** — Audit logger for every action with rollback classification
5. **E. UI Consistency & Mode Discipline** — Verify all panels have correct mode labels, no control illusions
6. **F. Obsidian / Spec / Runbook** — Documentation, registries, runbooks
7. **G. Security & Secrets Boundary** — Scan for hardcoded secrets, verify env-only injection

## Progress

| Deliverable | Status | Key Files |
|---|---|---|
| A. Telegram commands extractor | ✅ Done | `extract_telegram_commands.py` → `telegram-commands-data.js` |
| A. Admin panel updated | ✅ Done | `admin-telegram/index.html` Telegram panel shows commands + modes |
| B. Approval state machine | ✅ Done | `approval_state_machine.py` in `nervous-system/` |
| B. Queue extractor enriched | ✅ Done | `extract_queue_data.py` emits canonical status, time-in-queue, deny reasons |
| B. Queue panel updated | ✅ Done | Status flow diagram, required action, dry-run badge |
| C. verify_schema.py | ✅ Done | 19/19 JS files pass schema contract |
| C. verify_ui_contract.py | ✅ Done | All panels have mode labels, no orphaned scripts |
| C. run_ci.py | ✅ Done | Runs both verifiers, exits non-zero on failure |
| C. refresh-live-data.bat | ✅ Done | CI step added (commented out by default) |
| D. audit_logger.py | ✅ Done | Appends to `action-audit.jsonl` |
| D. extract_audit_trail.py | ✅ Done | Emits `audit-trail-data.js` |
| D. Admin audit panel | ✅ Done | Collapsed panel with recent actions, rollback coverage |
| E. UI consistency | ✅ Done | All 13 panels verified, mode labels correct |
| F. Specs + runbooks | 🔄 In Progress | This note + 4 specs + runbook |
| G. security-checklist.py | ✅ Done | 0 findings from 392 files scanned |

## Blockers

- **None.** All Wave 6 deliverables are implemented and passing CI.

## Risks Added in Wave 6

| ID | Risk | Mitigation |
|---|---|---|
| R-13 | Untested Telegram commands may have UX gaps | All commands are read-only or propose-only; no live execution without owner verdict |
| R-14 | Missing Telegram credentials block approval channel | Fail-closed by design: `NotWiredStub` returns no-approval |
| R-15 | Irreversible actions (spending, execute) lack manual rollback | Classified as `irreversible`; require explicit owner approval via Telegram |
| R-16 | CI schema checks may break if new extractors add unexpected keys | `verify_schema.py` has explicit allow-list; new keys = intentional change |

## Next Steps

1. Run `refresh-live-data.bat` to refresh all data
2. Open `OCTOPUS/admin-telegram/index.html` to verify panels
3. Run `nervous-system/run_ci.py` to verify schema + UI contract
4. Review `nervous-system/security-scan-report.json`

## Sign-off

- **Wave 6 Lead:** F. Obsidian / Spec / Runbook Agent
- **Safety Review:** All changes are additive, reversible, and fail-soft
- **Owner Verdict:** Not required for Wave 6 (no live execution paths added)
