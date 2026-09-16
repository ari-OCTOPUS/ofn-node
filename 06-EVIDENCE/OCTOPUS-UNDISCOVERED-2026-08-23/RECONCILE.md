# UNDISCOVERED RECONCILE — 2026-08-23T15:53:28+10:00

## Supersede
- **U14 command-trust residual** → SUPERSEDED by OCTOPUS-EDGE-NEXT-2026-08-23 M1 PASS (VERIFIED signed; reject bad/unsigned).

## Still P0
1. MiniApp public Telegram menu not LIVE
2. A18 live owner inbound Full Loop (lab fake already PASS)

## Hot P1 (pick next)
- lead_activation OFF vs code present
- 24 flags no reader
- outbox leftover surfaces post-C05
- arch-loop DESIGN slices backlog
- connector OAuth (GA4/GSC/Ads) dark
- center bridge queue never injected live
- Board2: /health vs /healthz; legs client later
- Pi: homeo freshness metric; doctor residual; NATS ACL

## Packs
- Laptop/Ios: this folder SUMMARY.md + UNDISCOVERED.json
- Board2: BOARD2/
- Pi: PI/

## Board2 deep refine (2026-08-23T15:58:35+10:00)
Source: marketing UNDISCOVERED-TOP10-DEEP.md (supersedes quick top10).
Highlights: Instagram/GBP doc-only; ShopifyConnector unwired; OFN dead flags; Studio OF adapter absent; Mining deferred; marketing.timer disabled; hypno /healthz 404; legs command locked; Bluesky unwired; Merchant API absent.
Skip already gap-closed: G01/G02/G11–G15/G20.

## U05 MiniApp public menu — 2026-08-23T06:04:29Z

- **Status: PASS**
- Evidence: `06-EVIDENCE/OCTOPUS-U05-MINIAPP-PUBLIC-MENU-2026-08-23/`
- Verified URL: `https://app.master-painting.com` (named tunnel + live HTTPS 200 shell)
- Durable env: `OCTOPUS_TG_MINIAPP=1`, `OCTOPUS_MINIAPP_URL` set in `OCTOPUS.env` + User env (stale trycloudflare replaced)
- Registration measure: already `registered` / menu matches → no `setChatMenuButton`
- `/ui` missing-URL CONFIG_NEEDED: cleared for env+json resolution path


## U07 MiniApp URL residual — 2026-08-23T16:15:00+10:00

- **Status: PASS_WITH_HOLDS**
- Evidence: `06-EVIDENCE/OCTOPUS-U07-MINIAPP-URL-RESIDUAL-2026-08-23/`
- Single durable public URL: `https://app.master-painting.com` (env + state + truth + flags)
- Process trycloudflare residual cleared; flags now durable; docs no longer claim CONFIG_NEEDED for missing public URL
- Holds: historical G10/DOC-RECONCILE bodies kept with SUPERSEDED-BY-U07 notes; optional recycle long-lived processes for Process env inheritance


## U02 connector_gap_hook FLAG_DRIFT — 2026-08-23T16:19:30+10:00

- **Status: PASS_WITH_HOLDS**
- Evidence: `06-EVIDENCE/OCTOPUS-U02-CONNECTOR-GAP-HOOK-2026-08-23/`
- Close path: A/C hybrid — keep `connector_gap_hook=true`; wire advisory consumer `organs.connector_gap.beat` into `run_session`
- Prove: consumer_fired=true; flag_drift=false; CG-001/002/003 still WAITING_OWNER_OAUTH; metrics_allowed=false; no LIVE connector claims
- Relation to U04: OAuth remains **owner HOLD** (no invent credentials); advisory surfaces gaps honestly
- Baks: `WIRING.json.bak-u02-20260823`, `run_session.py.bak-u02-20260823`


## U03 synthesis_node_packs_hook UNWIRED — 2026-08-23T16:25:39+10:00

- **Status: PASS_WITH_HOLDS**
- Evidence: `06-EVIDENCE/OCTOPUS-U03-SYNTHESIS-NODE-PACKS-2026-08-23/`
- Close path: A/C hybrid — keep `synthesis_node_packs_hook=true`; wire advisory consumer `organs.synthesis_node_packs.beat` into `run_session`
- Prove: consumer_fired=true; flag_drift=false; packs_present=3/3; HASHES ok; live_promote_claimed=false
- Holds: pack open_questions (6) remain owner surfaces; no LIVE promote; organism hot-path untouched
- Baks: `WIRING.json.bak-u03-20260823`, `run_session.py.bak-u03-20260823`

## CG-001 GA4 (2026-08-23T18:48:50+10:00)
- Status: **CLOSED** (studio property HOLD)
- OAuth readonly + vault token OK
- Map: painting 358651346 / Ziman 551101646 / studio absent
- metrics_allowed=false
