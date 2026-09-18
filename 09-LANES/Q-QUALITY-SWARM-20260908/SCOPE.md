---
type: handoff
status: active
tags: [octopus, quality, propose-only, board-180]
created: 2026-09-08
updated: 2026-09-08
lane: Q-QUALITY-SWARM-20260908
gov: V8
ladder: L2
---

# Q-QUALITY-SWARM-20260908 — scope

## Role

Quality brain, board 180, `PROPOSE_ONLY`, `may_authorize=false`.
`GOV_VERSION=V8` · `LADDER=L2` · `VERIFIED_CASH=0`.
No external send, no `0.0.0.0`, no wire-flag change, no GAP PASS without a same-domain receipt.

## Owned paths

- `09-LANES/Q-QUALITY-SWARM-20260908/`
- `tools/wiki_drift_check.py`
- `docs/NOW.md` (auto block only; never handwritten body)
- `_ops/state/wiki-drift-latest.json`
- `_ops/scripts/render_now.py` (additive wiki-drift section only)

## Forbidden

- Secrets, `.env`, tokens
- `OCTOPUS_WIRE_*` / `OFN_WIRE_*` flips
- Claiming GAP-015 PASS, revenue, sent, or booking
- Inventing serial/MAC
- `NEW_LAN_LISTENERS` increase
- Other lanes' files

## Exit gate

Lane report exists with evidence paths and rollback. GAP-015 stays UNVALIDATED unless COUNTER-SOURCE-MAP from agent 2 is present and a same-domain receipt is appended.
