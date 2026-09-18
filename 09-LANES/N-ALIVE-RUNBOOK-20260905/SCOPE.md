---
type: handoff
status: active
lane: N-ALIVE-RUNBOOK-20260905
created: 2026-09-05
---

# N-ALIVE-RUNBOOK-20260905 — scope

## Role

Ingest `NEXT-TO-ALIVE-RUNBOOK-138.md`. Execute only what this laptop may do. `PROPOSE_ONLY`. `may_authorize: false`.
Host: `DESKTOP-KA9RFN5` / `192.168.0.191`. Not node 138 and not node 180.

## Owned paths

- `09-LANES/N-ALIVE-RUNBOOK-20260905/`

## Forbidden

- Other lanes (`U-WHY-NOT-LIVE-20260905`, `Q-MARKET-COMPARE-20260905` except read)
- Overwrite `01-TRUTH/SEASON-5-2026-09-04.md`
- Phase C send without a filled GO-TOKEN
- Flag enable, SSH write, `contradictions.csv` (L0)

## Allowed

- Phase B paper contradiction in this lane
- Phase D closeout for this ingest
- Cite prior 138 receipts; do not invent a fresh 138 preflight
- Catalog + local `find_channels.py` (no network) for OF/leg feeders already named on disk

## Exit gate

Closeout names one of the three runbook verdicts for **this** execution, and records IGN-1's already-existing verdict separately.
