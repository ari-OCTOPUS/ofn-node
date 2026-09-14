# W4 — Inhibition Spec (SHADOW ONLY, no runtime activation)

## Route/Provider-Task Map (from live config + budget ledger)

| route | provider | task_type | call count (ledger) | est. cost |
|---|---|---|---|---|
| deterministic→local-180 | llama.cpp qwen3-0.6b | free-form patch | ~2/day | $0 (local) |
| deepseek | deepseek-chat | self-patch | 2 recent | ~$0.03/call |
| gemini | gemini-3.8-flash | (configured, no recent calls) | 0 | — |
| openai | gpt-5.6-terra | (configured, no recent calls) | 0 | — |

## Proposed Policies (NONE activated)

### P1: Suppress paid-first on self-patch tasks
- **scope**: task purpose == "free-form-patch" AND source == "self-feed"
- **reason**: local model already produces valid patches in 10.6s (measured);
  paid fallback only burns budget on tasks the local model can handle
- **evidence**: G18 measurement showed local model at 384-token cap produces
  complete valid patches; budget ledger shows deepseek calls for tasks
  that could have been local-first
- **estimated_savings**: ~$0.06/day (2 paid calls × $0.03) — COUNTERFACTUAL
  (not observed cost; assumption: local model would have succeeded)
- **expiry**: 7 days after activation
- **release condition**: local model success rate drops below 70%

### P2: Park low-priority queued requests during active witness cycles
- **scope**: priority > 5 in canary-requests when PENDING is non-empty
- **reason**: witness cycle occupies the single Class-B slot; lower-priority
  requests re-evaluate each tick anyway (no starvation after fix)
- **estimated_savings**: zero monetary; saves tick cycles
- **status**: ALREADY IMPLEMENTED by the no-starvation fix (budget-blocked
  requests skip instead of blocking the loop) — this is a no-op observation

### P3: (no third policy — honest)
No policy with positive savings beyond P1 was found in the current data.

## False-Positive Risk
"Zero false-positives in the sample" — sample size is 2 recent paid calls;
insufficient for any claim about false-positive rates.

# W5 — Retention & Resurrection Spec (SHADOW ONLY)

## Candidate Subjects (from actual filesystem)

| subject | count | age | rationale |
|---|---|---|---|
| superseded-tasks/ | 4 files | 1-5 days | replaced by TRIO |
| /tmp/b5-*/ | 10 dirs | hours | test fixtures (already cleaned per session) |
| .pre-* preimages in ops-agent/ | 5 files | 1-5 days | rollback chain (KEEP until post-deploy) |
| ops-receipts rows > 7 days | ~800 rows | >7 days | audit trail (PROTECTED) |
| prediction-ledger | 7 rows | mixed | unique evidence (PROTECTED) |

## Proposed Lifecycle (NOT EXECUTED)

```
ACTIVE → COLD (14 days no access) → QUARANTINE_PROPOSED → RETENTION_REVIEW
```

### Eligible for COLD transition (shadow analysis only):
- NOTE: these files are 1-5 days old (<7d protected, <14d COLD threshold) — inventory is NOT eligibility; ZERO candidates currently eligible
- .pre-g27/g27v2/g28e/g29/g30 preimages: 5 files (superseded by later preimages)

### NOT eligible (protected):
- ops-receipts.jsonl (append-only chain)
- prediction-ledger.jsonl (unique evidence)
- autonomy/receipts.jsonl
- all files in owner_dialogue/ (active decision chain)
- all .env files (secrets, never touched)
- 06-EVIDENCE/ (incident evidence)
- any file created <7 days ago

## Resurrection Test (SHADOW)
From the 4 superseded-tasks, select 1 (B5-MEASURED-RECOVERY-001):
- original path: state/ops-agent/state/superseded-tasks/native-B5-MEASURED-RECOVERY-001.json
- hash recorded in W0 manifest
- resurrection = copy back to canary-requests/ — TESTED IN FIXTURE ONLY
- actual resurrection: NOT PERFORMED (would pollute the live queue)

## Honest Assessment
- ZERO items are currently eligible (all <14 days old); inventory is NOT eligibility
- The archive_ convention + superseded-tasks/ already captures the main lifecycle
- A full ACTIVE→COLD→...→DELETED pipeline would be premature with 4 candidates
- No deletion is proposed in this wave
