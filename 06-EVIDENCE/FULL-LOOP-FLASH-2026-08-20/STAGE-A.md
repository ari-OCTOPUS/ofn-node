---
type: evidence
status: active
tags: [octopus, full-loop, stage-a, flash]
created: 2026-08-20
updated: 2026-08-20
---

# FULL-LOOP FLASH — Stage A preflight (NO NETWORK)

**5A soak: SUSPENDED.** This is not a 4h shadow-only soak and not a "full octopus" claim.

Verdict: **PASS**
`executable=true` count: `0`
model calls: `0` · AUD spent: `0` · K9 mixed: `NO` · organism.py patched: `NO`

## Hops (honest)

Sidecar reads live telemetry and an Inbox task, runs Trust→HC→WM→Metacontrol,
attaches lab memory with read-back, reserves isolated flash budget, **renders**
`POST /chat/completions`, then **STOPS**. DeepSeek was not called. `model_router.ask`
was not used (it would write `_ops/state/paid-calls.jsonl`).

Cockpit/Intake: Inbox task stand-in (`FRONTMATTER-DEBT-2026-08-20`); direct Owner Cockpit API = UNLOCATED.

## Rendered prompt (redacted, no key)

Endpoint: `https://api.deepseek.com/chat/completions`
Authorization header: `ABSENT`
prompt_sha256: `80a3225ccaa78d310259cb2470a724620312061e6865ad0315163bef3f991959`

```
وضعیت داده‌شده: HC=UNKNOWN beat=42861 D6=BETWEEN_RUN_VARIANCE GAP-001=OPEN executable=false
این request_id را برگردان و در یک جمله وضعیت داده‌شده را خلاصه کن.
```

## Evidence IDs

- `query_experiments:11`
- `query_experiments:10`
- `query_experiments:9`
- `query_experiments:8`
- `query_experiments:7`
- `get_pending_hypotheses:1086`
- `get_pending_hypotheses:1085`
- `get_pending_hypotheses:1084`
- `get_pending_hypotheses:1083`
- `get_pending_hypotheses:1082`
- `search_vault:EMPTY`
- `lm-cbe572940ac14d21`
- `live-period`
- `live-color`
- `live-cap`
- `live-tok`
- `live-unit`
- `live-id`

## Memory

- lab read-back: `PASS`
- live label: `PARTIAL_LIVE_PLUS_LAB`
- live status: `{'query_experiments': 'PASS', 'get_pending_hypotheses': 'PASS', 'search_vault': 'EMPTY', 'memory_read_patch': 'NOT_CALLED_AVOIDS_ENSURE_DB_WRITE'}`

## Skill scores

- `telemetry_interpretation`: score=0.78 mode=ADVISORY
- `homeostasis`: score=0.78 mode=ADVISORY
- `identity_assessment`: score=0.78 mode=ADVISORY
- `judge_reliability`: score=0.735 mode=ADVISORY
- `life_currency_accounting`: score=0.78 mode=ADVISORY
- `world_state_estimation`: score=0.78 mode=ADVISORY

## Budget reservation (flash, not K=9)

`{"est_aud": 0.01, "remaining_aud": 0.47, "remaining_calls": 12, "k9_mixed": false}`

## Homeostasis / judge

- HC global: `UNKNOWN`
- judge: `ADVISORY_PROPOSAL_ONLY` advisory (D6=BETWEEN_RUN_VARIANCE)
- pipeline hash: `5d8ec779734be1c6599c872edec5da39541779aaa2f90f646824062496bf667f`

## STOP

Stage B (one tiny DeepSeek Flash call) only if this pack is PASS and DEEPSEEK_API_KEY is present.
Stage C (1h) only if all six gates are green after A+B. Do not start soak #5A.
