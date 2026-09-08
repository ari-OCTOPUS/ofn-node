# LANE-REPORT — L7 (F3 LOCAL_CRDT EventEnvelope spine)

Lane ID: L7. Owner vote locked: LOCAL_CRDT. Additive schema + empty store
only. Did not edit FROZEN.lock (pins `runtime_truth_v1.py` only —
`tests/test_runtime_truth_contract_frozen.py`). Did not touch NATS,
Graphiti, Telegram LEDGER, or live writers.

## What was done
- `contracts/event_envelope_v1.py` — five mandatory fields, `ContractViolation`
- `contracts/local_crdt_store.py` — open/create empty jsonl, no migration
- `data/spine/events.jsonl` — empty durable file (0 bytes)
- `tests/test_event_envelope_v1.py` — reject/accept + empty-store proofs
- Local `git push` denied by `.cursor/hooks/deny_egress.py`
- Escalated publish: `07-HANDOFF/L7-local-crdt-spine-pr.md`

## What remains
- Writer/publisher/bus cutover (out of scope)
- Registering this contract in FROZEN.lock (not required by freeze test)
- Operator push + PR against `main` (this agent cannot publish)

## What failed
- Shell `git push` / `gh pr` blocked (egress hook).
- GitHub MCP `create_branch` 403 (org PAT lifetime > 366 days).
- `ManagePullRequest` cannot open until the branch is on the remote.

## Evidence paths
| Claim | Value | Source path | Grade | Status |
|---|---|---|---|---|
| new-file pytest | 15 passed / 0 failed / exit 0 | this-host `python3 -m pytest -q tests/test_event_envelope_v1.py` | E3 | verified |
| related freeze+no-LLM | 28 passed / 0 failed / exit 0 (15 new + 12 freeze + 1 no-LLM) | this-host `python3 -m pytest -q tests/test_event_envelope_v1.py tests/test_no_llm_import_in_reflex.py tests/test_runtime_truth_contract_frozen.py` | E3 | verified |
| FROZEN.lock | unchanged; still pins runtime_truth_v1.py | contracts/FROZEN.lock | E2 | verified |
| empty store, no migration | planted bytes unchanged after init | tests/test_event_envelope_v1.py | E3 | verified |

## Rollback steps
1. Revert this branch. Do not rewrite `FROZEN.lock` or `runtime_truth_v1.py`.
2. Do not cut over writers.
