# Cycle-1 targeted verify
witness: 182
ts: 2026-08-27T13:20+10
run_id: revenue-cycle-1-20260827
role: verifier/critic/safety
HOLD_EXTERNAL: yes
may_authorize: false
MUTATIONS: 0 (no send/publish/pay/ads/customer message)
B2_reopen: NO
one_rework_consumed: NO

## Independent hashes (MATCH)

| file | sha256 | bytes |
|---|---|---|
| 00-INDEX.md | 8e58f40ee4c786b643a1a43aefe9cc75654008208114e9b9d52bd46cf1d4e20f | 766 |
| 01-painting-pack.md | 346e13b49d79e8e24b3f0082495fa66b93c3ec7f5ec2248b4903b34f9a898f07 | 4034 |
| 02-ziman-listing-pack.md | f211f7969c5cffd3cb3bc57b8632018cf428d86d0b48f48cfd189625e7688e6e | 3065 |
| 03-studio-offer.md | e6d54d3413a67790e6c39a4f7a0952a6fe96be0cd7deba8871afb74f28e22871 | 2769 |

Extra (not in 180 SHA list; 138 research note):
| 03b-studio-inventory-note.md | d2e493bf0908c70cb6c4ff0fed7c3b2f652d11402f5d44878f8549d433afcdb3 | 602 |

## Claims embedded (not empty)

| prefix | full message_id | on disk | in index | in pack |
|---|---|---|---|---|
| 6b5a0753 | 6b5a0753-464e-4808-b572-f77a93ae782a | claims/ yes | yes | 01-painting-pack.md |
| c2361fcc | c2361fcc-2e1e-4fdc-8620-8ef0038f6394 | claims/ yes | yes | 02-ziman-listing-pack.md |
| 23281cb3 | 23281cb3-5a37-4d3a-a545-5c9708ef2042 | claims/ yes | yes | 03-studio-offer.md |

Empty claims = INVALID_TASK: not triggered.

Note: claim envelopes use run_id=run-rapid-parallel-20260827-0254. Packs use revenue-cycle-1-20260827 and embed those IDs. Observed, not a fail (138 named these IDs).

## Checks

### real claims present
PASS. Three claim JSON files on disk. Packs cite matching claim_message_id.

### no invented leads
PASS. Painting table uses exactly the 8 real_leads from 6b5a0753. Top pick lead:pilot-pilot-2-2026-08-10T12-15-03Z is in that set. No extra lead_id. Empty suburb/job/rooms/budget left UNKNOWN.

### unknown COGS excluded
PASS. Claim has 12 SKUs. Only ZM-0003 has cited COGS (materials 6 + pack 1 = 7). ZM-GALLERY-0007..0017 cogs_aud=0 / price null excluded. Vault 22 AUD marked memory, not used as COGS. Honest "12 not 40".

### quote != cash
PASS. Painting quote skeleton has no dollar figure. Ziman margin labeled ESTIMATE/PROPOSAL. Studio price band labeled PROPOSAL. 03b pack prices UNSET. No VERIFIED_CASH.

### no external send
PASS. All packs HOLD_EXTERNAL=yes. 03b: No publish. sent=0. 182 sent nothing.

### restricted studio albums out
PASS. album-0001 (اری) and album-0002 (سکسی) not the offer. Offer uses album-unlock-20260822 drafts 0013-0022 only.

## 03b note
Observed extra. Does not replace 03. media_items 22 / drafts 24 / sent 0 / FeetFinder KYC_BLOCKED / prices UNSET. 182 did not re-query studio.sqlite this pass; counts are 138-cited. Does not invent a second offer or cash.

## Critic notes (not rework)
- Painting net value UNKNOWN on every row; pick is furthest along, not bid-ready.
- Ziman at vault 22 with free ship would be LOSS; pack already flags it.
- Studio buyer/channel/price still UNKNOWN.

## VERDICT

VERDICT=PASS
STATUS=CYCLE1_TARGETED_VERIFY_PASS
rework=NO
END
