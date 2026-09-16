---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 6 — Code Quality & Python Patterns

Role: idiomatic async, error propagation (no bare/broad except swallowing), typed interfaces between
agents, testability, single-source-of-truth discipline for the "DB".

## Findings

### P6-01 [Medium] Blocking kernel IPC with no timeout — a hung kernel hangs the orchestrator forever
`KernelClient._call` (`igk/client.py:22-26`) writes a line then does a blocking
`self.p.stdout.readline()` with **no timeout**. If the daemon stalls (deadlock, partial write, slow
grounding), the orchestrator blocks indefinitely; there is no watchdog and the kill-switch cannot
help because it is only polled at boundaries between such calls. Everything is synchronous — there is
no async anywhere in the codebase — which is acceptable at this scale, but the unbounded blocking
read is a real robustness hole. [Certain]

### P6-02 [Medium] Broad `except Exception` used for control-flow downgrades (fail-open)
The dangerous instances (not mere logging):
- `src/orchestrator.py:47-49` — IGK spawn failure → downgrade to cooperative (Pass 1 P1-01).
- `src/orchestrator.py:26-30` — import fallback that silently redefines `PermitDenied` as a local
  stub, so a genuine `igk.client` import breakage still lets the pipeline run without the real gate.
Other `except Exception` sites are defensible telemetry/OS-portability guards
(`src/tracing.py:28-30`, `igk/kernel.py:50-53`, `igk/client.py:38-41`, `igk/daemon.py:45-46`,
`src/langfuse_sink.py`). No bare `except:` anywhere (always `Exception`) — good. The problem is
specifically the two that swallow errors on a **security-relevant** path. [Certain]

### P6-03 [Medium] Untyped stringly/dict interfaces between components
- Kernel protocol is entirely `dict` with ad-hoc keys (`{"ok":..., "reason":...}`,
  `igk/kernel.py`/`igk/daemon.py`); no TypedDict/dataclass/schema. A typo in a key
  (`g.get("grounding_ratio")` vs a kernel that returns something else) fails silently as `None`.
- Agent handoffs are bare `str` (`findings`, `analysis`); no structured claim type despite grounding
  wanting `{"subject","value"}` shapes (`igk/kernel.py:154-161`). Only `LLMResult`
  (`src/llm.py:16-21`) and `Usage` (`src/budget.py:18-24`) are typed. Weakens testability and lets
  malformed inter-agent data pass. [Certain]

### P6-04 [Low/Medium] Test isolation via unrestored global mutation
Tests mutate module-global `config` and do not always restore it:
- `test_igk_integration.py:20-23` reassigns `config.IGK_STATE_DIR`/`STOP_FILE`/`AUDIT_LOG_PATH` and
  never restores; `config.GROUNDING_REQUIRED` is toggled and reset (`:43,46`) but the paths are not.
- `test_phase3.py:57,71-73` reassigns `config.PROMPTS_PATH` globally and reloads modules.
`run_tests.py:57-62` and the pytest suite do restore via `finally`/`monkeypatch`. Mixed discipline;
cross-test contamination is possible when files are run in-process together. [Certain]

### P6-05 [Low] `_load_env` duplicated in three entry points (DRY)
Nearly identical env loaders in `run.py:19-28`, `self_update.py:23-31`, `smoke_live.py:22-30`. One
strips quotes (`smoke_live.py`), the others do not — a latent inconsistency in how values are parsed.
[Certain]

### P6-06 [Low] 64-bit truncated audit hash weakens collision resistance
`src/tracing.py:54` truncates SHA-256 to 16 hex (64 bits). The rewrite attack in Pass 2 P2-01 needs
no collision, but 64-bit chaining is below modern norms and needlessly so. [Certain]

### P6-07 [Low] Paid LLM call whose result is discarded (waste + misleading)
`Judge.vote` (`src/panel.py:48-50`) spends tokens on a provider call, then ignores the text
(cross-listed Pass 4 P4-01). In LIVE this is real money for zero decision value. [Certain]

## Positive notes
- Good testability primitives: injectable `hitl_approver`, MOCK LLM, tmp-dir fixtures; 40 tests
  across 6 files, IGK red-team suite runs 8/8 green (verified this session). [Certain]
- `from __future__ import annotations` used consistently; dataclasses where it counts; clear module
  docstrings. [Certain]

## Gaps I could not verify
- Runtime type conformance in LIVE mode (kernel/provider responses only exercised in MOCK).
