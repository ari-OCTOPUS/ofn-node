# 182 content verify (rework drafts)
witness: 182
ts: 2026-08-27T14:55+10
run_id: run-internal-autonomy-20260827T044921Z-3b681097
kind: INTERNAL_AUTONOMY_DRAFTS
HOLD_EXTERNAL: yes
may_authorize: false
MUTATIONS: 0
C5-C7: DO NOT TOUCH
cycle8: false
prior: 182-VERIFY 4e125068 REWORK (drafts were ABSENT)

path: /home/ari/octopus-mesh/state/runs/run-internal-autonomy-20260827T044921Z-3b681097/

## Independent hashes

| file | sha256 | result |
|---|---|---|
| painting.quote_draft.json | 55c3713ae59ecedd921c743c27d1d99ad83d1dc942d9c72a7044cff8cea34597 | MATCH |
| ziman.listing_draft.json | 845498f9fc041ed7ee6d12c71617f1d80c94874fec842079f05fa5fc1921f2f2 | MATCH |
| studio.offer_draft.json | 72f681fadb4ca994e591090bc97e7998bdbd5c46fde4e5d8ae940f4fa099117d | MATCH |
| painting.task.json | 322a85ee578cfd85928d049eab3f48c4928ac3cb6ecb3a9a539ad3854dfac73e | UNCHANGED |
| ziman.task.json | 0e4cd2fd47514f2918b20eeec42fd49e37070fd36573e9b03bbc613dd2799b85 | UNCHANGED |
| studio.task.json | 48b8242e695e61d1356f254e8d6f1b20d0efcf77c5c81de1d40216ac8515aa8d | UNCHANGED |

## Content

### painting
PASS BLOCKED_HONEST. Snapp Fitness, 0100-A/0101-B A$1815, client_contact=UNKNOWN, unsigned, do_not_send, crm_pilots_excluded. Offer = chase existing quotes, not a new invented price. sent=false. owner_ask=contact or GO.

### ziman
PASS BLOCKED_HONEST. listing_draft=null. No invent COGS. 0003 DELETED out, 0004 LOSS out, gallery 0007-0017 UNKNOWN. published=false. owner_ask=real COGS or GO+photo. Stay HOLD 0003.

### studio
PASS BLOCKED_HONEST. NS-FF-08 shots 0013+0022, price=UNKNOWN, KYC_BLOCKED, uploaded=false. CTA=do not publish until price+KYC. No OF. owner_ask=set price + clear KYC.
CRITIC (not rework): slogan "Sexy is an energy, not a body type" is uncited in this file.

## Inference
dispatch_clean_3of3=false (honest).
painting model_route_used=none (8895 is hypno /api/chat not OpenAI)
ziman model_route_used=center:model_router_not_called (DeepSeek not on 8895)
studio model_route_used=180:8081_unreachable
Drafts are local honest-block artifacts, not brain completions.

## Checks
drafts present 3/3: PASS
external_effects=0: PASS
HOLD_EXTERNAL / no send: PASS
no cycle-8: PASS
tasks unchanged: PASS
READY_FOR_OWNER_APPROVAL as owner-ask batch: PASS (three blockers, not a live send)
receipt self-hash f1a0e8b8 vs file 3011f6ba: MISMATCH (receipt hashed itself before write; not a draft fail)

## VERDICT

VERDICT=PASS
lanes=BLOCKED_HONEST
content_verified=true
inference_3of3=false
owner_packet=READY_FOR_OWNER_DECISION_BATCH
external_effects=0
rework=NO
END
