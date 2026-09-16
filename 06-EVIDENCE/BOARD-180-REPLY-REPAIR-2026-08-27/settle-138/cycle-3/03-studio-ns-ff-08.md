# Cycle-3 Studio refine NS-FF-08 only
run_id: revenue-cycle-3-20260827
deadline_utc: 2026-08-27T06:00:00Z
baseline: Cycle-2 CLOSED READY_FOR_OWNER_SEND (182 PASS, painting=INCOMPLETE, rework=NO). Do not rebuild Cycle-2.
kill: HOLD_EXTERNAL; no mesh-claim; no systemctl start/enable; B2 do not reopen
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

task_id: C3-STUDIO-NS-FF-08
idempotency_key: cycle3:studio:NS-FF-08
lane: C
claim_level: OBSERVED MANIFEST + LISTINGS-READY + live studio.sqlite 2026-08-27 ~13:22 AEST
bottleneck: FeetFinder KYC_BLOCKED + NS-FF-08 price unset

## Claims (NS-FF-08 only — not a second pack)

Pack: NS-FF-08 Teal velvet curtain soles up
Primary: shot-0013
- note: پاها رو به بالا مقابل پرده مخملی فیروزه‌ای؛ پوست براق، لاک قرمز تیره.
- Board2: /home/ari/.local/share/ofn/photos/studio/shot-0013/0-1600.jpg
- wm: F:\\backup\\06-EVIDENCE\\STUDIO-NOVA-SOLES-2026-08-24\\day1\\EXPORT-WATERMARKED\\NS-FF-08\\primary_shot-0013_1600_wm.jpg
Alt: shot-0022
- note: پاها رو به بالا مقابل پرده فیروزه‌ای؛ لاک قرمز تیره، قفسه و سبد حصیری گوشه پایین.
- Board2: /home/ari/.local/share/ofn/photos/studio/shot-0022/0-1600.jpg
- wm: .../NS-FF-08/alt_shot-0022_1600_wm.jpg

Price: UNKNOWN. LISTINGS-READY and MANIFEST have no price on NS-FF-08. LISTING-DRAFTS.md $6-$32 are generic titles, not bound to NS-FF-08. Do not bind them.

Channel: FeetFinder Day1 LOCKED. OF gated. Telegram already published 0013 and 0022 (skip_republish). No FF/TG/OF upload this cycle.

shot-0020 stays out of this pack (media collection_id=album-0002 restricted).

## KYC_BLOCKED checklist (do not execute)

- [ ] Owner Paxum / AU payout
- [ ] FeetFinder seller + verify (NovaSolesAU currently KYC_BLOCKED; uploaded 0/9)
- [ ] Owner binds a dollar to NS-FF-08 (none cited)
- [ ] Then upload wm files only — not this cycle
- [ ] OF still gated (separate GO)

## Offer (internal)

Buyer UNKNOWN. Deliverable: existing NS-FF-08 wm pair. Time: after KYC. CTA draft not sent. Price UNKNOWN.

No second decorative pack. No upload.
