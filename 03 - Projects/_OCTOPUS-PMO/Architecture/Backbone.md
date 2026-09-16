---
type: architecture
status: implemented
wave: 1-2
tags: [octopus, backbone, data, architecture, js]
created: 2026-07-12
updated: 2026-07-12
---

# Architecture · Backbone

> **What:** The shared JavaScript data layer that feeds all OCTOPUS visualizations.
> **Where:** `OCTOPUS/worlds/` + `nervous-system/`
> **How:** Plain JS files exporting `window.*_DATA` objects.

---

## Files

### Core Backbone (OCTOPUS/worlds/)

| File | Size | Role |
|---|---|---|
| `octo-data.js` | ~11.5 KB | Master data object — merged view of all channels |
| `shared-ui.js` | ~4.9 KB | Shared rendering utilities, color scales, formatters |
| `octo-core.js` | ~3.7 KB | Core 3D engine helpers (Three.js wrapper) |
| `octo-info.js` | ~11.5 KB | Info panel content + help text |

### Nervous System Data (nervous-system/)

| File | Source Extractor | Consumers |
|---|---|---|
| `live-data.js` | `extract_live_data.py` | Admin UI, Cockpit |
| `ops-data.js` | `extract_ops_data.py` | Admin UI, Cockpit |
| `health-data.js` | `extract_health_score.py` | Admin UI, Risk World |
| `queue-data.js` | `extract_queue_data.py` | Admin UI, Cockpit |
| `neural-data.js` | `extract_neural_data.py` | Admin UI, Time World |
| `watchdog-data.js` | `extract_watchdog_data.py` | Admin UI, Risk World |
| `audit-data.js` | `extract_audit_data.py` | Twin World |
| `graph-data.js` | `extract_graph.py` | Dream, Topology |

---

## Data Contract

Every `*_DATA` object follows:

```typescript
interface OctoDataFile {
  generated: string;  // ISO timestamp "2026-07-12T...Z"
  // ... channel-specific fields
  source?: {
    // provenance: which files/modules produced this
  };
}
```

---

## octo-data.js Structure

```javascript
window.OCTO_DATA = {
  meta: { generated: "...", version: "1.0" },
  organism: { /* _ops state summary */ },
  brain: { /* 4d_system daemon summary */ },
  health: { /* CH-07 composite */ },
  neural: { /* CH-16 vitals */ },
  queue: { /* CH-14 HITL badge */ },
  alerts: { /* CH-17 active alerts */ },
  audit: { /* CH-11 trace summary */ },
  wiring: { /* flag matrix */ }
};
```

This is the **authoritative merged view** for worlds that need cross-cutting data.

---

## shared-ui.js Utilities

| Function | Purpose |
|---|---|
| `formatNumber(n, digits)` | Farsi-aware number formatting |
| `statusColor(score)` | Map 0-100 → hex color |
| `timeAgo(iso)` | Relative time string |
| `badge(count, max)` | DOM badge element |
| `panel(title, items)` | Generic panel renderer |

---

## Loading Order

`admin-telegram/index.html`:
```html
<script src="../../nervous-system/live-data.js"></script>
<script src="../../nervous-system/ops-data.js"></script>
<script src="../../nervous-system/health-data.js"></script>
<script src="../../nervous-system/queue-data.js"></script>
<script src="../../nervous-system/neural-data.js"></script>
<script src="../../nervous-system/watchdog-data.js"></script>
<script src="../worlds/octo-data.js"></script>
```

All globals. No module bundler. Works from `file://` without a build step.

---

## Worlds Map

| World | Path | Primary Data | Channel |
|---|---|---|---|
| Cockpit | `worlds/01-cockpit/` | `live-data.js` + `queue-data.js` | — |
| Ontology | `worlds/02-ontology/` | `graph-data.js` | — |
| Money | `worlds/03-money/` | `ops-data.js` | — |
| Twin | `worlds/04-twin/` | `audit-data.js` | CH-11 |
| Galaxy | `worlds/05-galaxy/` | `live-data.js` (frontier) | — |
| Time | `worlds/06-time/` | `neural-data.js` | CH-16 |
| Decision | `worlds/07-decision/` | `queue-data.js` | CH-14 |
| Risk | `worlds/08-risk/` | `health-data.js` + `watchdog-data.js` | CH-07, CH-17 |
| Compass | `worlds/09-compass/` | `live-data.js` (identity) | — |
| Habit | `worlds/10-habit/` | `ops-data.js` (wires) | — |

---

## Related

- [[Dataflow]] — extractor → data file pipeline
- [[Admin-UI]] — primary consumer
- [[Wave-1]] — backbone foundation
- [[Wave-2]] — channel data additions
