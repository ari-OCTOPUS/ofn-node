---
type: evidence-milestone
status: local-fixture-results
created: 2026-09-05
updated: 2026-09-05
tags: [octopus, census, dare, multiobjective]
---

# Census and numerical candidate

## Census reconciliation

The historical nine quarantined files were not re-run as a full suite. A source-pinned no-import AST supplement found 178 static test-shaped nodes across eight files; `test_root_hygiene.py` is a script assertion with no test node. This is source inventory only—not pytest registration or execution.

The earlier v3/v4 collection attempts are retained as harness-boundary evidence, not project failures.

## DARE comparison

- **B0:** a pinned transcription of the historical closed form, benchmark-only.
- **C1:** isolated stable DARE candidate.
- Workload: 270 frozen scalar inputs; Decimal precision 80 used as the local numerical reference.
- C1 maximum relative error: `6.179952383167389e-16`.
- B0 maximum relative error: `1.0`; it therefore fails the predeclared numerical hard gate.

CPU, wall-clock latency, and `python_alloc_peak_bytes` were recorded separately; no composite score was formed. C1 is the sole eligible candidate **in this narrow numerical benchmark**, and no global architecture/production winner is claimed.

## Formula coverage

The registry retains all 20 families / 46 atomic relationships. The continuation added isolated contracts for selected rows only; rows that are source-only or spec-only remain so. See `FORMULA-REGISTRY-v4.json` and `FORMULA-CONSUMER-MAP-v2.json` in the local package.

## Next gate

G1A review is required before any candidate adoption. Do not use the local benchmark as a runtime activation rationale.
