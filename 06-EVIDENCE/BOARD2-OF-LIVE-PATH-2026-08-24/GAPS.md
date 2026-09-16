# GAPS — OnlyFans live path (ranked for money unblock)

Rank = dependency order to reach a **legal, gated, money-capable** OF publish later.  
Still **no live post** until second owner GO. Multi-image Ziman gallery Shopify upload remains **HOLD**. No Etsy.

## Ranked list

| Rank | Gap ID | Gap | Why it blocks money | Unblock move (still dry-default until 2nd GO) |
|------|--------|-----|---------------------|-----------------------------------------------|
| 1 | G1 | **HTTP client missing** | Even with LIVE+cookie, adapter returns `adapter:real-publish-not-implemented` — zero posts, zero revenue | Implement OF HTTP client behind dry_run; mirror telegram `urllib` call-time secrets pattern; tests for dry + NOT_IMPLEMENTED until GO |
| 2 | G2 | **Vault cookie fields** | Live branch needs `OFN_ONLYFANS_SESSION_COOKIE` (optional UA/account). Secrets.env has **no** `OFN_ONLYFANS_*` keys today | Create laptop vault path under `_ops/secrets/onlyfans/`; owner fills later; never chat/node.env |
| 3 | G3 | **Consent scope `onlyfans`** | Money-scan OFC1: only `telegram_channel` release exists; `may_publish(..., platform=onlyfans)` → OUT_OF_SCOPE / refuse | Owner records new release whose scope **names** `onlyfans` (comma/whitespace platform ids); no wildcard |
| 4 | G4 | **`OFN_ONLYFANS_LIVE`** | Without `=1`, `dry_run=False` → `wire:disabled` | Set **only** after second owner GO + HTTP wired + vault cookie + consent; never in this pack |
| 5 | G5 | **OwnerRelease / node call-site** | Telegram has `publish_to_telegram` + `require_release_context`; OF has **no** node path — cannot reuse outbox/consent/matrix safely | Add `publish_to_onlyfans` (or generic) mirroring O11 envelope: outbox-only, consent for `onlyfans`, matrix screen, two-step, dry_run default |

## Related (not in top-5 money chain but relevant)

- **G6** `OFN_WIRE_OUTBOUND` / closed gates — money-scan OFC3; leave closed unless owner widget
- **G7** Captions — auto-caption filled for TG; **do not invent** OF captions/prices
- **G8** Contract tests lack LIVE+cookie → NOT_IMPLEMENTED assertion
- **G9** Ziman multi-image gallery HOLD — do not upload Shopify as part of OF path work

## Dependency sketch

```
G1 HTTP (dry) → G2 vault cookie ready → G3 consent onlyfans
        → G5 OwnerRelease node wiring → [SECOND OWNER GO] → G4 OFN_ONLYFANS_LIVE=1
```

