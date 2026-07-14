---
type: plan
project: OCTOPUS
status: active
wave: 5
tags: [octopus, wave-5, hardening, stability, observability, control]
created: 2026-07-13
updated: 2026-07-13
---

# OCTOPUS · Wave 5 Hardening Plan

> **Mission:** Convert the system from "feature-complete demo" into "stable, observable, documented, and control-ready operational surface."
> **Status:** 🔄 In Progress
> **Wave:** 5 (final hardening before operational readiness)

---

## Objectives

Wave 5 has six parallel workstreams, each owned by a specialist agent:

| Workstream | Agent | Objective | Status |
|---|---|---|---|
| **A. Verification & Regression** | Verification Agent | Schema drift detection, defensive fallback rendering, task summary extractor, batch ordering | 🔄 Open |
| **B. Obsidian Steward** | Steward Agent (you are here) | Vault documentation, registries, maps, risks, folder structure | 🔄 In Progress |
| **C. Cockpit Propagation** | Propagation Agent | Wire Wave 4 data into 10 worlds incrementally | 🔄 Open |
| **D. Control-Readiness** | Control Agent | Mode labels, system banner, safe action placeholders, owner-verdict gating | 🔄 Open |
| **E. Data Weight / Performance** | Performance Agent | Task summary lazy-load, payload size audit, preview slimming | 🔄 Open |
| **F. Docs / Runbook** | Docs Agent | Batch comments, EXTRACTOR-RUNBOOK.md, TROUBLESHOOTING.md | 🔄 Open |

---

## Current State (Post-Wave-4)

| Metric | Value | Target |
|---|---|---|
| Extractors | 17 | 17 ✅ |
| Channels | 16 | 16 ✅ |
| Admin panels | 13 | 13 ✅ |
| Cockpit worlds | 10 | 10 ✅ |
| Data files | 17 + graph | 17 ✅ |
| Preview self-contained | Yes | Yes ✅ |
| Schema drift detection | None | Automated ❌ |
| Defensive fallback | Partial | Per-panel ❌ |
| Task summary | Exists | Loaded by default ❌ |
| Mode labels | None | All panels ❌ |
| System mode banner | None | Top of admin ❌ |
| Lazy-load details | None | Task + ideas ❌ |
| Runbook | None | Complete ❌ |

---

## Workstream Detail

### A. Verification & Regression

**Goal:** Ensure the UI never silently fails.

- [ ] Read all 17 extractors and verify JS output schemas match `admin-telegram/index.html` expectations
- [ ] Check for schema drift: do `L, O, H, Q, N, W, C, M, WL, R, G, TK, I, P, T` match what UI destructures?
- [ ] Identify silent failure points (missing files → empty panels without error)
- [ ] Add defensive fallback rendering per panel (show "داده یافت نشد" instead of blank)
- [ ] `extract_task_summary.py` already exists; ensure `index.html` loads it by default
- [ ] Check `refresh-live-data.bat` ordering for dependency respect

**Deliverables:**
- Schema drift report
- Defensive fallback patches in `index.html`
- Updated `refresh-live-data.bat` (if order changed)

### B. Obsidian Steward

**Goal:** The vault is the source of truth for system knowledge.

- [x] Create/update vault notes for Wave 4 completion
- [x] Create unified [[OCTOPUS-CHANNEL-REGISTRY]]
- [x] Create [[OCTOPUS-EXTRACTOR-REGISTRY]]
- [ ] Create this WAVE 5 HARDENING PLAN note
- [ ] Create/update [[OCTOPUS-ADMIN-DASHBOARD-MAP]]
- [ ] Create/update [[OCTOPUS-KNOWN-RISKS]]
- [ ] Ensure proper frontmatter, backlinks, status labels

**Deliverables:**
- List of notes created/updated with paths
- Content summary of each note
- Folder structure improvements

### C. Cockpit Propagation

**Goal:** Every world that should show data, shows data.

- [ ] Inspect all 10 cockpit worlds + hub
- [ ] Wire new data where appropriate:
  - `01-cockpit`: task count badge, git status tile, research scout tile ✅ (already wired)
  - `02-ontology`: verify `graph-data.js` loads with 107 KB data
  - `03-money`: wallet/crypto/mining summaries if not present
  - `07-decision`: task queue and ideas backlog tiles
  - `08-risk`: risk indicators from all channels
  - `hub index.html`: update navigation badges with new channel counts
- [ ] Keep changes minimal and consistent with existing styles

**Deliverables:**
- Worlds inspected list
- Changes made per world
- Files modified

### D. Control-Readiness

**Goal:** No action can be taken without explicit mode awareness and owner gating.

- [ ] Add explicit MODE LABELS to each admin panel:
  - `READ-ONLY` — vitals, health, neural, research, git, tasks, ideas, projects
  - `SHADOW MODE` — mining, crypto, wallet (advisory only)
  - `PROPOSE-ONLY` — approve/reject buttons (action proposed, not executed)
  - `NOT YET WIRED` — conceptual features with no backend
  - `OWNER VERDICT REQUIRED` — queue actions
- [ ] Add SYSTEM MODE banner at top of admin showing:
  - Overall system mode (shadow / propose-only / read-only)
  - Owner approval required flag
  - Last refresh timestamp
  - Active channel count / total
- [ ] Add safe action placeholders: buttons show "نیاز به تأیید صاحب" instead of silently failing
- [ ] Document in HTML comments what each action would do if wired

**Deliverables:**
- Mode labels added to panels
- System mode banner implemented
- Action placeholder behavior documented
- Control readiness assessment report

### E. Data Weight / Performance

**Goal:** Dashboard loads fast; large payloads are lazy-loaded.

- [ ] `task-data.js` is 677 KB — too large for dashboard payload
- [ ] `extract_task_summary.py` already emits `task-summary-data.js` (~0.5 KB)
- [ ] Modify `index.html` to load `task-summary-data.js` by default
- [ ] Add expandable "جزئیات کامل" button that lazy-loads `task-data.js`
- [ ] `ideas-data.js` is 83 KB — consider summary mode for preview
- [ ] Document payload sizes and recommendations

**Deliverables:**
- `task-summary-data.js` loaded by default
- Modified `index.html` with lazy-load for task details
- Payload size report with recommendations

### F. Docs / Runbook

**Goal:** A new developer (or future self) can understand, debug, and extend the system.

- [ ] Add comprehensive comments to `refresh-live-data.bat` explaining:
  - What each extractor does
  - Expected output files
  - Approximate runtime
  - Dependencies between extractors
- [ ] Create `EXTRACTOR-RUNBOOK.md` in `F:/backup/nervous-system/` describing:
  - How to add a new extractor
  - How to debug a failing extractor
  - How to run extractors individually
  - Schema conventions (`window.VAR_NAME = ...`)
- [ ] Create `TROUBLESHOOTING.md` for common issues:
  - "panel shows empty"
  - "extractor fails with file not found"
  - "JS variable not defined"
  - "preview.html too large"
- [ ] Update any existing README or docs in `OCTOPUS/` or `_ops/`

**Deliverables:**
- `refresh-live-data.bat` with inline comments
- `EXTRACTOR-RUNBOOK.md`
- `TROUBLESHOOTING.md`
- Updated existing docs

---

## Open Risks (Pre-Mitigation)

| Risk | Impact | Likelihood | Mitigation Owner |
|---|---|---|---|
| Schema drift breaks UI silently | High | Medium | Agent A |
| 677 KB task-data.js slows load | Medium | High | Agent E |
| Action buttons fail without feedback | High | Low | Agent D |
| Telegram stub mode confuses user | Medium | Medium | Agent D |
| New extractor added without docs | Medium | Medium | Agent F |
| Missing fallback → blank panel | Medium | Medium | Agent A |
| Preview.html >1 MB on mobile | Medium | High | Agent E |

---

## Definition of Done

Wave 5 is complete when:

1. All 13 admin panels show a mode label
2. System mode banner is visible at top of admin
3. All panels have defensive fallback (no blank/empty)
4. Task panel loads summary by default; full data lazy-loaded
5. `refresh-live-data.bat` has inline documentation
6. `EXTRACTOR-RUNBOOK.md` and `TROUBLESHOOTING.md` exist
7. Vault notes reflect current state (registries, maps, risks)
8. All 10 worlds inspected; new data wired where appropriate
9. No console errors on admin UI load
10. Preview.html still works offline

---

## Related

- [[Wave-4 · Full Channel Fleet]] — what Wave 5 hardens
- [[OCTOPUS-CHANNEL-REGISTRY]] — channels being hardened
- [[OCTOPUS-EXTRACTOR-REGISTRY]] — extractors being documented
- [[OCTOPUS-KNOWN-RISKS]] — detailed risk register
- [[OCTOPUS-ADMIN-DASHBOARD-MAP]] — panels being hardened
