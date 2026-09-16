# Cycle-5 targeted verify
witness: 182
ts: 2026-08-27T13:48+10
run_id: revenue-cycle-5-20260827
role: verifier/critic/safety
kind: CAPABILITY_MAP
HOLD_EXTERNAL: yes
may_authorize: false
MUTATIONS: 0
B2_reopen: NO
one_rework_consumed: NO
C2 04-VERIFY: DO NOT TOUCH 8b40677f
C3 04-VERIFY: DO NOT TOUCH a64b5138
C4 04-VERIFY: DO NOT TOUCH 2b9a2593
NOTE: 04-llm-route.md is an artifact, not this file. This verdict is 05-VERIFY.md.

## Independent hashes (box MATCH 180)

| file | sha256 | bytes | result |
|---|---|---|---|
| 00-INDEX.md | 0ae9cb6657d7f54434c640c87a14322d067e97561a977242b21461a552154532 | 1268 | MATCH |
| 01-painting-capability.md | ec0b37ea7d28b6448c3fece6e5050c27c9073b57a26adf81f40067fb18dcf57c | 1960 | MATCH |
| 02-ziman-capability.md | 41278c6d479647bf432d0517606705ea97b4cda142eaef4afa8232453da39f41 | 1557 | MATCH |
| 03-studio-capability.md | c08b8f9ad79c8b98ed091db081161587cf1349b286fef7e64e236853ad66da9f | 1369 | MATCH |
| 04-llm-route.md | 7881d32b704b266cb931443731889fea8b67f8e2fe2acb78e9061104397421f7 | 2661 | MATCH |

SHA 5/5 MATCH. Laptop settle-138 hop was down at write time; box copy used for hash.

## Claims

Embedded citations present (Fugu DAY1/INTAKE/RESULT/COPY-DRAFTS, catalog, NS-FF packs, FEETFINDER-STATUS, brainport.py, DEEPSEEK-CUTOVER, HEALTH 8895). Not empty. INVALID_TASK not triggered.

## Checks

### no new model/unit
PASS. Map says reconnect existing brainport/8895/8081 only. No new systemd unit. DeepSeek = env flip on existing BrainPort.

### painting
PASS. Fugu inbox + BrainPort ALLOW named. HUMAN send gate kept. No Snapp send. Client channel still UNKNOWN (Stay HOLD).

### ziman
PASS. COPY-DRAFTS exist (11/11 FUGU_COPY_DRAFTS_PASS). no_shopify_write. 0003 not recreated. Gallery COGS still UNKNOWN. No publish.

### studio
PASS. NS-FF-01..09 exist. NS-FF-08 0013/0022. KYC_BLOCKED. Price unbound. No upload. shot-0020 out.

### llm
PASS as map (182 did not re-curl 8895 this pass). Pack cites 8895 HTTP 200 LIVE; hypno.service INACTIVE named; DeepSeek = BRAIN_PROVIDER flip not a new gateway; 180 :8081 local tier.

### no external send
PASS. HOLD_EXTERNAL. 182 sent nothing.

## Critic notes (not rework)
- This is a capability map, not internalized runtime. EXTERNAL_AGENT_DISCONNECTED not proven this cycle.
- 8895 live vs hypno inactive is a reconnect job, not a fail of the map.
- VERIFIED_CASH still 0.

## VERDICT

VERDICT=PASS
STATUS=CYCLE5_CAPABILITY_MAP_VERIFY_PASS
rework=NO
END
