---
title: Wave 5 Hardening Plan
status: in-progress
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, wave-5, hardening, control-readiness, ops]
backlinks:
  - "[[OCTOPUS-CHANNEL-REGISTRY]]"
  - "[[OCTOPUS-EXTRACTOR-REGISTRY]]"
  - "[[ADMIN-TELEGRAM-DASHBOARD-MAP]]"
  - "[[OCTOPUS-KNOWN-RISKS]]"
---

# Wave 5 Hardening Plan

> Convert the system from "feature-complete demo" into "stable, observable, documented, and control-ready operational surface".

## Objectives

| # | Objective | Status | Agent |
|---|-----------|--------|-------|
| 1 | Verify all 17 extractor schemas match UI expectations | ✅ Done | A. Verification |
| 2 | Identify and fix silent failure points | ✅ Done | A. Verification |
| 3 | Create lightweight task summary (677KB → 1.5KB) | ✅ Done | E. Data Weight |
| 4 | Add defensive fallback rendering in admin UI | ✅ Done | A. Verification |
| 5 | Add explicit MODE LABELS to all 13 panels | ✅ Done | D. Control-Readiness |
| 6 | Add SYSTEM MODE banner with timestamp + channel count | ✅ Done | D. Control-Readiness |
| 7 | Add safe action placeholders (propose-only) | ✅ Done | D. Control-Readiness |
| 8 | Update refresh-live-data.bat comments + ordering | ✅ Done | F. Docs |
| 9 | Create EXTRACTOR-RUNBOOK.md | ✅ Done | F. Docs |
| 10 | Create TROUBLESHOOTING.md | ✅ Done | F. Docs |
| 11 | Create CHANNEL REGISTRY note | ✅ Done | B. Obsidian Steward |
| 12 | Create EXTRACTOR REGISTRY note | ✅ Done | B. Obsidian Steward |
| 13 | Create ADMIN TELEGRAM DASHBOARD MAP note | 🔄 Next | B. Obsidian Steward |
| 14 | Create KNOWN RISKS note | 🔄 Next | B. Obsidian Steward |
| 15 | Wire task-summary into cockpit + hub | ✅ Done | C. Cockpit Propagation |
| 16 | Update hub navigation badges | 🔄 Pending | C. Cockpit Propagation |

## Control-Readiness Assessment

### Current System Mode: SHADOW / PROPOSE-ONLY

- **No automatic execution**: All action buttons are placeholders.
- **Owner verdict required**: Queue approvals, wallet trades, mining commands all require human confirmation.
- **Telegram stub**: `approval_channel.py` uses `NotWiredStub` → always returns no-approval → gates fail-closed.
- **Budget gate**: Halt flag respected; no spend without explicit approval.

### Panel Modes

| Panel | Mode | Notes |
|-------|------|-------|
| Vitals | READ-ONLY | Live organism state |
| Queue | OWNER VERDICT REQUIRED | Buttons propose only; no execution |
| Health | READ-ONLY | Composite score |
| Neural | READ-ONLY | Rhythm + circadian |
| Wallet | SHADOW MODE | Advisory only; no trades |
| Mining | SHADOW MODE | Advisory only; no commands sent |
| Crypto | SHADOW MODE | Alert-only; EdgeClassifier unwired |
| Research | READ-ONLY | Pipeline digest |
| Git | READ-ONLY | Status display |
| Tasks | READ-ONLY | Counts + next action |
| Ideas | READ-ONLY | Backlog view |
| Projects | READ-ONLY | Index cards |
| Telegram | NOT YET WIRED | Stub mode; no live bot |

## Open Risks

See `[[OCTOPUS-KNOWN-RISKS]]` for full risk register.

Top 5:
1. **task-data.js size** (678KB) — mitigated by summary + lazy load.
2. **preview.html size** (~1MB) — mitigated by using `index.html` for daily use.
3. **Telegram stub mode** — bot not wired; approval channel returns no-approval.
4. **Empty registries** — Portfolio Registry and coin_hunter_cache may be empty.
5. **Stale LunarCrush data** — last update June 2026; crypto signals flagged as stale.

## Next Steps (Post-Wave 5)

1. Wire TelegramApprovalChannel (human-gated, creds from env).
2. Implement batch-approve safety limits (max N items per batch).
3. Add WebSocket or polling for real-time dashboard updates.
4. Compress/split task-data.js further (paginated API instead of monolithic JS).
5. Add automated schema drift tests (CI check that extractors match UI destructuring).
