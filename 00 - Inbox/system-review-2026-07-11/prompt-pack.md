---
type: proposal
status: active
tags: [prompts, subagent, parallel, build, handoff]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[00 - Inbox/system-review-2026-07-11/execution-plan]]"
---

# Prompt Pack — reusable subagent prompts (2026-07-11)

> Ready-to-paste prompts for parallel agents. **Shared preamble applies to every prompt** (the guardrails that make agent-built code safe for this system). Each builds a NEW standalone module + standalone test; zero edits to existing files.

## SHARED PREAMBLE (prepend to every lane prompt)

```
You are building ONE additive, standalone module for the OCTOPUS vault-organism (a Python
control-plane under _ops/). NON-NEGOTIABLE house rules:
- ADDITIVE ONLY. Create a NEW module + a NEW standalone test. Do NOT edit any existing file.
- FLAG-OFF / SHADOW: the module must have ZERO effect until an explicit env flag turns it on.
  Nothing you write may change live behavior when its flag is unset.
- Read BEFORE you write: read `_ops/budget/opslib.py` (paths: ORG_ROOT/STATE_DIR/OPS; helpers:
  now_iso, alert), one existing cortex module (e.g. `_ops/cortex/stress.py` or `part_loops.py`)
  for idioms, and `_ops/tests/harness.py` + one standalone test (e.g. `test_stress.py`) for the
  TEST style (plain asserts, `harness.setup(...)`, no pytest, __main__ runner, prints ✅/❌).
- FAIL-SOFT everywhere: any error → safe default, never crash the caller. Read-only w.r.t. the
  vault; only write under STATE_DIR, and only when your flag is on.
- CONTAINMENT: never read/echo Project-F identity (folder "اونلی فنز"/onlyfans/صبا). If you touch
  registry/entities, treat content_free entities as manifest-only.
- $0: no paid LLM calls, stdlib + existing opslib only.
- Match the codebase: Persian-ok comments, env-first state paths (STATE_DIR), same test harness.
- After writing, RUN your standalone test and confirm it passes. Do NOT register it in run_all.py
  (the integrator does that). Do NOT commit.
RETURN (structured): {module_path, module_code, test_path, test_code, test_output, passed:bool,
  flag_name, conventions_followed:[...], residual_risks:[...]}.
```

## Lane A — B5 route-scorer (`_ops/cortex/route_scorer.py`)

```
Build `route_scorer.py`: a pure, additive scorer that RECOMMENDS a routing tier
(local/secondary/primary) from a task descriptor, WITHOUT changing model_router.
Read `_ops/cortex/model_router.py` first (TASK_TIERS, ask(), the 3-tier local-first doctrine).
API: score_route(task:str, ctx:dict) -> {tier, scores:{complexity,risk,privacy,impact,cost,
urgency}, reasons:[...], decision_record:{...}}. Rules from the pasted routing doctrine: shallow/
routine/low-impact/reversible/private → local; deep/high-correctness/architecture/many-files →
primary; sensitive → prefer local-redact-first. Emit an in-memory decision_record (task_id, scores,
tier, why, est_cost, fallback) — do NOT write to disk unless flag CORTEX_ROUTE_SCORER is on. It must
NOT be called by model_router yet (wiring is a later owner-gated step). Standalone test: shallow→local,
deep→primary, sensitive→local, record shape, no-op-without-flag.
```

## Lane B — B4 calibration-probe (`_ops/cortex/calibration_probe.py`)

```
Build `calibration_probe.py`: externally-graded online calibration (Kamoi 2024; Brier/AURC), NOT
self-grading. Read `_ops/cortex/self_model.py` (what claims exist) and how outcomes/discoveries
ledgers are read elsewhere. API: probe() -> {n, brier, aurc, abstain_below, graded:[...]}. Pair recent
self-claims with EXTERNAL ground truth from state ledgers (outcomes.jsonl / discoveries.jsonl); compute
Brier + a simple AURC; suggest an abstain threshold. Ground truth = external ledger only. Fail-soft on
missing/empty ledgers (return n=0). Writes a metacognition record to STATE_DIR ONLY under flag
CORTEX_SELF_MONITOR. Do NOT wire into self_model. Standalone test with a synthetic ledger fixture:
Brier computed, abstain threshold set, no-op without flag, empty-ledger → n=0.
```

## Lane C — B3 consolidate (`_ops/cortex/consolidate.py`)

```
Build `consolidate.py`: episodic→semantic memory consolidation (Generative Agents salience;
sleep-time). Read how events are appended (`_ops/events.py`) and a cortex module for idioms.
API: consolidate_once() -> {n_in, n_semantic, archived}. Tail the events log, score each by
recency×importance×relevance, write BOUNDED semantic notes to state/semantic_memory.jsonl, and
ARCHIVE (never delete — §1 vault) processed raw events to an events.archive.jsonl. Everything gated
by flag CORTEX_CONSOLIDATE (no-op + zero writes when off). Fail-soft. Standalone test with a synthetic
events fixture under a temp STATE_DIR: bounded output, archive preserves originals (no deletion),
no-op without flag, salience ordering sane.
```

## Integrator checklist (me, after agents return)

1. Review each returned module for the house rules (additive/flag-off/fail-soft/containment).
2. Write the 3 new modules + 3 tests to the feature branch.
3. Register the 3 tests in `_ops/tests/run_all.py`.
4. Run the FULL suite with `REAL_VAULT=<worktree>` → must stay green.
5. Commit on the feature branch. Report. No flag flipped, no merge.
