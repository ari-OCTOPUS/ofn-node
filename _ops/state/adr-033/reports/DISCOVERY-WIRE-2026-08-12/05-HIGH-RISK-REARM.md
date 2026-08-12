---
type: evidence
status: active
created: 2026-08-12
updated: 2026-08-12
tags: [octopus, discovery, rearm, wiring]
related:
  - "[[00 - Inbox/2026-08-12 MEGAPROMPT — Discovery Wire Missing Connections (Junior-Safe)]]"
---

# OWNER VOTE #2 — High-Risk Re-Arm + Leftover Wires (2026-08-12)

> رأی مالک: «همه چی پرریسک روشن کن وصل کن چتای قبلیو بخون هرچی جا مونده رو کامل کن»
> خلاف `03-OWNER-DISARM-FLAGS.md` — last vote wins.

## Re-armed (OCTOPUS-flags.cmd last-wins)

| key | value |
|---|---|
| RUNNER_APPLY / SEED_ASSEMBLER / EVOLUTION_GATE / REDTEAM | 1 |
| KERNEL_BRIDGE_READER | 1 |
| PROFILE | live |
| VALUE_LEDGER / ENFORCE_MONEY_FSM / INITIATIVE_UNCAPPED | 1 |
| CODE_AUTOAPPLY_LOWRISK / MINING_OS / BUDGET_JUDGE | 1 |
| LEAD_FIRST_RESPONSE_LLM + caps / COLLAB_MODEL_DAILY_CAP | raised |
| IMPROVE_REFRACTORY_H | 0 |
| LIVE-ENABLED.flag | recreated |
| KILL_SWITCH / OTLP_ALLOW_REMOTE | stay OFF |
| SMTP poison keys | stay empty |

## Code wired

| id | change |
|---|---|
| DW-03 | `organism.py` → `kernel_bridge_reader.persist_report` every 11 beats |
| DW-02 | `seed_beat.py` + organism call every 17/23 beats |
| DW-05 / CHR-01 | `schedule_period_bias` soft-clamp on `_sleep_s` (±20%, \|bias\|≤30s, floor 60) |
| MEM-01 | `retrieval_router` searches `namespace=semantic` |
| MEM hebbian | advisory `hebbian_hint` from math_control `assoc_strength` |
| UI-02 | tasks/obsidian calm only if `status==="ok"` |
| UI-05 | Ask/Collab client timeout → 90s |
| UI-07 | toast on HTTP 403 / owner_auth |
| UI-09 | `buildSourcesPanel` on collab-fallback |

## Explicitly still NOT done

- Phase 4 money claim / lead address (needs owner data)
- RECONCILE C (AGI claims) — honesty A kept
- `WIRE_RUNNER_APPLY` still no production apply module (flag ON = armed inert until module exists)
- WORKLOCK files untouched (`wiring.py`, `run_all.py`, `center.py`, `orphan_scan.py`)

## Verify after restart

- `node --check telegram_center/miniapp/app.js`
- `pytest tests/test_chatbox_unified.py -q`
- env after organism restart: PROFILE=live, SEED_ASSEMBLER=1
- MiniApp: close/reopen
