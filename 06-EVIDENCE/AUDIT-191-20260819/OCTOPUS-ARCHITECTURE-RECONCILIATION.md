# OCTOPUS-ARCHITECTURE-RECONCILIATION — mapping the live tree into the nine-layer organism

Basis: 2026-08-19 audit + `ARCHITECTURE-SOT.md` (verdict 2026-07-18) + `DISCOVERY — Unwired & Dead Paths Catalog` (2026-08-16) + Deep-Seams/Improve ledgers. Principle: **only `_ops/` is the live organism; `4d_system` is a separate live brain daemon; everything else is dormant/visualization/research unless a runtime trace proves otherwise.** No merges proposed without evidence + migration + rollback.

## 1. Layer map (what exists, where it lives, wired state)

### A. Homeostatic Core — PARTIAL, SPLIT ACROSS TWO ORGANISMS
| Component | Location | State |
|---|---|---|
| Organism heartbeat/coherence, stop/freeze/recover, HALT-ALL, STOP-ORGANISM | `_ops/organism.py` (8771), `opslib.freeze()`, watchdogs (5× ps1) | **LIVE** (beat 37781, coherence 0.972 per 08-16 catalog) |
| Budget metabolism (organ_gate, budget_gate, budgets.yaml, FX pin) | `_ops/budget/` | **LIVE** (freeze incident fixed; receipts on paid path) |
| 4d daemon health (ticks, daemon_state.json, stop/pause files, signals) | `4d_system/brain/daemon.py` | **LIVE** (PID 18020) |
| Stability dashboard | `_ops/live/server.py` (8773 cockpit) | LIVE (per SOT) |
| `control_plane/supervisor.py` (~400 lines, 24/7 self-heal loop) | `4d_system/control_plane/` | **NEVER-WIRED** (only `__main__`+tests; no schtask) |
| `state_guard.py` (391 lines), `watchdog_extension.py`, `stop_probe.py` | `_ops/` | **ORPHAN** (only a comment references state_guard) |

### B. World Model — FRAGMENTED, PARTIALLY REALIZED
| Component | Location | State |
|---|---|---|
| Machine world-state registry (versioned, expiring, provenance-carrying labels) | `_ops/state/labels.json` + label-history.jsonl | **LIVE — this IS the world model's fact layer** (50 labels, expiry, supersedes) |
| 4d internal model (SOG math, anchors, self-model, frontier) | `4d_system/brain/`, `core/model.py` | LIVE-in-daemon; math anchors guarded in `_ops/heart/sog_math` but **TCB core still has the unguarded DARE ZeroDivision** (VOTE A, Improve ledger) |
| ORGANISM-STATE.* snapshots (13 domains) | `_ops/state/` | LIVE |
| belief/world pages in Obsidian | vault | advisory only (documentation, not runtime) |
| Contradiction handling | `contradiction_radar.py` + gate hook | **EXISTS, NOT WIRED** (biggest World-Model seam) |

### C. Memory Spine — STRONG CORE, TWO KNOWN GAPS
| Component | Location | State |
|---|---|---|
| Canonical graded store (23-col schema, FTS5, admission states) | `_ops/state/memory/memory.db` (508 rows) | **LIVE**, single write path through MemoryGate (`gate.py:182`) |
| Two-phase Admission + radar + quarantine | `_ops/memory/admission.py` | **CODED, NOT WIRED** (test-only import) |
| Raw ingest trails (self-loop, research, semantic) | `_ops/state/*.jsonl` | LIVE, correctly non-canonical |
| Prediction ledger (append-only, triggers) | `_ops/state/predictions.db` | **LIVE, tamper-evident** |
| 4d hypotheses/patterns/experiments | `4d_system/outputs/4d_experiments.db` (1439 hypotheses) | LIVE but **bypasses graded gate by design** (write_gate_enforcer compensates) |
| Consolidation | `_ops/neural/consolidation.py` (625 cycles) **and** `4d_system/brain/consolidation.py` (**NEVER-WIRED twin**) | **DUPLICATION** — the 4d fork is dead code with a false docstring (ERRATA'd 08-16) |
| Vector store | `chroma_db` + `_ops/…/vectorstore.py` ingesting semantic_memory.jsonl | LIVE as retrieval aid, non-canonical |
| Genome ledger | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | append-only hash-chain, LIVE |

### D. Hypothesis & Evolutionary Doctor — EMBRYONIC, MOSTLY ORPHANED
| Component | Location | State |
|---|---|---|
| Live-4 paired-hypothesis engine (evidence-conditioned vs baseline, VOID policy) | `06-EVIDENCE/CL01-191…/live4/` driver+harness+fg_runner | **LIVE — the only loop closing OBSERVATION→…→EVALUATION today** |
| Idea generation / dedup / self-transformation gating | `4d_system/brain/` (autoloop, self_evolve, hypotheses) | LIVE-in-daemon but producing **0 recorded predictions/proposals** this run (novelty gate blocks repeats) |
| `hypothesis_engine/experiments/analysis.py` (422 lines) | `_ops/` | **ORPHAN** (zero production imports — VOTE 1, Deep-Seams) |
| `auto_experiment.suggest_next_experiment` | `4d_system/brain/auto_experiment.py` | **NEVER-WIRED** (only self-reference) |
| meta_research / web_research | `4d_system/brain/` | UI-only; UI process not running |
| Councils (Architecture/Epistemic, ProtocolRunner, PEP) | `4d_system/councils/` | **DEAD-BY-DESIGN** (shadow/vote-seeking, zero production trigger) |
| OCTOPUS-DOCTOR (self-knowledge, box primitives) | `_ops/doctor/` | partially live (doctor-day task) |

### E. Metacontrol Gate — MINIMAL BUT PRESENT
| Component | Location | State |
|---|---|---|
| Capability/evidence/reversibility assessment, executable=false enforcement | `_ops/…/wiring.py` (executable default False), `autonomy_matrix.py`, `auto_approve.py`, `prereg.py` forbidden-list | **LIVE** — PROPOSE_ONLY enforced by code+tests; autonomy ruling 2026-07-16 (free vs important) implemented |
| Domain skill/evidence scoring per action | partial (critic_shadow scores on paid calls) | OBSERVED — scoring exists on the LLM path only |

### F. Policy & Execution Boundary — STRONG
| Component | Location | State |
|---|---|---|
| Hard stops (TCB mismatch, cost-unknown, receipt-missing, bypass, metadata, forbidden action, HALT-ALL) | guardrails.py, cost_receipt.py, admission.py, prereg.py, opslib.py | **LIVE** (all six verified in audit I12) |
| Raw shell capability | `_ops/shell_capability.py` | DISARMED + fail-closed tested |
| External effect receipts | paid-calls/cost-receipts/tg-send logs | LIVE |

### G. Execution (effectors) — NARROW BY DESIGN
- Telegram send (`_ops` center, 2011 rows/7d) — LIVE.
- Paid LLM calls (DeepSeek metered) — LIVE, reserved/deferred under Live-4 windows.
- 4d telegram_bot — DEAD-BY-DESIGN (409 guard); digest queue 24/0 sent (VOTE 4).
- Boards/SSH/actuators — NO_CONTACT (enforced).

### H. Observability — GOOD ON PAID PATH, GAPS ELSEWHERE
- Cost/receipt observability (COST-OBS-1) — LIVE inline, 82/82 complete; three wiring gaps (paid_blocked read, FX expiry general path, fallback-leg receipt) + the budget_before bug.
- Registry/NOW.md — LIVE with deterministic renderer (new `render_now.py`).
- Windows tasks: Observatory Hourly + doctor-day + germline-hourly green; **4d Consolidation Tick + Poisoning Watch + LiveDataRefresh failing/never-run** (`py` launcher PATH issue — FILE_NOT_FOUND pattern); http.server :8765 zombie (undeclared member since 08-14).
- Daemon event log — LIVE (Persian events, 4k+ lines/run).

### I. Hardware / Sensorium — DOCUMENTED AMBITION, ZERO VERIFIED RUNTIME
- .191 laptop = the only verified node (this is where everything above runs).
- .138/.180/.182 Orange Pi roles documented; .180 explicitly never started; no live probes in scope.
- ESP32 pool: no inventory, no pilot contract, no MQTT/NATS decision. **Nothing to reconcile yet — this layer is paper.**

## 2. Duplication / orphans / dead code / missing seams (ranked)

1. **Consolidation twin** — `_ops/neural` (live, 625 cycles) vs `4d_system/brain/consolidation.py` (never-wired). Keep `_ops` canonical; retire or wire the 4d fork only with a scheduler-free trigger (its Windows task exists but never ran — fix `py`→absolute python.exe first if kept).
2. **18 weighty orphan `_ops` modules** (experiments/analysis 422, epistemics/benchmark 407, state_guard 391, phase_gate 362, agent_gateway_http 353 …) — decide wire-or-retire per Deep-Seams VOTE 1 pattern; do not delete (negative knowledge has value; mark STATUS retired).
3. **LLM routing triple** — canonical `_ops/cortex/model_router.py`; dormant `4d_system/llm/router.py` + `survival-gateway/`. Keep single canonical; the 4d daemon's own clients (fugu/glm/ollama) are budget-gated but duplicate provider logic — unify behind model_router only with evidence.
4. **Math core divergence** — guarded `_ops/heart/sog_math` vs unguarded TCB `core/model.py` (DARE ZeroDivision; I_pred anchor not checked in run_self_test). Owner TCB ceremony required (VOTE A/B).
5. **Missing seam: radar → gate** (contradiction handling promised, unwired).
6. **Missing seam: 4d brain → prediction ledger** — daemon records 0 predictions; the learning loop only closes in the CL01 Live-4 harness today.
7. **Missing seam: improve-verdicts hook → digest cards** (OCTOPUS_WIRE_IMPROVE_LEARN=1 but verdicts file absent — VOTE 2).
8. **Effect-zero paths**: 4d telegram digest (queue-only), git_watcher (state says enabled, check_count=0 behind SELF_CODE_ENABLED).

## 3. Reconciliation verdict

The organism's **real, evidence-producing spine** is: labels registry + memory gate + prediction ledger + budget/organ gate + Live-4 harness + paid-path observability + autonomy/hard-stop boundary. Everything else is either support (dashboards, docs), shadow (councils), or paper (hardware). **No merges recommended now**; the highest-value structural moves are the five seams above, all additive, none TCB except the math-core guard which needs owner ceremony.
