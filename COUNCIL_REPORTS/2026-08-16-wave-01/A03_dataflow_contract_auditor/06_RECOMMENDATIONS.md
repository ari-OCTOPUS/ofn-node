# 06_RECOMMENDATIONS — A03 (2026-08-16)

Ordered by risk-reduction per effort. All are proposals for the owner/council — A03 does not modify anything.

## REC-1 · Wrap `/sh` in double-confirm + receipt (small, high value)
Require the same pw/pwc two-click flow used for `system.restart`, and append each executed
command (hash + cwd + exit code) to `state/action-audit.jsonl`. Keeps the console useful,
removes the single-message shell risk. (BP-01, R-1)

## REC-2 · Gate 4d hypothesis writes with provenance (small)
Minimum: tag `save_hypothesis` rows `producer=llm` + `trust=advisory` and have readers cap
their prompt budget for advisory rows; better: route through a MemoryGate-equivalent FSM
like the _ops side. (BP-08, R-2)

## REC-3 · Fix the bitemporal claim, not the schema, first (documentation)
Either (a) restate docs as "append-only hash-chained ledger + valid-time memory", or
(b) if bitemporality is wanted, make *one* producer (e.g., spine) emit true `occurred_at`
≠ `recorded_at` and add a reader that uses the difference. Cheapest honesty win available.
(C-1, R-4)

## REC-4 · Standardize timestamps (mechanical, medium effort)
One helper: UTC ISO-8601 with offset (or epoch float) everywhere new records are written;
migrate `started_at/finished_at` (receipts), 4d events `timestamp`, and add *some* time
field to `state/c6/research-ledger.jsonl`. Enables reliable cross-ledger correlation and
staleness math. (R-5)

## REC-5 · Publish a lane map for external effects (documentation + one probe)
A single doc: every lane capable of an external side effect (email today; supervisor
restarts; future), its gate stack, its flag, and its owner-vote reference. Add a test that
greps for network-capable modules not present in the map (drift alarm). (R-3, R-7)

## REC-6 · Unify policy vocabulary or add a translation table (design)
Keep A0-A6 as canonical; provide a mapping for 4d `ACTION_POLICY` levels and telegram risk
tiers; mark 4d control_plane explicitly "observe-only mirror" in its docstring header and
dashboards. (C-6, R-7)

## REC-7 · Runtime flag probe for wave 02 (probe, not change)
A02 should capture the *live* environment/flag state of running processes (read-only) and
diff against `flags-loaded-cortex.json` / AEB bundles, closing the T3→T0 gap on every
"armed" claim in this report. (R-6)

## REC-8 · Chain or checkpoint repair-target ledgers (small)
Either add prev-hash chaining to the REPAIR_TARGETS JSONL files, or have state_guard append
a quarantine-summary record to the file itself instead of rewriting it. (R-8)

## REC-9 · Rename or implement the sensory layer (documentation or build)
If real sensing is intended, implement the classifier the stub asks for ("برای معمار") and
feed at least one non-self source via the (already flagged) ingest lane. Otherwise relabel
docs from "Sensorium active" to "afferent stub (internal aggregates)". (R-9)

## REC-10 · Close the memory_read_patch content gap (small)
`patch_introspect`/`patch_conclude` currently use only counts; pass bounded excerpts of the
retrieved text into the introspection/conclusion prompts (still advisory) so the C-012
"read before decide" fix does its intended job. (MEMORY_DECISION_INFLUENCE §3)
