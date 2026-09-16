---
type: evidence
status: active
tags: [agi-loops, pass1, read-only, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# AGI-LOOPS PASS 1 — READ-ONLY

Wave 1 stays locked. Zero live Telegram. Zero memory writes. Zero paid calls. This is not a claim of AGI or consciousness.

Closure is **L6 OWNER_VISIBLE**. Green tests are L5 at most. A family without both `telegram_surface` and `miniapp_route` cannot close.

| grain | count | role |
|---|---|---|
| 12 families AGI-01..12 | execution / SLA | close these |
| 24 discovery D01..D24 | seam checklist | hunt, do not SLA-close |
| 13 Gemini bytes | first sprint map | Pass 3 LIVE not granted |

## Stuck-at (families)

| family | stuck_at | surfaces | can_close |
|---|---|---|---|
| AGI-01 perception | L6_OWNER_VISIBLE | both routed | no (owner has not closed) |
| AGI-02 attention | L2_WIRED | UNROUTED | no |
| AGI-03 memory | L5_VERIFIED | miniapp UNROUTED | no |
| AGI-04 learning | L3_OBSERVED | miniapp UNROUTED | no |
| AGI-05 decision | L2_WIRED | miniapp UNROUTED | no |
| AGI-06 owner_surface | L6_COMPLETE | both routed | yes — still not CLOSED_AUTO |
| AGI-07 effector | L3_OBSERVED | miniapp UNROUTED | no |
| AGI-08 sleep | L2_WIRED | UNROUTED | no |
| AGI-09 immune | L4_TESTED | UNROUTED | no |
| AGI-10 identity | L2_WIRED | miniapp UNROUTED | no |
| AGI-11 reality | L2_WIRED | UNROUTED | no |
| AGI-12 survival | L2_WIRED | miniapp UNROUTED | no |

Counts: `l6_complete_count=1` · `cannot_close_count=11` · `missing_surface_count=10` · call-graph parsed 14/14.

## Defect hunt (unit tests miss these)

- D14 webhook+polling: source comment claims center never calls `getUpdates`. Runtime dual-ingest not proven. `center.py` is WORKLOCK.
- D15 bot ingesting own replies: **NEEDS_EXPLICIT_BOT_ID_FILTER** (`is_bot` absent in center).
- D17 green heartbeat / dead worker: live `doctor-pulse` still `awaiting-merge`. Pass 1 did not touch live `missions.json`.
- D08 constant 0.4: gone; EMA present (working tree).
- D07 calibration-latest: wired in `improve.py` (working tree).

## Files

- `LOOP-REGISTRY.jsonl` — 12 family + 24 discovery rows (also `_ops/state/loops/AGI-LOOP-REGISTRY.jsonl`)
- `LOOP-CALL-GRAPH.json`
- `DEFECT-HUNT.json`
- `BYTE-SPRINT.json`
- `PASS1-SUMMARY.json`

Pass 3 LIVE is **not** granted. Tests: `_ops/tests/test_agi_pass1_readonly.py` (not registered in `run_all.py`).
