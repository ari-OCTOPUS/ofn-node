# Cycle-2 targeted verify
witness: 182
ts: 2026-08-27T13:30+10
run_id: revenue-cycle-2-20260827
role: verifier/critic/safety
HOLD_EXTERNAL: yes
may_authorize: false
MUTATIONS: 0
B2_reopen: NO
one_rework_consumed: NO
SoT: settle-138\\cycle-2\\ (laptop) + /home/box/shared/cycle-2-20260827 (same SHAs after 02 amend)

## Independent hashes

| file | sha256 | bytes | result |
|---|---|---|---|
| 00-INDEX.md | da0a6c60ac88725052f5eaa15bbe1b43a4a212f28e4d2c4781ea0642291bc712 | 1276 | MATCH |
| 01-painting-facts.md | 46a102db88d7b75a3637fc22db287d9719c49a6d7771c0eb432cddfa2777a53b | 2536 | MATCH unchanged |
| 02-ziman-listing-v2.md | 181f475bd99ed69d7e4a27623b0b6ae21d8862d6d1affc0e8271f8b4edaa6297 | 3056 | MATCH (NEW; was 796c477b) |
| 03-studio-offer-v2.md | 8a037131120a9965be3b1287c4c978595a0398b0b3e569d6c0b5fdf347e6396f | 5211 | MATCH unchanged |

SHA 4/4 MATCH against amended set. Box and laptop 02 now agree.

## Claims

No claims/ JSON dir. Index+manifest embed: painting.sqlite row lead:pilot-pilot-2-2026-08-10T12-15-03Z; 138 products.sqlite+OFN; media_items.note 0013-0022 + NS-FF-08. Not empty. INVALID_TASK not triggered.

## Checks

### painting
PASS as pilot, INCOMPLETE on vault jobs.
Pick is still lead:pilot-pilot-2-2026-08-10T12-15-03Z. Name مشتری آزمایشی دو. Phone 0411000002 labeled pilot / not a verified live buyer. Do not call/SMS this cycle unless owner says the number is real. No send proposed.
Snapp Fitness + Romeo ABSENT from pack. Not invented. painting=INCOMPLETE (facts outside painting.sqlite not in this pack).

### ziman (amended 02)
PASS.
Only ZM-0003 is for_sale real-COGS (7). ZM-0004 LOSS excluded. Gallery 0007-0017 UNKNOWN cost excluded. photo=NO. Do not publish.
NEW facts present: Shopify product 8688841752676 DELETED (admin 404 + public handle 404). Do not live-sell ZM-0003. qty=UNKNOWN. cogs conflict materials+pack=7 vs cogs_aud=6 both OBSERVED.

### studio
PASS.
Captions bound to media_items.note (not invented). Offer is NS-FF-08 shot-0013 primary + shot-0022 alt. shot-0020 album-0002 restricted not primary. No TG/OF upload. Price UNKNOWN. KYC_BLOCKED.

### quote != cash
PASS. Painting total UNKNOWN. Ziman margin PROPOSAL. Studio price UNKNOWN/UNSET. No VERIFIED_CASH.

### no external send
PASS. HOLD_EXTERNAL throughout. 182 sent nothing.

## Critic notes (not rework)
- Painting INCOMPLETE: real vault jobs not in pack; CRM pick remains a pilot.
- Ziman cannot live-sell: product deleted, no photo, no qty.
- Studio Board2 shot folders missing on disk; watermarked vault only.

## VERDICT

VERDICT=PASS
painting=INCOMPLETE
STATUS=CYCLE2_TARGETED_VERIFY_PASS
rework=NO
END
