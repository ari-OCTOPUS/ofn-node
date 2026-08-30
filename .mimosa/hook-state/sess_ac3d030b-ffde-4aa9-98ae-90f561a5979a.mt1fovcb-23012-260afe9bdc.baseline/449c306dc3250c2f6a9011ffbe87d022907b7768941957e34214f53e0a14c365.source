# OCTOPUS Activation Report — Hidden Potential Analysis

> **Date:** 2026-07-16  
> **Scope:** Full-stack scan of F:/backup (octopus project)  
> **Method:** 11 parallel explorer agents across 8 subsystems  
> **Finding:** ~70 dormant capabilities identified; ~40 are P0/P1 activatable with minimal risk

---

## Executive Summary

Your octopus is **structurally alive** but **functionally anaesthetized**. The codebase contains a fully-built nervous system (neural, heart, cortex), a dual-brain intelligence layer (v3), a 10-world dashboard, a Telegram cockpit (Ari + Saba), and a 4D control plane — yet **the majority of these subsystems are gated behind environment flags, missing a single import line, or lacking a caller**.

| Metric | Value |
|--------|-------|
| Python files scanned | ~200+ |
| Dormant / orphaned modules | 18 |
| Env flags that unlock major subsystems | 12 |
| Missing one-line imports / calls | 24 |
| Dead versions to archive | 6 |
| Fully-built but never-run validation harnesses | 4 |

**The good news:** Almost no hidden potential requires *writing* new logic. It requires *wiring* existing logic.

---

## Part 1: The Five Classes of Hidden Potential

### Class A — "Flip a Flag" (zero code changes)

These capabilities are 100% implemented and tested. They need an environment variable or a flag file.

| Subsystem | Flag | What It Unlocks |
|-----------|------|-----------------|
| `_ops/cortex` | `CORTEX_IGNITION=1` | Global Workspace Theory pipeline (competition → WTA ignition → re-entry) |
| `_ops/cortex` | `CORTEX_SELF_MONITOR=1` | Self-claims → Brier/AURC calibration loop |
| `_ops/cortex` | `CORTEX_CONSOLIDATE=1` | Generative Agents-style memory consolidation (episodic → semantic) |
| `_ops/cortex` | `OCTOPUS_AUTONOMY_FREE=1` | Auto-decide non-important proposals without owner escalation |
| `_ops/cortex` | `CORTEX_ROUTE_SCORER=1` | 6-signal routing advisor (complexity/risk/privacy/impact/cost/urgency) |
| `_ops/cortex` | `IGNITION_SOFT_WTA_SHADOW=1` | Soft-WTA shadow comparator alongside hard-WTA |
| `_ops/heart` | `OCTOPUS_WIRE_HEART=1` | Shadow heartbeat + setpoint + producers |
| `_ops/heart` | `OCTOPUS_WIRE_HEART_WORK=1` | Work pump cadence scheduler |
| `_ops/heart` | `HEART_PRECISION_WEIGHT=1` | Active-inference π-weighting in control law |
| `_ops/heart` | `HEART_W_SHADOW=1.0` | E_shadow rest term in living-beat control |
| `4d_system/control_plane` | `CONTROL_PLANE_SELF_HEAL=1` | 24/7 daemon + telegram_bot supervisor with crash/hang detection |
| `4d_system/control_plane` | `CONTROL_PLANE_KILL_SWITCH_LIVE=1` | Live pause/resume/stop from UI |
| `4d_system/control_plane` | `CONTROL_PLANE_APPROVALS_LIVE=1` | Approve/reject buttons for self-code proposals |
| `4d_system/control_plane` | `CONTROL_PLANE_SHADOW_POLICY=1` | Shadow policy analysis (destructive marker detection) |
| `4d_system/brain` | `EVOLVE_REQUIRE_APPROVAL=1` | Require owner approval for evolved strategy changes |

### Class B — "Add One Import / One Call" (one-line wiring)

These need a single `import` or a single function call added to an existing loop.

| From | To | Missing Connection |
|------|----|-------------------|
| `langar_bot.py` | `octopus_core.integration.langar_integration` | `attach_to_langar()` never called |
| `orchestrator.py` | `brain.store.OctopusState` | `record_tick()` never called |
| `daemon.py` | `brain.events` | `maybe_heartbeat()` never called |
| `daemon.py` | `meta_research.py` | `run_meta_research()` never called |
| `daemon.py` | `vault_sync.py` | `autolink_vault()` never called |
| `daemon.py` | `evaluation.py` | `save_report()` never called |
| `neural_beat` | `hebbian.py` | `decay()` never called |
| `neural_beat` | `signal_hub.py` | `doctor/acquisition/school` never passed |
| `organism.py` | `neural_driver.py` | `brain_inputs` discarded after compute |
| `pf_admin.py` | `brain.learning` | `with_bandit()` not used by default |
| `saba_studio.py` | `brain.dual_brain_v3` | `brain=` parameter never auto-wired |
| `saba_studio.py` | `brain.faq_engine` | No FAQ handler for Saba-side |
| `langar_bot.py` | `brain.lifecycle` | `/lifecycle` or `/churn` command missing |
| `langar_bot.py` | `brain.kpi_dashboard` | `/kpi_html` command missing |
| `telegram_bot.py` | `brain.self_code` | `/revert` and `/history` commands missing |
| `telegram_bot.py` | `brain.evaluation` | `/report` command missing |
| `telegram_bot.py` | `brain.backup` | `/backup` command missing |

### Class C — "Orphaned Modules" (fully built, zero importers)

These files are complete implementations with tests, but **nothing imports them**.

| Module | Capability | Activation Path |
|--------|-----------|-----------------|
| `brain/ab_tracker.py` | A/B test lifecycle (create, record, analyze, winner) | Wire into `acquisition_pipeline.py` + add `/ab_*` commands |
| `brain/content_engine.py` | Idea generation, script planning, reuse matrix, A/B pairs | Wire into `saba_studio.py` or `acquisition_pipeline._seeds()` |
| `brain/lifecycle.py` | Churn prediction, win-back strategy | Wire into `KPIRollup.record()` + `/fan_stats` |
| `brain/kpi_dashboard.py` | HTML dashboard renderer | Add `/kpi_html` command or scheduled weekly export |
| `4d_system/brain/graph.py` | LangGraph 7-node pipeline (verify→detect→analyze→report→reflect→decide) | Replace `autoloop.run_step()` with `graph.run_experiment()` |
| `4d_system/brain/patterns.py` | 5 SOG architectural patterns (DualTrack, EpistemicCensor, etc.) | Instantiate in `self_code.py` / `self_evolve.py` |
| `4d_system/brain/auto_experiment.py` | Autonomous experiment suggestion | Add `_job_auto_experiment` to `automation.py` mode cycle |
| `4d_system/brain/hypotheses.py` | 14 falsifiable hypotheses catalog | Integrate with `auto_experiment.py` |
| `_ops/cortex/depth_guard.py` | Delegation depth ≤2 detector | Import in `model_router.ask()` |
| `_ops/cortex/execution_board.py` | 6-lane execution board | Render in dashboard or Telegram |
| `_ops/cortex/guidance_box.py` | Top 5 owner actionable items | Render in dashboard or Telegram |
| `_ops/heart/replay_s.py` | S-batch calibration harness | Schedule as weekly automation |

### Class D — "Dead Versions" (superseded, create confusion)

| File | Status | Action |
|------|--------|--------|
| `brain/dual_brain.py` | Superseded by v3 | Archive to `archive/` |
| `brain/project_f_brain.py` | Superseded by v3 | Archive (or port archive/budget logic first) |
| `studio/studio_telegram.py` | Superseded by `saba_studio.py` | Delete |
| `studio/studio_telegram_v3.py` | Partially superseded | Merge quarantine/AI-brief into `saba_studio.py`, then delete |
| `4d_system/brain/autoloop.py` | Simpler loop; `graph.py` is richer | Keep as fallback, add `use_langgraph` flag |

### Class E — "Missing Data Paths" (advisory output computed then discarded)

| Source | What's Computed | Where It Goes (Now) | Where It Should Go |
|--------|----------------|---------------------|-------------------|
| `neural_driver.py` | `brain_inputs` (stress, confidence, schedule hints) | Discarded | `ORGANISM-STATE.json` or `UnifiedBus` |
| `control_law.py` | Precision-weighted error | Off by default | Enabled via `HEART_PRECISION_WEIGHT=1` |
| `doctor_setpoint.py` | LLM-refined viable band | Locked behind flag | Unlock after date/budget gate |
| `autoregulation.py` | `explore_advice` | Ignored by `governor_epoch.py` | Feed into `allocate_dry()` as soft advisory |
| `circadian.py` | `best_platform()`, `readiness()` | Telemetry only | Task router / sprint budget modulator |
| `telemetry.summary()` | Error rate, avg duration, intent distribution | No consumer | New `octopus_core/learning.py` calibration brain |
| `consolidation.py` | `latent_vector`, `bcm_pruned`, `sparse_ratio` | Default `None` | Enable `OCTOPUS_WIRE_BCM` and `OCTOPUS_WIRE_SPARSE` |

---

## Part 2: Activation Roadmap (Prioritized)

### 🔴 P0 — Critical (Unlock Major Subsystems)

**Goal:** Go from "octopus ticks in isolation" to "octopus is a connected organism."

1. **Flip the 12 env flags** (Class A above). Start with cortex flags (`CORTEX_IGNITION`, `CORTEX_SELF_MONITOR`, `CORTEX_CONSOLIDATE`, `OCTOPUS_AUTONOMY_FREE`) and control-plane flags (`CONTROL_PLANE_SELF_HEAL`, `CONTROL_PLANE_KILL_SWITCH_LIVE`, `CONTROL_PLANE_APPROVALS_LIVE`).
2. **Attach `LangarOctopusAdapter`** in `langar_bot.py` — 3 lines (import, instantiate in `__init__`, call `on_command()` in `handle()`). This immediately activates event_bus, telemetry, health heartbeat, and capability registry.
3. **Wire `LearningBridge` as default** in `AcquisitionBrain` — change `orchestrator.py` and `pf_admin.py` to use `with_bandit()` instead of plain constructor. This is the single biggest intelligence upgrade.
4. **Enable `DataSpine` as shared container** in `langar_bot.py` — replace individual `FanDB()` / `KPIRollup()` / `VaultBank()` instantiations with one `DataSpine()`.
5. **Fix orchestrator imports** — either implement minimal stubs for `_ops/neural` dependencies (`NeuralDriver`, `HebbianAssociator`, etc.) or simplify `PFOrchestrator` to only use existing components. Currently `/octopus_tick` falls back to isolated heartbeat because imports fail.
6. **Create `_ops/ACTIVATION-HEARTSTATE.flag`** — starts heart telemetry envelope.
7. **Run validation harnesses** — execute `_ops/heart/sog_math.py` and `_ops/heart/sim_heart.py` to generate lock files, then enable `HEART_PRECISION_WEIGHT` and `HEART_W_SHADOW`.

### 🟡 P1 — Important (Close Feedback Loops)

8. **Wire `AcquisitionPipeline.record_kpi()`** into `langar_bot._kpi_record()` — closes the learning loop so ThompsonBandit learns from real outcomes.
9. **Expose orphan modules via Telegram commands** — add `/ab_status`, `/ab_record`, `/kpi_html`, `/lifecycle`, `/churn`, `/winback`, `/suggest` to `langar_bot.py`.
10. **Inject `DualBrainV3` into `SabaStudio`** — pass `brain=DualBrainV3()` on startup so AI brief and smart recommendations activate.
11. **Connect `faq_engine` to both bots** — Ari already has `/dm_inbox`; add FAQ handler to Saba's DM flow too.
12. **Register `HookBus` listeners** in `organism.py` or `wiring.py` — at minimum `on_error` → `opslib.alert()` and `post_sprint` → `bus.publish()`.
13. **Add `hebbian.decay()` call** in `neural_beat` to prevent unbounded memory growth.
14. **Route `brain_inputs` to state** — merge neural driver advisory output into `ORGANISM-STATE.json` so dashboards can read confidence and schedule hints.
15. **Wire `octopus_core` integrations properly** — switch from raw `Telemetry` to `TelemetryBus`, add `HeartBeat` background threads, register `"organ.dead"` subscriber, and call `capability_registry.heartbeat()` periodically.

### 🟢 P2 — Deepening (Make It Smart)

16. **Replace `autoloop` with `LangGraph`** — add `use_langgraph` mode to `AutomationController` and route to `graph.run_experiment()`. This activates the full 7-node checkpointed pipeline.
17. **Enable meta-research loop** — call `meta_research.run_meta_research()` from `daemon.py` every 100 ticks.
18. **Schedule periodic observability** — automate `snapshot.collect_status()`, `shadow.run_shadow()`, `channel_doctor.run_doctor()`, and `registry.mirror_to_sqlite()`.
19. **Activate `MATHVIZ` with real data** — feed live geometry parameters (`bars`, `sizes`, `p`, `k`) from `OCTO_DATA` into every world's 3D hologram.
20. **Unify `OCTOPUS/worlds` data layer** — refactor `03-money`, `06-time`, `07-decision`, `08-risk` to use `OCTO_DATA` accessors instead of raw nervous-system files.
21. **Archive dead versions** — move `dual_brain.py`, `project_f_brain.py`, `studio_telegram.py`, `studio_telegram_v3.py` to `_Archive/`.
22. **Implement rollback payloads** in `actuator.py` production flows.
23. **Create `octopus_core/learning.py`** — consumes `telemetry.summary()` and adjusts routing probabilities.
24. **Wire `content_engine.py`** into `acquisition_pipeline._seeds()` as a real seed source between vault and safe-hooks.

---

## Part 3: Quick Wins (Do Today)

These are **≤5 minutes each** and unlock visible value immediately:

1. `export CORTEX_IGNITION=1`
2. `export CORTEX_SELF_MONITOR=1`
3. `export CONTROL_PLANE_SELF_HEAL=1`
4. `touch _ops/ACTIVATION-HEARTSTATE.flag`
5. Add `brain=DualBrainV3()` to `SabaStudio` startup
6. Change `AcquisitionBrain(...)` to `AcquisitionBrain.with_bandit(...)` in `orchestrator.py:54`
7. Add `from octopus_core.integration.langar_integration import attach_to_langar` + `self._octopus = attach_to_langar(self, ...)` in `langar_bot.py`
8. Add `/kpi_html` command to `langar_bot.py` that calls `KPIRenderer().render()`

---

## Part 4: Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Flag-flipping enables too much autonomy | `OCTOPUS_AUTONOMY_FREE=1` is advisory-only for non-important items; money/code/kill/secrets still escalate. All destructive actions still require approval. |
| Heart precision weight breaks stability | Run `replay_s.py` first; only enable if `gate6_unlock=True`. The control law has drift-guard and band-error limits. |
| LangGraph replaces working autoloop | Add as `use_langgraph` flag, not a hard switch. Keep autoloop as fallback. |
| Wiring orphan modules introduces bugs | All orphaned modules have tests. Activate behind feature flags or owner-gated commands first. |
| Dead versions deleted by mistake | Move to `_Archive/` instead of `rm`. Git history preserves everything. |

---

## Part 5: Metrics to Track Post-Activation

| Metric | Before | After (Target) |
|--------|--------|----------------|
| Active env flags | ~3 | 12+ |
| Orphaned modules in production | 18 | 0 |
| Neural tick isolation rate | 100% | <10% |
| Heart telemetry envelope | OFF | ON |
| Cortex Global Workspace | OFF | ON |
| Control plane self-heal | OFF | ON |
| Telegram bot command count (Ari) | 46 | 55+ |
| A/B tests running | 0 | Auto-created from pipeline |
| Dashboard data freshness | Manual | Auto-refresh every 15 min |

---

## Next Step

If you approve this roadmap, I can dispatch a **coder swarm** to implement P0 and P1 in parallel worktrees (one per subsystem), with each change behind a flag or in a separate branch. Nothing goes live until you review the diff and flip the flag yourself.

**Your call: Start with P0 flags, or go straight to wiring?**
