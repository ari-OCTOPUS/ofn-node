"""orchestration -- Durable Multi-Agent Task Orchestration (EQUIP G1).

Provides a lightweight, general-purpose task orchestrator that ensures
multi-stage missions survive crash/restart/timeout by resuming from the
last valid checkpoint without repeating side effects.

Integrates with existing chain components:
  - G2 memory: state persistence
  - G6 telemetry: trace_context propagation
  - G7 identity: agent IDs, capability tokens
  - G8 containment: kill coordinator, agent circuit, risk gate, audit chain

No external dependencies. stdlib-only. Fail-soft where possible, fail-closed
where required (kill switch, illegal transitions).
"""
