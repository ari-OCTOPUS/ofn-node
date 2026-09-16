# OCTOPUS UNDISCOVERED — Board2 lane ONLY
**Stamp:** 2026-08-23T15:56:56+10:00 (Australia/Sydney)  
**Host:** DietPi `192.168.0.138` user `ari` (not root)  
**Producer:** marketing (Board2 M4 Legs Runner) via grok-executor  
**Constraints:** readonly · no live publish · no setWebhook · no secret dump · no invent captions/TFN

Question: **What is still dark/unwired/doc-only on DietPi/ofn that gap-close did NOT cover?**

---

## Top 10 (one-liners)

1. **DOC-ONLY** | Instagram + GBP (+ Layer-C socials TikTok/FB/Pinterest/Reddit/X/YT/Threads) in registry/matrix with ZERO runtime adapters | `/home/ari/ofn/data/painting_source_registry.json` · `/home/ari/ofn/data/platform_matrix.json` · `/home/ari/ofn/docs/audit/INTEGRATION-INVENTORY.md` · `/home/ari/ofn/ofn/adapters/platforms/`
2. **UNWIRED** | `ShopifyConnector` scaffold never imported/registered into node (OAuth HTTP only; domain pack still listed register as next) | `/home/ari/ofn/ofn/adapters/shopify_connector.py` · `http_api.py` shopify branch · `F:\backup\06-EVIDENCE\BOARD2-SHOPIFY-DOMAIN-2026-08-23\RESULT.json`
3. **DEAD-FLAG** | `OFN_WIRE_EMAIL=1` + `OFN_WIRE_PUBLISH=1` in node.env but no `.py` reads those keys; `email_ses` self-only scaffold | `/home/ari/.config/ofn/node.env` · `INTEGRATION-INVENTORY.md` · `platforms/email_ses.py`
4. **ABSENT** | Studio OF/adult-platform adapter missing — publish hardwired to `telegram_channel` only (caption-gated approve→publish) | `/home/ari/ofn/ofn/node.py` · `platforms/` listing · `BOARD2-STUDIO-BATCH-QUEUE-2026-08-23`
5. **DEFERRED** | Mining leg kernel-only: `fleet/allocation/scout` present; `fleet_store/pools/scout_job` + `packs/mining.yaml` + `web/mine.html` ABSENT | `/home/ari/ofn/MEGAPROMPT-MINING.md` · `/home/ari/ofn/ofn/kernel/{fleet,allocation,scout}.py`
6. **DISABLED** | `ofn-marketing.timer` (Mon 03:30 weekly studio cycle) present but `systemctl is-enabled=disabled` | `/etc/systemd/system/ofn-marketing.timer` · `/etc/systemd/system/ofn-marketing.service`
7. **DARK** | hypno `/healthz` → **404** while `/health` → **200** (historical mismatch still live) | `curl 127.0.0.1:8895/health` · `curl 127.0.0.1:8895/healthz` · `hypno-fugu-mini.service`
8. **LOCKED** | `octopus.command.legs` / board-cp command-half intentionally absent on OFN (`/api/v1/command` + `/brain/ask` missing); G6 inert; G7 owner-only | `/home/ari/octopus-bridge/docs/COMMAND-HALF-LOCK.md` · `/home/ari/ofn/tests/test_command_surface_absent.py`
9. **UNWIRED** | Bluesky adapter file + matrix row exist but never imported into node | `/home/ari/ofn/ofn/adapters/platforms/bluesky.py` · `platform_matrix.json`
10. **ABSENT** | Google Merchant Center / Content API sync path missing — local `products.sqlite` only (for_sale=35) | `/home/ari/.local/share/ofn/products.sqlite` · grep merchant/content_api empty under `/home/ari/ofn`

---

## NOTE — what gap-close already covered (do not duplicate)

Pack: `F:\backup\06-EVIDENCE\OCTOPUS-GAP-CLOSE-2026-08-23\` (+ `BOARD2\RESULT.json`)

| ID | Status | Covered |
|----|--------|---------|
| G01 | HOLD | Ziman payouts blocked / bank+PayPal (DietPi `SHOPIFY-READY.json` later gained bank fields ~10:57+10; Shopify admin apply still OPEN) |
| G02 | HOLD | Gallery for_sale without photo binaries |
| G11 | PASS | WIRE_* ≠ auto_*; auto_post/dm/email CLOSED; studio manual |
| G12 | HOLD | Studio captions 0003–0022 empty — do not invent |
| G13 | PASS | dup shot-0002 leave; Etsy remains HELD |
| G14 | PASS | studio_wire=false vs OOB publish reconciled |
| G15 | PASS | money wires OFF/policy |
| G20 | HOLD/PARTIAL | ABN in SoT; GST confirm / note drift |

Inventory source: `OCTOPUS-GAP-INVENTORY-2026-08-23\GAPS.json`

---

## Live snapshot (readonly)

- Legs listen: `127.0.0.1:8791-8794` (ofn), `:8796` (octopus-bridge), `:8895` (hypno)
- healthz 200 on 8791–8794 + 8796; hypno healthz 404
- Active: `ofn`, `ofn-heartbeat`, `octopus-bridge`, `hypno-fugu-mini`, `cloudflared`
- `ofn-backup` last night **SUCCESS** (historical FAIL streak closed — not in top10)
- `ziman-gift.com` → `23.227.38.65` Shopify anycast (DNS seed likely closed — not in top10)
- Secrets: pointers only under `/home/ari/.local/share/ofn/secrets/` + `secrets.env` (not dumped)

## Honorable mentions

- Etsy **adapter** absent (channel enum only) — shop HELD already G13
- `setWebhook` write path absent by design (readonly `getWebhookInfo` only)
- Unlock package historically `READY_FOR_ACK` then partial execute — captions HOLD remains G12

**No live publish. Pack JSON+MD written.**
