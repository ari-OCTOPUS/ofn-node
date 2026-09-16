# SECOND-GO-CHECKLIST — before any live OnlyFans post

Owner must explicitly complete **every** item. Agents must not set `OFN_ONLYFANS_LIVE=1` or post until this checklist is signed off.

## Blockers (must be true)

- [ ] **HTTP client** implemented and reviewed; dry_run default still True; mocked tests green
- [ ] **Vault cookie** present on laptop at `F:\backup\_ops\secrets\onlyfans\` (values never in chat)
- [ ] Board2 `/home/ari/.config/ofn/secrets.env` has `OFN_ONLYFANS_SESSION_COOKIE` **name** populated by owner (agent did not invent)
- [ ] **Consent release** recorded with scope including platform id `onlyfans` (not only `telegram_channel`)
- [ ] **OwnerRelease call-site** exists (node path mirrors telegram O11: outbox-only, two-step confirm, matrix screen, kill switch, ledger, idempotency)
- [ ] Caption/media chosen from **existing** studio caption-gated items — **no invent** captions/prices
- [ ] Platform matrix `onlyfans` screen passes for that caption/framing
- [ ] `OFN_WIRE_OUTBOUND` / closed gates reviewed; owner widget if opening anything
- [ ] Kill switch **not** active; secret_rotation / partner_precondition understood
- [ ] Rate / `max_posts_24h` (24) respected
- [ ] Explicit **second owner GO** text/receipt archived under `06-EVIDENCE/`
- [ ] Then — and only then — `OFN_ONLYFANS_LIVE=1` on Board2
- [ ] First live attempt: **one** item, dry-run diff shown first, second confirm, receipt logged

## Explicitly do NOT do on second GO day

- [ ] Do not upload multi-image Ziman gallery to Shopify (HOLD)
- [ ] Do not touch Etsy
- [ ] Do not paste cookie into chat or evidence
- [ ] Do not invent OF captions/prices
- [ ] Do not set LIVE as part of HTTP-client-only slice

## Sign-off

| Field | Value |
|-------|-------|
| Owner GO stamp (AEST) | _pending_ |
| Evidence folder for GO receipt | _pending_ |
| First draft/idem key | _pending_ |

