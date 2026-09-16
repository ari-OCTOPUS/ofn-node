# Cycle-1 Ziman listing pack
run_id: revenue-cycle-1-20260827
claim_message_id: c2361fcc-2e1e-4fdc-8620-8ef0038f6394
lane: B
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message
claim_level: OBSERVED (embedded 12 SKUs) + vault memory marked separately
B2: do not reopen

## Filter

Directive: real COGS only; no unknown-cost / loss SKU; no fake sale; missing facts = UNKNOWN.

Cited products: 12 (not 40). 11 gallery SKUs have cogs_aud=0, materials=0, packaging=0, price_aud=null in the claim → UNKNOWN cost → excluded from pick.
Only **ZM-0003** has real cited COGS.

| sku | name | cited COGS AUD | cited price | vault price (memory, 2026-08-22/23) | verdict |
|---|---|---|---|---|---|
| ZM-0003 | ظرف آزمایشی | materials 6 + pack 1 = 7; labour 0 | null | public catalog 22 AUD, activated=false | ONLY ready+margin candidate |
| ZM-GALLERY-0007..0017 | gallery gifts | 0 (UNKNOWN) | null | 45-110 AUD in CATALOG.json | unknown-cost FLAG; not margin-ready |

Vault prices are memory, not embedded claims. They do not create COGS.

## Top pick

**SKU ZM-0003 — ظرف آزمایشی**
state: for_sale (cited)
channel/category: null (UNKNOWN)
COGS cited: 7.00 AUD (6 materials + 1 packaging)
labour: 0 h @ 0 AUD/h (cited)
price cited: UNKNOWN
vault list memory: 22.00 AUD; GST-inclusive UNKNOWN; activated false
GST: business GST-registered (owner-confirmed 2026-08-23); Shopify collect GST ON. SKU tax class UNKNOWN.
Domestic ship memory: AUD 20 flat; intl OFF.
Fees: UNKNOWN. ESTIMATE only ~2.6% + 0.30 AUD if card.

### Margin if vault 22 is used (PROPOSAL, not verified)

Gross 22.00
COGS 7.00
GST 1/11 of 22 = 2.00 if price includes GST (assumption)
Fee estimate 0.87
Ship 20.00 if charged to buyer separately (do not bury in 22)
Product net before ship: 22 - 7 - 2.00 - 0.87 ≈ 12.13 AUD (ESTIMATE)
If ship must come out of 22: 22 - 7 - 2 - 0.87 - 20 = -7.87 LOSS. Do not sell at 22 with free ship.

Floor (PROPOSAL):
- Pickup / ship extra: list 24-28 AUD
- Ship included: list 44-48 AUD
Do not publish either number this cycle.

## Listing draft (do not publish)

Title: ظرف آزمایشی / Test bowl — handmade gift (Ziman)
SKU: ZM-0003
Vendor: Ziman / aram@ziman-gift.com
Status: draft
Price: UNKNOWN — wait for 138/owner to lock floor above
GST: collect (store ON); tax class UNKNOWN
Shipping: domestic AUD 20; intl OFF
Inventory: UNKNOWN qty
Photos: UNKNOWN in this claim (do not invent)
Description (draft):
Handmade test bowl from Ziman. One physical piece. Colour/size UNKNOWN until photo+measure.
Not a food-safety claim. Sydney domestic post or pickup UNKNOWN.

## Dead-stock / loss flags

- ZM-GALLERY-0007..0017: UNKNOWN COGS. Vault prices exist; margin unverifiable.
- ZM-0003 at 22 with free shipping: LOSS.
- Old public catalog activated=false: not a live listing.

## Bundle above floor

No second real-COGS SKU in the claim. No honest bundle.

## Missing facts

qty, photo, dimensions, food-safe, locked list price, fee schedule, pickup vs post, labour time (cited 0 may be incomplete).
