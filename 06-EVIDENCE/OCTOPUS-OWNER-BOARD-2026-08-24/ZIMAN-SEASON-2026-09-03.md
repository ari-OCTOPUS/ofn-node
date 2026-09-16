---
type: truth
season: ziman-only
as_of: 2026-09-03
node: 138
hold_external_telegram: true
paid_ads: false
---

# Ziman season 2026-09-03 (live memory)

Runtime truth is the boards + Shopify. GitHub is delayed archive. No secrets in this note.

## Roles
- 138 operational gateway (DietPi 192.168.0.138). Does not choose content, price, lead, or offer.
- 180 decides. 182 verifies.
- Owner final gate. HOLD_EXTERNAL for Telegram production cards. No paid ads until a named budget.

## Store (live)
- Domain: ziman-gift.com (AUD, Basic, Australia/Sydney)
- Brand: Ziman Gift, English, Sydney handmade gifts. Not Iranian-targeting this season.
- 35 products. Vendor Ziman Gift. EN titles/handles/SEO. Farsi stripped from bodies.
- Category Gift Giving 35/35.
- Homepage SEO: "Ziman Gift | Thoughtful gifts from Sydney"
- Password protection: off
- Google & YouTube channel installed (not API-published)
- Judge.me present
- Orders last 30 days: 0
- taxesIncluded: false (owner Admin)

## Owner gates done
- Unpublish no-photo SKUs to DRAFT: `soft-flower-gift-basket`, `pink-wooden-gift-box-with-nail-set-teddy-kitkat-candle-and-party-flowers`, `strawberry-gift-box`, `light-green-woven-flower-basket`
- Frontpage: 8 first-wave products (180 rank)
- Deleted leftover "Default example products" collection

## Still owner Admin (Cloudflare blocks Grok box)
- Footer social still Shopify demo URLs
- Shipping policy page
- Tax inclusive
- Google channel Publish

## 138 mesh receipts
- `/home/ari/octopus-mesh/state/ziman/ziman-en-catalog-20260903.json` sha 5cd91e8e…
- `/home/ari/octopus-mesh/state/ziman/ziman-unlock-locks-20260903.json` sha 4e328659…
- Photo inventory sha af10f1bc… — 4 SKUs had no vault-bound photos

## Loop for automatic customers
Store event → 180 proposal → 182 EXECUTABLE_PASS → 138 Telegram card → owner APPROVE_ONCE → execute → receipt.
Do not remint painting 1522. Painting/studio out of season.