# ORGAN-MAP — 2026-08-20 · agent_C

Lane: `organs_and_afferent_wiring`. Telegram lane not touched. No files deleted.

Machine copy: `ORGANS.json`.

## Counts

| class | n |
|---|---|
| LIVE | 8 |
| SKELETON | 4 |
| ORPHAN | 0 (this catalog is organs, not all modules) |
| DEAD | 0 |
| DUPLICATE | 0 |
| UNSAFE_TO_WIRE | 2 |
| **total** | **14** |

Module-level orphans (~101 / ~18 weighty on 2026-08-16) were **not re-scanned** this session (`orphan_scan` hung under AV + worktree copy). Mapper instead listed **1257** `_ops/*.py` files newer than the master map (live cartographer count was 1256–1271).

## Table

| organ | class | graph | fresh | note |
|---|---|---|---|---|
| knowledge | LIVE (sidecar) | yes | yes after today | organism still reports `live=false` skeleton until C-047 hook |
| cartographer | LIVE | yes | lists yes / map stale 2026-07-29 | was count-only; now path list |
| lead | LIVE | yes | flaky | diagnose only; `phi` not comparable |
| heart | LIVE | yes | yes | arbiter GREEN |
| cortex | LIVE | yes | yes | did not hear organs until cognition_inbox |
| business_brain | LIVE | yes | yes | same |
| doctor | LIVE | yes | yes | RFC store currently 2 rows |
| ziman | LIVE | yes | yes | inventory hint, propose-only |
| mining | SKELETON | yes | no | `nodes_total=0`; **162 is a research plan**, not a measured fleet |
| crypto | SKELETON | yes | no | 10 snapshots, age ~66d, zero trades |
| sync_agent | SKELETON | flag on | no | `inert-until-flag-on` |
| afferent_bus | SKELETON | school on | no | reads spend-shape, not vault notes |
| accounting | UNSAFE_TO_WIRE | yes | count/mtime yes | PII red line on amounts |
| studio_pf | UNSAFE_TO_WIRE | yes | gated | GATE-STAMP-GO absent |

## Honest split

- **Sidecar LIVE today:** knowledge afferent (655 events), mapper path list (1257).
- **Organism loop still skeleton for knowledge:** `ORGANISM-STATE.business_legs.knowledge.live=false`. Hook is `live_organism_hook=false` (no restart, `wiring.py` WORKLOCK).
