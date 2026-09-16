# Cycle-2 Ziman listing pack v2
run_id: revenue-cycle-2-20260827
deadline_utc: 2026-08-27T06:00:00Z
baseline: Cycle-1 CLOSED READY_FOR_OWNER_SEND (182 PASS). Do not rebuild Cycle-1.
kill: HOLD_EXTERNAL; no mesh-claim; no systemctl start/enable; B2 do not reopen
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

task_id: C2-ZIMAN-LIST-V2
idempotency_key: cycle2:ziman:ZM-0003
lane: B
claim_source: 138 Cycle-2 evidence Board2 products.sqlite + OFN export (do not reopen Cycle-1)
claim_level: OBSERVED (138-cited) + live hunt 2026-08-27 ~13:25 AEST
bottleneck: live Shopify ZM-0003 is DELETED (admin 404); no photo; no qty. Cannot live-sell this SKU.

## Filter (138)

With real COGS:
- ZM-0003 ظرف آزمایشی for_sale cogs 6+pack 1=7 list 22 photo=NO Shopify Cost empty. Only for_sale real-COGS.
- ZM-0002 گلدان آزمایشی in_progress cogs 12+pack 2 list 48 photo=NO. Not for_sale. NEXT blocked.
- ZM-0004 ازمایشی in_progress cogs 250 list 220 LOSS. Exclude.
- ZM-0005/0006 gifted dups of 0002/0003. Exclude.
unknown_cost=35 including gallery 0007-0017 (0007 checkout-ready AUD75 but cogs_aud=0 default).

Do not pick a loss or unknown-cost SKU. Gallery still UNKNOWN COGS.

## Pick

SKU: ZM-0003
name: ظرف آزمایشی
state: for_sale
COGS: 7.00 AUD
list: 22.00 AUD
photo: NO
Shopify Cost: empty
qty: UNKNOWN (OFN has no inventory column; Shopify product gone)
tax class: SKU-level UNKNOWN. Store GST collect ON OBSERVED (SHOPIFY-READY.json 2026-08-23). Whether 22 includes GST: UNKNOWN.
activated: false / not on store. OBSERVED 2026-08-27: Admin GET /products/8688841752676.json HTTP 404 (deleted). Public products.json has no ZM-0003. Handle ظرف-آزمایشی 404. OFN state=for_sale is not storefront activation.
cogs_field_conflict: materials 6 + pack 1 = 7 vs stored cogs_aud=6. Both OBSERVED. Cycle-1 used 7.
shopify_last_write: 2026-08-22T15:17:43Z shopify_price=22.00 then product deleted.

## Margin (PROPOSAL, not cash)

If list 22 includes GST: GST 2.00; COGS 7; fee ESTIMATE ~0.87; net before ship ~12.
Domestic ship memory AUD 20 extra. Free-ship at 22 = LOSS. Do not.
Floor unchanged: pickup/ship-extra 24-28 PROPOSAL; ship-included 44-48 PROPOSAL. Not published.

## Listing draft v2 (do not publish)

Title: ظرف آزمایشی / Test bowl — Ziman
SKU: ZM-0003
Status: draft
Price: 22 cited — lock only after photo exists OR owner accepts no-photo draft
Photo: MISSING — this is the kill for publish
Inventory: UNKNOWN
Ship: domestic 20 / intl OFF
GST: collect ON at store; SKU tax UNKNOWN

## Next

1) Do not republish a deleted product this cycle.
2) Recreate ZM-0003 only after owner GO + one photo + qty. Until then HOLD.
3) Do not switch to 0002 until for_sale + photo.
4) Do not use gallery 0007-0017: live prices/photos exist, real COGS still 0-placeholder UNKNOWN.

## Missing / live hunt extras

photo binary, qty, SKU tax row, live Shopify product (404), resolve cogs_aud 6 vs 7.
Archived leftover ZM-0006 (same name, 22, qty 0, 0 photos) is not a pick.
