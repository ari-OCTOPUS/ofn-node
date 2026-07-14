---
title: OCTOPUS Known Risks
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, risks, wave-5, ops, security]
backlinks:
  - "[[WAVE-5-HARDENING-PLAN]]"
  - "[[OCTOPUS-CHANNEL-REGISTRY]]"
  - "[[ADMIN-TELEGRAM-DASHBOARD-MAP]]"
---

# OCTOPUS Known Risks

> Living risk register for the OCTOPUS ecosystem. Updated during Wave 5 hardening.

## Risk Matrix

| ID | Risk | Likelihood | Impact | Status | Mitigation |
|----|------|------------|--------|--------|------------|
| R-01 | `task-data.js` size (678KB) slows dashboard load | High | Medium | ✅ **Mitigated** | `task-summary-data.js` (~1.5KB) loaded by default; full data lazy-loaded on demand |
| R-02 | `preview.html` size (~1MB) unsuitable for daily use | High | Low | ✅ **Mitigated** | `index.html` loads external JS (~30KB total); `preview.html` is offline/distribution only |
| R-03 | Telegram bot in stub mode → no real approvals | High | High | ⚠️ **Accepted** | Fail-closed design: `NotWiredStub` returns no-approval; gates stay closed until human-gated wiring |
| R-04 | Empty Portfolio Registry → crypto blockers fire | Medium | Low | ⚠️ **Accepted** | Registry empty is a valid state; UI shows "خالی" and composite score penalizes -30 |
| R-05 | Stale LunarCrush data (June 2026) | High | Low | ⚠️ **Accepted** | Stale flag shown in UI; crypto panel marked SHADOW MODE; no trades executed |
| R-06 | Empty coin_hunter_cache → mining readiness drops | Medium | Low | ⚠️ **Accepted** | Readiness score accounts for missing cache (-15 if no candidates); fleet remains safe |
| R-07 | Schema drift between extractors and UI | Low | High | ✅ **Mitigated** | Wave 5 verification completed: all 17 extractors match UI destructuring |
| R-08 | Silent failures (missing file → blank panel) | Medium | Medium | ✅ **Mitigated** | Every panel now has explicit fallback: "داده یافت نشد" + offline chip |
| R-09 | Git panel JS syntax error (unescaped quotes) | Low | Low | ✅ **Fixed** | Wave 5 fixed single-quote escaping in `onclick` handler |
| R-10 | Batch-approve not implemented → queue backlog | Medium | Medium | ⚠️ **Accepted** | `actAll()` shows "batch-approve not implemented" placeholder; individual approval required |
| R-11 | `refresh-live-data.bat` has no error handling | Medium | Low | ✅ **Mitigated** | Wave 6: optional `run_ci.py` step added; non-zero exit on drift |
| R-12 | Ideas payload (84KB) may grow | Medium | Low | 🔄 **Watching** | Consider summary mode for ideas if >200KB |
| R-13 | Untested Telegram commands (Wave 6) | Medium | High | ⚠️ **Accepted** | Commands are read-only / propose-only; execution stubbed; no creds |
| R-14 | Missing credentials for live Telegram | High | High | ⚠️ **Accepted** | Token injection is human-gated; bot defaults to no-op if missing |
| R-15 | Irreversible actions lack rollback automation | Medium | High | 🔄 **Watching** | Audit logger classifies rollbackability; manual rollback required for wallet/mining |
| R-16 | Schema drift after extractor changes | Low | High | ✅ **Mitigated** | Wave 6: `verify_schema.py` + `verify_ui_contract.py` run in CI; non-zero on failure |

## Detailed Notes

### R-01: Task Data Size

**Before Wave 5**: `task-data.js` = 678KB loaded on every dashboard open.
**After Wave 5**:
- Default load: `task-summary-data.js` = 1.5KB
- Full load: `task-data.js` = 678KB (lazy-loaded via button click)
- Cockpit and Hub also switched to summary by default.

### R-03: Telegram Stub Mode

**Root cause**: Bot token is stored in env/secret-store (never hardcoded). The current environment does not have the token configured.
**Impact**: Approval channel always returns `valid=false` → all money gates fail-closed.
**Intentional**: This is the desired behavior for paper-trading / shadow phase.
**Path to live**: Human-gated step where operator provides token at runtime.

### R-05: Stale LunarCrush

**Age**: Data from June 2026 (weeks old at time of writing).
**Impact**: Crypto composite score penalized -15 for stale data.
**Action needed**: Re-run LunarCrush analysis pipeline or refresh API cache.
**Safety**: Crypto panel is SHADOW MODE; no BUY/SELL execution possible regardless of signal quality.

## Control Readiness Checklist

- [x] All panels have mode labels
- [x] System banner shows overall mode + freshness
- [x] Action buttons are propose-only with owner-verdict placeholders
- [x] Fail-closed gates (stub → no approval)
- [x] Budget halt flag wired
- [x] No LLM access to exchange keys
- [x] No automatic trades
- [ ] Telegram bot wired to real creds (post-Wave 6 — human-gated)
- [ ] Batch-approve with safety limits (post-Wave 6 — requires explicit override flag)
- [x] Automated CI schema drift tests (Wave 6 — `run_ci.py` active)
