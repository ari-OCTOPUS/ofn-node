---
type: architecture
status: implemented
wave: 2
tags: [octopus, admin, ui, telegram, architecture]
created: 2026-07-12
updated: 2026-07-12
---

# Architecture · Admin Telegram UI

> **What:** A single-page mobile-first admin dashboard for OCTOPUS.
> **Where:** `OCTOPUS/admin-telegram/index.html`
> **Language:** Farsi (RTL) with English technical terms

---

## Purpose

One screen to rule them all:
- **Vitals** — organism + brain live status
- **Queue** — HITL approval items with actions
- **Health** — composite score with color coding
- **Neural** — circadian + rhythm vitals

All read-only + propose-only. No execution without owner verdict.

---

## Files

| File | Role |
|---|---|
| `OCTOPUS/admin-telegram/index.html` | Main UI (~182 lines) |
| `OCTOPUS/worlds/octo-data.js` | Master merged data |
| `nervous-system/*.js` | Channel-specific data files |

---

## Design System

### Colors
```css
--ink:   #e8eef2   /* primary text */
--cyan:  #22d3ee   /* accent / links */
--green: #34d399   /* ok / healthy */
--red:   #ef4444   /* error / critical */
--gold:  #fcd34d   /* warning */
--purple:#a855f7   /* gradient accent */
```

### Layout
- Mobile-first, max-width 720px
- Safe-area insets for notched phones
- RTL (Farsi) with LTR code blocks

### Components
- **Panel** — bordered card with header
- **Chip** — key-value metric cell
- **Queue Item** — approval card with risk badge + actions
- **Log** — monospace scrollable trace
- **Nav** — pill links to other worlds

---

## Panels

### 1. Vitals (وضعیتِ زنده)
Loaded from `live-data.js` + `ops-data.js`:

| Chip | Source | Threshold |
|---|---|---|
| Identity | `LIVE_DATA.sog.identity_now` | — |
| Budget | `LIVE_DATA.budget.remaining` | > 100 = green |
| Daemon | `LIVE_DATA.daemon.stopped_at` | null = green |
| Events | `LIVE_DATA.events.total_rows` | — |
| Chrono | `OPS_DATA.time.chrono_beat` | — |
| Wires | `OPS_DATA.time.wires_on/total` | all on = green |

### 2. Queue (صفِ تأیید)
Loaded from `queue-data.js`:

- Empty state: "صف خالی است"
- Items: risk badge (R1/R2/R3) + title + meta + approve/reject buttons
- Actions are **propose-only** — log shows "need owner verdict"

### 3. Health (سلامتِ سیستم)
Loaded from `health-data.js`:

- Overall score + label (سالم / هشدار / بحرانی)
- Sub-scores: system, fitness, telemetry

### 4. Neural (شبکهٔ عصبی)
Loaded from `neural-data.js`:

- Mode color (GREEN/AMBER/RED)
- T_beat (heartbeat period)
- Readiness %
- Stress level

---

## Navigation

Footer nav links to other worlds:
- ‹ هاب (worlds/index.html)
- کاکپیت (worlds/01-cockpit/)
- ریسک (worlds/08-risk/)
- پول (worlds/03-money/)

---

## Security

- Static HTML — no server-side code
- Data loaded from relative `../../nervous-system/*.js` paths
- All actions are client-side log messages only (propose-only)
- No secrets in JS data files (content-free contract)

---

## Evidence

- File: `OCTOPUS/admin-telegram/index.html`
- Data deps: 7 × `.js` files
- Loads: `../worlds/octo-data.js` for merged view

---

## Related

- [[Dataflow]] — where the data comes from
- [[Backbone]] — shared data layer
- [[CH-04 · Telegram Bot Unified]] — the *real* execution surface (this UI is view-only)
- [[CH-14 · HITL Queue]] — queue data source
