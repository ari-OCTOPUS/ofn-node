---
type: offering
project: ZIMAN
status: draft
updated: 2026-07-12
---

# CATALOG — Product families (C1–C4)

> Inventory normalisation pending owner classification approach.

| ID | Family | Type | Perishable | Notes |
|---|---|---|---|---|
| C1 | Artificial floral arrangements | physical | no | lasting decor / gift |
| C2 | Gift baskets | physical | depends | birthday / thank-you / corporate candidate |
| C3 | Framed floral shadow boxes | personalised product/service | no | **hero candidate** — photo/name/date |
| C4 | Chocolate hampers | physical | **yes** | **local delivery/pickup only** |

## Rules
- 50 ready physical products (OWNER_INPUT) ≠ 50 unique SKUs
- 50 ≠ weekly capacity
- SKU cards must link photo file → product_id
- Public price only after owner approval
- Alcohol never implied for decorative bottles

## SKU card template (next)
```yaml
product_id: ZM-C3-0001
family: C3
title: ""
variation: ""
qty_on_hand: 0
photo_paths: []
cost_aud: null
price_aud_status: unapproved
personalisation: false
ship_policy: local_or_tbd
status: draft
```

## Photo sources (existing)
- `08 - Assets/Photos/WhatsApp-2026/` (product batch)
- map only after Product IDs exist
