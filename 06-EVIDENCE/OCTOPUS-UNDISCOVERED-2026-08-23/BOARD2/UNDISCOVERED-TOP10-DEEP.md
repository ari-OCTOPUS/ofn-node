# BOARD2 UNDISCOVERED (deep) — 2026-08-23
Producer: marketing executor + reconcile. Readonly. No publish.

## Top 10 (verified DietPi/ofn)
1. DOC-ONLY | Instagram + GBP (+ Layer-C socials) in registry/matrix with ZERO runtime adapters | `/home/ari/ofn/data/painting_source_registry.json` · `platform_matrix.json` · `docs/audit/INTEGRATION-INVENTORY.md` · `ofn/adapters/platforms/`
2. UNWIRED | `ShopifyConnector` scaffold never imported/registered into node (OAuth HTTP only) | `ofn/adapters/shopify_connector.py` · `http_api.py` · `BOARD2-SHOPIFY-DOMAIN-2026-08-23\RESULT.json`
3. DEAD-FLAG | `OFN_WIRE_EMAIL=1` + `OFN_WIRE_PUBLISH=1` in node.env but no `.py` reads them; `email_ses` self-only | `~/.config/ofn/node.env` · INTEGRATION-INVENTORY · `platforms/email_ses.py`
4. ABSENT | Studio OF/adult adapter missing — publish hardwired to `telegram_channel` only | `ofn/node.py` · `platforms/` · BOARD2-STUDIO-BATCH-QUEUE
5. DEFERRED | Mining leg kernel-only; fleet_store/pools/scout_job + packs/mining.yaml + web/mine.html ABSENT | MEGAPROMPT-MINING.md · kernel fleet/allocation/scout
6. DISABLED | `ofn-marketing.timer` present but `systemctl is-enabled=disabled` | `/etc/systemd/system/ofn-marketing.timer`
7. DARK | hypno `/healthz` 404 while `/health` 200 | curl :8895 · hypno-fugu-mini.service
8. LOCKED | `octopus.command.legs` / board-cp command-half intentionally absent; G6 inert; G7 owner-only | octopus-bridge COMMAND-HALF-LOCK.md · test_command_surface_absent.py
9. UNWIRED | Bluesky adapter + matrix row exist but never imported into node | `platforms/bluesky.py` · platform_matrix.json
10. ABSENT | Google Merchant Content API sync missing — local products.sqlite only (for_sale=35) | products.sqlite · no merchant/content_api

## Gap-close already covered
G01 HOLD payouts; G02 HOLD photos; G11 PASS WIRE≠auto; G12 HOLD captions; G13 PASS Etsy HELD; G14/G15 PASS; G20 HOLD/PARTIAL ABN/GST.
Seeds closed: ofn-backup last SUCCESS; ziman-gift.com → Shopify 23.227.38.65.
