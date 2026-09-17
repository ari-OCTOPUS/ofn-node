# NEXT-15 Release Package + 24h window START
window_start_utc: 2026-09-17T11:01:39Z
window_end_utc:   2026-09-18T11:05:00Z (24h real, per plan A15; waiver = owner-explicit only, counts NOT-pass)

## Deployed/changed inventory (this program)
1. LIVE 138 broker /home/ari/ofn/state/api-budget/api_budget.py — fcntl critical section + outstanding-reserve liability.
   preimage 43aa9c5a6c9f5b5d7b97aadafbfb25b04e2c4921f941413da59731688fea984a; backup api_budget.py.pre-a06fix-20260917T105427Z; rollback = cp back.
2. Mirror v2 (receiver 182 /usr/local/bin/octopus-mirror-receive sha 271973cc…, sender 138 push.sh f8779ca2…; .bak-s1pa-* both).
3. T1 candidate snapshot.py + replay_streaming (commit 942d0c3) — NOT deployed to 182 sensorium.
4. Worktree codex/next15-exec-20260917 @ 0c9941ae (A02/A03/A04) — NOT deployed.
5. S2 worktree s2-maturity-20260917 @ 1251b8a3 (money_executor, x402) — NOT deployed.

## Window canary criteria (checked at end; fail => window FAIL)
- broker: status() healthy; no cap breach rows; window/month sane (liability fn present).
- mirror: daily 03:30Z push -> RECEIVED+HASH-MATCH v2 or explicit DUP_REJECTED (no-change day).
- 182 apply-units frozen (W1 verdict automation 09:20Z) + sensorium alive, no OOM.
- live 138 economic files untouched (append-only).
- fleet heartbeat: 7 nodes reporting.

## Stop conditions
HALT-ALL semantics, budget FAIL_CLOSED, mirror quarantine flood, any OOM on 182 sensorium.
