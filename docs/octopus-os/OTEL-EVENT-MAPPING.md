# OTEL-EVENT-MAPPING — typed events ↔ OpenTelemetry GenAI (design-only, P5 preview)

scope_measured: event vocabulary read from ofn/kernel/events.py (P1 branch @92f5267 lineage);
  OTel GenAI convention status quoted from the blueprint's own warning.
scope_not_measured: no OTel SDK added anywhere; no exporter; no network. This is a design map,
  deliberately NOT wired (P5), because the GenAI conventions were still "Development" status —
  adopting an unstable convention as stable is how a schema becomes a liability.

## The mapping (when P5 executes)

| octopus event (kernel/events.py) | OTel GenAI span (proposed) | notes |
|---|---|---|
| RUN_CREATED | `create_agent` (run-scoped) | run_id = envelope.run_id (boundary-minted) |
| CLAIM_CREATED | `invoke_workflow` (queue segment) | outbox claim, exactly-once |
| PROPOSAL_CREATED | `invoke_agent` (output artifact) | proposal ≠ execution, never merged |
| POLICY_DECISION | `invoke_workflow` (decision node) | carries rule id (release_switch RULE_*) |
| TOOL_INVOKED | `execute_tool` | allowed_tools allowlist pre-checked |
| EXECUTION_RECEIPT | `execute_tool` (terminal event) | one receipt settles one effect |
| BUDGET_DEBIT | span attribute on the receipt span | `octopus.budget.debit_cents` |
| RUN_CLOSED | `create_agent` (end) | after close, appends are REJECTED |
| RUN_REJECTED | span attribute on a synthetic parent | kill-switch refusals leave a trace, not a run |

## Rules carried over unchanged

1. `octopus.*` is our namespace; `gen_ai.*` mapping lives in exactly one adapter file
   (grep-tested isolation, P1/P3 pattern).
2. Events stay the spine of record (JSONL, append-only); OTel is a projection, never the ledger.
3. If the GenAI convention stabilizes, the adapter changes — the schema does not.
