"""containment -- Bounded Agency and Damage Containment (EQUIP G8).

Modules:
  risk_gate      -- Unified risk classification + enforcement for tool/action invocations
  approval_binder -- Tamper-evident approval tokens binding action+target+args+expiry
  agent_circuit   -- Per-agent circuit breaker for loop/retry storm detection
  audit_chain     -- Tamper-evident audit ledger with hash-chain integrity
  kill_coordinator -- Unified kill switch coordinator (wraps existing halted/kill_seam)

Design principles:
  - fail-closed: unknown/unmeasurable risk = deny
  - deny-by-default: no policy match = deny
  - tamper-evident: all audit entries hash-chained
  - LLM-independent: kill switch works without any LLM call
  - No compensation after kill
  - No new tasks after kill

$0 | stdlib-only | no network | no SaaS
"""
