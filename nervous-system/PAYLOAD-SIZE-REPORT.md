# Payload Size Report — Wave 5 Data Weight / Performance Agent

Generated: 2026-07-12

## Executive Summary

The OCTOPUS dashboard's primary performance bottleneck is `task-data.js` at **677,575 bytes** (~662 KB). This single file represents **63% of all nervous-system JS payload** and is the dominant contributor to `preview.html` reaching ~1 MB.

**Key action taken:** Created `task-summary-data.js` (1,644 bytes) as a lightweight default, achieving a **412× size reduction** for the initial dashboard load. Full task data is now lazy-loaded on demand via a "جزئیات کامل" button.

---

## Current Payload Inventory

| File | Size (bytes) | Size (human) | Panel | Notes |
|------|-------------:|-------------:|-------|-------|
| `task-data.js` | 677,575 | 662 KB | Task Queue | **LARGEST** — contains 1,422 task records |
| `live-data.js` | 141,553 | 138 KB | Vitals | Large but necessary for real-time data |
| `graph-data.js` | 107,829 | 105 KB | Ontology | Graph structure — acceptable |
| `ideas-data.js` | 83,534 | 82 KB | Ideas Backlog | 94 ideas with full metadata |
| `watchdog-data.js` | 15,288 | 15 KB | Audit | Acceptable |
| `audit-data.js` | 10,951 | 11 KB | Audit | Acceptable |
| `mining-data.js` | 7,403 | 7.2 KB | Mining | Acceptable |
| `git-data.js` | 4,872 | 4.8 KB | Git Status | Acceptable |
| `project-data.js` | 4,410 | 4.3 KB | Project Index | Acceptable |
| `crypto-data.js` | 4,066 | 4.0 KB | Crypto | Acceptable |
| `research-data.js` | 3,943 | 3.8 KB | Research | Acceptable |
| `telegram-data.js` | 1,964 | 1.9 KB | Telegram Control | Acceptable |
| `neural-data.js` | 1,563 | 1.5 KB | Neural | Acceptable |
| `wallet-data.js` | 1,557 | 1.5 KB | Wallet | Acceptable |
| `health-data.js` | 1,256 | 1.2 KB | Health | Acceptable |
| `ops-data.js` | 891 | 0.9 KB | Ops | Acceptable |
| `queue-data.js` | 323 | 0.3 KB | Queue | Acceptable |
| **`task-summary-data.js`** | **1,644** | **1.6 KB** | Task Queue | **NEW** — replaces task-data.js for default load |
| **TOTAL (all .js)** | **1,070,486** | **1.02 MB** | — | — |
| **TOTAL (summary default)** | **394,555** | **385 KB** | — | **63% reduction** |

---

## Optimization Applied: Task Data

### Before
- `admin-telegram/index.html` loaded `task-data.js` (677 KB) unconditionally on every page load.
- The dashboard UI only uses `TK.summary` (counts, by_priority, next_action) for the initial render.
- The full `open_tasks` array (1,377 items) and `done_tasks` array (45 items) were transferred but only displayed on explicit user action.

### After
1. **New extractor:** `extract_task_summary.py` — consumes `task-data.js` and emits `task-summary-data.js`.
2. **Default load:** `index.html` now loads `task-summary-data.js` (1.6 KB).
3. **Lazy load:** A "📂 جزئیات کامل (۱,۳۷۷ کار)" button in the Task Queue panel injects a `<script>` tag for `task-data.js` only when clicked.
4. **Backward compatible:** `TK = window.TASK_SUMMARY_DATA || window.TASK_DATA` — if both are loaded (e.g., preview.html), full data takes precedence.
5. **Batch integration:** `refresh-live-data.bat` now runs `extract_task_summary.py` immediately after `extract_obsidian_tasks.py`.

### Impact
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Initial JS payload | 1,070 KB | 394 KB | **−63%** |
| Task-specific payload | 677 KB | 1.6 KB | **−99.8%** |
| Time-to-interactive (est.) | baseline | ~2× faster | Significant on slow connections |

---

## Recommendations

### 1. ideas-data.js — Medium Priority
- **Current size:** 83 KB (94 ideas with full metadata + snippets)
- **Issue:** Not critical for dashboard load, but contributes to preview.html bloat.
- **Recommendation:** Create `ideas-summary-data.js` (~2 KB) with counts, top-tier breakdown, and ready-to-build count. Lazy-load full `ideas-data.js` only when the Ideas panel is expanded. The Ideas panel currently renders only the top 5 ideas inline, so a summary is sufficient for the collapsed/default view.
- **Effort:** Low — pattern identical to task-summary extraction.

### 2. preview.html — High Priority
- **Current size:** ~1 MB (inlines all data)
- **Root cause:** Inlines the full `window.TASK_DATA` object (677 KB) directly into the HTML.
- **Recommendation:** Generate a `preview-slim.html` that:
  - Inlines `task-summary-data.js` instead of `task-data.js` (saves ~676 KB).
  - Keeps all other data inlined (the remaining ~324 KB is acceptable for an offline preview).
  - This would reduce preview.html from **1 MB to ~350 KB**.
- **Effort:** Low — change the generator script to emit `TASK_SUMMARY_DATA` instead of `TASK_DATA`.

### 3. Cockpit Worlds — Medium Priority
The following worlds load the full `task-data.js` and would benefit from switching to `task-summary-data.js`:
- `OCTOPUS/worlds/01-cockpit/index.html` — loads `task-data.js` and passes it to `taskModel()`
- `OCTOPUS/worlds/07-decision/index.html` — loads `task-data.js`
- `OCTOPUS/worlds/index.html` (hub) — loads `task-data.js`
- `OCTOPUS/worlds/octo-data.js` — references `window.TASK_DATA`

**Recommendation:** Agent C (Cockpit Propagation) should evaluate each world's actual task data usage. If only summary-level data is needed, migrate to `task-summary-data.js`. If full task lists are rendered (e.g., a full task board in 07-decision), keep `task-data.js` but consider pagination or virtual scrolling.

### 4. live-data.js — Low Priority
- **Current size:** 141 KB
- **Contains:** Budget, daemon, events, sog identity data.
- **Assessment:** This is genuinely large because it carries historical event rows. Consider adding a `live-summary-data.js` (~3 KB) with only the latest snapshot for very fast initial renders, then lazy-load the full history. However, this is lower priority than task and ideas optimization.

### 5. graph-data.js — Monitor
- **Current size:** 107 KB
- **Used by:** 02-ontology world.
- **Assessment:** Acceptable for a graph visualization payload. The ontology world is a specialized view, not loaded on the main dashboard.

---

## Files Changed / Created

### Created
- `nervous-system/extract_task_summary.py` — summary extractor (4,168 bytes)
- `nervous-system/task-summary-data.js` — emitted summary payload (1,644 bytes)
- `nervous-system/PAYLOAD-SIZE-REPORT.md` — this document

### Modified
- `OCTOPUS/admin-telegram/index.html`
  - Changed `<script src=".../task-data.js">` → `<script src=".../task-summary-data.js">`
  - Updated `TK` binding: `window.TASK_SUMMARY_DATA || window.TASK_DATA`
  - Added lazy-load button "📂 جزئیات کامل" in Task Queue panel
  - Added `renderTaskList()` and `loadFullTasks()` functions
  - Added auto-render for preview.html case where full data is already present
- `nervous-system/refresh-live-data.bat`
  - Added `python extract_task_summary.py` after `extract_obsidian_tasks.py`

### Unchanged (by design)
- `nervous-system/extract_obsidian_tasks.py` — left intact; summary extractor consumes its output
- `nervous-system/task-data.js` — left intact; still generated for lazy-load and other consumers
- `OCTOPUS/admin-telegram/preview.html` — left intact; documented as recommendation only

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Lazy-load fails (network/offline) | Low | Fallback message rendered: "❌ لودِ task-data.js ناموفق بود" |
| task-data.js missing when user clicks "جزئیات کامل" | Low | `onerror` handler shows clear error; summary data still visible |
| Cockpit worlds break if TASK_DATA not loaded | Low | Those worlds still load `task-data.js`; unchanged by this agent |
| preview.html no longer auto-renders task list | None | Auto-render logic explicitly handles `window.TASK_DATA` presence |
| Summary extractor fails if task-data.js corrupt | Low | Writes a minimal fallback JSON so dashboard never breaks |

---

## Next Steps (for other agents)

1. **Agent C (Cockpit Propagation):** Evaluate `01-cockpit`, `07-decision`, and hub `index.html` for task-summary migration.
2. **Agent F (Docs/Runbook):** Document the lazy-load pattern in `EXTRACTOR-RUNBOOK.md` so future extractors can follow the same summary/full split convention.
3. **Future Wave:** Apply the same summary/full split pattern to `ideas-data.js` and potentially `live-data.js`.
