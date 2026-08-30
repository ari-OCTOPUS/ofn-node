# Cycle-6 targeted verify
witness: 182
ts: 2026-08-27T13:51+10
run_id: revenue-cycle-6-20260827
role: verifier/critic/safety
kind: INTERNAL_RUNBOOK
HOLD_EXTERNAL: yes
may_authorize: false
MUTATIONS: 0
B2_reopen: NO
one_rework_consumed: NO
C2 04-VERIFY: DO NOT TOUCH 8b40677f
C3 04-VERIFY: DO NOT TOUCH a64b5138
C4 04-VERIFY: DO NOT TOUCH 2b9a2593
C5 05-VERIFY: DO NOT TOUCH 651490f0
NOTE: 04-llm-runbook.md is an artifact, not this file. This verdict is 05-VERIFY.md.

## Independent hashes (box MATCH 180)

| file | sha256 | bytes | result |
|---|---|---|---|
| 00-INDEX.md | 59b9f5c6a4f925c0aaf110a1061ed81aa845713970d044a429400c406f8aa502 | 1479 | MATCH |
| 01-painting-runbook.md | b03430831cbbc45d9b830fc860361cdbb7108856be57e55a1742d69c0205160f | 1515 | MATCH |
| 02-ziman-runbook.md | fecd6ddbf3bdd18dee02be542424b769cfdacbc6b364f1d274fea4c6b244bf4e | 1265 | MATCH |
| 03-studio-runbook.md | b3b00a87fa76c1792de689c95c56cab2599d5e118a373c3ac9fdb4af4b4216c2 | 1276 | MATCH |
| 04-llm-runbook.md | c373d5a8393648957d19086824bed49800d80725fc859aa852098be6875028ca | 1928 | MATCH |

SHA 5/5 MATCH. Manifest CYCLE-6-MANIFEST.json sha256=43b1dc7a1048ba12bd20bd7eac3c247ca397b62ef0dd13a9d38b8599a844b4d6 extra (not in required set).

## Claims

Embedded citations present, not empty. INVALID_TASK not triggered.
- painting: C3 01-painting.md + C4 01-painting-snapp-contact.md + Fugu painting/DAY1.md + INTAKE.json
- ziman: C4 02-ziman-gallery-cogs.md + Fugu RESULT.json + ziman/COPY-DRAFTS.json
- studio: C4 03-studio-ns-ff-08-price.md + LISTINGS-READY.md + FEETFINDER-STATUS.md
- llm: C5 04-llm-route.md + ofn/helpers/brainport.py + 8895 hypno-fugu-mini + 180 :8081 qwen3-0.6b-q4_0 + model_router.py deepseek-v4-flash

## Checks

### no new unit/path / no systemctl start / no secrets
PASS. Index + 04 forbid systemctl start/enable, new unit, fifth path. DeepSeek key named as vault-only (not in these files). 182 wrote no secrets.

### 8895 / DeepSeek / 180 :8081 / laptop flip
PASS. 04 binds 8895 = hypno-fugu-mini only; "DeepSeek is NOT proven on :8895. Do not point this port at DeepSeek." 180 :8081 = local tier only (qwen3-0.6b-q4_0). Laptop model_router collab_chat=deepseek-v4-flash documented BRAIN_PROVIDER flip only.

### DEAD left dead
PASS. 04 lists hypno.service | /brain/ask | octopus-wire | ofn-backup | ollama :11434 | 182 no LLM. No start proposed.

### lanes bind existing stores only
PASS.
- painting: Fugu painting/inbox + lead.schema.json; outbox drafts only; APPROVE_QUOTE gate; no Snapp contact
- ziman: existing COPY-DRAFTS.json (prefer 11); DRY_WAIT_OWNER_REVIEW; gallery COGS still UNKNOWN; 0003 not recreated; 0004 out
- studio: LISTINGS-READY + NS-FF-08; no price bind; KYC_BLOCKED; shot-0020 out; skip_republish 0013/0022

### no send/publish
PASS. HOLD_EXTERNAL. HUMAN send gate. No FF/TG/OF upload. 182 sent nothing. MUTATIONS=0.

## Critic notes (not rework)
- Runbook internalization of C5 map, not a live ask() proof. EXTERNAL_AGENT_DISCONNECTED still unproven this cycle.
- 182 did not re-curl 8895 and did not start units.
- VERIFIED_CASH still 0.

## VERDICT

VERDICT=PASS
STATUS=CYCLE6_INTERNAL_RUNBOOK_VERIFY_PASS
rework=NO
END
