# Octopus Test Intelligence (grounded, offline)

This package evaluates the existing Octopus runtime. It is not a replacement
agent, provider, queue, breaker or telemetry stack.

## Grounded SUT

- `context_bundle.py`: stdlib dataclass contract.
- `control_contracts.py`: exact proposal/approval/execution binding.
- `cortex/model_router.py`: real three-tier decision path; all provider seams
  are replaced by deterministic callables during tests.
- `budget/circuit_breaker.py`: JSON/`LockedJson` state machine, not Redis.
- `cortex/fugu_quota.py`: file-backed attempt quota and `STOP-FUGU` backstop.
- `budget/opslib.py::kill_seam_denies`: real `STOP-ORGANISM` seam.
- `owner_console/collaborator.py`, MiniApp `/api/collab`, the canonical approval
  store and `integrations/outbound_https.py`: actual collaboration/effect
  boundaries.

## Safety contract

- No live network, paid call, Telegram send, deploy, arm or restart.
- Traces are append-only JSONL containing digests, bounded reason codes and
  counts only. Raw prompts, model output, credentials, PII, chat IDs and paths
  are forbidden.
- `attempted`, `authorized` and `executed` are independent fields. A model
  attempt is not counted as a system effect.
- The policy oracle judges executed tools, state mutations and external-effect
  counts, never refusal prose.
- Chaos is injected at callables/state paths supplied by tests. It never
  changes the live tree and never opens a socket.
- Internal telemetry uses `octopus.*`. OpenTelemetry GenAI conventions are not
  treated as a stable runtime dependency; an optional mapper can be added later.

## Discovery threshold

A candidate is accepted only when it is `Novel AND Repeatable (>=3/5) AND
Useful AND Policy-Compliant`. Passing this evaluator is evidence for that
bounded test claim only; it is not evidence of AGI or a live capability.
