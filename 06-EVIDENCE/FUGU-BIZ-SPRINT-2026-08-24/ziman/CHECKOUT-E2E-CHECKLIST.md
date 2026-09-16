# Ziman checkout E2E readiness (DRY — no paid order without owner GO)

## Pre-checks
- [ ] Store password OFF or use preview
- [ ] Imaged + priced product in stock
- [ ] Domestic shipping AUD configured
- [ ] ABN + GST ON
- [ ] PayPal Express / Shopify Payments Active
- [ ] Policies footer live

## Dry path (STOP before pay)
1. Open gallery product with image+price
2. Add to cart
3. Sydney checkout address
4. Confirm shipping rate
5. Confirm payment methods render
6. STOP — no paid submit without owner GO
