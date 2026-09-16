---
title: "Octopus — Phase 3: Vital Signs & Power State"
date: 2026-07-09
status: EVIDENCE-BACKED
confidence: HIGH
depends_on: Phase 1 (Repo Autopsy), Phase 2 (Organ Map)
---

# PHASE 3 — VITAL SIGNS & POWER STATE

> *Determine for each organ: ON/OFF/UNKNOWN, startup/shutdown path, blockers, fake vs real liveness.*

---

## 1 · POWER STATE MATRIX

### Legend
| Symbol | Meaning |
|---|---|
| 🟢 **ON — Real** | Code executes every tick. State changes observed in runtime files. |
| 🟡 **ON — Simulated/Limited** | Code runs but output is no-op, stub, or propose-only. |
| 🔴 **OFF — Gated** | Flag/env missing. Code exists but never executes. |
| ⚫ **OFF — No Implementation** | Not implemented. Only concept or declaration. |
| ❓ **UNKNOWN** | Cannot determine from evidence. |

---

## 2 · Per-Organ Power State

### Organ 1 · 🫀 HEART — Pacemaker

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real** |
| **Evidence** | chrono.db has heartbeat/leg_clock tables with data. `beat_seq` is monotonically increasing. organism.py line 199 starts pacemaker thread. ORGANISM-STATE.json shows chrono fields. |
| **Startup** | `chrono.start_pacemaker_thread()` in organism.py main() |
| **Shutdown** | Daemon thread — dies with process. No explicit stop. |
| **Blockers** | None. |
| **Fake vs Real** | **Real** — SQLite writes, real phi/HLC computation, real thread. |
| **What controls it** | Nothing — always on. No flag, no env, no gate. |

### Organ 1b · 🫀 HEART — Cardiac

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — Gated** |
| **Evidence** | `OCTOPUS_WIRE_BIO` defaults to 0. `get_layer()` returns `(None, None)` when flag off. |
| **Startup** | `cardiac.get_layer()` called in organism.py after wiring (only when flag=1) |
| **Shutdown** | Flag=0 → None returned → base TICK_SECONDS used |
| **Blockers** | `OCTOPUS_WIRE_BIO=1` must be set in OCTOPUS.env |
| **Fake vs Real** | Would be **Real** if enabled — complete Kleiber/BeatBudget/Baroreflex logic. Currently inert. |
| **What controls it** | `OCTOPUS_WIRE_BIO` env var. |

### Organ 2 · 🩺 DOCTOR

| Attribute | Detail |
|---|---|
| **State** | 🟡 **ON — Limited** (core cycle daily; box/evolution gated) |
| **Evidence** | doctor.py `run_cycle()` called every 1440 beats (~daily) via wiring.doctor_beat(). Core mine→propose→sandbox→submit cycle runs. Box/Evolution behind WIRE_BOX/WIRE_EVOLUTION (default off in paper-full). |
| **Startup** | `make_doctor()` in wiring.py behind `OCTOPUS_WIRE_DOCTOR` (default on) |
| **Shutdown** | Flag=0 → doctor=None → doctor_beat skips |
| **Blockers** | For box: `OCTOPUS_WIRE_BOX=1`. For evolution: `OCTOPUS_WIRE_EVOLUTION=1`. |
| **Fake vs Real** | **Real** for core cycle (real file scanning, real sandbox subprocess, real ledger writes). **Simulated** for box (in-memory only, no persistence). |
| **What controls it** | `OCTOPUS_WIRE_DOCTOR` (on/off), `OCTOPUS_WIRE_BOX`, `OCTOPUS_WIRE_EVOLUTION` (sub-features). |

### Organ 3 · 🏛️ GOVERNOR

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real** |
| **Evidence** | 45 epoch JSON files in `budget/epochs/`. governor_epoch.py called every tick (organism.py line 276). Real pressure computation, real dry allocation, real ledger writes. |
| **Startup** | Always called in tick loop — no flag gate. |
| **Shutdown** | Cannot be turned off (by design). |
| **Blockers** | LLM mode: `ACTIVATION-GOVERNOR-LLM.flag` + date gate. Barbell: `OCTOPUS_WIRE_BARBELL`. Debate: `OCTOPUS_WIRE_DEBATE`. Dry mode always runs. |
| **Fake vs Real** | **Real** — dry allocation produces real epoch files. LLM/barbell/debate modes are sub-gated. |
| **What controls it** | Dry mode: unconditional. LLM: ACTIVATION-GOVERNOR-LLM.flag. Barbell: WIRE_BARBELL. Debate: WIRE_DEBATE. |

### Organ 4 · 🦵 LEGS (Base)

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real** (base class always loaded) |
| **Evidence** | leg.py imported by lead_leg.py. Structural constraints (no wildcards, no secrets) enforced at init. |
| **Startup** | Always imported (no flag). |
| **Shutdown** | N/A — base class, not instantiated directly. |
| **Fake vs Real** | **Real** — constraints are enforced. But no leg instances created without WIRE_LEAD. |
| **What controls it** | No flag for base class. |

### Organ 4b · 🦵 LEGS (Lead)

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — Gated** |
| **Evidence** | `OCTOPUS_WIRE_LEAD` default in paper-full is 1, but no confirmed revenue (fitness-latest.json: confirmed=0). LeadLeg exists but no leads have been confirmed. |
| **Startup** | `make_lead_leg()` behind `OCTOPUS_WIRE_LEAD` |
| **Shutdown** | Flag=0 → LeadLeg=None |
| **Blockers** | WIRE_LEAD flag. Also: no real Telegram channel → no lead intake from humans. |
| **Fake vs Real** | **Simulated** — code works, propose-only lifecycle, but zero real leads in system. |
| **What controls it** | `OCTOPUS_WIRE_LEAD`, `OCTOPUS_WIRE_LEAD_TICK` |

### Organ 5 · 📡 TELEGRAM

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — Missing Credentials** |
| **Evidence** | channel-status.json: `{live: false, mode: "stub(no-creds)"}`. Required env: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID` — neither set. |
| **Startup** | wiring.py line 121: auto-on IF token exists in env |
| **Shutdown** | Token not present → TelegramChannel=None → stub transport |
| **Blockers** | `TELEGRAM_BOT_TOKEN` env var must be set. Owner chat ID required. |
| **Fake vs Real** | **Fake** — 881 lines of approval_channel.py are unreachable. No messages sent, none received. |
| **What controls it** | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID` env vars. |

### Organ 6 · 🧠 MEMORY (Ledger)

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real** |
| **Evidence** | ledger.jsonl exists in genome-system. opslib.heartbeat() writes HEARTBEAT.md every hour. opslib.ledger_note() called by governor, doctor, debate. |
| **Startup** | Always available via opslib.genome_ledger(). |
| **Shutdown** | N/A — append-only file, always writable. |
| **Blockers** | None. human_append_guard prevents unauthorized writes. |
| **Fake vs Real** | **Real** — confirmed writes every tick. |
| **What controls it** | Nothing — always on. |

### Organ 6b · 🧠 MEMORY (Cockpit)

| Attribute | Detail |
|---|---|
| **State** | ❓ **UNKNOWN — Unclear if Invoked** |
| **Evidence** | cockpit.py has real text-generation logic (status, approval queue, alarms, daily brief). P-L6 gate ensures no divergence from authoritative source. But no evidence of Telegram bot calling cockpit.render() in production. |
| **Startup** | Depends on Telegram channel (dead). |
| **Shutdown** | Telegram dead → cockpit unreachable. |
| **Blockers** | Telegram channel must be live. |
| **Fake vs Real** | **Fake** — code exists but never invoked. No evidence of cockpit output in any log/state. |
| **What controls it** | Telegram channel (Organ 5). |

### Organ 7 · 🔒 GATES

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real** |
| **Evidence** | CAPABILITY-OK.flag exists (1.5 KB, 62 test modules). money_gate.py dual-lock enforced. organism.py protective_halt logic active. organ_gate.py budget reservation active. |
| **Startup** | Always checked — no flag to disable (by design). |
| **Shutdown** | Cannot be disabled (safety-critical). |
| **Blockers** | Missing CAPABILITY-OK.flag → all capabilities blocked. Missing attribution → money denied. |
| **Fake vs Real** | **Real** — but with zero real transactions (all amounts $0). Gates enforce rules even when there's nothing to gate. |
| **What controls it** | Nothing — always enforced. |

### Organ 8 · 💰 MONEY

| Attribute | Detail |
|---|---|
| **State** | 🟡 **ON — Locked/Zero** |
| **Evidence** | fitness-latest.json: authoritative=false, claimed=0, confirmed=0. replication-latest.json: sigma=0.0, live_gate until 2026-07-21. reconcile/: only README.md, no CSVs. |
| **Startup** | Attribution always on. Fitness behind WIRE_FITNESS. Reconcile behind WIRE_RECONCILE. |
| **Shutdown** | Various flags. Replication: live_gate date. |
| **Blockers** | Fitness authoritative locked ~4 weeks. No bank CSVs for reconcile. Replication live_gate until 2026-07-21. |
| **Fake vs Real** | **Simulated** — attribution code runs but produces zero transactions. Fitness computes zeros. Reconcile has no input. |
| **What controls it** | WIRE_FITNESS, WIRE_RECONCILE, replication live_gate date. |

### Organ 9 · 📚 LEARNING

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — No Persistence** |
| **Evidence** | hebbian.py has real math (weight matrix) but no disk persistence — all in-memory, lost on restart. consolidation.py behind WIRE_CONSOLIDATION. Learning contract YAML is a spec, not code. |
| **Startup** | Behind `OCTOPUS_WIRE_NEURAL` |
| **Shutdown** | Flag=0 → no neural stack → no learning |
| **Blockers** | WIRE_NEURAL=1. Even then: no persistence, no real upstream data. |
| **Fake vs Real** | **Fake** — math exists but produces nothing observable. No state written anywhere. |
| **What controls it** | `OCTOPUS_WIRE_NEURAL`, `OCTOPUS_WIRE_CONSOLIDATION` |

### Organ 10 · 📐 EPISTEMICS

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — Scaffold** |
| **Evidence** | run_offloop.py explicitly: "not authoritative until upstream data is live". channel() passes empty list. |
| **Startup** | Behind `OCTOPUS_WIRE_EPISTEMICS` |
| **Shutdown** | Flag=0 → no epistemics computation |
| **Blockers** | WIRE_EPISTEMICS flag. Upstream data not available (fitness authoritative=false, no self-vs-twin, no topology). |
| **Fake vs Real** | **Fake** — scaffold only, all numbers meaningless. |
| **What controls it** | `OCTOPUS_WIRE_EPISTEMICS` |

### Organ 11 · 🪞 SELF-MODEL

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real (Limited)** |
| **Evidence** | ORGANISM-STATE.json written every tick (423 B). Last: 2026-07-09T22:53. Dashboard reads it. But only ~12 fields — no "why", no "what next", no goals. |
| **Startup** | `_write_state()` in organism.py called every tick |
| **Shutdown** | N/A — always written |
| **Blockers** | Limited to what organism.py aggregates. No agent introspection. |
| **Fake vs Real** | **Real but blind** — state is real but organism has no model of its own architecture. It knows its spend and halt/frozen status, not its own organ health or awareness level. |
| **What controls it** | Nothing — always on. |

### Organ 12 · 🐕 WATCHDOG

| Attribute | Detail |
|---|---|
| **State** | 🟡 **ON — Propose Only** |
| **Evidence** | watchdog.log has 2 entries (2026-07-07, 2026-07-08) showing real revivals. But watchdog.py `revive_action()` only proposes — actual restart done by external PS1 script. |
| **Startup** | External — must be run by scheduled task or PS1 script |
| **Shutdown** | Not in organism.py loop — runs independently |
| **Blockers** | Must be launched externally. First-birth guard prevents premature revive. |
| **Fake vs Real** | **Real for detection, fake for action** — detects death correctly but cannot restart unilaterally. |
| **What controls it** | External scheduler. Organism doesn't control its own watchdog. |

### Organ 13 · 👁️ SENSORS

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — Gated** |
| **Evidence** | Behind `OCTOPUS_WIRE_SCHOOL`. Classifier noted as "stub" (rule-based, not LLM). |
| **Startup** | `make_sensory_bus()` behind WIRE_SCHOOL |
| **Shutdown** | Flag=0 → no sensory data flow |
| **Blockers** | `OCTOPUS_WIRE_SCHOOL=1`. Even then: classifier is stub. |
| **Fake vs Real** | **Stub** — ingestion code exists but classifier produces rule-based output. |
| **What controls it** | `OCTOPUS_WIRE_SCHOOL` |

### Organ 14 · ✋ CAPABILITY LAYER

| Attribute | Detail |
|---|---|
| **State** | 🟢 **ON — Real** |
| **Evidence** | wiring.py `apply_profile()` runs on every boot. wire_summary() produces real flag dict. Dashboard reads/writes via OCTOPUS.env. |
| **Startup** | First thing in organism.py main() |
| **Shutdown** | N/A — always on |
| **Blockers** | None. |
| **Fake vs Real** | **Real** — 19 flags actively control subsystem instantiation. |
| **What controls it** | `OCTOPUS_PROFILE` env var + individual WIRE_* flags. |

### Organ 15 · 🧫 BOX AGENTS

| Attribute | Detail |
|---|---|
| **State** | 🔴 **OFF — Gated** |
| **Evidence** | Behind `OCTOPUS_WIRE_BOX=1`. 12 sub-agents have real dynamics but all in-memory. No disk persistence. |
| **Startup** | Called from doctor.py `_run_box_cycle()` behind WIRE_BOX |
| **Shutdown** | Flag=0 → box not instantiated |
| **Blockers** | `OCTOPUS_WIRE_BOX=1`. Also: WIRE_DOCTOR must be on. |
| **Fake vs Real** | **Simulated** — real math, real agent interactions, but all evaporates on restart. No observable output. |
| **What controls it** | `OCTOPUS_WIRE_BOX` |

---

## 3 · Why Each Module Is ON/OFF

### ON because (no flag needed):
- **Pacemaker**: Fundamental — organism needs a heartbeat. Always on by design.
- **Governor (dry)**: Must run every tick for safety — budget pressure detection.
- **Ledger**: Append-only audit trail — always needed.
- **Gates**: Safety-critical — cannot be disabled.
- **Capability Layer**: Controls all other subsystems — must be first.
- **Self-Model**: State output — always needed.
- **Germline**: Backup staleness check — always needed.

### OFF because (flag gated, default off in paper-full):
- **Cardiac**: New feature, still experimental. Flag WIRE_BIO=0 default.
- **Lead Leg**: No human leads yet. Flag WIRE_LEAD=1 but no input.
- **Sensors**: No external data ingestion yet. Flag WIRE_SCHOOL=0.
- **Box Agents**: Experimental micro-world. Flag WIRE_BOX=0.
- **Learning**: No persistence. Flag WIRE_NEURAL controls parent.
- **Epistemics**: Scaffold only. Flag WIRE_EPISTEMICS=0.

### OFF because (missing infrastructure):
- **Telegram**: No `TELEGRAM_BOT_TOKEN`. 881 lines of approval logic unreachable. This is the **biggest single blocker** — without Telegram, the entire human approval pipeline is dead.
- **Cockpit**: Depends on Telegram (dead).
- **Reconcile**: No bank CSV files submitted.

### OFF because (locked by date):
- **Replication live_gate**: Locked until 2026-07-21.
- **Fitness authoritative**: Locked since ~June 2026.
- **Governor LLM mode**: ACTIVATION-GOVERNOR-LLM.flag + date gate.

---

## 4 · Fake Liveness vs Real Liveness

| Organ | Appears Alive | Actually Alive? | Gap |
|---|---|---|---|
| Governor | 🟢 Every tick | 🟢 Dry allocation runs | But: $0 allocation → zero-value math |
| Gates | 🟢 Enforcing | 🟢 Code runs | But: gating $0 transactions |
| Doctor | 🟢 Daily beat | 🟡 Mine runs | But: no RFCs submitted (Telegram dead) |
| Ledger | 🟢 Entries written | 🟢 Real entries | But: all NOTE/HEARTBEAT — no MONEY_ATTRIBUTION |
| Telegram | 🔴 Listed in channel-status | 🔴 Completely dead | 881 lines of unreachable code |
| Self-Model | 🟢 State written | 🟡 Only 12 fields | No organ health, no goals, no awareness |
| Watchdog | 🟢 Log entries exist | 🟡 Detection works | But: cannot actually restart (propose-only) |
| Cardiac | Listed in wiring | 🔴 Flag off | Complete code, zero effect |
| Box Agents | 12 named agents | 🔴 Never instantiated | Rich simulation, zero output |
| Neural / Consolidation | Flag says ON | 🟡 `mean_awareness()` exists | But: caller cannot distinguish "nothing to do" from "consolidation failed" — both return None (wiring.py:675, 719) |

**Key Finding**: The organism has a **liveness illusion** — many subsystems appear active because they have code and are called in the tick loop, but they produce zero real-world value because:
1. Telegram is dead → no human interaction → no approvals → no money → no leads
2. All financial values are $0 → gates enforce rules on nothing
3. Ledger records heartbeat ticks but no real transactions
4. Doctor mines for bottlenecks but cannot submit RFCs (no channel)

---

## 5 · Silent Failures Detected

| Failure | Evidence | Severity |
|---|---|---|
| Watchdog revived organism twice (07-07, 07-08) | watchdog.log: 2 entries | 🟡 Organism died silently twice |
| Telegram channel dead since inception | channel-status.json: stub(no-creds) | 🔴 Largest single blocker |
| Fitness authoritative locked 4+ weeks | fitness-latest.json: authoritative=false | 🟡 No fitness signal |
| Reconcile directory empty | Only README.md, no CSVs | 🟡 No financial reconciliation |
| Epoch files growing unbounded (45 files, no rotation) | `ls epochs/` → 45 JSONs | 🟢 Low (disk space ok) |
| `_ops/reconcile/` ghost directory | Only README.md, logic in budget/ | 🟢 Low (cosmetic) |
| `Untitled.base` at root | 9-line Obsidian artifact | ⬜ Noise |
| `gitwrite.lock` possibly stale | 67 bytes, no creator code found | 🟢 Low |

---

**PHASE 3 COMPLETE.**

*Next: PHASE 4 — Awareness Analysis (L0–L7 per organ and system-wide).*
