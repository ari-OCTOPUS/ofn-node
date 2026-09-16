---
title: "Octopus — Phase 4: Awareness Analysis"
date: 2026-07-09
status: EVIDENCE-BACKED
confidence: HIGH
depends_on: Phase 1-3
---

# PHASE 4 — AWARENESS ANALYSIS

> *Rate each organ and the system-as-a-whole on the L0–L7 awareness scale. Every rating grounded in code evidence from Phases 1–3.*

---

## 1 · Awareness Scale (L0–L7)

| Level | Name | Description |
|---|---|---|
| **L0** | No Awareness | Static scripts. No state knowledge. No decision-making. |
| **L1** | Local State Awareness | Knows its own current task, status, inputs, outputs. Cannot reason about anything beyond itself. |
| **L2** | Inter-Module Awareness | Knows dependencies and neighbors. Can report on other modules' states. Cannot explain WHY things are the way they are. |
| **L3** | System Awareness | Knows all major organs and their current health. Has a model of the whole system. Cannot explain failure patterns or reason about goals. |
| **L4** | Goal Awareness | Knows what it is trying to achieve and why. Can connect actions to objectives. |
| **L5** | Reflective Awareness | Can explain failures, uncertainty, and missing knowledge. Knows what it does not know. |
| **L6** | Adaptive Awareness | Can change strategy based on outcomes. Learns from failure history. |
| **L7** | Meta-Awareness | Can reason about its own architecture and propose safe improvements. Understands its own limitations and design trade-offs. |

---

## 2 · Per-Organ Awareness Ratings

### Organ 1 · HEART (Pacemaker) — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | `beat_seq`, `phi` (per-leg liveness), `HLC` (Hybrid Logical Clock), `metabolic_age`, `experience_meter`, `anticipation_queue`. Writes all to `chrono.db`. |
| **What it does not know** | WHY it beats (no purpose model). What other organs do (no neighbor awareness). Whether the organism is achieving anything. |
| **Evidence** | `chrono.py` line 475 `beat_once()`: increments counter, collects acks, computes phi, writes to SQLite. No reference to goals, no inter-organ reasoning. `ORGANISM-STATE.json` receives only raw chrono fields: `{"chrono": {"beat": N, "phi": {...}, "period": ...}}`. |
| **Why not L2** | The pacemaker publishes `pulse` to the tick loop (organism.py:230) but never reads other organs' state. It is a pure oscillator — a metronome, not a diagnostician. |
| **Gap to L2** | Would need to read ORGANISM-STATE or epoch data and adjust beat cadence based on system health (Cardiac purports to do this but is gated off). |
| **Gap to L0** | L0 would be a `time.sleep(30)` with no state at all. Pacemaker is clearly above that. |

---

### Organ 1b · HEART (Cardiac) — L0: No Awareness (Gated)

| Attribute | Detail |
|---|---|
| **Rating** | **L0** (effectively — code is unreachable) |
| **What it knows (in theory)** | If enabled, would know mass, period, BeatBudget, Kleiber scaling, baroreflex pressure. Would be L1 at best. |
| **What it does not know** | Everything — it is behind `OCTOPUS_WIRE_BIO=0`. `cardiac.get_layer()` returns `(None, None)`. |
| **Evidence** | Phase 3: `OCTOPUS_WIRE_BIO` defaults to 0. organism.py calls `cardiac.get_layer()` after wiring — returns None when flag off. Base `TICK_SECONDS` used instead. |
| **Why not L1** | Code does not execute. A gated module has zero awareness. Awareness is measured at runtime, not on paper. |

---

### Organ 2 · DOCTOR — L2: Inter-Module Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L2** |
| **What it knows** | Reads ORGANISM-STATE, telemetry snapshots, ledger entries, fitness scores, sandbox results. Identifies bottlenecks (error-rate-high, effects-stuck, frozen-conflict, sigma-cancer-risk). Knows the severity landscape across subsystems. |
| **What it does not know** | WHY a bottleneck recurs. Whether its proposed fixes actually resolved anything (no measured_lift feedback loop — evolution behind flag). Whether the organism is making progress toward goals. Its own success/failure rate. |
| **Evidence** | `doctor.py` line 227 `mine()`: reads `trace` dict with `errors_24h`, `effects_pending`, `frozen`, `sigma_effective`. Returns `{bottleneck, evidence, severity}`. No historical pattern analysis — each mine is a fresh scan. `doctor.py` line 473 `run_cycle()`: mine → propose → sandbox → submit. Submit goes to dead Telegram (Phase 3 finding). No feedback loop from "submitted → approved/rejected → measured". |
| **Why not L3** | L3 requires a persistent model of all organs' health. Doctor reads snapshots but does not maintain a health model. Its `mine()` is stateless — no memory of past bottlenecks, no trend detection. It cannot answer "which organ is degrading?" across time. |
| **Gap to L3** | Maintain a bottleneck history. Track recurrence patterns. Correlate with governor pressure changes. Build an organ health model that persists across cycles. |
| **Gap to L5** | Cannot explain uncertainty. `mine()` returns None when nothing is wrong but cannot articulate *why* nothing is wrong or what blind spots exist. |

---

### Organ 3 · GOVERNOR — L3: System Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L3** |
| **What it knows** | All organs' fitness scores (value, urgency, efficiency, human, waste from `budgets.yaml`). Budget pressure = `max(spend_velocity, deadline_proximity, anomaly)`. Deadline proximity for every organ (sigmoid 14-day curve). Allocation across all organs. Conflict detection. |
| **What it does not know** | Whether its allocations are effective (no outcome tracking). WHY certain organs consistently get low fitness. Whether the organism has goals beyond "don't overspend." How to change strategy based on failure history. |
| **Evidence** | `governor_epoch.py` line 45 `_deadline_proximity()`: iterates `organs` dict, computes sigmoid per organ. Line 59 `pressure_state()`: reads `organ_table()`. Line 1-10 docstring: `pressure = max(spend_velocity, deadline_proximity, anomaly)`. Knows all organs, all budgets, all deadlines. Most system-aware organ in the codebase. |
| **Why not L4** | L4 requires goal awareness — knowing what the organism is *trying to achieve*. Governor optimizes `pressure` (avoid overspend) but has no concept of *purpose*. It cannot answer "are we making progress?" — only "are we within budget?" Pressure is a constraint metric, not an objective function. The organism's goal is survival (append-only genome), but Governor does not model this. |
| **Why not L5** | No reflective capacity. Cannot explain why pressure is high beyond the formula. Cannot articulate uncertainty about its allocations. Does not know what it does not know. |
| **Gap to L4** | Inject goal-derived objectives into the fitness function. Connect allocation outcomes to organism-level goals (e.g., "reduce RFC rejection rate", "increase lead conversion"). |
| **Gap to L6** | No adaptation based on outcomes. Governor runs the same S1..S5 Darwinian allocation every epoch regardless of whether previous allocations helped. No outcome feedback loop. |

---

### Organ 4 · LEGS (Base) — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Budget reservation/settle/release logic. Read allowlist (vault notes). Structural constraints (no wildcards, no secrets in TaskPacket). `__post_init__` enforces PII guard. |
| **What it does not know** | Why it is reserving budget. What the budget is for. What other legs are doing. What goal the task serves. Whether its proposals ever get approved (no feedback). |
| **Evidence** | `leg.py` line 99 `Leg` class: `reserve()`, `settle()`, `release()` — pure financial mechanics. Line 193: structural constraint comment. No reference to goals, no neighbor queries, no outcome tracking. |
| **Why not L2** | No inter-module awareness. Does not read other organs' state. Does not know if the Governor allocated its budget. Does not know if Doctor found a bottleneck related to its tasks. |
| **Gap to L2** | Read allocation from epoch files. Know which organ's budget it draws from. Report own status to the system model. |

---

### Organ 4b · LEGS (Lead) — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Attribution data. Lead quotes. Revenue claims (confirmed=0, Phase 3 finding). HLC for local coordination. |
| **What it does not know** | Whether leads are profitable. Why confirmed=0. What the sales pipeline looks like. How its intake connects to organism goals. |
| **Evidence** | `lead_leg.py` line 39 `LeadLeg(Leg)`: extends base Leg with lead-specific methods. Phase 3: zero confirmed revenue. No strategic pipeline model. |
| **Why not L2** | Does not correlate lead outcomes with other organs (e.g., does Governor allocation affect lead intake?). No pipeline health model. |
| **Gap to L2** | Track lead conversion funnel. Correlate with budget allocation. Report pipeline health to system model. |

---

### Organ 5 · TELEGRAM — L0: No Awareness (Dead)

| Attribute | Detail |
|---|---|
| **Rating** | **L0** |
| **What it knows** | Nothing. Code is unreachable. |
| **Evidence** | Phase 3: `channel-status.json`: `{live: false, mode: "stub(no-creds)"}`. 881 lines of `approval_channel.py` never execute. `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_CHAT_ID` not set. |
| **Why not L1** | Dead code has zero awareness at runtime. If enabled, would be L1 (knows message content, approval state). |

---

### Organ 6 · MEMORY (Ledger) — L0: Passive Append-Only

| Attribute | Detail |
|---|---|
| **Rating** | **L0** |
| **What it knows** | Nothing. It is a data structure, not an agent. |
| **Evidence** | `opslib.ledger_note()` appends JSON lines to `ledger.jsonl`. No read-back analysis. No querying. No indexing. No awareness of what it stores. It is a write-only pipe. |
| **Why not L1** | L1 requires "knows current task/status." Ledger has no task and no status. It is infrastructure, not an agent. Even infrastructure can have awareness (e.g., a smart cache knows hit rates — L1), but this ledger is purely passive. |
| **Note** | If Ledger were to gain awareness, it would start by knowing its own size, growth rate, and entry-type distribution. That would be L1. |

---

### Organ 6b · MEMORY (Cockpit) — L2: Inter-Module Awareness (Unreachable)

| Attribute | Detail |
|---|---|
| **Rating** | **L2** (if invoked; currently **L0** at runtime) |
| **What it knows (in theory)** | Organism state, approval queue, alarms, daily brief. Reads `ORGANISM-STATE.json`. Renders status for human consumption. P-L6 gate ensures no divergence from authoritative source. |
| **What it does not know** | Why alarms fire. Whether the organism is healthy. What to do about problems (display-only). |
| **Evidence** | Phase 3: `cockpit.py` has real text-generation logic for status, approval queue, alarms, daily brief. But Telegram is dead, so cockpit is never invoked. No evidence of cockpit output in any log or state file. |
| **Why not L3** | Cockpit reads state but does not model it. Cannot answer "is the organism healthy?" — it can only display what it reads. No diagnostic capability. |
| **Runtime rating** | **L0** — dead code, same as Telegram. Awareness is measured at runtime. |

---

### Organ 7 · GATES — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Approval state (CAPABILITY-OK.flag exists, 62 test modules). Capability checks pass/fail. Budget reservation active. Money gate dual-lock (attribution + capability). |
| **What it does not know** | Why a capability was denied. Whether denials are increasing. What pattern exists in gate failures. Whether gating is too strict or too loose. |
| **Evidence** | `organ_gate.py` enforces budget reservation. `money_gate.py` dual-lock enforced. `CAPABILITY-OK.flag` (1.5 KB, 62 modules) checked before every capability use. organism.py `protective_halt` logic active. Gates return pass/fail but never explain reasoning. |
| **Why not L2** | No inter-module awareness. Does not report denial patterns to Doctor or Governor. Does not correlate denials with system health. Cannot explain "capability X was denied because Y" in a diagnostic context. |
| **Gap to L2** | Log denial reasons with structured metadata. Report denial patterns to Doctor for bottleneck mining. Correlate denials with allocation changes. |

---

### Organ 8 · MONEY — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Fitness scores (value, urgency, efficiency, human, waste). Attribution data. Replication sigma. Reconcile status. |
| **What it does not know** | Whether fitness scores are accurate (`authoritative=false` — Phase 3). Whether money flows are real (all $0). Why confirmed=0. Whether its metrics drive useful behavior. |
| **Evidence** | `fitness-latest.json`: `authoritative=false`, `claimed=0`, `confirmed=0`. `replication-latest.json`: `sigma=0.0`, `live_gate` until 2026-07-21. Phase 3: fitness authoritative locked ~4 weeks. Money computes numbers but has no learning mechanism — `authoritative=false` means it cannot calibrate. |
| **Why not L2** | No learning loop. Fitness scores are computed but never validated against outcomes. Cannot correlate fitness allocation with organism performance. Authoritative=false means it operates on faith, not feedback. |
| **Gap to L2** | Close the feedback loop: track allocation outcomes → validate fitness weights → update authoritative status. Without this, Money is a calculator, not a financial nervous system. |

---

### Organ 9 · LEARNING — L0: Scaffold Only

| Attribute | Detail |
|---|---|
| **Rating** | **L0** |
| **What it knows** | Nothing at runtime. Code exists but is gated off. |
| **Evidence** | `hebbian.py` has real math (weight matrix, decay, fire-together-wire-together) but behind `OCTOPUS_WIRE_NEURAL=0`. Even if enabled: no disk persistence — all in-memory, lost on restart. `consolidation.py` behind `WIRE_CONSOLIDATION`. Phase 3: "math exists but produces nothing observable. No state written anywhere." |
| **Why not L1** | Code does not execute at runtime. If enabled, the HebbianAssociator would be L1 (knows its own weight matrix). But it cannot persist across restarts, so even then its awareness would reset every boot. |

---

### Organ 10 · EPISTEMICS — L0: Scaffold Only

| Attribute | Detail |
|---|---|
| **Rating** | **L0** |
| **What it knows** | Nothing. Numbers are explicitly meaningless. |
| **Evidence** | `run_offloop.py` line 1: **"Numbers are MEANINGLESS until Phase 1-3 fill upstream data."** Line 6: **"Do NOT wire into the loop before Phase 5."** Behind `OCTOPUS_WIRE_EPISTEMICS=0`. Even if enabled: `channel()` passes empty list (line 32). `read_self_vs_twin()` returns zeros. |
| **Why not L1** | Scaffold explicitly documented as non-authoritative. If upstream data existed, it would compute 5 metrics (identifiability, channel, levels, self-reference, method) — that would be L1 at best (knows its own metrics). But no upstream data, no flag, no runtime. |

---

### Organ 11 · SELF-MODEL — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Writes 12 fields to ORGANISM-STATE.json every tick: `ts`, `started`, `epoch_mode`, `halted`, `frozen`, `stop_organism`, `month` (spend), `today` (spend), `suspect_zero_total`, `conflicts`, `germline_lag_h`. |
| **What it does not know** | Its own organ health. Its own architecture. Why it is in a given state. What its goals are. What "healthy" looks like. Whether it is improving or degrading. |
| **Evidence** | `ORGANISM-STATE.json` (423 B, read 2026-07-09T23:28:36): only the 12 fields listed above. organism.py line 376-379 `_write_state()`: writes `month`, `today`, `suspect_zero_total`, `conflicts`, `germ`, `epoch_info`, `daily`, `pulse`, `prot_state`. No "why", no "what next", no goals, no architecture model, no organ-level health summary. |
| **Why not L2** | Self-model does not model itself. It writes a flat JSON with scalar fields. It does not know: (a) which organs exist, (b) which are healthy, (c) which are dead, (d) what the system architecture is. It is a telemetry dump, not a self-model. The name is aspirational. |
| **Gap to L2** | Add organ-level health fields (per-organ status, uptime, last_error). Add architecture summary (which organs exist, which are enabled). Add a compact representation of the organism's structure. |
| **Gap to L3** | Would need to maintain persistent health trends, not just point-in-time values. Compare current state to historical baselines. Detect anomalies in organ health trajectories. |

---

### Organ 12 · WATCHDOG — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Port alive/dead (socket probe on 8771). STOP flag state. Whether ORGANISM-STATE.json exists (first-birth guard). |
| **What it does not know** | WHY the organism died. WHAT was happening before death. Whether the death is a pattern. How to prevent recurrence. Whether the revive succeeded. |
| **Evidence** | `watchdog.py` line 39 `should_revive()`: checks `port_alive`, `stop_flags`, `state_exists`. Returns `(bool, reason)`. `watchdog.log`: 2 entries (2026-07-07, 2026-07-08) showing revivals. But the reason string is generic: `"alive"` or `"yield: STOP flag present"`. No diagnostic payload. No crash log analysis. |
| **Why not L2** | No inter-module awareness. Does not check organ health. Does not read ORGANISM-STATE before/after death to understand what happened. Cannot correlate deaths with Governor pressure, Doctor cycles, or memory state. |
| **Gap to L2** | On death: snapshot ORGANISM-STATE, last epoch, last doctor cycle, ledger tail. On revive: compare pre-death and post-revive state. Report death patterns to Doctor. |
| **Gap to L5** | Cannot explain WHY organism died. Cannot distinguish "crashed due to OOM" from "killed by STOP flag" from "network glitch" — all are `(False, reason)` with no diagnostic depth. |

---

### Organ 13 · SENSORS — L1: Local State Awareness (Stub)

| Attribute | Detail |
|---|---|
| **Rating** | **L1** (stub classifier reduces effective awareness) |
| **What it knows** | Classification labels for observations. Rule-based classifier (not LLM). |
| **What it does not know** | Why observations matter. How they connect to system health. Whether classifications are accurate. |
| **Evidence** | Behind `OCTOPUS_WIRE_SCHOOL=0`. Classifier noted as "stub" in Phase 3: rule-based, not LLM. Ingestion code exists but produces trivial output. If enabled, would classify observations but not reason about them. |
| **Why not L2** | No neighbor awareness. Does not feed classified observations into the system model. Does not correlate observations with organ health or Governor pressure. |
| **Runtime rating** | **L0** — gated off. Same as Learning. If enabled, would be L1 at best (knows its own classifications). |

---

### Organ 14 · CAPABILITY LAYER — L1: Local State Awareness

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | All WIRE_* flags and their states. Which subsystems are enabled/disabled. Boot profile (paper-full, bare, live). `wire_summary()` produces real flag dict. |
| **What it does not know** | Why certain flags are off. What turning a flag on would do to system health. Whether the current configuration is optimal. What the dependency graph between flags looks like. |
| **Evidence** | `wiring.py` line 29 `flag()`: reads env, returns bool. Line 41-49 `PAPER_FULL_FLAGS`: 12 flags. Line 52 `resolve_profile()`: reads `OCTOPUS_PROFILE`. Line 60 `apply_profile()`: sets flags on boot. Knows flags, knows profile. No reasoning about implications. |
| **Why not L2** | No inter-module awareness. Does not check whether enabled subsystems are actually healthy. Does not flag configuration anomalies (e.g., WIRE_DOCTOR=1 but Telegram dead → Doctor cannot submit). No dependency validation. |
| **Gap to L2** | Validate flag combinations against system health. Warn when enabled subsystems are blocked by missing dependencies. Track configuration changes over time. |

---

### Organ 15 · BOX AGENTS — L1: Internal Dynamics Only

| Attribute | Detail |
|---|---|
| **Rating** | **L1** |
| **What it knows** | Internal agent dynamics: cognitive, psych, energy layers. Agent-to-agent interactions. Warden gate (2% mutation, STOP-obey). In-memory state of 12 sub-agents. |
| **What it does not know** | External system state. Whether its simulations map to real organism behavior. Whether its proposals are useful. The real-world consequences of its simulated mutations. |
| **Evidence** | `doctor/box/` (12 files). `box.py` (147 LOC). All in-memory, no disk persistence. Behind `OCTOPUS_WIRE_BOX=0`. Phase 3: "real math, real agent interactions, but all evaporates on restart." |
| **Why not L2** | No connection to external system. Does not read ORGANISM-STATE, epochs, or ledger. Cannot correlate its internal dynamics with real organism behavior. A closed world with no sensors. |
| **Runtime rating** | **L0** — gated off. If enabled, would be L1 (knows internal dynamics). Would need external state input to reach L2. |

---

## 3 · Awareness Matrix (Summary)

| Organ | Rating | Knows | Does Not Know | Runtime? |
|---|---|---|---|---|
| HEART (Pacemaker) | **L1** | beat_seq, phi, HLC, metabolic_age | Why it beats, what other organs do | Yes |
| HEART (Cardiac) | **L0** | (gated off) | Everything | No |
| DOCTOR | **L2** | Bottlenecks, severity, sandbox results | Why bottlenecks recur, own success rate | Yes (core) |
| GOVERNOR | **L3** | All fitness scores, pressure, deadlines, allocations | Whether allocations work, system goals | Yes |
| LEGS (Base) | **L1** | Budget reservation, allowlist | Why, what for, outcomes | Yes |
| LEGS (Lead) | **L1** | Attribution, quotes, revenue (all $0) | Pipeline health, conversion rates | Gated |
| TELEGRAM | **L0** | Nothing (dead) | Everything | No |
| MEMORY (Ledger) | **L0** | Nothing (passive pipe) | Everything (it is infrastructure) | Yes (but passive) |
| MEMORY (Cockpit) | **L0** | (dead via Telegram) | Everything | No |
| GATES | **L1** | Pass/fail state, capability checks | Why denials happen, denial patterns | Yes |
| MONEY | **L1** | Fitness scores, attribution | Whether scores are accurate (auth=false) | Yes (simulated) |
| LEARNING | **L0** | (gated off) | Everything | No |
| EPISTEMICS | **L0** | (scaffold, explicitly meaningless) | Everything | No |
| SELF-MODEL | **L1** | 12 scalar fields | Architecture, organ health, goals, why | Yes |
| WATCHDOG | **L1** | Port alive/dead, STOP flags | Why death happened, death patterns | Yes (external) |
| SENSORS | **L0** | (gated off) | Everything | No |
| CAPABILITY LAYER | **L1** | All WIRE_* flags, boot profile | Flag interaction effects, config validation | Yes |
| BOX AGENTS | **L0** | (gated off) | External system state | No |

---

## 4 · System-Wide Rating: L2

### The organism as a whole operates at L2 — Inter-Module Awareness.

**What the system knows collectively:**
- Governor knows all organs' fitness scores and budget allocations.
- Doctor reads organism state and telemetry to mine bottlenecks.
- Self-model writes 12 fields to ORGANISM-STATE.json every tick.
- Watchdog knows port alive/dead.
- Ledger records all events (passive but comprehensive).

**What the system does NOT know collectively:**

| Missing Capability | Evidence | Why It Matters |
|---|---|---|
| **Why things are the way they are** | No causal reasoning anywhere. Doctor mines symptoms, not causes. Governor computes pressure, not etiology. | Cannot prevent recurring failures. Cannot distinguish root cause from surface symptom. |
| **Whether it is achieving goals** | ORGANISM-STATE.json has no goal fields. No objective function beyond "don't overspend." | Cannot evaluate progress. Cannot prioritize actions by impact. |
| **Its own architecture** | Self-model writes 12 scalars. No organ topology. No dependency graph. No capability map. | Cannot reason about missing organs or broken dependencies. Cannot self-diagnose architectural gaps. |
| **What it does not know** | No uncertainty quantification. Epistemics scaffold explicitly says "numbers are MEANINGLESS." | Cannot flag blind spots. Cannot request human help for unknown unknowns. |
| **How to adapt based on outcomes** | No feedback loop from allocation → outcome → strategy change. Governor runs the same algorithm every epoch. Doctor proposes fixes but never learns whether they worked. | Strategy is static. Improvement is accidental, not intentional. |
| **How to propose safe improvements** | Doctor proposes RFCs but cannot explain expected system-level impact. No architectural reasoning. | Proposals are local fixes, not systemic improvements. No safety case for architectural changes. |

### Why L2 and not L3:

L3 requires a *persistent, integrated model of all organs' health*. The system has fragments of this:
- Governor knows fitness scores per organ (L3 fragment).
- Doctor knows bottleneck snapshots (L2 fragment).
- Watchdog knows alive/dead (L1 fragment).

But these fragments are not integrated. There is no single place that answers "how healthy is the organism?" ORGANISM-STATE.json has 12 scalar fields, none of which describe organ-level health. The Governor's epoch files have per-organ allocation data, but no health status. No organ reports its own health in a standard format consumed by others.

**The organism lacks a nervous system.** It has organs that independently compute local metrics, but no integrative center that synthesizes these into a system-level health model. The closest thing is Governor (L3 fragment), but it only knows budget fitness — not runtime health, not error rates, not dependency status.

---

## 5 · Critical Awareness Gaps (Ranked by Impact)

### Gap 1: No Causal Reasoning (L2 → L5 blocker)

The system can detect symptoms but cannot infer causes. Doctor finds "effects-stuck: 7 pending" but cannot ask "why are effects stuck? Is the approval channel dead? Is the human offline? Is the sandbox crashing?"

**Impact**: Every fix proposal is a guess, not a diagnosis. The organism treats symptoms, not diseases.

**What's needed**: A causal inference layer that connects symptoms to root causes using the event graph (idea_graph.py exists but is gated off) and ledger history.

### Gap 2: No Goal Model (L2 → L4 blocker)

ORGANISM-STATE.json has zero goal-related fields. The organism's purpose (survival via append-only genome) is documented in design docs but not encoded in any runtime state.

**Impact**: The organism cannot evaluate whether its actions serve its purpose. Every allocation, every RFC, every heartbeat is purposeless from the system's own perspective.

**What's needed**: A goal register in ORGANISM-STATE.json: `{"goals": [...], "progress": {...}}`. Even a simple "last successful RFC merge date" or "days since last human interaction" would be a start.

### Gap 3: No Outcome Feedback (L2 → L6 blocker)

No closed loop from action → outcome → strategy adjustment. Governor allocates but never measures whether allocation helped. Doctor proposes but never learns whether fixes worked (Telegram dead → no approval → no merge → no outcome).

**Impact**: The system cannot learn from experience. Every epoch is independent. Every doctor cycle is independent. No compound improvement.

**What's needed**: Track allocation → outcome latency. Track RFC → approval → measured_lift pipeline. Feed outcomes back into fitness weights.

### Gap 4: No Architecture Self-Model (L2 → L7 blocker)

The system does not know its own structure. It cannot answer: "which organs are alive?" "which depend on Telegram?" "what breaks if I disable WIRE_DOCTOR?"

**Impact**: Cannot reason about its own limitations. Cannot propose safe architectural changes. Cannot self-diagnose systemic failures (e.g., "everything is slow because Telegram is dead and 5 organs depend on it").

**What's needed**: An architecture map in runtime state: organ topology, dependency graph, capability matrix, current health per organ. Phase 2's organ map exists on paper — it needs to exist in ORGANISM-STATE.json.

### Gap 5: No Uncertainty Awareness (L2 → L5 blocker)

Epistemics is scaffold-only with explicitly meaningless numbers. No module reports confidence intervals or uncertainty. MONEY operates on `authoritative=false` fitness scores without flagging the uncertainty to downstream consumers.

**Impact**: The system makes decisions on data it knows is unreliable, but cannot articulate that unreliability. Cannot request human help for ambiguous situations.

**What's needed**: Uncertainty propagation from upstream (fitness, telemetry) to downstream (Governor, Doctor). Confidence-weighted decision making.

---

## 6 · Awareness Distribution Visualization

```
L7 ████████████████████ Meta-Awareness         — empty
L6 ████████████████████ Adaptive Awareness     — empty
L5 ████████████████████ Reflective Awareness   — empty
L4 ████████████████████ Goal Awareness         — empty
L3 ██░░░░░░░░░░░░░░░░ System Awareness         — GOVERNOR only
L2 ███░░░░░░░░░░░░░░░ Inter-Module Awareness   — DOCTOR (core)
L1 ██████████████░░░░░ Local State Awareness   — Pacemaker, Legs, Gates,
                                                Money, Self-Model, Watchdog,
                                                Capability Layer
L0 ████████████████████ No Awareness            — Cardiac (gated), Telegram,
                                                Ledger (passive), Cockpit,
                                                Learning, Epistemics,
                                                Sensors, Box Agents
```

**Observation**: The distribution is bottom-heavy. 11 of 18 organs (61%) are at L0 or effectively L0 (dead/gated/passive). The most aware organ (Governor at L3) is still 4 levels below adaptive or meta-awareness. The system has no organ above L3.

---

## 7 · Comparison: What L4+ Would Require

| Level | Minimum Requirement | Current Status | Gap |
|---|---|---|---|
| **L4 (Goal)** | ORGANISM-STATE.json contains goals + progress. At least one organ connects actions to objectives. | No goal fields anywhere in runtime state. | Add goal register. Wire Governor allocations to organism goals. |
| **L5 (Reflective)** | At least one organ can explain failures and flag uncertainty. Doctor can say "I don't know why this recurs." Epistemics is live with real upstream data. | Doctor is stateless. Epistemics is scaffold with "MEANINGLESS" numbers. | Close feedback loop. Enable epistemics with real data. Add uncertainty reporting to Doctor. |
| **L6 (Adaptive)** | At least one organ changes strategy based on outcome history. Governor adjusts weights based on allocation outcomes. | No outcome tracking anywhere. Same algorithm every epoch/cycle. | Add outcome measurement. Feed back into fitness/pressure/allocation. |
| **L7 (Meta)** | At least one organ can reason about the system's architecture and propose safe changes. Architecture map in runtime. | No architecture self-model. Self-model is 12 scalar fields. | Build architecture map in ORGANISM-STATE. Add causal reasoning. Enable Doctor to propose architectural (not just local) fixes. |

---

## 8 · Key Code Evidence Index

| Evidence | Location | Relevance |
|---|---|---|
| ORGANISM-STATE.json (12 fields) | `_ops/state/ORGANISM-STATE.json` | Self-model is L1 — flat scalars, no goals, no architecture |
| "Numbers are MEANINGLESS" | `_ops/epistemics/run_offloop.py:1-6` | Epistemics is L0 scaffold |
| Doctor mine() — stateless bottleneck scan | `_ops/doctor/doctor.py:227-259` | Doctor is L2 — detects symptoms, not causes |
| Governor pressure_state() | `_ops/budget/governor_epoch.py:59-60` | Governor is L3 — knows all organs' fitness |
| Watchdog should_revive() | `_ops/watchdog.py:39-60` | Watchdog is L1 — port alive/dead, no diagnosis |
| Cardiac get_layer() returns None | `_ops/cardiac.py` (flag=0) | Cardiac is L0 — unreachable code |
| Ledger append-only | `opslib.ledger_note()` | Ledger is L0 — passive pipe, no awareness |
| Wiring apply_profile() | `_ops/wiring.py:60` | Capability Layer is L1 — knows flags, not implications |
| Hebbian no persistence | `_ops/neural/hebbian.py` (WIRE_NEURAL=0) | Learning is L0 — gated, in-memory only |
| Governor epoch — no outcome tracking | `_ops/budget/governor_epoch.py:1-26` | No L6 — same algorithm every epoch |
| Doctor run_cycle() — no feedback loop | `_ops/doctor/doctor.py:473-539` | No L6 — proposes fixes, never measures outcomes |
| Telegram channel-status | `channel-status.json: {live: false}` | Telegram is L0 — dead, 881 lines unreachable |
| organism.py _write_state() | `_ops/organism.py:376-379` | Self-model writes 12 fields, nothing more |

---

**PHASE 4 COMPLETE.**

*Summary: The Octopus organism operates at system-wide L2 (Inter-Module Awareness). 11 of 18 organs are at L0 (dead, gated, or passive). The most aware organ (Governor, L3) knows all organs' budget fitness but cannot reason about goals, outcomes, or its own architecture. No organ exceeds L3. The system can detect symptoms but not infer causes, can allocate budgets but not measure effectiveness, and can report state but not explain itself. The five critical gaps are: (1) no causal reasoning, (2) no goal model, (3) no outcome feedback, (4) no architecture self-model, and (5) no uncertainty awareness. Reaching L4 requires a goal register; L5 requires epistemics with real data; L6 requires outcome feedback loops; L7 requires an architecture map in runtime state.*

*Next: PHASE 5 — Failure Mode Analysis (cascade detection, silent failure inventory, recovery gaps).*
