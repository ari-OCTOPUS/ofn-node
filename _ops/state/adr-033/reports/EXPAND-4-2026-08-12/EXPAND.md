---
type: evidence
created: 2026-08-12
owner_verdict: "هر4 مورد رو کامل"
---

# EXPAND-4 — چهار پلهٔ امن (2026-08-12)

## Scope (رأی مالک)

1. Collaborator model daily cap `20 → 50`
2. Panel `8790` روشن
3. auto_approve refractory کوتاه‌تر (`24h → 6h`) پس از نقاهت
4. Lead send با سقف پایین + Harvest

## Applied

| # | Change | Where |
|---|---|---|
| 1 | `OCTOPUS_COLLAB_MODEL_DAILY_CAP=50` | `_ops/OCTOPUS-flags.cmd` |
| 2 | Panel process on `127.0.0.1:8790` · `panel_8790=true` | `_ops/panel/server.py` + `channel-status.json` |
| 3 | `OCTOPUS_IMPROVE_REFRACTORY_H=6` (+ legacy `IMPROVE_REFRACTORY_H`) · `improve.py` reads both | flags + `_ops/cortex/improve.py` |
| 4a | `OCTOPUS_WIRE_HARVEST=1` (AusTender keyless → lead-inbox; zero send/spend) | flags |
| 4b | `OCTOPUS_WIRE_LEAD_FIRST_REPLY=1` (compose only) | flags |
| 4c | `OCTOPUS_WIRE_LEAD_FIRST_RESPONSE=1` (owner draft card; never auto-sends) | flags |
| 4d | Send path unchanged: `LEAD_OUTBOUND=1` · hard `LEAD_DAILY_SEND_CAP=10` two layers · `RESPONSE_LLM=0` · money/UNCAPPED off | already armed |

## Live verify

See `VERIFY.json` — `all_ok=true`:

- cap50 / harvest / first_reply / first_response / refractory_flag=6 / panel HTTP 200 / lead_cap=10

## Restarts

- organism · center · cortex (fresh PIDs after flag reload)
- Panel started separately (not in RESTART-PROCESS)

## Rollback

```bat
set OCTOPUS_COLLAB_MODEL_DAILY_CAP=20
set OCTOPUS_IMPROVE_REFRACTORY_H=24
set OCTOPUS_WIRE_HARVEST=0
set OCTOPUS_WIRE_LEAD_FIRST_REPLY=0
set OCTOPUS_WIRE_LEAD_FIRST_RESPONSE=0
```

Then restart organism/cortex/center; stop panel process on 8790.

## Still closed (deliberate)

- memory `may_authorize`
- money live / VALUE_LEDGER / MONEY_FSM
- `LEAD_FIRST_RESPONSE_LLM`
- INITIATIVE_UNCAPPED
