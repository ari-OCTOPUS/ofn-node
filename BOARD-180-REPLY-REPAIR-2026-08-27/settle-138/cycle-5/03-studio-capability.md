# Cycle-5 C — Studio offer/KYC/FF capability map
run_id: revenue-cycle-5-20260827
task_id: C5-STUDIO-CAP
idempotency_key: cycle5:studio:capability-map-v2
lane: C
claim_level: OBSERVED C1-C4 stores + NS-FF vault
HOLD_EXTERNAL=yes | no FF/TG/OF upload

## Internalize C1-C4 stores (do not mint a new pack)

- C1-C3: NS-FF-08 shot-0013 / 0022 captions + wm paths
- C4: 03-studio-ns-ff-08-price.md — PRICE_STATUS=UNKNOWN, KYC_BLOCKED. Stay HOLD. Do not bind.

Vault:
- EXPORT-WATERMARKED/NS-FF-01..09
- FEETFINDER-STATUS.md NovaSolesAU KYC_BLOCKED uploaded 0/9
- TG 0013/0022 skip_republish

## Reconnect

Draft/explain only via 138 :8895 fugu ask(business=studio).
Local: 180 :8081 qwen3-0.6b-q4_0.
Center teacher: laptop deepseek-v4-flash.
After owner KYC: upload existing wm packs (resume rule already written). Not this cycle. No new pack.
