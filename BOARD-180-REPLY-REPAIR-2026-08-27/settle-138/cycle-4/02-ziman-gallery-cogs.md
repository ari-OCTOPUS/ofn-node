# Cycle-4 Ziman — gallery COGS hunt
run_id: revenue-cycle-4-20260827
deadline_utc: 2026-08-27T10:00:00Z
baseline: Cycle-3 CLOSED. Do not write Cycle-3 again. Do not recreate ZM-0003.
kill: HOLD_EXTERNAL; no mesh-claim; no systemctl start/enable; B2 do not reopen
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

task_id: C4-ZIMAN-GALLERY-COGS
idempotency_key: cycle4:ziman:gallery-cogs-unknown
lane: B
claim_level: OBSERVED vault catalog + tracker + Accounting
bottleneck: no real BOM/receipt for gallery SKUs

## Claims

GALLERY_COGS_STATUS=UNKNOWN

- F:\\backup\\03 - Projects\\Ziman Galerry\\03-Offering\\ziman-catalog.json
  36 photo products (ZIM-F1/F2/F3/F4 + OTHER). Fields: product_id/family/photo/one_line only.
  data_gaps quote: "No pricing, stock, or capacity data was inferable from images and none was fabricated."
- CATALOG.md (2026-07-12 grounded-v1): "هیچ قیمت/ظرفیت ساخته نشد."
- content/first-sale-pack.md: warm-market DM copy. No SKU costs.
- content/Ziman-FirstSale-Tracker.xlsx: template rows ([نام ۱]…). ستون مبلغ (AUD) empty / placeholder. Not a receipt.
- Accounting: Ziman COGS is a planned ledger action only (README/REGISTRY/adapter.yaml). No per-SKU receipt. Maliheh bank lines are transfers/Amazon, not gallery BOM.
- Cycle-2/3: Board2 ZM-GALLERY-0007..0017 cogs_aud=0 remain PLACEHOLDER, not a cost.
- ZM-0003 still deleted (Shopify 8688841752676 404). Do not recreate. 0003 materials 6+pack 1=7 is not gallery COGS.
- ZM-0004 LOSS. Exclude.

## Verdict

BLOCKED. Honest empty. Need owner receipt/materials for a named gallery SKU, or a later GO+photo+qty for 0003 (not this cycle).
Do not publish. Do not treat 0 as free.
