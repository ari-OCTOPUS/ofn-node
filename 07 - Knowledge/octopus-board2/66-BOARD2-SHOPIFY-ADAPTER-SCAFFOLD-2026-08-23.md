# 66-BOARD2-SHOPIFY-ADAPTER-SCAFFOLD-2026-08-23

- **Result:** PASS (scaffold, wire closed)
- **Owner GO:** phase2-adapter
- **Added:**
  - `ofn/adapters/platforms/shopify.py` (dry_run OK; real → wire:disabled)
  - `ofn/adapters/shopify_connector.py` (HMAC verify scaffold; not registered on node yet)
  - `CHANNELS` += shopify; matrix `shopify` Layer B YELLOW
  - `packs/ziman.yaml` platforms: [etsy, shopify]
- **Prove:** available_platforms includes shopify; unittest TestShopifyAdapter OK; ofn active
- **Bak:** `/home/ari/.local/share/ofn/bak-shopify-scaffold-20260822T142851Z`
- **Evidence:** `F:\backup\06-EVIDENCE\BOARD2-SHOPIFY-ADAPTER-SCAFFOLD-2026-08-23\`
- **Still needed:** shop domain, Admin API token + webhook secret (not in chat), node connector register, SQLite products.channel CHECK migrate, Shopify plan fees in pack (not invented)
- **Etsy:** still pending-review; watch routine continues
