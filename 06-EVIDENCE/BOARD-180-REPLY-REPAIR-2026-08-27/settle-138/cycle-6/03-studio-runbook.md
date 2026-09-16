# Cycle-6 Studio — OCTOPUS reconnect runbook
run_id: revenue-cycle-6-20260827
task_id: C6-STUDIO-RUNBOOK
idempotency_key: cycle6:studio:brainport-listing-drafts
lane: C
claim_level: C1-C5 receipts + LISTINGS-READY + FEETFINDER-STATUS
HOLD_EXTERNAL=yes | no FF/TG/OF upload

## Memory inputs (do not rebuild)

- C1-C3 03-studio packs — NS-FF-08 shot-0013 / 0022 captions + wm paths
- C4 03-studio-ns-ff-08-price.md — PRICE_STATUS=UNKNOWN KYC_BLOCKED Stay HOLD
- C5 03-studio-capability.md — no new pack
- LISTINGS-READY.md NS-FF-01..09 (NS-FF-08 has no dollar)
- FEETFINDER-STATUS.md NovaSolesAU KYC_BLOCKED uploaded 0/9
- wm: F:\\backup\\06-EVIDENCE\\STUDIO-NOVA-SOLES-2026-08-24\\day1\\EXPORT-WATERMARKED\\

## Bind (OCTOPUS, no external agent)

1) Offer store = existing LISTINGS-READY.md + NS-FF-08 files. Do not mint a tenth pack.
2) ask(business="studio", pipeline="listing_draft", prompt=<pack theme + caption>, tier="default") against :8895 fugu for copy refine only. Do not bind a price.
3) TG 0013/0022 already published → skip_republish.
4) After owner KYC clear (not this cycle): upload existing wm packs only, resume rule already written.

## Do not

Upload FF/TG/OF. Bind generic $6-$32 to NS-FF-08. Include shot-0020 (album-0002). Start hypno.service.
