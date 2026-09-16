---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 4 — Multi-Agent Systems Reviewer: Orchestrator Pipeline

Role: trace researcher → analyst → guardrail → panel → grounding → HITL → finalize; compare against
Anthropic's *Building Effective Agents* (prefer simple, composable, predictable patterns over
autonomous swarms); flag every place an agent failure is **not** surfaced — silent failures are the
highest-severity class here.

## Pipeline trace (evidence: `src/orchestrator.py:81-137`)
1. `_kguard("researcher")` → `researcher.run(topic)` — tool `web_search_mock` then LLM (`:86-87`).
2. `_kguard("analyst")` → `analyst.run(findings)` (`:89-90`).
3. Output guardrail `guardrails.check_output(analysis)` (`:93-96`); fail → `_stop`.
4. Panel review `self.panel.review(analysis)` (`:100-111`); split → HITL escalation; reject → `_stop`.
5. Grounding (advisory unless `GROUNDING_REQUIRED`) (`:114-120`).
6. HITL finalize approval (`:123-127`).
7. IGK actuation gate `self.gate.act("finalize", …)` (`:130-131`) then `run_done` (`:133`).

This is a **prompt-chaining + gating** pattern — exactly the "simple, composable" style the guidance
recommends. There is no autonomous planner, no agent-spawns-agent recursion, no open-ended tool loop.
Alignment with the guidance is good. [Certain]

## Findings

### P4-01 [High] The judge panel ignores its own LLM output — "no single point of decision" is partly theater
`Judge.vote` (`src/panel.py:44-53`) calls `self.provider.complete(...)` and pays for the tokens
(`self.ledger.record("panel", …)`, `:49`) but then computes the vote with
`approve = self._decide(analysis)` (`:50`), a pure Python heuristic (`:33-42`) that never reads
`res.text`. Consequences:
- Diversity across providers/models is illusory — all three stances are deterministic functions of
  the same `analysis` string; round-robin provider assignment (`:63-65`) changes nothing.
- A real judge-model failure, refusal, or malformed response is **invisible**: the vote is computed
  regardless. This is a silent-failure class defect for the very control (#5, no single point of
  decision) it is meant to implement. [Certain]

### P4-02 [High] IGK spawn failure silently downgrades the whole enforcement path
Cross-listed from Pass 1 P1-01 (`src/orchestrator.py:42-49`). In pipeline terms: a failed kernel
spawn removes steps 5 and 7 (grounding + actuation gate) with only a console warning; the run still
reaches `run_done`. Highest-severity *silent* behavior in the pipeline alongside P4-01. [Certain]
(existence) / [Probable] (inducibility).

### P4-03 [Medium] `MAX_STEPS` is declared but never enforced
`config.py:27` `MAX_STEPS = 8` is referenced nowhere except its own definition (`grep`). The
orchestrator has no step counter/loop bound. It is a claimed safety limit that does not exist. Low
practical risk today (the pipeline is linear and finite) but it is a documented control with no
implementation. [Certain]

### P4-04 [Medium] `Supervisor.review` is dead code; README/agents still imply it decides
`src/agents.py:78-86` implements a supervisor verdict from LLM output, but the orchestrator replaced
it with the panel and never calls `supervisor.review` (`grep`: only `panel.review` is invoked at
`src/orchestrator.py:100`). The `Supervisor` agent is still constructed (`:68`) and consumes budget
capacity in config (`config.py:22`). This is a correctness/auditability hazard: docs describe a
control flow that no longer runs. [Certain]

### P4-05 [Medium] Non-panel failures halt but are not escalated to HITL
Guardrail rejection (`src/orchestrator.py:96`), panel full-reject (`:110-111`), and grounding
rejection when enabled (`:118-120`) all call `_stop` and terminate. This is fail-closed (safe), but
none escalates to the human gate for a judgement call; only panel-*split* and finalize do. Per the
task's framing, terminating-without-escalation is acceptable (safe) but worth noting: the human is
informed via the (unsigned) audit log, not asked. [Certain]

### P4-06 [Low] Telemetry failures are swallowed by design
`LangfuseSink` swallows all exceptions in `emit`/`start_run`/`flush`
(`src/langfuse_sink.py:38-40,46-50,54-57`) to protect the main run. Reasonable, but observability
loss is silent. [Certain]

## Positive notes
- Multiple independent stop authorities (budget, kill-switch, HITL, panel) each terminate the run —
  genuine defense-in-depth (`src/orchestrator.py:139-146`). [Certain]
- Budget errors raised inside `Judge.vote` (`src/panel.py:49` → `BudgetExceeded`) propagate to the
  run-level handler and are surfaced (`src/orchestrator.py:143-144`). [Certain]

## Gaps I could not verify
- Real multi-provider behavior (LIVE, no keys). In MOCK all providers are the same class
  (`src/providers.py:18-22`), so provider diversity is untested end-to-end.
