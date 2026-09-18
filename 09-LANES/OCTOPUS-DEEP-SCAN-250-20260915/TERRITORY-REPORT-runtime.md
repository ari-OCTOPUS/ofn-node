# TERRITORY-REPORT — runtime

findings: **22** · classes: OPEN_WORK 10 · DEBT_HIDDEN 4 · SEASON_LEFTOVER 4 · RULING_UNEXECUTED 2 · DOC_RUNTIME_DISCREPANCY 1 · ABANDONED 1

## top findings (rank order)

- **[F-001] r21.0 OPEN_WORK** G8-021 executed but never retired — request now self-stale (base 02fb704d vs live fc993720), burns component budget each
  - `138:/home/ari/ofn/state/ops-agent/state/canary-requests + ops-receipts.jsonl` · `OPS_B_STALE_BASE have:fc993720 at 07:05:00Z`
- **[F-005] r20.6 DEBT_HIDDEN** fleet-jobs bus: 61 of 91 rows stuck non-terminal (17 QUEUED, 16 LEASED, 15 RUNNING, 13 ACK_RESULT, 13 PERSISTED) — most 
  - `138:/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl` · `state histogram 07:10Z`
- **[F-007] r20.4 OPEN_WORK** TRAFFIC-DECISION owner card open — 'the single real money unlock' (ads/outreach/market choice) blocks the entire revenue
  - `138:/home/ari/ofn/state/revenue-drive/owner-review.json + F:/backup/01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `'تنها قفلِ واقعی جلوی پول'`
- **[F-014] r13.0 OPEN_WORK** TRIO-002 + W3G30-COMBINED deploys complete the G28 arc (decision consumer, precondition freeze, CATSCOPE) — queued, exec
  - `138: canary-requests/native-Z-SUCCESSOR-TRIO-002.json + W3G30` · `ROUND31 'QUEUED (inside TRIO v3d) awaiting only TRIO deploy'`
- **[F-020] r12.8 OPEN_WORK** 17 CHANNEL_AUTHORIZED packets unsent + rate-card single-source — funnel staged but stalled at owner traffic decision
  - `138: revenue-state.json 06:01:30Z` · `counts CHANNEL_AUTHORIZED=17 SENT=3`
- **[RT-1] r10.0 OPEN_WORK** board138 deep-scan findings-current.json holds ~65 open findings; G8-021 executed but never retired, burns budget each t
  - `138:~/ofn/state/deep-scan/findings-current.json` · `"F-001" state open: G8-021 executed but never retired — request now self-stale (base 02fb704d vs live fc993720`
- **[RT-8] r10.0 DEBT_HIDDEN** board138 ~/ofn dirty: data/gates.json (governance) modified uncommitted + live-code .bak files from 09-11/09-14
  - `138:~/ofn (git status)` · `M data/gates.json; M ofn/agents/glass_runner.py; ?? glass_runner.py.pre-g13live-20260914; ?? self_model_produc`
- **[F-011] r9.8 OPEN_WORK** OW-9: B5 circuit breaker OPEN since 06:38Z, feeding failures not root-caused
  - `138: ops-receipts + budget_allows('B5')` · `(False,'CIRCUIT_BREAKER_OPEN') 07:08Z`
- **[RT-15] r9.8 OPEN_WORK** ops_agent.py.pre-retirefix-20260915 backup next to live ops_agent.py on 138 — today hotfix uncommitted
  - `138:~/ofn/state/ops-agent/ops_agent.py` · `ops_agent.py + ops_agent.py.pre-retirefix-20260915 adjacent in same dir`
- **[F-046] r9.0 DEBT_HIDDEN** smartmontools.service FAILED on 138 — disk monitoring down on the node that survived a full disk crisis
  - `138: systemctl list-units --state=failed` · `smartmontools loaded failed`
- **[RT-2] r6.8 SEASON_LEFTOVER** octopus-revenue-drive.service dead 4h27m mid-season-window on 138
  - `138:systemctl status octopus-revenue-drive.service` · `Active: inactive (dead) since Tue 2026-09-15 06:01:32 UTC; 4h 27min ago; timer next 12:00:27 UTC`
- **[RT-3] r6.8 DEBT_HIDDEN** Laptop F:/ofn-node working tree dirty: 19 files +1145/-556 uncommitted, incl budget/opslib.py DELETED with its boundary 
  - `F:/ofn-node (git status)` · `D budget/opslib.py; D tests/test_counter_source_f2.py; D tests/test_opslib_import_boundary.py; 19 files change`

## coverage

- read: n/a (carried group; per-item anchors in FORGOTTEN-250.json)
