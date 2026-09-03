# P5 — telemetry mapping contract

purpose: name the span a typed run event would occupy. A mapping is not an export.
status: contract only. No SDK, no exporter, no network.

## Pointers (not mirrors)

| artefact | body | SHA-256 of the source blob | bytes | evidence |
|---|---|---|---|---|
| D-27 unlock directive | PR #66 `docs/octopus-surgery/stage-01-lineage-scan/2026-09-01/sources/D-27-UNLOCK-DIRECTIVE.md` | `c55f90852fe2753a8a1650662d256a6b7a20549c67de578a32ddfd7d07041ea9` | 5469 | B (branch blob; not independently re-hashed on disk outside git) |
| D-28 edge runbook | PR #67 `docs/octopus-surgery/stage-01-lineage-scan/2026-09-01/sources/D-28-EDGE-RUNBOOK.md` | `c79f0e7467c70c639132e0d75ef0a98de5e733d5f0e49176a1eedd35dc73f28a` | 16212 | B (same) |
| P1 events vocabulary | PR #74 `ofn/kernel/events.py` | see that PR's HEAD | — | A once #74 merges |

`MASTER-BLUEPRINT.md` and `CONTRIBUTING.md` were **absent on `main` @67359a6** this run (2026-09-02T05:19:24Z). Absence is UNKNOWN-on-this-body, not proof they do not exist elsewhere.

## Binding code

- `ofn/kernel/otel_map.py` — nine-kind span table; unknown kind → `FailClosedError`
- `tests/test_otel_map.py` — completeness + fail-closed + ready/send are not spans

## Rules

1. Every event kind has exactly one dotted span name.
2. `campaign_envelope_ready`, `send_authorized`, `quote_sent` are not span names and are not exportable states.
3. Attribute keys are an allow-list. Unknown fields (including `payload`) are omitted, not forwarded.
4. Emitting a span is an adapter decision this contract does not make.
