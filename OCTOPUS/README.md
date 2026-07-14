# OCTOPUS — Multi-Agent Organism Dashboard & 3D Architecture Maps

> **Project:** Octopus (اختاپوس) — a self-improving, governed multi-agent organism.
> **Location:** `F:/backup/OCTOPUS/`
> **Last updated:** 2026-07-12 (Wave 5 hardening)

---

## What This Is

OCTOPUS is the **visualization layer** of the organism. It consists of:

1. **Admin Telegram Dashboard** (`admin-telegram/`) — 13-panel operational control surface.
2. **10 Cockpit Worlds** (`worlds/`) — thematic visualization lenses over the system.
3. **3D Architecture Maps** — geometric / holographic views of the multi-agent topology.
4. **Self-Contained Preview** (`preview.html`) — a ~1MB standalone snapshot for sharing.

No installation required; everything is static HTML/JS. Three.js loads from CDN, so an internet connection is needed for the 3D views.

---

## Quick Start

### Operational Dashboard (Primary)
Open **`admin-telegram/index.html`** in any modern browser:
- 13 panels: Vitals, Queue, Health, Neural, Wallet, Mining, Crypto, Research, Git, Tasks, Ideas, Projects, Telegram Control.
- Data refreshes by running `F:/backup/nervous-system/refresh-live-data.bat`.
- All panels have defensive fallbacks; empty sources show "داده یافت نشد" instead of blank.

### Cockpit Worlds
Open **`worlds/index.html`** (the hub) and navigate to any world:

| World | File | Theme | Data Source |
|---|---|---|---|
| 01 Cockpit | `01-cockpit/index.html` | Command center — badges, vitals, queue | `octo-data.js` + `live-data.js` |
| 02 Ontology | `02-ontology/index.html` | Knowledge graph — vault wiki-links | `graph-data.js` (108KB) |
| 03 Money | `03-money/index.html` | Wallet, mining, crypto summaries | `wallet-data.js`, `mining-data.js`, `crypto-data.js` |
| 04 Twin | `04-twin/index.html` | Audit trail — events, traces, ledger | `audit-data.js` |
| 05 Genome | `05-genome/index.html` | Genome system visualization | `ops-data.js`, organism state |
| 06 Time | `06-time/index.html` | Chronos / rhythm / circadian | `neural-data.js` |
| 07 Decision | `07-decision/index.html` | Task queue, ideas backlog | `task-data.js`, `ideas-data.js` |
| 08 Risk | `08-risk/index.html` | Risk indicators, health composite | `health-data.js`, `watchdog-data.js` |
| 09 Growth | `09-growth/index.html` | Fitness, replication, evolution | `ops-data.js`, fitness data |
| 10 Habit | `10-habit/index.html` | Habits, routines, checklists | `task-data.js` (filtered) |
| **Hub** | `index.html` | Navigation + system overview | Aggregated badges |

### 3D Architecture Maps
Open **`index.html`** at the OCTOPUS root for the original 5 holographic views:

| # | File | View | Interaction |
|---|---|---|---|
| 1 | `01-topology.html` | Topology: core + 6 black boxes + tentacles | drag/scroll · hover → tentacle glow |
| 2 | `02-blackbox-cross-section.html` | Internal cross-section of a black box | slice slider · lil-gui |
| 3 | `03-hexagonal-swarm.html` | Hexagonal swarm arrangement | auto-rotate · hover → label |
| 4 | `04-data-flow-river.html` | Data flow river to Telegram storage | fly-through button |
| 5 | `05-isometric-dashboard.html` | Isometric control center | limited rotation · hover → details |

**6 Agent color map:** 🔵 scanner · 🔴 compressor · 🟢 encryptor · 🟣 uploader · ⚪ scheduler · 🟠 verifier

**Libraries:** three@0.128.0 + OrbitControls + CSS2DRenderer + lil-gui (all from jsDelivr CDN).

---

## Data Backbone

All dashboards and worlds consume JavaScript data files produced by the **nervous system** (`F:/backup/nervous-system/`):

```
nervous-system/
├── refresh-live-data.bat      ← run this to refresh all data
├── EXTRACTOR-RUNBOOK.md       ← how extractors work
├── TROUBLESHOOTING.md         ← debug guide
├── live-data.js               ← 4D system state
├── ops-data.js                ← organism state
├── health-data.js             ← composite health score
├── queue-data.js              ← approval queue
├── neural-data.js             ← neural telemetry
├── watchdog-data.js           ← alerts & liveness
├── crypto-data.js             ← market signals
├── mining-data.js             ← fleet monitor
├── wallet-data.js             ← eToro governance
├── research-data.js           ← scout digests
├── git-data.js                ← repo status
├── task-data.js               ← obsidian tasks (677KB — largest)
├── ideas-data.js              ← backlog (83KB)
├── project-data.js            ← project index
├── telegram-data.js           ← control channel
├── graph-data.js              ← vault graph (108KB)
└── audit-data.js              ← audit trail
```

**To refresh data:**
```cmd
F:\backup\nervous-system\refresh-live-data.bat
```

Then reload the dashboard (`Ctrl+F5`).

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Source Systems                         │
│  ├── _ops/          (organism state)    │
│  ├── 4d_system/     (SOG / daemon)      │
│  └── F:/backup/     (vault markdown)    │
└─────────────────┬───────────────────────┘
                  │ 17 extractors (.py)
                  ▼
┌─────────────────────────────────────────┐
│  Nervous System (*.js)                  │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Admin   │ │ Worlds  │ │ 3D Maps  │
│ Telegram│ │ 01-10   │ │ 01-05    │
│ Dashboard│ │ + Hub   │ │          │
└─────────┘ └─────────┘ └──────────┘
```

---

## Safety & Governance

- **Read-only by default:** All extractors and dashboards are read-only. No code execution, no mutations.
- **Shadow mode:** Panels labeled "SHADOW MODE" are advisory only.
- **Owner verdict required:** Any action button (approve, reject) shows "نیاز به تأیید صاحب" and logs the intent without executing.
- **No secrets in output:** Extractors are content-free; no API keys, no PII, no Project-F identity in `.js` files.

---

## File Sizes & Performance

| Artifact | Size | Notes |
|---|---|---|
| `admin-telegram/index.html` | ~37KB | Main dashboard shell |
| `preview.html` | ~1MB | Self-contained; embeds all data inline |
| `worlds/octo-data.js` | ~15KB | Shared world data |
| `task-data.js` | 677KB | Largest payload; summary mode recommended |
| `graph-data.js` | 108KB | Only needed by 02-ontology |
| `ideas-data.js` | 83KB | Backlog with full scoring |

**Recommendation:** Use `admin-telegram/index.html` for daily operations. Use `preview.html` only for offline snapshots.

---

## Development

### Adding a new panel to the admin dashboard
1. Create `extract_MYTHING.py` in `nervous-system/`.
2. Add it to `refresh-live-data.bat`.
3. Add `<script src="../../nervous-system/mything-data.js"></script>` to `admin-telegram/index.html`.
4. Add destructuring: `const X = window.MYTHING_DATA || {};`
5. Add render block with defensive fallback.
6. Document in `EXTRACTOR-RUNBOOK.md` and `TROUBLESHOOTING.md`.

### Adding a new world
1. Create `worlds/XX-name/index.html`.
2. Load `../octo-data.js` and relevant `../../nervous-system/*.js` files.
3. Add navigation link in `worlds/index.html`.
4. Update this README.

---

## Troubleshooting

See **`F:/backup/nervous-system/TROUBLESHOOTING.md`** for detailed diagnostics:
- Panel shows empty
- Extractor fails with file not found
- JS variable not defined
- preview.html too large
- Dashboard loads slowly

---

## License & Governance

This is a private organism dashboard. All external actions (publish, send, spend, create-account, apply-code) are hard-gated behind explicit human verdict. See `_ops/GOALS-OCTOPUS.md` and `_ops/ORGANISM-SPEC.md` for organism governance.
