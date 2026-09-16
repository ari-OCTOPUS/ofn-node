# Cycle-6 Ziman — OCTOPUS reconnect runbook
run_id: revenue-cycle-6-20260827
task_id: C6-ZIMAN-RUNBOOK
idempotency_key: cycle6:ziman:brainport-copy-drafts
lane: B
claim_level: C1-C5 receipts + Fugu RESULT
HOLD_EXTERNAL=yes | no publish | no ZM-0003 recreate

## Memory inputs (do not rebuild)

- C1 02-ziman-listing-pack.md — ZM-0003 cogs 7 only
- C3 02-ziman-blocked.md — 0003 Shopify 404; gallery 0007-0017 cogs=0 PLACEHOLDER
- C4 02-ziman-gallery-cogs.md — GALLERY_COGS_STATUS=UNKNOWN Stay HOLD
- C5 02-ziman-capability.md — reuse COPY-DRAFTS
- Fugu RESULT.json 20260824T071341Z FUGU_COPY_DRAFTS_PASS sku_count=11 apply=DRY_WAIT_OWNER_REVIEW
- Fugu ziman/COPY-DRAFTS.json sample ZM-GALLERY-0007 product_id 8688854564964

## Bind (OCTOPUS, no external agent)

1) Listing store = existing COPY-DRAFTS.json. Do not mint a new catalog.
2) ask(business="ziman", pipeline="listing_copy", prompt=<sku card>, tier="default") against :8895 fugu only if a draft must be refreshed. Prefer the 11 already-passing drafts.
3) Shopify apply stays DRY_WAIT_OWNER_REVIEW. No live mutate.
4) Costing: still UNKNOWN for gallery. 0-placeholder stays UNKNOWN. Do not treat as free.

## Do not

Publish. Recreate ZM-0003. Pick 0004 LOSS. Start hypno.service. Write secrets.
