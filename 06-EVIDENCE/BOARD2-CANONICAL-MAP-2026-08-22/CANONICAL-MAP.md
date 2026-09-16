# Board2 CANONICAL BUSINESS MAP — owner forever (2026-08-22)

Align all Board2 docs/legs to this naming. No argue.

| # | Business | People | Board2 surface | Notes |
|---|---|---|---|---|
| 1 | **Master Painting** (building painting, Sydney) | owner + Abbas | **lead / painting lane** — `lead.master-painting.com` `:8792` | CRM / lead-gen for painting company |
| 2 | **Ziman** (personalized/handmade gifts) | Maliheh | **ziman** — `ziman.master-painting.com` `:8791` · brand GiftMesh | **NOT painting** |
| 3 | **Studio / OnlyFans** | with Saba | **studio** — `studio.master-painting.com` + `app.*` `:8793` | Automation + scheduled posts from **existing library only**; no invent content |
| 4 | **Mining** | — | — | **SEPARATE; DEFERRED** — do not work now |

Also on Board2 (not customer brands): `panel` owner cockpit `:8794`; `ofn.service` node host; `hypno-fugu-mini` `:8895` adjacent miniapp.

## Live status (unchanged scan)

- lead/ziman/studio/panel healthz **200**; ofn + bridge + heartbeat + hypno-fugu-mini **active**
- ofn/wire ls-remote OK
- Mining: not touched

## GO status

### Master Painting / lead — PASS
Painting+Lead reversible #1–#3 already executed:
- gap inventory (INDEX)
- outbox dry counts (2× lead `manual_completed`)
- public catalog shape `GET /api/v1/public/catalog` → 200, 2 items, `activated:false`
Evidence: `F:\backup\06-EVIDENCE\BOARD2-PAINTING-LEAD-GO-2026-08-22\`

### Studio/Saba — unlock diagnose (scheduled-from-library)
**BLOCKED** for live schedule/post until unlock package:
- `OFN_WIRE_OUTBOUND=0` + `wire_outbound` in `OFN_EXTRA_CLOSED_GATES`
- `secret_rotation` + `partner_precondition` closed (post `GATE_OPEN_UNTIL_UTC=2026-08-17`)
- owner two-step (`release_switch.py`)
- `sender_dryrun` has no `send()` — only `dry_run_diff()`
Library ready: **66** media under `studio/shot-*` (no invent).

### Ziman / Maliheh gifts
Keep healthy only; no painting work on this leg.

### Mining
Deferred — no work.