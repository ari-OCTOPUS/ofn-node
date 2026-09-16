# 4D System — Architectural Scan Report

**Date:** 2026-07-13
**Scanner:** Octopus Architectural Scanner
**Scope:** `F:/backup/4d_system/` (read-only scan, 3,355 files total)
**Epistemic stance:** DERIVED from source code unless marked FACT / ASSUMPTION / UNKNOWN.

---

## 1. Executive Summary

The `4d_system/` directory contains a **self-improving, self-aware, self-governing research system** built around the SOG mathematical model. Organized into four families:

| Family | Core Files | Status |
|--------|-----------|--------|
| Self-healing | 7 files + 4 tests | ACTIVE |
| Self-control / Governance | 12 files + 8 tests | ACTIVE (v1 observe-only) |
| Self-awareness / Self-model | 18 files + 8 tests | ACTIVE |
| Self-modification / Evolution | 7 files + 3 tests | ACTIVE but GATED |

All high-risk self-modification is **owner-gated** and **TCB-protected**. Default governance mode is **observe-only**; live kill-switches are flag-gated and default-off.

---

## 2. File Inventory by Family

### 2.1 Self-healing

| Path | Size | Role | Risk |
|------|------|------|------|
| brain/backup.py | 3,907 | Daily DB + JSON snapshot backup (max 5 rotation) | LOW |
| brain/housekeeping.py | 10,173 | Smart caps: vault notes (500), rhythms (500), patterns (1000), events (5000), proposals (200). Archive-never-delete. | LOW |
| tests/test_backup.py | — | Backup tests | LOW |
| tests/test_housekeeping_trim.py | — | Housekeeping tests | LOW |
| tests/_shadow_tails/brain__housekeeping.py.tail | — | Historical tail | LOW |
| tests/_shadow_tails/brain__housekeeping.py.tail2 | — | Historical tail | LOW |
| outputs/backups/2026-07-11/ | — | Actual backup dir | LOW |

**Evidence:**
- backup.py:36: `backup_now(tag)` uses sqlite3 backup API for WAL-safe copies.
- backup.py:59: Copies `self_evolved/strategy.json` and `self_evolved/frontier.json` as identity files.
- housekeeping.py:37: `archive_vault_notes()` archives auto-notes (🔍 prefix); hand-crafted notes never move.
- housekeeping.py:165: `archive_self_code_proposals()` never archives pending_approval proposals.

### 2.2 Self-control / Governance

| Path | Size | Role | Risk |
|------|------|------|------|
| brain/guardrails.py | 13,393 | TCB gate. Safe param ranges, clamping, TCB lists, assert_code_target_allowed, assert_safe_write. | HIGH |
| control_plane/policy.py | 5,423 | Policy ladder 0..5 (observe → kill-switch). Pure function. | LOW |
| control_plane/registry.py | 6,809 | YAML registry loader + SQLite mirror. | LOW |
| control_plane/registry.yaml | 17,754 | Source of truth for subsystems/channels. | LOW |
| control_plane/contracts.py | 6,062 | Dataclasses: EventEnvelope, StateSnapshot, ActionEnvelope, ApprovalRequest, PolicyResult, HealthSignal, KillSwitchCommand, HumanOverrideRecord. | LOW |
| control_plane/flags.py | 2,120 | Governance flags: all default-off except OBSERVE_ONLY. | LOW |
| control_plane/channel_doctor.py | 7,732 | Channel health: PASS/WARN/FAIL/UNKNOWN. Writes only to _reports/. | LOW |
| control_plane/snapshot.py | 13,011 | Read-only collector: daemon, budget, events, workspace, approvals, evolution. | LOW |
| brain/daemon.py | 11,475 | Headless month-runner. Tick loop with pause/stop files. Auto-proposes code. | HIGH |
| brain/budget.py | 3,989 | Daily cloud LLM cap (1000). Falls back to Ollama/mock. | MEDIUM |
| brain/events.py | 12,119 | Structured event bus in SQLite. dashboard_events with approval_state. | MEDIUM |
| brain/state.py | 2,219 | LangGraph AgentState. Includes SOG scores (sms, sls, pcai). | LOW |
| tests/test_scores_guards.py | — | Guard tests | LOW |
| tests/test_control_plane_policy.py | — | Policy tests | LOW |
| tests/test_control_plane_registry.py | — | Registry tests | LOW |
| tests/test_control_plane_snapshot.py | — | Snapshot tests | LOW |
| tests/test_channel_doctor.py | — | Doctor tests | LOW |
| tests/test_budget.py | — | Budget tests | LOW |
| scripts/hooks/pre-commit | 429 | Git hook: blocks commit if tests fail. | MEDIUM |

**Evidence:**
- guardrails.py:69-91: CODE_TCB_FILES and CODE_TCB_DIR_NAMES. Protected: run.py, guardrails.py, self_code.py, self_evolve.py, budget.py, automation.py, daemon.py, telegram_bot.py, events.py, router.py, settings.py. Protected trees: core/, tests/, config/.
- guardrails.py:147: assert_code_target_allowed() is fail-closed.
- policy.py:25-31: Level enum: OBSERVE=0, SHADOW_LOG=1, SOFT_WARN=2, REQUIRE_APPROVAL=3, PAUSE_SUBSYSTEM=4, KILL_SWITCH=5.
- policy.py:60-76: High-risk actions: self_code_approve, self_code_apply, change_tcb, flip_live_flag, budget_increase, delete_data, change_env_or_secrets, change_daemon_behavior, etc.
- flags.py:13-19: Only CONTROL_PLANE_OBSERVE_ONLY=true. All live flags false.
- registry.yaml:21-48: 24 subsystems. self_evolve (tcb:true, authority:approve). self_code (tcb:true, authority:approve, live:gated).
- daemon.py:99: self_code_on = os.getenv("SELF_CODE_ENABLED", "0") — default OFF.
- daemon.py:129-136: Pause file check skips tick but keeps process alive.
- daemon.py:146-157: Protective halt on invariant violation; force-flushes critical message.

### 2.3 Self-awareness / Self-model

| Path | Size | Role | Risk |
|------|------|------|------|
| brain/self_model.py | 9,395 | AST-based self-map. 3 layers: Self-Map, Self-Description, Self-Critique. | LOW |
| brain/reflection.py | 4,681 | Quality eval: ACCEPT/REVISE/REJECT. Rule-based + LLM. | LOW |
| brain/self_growth.py | 7,262 | Goal-directed growth. current_focus(), record_learned_capability(), self_portrait(). | LOW |
| brain/workspace.py | 2,546 | GWT metrics: ignition, broadcast_width, coherence, ignition_rate. | LOW |
| brain/frontier.py | 10,004 | Quality-diversity archive (MAP-Elites). | LOW |
| brain/conclusions.py | 8,561 | SOG math conclusion engine. | LOW |
| llm/shadow_analyze.py | 27,152 | Shadow analysis Phase 2: MIGRATE/HOLD/INSUFFICIENT. | MEDIUM |
| llm/shadow_compare.py | 12,984 | Shadow analysis Phase 1: two-stack divergence records. | MEDIUM |
| core/model.py | 11,328 | SOG heart: DARE solver, Kalman, ModelSolution (E_shadow, Delta_self, identity_check). | LOW |
| core/scores.py | 7,940 | Operational scores: SMS, SLS, PCAI, MSC. | LOW |
| core/metrics.py | 8,431 | Empirical: empirical_shadow, fit_shadow_parameters, build_report_card. | LOW |
| brain/graph.py | 11,978 | LangGraph: load_context → verify → detect → scores → analyze → report → reflect → decide_next. | LOW |
| brain/nodes.py | 15,978 | Graph nodes. RAG + past reflections = learning loop. | LOW |
| brain/automation.py | 36,816 | 13-mode cycle: explore, introspect, create, evolve, real, synthesize, mutate, guard. | MEDIUM |
| brain/autoloop.py | 23,565 | Research autoloop. Local-first (Ollama → GLM → heuristic). | LOW |
| agents/orchestrator.py | 5,106 | Legacy W0→W1→W2→W3 gated pipeline. | LOW |
| agents/detector.py | 3,950 | W1 shadow detector. | LOW |
| agents/base.py | 2,327 | Base agent with LLM routing. | LOW |
| llm/router.py | 10,228 | LLM router: Fugu, GLM, Ollama, Mock. Budget-aware fallback. | MEDIUM |
| memory/store.py | 10,011 | SQLite store: experiments, hypotheses, conversations, reflections, rhythms. WAL mode. | LOW |
| config/settings.py | 6,707 | System root, ref dir, LLM config, anchors, logging. | LOW |
| run.py | 7,355 | Entry point. Self-healing import reload on API mismatch. | LOW |

**Evidence:**
- self_model.py:7-10: Self-awareness three layers: Self-Map, Self-Description, Self-Critique.
- self_model.py:192-199: Inferred limitation: "cannot self-modify — only analyzes."
- self_growth.py:4-7: Explicitly denies phenomenological awareness: "this is not consciousness."
- self_growth.py:120-152: self_portrait() generates live self-portrait with mission, caps, lims, goals, focus, learned capabilities.
- workspace.py:5-10: GWT metrics from event bus: ignition, broadcast_width, coherence, ignition_rate.
- frontier.py:15-16: Quality-diversity, MAP-Elites style. Coverage growth = real progress.
- conclusions.py:48-55: synthesize_conclusions() applies SOG math to frontier data.
- reflection.py:19-22: evaluate_quality() returns (ACCEPT/REVISE/REJECT, score, feedback).
- shadow_analyze.py:45-47: MIN_RECORDS=30, SIM_FORBID=0.5, SIM_MIGRATE=0.7.
- shadow_analyze.py:148-151: MIGRATE is only a recommendation "behind a flag" — never auto-switches.
- automation.py:36-39: 13-mode cycle including mutate, evolve, guard.
- automation.py:71-85: Loads evolved strategy, clamps params via guardrails.
- automation.py:141-149: Human trigger on 3 consecutive failures.
- graph.py:38-91: LangGraph with MemorySaver checkpointing. Reflection loop with reflect_should_revise() gate.
- nodes.py:25-92: load_context_node loads RAG + history + past reflections (learning loop).
- state.py:59-62: SOG scores in state: sms, sls, pcai.
- core/model.py:83-168: ModelSolution with Delta_self, E_shadow, identity_check, detectable.
- core/scores.py:25-31: OperationalScores with SMS, SLS, PCAI, MSC.
- llm/router.py:121-143: Local-first TASK_ROUTING: summarize/rewrite → Ollama; analysis → Fugu; verify → GLM.
- llm/router.py:159-166: Budget fallback to Ollama when cloud cap reached.

### 2.4 Self-modification / Evolution

| Path | Size | Role | Risk |
|------|------|------|------|
| brain/self_evolve.py | 16,764 | Strategy evolution. JSON-only. propose → test_candidate → save/rollback. | HIGH |
| brain/self_code.py | 26,975 | Self-code pipeline: PROPOSE (static AST) → APPROVE → test → apply. | HIGH |
| outputs/self_evolved/strategy.json | 318 | Current strategy. Generation 9, fitness 1.0. | LOW |
| outputs/self_evolved/strategy.backup.json | 341 | Rollback backup. | LOW |
| outputs/self_evolved/frontier.json | 6,276 | Quality-diversity archive (27 cells). | LOW |
| outputs/self_evolved/conclusions.json | — | Cached conclusions. | LOW |
| outputs/self_code_proposals/ | — | Proposal sandbox (empty). | LOW |
| tests/test_self_code_gate.py | — | Self-code gate tests (AST, TCB). | HIGH |
| tests/test_frontier.py | — | Frontier tests. | LOW |

**Evidence:**
- self_evolve.py:12-18: 4-stage test gate: anchors, experiments, invariants, no-regression.
- self_evolve.py:44-53: DEFAULT_STRATEGY with novelty_threshold, rho_bias, creativity, explore_points, source_policy, notable_weights.
- self_evolve.py:130-165: propose() only mutates explore_points or source_policy. Uses guardrails.clamp_param().
- self_evolve.py:172-200: test_candidate() runs anchor tests, autoloop, invariants, fitness.
- self_evolve.py:108-123: rollback() restores from strategy.backup.json inside file_lock.
- self_code.py:1-2: Pipeline: propose → (owner) approve → apply.
- self_code.py:8-17: Safety: static analysis only, owner sees full diff, throwaway test, tampering detection, textual apply.
- self_code.py:120-157: _danger_features() AST scan for subprocess, importlib, ctypes, pickle, socket, urllib, eval, exec, compile, getattr, setattr, globals, locals, and dangerous file ops.
- self_code.py:160-171: _ast_danger() is delta analysis: only flags NEW dangers vs original.
- self_code.py:197-200: propose_code_change() only if enabled() (env SELF_CODE_ENABLED).
- strategy.json: "_generation": 9, "explore_points": 8000 (evolved from 3000), source_policy shifted to mostly physical.

---

## 3. Dependency Map (Key Call Graph)

```
run.py
├── cli_self_test()
│   ├── config.settings (verify_reference_dir, ANCHORS)
│   ├── core.model.run_self_test()          ← anchor verification
│   ├── memory.store (get_stats, _ensure_db)
│   ├── memory.vectorstore (index_vault, search_vault)
│   ├── llm.langchain_models (get_default_chat, get_mock_chat)
│   ├── brain.tools (ALL_TOOLS)
│   └── brain.graph.run_experiment_streaming()
│       ├── brain.graph.build_graph()
│       │   ├── brain.nodes.*_node
│       │   ├── brain.patterns.reflect_should_revise()
│       │   └── langgraph.checkpoint.memory.MemorySaver
│       └── memory.store.save_experiment()
│           └── memory.store.save_reflection()
└── _run_streamlit_app()
    └── ui.app (6 tabs)
        ├── ui.tab_control_plane
        │   ├── control_plane.snapshot.*_status()
        │   └── control_plane.registry.read_mirror()
        └── ui.tab_dashboard / tab_research / tab_laboratory / tab_graph / tab_meta

brain.daemon.run_forever()  (headless, monthly)
├── brain.automation.AutomationController.run_one()
│   ├── brain.autoloop.AutoLoopEngine.run_step()
│   │   ├── data.synthetic|physical|real_api.CATALOG
│   │   ├── core.metrics.empirical_shadow / fit_shadow_parameters
│   │   ├── llm.router / ollama_client / glm_client
│   │   └── memory.store.save_experiment()
│   ├── brain.self_code.auto_propose_once()   [if SELF_CODE_ENABLED]
│   │   ├── brain.self_growth.current_focus()
│   │   └── brain.guardrails.assert_safe_write()
│   ├── brain.git_watcher.check_and_trigger() [if SELF_CODE_ENABLED]
│   ├── brain.notify.flush_digest()
│   └── brain.housekeeping.run_housekeeping()
│       ├── brain.backup.maybe_daily_backup()
│       └── archive_vault_notes / archive_rhythms / archive_rows / trim_textfile
└── brain.budget.record_call()  [via llm.router]

brain.self_evolve.propose() → test_candidate() → save_strategy()
├── core.model.run_self_test()          (anchor check)
├── brain.autoloop.AutoLoopEngine     (experimental fitness)
└── brain.guardrails.clamp_param()      (safe ranges)

brain.self_code.propose_code_change() → approve → apply
├── brain.guardrails.assert_code_target_allowed()  (TCB check)
├── _static_check() = AST danger scan + substring pre-filter
├── _danger_features() = AST walk for suspicious imports/calls/attrs
└── test in throwaway temp copy → detect tampering → textual apply

control_plane.snapshot.*_status()
├── control_plane.flags.all_flags()
├── control_plane.registry.read_mirror()
├── brain.events.get_recent() / events_summary()
└── brain.workspace.workspace_metrics()   (GWT ignition/coherence)
```

---

## 4. Risk Assessment

| File | Risk | Justification |
|------|------|---------------|
| brain/self_code.py | CRITICAL | Can modify .py files. Protected by TCB + AST scan + owner approval + throwaway test + tampering detection. Default OFF. |
| brain/self_evolve.py | CRITICAL | Mutates strategy JSON that drives behavior. Protected by anchor test + fitness + rollback. |
| brain/daemon.py | HIGH | Headless runner. Can trigger self-code and self-evolution. Protected by pause/stop files, protective halt. |
| brain/guardrails.py | HIGH | The TCB itself. If compromised, all safety collapses. Guards itself. |
| brain/automation.py | HIGH | 13-mode autonomous engine. Includes mutate and evolve. Params clamped by guardrails. |
| control_plane/policy.py | MEDIUM | Pure function, no enforcement yet (v1). Risk rises if flags go live. |
| control_plane/flags.py | MEDIUM | All live governance default-off. If env overrides flip flags, enforcement activates. |
| llm/router.py | MEDIUM | Routes to cloud LLMs. Budget cap prevents runaway. Mock fallback available. |
| brain/budget.py | MEDIUM | Cloud call cap. If bypassed, could exhaust API budget. |
| brain/events.py | MEDIUM | Event bus. If compromised, observability breaks. Does not control execution. |
| llm/shadow_analyze.py | LOW-MEDIUM | Only recommends migration; never auto-switches. Flag-gated. |
| All other files | LOW | Read-only, pure math, archive, or observability. |

---

## 5. Epistemic Labels

| Claim | Label | Evidence |
|-------|-------|----------|
| TCB protects itself from self-modification. | FACT | guardrails.py:69-91 explicitly lists protected files/dirs including guardrails.py itself. |
| Self-code requires owner approval before apply. | FACT | self_code.py:8-17 documents 3-stage pipeline. policy.py:60-61 lists as Level 3. |
| Daemon can propose code changes autonomously. | FACT | daemon.py:162-177 shows auto_propose_once() triggered every N ticks when self_code_on. |
| All governance flags default OFF except observe. | FACT | flags.py:13-19. |
| System denies phenomenological awareness. | FACT | self_growth.py:4-7: "this is not consciousness." |
| Strategy JSON has evolved to generation 9. | FACT | outputs/self_evolved/strategy.json shows "_generation": 9. |
| Frontier contains 27 discovered cells. | FACT | registry.yaml:133 notes "27 cells (verified)". |
| Event bus has ~5031 events as of 2026-07-11. | FACT | registry.yaml:63. |
| Shadow analysis auto-switches LLM stack. | ASSUMPTION (false) | shadow_analyze.py:148-151 says MIGRATE is only a recommendation behind a flag; tool never changes behavior. |
| Self-heals broken Streamlit imports. | FACT | run.py:164-183 has self-healing import reload logic. |
| Pre-commit hook blocks commits on red tests. | FACT | scripts/hooks/pre-commit:4-10. |
| Housekeeping policy is archive-never-delete. | FACT | housekeeping.py:2-5. |
| guardrails.py guards itself (single point of failure). | DERIVED | TCB list includes guardrails.py; no external validator found. |
| Self-model correctly identifies all capabilities. | ASSUMPTION | self_model.py uses keyword heuristics; may miss undocumented capabilities. |

---

## 6. Gaps & Anomalies

1. **TCB Self-Guard:** guardrails.py guards itself. No external validator or checksum auditor was found. Single point of failure.
2. **Empty Proposal Sandbox:** outputs/self_code_proposals/ is empty. Self-code pipeline has not been end-to-end tested in production.
3. **registry.yaml UNKNOWN health_sources:** vault_sync, web_research, agents channels list health_source as UNKNOWN.
4. **Shadow tails:** tests/_shadow_tails/ contains historical tails. Not executed but could confuse.
5. **Budget is best-effort:** budget.py uses file_lock but notes "best-effort"; race conditions possible between daemon and Streamlit.
6. **No watchdog:** daemon writes daemon_state.json but no separate process detects daemon crashes.
7. **Kill-switch unimplemented:** contracts.py defines KillSwitchCommand but notes "v1: always False remains". No live execution path.
8. **Self-reported fitness:** self_evolve.py computes fitness from autoloop engine, which is part of the same system. Circular measurement.

---

## 7. Summary Matrix

| Family | Files | Tests | Live? | Owner-gated? | TCB-protected? |
|--------|-------|-------|-------|--------------|----------------|
| Self-healing | 7 | 4 | Yes | N/A | Partial |
| Self-control | 12 | 8 | Yes (v1) | Partial (flags) | Yes |
| Self-awareness | 18 | 8 | Yes | N/A | No (obs only) |
| Self-evolution | 7 | 3 | Conditional | Yes (approve) | Yes |

**Overall verdict:** The system is a well-architected "perilous but protected" self-improving research OS. Safety is defense-in-depth: TCB + AST scan + owner approval + throwaway test + rollback + policy ladder + flags + budget cap + protective halt. Weakest links: TCB self-guard (no external validator) and untested self-code approval pipeline (empty sandbox). All high-risk actions are disabled by default or require explicit owner approval.

---
*End of report.*
