# 07 TEST PLAN — A01 Repository Cartographer (2026-08-16)

Purpose: convert tonight's static/observational evidence into executable verification for a **sanctioned
wired lane** (council agents remain read-only). Each test states pass criterion and evidence tier it would earn.

## P0 — freezes & incidents (highest priority)
| ID | Test | Command (sanctioned lane) | Pass criterion | Tier earned |
|----|------|---------------------------|----------------|-------------|
| T-01 | Reproduce budget settle failure read-only | inspect `_ops/budget/budget-state.json` + `organ-gate-log.jsonl` + open handles (`handle.exe`/`lsof`) around settle; no writes | identify the writer holding the lock at 20:09; Errno 22 explained | T0 |
| T-02 | Freeze lifecycle | `cat _ops/budget/FREEZE.flag`; check `frozen` flips false after owner-approved clear | freeze cleared only after root cause; recovery documented | T0 |
| T-03 | Alert path for freeze | grep governor-alerts.md tail; confirm an alert exists for the 20:09 freeze | alert recorded with timestamp + actor | T0 |

## P1 — live runtime claims
| ID | Test | Command | Pass criterion | Tier |
|----|------|---------|----------------|------|
| T-04 | organism beats progress | poll `http://127.0.0.1:8771/api/organism` twice ≥5 min apart | beat increases; ts advances | T0 |
| T-05 | cortex journal append | `tail _ops/state/cortex/journal.jsonl` | new entries while PID 11144 alive | T0 |
| T-06 | live room serves | `curl http://127.0.0.1:8773/` + `/api/live` | HTTP 200; state fields render | T0 |
| T-07 | dashboard port | `curl http://127.0.0.1:8770/` | 200 (or documented offline) | T0 |
| T-08 | port 8768 ownership | `netstat -ano | findstr 8768` | **expect none** (stale lore, F-021); if something listens, A04 must review it | T0 |
| T-09 | scheduled task targets | `schtasks /query /v /fo csv` per OCTOPUS-* task | each task Action points at an existing file (watchdog ps1 / run.py) | T0 |

## P2 — governance claims
| ID | Test | Command | Pass criterion | Tier |
|----|------|---------|----------------|------|
| T-10 | Policy Gate wired | `python -c "import policy_gate"` under `_ops` + inspect wiring.py branch using it; trigger one talk-gate decision in shadow | DENY/QUARANTINE on ambiguous action; reason string recorded | T1/T2 |
| T-11 | Money gate fail-closed | pytest `_ops/tests/test_money_gate*` (exists? run `pytest _ops/tests -k money`) | negative/NaN/above-gate all denied; ≤20 allowed only with valid channel | T1 |
| T-12 | Dual veto dormant | grep env of live processes for OCTOPUS_WIRE_DUAL_VETO; grep events.jsonl for `veto-` trace_ids | no veto traces in live events while flag unset | T0 |
| T-13 | A2 blocked claim | `pytest _ops/tests -k action_bridge`; inspect executor paths for A2/A4/A5 | A2 returns BLOCK; A4/A5 no executor (match integration.py:42) | T1 |
| T-14 | octopus_v3 unwired | `grep -rn "octopus_v3" _ops/organism.py _ops/wiring.py` | no import; 18/18 tests still pass (`pytest _ops/tests -k octopus_v3` or suite) | T1 |
| T-15 | propose-only invariant | scan events.jsonl for effector/execute receipts; confirm only propose_action writes `_octopus/queue/pending` | zero non-propose execution receipts tonight | T0 |

## P3 — ledger & memory claims
| ID | Test | Command | Pass criterion | Tier |
|----|------|---------|----------------|------|
| T-16 | ledger chain integrity | genome-system `ledger.py verify()` | full-chain verify OK on 11,444 records | T1 |
| T-17 | ledger live append | note head id; wait one governor epoch (≤15 min) | new records appended by governor/actor | T0 |
| T-18 | bitemporality audit | grep ledger.py for valid_from/valid_to/effective fields | none found ⇒ documented as unitemporal (C-02) | T2 |
| T-19 | memory read-back | trace one `recall_reach` event: read code path from events.jsonl → neural consolidation → any consumer | consumer actually uses recalled items (not just writes) | T2 |
| T-20 | identity_health freshness | two samples of ORGANISM-STATE.json across beats | value recomputed (drifts or recalculates), equations_touching non-empty | T0 |

## P4 — suite health (residual debt)
| ID | Test | Command | Pass criterion | Tier |
|----|------|---------|----------------|------|
| T-21 | `_ops` full suite | `cd _ops && python -m pytest` | all green; lastfailed cache clears | T1 |
| T-22 | root suite | `cd F:/backup && python -m pytest` (config permits) | documented failures vs cache's 5 | T1 |
| T-23 | 4d_system suite | `cd 4d_system && python -m pytest` (incl. l0/l1/l2 trees) | matches MANIFEST claim "141 tests" or newer count | T1 |
| T-24 | NBB-CP canonical fork suite | per owner decision in R-02; run the chosen fork's `pytest` | green on canonical fork only | T1 |

## P5 — repository integrity
| ID | Test | Command | Pass criterion | Tier |
|----|------|---------|----------------|------|
| T-25 | germline remote health | `git -C F:/backup fsck` + `git fetch germline --dry-run` | no corruption; lag matches live germline_lag_h | T2 |
| T-26 | worktree garbage | `git -C F:/backup worktree prune --dry-run` | only the 2 archived worktrees prune | T2 |
| T-27 | bundle backup | copy `nbb-control-plane-history.bundle` hash + size; verify Desktop repo still fetches | bundle readable (fetch OK) | T2 |

**Constraint for all runs**: tests that write (pytest caches, ledger verify with fix flags, bundle fetches)
are authorized ONLY to the owner/wired lane; council runs are observation-only. Any test that would
clear FREEZE.flag or restart a process is explicitly EXCLUDED from this plan until owner word.
