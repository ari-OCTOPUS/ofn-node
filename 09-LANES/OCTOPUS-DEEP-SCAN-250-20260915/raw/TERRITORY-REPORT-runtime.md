# TERRITORY-REPORT — runtime (READ-ONLY scan, 2026-09-15)

GOV_VERSION=V8 · LADDER=L2 · lane: OCTOPUS-DEEP-SCAN-250 (runtime territory)
Scope: F:\ofn-node, ssh board138 (~/ofn, ~/octopus-mesh, systemd), E:/wt-eti-* + E:/germline, F:/backup worktrees. All probes read-only; zero writes on any host.

## Coverage
read: 14/14 probes executed, excluded: 0 (all four territories reachable; germline probed but is not itself a git repo — it hosts vault.git + ops files)
Probes: ofn-node git log/status/docs/TODO; 138 ofn git log -30/status/TODO/state/deep-scan/systemctl units+timers/ops-agent state/octopus-mesh state+receipts; E: 4 ETI worktrees + germline logs; worktree list + merge-base checks on 8 branches.

## Findings (15; full JSONL: runtime-findings.json)
| id | class | title |
|---|---|---|
| RT-1 | OPEN_WORK | deep-scan findings-current.json ~65 open items; G8-021 executed-but-unretired burns budget each tick |
| RT-2 | SEASON_LEFTOVER | octopus-revenue-drive.service dead 4h27m mid-season window |
| RT-3 | DEBT_HIDDEN | ofn-node dirty: +1145/-556 uncommitted; opslib.py + its boundary tests deleted |
| RT-4 | OPEN_WORK | ofn-node 227 untracked files incl 31 untracked 09-LANES dirs |
| RT-5 | RULING_UNEXECUTED | GAP-LEDGER canonical switch blocked on "2 of 4" Downloads files since 09-09 |
| RT-6 | DOC_RUNTIME_DISCREPANCY | DISCOVERY.md still fronts the retired email channel |
| RT-7 | OPEN_WORK | OWNER-CHECKLIST 4 owner-only actions open since 09-01 |
| RT-8 | DEBT_HIDDEN | 138: data/gates.json modified uncommitted + live-agent .bak swaps |
| RT-9 | SEASON_LEFTOVER | 12 days ECONOMIC-LEARNING auto-runs untracked on 138 |
| RT-10 | RULING_UNEXECUTED | ETI armed reconciliation (due 09-13T06:30Z) never fired |
| RT-11 | ABANDONED | germline: 3 board-cp acks pending since 2026-08-17 |
| RT-12 | DEBT_HIDDEN | germline hourly push: github_wire phase permanently absent |
| RT-13 | OPEN_WORK | 4 unmerged worktree branches (s2b-claim, autonomy-full, transform-revenue, sul/brain-c1) |
| RT-14 | SEASON_LEFTOVER | 6 eti branches + 5 worktrees unmerged; run2 canonical PARTIAL unclosed |
| RT-15 | OPEN_WORK | ops_agent.py retirefix hotfix today, uncommitted, timer firing on it |

## What failed / not probed deeper
- No secrets printed; key names only. All ssh used BatchMode + ConnectTimeout=8; none timed out.
- systemctl: no octopus-* unit in FAILED state (exit grep found none) — dead services are oneshot-between-timer-runs; RT-2 cadence gap is the only season-relevant anomaly.
- octopus-mesh receipts/ holds 8107 files incl many *.claim.json; not individually reconciled (out of probe budget).

## Rollback steps
None needed: scan performed zero mutations on all hosts. The only files created are the two artifacts in this raw/ directory inside the vault.

## Status: verified (all anchors from live command output, 2026-09-15 ~10:30 UTC)
