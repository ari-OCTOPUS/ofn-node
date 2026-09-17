# LANE REPORT — OCTOPUS-NEXT15-EXEC-20260917

GOV_VERSION=V8 · LADDER=L2 · 2026-09-17 · Option A (verbatim «a», OWNER-DECISION.json, plan_sha 72f51ca1…)
Worktree: `F:/wt-next15-20260917` @ `codex/next15-exec-20260917` (base 1251b8a3). Commit: see git log (A02+A03+A04).

## What was executed this session (first NEXT-15 execution round)

| Action | Status | Evidence |
|---|---|---|
| A01 identity/measure | PARTIAL | `RUNTIME-MAP.json` (scoped first cut: nodes/PIDs/code/data/unknowns) + S2 M0 receipt; full TRACE.json pending (next) |
| A02 event contract | **FIXED_TESTED** | `normalize_feeder_events` + `FEEDER_EVENT_MAP` in chain.py, wired in cli.run with visible mapping report. Tests: 8 real `communication.sent` → 8 traceable contacts; `payment.claimed` NOT mapped (no fabricated payments); unknown/malformed classified; chain leaves payment=unknown without verified receipt |
| A03 ledger integrity | **FIXED_TESTED** | Ledger contract v2: `prev_line_sha256` chaining + checkpoint sidecar (head anchor, fsync) + legacy v1 prefix counted, never rewritten. Tests: content-tamper→TAMPERED; reorder/mid-delete→CHAIN_BREAK; duplicate→detected; end-truncate→TRUNCATION_SUSPECTED; legacy prefix→VALID |
| A04 durable recovery | **FIXED_TESTED** | Supersession-aware recover: exactly ONE disposition per damage across restarts (restart×3 → 1 row); torn writes preserved byte-for-byte, excluded from recovered view, one SAFE_HOLD disposition; append-only proven by test |
| A05 low-cost replay | MEASURED_DONE(reader) | `replay_streaming()` (T1 commit 942d0c3): full 3.08M-event from-empty = 28.9s / 216MB peak (was OOM 1.5G ×2); equality TRUE on 300k prefix. App-batch integration + full replica boot pending (blockers recorded) |
| A06 atomic budget | ADVANCED | money_executor gate tests + M6 drill (DUPLICATE_SETTLE/tamper). Open: subprocess-crash persistence, concurrency stress, all-callers inventory |
| A07 real effect halt | PARTIAL | halt-oracle fail-closed 3/3 (isolated). Open: effect-path capture-transport incl. race/retry |
| A08 valid witness | PARTIAL | mirror v2 negative suite 23/23 + W1 window running (verdict auto-fires 2026-09-18 09:20Z). Open: sensorium witness binding |
| A09–A12 | NOT_RUN | unblocked by A02–A04 now; A09 is the single next action |
| A13–A15 | NOT_RUN | A13 needs real holdout arms; A15's 24h window not started (by design, post-final-change) |

Test totals this worktree: dedicated 15/15 + full suite **9,781 passed / 28 skipped** (one hygiene
failure introduced and fixed in-session: bare `mkdtemp` → managed `temp_dir`).

## Honesty records
- The 9 undetected fault classes, duplicate remediations and torn-write errors were proven by the
  S2-LEARNING-PROOF lane on real bytes; this session reproduced them as failing expectations of the
  FIXED code's tests (defect→fix→regression), not re-measured on the old code.
- Live 138 economic ledger NOT migrated to v2 — that is a Class-B step needing preimage+rollback;
  the contract migration is append-only by construction.
- No gates weakened; no failures erased; zero API spend; no secrets.

## Rollback
Worktree: `git revert HEAD` (single commit). Vault lane: remove `09-LANES/OCTOPUS-NEXT15-EXEC-20260917/`.
Nothing deployed to any node this session.

## Next single action
A09: wire outcome→memory on `_ops/outcomes/learning_gate.py` against the fixed ledger+chain;
one full trace (event → ledger row → lesson → restart survival → consumption ref) then A10.

## ROUND 2 — «همرو کامل کن» (2026-09-17 ~11:15Z)
- **A06 FIXED_TESTED_ISOLATED**: measured TWO real production defects in the api-budget broker
  (TOCTOU race: both concurrent reserves accepted; open reservations invisible to all caps).
  Fix (fcntl critical section + outstanding-reserve liability) applied to the isolated drill copy
  on 182 and re-measured: exactly-one-accepted + crasher liability retained across reload
  (evidence/A06-RESULT.json, verdict_pass=true). Live broker patch staged, NOT deployed.
- **A11 SYSTEM_SELF_REPAIR_SCOPED**: ledger-damage family (orphan/torn/tamper ×2 rounds each)
  executed BY the system path with zero engineer interventions, on TWO hosts
  (laptop + node160), all_pass both, 16 receipt rows each (evidence/A11-*-receipts.jsonl).
  Full A11 (supervisor/transport families) remains open.
- **A14 PARTIAL**: real fleet job on 160 with durable receipts (the A11 run itself);
  self-model consumption + business workflow still open.
- A09 remains the loop entry (API mapped, trace build next); A10/A12/A13/A15 NOT_RUN.
