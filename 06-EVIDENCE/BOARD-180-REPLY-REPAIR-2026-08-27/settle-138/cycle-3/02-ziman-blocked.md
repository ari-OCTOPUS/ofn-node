# Cycle-3 Ziman BLOCKED
run_id: revenue-cycle-3-20260827
deadline_utc: 2026-08-27T06:00:00Z
baseline: Cycle-2 CLOSED READY_FOR_OWNER_SEND (182 PASS, painting=INCOMPLETE, rework=NO). Do not rebuild Cycle-2.
kill: HOLD_EXTERNAL; no mesh-claim; no systemctl start/enable; B2 do not reopen
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

task_id: C3-ZIMAN-BLOCKED
idempotency_key: cycle3:ziman:blocked-no-cogs-or-0003-recreate
lane: B
claim_level: OBSERVED prior live hunt + 138 cites
bottleneck: no SKU is live-sellable without inventing COGS or republishing a deleted product

## Claims

- ZM-0003: OFN for_sale, cogs_aud=6 + pack 1 (Cycle-1 used 7). list 22. photo=NO. Shopify Admin GET 8688841752676 = 404 deleted. Public handle 404. qty UNKNOWN.
- ZM-0002: in_progress, cogs 12, list 48, photo=NO, not for_sale.
- ZM-0004: cogs 250 list 220 LOSS. Exclude.
- ZM-0005/0006: gifted/shop-sample dups. Exclude.
- Gallery ZM-GALLERY-0007..0017: cogs_aud=0 / materials=0 / pack=0 / labour=0 in Board2 sqlite + OFN export = UNKNOWN placeholders, not a BOM. Live storefront prices 45-110 and some photos exist. Still no real COGS in receipts/notes hunted (catalog, ingest, Cycle-2 hunt).

## Verdict

BLOCKED. Need either:
- real COGS (receipt/materials) for a gallery SKU, or
- owner GO + photo + qty to recreate ZM-0003 on Shopify (not this cycle).

Do not publish. Do not pick 0004. Do not treat 0 as free.

## Missing

gallery BOM, 0003 photo/qty, live Shopify product.
