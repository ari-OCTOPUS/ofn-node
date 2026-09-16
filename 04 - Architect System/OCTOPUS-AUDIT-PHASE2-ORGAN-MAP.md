---
title: "Octopus — Phase 2: Organ Map"
date: 2026-07-09
status: EVIDENCE-BACKED
confidence: HIGH
scope: Architecture map of 15 organs with maturity classification
depends_on: Phase 1 — Repository Autopsy
---

# PHASE 2 — ORGAN MAP

> *Every organ classified by: name, files, purpose, inputs, outputs, dependencies, state fields, current maturity, failure modes, alive/dead, what turns it on/off, and evidence.*

---

## Classification Legend

| Status | Meaning |
|---|---|
| **ACTIVE** | Code runs in production every tick. Evidence of execution in logs/state. |
| **PARTIAL** | Complete logic exists but gated behind WIRE flag (default off) or propose-only. |
| **STUB** | Scaffold only. Returns constants or empty. Explicitly documented as incomplete. |
| **DEAD** | Unreachable code. No import path in production. |

---

## Organ 1 · 🫀 HEART (Pacemaker + Cardiac)

| Attribute | Detail |
|---|---|
| **Name** | Pacemaker + Cardiac Allometry |
| **Files** | `chrono.py` (638 LOC), `cardiac.py` (275 LOC) |
| **Purpose** | Generates the global heartbeat rhythm. Chrono = SQLite-backed pacemaker thread. Cardiac = bio-inspired dynamic tick period (Kleiber scaling). |
| **Inputs** | Leg acks (phi-accrual), leg HLCs, scheduler tasks, `OCTOPUS_WIRE_BIO` flag |
| **Outputs** | `beat_seq` (monotonic counter), `metabolic_age`, `experience_meter`, `duration_marker`, `anticipation_queue`, `checkpoint`, `gated_effect` (all in `chrono.db`). Cardiac: `effective_period()` → dynamic sleep. |
| **Dependencies** | sqlite3, threading, `opslib` |
| **State Fields** | `heartbeat` table (beat_seq, ts, phi), `leg_clock`, `experience_meter`, `metabolic_age`, `duration_marker`, `anticipation_queue`, `checkpoint`, `gated_effect` |
| **Maturity** | Chrono: **ACTIVE / PRODUCTION**. Cardiac: **PARTIAL** (flag off by default). |
| **Alive?** | 🟢 Chrono thread runs every tick. 🟡 Cardiac dormant (WIRE_BIO=0). |
| **What turns it on/off** | Chrono: always on (no flag). Cardiac: `OCTOPUS_WIRE_BIO=1` via OCTOPUS.env. |
| **Failure Modes** | SQLite corruption (WAL mode mitigates). Thread deadlock (daemon → recoverable). Cardiac: BeatBudget depletion forces whale-mode (design intent, not failure). |
| **Evidence** | chrono.db tables (heartbeat, leg_clock, etc.). ORGANISM-STATE.json shows `chrono` fields. organism.py line 199 `chrono.start_pacemaker_thread()`. |

---

## Organ 2 · 🩺 DOCTOR

| Attribute | Detail |
|---|---|
| **Name** | Evolutionary Doctor + Box of Agents |
| **Files** | `doctor/doctor.py` (754 LOC), `doctor/chamber.py` (192), `doctor/evolution.py` (204), `doctor/calibration.py` (126), `doctor/spectral.py` (136), `doctor/box/box.py` (147), `doctor/box/` (12 files total) |
| **Purpose** | Self-repair cycle: mine bottlenecks → propose RFC → adversarial chamber → sandbox test → box simulation → evolution tournament → submit for human approval. |
| **Inputs** | State files (ORGANISM-STATE, telemetry, fitness), budget pressure, spectral analysis |
| **Outputs** | RFC markdown files in `knowledge/internal/`, ledger notes (DOCTOR_RFC_DRAFT, DOCTOR_SANDBOX, DOCTOR_SUBMIT), Telegram approval cards |
| **Dependencies** | `opslib`, `spectral.py`, `chamber.py`, `evolution.py`, `box/`, subprocess (test runner), tempfile (sandbox) |
| **State Fields** | RFC lifecycle (draft→drafted→sandboxed→submitted→merged/rejected). Box agents: cognitive/psych/energy layers (in-memory). |
| **Maturity** | **ACTIVE** (core mine→propose→sandbox cycle runs daily). **PARTIAL** (box, evolution behind flags). |
| **Alive?** | 🟢 Doctor beat runs every 1440 beats (~daily). 🟡 Box/Evolution dormant. |
| **What turns it on/off** | `OCTOPUS_WIRE_DOCTOR=1` (default on in paper-full). `OCTOPUS_WIRE_BOX=1`, `OCTOPUS_WIRE_EVOLUTION=1` for sub-features. |
| **Failure Modes** | Sandbox crash (subprocess timeout). No RFC submitted if mine returns None. Box agents diverge without Warden gate. |
| **Evidence** | doctor.py line 473 `run_cycle()`. Ledger entries. `knowledge/internal/` RFC files (if any). wiring.py line 276 doctor_beat. |

---

## Organ 3 · 🏛️ GOVERNOR (Budget + Epoch)

| Attribute | Detail |
|---|---|
| **Name** | Allostatic Governor |
| **Files** | `budget/governor_epoch.py` (341 LOC), `budget/telemetry.py` (205), `budget/opslib.py` (285), `budget/budgets.yaml` (6.9 KB) |
| **Purpose** | Pressure-based budget allocation. Computes spend_velocity, deadline_proximity, anomaly. Distributes headroom by fitness scores (value + urgency + efficiency + human − waste). Dry mode always runs; LLM mode gated. |
| **Inputs** | budgets.yaml (floors, caps, weights), telemetry snapshot, fitness scores, reconcile data, calendar (Friday = replan) |
| **Outputs** | `epochs/epoch-<ts>.json` (45 files), ledger NOTE(ALLOCATION_SHADOW), ORGANISM-STATE fields (month/today spend) |
| **Dependencies** | `opslib`, `telemetry`, `fitness`, budgets.yaml, organ_gate, barbell (flag-gated) |
| **State Fields** | `pressure`, `allostatic_period`, `allocation_dry` (per-organ), `explore_reserve`, `conflicts`, `suspect_zero_total` |
| **Maturity** | **ACTIVE / PRODUCTION** — dry allocation runs every tick. LLM mode: PARTIAL. |
| **Alive?** | 🟢 Every tick. |
| **What turns it on/off** | Always on (no flag). `OCTOPUS_WIRE_BARBELL` for barbell sub-allocation. LLM mode: `ACTIVATION-GOVERNOR-LLM.flag` + date gate. |
| **Failure Modes** | YAML parse error → crash. Budget floor > cap → no allocation. All organs at zero fitness → explore_reserve only. |
| **Evidence** | 45 epoch JSONs in `_ops/budget/epochs/`. organism.py line 276 `governor_epoch.run_epoch()`. budgets.yaml structure. |

---

## Organ 4 · 🦵 LEGS (Actuators)

| Attribute | Detail |
|---|---|
| **Name** | Lead Leg + Generic Leg base |
| **Files** | `legs/leg.py` (220 LOC), `legs/lead_leg.py` (143 LOC) |
| **Purpose** | Autonomous HLC (Heuristic Local Controller). Leg base: read allowlisted notes, reserve/settle/release budget, emit proposals (propose-only). LeadLeg: intake leads, draft quotes, claim, confirm revenue, run reconciliation. |
| **Inputs** | Attribution proposals, budget gate decisions, allowlisted vault notes |
| **Outputs** | Proposals (propose-only, never settle), attribution IDs, claim records, revenue reports |
| **Dependencies** | `opslib`, `attribution.py`, `reconcile.py`, `organ_gate.py` |
| **State Fields** | `TaskPacket` (frozen, capability-scoped, no wildcards, no secrets). `Proposal` dataclass. Attribution cell tracking. |
| **Maturity** | leg.py: **ACTIVE** (base class, structural constraints enforced). lead_leg.py: **PARTIAL** (behind WIRE_LEAD). |
| **Alive?** | 🟢 Leg base always imported. 🟡 LeadLeg gated. |
| **What turns it on/off** | `OCTOPUS_WIRE_LEAD=1` for LeadLeg. `OCTOPUS_WIRE_LEAD_TICK=1` for autonomous HLC loop. |
| **Failure Modes** | No organ resolved → "incubating" (never gets budget). Budget reserve without settle → leak. PII in TaskPacket (blocked at __post_init__). |
| **Evidence** | leg.py line 99 `Leg` class, line 193 structural constraint comment. lead_leg.py line 39 `LeadLeg(Leg)`. |

---

## Organ 5 · 📡 TELEGRAM / HUMAN INTERFACE

| Attribute | Detail |
|---|---|
| **Name** | Telegram Channel (stub) |
| **Files** | `wiring.py` (make_telegram_channel, line 121), `budget/approval_channel.py` (881 LOC) |
| **Purpose** | Human communication channel. Approval queue for RFCs and proposals. Lead submission confirmation. Doctor RFC submission. |
| **Inputs** | Telegram messages (from human), approval/rejection decisions |
| **Outputs** | Telegram messages (RFC cards, lead confirmations, organism status, daily brief) |
| **Dependencies** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID` (env vars — currently missing) |
| **State Fields** | `channel-status.json`: telegram={live: false, mode: "stub(no-creds)"} |
| **Maturity** | **STUB** — code exists but no credentials → stub transport. Approval channel logic complete but unreachable. |
| **Alive?** | 🔴 Dead. channel-status.json confirms `mode: "stub(no-creds)"`. |
| **What turns it on/off** | Presence of `TELEGRAM_BOT_TOKEN` env var. Currently absent. |
| **Failure Modes** | N/A — not running. If activated: API rate limit, network timeout, message too long (>4096 chars). |
| **Evidence** | channel-status.json line 12-21. wiring.py line 121 auto-on condition. approval_channel.py 881 lines of unreachable logic. |

---

## Organ 6 · 🧠 MEMORY (Ledger + Brain)

| Attribute | Detail |
|---|---|
| **Name** | Genome Ledger + Brain Cockpit |
| **Files** | `07 - Knowledge/genome-system/ledger/ledger.py` (12.6 KB), `brain/cockpit.py` (213 LOC), `_memory/HEARTBEAT.md` (19 KB), `_memory/EXPERIENCE-LEDGER.md` (47 KB) |
| **Purpose** | Append-only event ledger (genome-system, standalone git repo). Brain cockpit: Telegram-style multi-project approval UI. Experience ledger: human-readable organism history. |
| **Inputs** | Ledger entries from all subsystems (NOTE, EXPERIENCE, PROPOSAL, MONEY_ATTRIBUTION, ALLOCATION_SHADOW, DOCTOR_*). Cockpit reads ORGANISM-STATE. |
| **Outputs** | `ledger.jsonl` (append-only), HEARTBEAT.md (hourly), EXPERIENCE-LEDGER.md |
| **Dependencies** | genome-system/ledger.py, `opslib` (ledger bridge) |
| **State Fields** | Ledger: `{type, ts, agent, payload}`. Cockpit: in-memory approval queue. |
| **Maturity** | Ledger: **ACTIVE** (written every tick by opslib.heartbeat, governor, doctor). Cockpit: **PARTIAL** (real logic but unclear if invoked in production). |
| **Alive?** | 🟢 Ledger writes confirmed. 🟡 Cockpit — code exists but no evidence of Telegram invocation. |
| **What turns it on/off** | Ledger: always on. Cockpit: requires Telegram channel (currently dead). |
| **Failure Modes** | Ledger corruption (append-only mitigates). Human-append-guard prevents unauthorized edits. Cockpit: P-L6 reconciliation ensures no divergence from authoritative gate. |
| **Evidence** | ledger.jsonl exists in genome-system. opslib.heartbeat() writes HEARTBEAT.md every hour. cockpit.py line 67-91 P-L6 gate. |

---

## Organ 7 · 🔒 GATES (Money + Capability + Organ)

| Attribute | Detail |
|---|---|
| **Name** | Triple-Layer Gate System |
| **Files** | `budget/money_gate.py` (46 LOC), `budget/capability_gate.py` (104), `budget/organ_gate.py` (178), `budget/approval_channel.py` (881), `budget/human_append_guard.py` (122), `state/CAPABILITY-OK.flag` (1.5 KB) |
| **Purpose** | Fail-closed spending authorization. Money gate: dual-lock (attribution + approval). Capability gate: checks CAPABILITY-OK.flag. Organ gate: per-organ floor enforcement. Human append guard: prevents unauthorized ledger edits. |
| **Inputs** | Spending requests (budget reservation, capability invocation, ledger writes), human approvals (Telegram) |
| **Outputs** | Approved/denied decisions, CAPABILITY-OK.flag (62 test pass list), approval queue entries |
| **Dependencies** | `opslib`, attribution.py, fitness.py, replication.py |
| **State Fields** | Money: `authorize(cap, organ, attribution_id, human_ref)`. Capability: `CAPABILITY-OK.flag` SHA-256 fingerprint. Organ: `reserve()`, `settle()`, `release()`. |
| **Maturity** | **ACTIVE / PRODUCTION** — all gates enforced. money_gate: dual-lock. capability_gate: 62 tests must pass. |
| **Alive?** | 🟢 All gates enforced every tick. |
| **What turns it on/off** | Always on. No flag to disable (by design — safety critical). |
| **Failure Modes** | CAPABILITY-OK.flag missing → all capabilities blocked. Attribution ID missing → money_gate denies. Live gate date not reached → replication blocked. |
| **Evidence** | money_gate.py line 46 (dual-lock). capability_gate.py checks CAPABILITY-OK.flag. organism.py protective_halt logic. |

---

## Organ 8 · 💰 LEDGER / MONEY / RISK

| Attribute | Detail |
|---|---|
| **Name** | Financial Attribution + Reconciliation |
| **Files** | `budget/attribution.py` (191 LOC), `budget/reconcile.py` (122), `budget/fitness.py` (237), `budget/replication.py` (134), `budget/env_loader.py` (76) |
| **Purpose** | Money lifecycle: propose attribution → confirm revenue → reconcile bank CSVs → compute fitness → evaluate replication sigma. |
| **Inputs** | Bank CSV files (reconcile), attribution proposals (attribution), confirmed revenue (fitness), genome data (fitness). |
| **Outputs** | `fitness-latest.json`, `replication-latest.json`, `telemetry-latest.json` (per-organ costs), attribution cell records |
| **Dependencies** | `opslib`, budgets.yaml, ledger |
| **State Fields** | Fitness: authoritative, claimed, confirmed, integrity_alerts, weights. Replication: sigma, zone, eligible_cells, live_gate. |
| **Maturity** | Attribution: **ACTIVE**. Fitness: **PARTIAL** (authoritative=false since ~Jun 2026). Reconcile: **STUB** (no CSVs submitted). Replication: **LOCKED** (live_gate until 2026-07-21). |
| **Alive?** | 🟢 Attribution runs. 🟡 Fitness frozen (claimed=0, confirmed=0). 🔴 Reconcile empty. 🔴 Replication locked. |
| **What turns it on/off** | Attribution: always on. Fitness: `OCTOPUS_WIRE_FITNESS`. Reconcile: `OCTOPUS_WIRE_RECONCILE`. Replication: live_gate (date + flag). |
| **Failure Modes** | Authoritative locked → fitness meaningless. Reconcile CSV parse error. Replication sigma > 1 → danger zone. |
| **Evidence** | fitness-latest.json: authoritative=false. replication-latest.json: sigma=0.0, live_gate until 2026-07-21. _ops/reconcile/: only README.md (no CSVs). |

---

## Organ 9 · 📚 LEARNING ENGINE

| Attribute | Detail |
|---|---|
| **Name** | Learning Engine (off-loop) |
| **Files** | `04 - Architect System/learning-engine/` (LEARNING-CONTRACT.yaml, STARTUP-CHECKLIST.yaml), `neural/hebbian.py` (107 LOC), `neural/consolidation.py` (80) |
| **Purpose** | Hebbian association learning + canonical memory consolidation. Off-loop (not in tick cycle). |
| **Inputs** | Neural signal patterns (SignalHub), vault notes (for consolidation paths) |
| **Outputs** | Hebbian weight updates (in-memory). Consolidated canonical paths (propose-only). |
| **Dependencies** | `neural/signal_hub.py`, neural stack |
| **State Fields** | Hebbian: weight matrix (in-memory, no persistence). Consolidation: canonical_paths (in-memory). |
| **Maturity** | **STUB** — hebbian.py has code but no persistence. Consolidation behind WIRE_CONSOLIDATION. Learning contract is a YAML spec, not running code. |
| **Alive?** | 🟡 Hebbian exists but no evidence of state changes. 🔴 Consolidation gated. |
| **What turns it on/off** | `OCTOPUS_WIRE_NEURAL` (parent). `OCTOPUS_WIRE_CONSOLIDATION` (specific). |
| **Failure Modes** | In-memory weights lost on restart (no persistence). Consolidation path explosion. |
| **Evidence** | hebbian.py 107 lines (real math, no disk I/O). consolidation.py 80 lines. wiring.py line 540 make_neural_stack. |

---

## Organ 10 · 📐 EPISTEMICS

| Attribute | Detail |
|---|---|
| **Name** | Epistemic Metrics Layer |
| **Files** | `epistemics/run_offloop.py` (62), `epistemics/contracts.py` (75), `epistemics/emit.py`, `epistemics/metrics.py`, `epistemics/readers.py`, `epistemics/__init__.py` |
| **Purpose** | 5 epistemic metrics: identifiability, channel fidelity, levels, self-reference, methodology. Scaffold for measuring how well the organism knows what it knows. |
| **Inputs** | Fitness history, topology data, self-vs-twin comparison data |
| **Outputs** | `_ops/state/epi-latest.json` (only with --emit flag) |
| **Dependencies** | `epistemics/metrics.py`, `epistemics/readers.py` |
| **State Fields** | identifiability, channel, levels, self_reference, method |
| **Maturity** | **STUB** — explicitly documented: "not authoritative until upstream data is live". channel() passes empty list. |
| **Alive?** | 🔴 Scaffold only. No upstream data. |
| **What turns it on/off** | `OCTOPUS_WIRE_EPISTEMICS` flag. |
| **Failure Modes** | N/A — already non-functional. |
| **Evidence** | run_offloop.py line 6: "Numbers are MEANINGLESS until Phase 1-3 fill upstream data". line 32: `channel([])` with TODO comment. |

---

## Organ 11 · 🪞 SELF-MODEL

| Attribute | Detail |
|---|---|
| **Name** | Organism Self-Model |
| **Files** | `organism.py` (_write_state), `state/ORGANISM-STATE.json`, `dashboard/server.py` (read-only mirror) |
| **Purpose** | The organism writes its own state every tick: halted, frozen, month/today spend, germline_lag, epoch_mode, suspect_zero, conflicts, protective_skip, wiring summary. Dashboard reads this state and presents it. |
| **Inputs** | All subsystem states aggregated by organism.py |
| **Outputs** | ORGANISM-STATE.json (423 B), dashboard UI rendering |
| **Dependencies** | All subsystems (for state collection) |
| **State Fields** | ts, started, epoch_mode, halted, frozen, stop_organism, month, today, suspect_zero_total, conflicts, germline_lag_h |
| **Maturity** | **ACTIVE** — written every tick. But limited to ~12 fields. No awareness of "why" or "what next". |
| **Alive?** | 🟢 Written every ~5 minutes. |
| **What turns it on/off** | Always on. |
| **Failure Modes** | Stale state (timestamp > 30 min = organism dead). Missing fields (partial write). |
| **Evidence** | ORGANISM-STATE.json last written 2026-07-09T22:53. organism.py line 369 `_write_state()`. |

---

## Organ 12 · 🐕 WATCHDOG / STAY-ALIVE

| Attribute | Detail |
|---|---|
| **Name** | Process Watchdog |
| **Files** | `watchdog.py` (86 LOC), `state/watchdog.log` (153 B) |
| **Purpose** | Detects organism death (port 8771 dead) and proposes revival. Propose-only — execution is owner/PS1 only. |
| **Inputs** | TCP connection to 127.0.0.1:8771, STOP-ORGANISM flag, ORGANISM-STATE.json existence |
| **Outputs** | `watchdog.log` (revival entries), proposal string for revival action |
| **Dependencies** | `opslib`, socket |
| **State Fields** | watchdog.log (2 entries: 2026-07-07, 2026-07-08 revivals) |
| **Maturity** | **PARTIAL** — logic complete but execution is propose-only. Real revival requires external PS1 script. |
| **Alive?** | 🟡 Watchdog logic works (2 proven revivals). But it only proposes — external script does actual restart. |
| **What turns it on/off** | Must be run externally (not in organism.py loop). |
| **Failure Modes** | Port check false-positive (organism slow but alive). First-birth guard prevents premature revive. |
| **Evidence** | watchdog.log: 2 entries showing real revivals. watchdog.py line 81: "execution = owner/PS1 only". |

---

## Organ 13 · 👁️ SENSORS (Afferent + Sensory Bus)

| Attribute | Detail |
|---|---|
| **Name** | Sensory Input System |
| **Files** | `afferent/ingest_raw.py` (218 LOC), `afferent/sensory_bus.py` (154), `afferent/school_bridge.py` (103) |
| **Purpose** | Ingest raw data (crypto/accounting CSVs), classify observations (rule-based, stub for LLM/embedding), detect PII (15 patterns), compute afferent ratio (alarm if < 15% real sensory). |
| **Inputs** | CSV files (crypto, accounting), internal events, external observations |
| **Outputs** | Classified observations (lead, error, payment, status, market), afferent_ratio alarm, advisory bus events |
| **Dependencies** | `opslib`, unified_bus (optional), school_bridge |
| **State Fields** | Observation (source, obs_type, label, intensity), afferent_ratio, alarm status |
| **Maturity** | **PARTIAL** — ingestion works. Classifier is explicitly "stub" (rule-based, not LLM). Behind WIRE_SCHOOL. |
| **Alive?** | 🟡 Behind flag. When off, no sensory data flows. |
| **What turns it on/off** | `OCTOPUS_WIRE_SCHOOL=1`. |
| **Failure Modes** | CSV parse error. PII leak (15 patterns may not cover all). Afferent ratio < 15% = "system is dreaming" alarm. |
| **Evidence** | sensory_bus.py line 64: "classifier with LLM/embedding — currently rule-based". wiring.py line 728 make_sensory_bus behind WIRE_SCHOOL. |

---

## Organ 14 · ✋ CAPABILITY LAYER

| Attribute | Detail |
|---|---|
| **Name** | Profile + Wiring + Flag System |
| **Files** | `wiring.py` (856 LOC), `budget/env_loader.py` (76), `_ops/OCTOPUS.env` (dynamic, created by dashboard) |
| **Purpose** | Central nervous system: 19 WIRE_* flags + 5 CHRONO_* cadences + 3 profile levels (bare/paper-full/live). Factory functions create subsystems based on flags. |
| **Inputs** | `OCTOPUS_PROFILE` env var, `OCTOPUS_WIRE_*` flags, `CHRONO_*_EVERY_N_BEATS` cadences |
| **Outputs** | Instantiated subsystem objects (or None), wire_summary dict (shown in dashboard) |
| **Dependencies** | All subsystem modules (conditionally imported) |
| **State Fields** | 19 boolean flags, 5 integer cadences, 1 profile level |
| **Maturity** | **ACTIVE / PRODUCTION** — every boot applies profile and wires subsystems. |
| **Alive?** | 🟢 Core infrastructure. Always runs. |
| **What turns it on/off** | Profile: `OCTOPUS_PROFILE` ∈ {bare, paper-full, live}. Individual flags: OCTOPUS_WIRE_*. |
| **Failure Modes** | Import error in conditional subsystem → that subsystem = None (fail-soft). Flag conflict (e.g., WIRE_LEAD but not WIRE_DOCTOR). |
| **Evidence** | wiring.py line 60 `apply_profile()`. organism.py line 167 calls wiring. Dashboard reads/writes flags via OCTOPUS.env. |

---

## Organ 15 · 🧫 SHADOW / SANDBOX / BOXED AGENTS

| Attribute | Detail |
|---|---|
| **Name** | Box of Agents (Micro-World) |
| **Files** | `doctor/box/box.py` (147), `doctor/box/agent_state.py` (118), `doctor/box/archivist.py` (85), `doctor/box/warden.py` (137), `doctor/box/sensors.py` (149), `doctor/box/dynamics.py` (106), `doctor/box/topology.py` (92), `doctor/box/primitive.py` (115), `doctor/box/null_dreamer.py` (48), `doctor/box/falsif_harness.py` (152), `doctor/box/b3_bridge.py` (109), `doctor/box/b4_fusion.py` (148) |
| **Purpose** | 12 specialized sub-agents in an isolated micro-world. Each agent has cognitive, psych, and energy layers. Warden is master gate. Runs MAP-Elites–style tournament inside doctor's sandbox cycle. |
| **Inputs** | Doctor's RFC context, sensory signals, topological data |
| **Outputs** | In-memory metrics history. Agent messages. Jacobian estimates. Safety check results. |
| **Dependencies** | doctor.py (orchestrator), box sub-modules |
| **State Fields** | AgentState (cognitive, psych, energy), metrics_history (accumulating list), Jacobian, rho(J) |
| **Maturity** | **PARTIAL** — complete agent dynamics but all in-memory, no persistence. Behind WIRE_BOX. |
| **Alive?** | 🟡 Behind flag. When on, runs inside doctor cycle. No disk state. |
| **What turns it on/off** | `OCTOPUS_WIRE_BOX=1`. |
| **Failure Modes** | Agent divergence (Jacobian explosion). Warden denies all → cycle dead-ends. No persistence → all state lost on restart. |
| **Evidence** | box.py line 56: 6 agents (Warden, Archivist, Dreamer, Skeptic, Integrator, null-dreamer). wiring.py line 134 make_box. No disk writes found. |

---

## Organ Summary Matrix

| # | Organ | Status | Maturity | Alive | Flag | LOC |
|---|---|---|---|---|---|---|
| 1 | 🫀 HEART (Pacemaker) | ACTIVE | Production | 🟢 | Always on | 638 |
| 1b | 🫀 HEART (Cardiac) | PARTIAL | Gated | 🟡 | WIRE_BIO | 275 |
| 2 | 🩺 DOCTOR | ACTIVE | Production | 🟢 | WIRE_DOCTOR | 1,559 |
| 3 | 🏛️ GOVERNOR | ACTIVE | Production | 🟢 | Always on | 831 |
| 4 | 🦵 LEGS (base) | ACTIVE | Production | 🟢 | Always on | 220 |
| 4b | 🦵 LEGS (Lead) | PARTIAL | Gated | 🟡 | WIRE_LEAD | 143 |
| 5 | 📡 TELEGRAM | STUB | No creds | 🔴 | Token env | 881 |
| 6 | 🧠 MEMORY (Ledger) | ACTIVE | Production | 🟢 | Always on | ~12.6 KB |
| 6b | 🧠 MEMORY (Cockpit) | PARTIAL | Unclear | 🟡 | Telegram | 213 |
| 7 | 🔒 GATES | ACTIVE | Production | 🟢 | Always on | 1,335 |
| 8 | 💰 MONEY | PARTIAL | Locked | 🟡 | Multiple | 760 |
| 9 | 📚 LEARNING | STUB | Scaffold | 🟡 | WIRE_NEURAL | 187 |
| 10 | 📐 EPISTEMICS | STUB | Scaffold | 🔴 | WIRE_EPISTEMICS | ~300 |
| 11 | 🪞 SELF-MODEL | ACTIVE | Limited | 🟢 | Always on | ~50 |
| 12 | 🐕 WATCHDOG | PARTIAL | Propose | 🟡 | External | 86 |
| 13 | 👁️ SENSORS | PARTIAL | Gated | 🟡 | WIRE_SCHOOL | 475 |
| 14 | ✋ CAPABILITY LAYER | ACTIVE | Production | 🟢 | Always on | 856 |
| 15 | 🧫 BOX AGENTS | PARTIAL | Gated | 🟡 | WIRE_BOX | 1,319 |

---

## Maturity Distribution

```
ACTIVE (Production):   7 organs  (Heart-pacemaker, Doctor, Governor, Legs-base, Ledger, Gates, Capability)
PARTIAL (Gated/Propose): 9 organs (Cardiac, LeadLeg, Telegram, Cockpit, Money, Learning, Self-Model-limited, Watchdog, Sensors, Box)
STUB (Scaffold):        2 organs  (Epistemics, Telegram-channel)
LOCKED:                 2 sub-organs (Fitness-authoritative, Replication-live-gate)
```

**Key Insight:** 7 of 15 organs are fully active. 9 are gated behind flags or propose-only. Only the Telegram channel is truly dead (missing credentials). The system is heavily in "propose-only" mode — it can think, analyze, and suggest, but cannot act in the real world without human approval channels.

---

**PHASE 2 COMPLETE.**

*Next: PHASE 3 — Vital Signs & Power State (ON/OFF per organ, fake vs real liveness, blockers).*
