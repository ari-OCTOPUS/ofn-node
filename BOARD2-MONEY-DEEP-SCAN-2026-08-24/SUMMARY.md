# BOARD2 MONEY DEEP SCAN — 2026-08-24

**Producer:** Ios  
**SoT:** `F:\backup`  
**Constraints:** no money move / no live TG send / no PWM / no invent / no live OF

## Snapshot
Ziman **payments foot is LIVE** (bank READY, PayPal Active, GST+ABN ON, shipping `$20` AU). Cash this week is blocked by **gallery/conversion**, not rails.

## Ziman gallery blockers
| ID | Sev | Blocker |
|---|---|---|
| ZG1 | P0 | Mom-set binaries still MISSING (10 IMG_*); inbox has 180 files, only IMG_4109 matched |
| ZG2 | P0 | 14 Shopify/Meta products missing featured image (FB 35/35 publish ≠ featured) |
| ZG3 | P1 | 128 unmatched IMG_* photo-pending (no caption/price map; no invent) |
| ZG4 | P1 | Shopify ZM-0003/0006 ACTIVE with 0 photos |
| ZG5 | P2 | Etsy HELD pending persona/shop verify |

## OF consent gaps
| ID | Sev | Gap |
|---|---|---|
| OFC1 | P0 | Consent release exists for **telegram_channel only** — no `onlyfans` scope |
| OFC2 | P0 | OF adapter scaffold dry-run; real publish not implemented; no cookie; needs 2nd owner GO |
| OFC3 | P1 | `wire_outbound` + `auto_post` still closed; `OFN_WIRE_OUTBOUND=0` |
| OFC4 | P1 | Captions filled 0003–0022; OF path still gated (consent+HTTP+creds) |
| OFC5 | P2 | Early OF-ALIVE ABSENT superseded by later scaffold PASS |

## TOP 5 unlocks for cash this week
1. **CASH-1** Drop Mom-set photos → attach featured images (ZM-GALLERY-0007..0017)
2. **CASH-2** Owner SKU/caption+price map for unmatched gallery → image attach (no invent)
3. **CASH-3** Smoke-test Shopify paid checkout; watch payouts resume ~Aug 27
4. **CASH-4** Finish Etsy Persona verify (GO already out) to unhold listings
5. **CASH-5** Owner GO TG caption-gated enqueue 0003–0022; OF needs separate consent+adapter+2nd GO (not invent)

See `RESULT.json` for evidence paths.

---

## Corrections (ari 2026-08-24T15:24:14+10:00)
- Skip CASH-5 TG (0003–0022 already LIVE).
- Etsy CASH-4 STOPPED — keep HELD.
- Prefer **CASH-1 / CASH-2 / CASH-3** only.
See CORRECTIONS.md + updated TOP5.md.
