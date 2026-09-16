---
title: "Octopus -- Phase 7: Panel Upgrade Plan"
date: 2026-07-09
status: PROPOSAL
confidence: HIGH
depends_on: Phase 6 (Panel Autopsy)
---

# PHASE 7 -- PANEL UPGRADE PLAN

> *Based on Phase 6's 9 visibility gaps, propose 8 new dashboard views that transform the existing localhost-only, stdlib-only panel into a real operational cockpit -- without breaking crash independence or read-only safety.*

---

## 1 · DESIGN CONSTRAINTS

Every proposed view MUST satisfy these constraints (inherited from the existing dashboard):

| Constraint | Rule | Evidence |
|---|---|---|
| **stdlib only** | No pip packages. No external CSS/JS frameworks. | dashboard/server.py: imports only from stdlib |
| **No organism import** | Dashboard must never `import organism` or `import opslib`. Crash independence is non-negotiable. | dashboard/server.py: zero organism imports |
| **Read-only state** | New views read state JSONs only. No writes to organism state. Only control-file writes (OCTOPUS.env, STOP, RESTART) are permitted. | Phase 6 Section 2.3 |
| **RTL Persian** | All labels and UI text in Farsi. dir="rtl". | dashboard/server.py: `<html lang="fa" dir="rtl">` |
| **Vazirmatn/Tahoma styling** | Font stack: `Vazirmatn, Tahoma, Arial, sans-serif`. Color palette: warm earth tones. | dashboard/server.py: STYLE block |
| **127.0.0.1 only** | No remote access. Localhost only. | dashboard/server.py: `("127.0.0.1", PORT)` |
| **No JavaScript required** | Current dashboard uses zero JavaScript (pure HTML + server-side rendering). New views should prefer the same. If JS is needed (charts), use inline `<script>` only. | dashboard/server.py: no `<script>` tags |

---

## 2 · PROPOSED VIEWS (8 NEW TABS)

### Priority Order: A > E > F > G > C > B > H > D

| Priority | View | Code | Purpose | Addresses Gap |
|---|---|---|---|---|
| 1 | Organism Overview | A | All organs status at a glance | Gap 8 (gates), Gap 5 (legs) |
| 2 | Power/Gates | E | Which gate is blocking, what is pending | Gap 8 |
| 3 | Incidents | F | Recent failures, watchdog revivals | Gap 7 (events) |
| 4 | Reality Gap | G | Intended vs real implementation | Gap 2 (RFC), Gap 6 (self-model) |
| 5 | Awareness | C | L0-L7 per organ, self-model completeness | Gap 4 (epistemics), Gap 6 (self-model) |
| 6 | Vital Signs | B | Heartbeat, queue depth, token burn, throughput | Gap 3 (cardiac) |
| 7 | Evolution | H | What changed, what learned, safe next upgrades | Gap 2 (RFC) |
| 8 | Neural Map | D | Connection diagram (simplified) | Gap 1 (neural stack) |

---

## 3 · VIEW A: ORGANISM OVERVIEW (Priority 1)

### Purpose
Single-page view of all organs' status lights, confidence, and uptime. Replaces the need to click through 5 tabs to understand system health. The "cockpit at a glance."

### Route
`/overview`

### Data Sources (all read-only)
- `ORGANISM-STATE.json` -- chrono, wiring, cardiac, halt/frozen/stop state
- `channel-status.json` -- channel live/stub
- `fitness-latest.json` -- authoritative status
- `replication-latest.json` -- live gate
- `CAPABILITY-OK.flag` -- capability check passed

### Layout

```
+------------------------------------------------------------------+
| ORGANISM OVERVIEW                              confidence: 87%   |
+------------------------------------------------------------------+
|                                                                   |
|  [HEART]  [DOCTOR]  [GOVERNOR]  [LEGS]  [TELEGRAM]  [MEMORY]   |
|   green     green     green       gray     gray        green     |
|  running   running   running    gated    stub       running      |
|                                                                   |
|  HEART (green)
|  - Pacemaker: running, beat_seq 42318, phi=0.92
|  - Cardiac: OFF (WIRE_BIO=0)
|  - Next epoch: 12 min
|
|  DOCTOR (green)
|  - Cycle: daily (every 1440 beats)
|  - Box: OFF | Evolution: OFF
|  - Last RFC: 3 proposals in ledger
|
|  GOVERNOR (green)
|  - Mode: dry
|  - Pressure: 0.23 (low)
|  - Next epoch: 12 min
|
|  LEGS (gray)
|  - LeadLeg: gated (WIRE_LEAD=1 but no confirmed leads)
|  - Live gate: LOCKED (no CONFIRMED revenue)
|
|  TELEGRAM (gray)
|  - Status: stub (no-creds)
|  - Required: TELEGRAM_BOT_TOKEN + TELEGRAM_OWNER_CHAT_ID
|
|  MEMORY (green)
|  - Ledger: 1,247 entries
|  - Last write: 4 minutes ago
|
+------------------------------------------------------------------+
|  METRICS                                                          |
|  +----------+ +----------+ +----------+ +----------+ +----------+  |
|  | Spend/mo | | Spend/dy | |   sigma  | | germ lag | | conflicts |  |
|  | AU$12.30 | | $0.0234  | |  0.72    | |   2.1h   | |     0     |  |
|  +----------+ +----------+ +----------+ +----------+ +----------+  |
+------------------------------------------------------------------+
```

### Implementation Notes
- Status light per organ: derive from ORGANISM-STATE.json wiring dict + flag states + channel-status
- Confidence score: composite of (organs running / total organs) * 100, with deductions for stale ts, halted, frozen
- Uptime: from ORGANISM-STATE.json `started` field
- All rendering is server-side HTML. No JavaScript.
- Read-only. No new writes.

---

## 4 · VIEW B: VITAL SIGNS (Priority 6)

### Purpose
Time-series-inspired view of heartbeat rhythm, queue depth, tool latency, token burn rate, and task throughput. Shows the organism's metabolic vital signs.

### Route
`/vitals`

### Data Sources (all read-only)
- `ORGANISM-STATE.json` -- chrono (beat_seq, phi), cardiac (if WIRE_BIO=1), pressure
- `telemetry-latest.json` -- per-organ costs, genome/brain metrics
- `replication-latest.json` -- sigma, spawn
- `budget/epochs/epoch-*.json` (latest 5) -- spend trend

### Layout

```
+------------------------------------------------------------------+
| VITAL SIGNS                          bio-rhythm: mice (40s tick)  |
+------------------------------------------------------------------+
|                                                                   |
|  HEARTBEAT                                                       |
|  +--------------------------------------------------------------+|
|  | beat_seq: 42318    | phi: 0.92   | tick: 60s (default)      ||
|  | metabolic_age: 47d  | experience: 42318 beats                 ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  CARDIAC (when WIRE_BIO=1)                                       |
|  +--------------------------------------------------------------+|
|  | pace: balanced | period: 60s | budget: 85/100 remaining      ||
|  | baroreflex: inactive | Kleiber factor: 1.0                   ||
|  +--------------------------------------------------------------+|
|  If WIRE_BIO=0: "Cardiac OFF -- running on fixed 60s tick"      |
|                                                                   |
|  TOKEN BURN (last 5 epochs)                                      |
|  +--------------------------------------------------------------+|
|  | Epoch 1: $0.02 | Epoch 2: $0.03 | ... | trend: flat           ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  THROUGHPUT                                                       |
|  +--------------------------------------------------------------+|
|  | Doctor cycles: 3/mo | Ledger writes: 18/day | RFCs: 1/day      ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### Implementation Notes
- Token burn: read last 5 epoch files, extract `spent_month_aud` from each, render as inline bar chart (CSS-only, no JS)
- CSS-only bar chart: `<div style="width: N%; background: green">` inside a container
- Cardiac section conditional on WIRE_BIO flag state
- Read-only. No new writes.

---

## 5 · VIEW C: AWARENESS VIEW (Priority 5)

### Purpose
Shows L0-L7 awareness level per organ, self-model completeness (SKELETON 5-field model), and epistemic metrics when available. Answers "how much does the organism know about itself?"

### Route
`/awareness`

### Data Sources (all read-only)
- `ORGANISM-STATE.json` -- wiring state (which organs are active)
- `school-awareness.json` -- learning awareness data
- `telemetry-latest.json` -- per-organ spending (proxy for awareness depth)
- `fitness-latest.json` -- experience_span_days, weights

### Layout

```
+------------------------------------------------------------------+
| AWARENESS VIEW                                                    |
+------------------------------------------------------------------+
|                                                                   |
|  ORGAN AWARENESS LEVELS                                           |
|  +--------------------------------------------------------------+|
|  | Organ      | Level | Evidence                                  ||
|  |------------|-------|------------------------------------------||
|  | HEART      | L7    | Real heartbeat, phi, metabolic age       ||
|  | DOCTOR     | L5    | Core cycle runs, box/evolution gated     ||
|  | GOVERNOR   | L6    | Dry allocation real, LLM gated            ||
|  | LEGS       | L3    | Code exists, no real leads confirmed      ||
|  | TELEGRAM   | L1    | Stub only, no credentials                 ||
|  | MEMORY     | L6    | Ledger active, heartbeat writes          ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  SELF-MODEL COMPLETENESS (SKELETON 5-field)                      |
|  +--------------------------------------------------------------+|
|  | Field          | Status   | Source                            ||
|  |----------------|----------|-----------------------------------||
|  | Identity       | partial  | organism.py name/version          ||
|  | Purpose        | complete | _PROJECT_INSTRUCTIONS.md           ||
|  | Capability     | complete | wiring state + Budgets.yaml       ||
|  | Boundary       | complete | .agentignore + safety constraints ||
|  | Context        | partial  | telemetry + fitness data           ||
|  |----------------|----------|-----------------------------------||
|  | Overall:       | 80%      | 4/5 complete, 1 partial           ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  EPISTEMIC METRICS (when WIRE_EPISTEMICS=1)                      |
|  If OFF: "Epistemic layer OFF -- metrics not computed"           |
|  If ON: coherence, novelty, grounding, calibration, coverage      |
+------------------------------------------------------------------+
```

### Awareness Level Legend

| Level | Meaning | Criteria |
|---|---|---|
| L0 | Dead | Code does not exist |
| L1 | Stub | Code exists but does nothing real |
| L2 | Simulated | Code runs but output is no-op or propose-only |
| L3 | Partial | Core logic works but gated or limited |
| L4 | Limited | Full logic but no real data (sandbox only) |
| L5 | Operational | Runs in production with propose-only safety |
| L6 | Autonomous | Runs in production with real effects |
| L7 | Self-aware | Runs, measures itself, adapts behavior |

### Implementation Notes
- Awareness levels derived from Phase 3 Vital Signs power-state matrix
- Self-model fields are static analysis (check if source files declare each field)
- Epistemic metrics conditional on WIRE_EPISTEMICS flag
- Read-only. No new writes.

---

## 6 · VIEW D: NEURAL MAP (Priority 8 -- lowest)

### Purpose
Simplified connection diagram showing the 8 neural stack modules and their activation state. ASCII-art or CSS-box diagram. Lowest priority because neural stack is behind WIRE_NEURAL and currently has no visible state JSONs.

### Route
`/neural`

### Data Sources (all read-only)
- `ORGANISM-STATE.json` -- WIRE_NEURAL flag state
- No dedicated neural state file currently exists (this is a blocker)

### Layout

```
+------------------------------------------------------------------+
| NEURAL MAP                              WIRE_NEURAL: OFF          |
+------------------------------------------------------------------+
|                                                                   |
|  +--------+    +--------+    +--------+    +--------+             |
|  | RHYTHM | --> |CIRCADIAN| --> | SPRINT | --> |AFFERENT|         |
|  |  L0    |    |   L0    |    |   L0    |    |   L0   |          |
|  +--------+    +--------+    +--------+    +--------+             |
|       |             |             |             |                  |
|       v             v             v             v                  |
|  +--------+    +--------+    +--------+    +--------+             |
|  |SPINDLE | <-- | CHEMO  | <-- |  GATE  | <-- | MEMORY |         |
|  |  L0    |    |   L0    |    |   L0    |    |   L0   |          |
|  +--------+    +--------+    +--------+    +--------+             |
|                                                                   |
|  All modules: L0 (WIRE_NEURAL=0, no state data)                  |
|                                                                   |
|  NOTE: This view requires WIRE_NEURAL=1 and neural state JSONs  |
|  to be emitted by the organism. Currently no neural state files  |
|  are written to _ops/state/.                                      |
+------------------------------------------------------------------+
```

### Implementation Notes
- CSS-only boxes with arrows (using CSS borders/pseudo-elements or simple ASCII in `<pre>`)
- All modules will show L0 until neural stack is actually emitting state
- This view is **placeholder-first**: it shows what the diagram will look like when data exists
- Read-only. No new writes.
- **Prerequisite**: organism must write neural state JSONs (out of scope for this plan)

---

## 7 · VIEW E: POWER/GATES VIEW (Priority 2)

### Purpose
Single-page view of all gates, which is currently blocking, what is pending approval, and the gate chain. This is the "why is X not happening?" page.

### Route
`/gates`

### Data Sources (all read-only)
- `ORGANISM-STATE.json` -- halted, frozen, stop_organism, protective_mode
- `_ops/budget/FREEZE.flag` -- budget freeze
- `replication-latest.json` -- live_gate (open/closed/why)
- `channel-status.json` -- telegram gate (creds)
- `OCTOPUS.env` -- WIRE flags (which features are gated)
- `Budgets.yaml` -- capability gates (readable, currently not parsed by dashboard)
- `CAPABILITY-OK.flag` -- capability check status

### Layout

```
+------------------------------------------------------------------+
| POWER / GATES                                                      |
+------------------------------------------------------------------+
|                                                                   |
|  SYSTEM GATES                                                     |
|  +--------------------------------------------------------------+|
|  | Gate            | State  | Detail                             ||
|  |-----------------|--------|-------------------------------------|
|  | Organism Stop   | green  | Not requested                       ||
|  | Freeze          | green  | FREEZE.flag not present             ||
|  | Protective Mode | green  | Not active                          ||
|  | Halted          | green  | Not halted                          ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  REVENUE GATES                                                    |
|  +--------------------------------------------------------------+|
|  | Gate            | State  | Detail                             ||
|  |-----------------|--------|-------------------------------------|
|  | Live Gate       | amber  | LOCKED (no CONFIRMED revenue)       ||
|  | Telegram        | red    | stub (no-creds)                    ||
|  | Reconcile       | amber  | WIRE_RECONCILE=0 (risky, off)       ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  FEATURE GATES (WIRE flags)                                       |
|  +--------------------------------------------------------------+|
|  | Flag               | State | Risk   | Note                     ||
|  |--------------------|-------|--------|--------------------------|
|  | WIRE_BIO           | OFF   | risky  | Cardiac dormant           ||
|  | WIRE_BARBELL       | OFF   | risky  | No barbell allocation    ||
|  | WIRE_DEBATE        | OFF   | risky  | No LLM debate            ||
|  | WIRE_EPISTEMICS    | OFF   | risky  | No epistemic metrics     ||
|  | WIRE_SELFHEAL      | OFF   | risky  | No circuit breaker       ||
|  | WIRE_RECONCILE     | OFF   | risky  | No Track-B reconcile      ||
|  | WIRE_FITNESS       | OFF   | risky  | No fitness outbox         ||
|  | All safe flags     | ON    | safe   | 11/11 active             ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  GATE CHAIN                                                       |
|  Lead --> confirm(reconcile) --> live_gate --> WIRE_BARBELL      |
|  [blocked: no confirmed revenue]                                |
+------------------------------------------------------------------+
```

### Implementation Notes
- Gate state derived from multiple read-only sources
- Color coding: green=open, amber=partially blocked, red=fully blocked
- Gate chain rendered as text flow diagram
- Read-only. No new writes.

---

## 8 · VIEW F: INCIDENT VIEW (Priority 3)

### Purpose
Recent failures, watchdog revivals, errors, and recovery events. The "what went wrong and how did it recover?" page.

### Route
`/incidents`

### Data Sources (all read-only)
- `ORGANISM-STATE.json` -- last_error, halted, suspect_zero_total, conflicts
- `watchdog.log` -- structured watchdog events (revivals, timeouts)
- `ledger.jsonl` -- filter for ERROR, REVIVAL, WATCHDOG event types (last 50)
- `replication-latest.json` -- sigma zone alerts
- `fitness-latest.json` -- integrity_alerts

### Layout

```
+------------------------------------------------------------------+
| INCIDENT VIEW                                                      |
+------------------------------------------------------------------+
|                                                                   |
|  ACTIVE ALERTS                                                    |
|  +--------------------------------------------------------------+|
|  | [!] Suspect Zero Totals: 3  | Conflicts: 0 | Errors: 0       ||
|  | [!] Integrity Alerts: 0    | Sigma Zone: PRE-REPLICATION     ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  LAST ERROR (from ORGANISM-STATE)                                  |
|  +--------------------------------------------------------------+|
|  | (none)                                                       ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  WATCHDOG LOG (last 30 entries)                                   |
|  +--------------------------------------------------------------+|
|  | 2026-07-08T06:07:14  REVIVAL   pacemaker thread recovered     ||
|  | 2026-07-08T05:07:12  HEARTBEAT beat_seq=42316 phi=0.91       ||
|  | 2026-07-08T04:07:10  HEARTBEAT beat_seq=42256 phi=0.89       ||
|  | ...                                                           ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  LEDGER EVENTS (ERROR/REVIVAL filter, last 20)                    |
|  +--------------------------------------------------------------+|
|  | (none in last 20 entries -- all events are NORMAL)            ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### Implementation Notes
- watchdog.log: parse last 30 lines, render in syntax-highlighted `<pre>` block (same style as ledger tail)
- Ledger filter: read last 50 entries, filter by type containing "ERROR", "REVIVAL", "WATCHDOG", "ALERT"
- Active alerts summary: aggregate from ORGANISM-STATE.json + fitness-latest.json
- Read-only. No new writes.

---

## 9 · VIEW G: REALITY GAP (Priority 4)

### Purpose
Shows the gap between what the system is designed to do (architecture) and what it actually does (runtime state). Answers "how far is design from reality?"

### Route
`/reality`

### Data Sources (all read-only)
- Phase 3 Vital Signs (static analysis of organ power states)
- `ORGANISM-STATE.json` -- runtime state
- Ledger event type distribution (from ledger.jsonl tail 100)
- Wiring flags from effective_flags()

### Layout

```
+------------------------------------------------------------------+
| REALITY GAP                                                        |
+------------------------------------------------------------------+
|                                                                   |
|  DESIGN vs REALITY                                                |
|  +--------------------------------------------------------------+|
|  | Component       | Design    | Reality   | Gap    | Risk      ||
|  |-----------------|-----------|-----------|--------|-----------||
|  | Pacemaker       | L7        | L7        | NONE   | --        ||
|  | Doctor Core     | L6        | L5        | SMALL  | low       ||
|  | Doctor Box      | L6        | L2        | LARGE  | medium    ||
|  | Doctor Evolution| L6        | L2        | LARGE  | medium    ||
|  | Governor Dry    | L6        | L6        | NONE   | --        ||
|  | Governor LLM    | L7        | L0        | MAX    | high      ||
|  | LeadLeg         | L6        | L2        | LARGE  | medium    ||
|  | Telegram        | L7        | L1        | MAX    | high      ||
|  | Cardiac         | L7        | L0        | MAX    | high      ||
|  | Neural Stack    | L6        | L0        | MAX    | high      ||
|  | Epistemics      | L6        | L0        | MAX    | high      ||
|  | Memory/Ledger   | L7        | L7        | NONE   | --        ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  GAP SCORE: 5.4 / 10  (weighted: 54% of design intent realized)  |
|                                                                   |
|  LEDGER ACTIVITY DISTRIBUTION (last 100 events)                  |
|  +--------------------------------------------------------------+|
|  | HEARTBEAT: 72 | EPOCH: 12 | PROPOSAL: 8 | MINE: 3 | ...     ||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

### Gap Score Calculation

```
gap_score = sum(real_level / design_level for each organ) / num_organs
```

Where levels are: L0=0, L1=1, ..., L7=7. Design levels from Phase 2 Organ Map maturity. Reality levels from Phase 3 Vital Signs power state.

### Implementation Notes
- Gap scores are static (derived from Phase 2/3 analysis) but can be auto-updated as data sources change
- Ledger event distribution: count event types in last 100 entries
- Read-only. No new writes.

---

## 10 · VIEW H: EVOLUTION VIEW (Priority 7)

### Purpose
Shows what changed in the system, what was learned, and what safe next upgrades are available. The "what's next?" page.

### Route
`/evolution`

### Data Sources (all read-only)
- `ledger.jsonl` -- filter for RFC, PROPOSAL, IMPLEMENTED, VERIFIED events (last 50)
- `ORGANISM-STATE.json` -- current wiring state, profile
- Phase 3 Vital Signs -- which risky flags are safely enablable

### Layout

```
+------------------------------------------------------------------+
| EVOLUTION VIEW                                                     |
+------------------------------------------------------------------+
|                                                                   |
|  RECENT CHANGES (from ledger, last 30 days)                      |
|  +--------------------------------------------------------------+|
|  | 2026-07-07  RFC       Doctor: mine 3 files, propose 1 RFC   ||
|  | 2026-07-07  EPOCH     Pressure 0.23, dry allocation OK        ||
|  | 2026-07-06  RFC       Doctor: 2 proposals, 0 implemented      ||
|  | ...                                                           ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  WHAT WAS LEARNED                                                 |
|  +--------------------------------------------------------------+|
|  | Experience: 47 days | Beats: 42,318 | RFCs proposed: 5       ||
|  | Confirmed revenue: $0 | Fitness authoritative: NO (shadow)   ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  SAFE NEXT UPGRADES (risky flags, ranked by safety)              |
|  +--------------------------------------------------------------+|
|  | Priority | Flag              | Impact         | Precondition  ||
|  |----------|-------------------|----------------|---------------|
|  | 1        | WIRE_FITNESS      | Fitness outbox | Reconcile OK  ||
|  | 2        | WIRE_EPISTEMICS   | 5 new metrics  | Doctor ON     ||
|  | 3        | WIRE_SELFHEAL     | Auto-recovery  | Cardiac ON    ||
|  | 4        | WIRE_RECONCILE    | Track-B        | CSV source    ||
|  | 5        | WIRE_BIO          | Dynamic tick   | Budget data   ||
|  | 6        | WIRE_DEBATE       | LLM debate     | Governor LLM  ||
|  | 7        | WIRE_BARBELL      | Core/Sat split | Live gate     ||
|  +--------------------------------------------------------------+|
|                                                                   |
|  NOTE: All risky flags are OFF by design (paper-full profile).   |
|  Each requires explicit owner approval + OCTOPUS.env write.       |
+------------------------------------------------------------------+
```

### Implementation Notes
- Ledger filter: scan last 50 entries for types RFC, PROPOSAL, IMPLEMENTED, VERIFIED, LEARNED
- Safe upgrades: static list derived from WIRE_FLAGS definition + dependency analysis
- Priority ranking based on: (1) no external dependency, (2) propose-only safety, (3) data availability
- Read-only. No new writes.

---

## 11 · IMPLEMENTATION ROADMAP

### Phase A: Foundation (1-2 hours)

| Task | Detail |
|---|---|
| Add new routes to dashboard/server.py | Add 8 new GET handlers in `_Handler.do_GET()` |
| Add nav items to `_shell()` | Extend nav_items list with 8 new tabs |
| Create placeholder functions | `page_overview()`, `page_vitals()`, etc. returning "coming soon" |

### Phase B: High-Priority Views (3-4 hours)

| View | Effort | Dependencies |
|---|---|---|
| A. Organism Overview | 1.5h | ORGANISM-STATE.json parsing (already exists) |
| E. Power/Gates | 1h | Flag parsing (already exists), FREEZE.flag check |
| F. Incidents | 1h | watchdog.log parser, ledger filter |
| G. Reality Gap | 0.5h | Static gap matrix (from Phase 2/3 data) |

### Phase C: Medium-Priority Views (2-3 hours)

| View | Effort | Dependencies |
|---|---|---|
| C. Awareness | 1h | school-awareness.json parsing, awareness level mapping |
| B. Vital Signs | 1h | Multi-epoch parsing, CSS-only bar charts |
| H. Evolution | 1h | Ledger event filtering, upgrade safety ranking |

### Phase D: Low-Priority Views (1-2 hours)

| View | Effort | Dependencies |
|---|---|---|
| D. Neural Map | 1.5h | **BLOCKED**: needs organism to emit neural state JSONs |

### Total Estimated Effort: 8-12 hours

---

## 12 · NAVIGATION STRUCTURE (FINAL)

Current 5 tabs become 13 tabs. Group into two rows:

**Row 1 (Operational -- most used):**
| Icon | Label | Route | New? |
|---|---|---|---|
| Home | Overview | `/overview` | YES (A) |
| Heart | Organism | `/` | existing |
| Tools | Capabilities | `/capabilities` | existing |
| Lock | Gates | `/gates` | YES (E) |
| Alert | Incidents | `/incidents` | YES (F) |

**Row 2 (Analytical -- less used):**
| Icon | Label | Route | New? |
|---|---|---|---|
| Eye | Awareness | `/awareness` | YES (C) |
| Pulse | Vitals | `/vitals` | YES (B) |
| Chart | Activity | `/activity` | existing |
| Radio | Channels | `/channels` | existing |
| Brain | Ideas | `/ideas` | existing |
| Split | Reality Gap | `/reality` | YES (G) |
| Grow | Evolution | `/evolution` | YES (H) |
| Net | Neural | `/neural` | YES (D) |

Implementation: split `nav_items` into two groups, render as two `<div class="nav">` blocks.

---

## 13 · DATA ACCESS PATTERN (TEMPLATE)

Every new view follows this pattern (derived from existing dashboard code):

```python
def page_gates() -> bytes:
    """Read-only gates view. No writes. No organism import."""
    st = _read_json("ORGANISM-STATE.json")      # existing helper
    ch = _read_json("channel-status.json")       # existing helper
    rep = _read_json("replication-latest.json")  # existing helper

    # Build HTML from read-only data
    body = (
        "<h1>...</h1>"
        f'<div class="card">...</div>'
    )
    return _shell(body, "gates")
```

Key rules:
1. Use `_read_json()` for all state files (existing helper, lines 162-167)
2. Use `_ledger_tail()` for ledger data (existing helper, lines 219-233)
3. Use `_effective_flags()` for flag state (existing helper, lines 190-204)
4. Use `_badge()` for status badges (existing helper, lines 299-300)
5. Use `_metric()` for metric cards (existing helper, lines 303-304)
6. Never write anything except control-files
7. Never import organism or opslib

---

## 14 · ACCEPTANCE CRITERIA

| Criterion | Test |
|---|---|
| All 8 new views render without error | Navigate to each route, verify 200 OK |
| No new imports beyond stdlib | `grep -c "import organism\|import opslib\|import attribution"` == 0 |
| No writes to organism state | No new write targets beyond OCTOPUS.env + STOP + RESTART |
| All text in Farsi | Every visible label is Persian |
| RTL layout | `dir="rtl"` on all pages |
| Vazirmatn font stack | Font-family matches existing dashboard |
| 127.0.0.1 only | Server binds to localhost only |
| Crash-safe | Dashboard crash does not affect organism on 8771 |
| Zero JavaScript (preferred) | No `<script>` tags (CSS-only charts) |
| Existing pages unchanged | `/`, `/capabilities`, `/activity`, `/channels`, `/ideas` work identically |

---

## 15 · RISK ASSESSMENT

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Performance: scanning ledger for incidents | Medium | Low | Limit to last 50/100 entries; ledger is ~1.2K entries |
| Performance: scanning epoch files for vitals | Low | Low | Only read last 5 epoch files |
| FREEZE.flag check adds filesystem I/O | Low | Negligible | Single `exists()` call |
| Bug in new views causes template error | Medium | Low | Server catches all exceptions in handler; user sees 500 |
| Nav becomes too crowded with 13 tabs | High | Medium | Two-row nav with clear grouping; responsive flex-wrap |

---

## 16 · WHAT THIS PLAN DOES NOT COVER

| Out of Scope | Reason |
|---|---|
| Neural state emission by organism | Requires changes to organism.py -- separate build plan |
| Telegram integration | Requires credentials and bot setup -- operational decision |
| Reconcile/CSV pipeline | Requires external data source (bank CSV) -- operational decision |
| Real-time WebSocket updates | Violates "no JavaScript required" constraint; organism is tick-based anyway |
| External package usage (Flask, FastAPI, etc.) | Violates "stdlib only" constraint |
| Mobile-responsive redesign | Current dashboard is desktop-localhost only by design |
| Multi-user access | Current dashboard is 127.0.0.1 only by design |
