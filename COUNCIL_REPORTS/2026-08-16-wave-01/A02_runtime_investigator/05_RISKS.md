# 05 Risks — A02 Runtime Investigator (CONSOLIDATED)

| ID | Risk | Severity | Evidence |
|---|---|---|---|
| RK-1 | **Public internet exposure**: cloudflared tunnel `octopus-miniapp` has published the MiniApp gateway (8774) since 06:58 today. Auth wall is initData HMAC + owner-id binding (code-verified), but any gateway bug is internet-reachable. | MEDIUM | R-014, F-03 |
| RK-2 | **LAN-wide board listener**: board_cp on 0.0.0.0:8801 (TLS self-signed, Bearer). Default bind is all-interfaces; compromise of the Bearer secret exposes pull/ack. | MEDIUM | R-014, F-04 |
| RK-3 | **Safety is structural, not gated**: today's safety depends on absence of executor paths (A2+ have no functions) and NOT_WIRED stubs. Any new effector code added without a gate silently inherits "allowed". | MEDIUM-HIGH | R-007, R-009, R-010, F-15/F-16/F-18 |
| RK-4 | **Stale-secret hygiene**: `.env.bak-20260810` at repo root holds old credential copies; `.env` sits in a git-tracked vault root (assume compromise-on-read). | LOW-MEDIUM | R-016 |
| RK-5 | **Snapshot truth drift**: channel-status dashboard entries (8790/8770) and the 30-min-cooldown CURRENT-TRUTH lag runtime; operators may act on stale "live" indicators. Same family: board-status 53 min stale while bridge self-reports "active"; identities-latest 11 h old. | LOW | R-012, R-013, F-29 |
| RK-6 | **Terminology hazards**: `frozen: true` while running; `money_link: active` while nothing can transact; "propose_only" label implies enforcement. Human misdecision risk during incidents. | LOW | R-015, C-3 |
| RK-7 | **brain_core parity soak produces no old-side samples** (missing_old=4167, matched=0) — shadow comparison is not actually comparing; promotion decisions would rest on nothing. | LOW | R-017 |
| RK-8 | **Single-host coupling**: ollama, cloudflared, all six python processes share one machine and one git worktree; a crash/oom of PID 29028 halts the organism with watchdog-only recovery (unverified this session). | LOW | process map |
| RK-9 | **Runtime-code drift**: running processes predate the 23:01 edits / 23:27 HEAD; no boot-hash recorded; lazy imports could mix module versions mid-process. Debugging or incident response against current code would mismatch the running reality. | MEDIUM | F-23 |
| RK-10 | **Unversioned scheduled execution**: `OCTOPUS Observatory Hourly` runs `run_observatory.py` from a Desktop working copy outside the repo/TCB — no git provenance, no review gate. | MEDIUM | F-02 |
| RK-11 | **Pre-armed autonomy**: AUTONOMY_FREE/GRANT, CODE_AUTOAPPLY_LOWRISK, LEAD_OUTBOUND flags live; A2 is blocked only by a classifier vote (VQ-SELFGOAL-002). A future vote/flag flip widens automation without any wiring change. | MEDIUM | F-12, R-009 |
| RK-12 | **Clock fragility**: no `time.monotonic`; beat scheduling and freshness checks on wall clock (NTP step/DST sensitive); plus the local-time-with-`Z` bug misleads UTC consumers by 10 h. | MEDIUM | F-24 |
| RK-13 | **Ambient environment**: no venv (system Python shared with everything else); `fingagent` third-party agent listens on 0.0.0.0:3653 on the same host; ExpressVPN present. Not OCTOPUS faults, but they share its blast radius. | LOW | F-26, port map |
| RK-14 | **Dual approval ledgers**: active `_octopus` approvals today vs adr-033 vs cortex cards; 0 rows in `gated_effect` — audit trails can disagree about what was ever approved. | LOW-MEDIUM | F-28, R-006 |

No CRITICAL runtime risk observed: no unauthenticated consequential surface found at the runtime layer during this read-only window (deep injection testing is A04/A14 scope).
