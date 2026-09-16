# OCTOPUS UNDISCOVERED — SUMMARY (top 25)
**Stamp (AEST):** 2026-08-23T16:03:18+10:00
**Path:** `F:\backup\06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23`
**Constraints:** no invent · no live sendMessage · no money · no PWM · no secrets

## Scope
Still-dark after 2026-08-23 waves. Merges laptop scan + BOARD2/ + PI/ lane packs + RECONCILE.md. Known G01–G25 / named packs = reference only.

## Counts (all items): P0=3 P1=19 P2=22 total=44

| Rank | ID | Sev | Status | Area | Title |
|---:|---|---|---|---|---|
| 1 | U01 | P0 | PARTIAL | telegram_full_loop | A18 LIVE owner inbound Full Loop still OPEN (lab fake PASS only) |
| 2 | U08 | P0 | PARTIAL | telegram_full_loop | Telegram poll alive but inbound update SoT stale (empty polls dominate; last_update old) |
| 3 | U29 | P0 | PARTIAL | miniapp_public_url | MiniApp public Telegram menu URL not LIVE / not owner-published (reconcile P0) |
| 4 | U02 | P1 | FLAG_DRIFT | wiring_organs | WIRING connector_gap_hook=true with no organism/wiring beat consumer |
| 5 | U03 | P1 | UNWIRED | wiring_organs | synthesis_node_packs_hook ON + pointer enabled; packs orphaned from live beat |
| 6 | U04 | P1 | PARTIAL | connectors | CONNECTOR-GAP CG-001/002/003 still WAITING_OWNER_OAUTH (GA4/GSC/Ads) |
| 7 | U07 | P1 | FLAG_DRIFT | miniapp_public_url | MiniApp triple-URL residual: state named-tunnel + env trycloudflare + docs localhost primary |
| 8 | U30 | P1 | FLAG_DRIFT | wiring_organs | WIRING lead_activation=false while lead_* leg code present (flag OFF / consumer dark) |
| 9 | U09 | P1 | UNKNOWN | cross_surface | Board2 ports 8791/8792/8793 not listening on laptop (business node remote-liveness blind) |
| 10 | U10 | P1 | PARTIAL | cross_surface | Laptop NATS:4222 direct connect timed out (EDGE E2E stayed on-Pi) |
| 11 | U39 | P1 | FLAG_DRIFT | pi | Pi: MQTT loopback SoT LIVE (127.0.0.1:1883 auth) vs stale CLOSED docs risk |
| 12 | U40 | P1 | PARTIAL | pi | Pi: gateway allowlist freeze leaves non-diag cmds dark; laptop NATS client flaky |
| 13 | U43 | P1 | PARTIAL | pi | Pi: NATS ACL / octopus-core E2E creds lifecycle + production ACL still open design |
| 14 | U31 | P1 | DOC_ONLY | board2 | Board2: Instagram/GBP/Layer-C socials DOC-ONLY (registry claims, zero runtime adapters) |
| 15 | U32 | P1 | UNWIRED | board2 | Board2: ShopifyConnector scaffold never imported/registered into node |
| 16 | U33 | P1 | FLAG_DRIFT | board2 | Board2: OFN_WIRE_EMAIL/PUBLISH=1 dead flags (no .py readers) |
| 17 | U38 | P1 | UNWIRED | board2 | Board2: Google Merchant Center / Content API sync path ABSENT |
| 18 | U15 | P1 | PARTIAL | epistemics_self_audit | Epistemics advisory live but ident/channel/levels/self_reference still non-authoritative null samples |
| 19 | U16 | P1 | PARTIAL | evelab_promote | evelab/self_upgrade promoter exists but no continuous promote schedule |
| 20 | U18 | P1 | DOC_ONLY | docs_no_code | MCP 2026-07-28 Mcp-Method/Mcp-Name headers not implemented; initialize handshake still present |
| 21 | U27 | P1 | DOC_ONLY | docs_no_code | TECH-ADMISSION immediate_week TDRs not drafted (MCP headers / SSE tests / gen_ai mapping) |
| 22 | U24 | P1 | PARTIAL | handoffs_registries | NODE-PACK laptop open gates still dark: gap002_registry blocking + GitHub DietPi PAT pending |
| 23 | U06 | P2 | PARTIAL | arch_loop | Arch-loop DESIGN backlog not fully sliced (CONNECTOR-GAP hygiene + MiniApp lab UI still uncut) |
| 24 | U12 | P2 | UNWIRED | unwired_code | 4d ConsolidationCycle still NEVER-WIRED into daemon (Aug-16 UNWIRED remains real) |
| 25 | U05 | P2 | UNWIRED | connectors | Connector probe queue never runtime-probed (Similarweb/Statista/CB Insights/Finance/GitHub/HF) |

## Category rollup
- **Telegram/MiniApp P0:** U01/U08/U29 live inbound + menu/public URL still dark.
- **WIRING/flags:** U02/U03/U30 hooks ON or consumers missing; Board2 U33 dead env flags.
- **Connectors:** U04 OAuth waiting; U05 probe queue.
- **Cross-surface:** U09 Board2 ports blind; U10/U40 laptop↔Pi NATS; U39 MQTT SoT; U43 NATS ACL.
- **Board2 business:** U31–U38 socials/Shopify/Merchant/marketing.timer/healthz.
- **Epistemics/evelab/tech:** U15–U16/U18/U27.
- **Arch/handoffs:** U06 unsliced DESIGN; U11 Wave-B patch; U12 4d consolidation.

## Sibling lane packs
- `BOARD2/` — DietPi OFN deep refine
- `PI/` — OrangePi/sensorium after EDGE+HOMEO
- `RECONCILE.md` / `RECONCILE.json` — supersede notes
