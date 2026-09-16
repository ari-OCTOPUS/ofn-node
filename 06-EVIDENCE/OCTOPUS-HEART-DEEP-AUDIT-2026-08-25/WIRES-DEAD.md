# WIRES-DEAD (propose list only, no disable)
Stamp: 2026-08-25T08:16:03+10:00

## work_pump templates (work-plan.v1 aligned 2026-08-21)
| kind | every_s | paid | last_run | last result |
|---|---|---|---|---|
| health | 21600 | no | 2026-08-25 06:50 | ok, gate0 false, period_shadow 276.75 |
| gap_report | 43200 | no | 2026-08-25 00:55 | ok, A08/A07/A06 awareness |
| web_research | 43200 | no | 2026-08-25 01:04 | ok n_hits=6, ingest skipped 6 (may_authorize false) |
| search | 86400 | yes | 2026-08-24 13:08 | skipped: paid-search provider not configured |
| llm_learn | 86400 | yes | 2026-08-24 13:13 | ok local, n_proposals=0, cost 0 |

ACTIVATION-WORK-LLM.flag is PRESENT. Paid search still skips (no provider). llm_learn local $0.

life_economy-latest (2026-08-19) marks work_pump RETIRED. That is STALE metaphor: pump still fires 2026-08-25. Do not delete pump.

## heart_wires (lives at _ops/heart_wires.py, NOT in heart/)
Latest: 2026-08-24T14:10:23Z (stale vs beat 48905). Last stamp 2026-08-25T00:10 beat 48450.
Lanes: thesis (ok, 5 runnable / 6 needs_design / 8 blocked), coherence (ok health 1.0), identity (ok, missing sigma), seed_killer (kept 49).
Flag-gated: OCTOPUS_WIRE_THESIS_QUEUE / COHERENCE / IDENTITY_EQ. Latest shows ok:true so those env flags were on at last run.

## Propose later GO (do not disable now)
- search template: already no-op; leave until a provider exists
- web_research ingest: all skipped; leave template, fix ingest later
- heart_wires latest is 18h stale vs pacemaker; later: emit on beat or accept advisory
- Do not delete any template this wave
