# Cycle-5 B — Ziman costing/listing capability map
run_id: revenue-cycle-5-20260827
task_id: C5-ZIMAN-CAP
idempotency_key: cycle5:ziman:capability-map-v2
lane: B
claim_level: OBSERVED C1-C4 stores + Fugu RESULT
HOLD_EXTERNAL=yes | no publish | no ZM-0003 recreate

## Internalize C1-C4 stores (do not mint a new catalog)

- C1: 02-ziman-listing-pack.md — only ZM-0003 had real COGS (7)
- C2/C3: 0003 Shopify deleted; gallery 0007-0017 cogs=0 PLACEHOLDER
- C4: 02-ziman-gallery-cogs.md — GALLERY_COGS_STATUS=UNKNOWN. Stay HOLD.

Fugu already drafted:
- RESULT.json 20260824T071341Z FUGU_COPY_DRAFTS_PASS sku_count=11 apply=DRY_WAIT_OWNER_REVIEW
- ziman/COPY-DRAFTS.json (sample ZM-GALLERY-0007)

## Reconnect

Listing drafts: reuse COPY-DRAFTS.json + C1-C4 packs. Shopify apply stays DRY.
Draft model: 138 :8895 fugu via ofn/helpers/brainport.py ask(business=ziman).
Costing language / Center: laptop model_router.py collab_chat=deepseek-v4-flash — not proven on :8895.
Do not publish. Do not recreate 0003.
