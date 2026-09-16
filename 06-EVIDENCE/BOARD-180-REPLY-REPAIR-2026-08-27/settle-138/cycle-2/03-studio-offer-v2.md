# Cycle-2 Studio refined offer
run_id: revenue-cycle-2-20260827
deadline_utc: 2026-08-27T06:00:00Z
baseline: Cycle-1 CLOSED READY_FOR_OWNER_SEND (182 PASS). Do not rebuild Cycle-1.
kill: HOLD_EXTERNAL; no mesh-claim; no systemctl start/enable; B2 do not reopen
HOLD_EXTERNAL=yes | may_authorize=false | NO send/publish/pay/ads/customer message

task_id: C2-STUDIO-FF-NS-FF-08
idempotency_key: cycle2:studio:NS-FF-08
lane: C
claim_level: OBSERVED captions (studio.sqlite media_items.note + CAPTIONS.json 2026-08-24) + watermarked vault paths
bottleneck: FeetFinder KYC_BLOCKED and pack prices UNSET; Board2 shot folders for 0013-0022 missing on disk even though has_original=1

## Channel lock

FeetFinder Day1 (Nova Soles). OnlyFans gated. Telegram not this cycle (138 lock). 03b: FeetFinder NovaSolesAU KYC_BLOCKED; 9 NS-FF packs ready, 0 uploaded.

## Captions bound (existing notes — not invented)

From live studio.sqlite media_items.note AND F:\\backup\\06-EVIDENCE\\BOARD2-STUDIO-AUTO-CAPTION-2026-08-24\\CAPTIONS.json (match).

| shot | media_items.note | Board2 folder | watermarked vault |
|---|---|---|---|
| shot-0013 | پاها رو به بالا مقابل پرده مخملی فیروزه‌ای؛ پوست براق، لاک قرمز تیره. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0013/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-08/primary_shot-0013_1600_wm.jpg |
| shot-0014 | پاها به دیوار خنثی تکیه؛ پوست براق/روغنی، لاک بورگوندی، نور و سایه قوی. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0014/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-07/primary_shot-0014_1600_wm.jpg |
| shot-0015 | پاها به دیوار؛ پوست براق، لاک قرمز تیره، سایه تند پاها روی دیوار. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0015/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-07/alt_shot-0015_1600_wm.jpg |
| shot-0016 | پاها روی پارچه سفید اکلیلی/توری پرحجم؛ لاک بورگوندی. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0016/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-09/alt_shot-0016_1600_wm.jpg |
| shot-0017 | یک پا روی توری سفید؛ لاک سرخایی براق با جزئی فلزی روی شست، نور پنجره. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0017/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-06/alt_shot-0017_1600_wm.jpg |
| shot-0018 | پاها میان چین توری سفید؛ لاک بورگوندی براق، فوکوس نرم. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0018/ MISSING on disk 2026-08-27 | NONE |
| shot-0019 | یک پا روی پارچه سفید بافت‌دار؛ لاک قرمز تیره، نیمه‌فریم محو در پیش‌زمینه. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0019/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-02/alt_shot-0019_1600_wm.jpg |
| shot-0020 | دو پا روی مبل روشن با پارچه توری؛ لاک قرمز براق، آینه چوبی در پس‌زمینه. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0020/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-09/primary_shot-0020_1600_wm.jpg (also collection_id=album-0002 restricted — do not primary) |
| shot-0021 | پاها روی مبل با روتختی توری سفید؛ لاک بورگوندی، انعکاس در آینه و پرده عمودی. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0021/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-09/alt_shot-0021_1600_wm.jpg |
| shot-0022 | پاها رو به بالا مقابل پرده فیروزه‌ای؛ لاک قرمز تیره، قفسه و سبد حصیری گوشه پایین. | has_original=1; folder /home/ari/.local/share/ofn/media/studio/shot-0022/ MISSING on disk 2026-08-27 | EXPORT-WATERMARKED/NS-FF-08/alt_shot-0022_1600_wm.jpg |

Canonical pattern (vault STUDIO-LIBRARY-PATHS.json): /home/ari/.local/share/ofn/media/studio/shot-NNNN/
Observed 2026-08-27: those 0013-0022 directories do not exist. Full-res path UNKNOWN. Vault thumbs may exist under AUTO-CAPTION thumbs. Watermarked JPGs exist under day1/EXPORT-WATERMARKED/.

shot-0020 collection_id=album-0002 (restricted). Keep out of primary offer.

## One refined offer (not a second decorative pack)

Reuse existing **NS-FF-08** (already watermarked):
- Primary: shot-0013 + caption above
- Alt: shot-0022 + caption above
- Paths: F:\\backup\\06-EVIDENCE\\STUDIO-NOVA-SOLES-2026-08-24\\day1\\EXPORT-WATERMARKED\\NS-FF-08\\
- Buyer: UNKNOWN (FF audience after KYC)
- Price: UNKNOWN / UNSET on LISTINGS-READY and MANIFEST (no cited listing draft binds a number)
- Time: after owner KYC; not now
- CTA (draft, not sent): Nova Soles — turquoise curtain set. Watermarked preview. No face.
- Brand: Nova Soles / @novasoles

Do not upload. Do not post TG/OF.

## Missing

live Board2 binaries for 0013-0022 folders, locked FF price, KYC clear, buyer.
