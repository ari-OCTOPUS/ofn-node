# Phase 3 P4 — Memory Gate implementation

MEMORY_GATE_CODE: PASS on source
MANDATORY_MEMORY_READ_LIVE: false (PID 12748 still old bytecode)

## Proven path

```
decision cycle
→ MemoryQuery(purpose, as_of=decision_time)
→ SELECT episodes LEFT JOIN events WHERE ep.created_at<=as_of
   AND (ev missing OR ev.created_at<=as_of)
→ SELECT events WHERE created_at<=as_of
→ audit_future_use (no futures table, no fake ids)
→ MemoryReadReceipt (empty SELECT still ok)
→ DecisionEvidenceBundle
→ persist memory_read_receipts + decision_evidence (executable CHECK = 0)
→ infer / propose
```

Fail-closed: `MemoryUnavailable` → `memory_status=UNAVAILABLE`, `confidence=reduced`, `external_action=blocked`, `executable=false`. Failed receipts are not inserted (`CHECK future_use_count=0`).

Live `connect(organism.db)` remains blocked unless `OCTOPUS_ALLOW_LIVE_SCHEMA=1`.

## Wired purposes

| path | function | purpose string |
| --- | --- | --- |
| cycle | `life_cycle.tick` | `life_cycle.tick` |
| introspect | `introspect_self` | `introspect` |
| create | `persist_self_model` | `create` |
| conclude | `run_transformation_eval` | `conclude` |
| curiosity | `propose_curiosity` | `curiosity` |
| school | `evaluate_school` | `school` |
| inner_speech | `inner_turn` | `inner_speech` |
| learning | `maybe_self_learn` / explicit gate | `learning` |
| proposal | `seed_futures` | `proposal` |
| utterance | `persist_utterance` | `utterance` |
| ask | `AskCascade.ask` | `AskCascade.ask` |

Ask still does not call WAN. Active Inference and WBE are not on this path (`executable=false`).
