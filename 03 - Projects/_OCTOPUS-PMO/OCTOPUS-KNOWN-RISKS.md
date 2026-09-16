---
type: risk-register
project: OCTOPUS
status: active
wave: 4
tags: [octopus, risks, register, operational, performance]
created: 2026-07-13
updated: 2026-07-13
---

# OCTOPUS · Known Risks Register

> **What this is:** A living register of all known risks in the OCTOPUS system at the Wave 4 → Wave 5 boundary.
> **Scope:** Data weight, UI behavior, external dependencies, stub modes, and operational gaps.
> **Severity:** 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low
> **Last synced:** 2026-07-13

---

## Risk Summary Matrix

| ID | Risk | Severity | Likelihood | Owner | Wave 5/6 Mitigation | Status |
|---|---|---|---|---|---|---|
| R01 | `task-data.js` 677 KB slows dashboard load | 🟡 Medium | 🔴 High | Agent E | Lazy-load summary by default | ✅ Fixed |
| R02 | `preview.html` ~1 MB is too large for mobile | 🟡 Medium | 🔴 High | Agent E | Slim preview with summary only | ✅ Fixed |
| R03 | Telegram stub mode hides true status | 🟡 Medium | 🟡 Medium | Agent D | Explicit mode label + stub indicator + command registry | ✅ Fixed Wave 6 |
| R04 | Empty crypto/mining registries show no guidance | 🟢 Low | 🟡 Medium | Agent A | Defensive fallback + "empty" message | ✅ Fixed |
| R05 | LunarCrush data frequently stale | 🟡 Medium | 🟡 Medium | Agent A | Stale flag + fallback rendering | ✅ Fixed |
| R06 | Schema drift breaks UI silently | 🟠 High | 🟡 Medium | Agent A/C | `verify_schema.py` + `verify_ui_contract.py` CI gate | ✅ Fixed Wave 6 |
| R07 | Action buttons fail without owner feedback | 🔴 Critical | 🟢 Low | Agent D | Safe placeholders + mode labels + propose-only stubs | ✅ Fixed Wave 6 |
| R08 | `refresh-live-data.bat` order not documented | 🟢 Low | 🟡 Medium | Agent F | Inline comments + runbook | ✅ Fixed |
| R09 | New extractors added without documentation | 🟡 Medium | 🟡 Medium | Agent F | EXTRACTOR-RUNBOOK.md + registry sync | ✅ Fixed |
| R10 | Missing `TASK_SUMMARY_DATA` default load | 🟡 Medium | 🟡 Medium | Agent E | Switch index.html to summary | ✅ Fixed |
| R11 | `ideas-data.js` 83 KB adds to payload | 🟢 Low | 🟡 Medium | Agent E | Consider summary mode | 🟢 Accepted |
| R12 | Queue panel empty without explanation | 🟡 Medium | 🟢 Low | Agent A | "صف خالی است" message + status flow diagram | ✅ Fixed Wave 6 |
| R13 | Health panel null-reference crash (fixed) | 🟢 Low | 🟢 Low | Agent A | Fixed Wave 4 | ✅ Fixed |
| R14 | Wallet gate shows "unknown" when cache missing | 🟢 Low | 🟡 Medium | Agent A | Defensive fallback chip | ✅ Fixed |
| R15 | Neural protective mode flag may be stale | 🟢 Low | 🟢 Low | — | Documented, acceptable | 🟢 Accepted |
| R16 | Graph-data.js 107 KB loads on every hub open | 🟢 Low | 🟡 Medium | — | Consider lazy-load or caching | 🟢 Accepted |
| R17 | Git status timeout 30s per repo | 🟢 Low | 🟢 Low | — | Documented, acceptable | 🟢 Accepted |
| R18 | Extractor runtime not monitored | 🟡 Medium | 🟡 Medium | Agent F | Add timing logs to batch | 🟡 Open |
| R19 | No automated test for extractors | 🟠 High | 🟡 Medium | — | Future wave: pytest coverage | 🟠 Open |
| R20 | Vault scan (extract_obsidian_tasks.py) takes ~3s | 🟢 Low | 🔴 High | — | Expected; full vault scan | 🟢 Accepted |
| R21 | Untested Telegram commands may have parsing edge cases | 🟡 Medium | 🟡 Medium | Agent G | All commands read-only/propose-only by default; command registry extracted | ✅ Mitigated Wave 6 |
| R22 | Missing credentials for live Telegram bot | 🟡 Medium | 🟡 Medium | Agent G | Stub mode active; env-only injection; masked chat ID in UI | ✅ Mitigated Wave 6 |
| R23 | Irreversible actions lack rollback automation | 🟠 High | 🟢 Low | Agent D | Rollback classification table + audit trail + manual procedures | ✅ Mitigated Wave 6 |
| R24 | Batch approve not implemented (intentional gap) | 🟢 Low | 🔴 High | Agent G | Explicitly blocked with warnings; actAll() shows "not implemented" | ✅ Fixed Wave 6 |
| R25 | Security scan may miss novel secret patterns | 🟡 Medium | 🟡 Medium | Agent G | Regex-based; manual review required; 0 findings on current scan | 🟡 Ongoing |
| R26 | CI gate not yet running automatically | 🟢 Low | 🟡 Medium | Agent C | Added to refresh-live-data.bat as optional commented step | ✅ Mitigated Wave 6 |
| **R27** | **Audit trail may grow unbounded** | 🟡 Medium | 🟡 Medium | Agent D | Append-only JSONL; external rotation needed | 🟡 **New Wave 6** |
| **R28** | **Approval log may grow unbounded** | 🟡 Medium | 🟡 Medium | Agent B | Append-only JSONL; external rotation needed | 🟡 **New Wave 6** |
| **R29** | **Dry-run default may mask live path bugs** | 🟡 Medium | 🟢 Low | Agent D | All new paths start dry_run; explicit graduation required | 🟡 **New Wave 6** |

---

## Detailed Risk Cards

### R01 · task-data.js Size (677 KB)

**Description:** `task-data.js` is the largest payload by far (63% of total JS load). On slow connections, this blocks dashboard interactivity.

**Impact:** Dashboard load time >2s on 3G; poor mobile experience.

**Current mitigation:** `extract_task_summary.py` already exists and emits `task-summary-data.js` (~0.5 KB).

**Wave 5 mitigation:**
- Modify `index.html` to load `task-summary-data.js` by default
- Add "جزئیات کامل" button that lazy-loads `task-data.js` on demand
- Update `preview.html` generation to use summary only

**Risk level after mitigation:** 🟢 Low

---

### R02 · preview.html Size (~1 MB)

**Description:** `preview.html` bundles all data inline for offline use. At ~1 MB, it's large for mobile sharing.

**Impact:** Slow to open on messenger in-app browsers; may exceed some message size limits.

**Current mitigation:** Self-contained; works offline.

**Wave 5 mitigation:**
- Generate `preview-slim.html` using `task-summary-data.js` + `ideas-summary-data.js`
- Keep `preview.html` as the full offline archive
- Document size in README

**Risk level after mitigation:** 🟢 Low

---

### R03 · Telegram Stub Mode

**Description:** When `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is missing, the system runs in "stub mode" (live=false). This is not obvious to the user.

**Impact:** User may think Telegram integration is broken when it's simply not configured.

**Current mitigation:** `extract_telegram_control.py` reports `live=false` and mode="unknown".

**Wave 5 mitigation:**
- Add `NOT YET WIRED` or `STUB MODE` label to Telegram Control panel
- Show required env vars in detail box
- Surface "کانال تلگرام غیرفعال (stub)" in health summary

**Risk level after mitigation:** 🟢 Low

---

### R05 · LunarCrush Data Stale

**Description:** LunarCrush cache is often missing or outdated. `extract_crypto_data.py` shows a stale flag but the UI may not make this obvious enough.

**Impact:** Crypto signals may be based on old data; user makes decisions on stale information.

**Current mitigation:** Stale flag with emoji + color (`🟡 stale` / `🔴 stale`).

**Wave 5 mitigation:**
- Make stale indicator more prominent in crypto panel
- Add "last updated" timestamp
- Consider fallback to alternative data source

**Risk level after mitigation:** 🟢 Low

---

### R06 · Schema Drift

**Description:** If an extractor changes its output schema (e.g., renames a field), the UI may fail silently because JS destructuring just produces `undefined`.

**Impact:** Blank panels, NaN in metrics, or undefined crashes.

**Current mitigation:** None automated. Human review of extractor changes.

**Wave 5 mitigation:**
- Agent A performs manual schema drift check
- Add defensive fallback in every panel (if var missing → show error chip)
- Consider JSON Schema validation in future wave

**Risk level after mitigation:** 🟢 Low

---

### R07 · Action Button Failure Without Feedback

**Description:** Approve/reject buttons in Queue panel call `actOne()` / `actAll()` which only log to a text element. If the user misses the log, they think nothing happened.

**Impact:** User confusion; potential for repeated clicks.

**Current mitigation:** Log message: "ACT: approve ID (propose-only → need owner verdict)"

**Wave 5 mitigation:**
- Add modal or prominent banner: "نیاز به تأیید صاحب"
- Disable button after first click with visual feedback
- Document in HTML comments what the action would do if wired

**Risk level after mitigation:** 🟢 Low

---

### R19 · No Automated Tests for Extractors

**Description:** None of the 17 extractors have unit tests. A change to source data format or vault structure could break an extractor without anyone knowing.

**Impact:** Silent data pipeline failure; blank panels in production.

**Current mitigation:** Manual run of `refresh-live-data.bat` after changes.

**Wave 5 mitigation:** Out of scope for Wave 5. Recommended for Wave 6:
- Add `tests/test_extractors.py` with sample data fixtures
- Run in CI (or pre-commit hook)

**Risk level:** 🟠 High (accepted risk for now)

---

## Risk by Channel

| Channel | Risks |
|---|---|
| CH-01 (Research) | Stale scouts, synthesis lag |
| CH-02 (Git) | Timeout on large repos, file cap |
| CH-03 (Graph) | 107 KB payload |
| CH-05 (Tasks) | R01, R20 |
| CH-07 (Health) | R13 (fixed) |
| CH-08 (Crypto/Wallet) | R04, R05, R14 |
| CH-09 (Mining) | R04 |
| CH-12 (Ideas) | R11 |
| CH-15 (Telegram) | R03 |
| CH-16 (Neural) | R15 |
| Foundation | R06, R08, R18, R19 |

---

## Risk by Panel

| Panel | Risks |
|---|---|
| Vitals | R06 |
| Queue | R07, R12 |
| Health | R13 (fixed) |
| Neural | R15 |
| Wallet | R14 |
| Mining | R04 |
| Crypto | R04, R05 |
| Research | — |
| Git | — |
| Tasks | R01, R10, R20 |
| Ideas | R11 |
| Projects | — |
| Telegram | R03 |

---

## Backlinks

- [[OCTOPUS-WAVE5-HARDENING-PLAN]] — mitigations being implemented
- [[OCTOPUS-CHANNEL-REGISTRY]] — channels where risks originate
- [[OCTOPUS-EXTRACTOR-REGISTRY]] — extractors where risks originate
- [[OCTOPUS-ADMIN-DASHBOARD-MAP]] — panels affected by risks
